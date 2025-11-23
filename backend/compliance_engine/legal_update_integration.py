"""
Legal Update Integration für Compliance Scanner
Bindet aktuelle Gesetzesänderungen in Scans und Fixes ein
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LegalUpdateIntegration:
    """
    Integriert aktuelle Gesetzesänderungen in den Compliance-Scanner
    
    ✨ UPGRADED:
    - Automatische wöchentliche Checks
    - User-Notifications bei neuen Updates
    - Smarte Filterung nach Website-Relevanz
    """
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._active_updates = []
        self._last_refresh = None
        self._notification_queue = []
        
    async def get_active_legal_updates(self, force_refresh: bool = False) -> List[Dict]:
        """
        Holt aktive Gesetzesänderungen aus der Datenbank
        
        Args:
            force_refresh: Erzwingt Aktualisierung des Cache
            
        Returns:
            Liste aktiver Legal Updates
        """
        # Cache für 1 Stunde
        if (not force_refresh and 
            self._last_refresh and 
            (datetime.now() - self._last_refresh).seconds < 3600):
            return self._active_updates
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        id,
                        update_type,
                        title,
                        description,
                        severity,
                        action_required,
                        source,
                        published_at,
                        effective_date,
                        url
                    FROM legal_updates
                    WHERE published_at >= NOW() - INTERVAL '90 days'
                    ORDER BY severity DESC, published_at DESC
                """)
                
                self._active_updates = [dict(row) for row in rows]
                self._last_refresh = datetime.now()
                
                logger.info(f"✅ {len(self._active_updates)} aktive Gesetzesänderungen geladen")
                return self._active_updates
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Legal Updates: {e}")
            return []
    
    def get_relevant_updates_for_category(
        self, 
        category: str,
        updates: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Filtert Legal Updates nach Compliance-Kategorie
        
        Args:
            category: Compliance-Kategorie (impressum, datenschutz, cookies, barrierefreiheit)
            updates: Optional Liste von Updates (sonst wird Cache verwendet)
            
        Returns:
            Relevante Updates für die Kategorie
        """
        if updates is None:
            updates = self._active_updates
        
        # Mapping von Kategorien zu Update-Types
        category_mapping = {
            'impressum': ['regulation_change', 'new_law'],
            'datenschutz': ['regulation_change', 'court_ruling', 'new_law', 'enforcement'],
            'cookies': ['court_ruling', 'regulation_change', 'enforcement'],
            'barrierefreiheit': ['new_law', 'regulation_change']
        }
        
        relevant_types = category_mapping.get(category.lower(), [])
        
        # Zusätzliche Keyword-Filterung
        keywords = {
            'impressum': ['impressum', 'tmg', 'anbieterkennzeichnung'],
            'datenschutz': ['dsgvo', 'datenschutz', 'privacy', 'gdpr'],
            'cookies': ['cookie', 'tracking', 'consent', 'einwilligung', 'ttdsg'],
            'barrierefreiheit': ['barrierefreiheit', 'accessibility', 'wcag', 'bfsg']
        }
        
        category_keywords = keywords.get(category.lower(), [])
        
        relevant = []
        for update in updates:
            # Filter nach Update-Type
            if update['update_type'] in relevant_types:
                relevant.append(update)
                continue
            
            # Filter nach Keywords in Titel oder Beschreibung
            text = f"{update['title']} {update.get('description', '')}".lower()
            if any(keyword in text for keyword in category_keywords):
                relevant.append(update)
        
        return relevant
    
    def apply_updates_to_scan_results(
        self, 
        scan_results: Dict[str, Any],
        updates: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Wendet Legal Updates auf Scan-Ergebnisse an
        Erhöht Severity und Risiko basierend auf aktuellen Änderungen
        
        Args:
            scan_results: Scan-Ergebnisse vom Scanner
            updates: Optional Liste von Updates
            
        Returns:
            Angepasste Scan-Ergebnisse
        """
        if updates is None:
            updates = self._active_updates
        
        if not updates:
            return scan_results
        
        # Kategorisiere Issues nach Kategorie
        issues_by_category = {}
        for issue in scan_results.get('issues', []):
            category = issue.get('category', 'other')
            if category not in issues_by_category:
                issues_by_category[category] = []
            issues_by_category[category].append(issue)
        
        # Wende Updates pro Kategorie an
        affected_issues = []
        for category, issues in issues_by_category.items():
            relevant_updates = self.get_relevant_updates_for_category(category, updates)
            
            if not relevant_updates:
                continue
            
            # Höchste Severity der relevanten Updates
            max_severity = self._get_max_severity(relevant_updates)
            
            for issue in issues:
                # Erhöhe Severity wenn Critical Update existiert
                if max_severity == 'critical' and issue.get('severity') != 'critical':
                    original_severity = issue.get('severity', 'info')
                    issue['severity'] = 'critical' if original_severity == 'warning' else 'warning'
                    issue['legal_update_affected'] = True
                    issue['relevant_updates'] = [
                        {
                            'id': u['id'],
                            'title': u['title'],
                            'url': u.get('url')
                        } 
                        for u in relevant_updates[:3]  # Max 3 Updates pro Issue
                    ]
                    affected_issues.append(issue)
                
                # Erhöhe Risk-Euro um 50% bei kritischen Updates
                if max_severity == 'critical':
                    original_risk = issue.get('risk_euro', 0)
                    issue['risk_euro'] = int(original_risk * 1.5)
                    issue['risk_increase_reason'] = 'Aktuelle Gesetzesänderung erhöht Abmahnrisiko'
        
        # Füge Meta-Info zu Legal Updates hinzu
        scan_results['legal_updates_applied'] = True
        scan_results['active_legal_updates_count'] = len(updates)
        scan_results['affected_issues_count'] = len(affected_issues)
        
        # Erhöhe Gesamt-Risiko
        if affected_issues:
            original_total_risk = scan_results.get('total_risk_euro', 0)
            scan_results['total_risk_euro'] = int(original_total_risk * 1.3)
            scan_results['risk_increase_due_to_legal_updates'] = int(original_total_risk * 0.3)
        
        return scan_results
    
    def _get_max_severity(self, updates: List[Dict]) -> str:
        """Ermittelt höchste Severity aus Updates"""
        severity_order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0, 'info': 0}
        max_severity = 'info'
        max_value = 0
        
        for update in updates:
            severity = update.get('severity', 'info')
            value = severity_order.get(severity, 0)
            if value > max_value:
                max_value = value
                max_severity = severity
        
        return max_severity
    
    async def get_fix_priority_adjustments(self, updates: Optional[List[Dict]] = None) -> Dict[str, int]:
        """
        Berechnet Prioritäts-Anpassungen für Fixes basierend auf Legal Updates
        
        Returns:
            Dict mit Kategorie -> Prioritäts-Boost
        """
        if updates is None:
            updates = self._active_updates
        
        priority_boost = {}
        
        for category in ['impressum', 'datenschutz', 'cookies', 'barrierefreiheit']:
            relevant = self.get_relevant_updates_for_category(category, updates)
            
            # Kritische Updates geben +100 Priorität
            # High Updates geben +50 Priorität
            boost = 0
            for update in relevant:
                severity = update.get('severity', 'info')
                if severity == 'critical':
                    boost += 100
                elif severity == 'high':
                    boost += 50
                elif severity == 'medium':
                    boost += 25
            
            if boost > 0:
                priority_boost[category] = boost
        
        return priority_boost
    
    async def create_scan_notification_for_users(
        self, 
        update_id: int,
        affected_categories: List[str]
    ):
        """
        Erstellt Benachrichtigungen für User, deren letzte Scans von einem Update betroffen sind
        
        Args:
            update_id: ID des Legal Updates
            affected_categories: Betroffene Compliance-Kategorien
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Finde User mit Scans in den betroffenen Kategorien
                users_to_notify = await conn.fetch("""
                    SELECT DISTINCT 
                        u.id as user_id,
                        u.email,
                        tw.id as website_id,
                        tw.url,
                        sh.id as scan_id
                    FROM users u
                    JOIN tracked_websites tw ON u.id = tw.user_id
                    JOIN scan_history sh ON tw.id = sh.website_id
                    WHERE 
                        sh.scan_date >= NOW() - INTERVAL '30 days'
                        AND tw.status = 'active'
                    ORDER BY u.id, sh.scan_date DESC
                """)
                
                # Erstelle Notifications
                for user in users_to_notify:
                    await conn.execute("""
                        INSERT INTO user_legal_notifications 
                        (user_id, legal_update_id, website_id, notification_type, is_read)
                        VALUES ($1, $2, $3, 'rescan_required', FALSE)
                        ON CONFLICT DO NOTHING
                    """, user['user_id'], update_id, user['website_id'])
                
                logger.info(f"✅ {len(users_to_notify)} User über Legal Update #{update_id} benachrichtigt")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Benachrichtigungen: {e}")


# Global instance
legal_update_integration = None


def init_legal_update_integration(db_pool):
    """Initialisiert die Legal Update Integration"""
    global legal_update_integration
    legal_update_integration = LegalUpdateIntegration(db_pool)
    return legal_update_integration

