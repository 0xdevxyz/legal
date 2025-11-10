"""
Complyo Compliance Rule Engine
Modulare, DB-gesteuerte Regel-Engine für Compliance-Checks
"""

import asyncpg
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ComplianceRule:
    """Einzelne Compliance-Regel aus der Datenbank"""
    id: int
    issue_category: str
    severity: str
    market: str
    risk_min_eur: float
    risk_max_eur: float
    bussgeld_max_eur: Optional[float]
    legal_basis: str
    description: str
    effective_date: str

class ComplianceRuleEngine:
    """
    Zentrale Regel-Engine für Compliance-Checks
    
    Features:
    - Lädt Regeln aus compliance_risk_matrix
    - Cached Regeln für Performance
    - Ermöglicht dynamische Regel-Updates
    - Berechnet Risiken basierend auf DB-Werten
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.rules_cache: Dict[str, ComplianceRule] = {}
        self.cache_loaded = False
    
    async def load_rules_from_db(self, force_reload: bool = False) -> int:
        """
        Lädt alle aktiven Compliance-Regeln aus der Datenbank
        
        Args:
            force_reload: Cache neu laden, auch wenn bereits geladen
            
        Returns:
            Anzahl geladener Regeln
        """
        if self.cache_loaded and not force_reload:
            return len(self.rules_cache)
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        id,
                        issue_category,
                        severity,
                        market,
                        risk_min_eur,
                        risk_max_eur,
                        bussgeld_max_eur,
                        legal_basis,
                        description,
                        effective_date
                    FROM compliance_risk_matrix
                    WHERE effective_date <= CURRENT_DATE
                    ORDER BY severity DESC, risk_max_eur DESC
                """)
                
                self.rules_cache = {}
                for row in rows:
                    rule = ComplianceRule(
                        id=row['id'],
                        issue_category=row['issue_category'],
                        severity=row['severity'],
                        market=row['market'],
                        risk_min_eur=float(row['risk_min_eur']),
                        risk_max_eur=float(row['risk_max_eur']),
                        bussgeld_max_eur=float(row['bussgeld_max_eur']) if row['bussgeld_max_eur'] else None,
                        legal_basis=row['legal_basis'],
                        description=row['description'],
                        effective_date=str(row['effective_date'])
                    )
                    self.rules_cache[rule.issue_category] = rule
                
                self.cache_loaded = True
                logger.info(f"✅ Loaded {len(self.rules_cache)} compliance rules from database")
                return len(self.rules_cache)
                
        except Exception as e:
            logger.error(f"Failed to load rules from database: {e}", exc_info=True)
            return 0
    
    async def get_rule(self, category: str) -> Optional[ComplianceRule]:
        """
        Holt eine spezifische Regel aus dem Cache
        
        Args:
            category: Kategorie-Name (z.B. 'impressum', 'datenschutz')
            
        Returns:
            ComplianceRule oder None
        """
        if not self.cache_loaded:
            await self.load_rules_from_db()
        
        return self.rules_cache.get(category)
    
    async def get_all_rules(self) -> List[ComplianceRule]:
        """Gibt alle geladenen Regeln zurück"""
        if not self.cache_loaded:
            await self.load_rules_from_db()
        
        return list(self.rules_cache.values())
    
    async def calculate_risk(self, category: str) -> Dict[str, Any]:
        """
        Berechnet Risiko-Daten für eine Kategorie
        
        Args:
            category: Issue-Kategorie
            
        Returns:
            Dict mit risk_min, risk_max, risk_range, legal_basis, severity
        """
        rule = await self.get_rule(category)
        
        if not rule:
            # Fallback für unbekannte Kategorien
            return {
                'category': category,
                'severity': 'warning',
                'risk_min': 500,
                'risk_max': 2000,
                'risk_range': '500 - 2.000 €',
                'legal_basis': 'Allgemeine Compliance-Pflichten',
                'bussgeld_max': None
            }
        
        return {
            'category': rule.issue_category,
            'severity': rule.severity,
            'risk_min': rule.risk_min_eur,
            'risk_max': rule.risk_max_eur,
            'risk_range': f"{int(rule.risk_min_eur):,} - {int(rule.risk_max_eur):,} €".replace(',', '.'),
            'legal_basis': rule.legal_basis,
            'bussgeld_max': rule.bussgeld_max_eur,
            'description': rule.description
        }
    
    async def get_rules_by_severity(self, severity: str) -> List[ComplianceRule]:
        """
        Filtert Regeln nach Severity
        
        Args:
            severity: 'critical', 'warning', oder 'info'
            
        Returns:
            Liste von ComplianceRule
        """
        if not self.cache_loaded:
            await self.load_rules_from_db()
        
        return [rule for rule in self.rules_cache.values() if rule.severity == severity]
    
    async def get_categories_list(self) -> List[str]:
        """Gibt Liste aller Kategorien zurück"""
        if not self.cache_loaded:
            await self.load_rules_from_db()
        
        return list(self.rules_cache.keys())
    
    async def update_rule(self, category: str, **updates) -> bool:
        """
        Aktualisiert eine Regel in der Datenbank und im Cache
        
        Args:
            category: Kategorie zu aktualisieren
            **updates: Felder zum Aktualisieren (z.B. risk_min_eur=3000)
            
        Returns:
            True bei Erfolg
        """
        try:
            if not updates:
                return False
            
            # Build UPDATE query dynamically
            set_clauses = []
            values = []
            param_idx = 1
            
            for field, value in updates.items():
                set_clauses.append(f"{field} = ${param_idx}")
                values.append(value)
                param_idx += 1
            
            values.append(category)  # WHERE clause parameter
            
            query = f"""
                UPDATE compliance_risk_matrix
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE issue_category = ${param_idx}
            """
            
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(query, *values)
                
                if result == "UPDATE 1":
                    # Reload rules cache
                    await self.load_rules_from_db(force_reload=True)
                    logger.info(f"✅ Updated rule for category: {category}")
                    return True
                else:
                    logger.warning(f"No rule found for category: {category}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update rule {category}: {e}", exc_info=True)
            return False

