"""
Zentrale Score-Berechnung für alle Compliance-Scores
Einzige Source of Truth zur Vermeidung von Inkonsistenzen

WICHTIG: Diese Funktion wird überall verwendet statt ad-hoc Berechnungen
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ComplianceIssue:
    """Standard Issue Dataclass (muss mit bestehender Definition abgeglichen werden)"""
    severity: str  # "critical", "warning", "info"
    category: str  # "datenschutz", "cookie", "tcf", etc.
    title: str
    legal_risk_score: float = 0.0
    risk_euro: float = 0.0


class ScoreCalculator:
    """
    Deterministische Score-Berechnung für Websites
    
    GARANTIEN:
    - Gleiche Issues → Gleicher Score (100% deterministisch)
    - Keine externen API-Calls während Scoring
    - Keine Zeit-abhängigen Berechnungen
    - Keine Random-Elemente
    """
    
    # Scoring-Gewichte (einmalig definiert)
    WEIGHTS = {
        "critical": -20,      # Ein Critical Issue = -20 Punkte
        "warning": -5,         # Ein Warning = -5 Punkte
        "info": 0              # Info-Level zählt nicht
    }
    
    # Boni (DETERMINISTISCHE Bedingungen nur!)
    BONUSES = {
        "tcf_complete": 5,     # TCF vollständig implementiert UND geprüft
        "gdpr_compliant": 3,   # Alle DSGVO-Anforderungen erfüllt
    }
    
    @staticmethod
    def calculate_compliance_score(issues: List[ComplianceIssue]) -> float:
        """
        Berechne Overall Compliance Score (0-100)
        
        Formel:
            1. Base Score = 100
            2. Für jedes Critical Issue: -20 Punkte
            3. Für jedes Warning Issue: -5 Punkte
            4. Info-Issues nicht berücksichtigt
            5. Boni nur bei OFFLINE-geprüften Status-Issues
            6. Capped bei 0-100 Range
        
        Args:
            issues: Liste von ComplianceIssue Objekten
        
        Returns:
            float: Score 0-100 (gerundet auf Ganzzahlen)
        
        Examples:
            - 0 Issues → 100%
            - 2 Critical + 1 Warning → 100 - 40 - 5 = 55%
            - 2 Critical + TCF Complete → 100 - 40 + 5 = 65%
        """
        if not issues:
            return 100.0
        
        # 1. Basis-Score
        base_score = 100.0
        
        # 2. Issues abziehen
        for issue in issues:
            severity_weight = ScoreCalculator.WEIGHTS.get(issue.severity, 0)
            base_score += severity_weight
            logger.debug(f"Issue: {issue.category} ({issue.severity}) → {severity_weight} pts")
        
        # 3. Boni (DETERMINISTISCHE Bedingungen!)
        # TCF-Bonus: Nur wenn TCF-Check als "ok" in den Issues existiert (offline-geprüft)
        if ScoreCalculator._has_tcf_compliant_status(issues):
            base_score += ScoreCalculator.BONUSES["tcf_complete"]
            logger.info("✅ TCF Bonus: +5 Punkte (offline geprüft)")
        
        # 4. Cappen auf 0-100
        final_score = max(0, min(100, base_score))
        
        # 5. Runden für Konsistenz
        return round(final_score)
    
    @staticmethod
    def _has_tcf_compliant_status(issues: List[ComplianceIssue]) -> bool:
        """
        Prüft ob TCF als COMPLIANT OFFLINE geprüft wurde
        
        NICHT: External API Call
        JA: Issue in der Liste mit status "ok"
        """
        for issue in issues:
            if issue.category == "tcf":
                # Wenn TCF-Issue da ist aber NICHT als warning/critical
                # → dann wurde es offline geprüft und ist ok
                if issue.severity == "info" or issue.severity not in ["critical", "warning"]:
                    return True
        
        return False
    
    @staticmethod
    def calculate_pillar_scores(issues: List[ComplianceIssue]) -> Dict[str, float]:
        """
        Berechne Scores pro Compliance-Säule
        
        Säulen:
        - Datenschutz (DSGVO, TTDSG)
        - Cookies (TTDSG Cookies, TCF)
        - Impressum/AGB
        - Barrierefreiheit (BFSG)
        
        Returns:
            Dict mit pillar_name → score (0-100)
        """
        pillars = {
            "datenschutz": [],      # datenschutz, dsgvo, ttdsg, legality
            "cookies": [],          # cookie, tcf, tracking
            "impressum": [],        # impressum, agb, datenschutz-erklaerung
            "barrierefreiheit": []  # accessibility, aria, alt_text
        }
        
        # Issues in Säulen sortieren
        for issue in issues:
            category = issue.category.lower()
            
            if any(c in category for c in ["datenschutz", "dsgvo", "ttdsg", "legality"]):
                pillars["datenschutz"].append(issue)
            elif any(c in category for c in ["cookie", "tcf", "tracking"]):
                pillars["cookies"].append(issue)
            elif any(c in category for c in ["impressum", "agb", "datenschutz-erklaerung"]):
                pillars["impressum"].append(issue)
            elif any(c in category for c in ["accessibility", "aria", "alt_text", "contrast"]):
                pillars["barrierefreiheit"].append(issue)
        
        # Score pro Säule
        pillar_scores = {}
        for pillar_name, pillar_issues in pillars.items():
            if not pillar_issues:
                pillar_scores[pillar_name] = 100.0  # Keine Issues → 100%
            else:
                pillar_scores[pillar_name] = ScoreCalculator.calculate_compliance_score(pillar_issues)
        
        return pillar_scores
    
    @staticmethod
    def get_score_breakdown(issues: List[ComplianceIssue]) -> Dict[str, Any]:
        """
        Detaillierte Score-Aufschlüsselung für Debugging
        
        Returns:
            {
                "overall_score": 75,
                "base_issues": {
                    "critical_count": 2,
                    "warning_count": 1,
                    "info_count": 3
                },
                "base_score": 75,
                "bonuses_applied": ["tcf_complete"],
                "pillar_scores": {...},
                "formula_used": "100 - (critical*20 + warning*5) + bonuses"
            }
        """
        critical = [i for i in issues if i.severity == "critical"]
        warning = [i for i in issues if i.severity == "warning"]
        info = [i for i in issues if i.severity == "info"]
        
        base_score = 100 - (len(critical) * 20 + len(warning) * 5)
        
        bonuses = []
        if ScoreCalculator._has_tcf_compliant_status(issues):
            bonuses.append("tcf_complete")
            base_score += 5
        
        final_score = ScoreCalculator.calculate_compliance_score(issues)
        
        return {
            "overall_score": final_score,
            "base_issues": {
                "critical_count": len(critical),
                "warning_count": len(warning),
                "info_count": len(info),
                "total_issues": len(issues)
            },
            "base_score": max(0, min(100, base_score)),
            "bonuses_applied": bonuses,
            "pillar_scores": ScoreCalculator.calculate_pillar_scores(issues),
            "formula_used": "100 - (critical*20 + warning*5) + bonuses [capped 0-100]"
        }


# ============================================================================
# MIGRATION: Alle alten Funktionen auf diese Funktion umleiten
# ============================================================================

def old_calculate_score_scanner(critical_issues: int, warning_issues: int, tcf_bonus: bool = False) -> float:
    """
    DEPRECATED: Alt Funktion aus scanner.py Zeile 188
    Nutze stattdessen: ScoreCalculator.calculate_compliance_score()
    """
    logger.warning("DEPRECATED: old_calculate_score_scanner() - Nutze ScoreCalculator.calculate_compliance_score()")
    
    score = max(0, 100 - (critical_issues * 20 + warning_issues * 5))
    
    # TCF-Bonus NUR wenn offline-geprüft!
    if tcf_bonus:
        score = min(100, score + 5)
    
    return float(score)


def old_calculate_score_engine(issues: List[ComplianceIssue]) -> float:
    """
    DEPRECATED: Alt Funktion aus engine.py Zeile 464
    Nutze stattdessen: ScoreCalculator.calculate_compliance_score()
    """
    logger.warning("DEPRECATED: old_calculate_score_engine() - Nutze ScoreCalculator.calculate_compliance_score()")
    
    if not issues:
        return 100.0
    
    total_risk = sum(issue.legal_risk_score for issue in issues)
    max_risk = len(issues) * 1.0
    
    return max(0, 100 - (total_risk / max_risk * 100))
