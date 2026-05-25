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
    Deterministische Score-Berechnung für Websites — Single Source of Truth (v2.0)

    GARANTIEN:
    - Gleiche Issues → Gleicher Score (100% deterministisch)
    - Keine externen API-Calls während Scoring
    - Keine Zeit-abhängigen Berechnungen
    - Keine Random-Elemente

    FORMEL v2.0:
    - Pro Säule: max(0, 100 - (critical × 25 + warning × 8))
    - Fehlendes Kern-Element (Impressum, Datenschutz, Cookie-Banner, A11y-Widget): 0
    - Gesamtscore: gewichteter Mittelwert über Säulen
    """

    FORMULA_VERSION = "v2.0"

    # Pillar-Gewichte (Summe = 1.0)
    PILLAR_WEIGHTS: Dict[str, float] = {
        "accessibility": 0.15,   # BFSG ab 06/2025 verpflichtend
        "gdpr":          0.25,   # Kernanforderung, höchste Bußgelder
        "legal":         0.20,   # Impressum/AGB = TMG-Pflicht
        "cookies":       0.20,   # TTDSG + EuGH C-673/17
        "security":      0.15,   # DSGVO Art. 32 technische Schutzmaßnahmen
        "shop":          0.05,   # Nur E-Commerce-relevant
    }

    # Severity-Abzüge pro Pillar-Issue (v2.0)
    SEVERITY_DEDUCTIONS = {
        "critical": 25,
        "warning":  8,
        "info":     0,
    }

    # Legacy-Gewichte (v1, für Rückwärtskompatibilität in alten Methoden)
    WEIGHTS = {
        "critical": -20,
        "warning": -5,
        "info": 0,
    }

    # Boni (DETERMINISTISCHE Bedingungen nur!)
    BONUSES = {
        "tcf_complete": 5,
        "gdpr_compliant": 3,
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
    def calculate_pillar_score(critical_count: int, warning_count: int, has_missing_core: bool = False) -> int:
        """
        Berechne Score für eine einzelne Compliance-Säule (v2.0).

        Args:
            critical_count: Anzahl Critical-Issues in dieser Säule
            warning_count:  Anzahl Warning-Issues in dieser Säule
            has_missing_core: True wenn das Kern-Element fehlt (Impressum, Datenschutz, etc.)

        Returns:
            int: Score 0-100
        """
        if has_missing_core:
            return 0
        score = 100 - (critical_count * ScoreCalculator.SEVERITY_DEDUCTIONS["critical"]
                       + warning_count * ScoreCalculator.SEVERITY_DEDUCTIONS["warning"])
        return max(0, score)

    @staticmethod
    def calculate_overall_score(pillar_scores: Dict[str, int]) -> int:
        """
        Berechne gewichteten Gesamt-Score aus Säulen-Scores (v2.0).

        Args:
            pillar_scores: {"gdpr": 100, "legal": 85, "cookies": 70, ...}

        Returns:
            int: Gewichteter Gesamtscore 0-100
        """
        total = 0.0
        total_weight = 0.0
        for pillar, weight in ScoreCalculator.PILLAR_WEIGHTS.items():
            score = pillar_scores.get(pillar, 100)  # Fehlende Säule = 100 (keine Issues)
            total += score * weight
            total_weight += weight
        if total_weight == 0:
            return 0
        return round(total / total_weight)

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
