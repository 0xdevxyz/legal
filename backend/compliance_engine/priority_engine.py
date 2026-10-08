"""
Priority Engine - Berechnet Prioritäten für Compliance-Issues
Sortiert Issues nach Wichtigkeit basierend auf Risiko, Aufwand und Häufigkeit
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IssuePriority:
    """Prioritäts-Score für ein Issue"""
    issue_id: str
    priority_score: float  # 0-100
    priority_label: str  # 'critical', 'high', 'medium', 'low'
    risk_score: float
    effort_score: float
    frequency_score: float
    recommendation: str

class PriorityEngine:
    """Berechnet Prioritäten für Issues"""
    
    def __init__(self):
        self.risk_weights = {
            'critical': 100,
            'warning': 50,
            'info': 20
        }
        
        self.category_frequency = {
            'impressum': 95,  # Sehr häufig abgemahnt
            'datenschutz': 90,
            'cookies': 85,
            'ssl': 80,
            'barrierefreiheit': 70,
            'agb': 60,
            'responsive': 30
        }
    
    def calculate_fix_priority(
        self,
        issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Berechnet Prioritäten für alle Issues und sortiert sie
        
        Args:
            issues: Liste von Compliance-Issues
            
        Returns:
            Sortierte Liste mit Prioritäts-Informationen
        """
        prioritized = []
        
        for issue in issues:
            priority = self._calculate_issue_priority(issue)
            
            # Erweitere Issue um Prioritäts-Info
            issue_with_priority = {
                **issue,
                'priority_score': priority.priority_score,
                'priority_label': priority.priority_label,
                'priority_badge': self._get_priority_badge(priority.priority_label),
                'recommendation': priority.recommendation
            }
            
            prioritized.append(issue_with_priority)
        
        # Sortiere nach Priorität (höchste zuerst)
        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return prioritized
    
    def get_quick_wins(
        self,
        issues: List[Dict[str, Any]],
        max_effort_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Findet "Quick Wins" - Issues mit hohem Impact und geringem Aufwand
        
        Args:
            issues: Liste von Issues
            max_effort_minutes: Maximaler Aufwand in Minuten
            
        Returns:
            Liste von Quick-Win Issues
        """
        quick_wins = []
        
        for issue in issues:
            effort = self._estimate_effort_minutes(issue)
            impact = self._calculate_impact_score(issue)
            
            # Quick Win: Geringer Aufwand, hoher Impact
            if effort <= max_effort_minutes and impact >= 50:
                quick_wins.append({
                    **issue,
                    'estimated_minutes': effort,
                    'impact_score': impact,
                    'score_improvement': self._estimate_score_improvement(issue)
                })
        
        # Sortiere nach Score-Verbesserung
        quick_wins.sort(key=lambda x: x['score_improvement'], reverse=True)
        
        return quick_wins
    
    # ==================== Private Methoden ====================
    
    def _calculate_issue_priority(self, issue: Dict[str, Any]) -> IssuePriority:
        """Berechnet Priorität für ein einzelnes Issue"""
        
        # 1. Risiko-Score (0-100)
        risk_score = self._calculate_risk_score(issue)
        
        # 2. Aufwands-Score (0-100, niedrig = einfach)
        effort_score = self._calculate_effort_score(issue)
        
        # 3. Häufigkeits-Score (0-100, wie oft wird abgemahnt?)
        frequency_score = self._calculate_frequency_score(issue)
        
        # Gewichtete Gesamt-Priorität
        # Risiko: 50%, Häufigkeit: 30%, Aufwand: 20% (invertiert)
        priority_score = (
            risk_score * 0.5 +
            frequency_score * 0.3 +
            (100 - effort_score) * 0.2  # Wenig Aufwand = höhere Priorität
        )
        
        # Prioritäts-Label
        priority_label = self._get_priority_label(priority_score)
        
        # Empfehlung
        recommendation = self._generate_recommendation(
            priority_label,
            risk_score,
            effort_score
        )
        
        return IssuePriority(
            issue_id=issue.get('id', 'unknown'),
            priority_score=priority_score,
            priority_label=priority_label,
            risk_score=risk_score,
            effort_score=effort_score,
            frequency_score=frequency_score,
            recommendation=recommendation
        )
    
    def _calculate_risk_score(self, issue: Dict[str, Any]) -> float:
        """Berechnet Risiko-Score basierend auf Severity und Euro-Risiko"""
        severity = issue.get('severity', 'info')
        base_score = self.risk_weights.get(severity, 20)
        
        # Frueher kam hier ein Bonus aus dem Eurobetrag des Befunds dazu.
        # Der Betrag war erfunden (siehe rangstufe.py); ein fehlendes
        # Pflichtelement wiegt stattdessen schwerer als ein Teilmangel.
        if issue.get('is_missing'):
            base_score = min(100, base_score + 20)
        
        return base_score
    
    def _calculate_effort_score(self, issue: Dict[str, Any]) -> float:
        """Schätzt Aufwand (0=einfach, 100=schwer)"""
        category = issue.get('category', 'unknown')
        
        # Aufwands-Schätzungen pro Kategorie
        effort_map = {
            'ssl': 20,  # Oft nur Zertifikat installieren
            'impressum': 30,  # Link setzen + Text einfügen
            'cookies': 60,  # Cookie-Banner integration
            'datenschutz': 50,  # Generator + Link
            'barrierefreiheit': 80,  # Viele Änderungen nötig
            'agb': 40,  # Generator + Link
            'responsive': 70  # CSS-Anpassungen
        }
        
        return effort_map.get(category, 50)  # Default: mittel
    
    def _calculate_frequency_score(self, issue: Dict[str, Any]) -> float:
        """Berechnet Häufigkeit von Abmahnungen für diese Kategorie"""
        category = issue.get('category', 'unknown')
        return self.category_frequency.get(category, 50)
    
    def _get_priority_label(self, priority_score: float) -> str:
        """Konvertiert Score zu Label"""
        if priority_score >= 80:
            return 'critical'
        elif priority_score >= 60:
            return 'high'
        elif priority_score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def _get_priority_badge(self, label: str) -> Dict[str, str]:
        """Gibt Badge-Informationen für UI zurück"""
        badges = {
            'critical': {
                'text': '⚡ Hohe Priorität',
                'color': 'red',
                'icon': '⚡'
            },
            'high': {
                'text': '🔥 Wichtig',
                'color': 'orange',
                'icon': '🔥'
            },
            'medium': {
                'text': '📌 Normal',
                'color': 'yellow',
                'icon': '📌'
            },
            'low': {
                'text': '📎 Niedrig',
                'color': 'gray',
                'icon': '📎'
            }
        }
        return badges.get(label, badges['medium'])
    
    def _generate_recommendation(
        self,
        priority_label: str,
        risk_score: float,
        effort_score: float
    ) -> str:
        """Generiert Handlungsempfehlung"""
        if priority_label == 'critical':
            return "Sofort beheben! Hohes Abmahnrisiko."
        elif priority_label == 'high':
            if effort_score < 40:
                return "Schnell umsetzen - geringer Aufwand, hoher Nutzen."
            else:
                return "Zeitnah beheben - wichtig für Compliance."
        elif priority_label == 'medium':
            return "In den nächsten Wochen beheben."
        else:
            return "Bei Gelegenheit optimieren."
    
    def _calculate_impact_score(self, issue: Dict[str, Any]) -> float:
        """Berechnet Impact-Score (wie stark verbessert Fix den Compliance-Score?)"""
        severity = issue.get('severity', 'info')
        
        impact_map = {
            'critical': 85,
            'warning': 60,
            'info': 30
        }
        
        return impact_map.get(severity, 50)
    
    def _estimate_effort_minutes(self, issue: Dict[str, Any]) -> int:
        """Schätzt Aufwand in Minuten"""
        category = issue.get('category', 'unknown')
        
        effort_map = {
            'ssl': 30,
            'impressum': 15,
            'cookies': 60,
            'datenschutz': 45,
            'barrierefreiheit': 120,
            'agb': 30,
            'responsive': 90
        }
        
        return effort_map.get(category, 60)
    
    def _estimate_score_improvement(self, issue: Dict[str, Any]) -> int:
        """Schätzt Score-Verbesserung durch Fix"""
        severity = issue.get('severity', 'info')
        
        improvement_map = {
            'critical': 15,
            'warning': 10,
            'info': 5
        }
        
        return improvement_map.get(severity, 5)

# Global Instance
priority_engine = PriorityEngine()

