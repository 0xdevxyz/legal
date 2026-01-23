"""
Risk Calculator Service für Complyo
Berechnet Abmahnrisiken basierend auf der Risk-Matrix
"""

import asyncpg
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class RiskCalculator:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self._cache = {}  # Simple in-memory cache
    
    async def calculate_issue_risk(
        self, 
        issue_text: str, 
        market: str = 'DE'
    ) -> Dict[str, Any]:
        """
        Berechnet das Abmahnrisiko für ein gefundenes Issue
        
        Args:
            issue_text: Text-Beschreibung des Issues
            market: Markt (DE, AT, CH, EU)
        
        Returns:
            Dict mit category, risk_min, risk_max, risk_range, legal_basis
        """
        try:
            # Kategorisiere Issue
            category = self._categorize_issue(issue_text)
            
            # Hole Risiko aus Matrix
            risk = await self._get_risk_from_matrix(category, market)
            
            if not risk:
                # Fallback für unbekannte Kategorien
                return self._get_default_risk(category)
            
            return {
                'category': category,
                'severity': risk['severity'],
                'risk_min': float(risk['risk_min_eur']),
                'risk_max': float(risk['risk_max_eur']),
                'risk_range': self._format_risk_range(
                    risk['risk_min_eur'], 
                    risk['risk_max_eur']
                ),
                'bussgeld_max': float(risk['bussgeld_max_eur']) if risk['bussgeld_max_eur'] else None,
                'legal_basis': risk['legal_basis'],
                'description': risk['description']
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk for '{issue_text}': {e}")
            return self._get_default_risk('unknown')
    
    async def _get_risk_from_matrix(
        self, 
        category: str, 
        market: str
    ) -> Optional[Dict[str, Any]]:
        """Holt Risiko-Daten aus der Datenbank"""
        cache_key = f"{category}_{market}"
        
        # Check Cache
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            async with self.db_pool.acquire() as conn:
                risk = await conn.fetchrow(
                    """
                    SELECT 
                        category as issue_category,
                        severity,
                        min_risk_euro as risk_min_eur,
                        max_risk_euro as risk_max_eur,
                        0 as bussgeld_max_eur,
                        '' as legal_basis,
                        description
                    FROM compliance_risk_matrix
                    WHERE category = $1
                    """,
                    category
                )
                
                if risk:
                    risk_dict = dict(risk)
                    self._cache[cache_key] = risk_dict
                    return risk_dict
                
                return None
                
        except Exception as e:
            logger.error(f"Database error getting risk for {category}: {e}")
            return None
    
    def _categorize_issue(self, issue_text: str) -> str:
        """
        Kategorisiert ein Issue basierend auf Schlüsselwörtern
        
        Mapping auf die 4 Hauptsäulen:
        1. Barrierefreiheit
        2. Cookie Compliance
        3. Rechtstexte
        4. DSGVO
        """
        text_lower = issue_text.lower()
        
        # Säule 4: DSGVO
        if any(word in text_lower for word in ['datenschutz', 'dsgvo', 'daten', 'privacy']):
            if 'tracking' in text_lower or 'analytics' in text_lower:
                return 'tracking'
            elif 'verarbeitung' in text_lower:
                return 'datenverarbeitung'
            else:
                return 'datenschutz'
        
        # Säule 2: Cookie Compliance
        if any(word in text_lower for word in ['cookie', 'consent', 'einwilligung']):
            return 'cookies'
        
        # Säule 1: Rechtstexte
        if 'impressum' in text_lower:
            return 'impressum'
        if 'agb' in text_lower or 'allgemeine geschäftsbedingungen' in text_lower:
            return 'agb'
        if 'widerruf' in text_lower:
            return 'widerrufsbelehrung'
        if 'kontakt' in text_lower or 'e-mail' in text_lower or 'email' in text_lower:
            return 'contact'
        
        # Säule 3: Barrierefreiheit
        if any(word in text_lower for word in [
            'barrierefreiheit', 'accessibility', 'barrierefrei',
            'screenreader', 'tastatur', 'kontrast'
        ]):
            if 'kontrast' in text_lower:
                return 'kontraste'
            elif 'tastatur' in text_lower:
                return 'tastaturbedienung'
            else:
                return 'barrierefreiheit'
        
        # Weitere Kategorien
        if 'urheberrecht' in text_lower or 'bild' in text_lower or 'foto' in text_lower:
            return 'urheberrecht'
        if 'marke' in text_lower or 'logo' in text_lower:
            return 'markenrecht'
        if 'preis' in text_lower:
            if 'grundpreis' in text_lower:
                return 'grundpreis'
            return 'preisangaben'
        if 'werbung' in text_lower:
            if 'prüfsiegel' in text_lower or 'tüv' in text_lower:
                return 'pruefsiegel'
            elif 'influencer' in text_lower or 'sponsored' in text_lower:
                return 'schleichwerbung'
            return 'irrefuehrende_werbung'
        
        # Default
        return 'compliance'
    
    def _format_risk_range(self, min_eur: float, max_eur: float) -> str:
        """Formatiert Risiko-Range für Anzeige"""
        if min_eur == max_eur:
            return f"{int(min_eur):,}€".replace(',', '.')
        return f"{int(min_eur):,}€ - {int(max_eur):,}€".replace(',', '.')
    
    def _get_default_risk(self, category: str) -> Dict[str, Any]:
        """Fallback-Risiko für unbekannte Kategorien"""
        return {
            'category': category,
            'severity': 'warning',
            'risk_min': 500,
            'risk_max': 2000,
            'risk_range': '500€ - 2.000€',
            'bussgeld_max': None,
            'legal_basis': 'Allgemeine Compliance-Anforderungen',
            'description': 'Allgemeines Compliance-Risiko'
        }
    
    async def get_pillar_summary(self, market: str = 'DE') -> Dict[str, Any]:
        """
        Gibt Zusammenfassung der 4 Hauptsäulen zurück
        """
        try:
            async with self.db_pool.acquire() as conn:
                pillars = await conn.fetch(
                    """
                    SELECT 
                        pillar,
                        COUNT(*) as issue_count,
                        SUM(risk_min_eur) as total_risk_min,
                        SUM(risk_max_eur) as total_risk_max
                    FROM complyo_main_pillars
                    GROUP BY pillar
                    ORDER BY 
                        CASE pillar
                            WHEN 'Barrierefreiheit' THEN 1
                            WHEN 'Cookie Compliance' THEN 2
                            WHEN 'Rechtstexte' THEN 3
                            WHEN 'DSGVO' THEN 4
                            ELSE 5
                        END
                    """
                )
                
                return {
                    'pillars': [
                        {
                            'name': p['pillar'],
                            'issue_count': p['issue_count'],
                            'risk_range': self._format_risk_range(
                                p['total_risk_min'],
                                p['total_risk_max']
                            )
                        }
                        for p in pillars
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting pillar summary: {e}")
            return {'pillars': []}
    
    async def calculate_total_risk(
        self, 
        issues: list,
        market: str = 'DE'
    ) -> Dict[str, Any]:
        """
        Berechnet Gesamt-Risiko für mehrere Issues
        
        ✅ FIX: Realistische Risiko-Berechnung
        - Nicht alle Issues werden gleichzeitig abgemahnt
        - Kritische Issues haben höheres Gewicht
        - Maximales Risiko ist begrenzt (realistische Abmahnung)
        """
        total_min = 0
        total_max = 0
        critical_count = 0
        critical_risks = []
        warning_risks = []
        info_risks = []
        
        for issue in issues:
            risk = await self.calculate_issue_risk(issue, market)
            
            # Gruppiere nach Severity
            if risk['severity'] == 'critical':
                critical_count += 1
                critical_risks.append(risk)
            elif risk['severity'] == 'warning':
                warning_risks.append(risk)
            else:
                info_risks.append(risk)
        
        # ✅ Realistische Berechnung:
        # - Kritische Issues: 100% des Risikos (höchste Priorität)
        # - Warning Issues: 50% des Risikos (werden oft zusammen abgemahnt)
        # - Info Issues: 20% des Risikos (selten einzeln abgemahnt)
        # - Maximum: Realistisches Maximum für eine Abmahnung (50.000€)
        
        critical_total_min = sum(r['risk_min'] for r in critical_risks)
        critical_total_max = sum(r['risk_max'] for r in critical_risks)
        
        warning_total_min = sum(r['risk_min'] for r in warning_risks) * 0.5
        warning_total_max = sum(r['risk_max'] for r in warning_risks) * 0.5
        
        info_total_min = sum(r['risk_min'] for r in info_risks) * 0.2
        info_total_max = sum(r['risk_max'] for r in info_risks) * 0.2
        
        total_min = int(critical_total_min + warning_total_min + info_total_min)
        total_max = int(critical_total_max + warning_total_max + info_total_max)
        
        # ✅ Begrenze auf realistische Maximalwerte
        # Eine einzelne Abmahnung liegt typischerweise zwischen 2.000€ und 50.000€
        # Bei mehreren Issues kann es mehrere Abmahnungen geben, aber nicht unrealistisch hoch
        if total_max > 200000:  # Mehr als 200k€ ist unrealistisch
            total_max = 200000
            if total_min > 100000:
                total_min = 100000
        
        return {
            'total_risk_min': total_min,
            'total_risk_max': total_max,
            'total_risk_range': self._format_risk_range(total_min, total_max),
            'critical_issues': critical_count,
            'total_issues': len(issues)
        }

