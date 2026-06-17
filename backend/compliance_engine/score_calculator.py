"""
Zentrale Score-Berechnung für alle Compliance-Scores
Einzige Source of Truth zur Vermeidung von Inkonsistenzen

WICHTIG: Diese Funktion wird überall verwendet statt ad-hoc Berechnungen
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class PillarStatus:
    """
    Status einer Compliance-Säule (evidenz-basiert, v4.0).

    Leitprinzip: Compliance muss AKTIV nachgewiesen werden. Abwesenheit von
    erkannten Problemen ist NICHT automatisch "konform" — wenn eine Säule gar
    nicht geprüft werden konnte (Check abgestürzt / Seite nicht lesbar / nur
    per JS gerendert), ist sie UNVERIFIED und zählt NICHT als bestanden.
    """
    COMPLIANT = "compliant"          # Nachgewiesen konform (Pflichtelemente vorhanden + valide)
    PARTIAL = "partial"              # Vorhanden, aber mit Mängeln
    NON_COMPLIANT = "non_compliant"  # Kern-Element fehlt / nicht erfüllt
    UNVERIFIED = "unverified"        # Konnte nicht geprüft werden → 0 Credit, separat ausgewiesen


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

    FORMULA_VERSION = "v4.0"

    # ========================================================================
    # 4 SÄULEN — einzige kanonische Definition (Frontend + Backend identisch)
    #
    # Bewusste Design-Entscheidungen:
    #   - Sicherheit (CSP/HSTS/Header) ist KEINE eigene Säule, sondern
    #     technische Schutzmaßnahme nach DSGVO Art. 32 → fällt in "gdpr".
    #   - Shop-Themen (Widerruf, Preisangaben, AGB-Shop) sind rechtliche
    #     Pflichttexte → fallen in "legal". Shop-Checks werden ohnehin nur
    #     bei erkanntem Shop erzeugt (detect_shop), sonst irrelevant.
    #   - Alle 4 Säulen werden GLEICH gewichtet (siehe calculate_overall_score),
    #     damit der Gesamtscore für den Nutzer nachvollziehbar bleibt.
    # ========================================================================
    PILLAR_IDS = ["accessibility", "gdpr", "legal", "cookies"]

    # Kategorie → Säule. Reihenfolge = Priorität (erste Übereinstimmung gewinnt).
    # Default für unbekannte Kategorien: "legal" (rechtliche Auffangsäule).
    PILLAR_CATEGORY_KEYWORDS = [
        ("accessibility", [
            "barriere", "accessibility", "wcag", "aria", "alt_text", "alt-text",
            "kontrast", "contrast", "tastat",
        ]),
        ("cookies", [
            "cookie", "consent", "tcf", "tracking", "ttdsg",
        ]),
        ("gdpr", [
            "datenschutz", "dsgvo", "gdpr", "privacy", "personenbezogen",
            "datenverarbeitung", "avv",
            # Sicherheit = DSGVO Art. 32 (technische Schutzmaßnahmen)
            "security", "sicherheit", "csp", "content-security", "hsts",
            "x-frame", "header", "ssl", "tls", "https",
        ]),
        ("legal", [
            "impressum", "agb", "legal", "rechtlich", "tmg", "uwg",
            "widerruf", "preisangaben", "preisangabe", "pangv", "preis",
            # Shop-Pflichttexte zählen rechtlich
            "shop", "contact", "kontakt", "social_media", "social",
            "urheberrecht", "markenrecht",
        ]),
    ]

    # Anzeigenamen der Säulen (für Reports/Logs)
    PILLAR_LABELS = {
        "accessibility": "Barrierefreiheit",
        "gdpr":          "Datenschutz",
        "legal":         "Rechtssichere Texte",
        "cookies":       "Cookie-Compliance",
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

    # Aufwands-Klassifizierung (v4.0) für Bearbeitungshinweise/Priorisierung
    EFFORT_LOW = "gering"      # automatisch / per KI behebbar
    EFFORT_MEDIUM = "mittel"   # manuell, aber überschaubar
    EFFORT_EXPERT = "experte"  # rechtliche Beratung / vollständige Erstellung nötig

    @staticmethod
    def classify_effort(severity: str, auto_fixable: bool = False, is_missing: bool = False) -> str:
        """
        Klassifiziere den Bearbeitungsaufwand eines Issues (deterministisch).

        - auto_fixable                      → gering   (Complyo/KI kann es erledigen)
        - komplett fehlendes Kern-Element   → experte  (z.B. Impressum/Datenschutz neu erstellen)
        - critical                          → experte
        - warning                           → mittel
        - sonst (info)                      → gering
        """
        if auto_fixable:
            return ScoreCalculator.EFFORT_LOW
        if is_missing and severity == "critical":
            return ScoreCalculator.EFFORT_EXPERT
        if severity == "critical":
            return ScoreCalculator.EFFORT_EXPERT
        if severity == "warning":
            return ScoreCalculator.EFFORT_MEDIUM
        return ScoreCalculator.EFFORT_LOW

    @staticmethod
    def categorize(category: str) -> str:
        """
        Ordne eine Issue-Kategorie genau einer der 4 Säulen zu.

        Garantie: JEDE Kategorie landet in genau einer Säule (kein Issue
        fällt durchs Raster). Unbekannte Kategorien → "legal".

        Args:
            category: Roh-Kategorie eines Issues (z.B. "security", "shop")

        Returns:
            str: Säulen-ID aus PILLAR_IDS
        """
        cat = (category or "").lower()
        for pillar_id, keywords in ScoreCalculator.PILLAR_CATEGORY_KEYWORDS:
            if any(keyword in cat for keyword in keywords):
                return pillar_id
        return "legal"  # rechtliche Auffangsäule

    @staticmethod
    def calculate_overall_score(pillar_scores: Dict[str, int]) -> int:
        """
        Berechne Gesamt-Score als GLEICH gewichteten Mittelwert der 4 Säulen (v3.0).

        Bewusst gleich gewichtet: ein Säulen-Wert von 100,100,100,70 ergibt so
        (100+100+100+70)/4 = 93 — für den Nutzer nachvollziehbar. Eine schwache
        Säule senkt den Gesamtscore proportional, statt ihn (wie früher über eine
        globale Issue-Zählung) unerklärlich zu drücken.

        Args:
            pillar_scores: {"accessibility": 100, "gdpr": 100, "legal": 100, "cookies": 70}
                           ⚠️ v4.0: Eine fehlende Säule wird als 0 gewertet
                           (Compliance muss NACHGEWIESEN werden — Abwesenheit ist
                           kein Nachweis). Normalerweise liefert die Engine ohnehin
                           für alle 4 Säulen einen Wert, sodass der Default nicht greift.

        Returns:
            int: Gesamtscore 0-100
        """
        scores = [
            pillar_scores.get(pillar, 0)
            for pillar in ScoreCalculator.PILLAR_IDS
        ]
        if not scores:
            return 100
        return round(sum(scores) / len(scores))

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
    def calculate_pillar_scores(issues: List[ComplianceIssue]) -> Dict[str, int]:
        """
        Berechne Scores pro Compliance-Säule (v3.0) — 4 Säulen, vollständige
        Kategorie-Abdeckung über ScoreCalculator.categorize().

        Säulen (IDs identisch zu Frontend):
        - accessibility  (Barrierefreiheit / BFSG)
        - gdpr           (Datenschutz / DSGVO inkl. Sicherheit Art. 32)
        - legal          (Impressum, AGB, Shop-Pflichttexte, UWG …)
        - cookies        (Cookie-Banner / TTDSG / TCF)

        Jede Säule: max(0, 100 - (critical×25 + warning×8)),
        fehlendes Kern-Element (is_missing) → 0.

        Returns:
            Dict mit pillar_id → score (0-100, int). Säulen ohne Issues = 100.
        """
        buckets: Dict[str, list] = {pillar: [] for pillar in ScoreCalculator.PILLAR_IDS}

        for issue in issues:
            pillar = ScoreCalculator.categorize(issue.category)
            buckets[pillar].append(issue)

        pillar_scores: Dict[str, int] = {}
        for pillar_id, pillar_issues in buckets.items():
            critical_count = sum(1 for i in pillar_issues if i.severity == "critical")
            warning_count = sum(1 for i in pillar_issues if i.severity == "warning")
            # is_missing wird von vielen Checks auch auf einzelne Warning-Sub-Findings
            # gesetzt ("Widerrufsmöglichkeit fehlt", "Ablehnen-Button fehlt" …). Nur ein
            # komplett fehlendes KERN-Element (Impressum, Datenschutz, Cookie-Banner,
            # A11y-Widget) soll die Säule auf 0 ziehen — solche Issues sind immer
            # critical. Sonst kollabiert jede Säule mit einer einzelnen "fehlt"-Warnung.
            has_missing_core = any(
                getattr(i, "is_missing", False) and i.severity == "critical"
                for i in pillar_issues
            )
            pillar_scores[pillar_id] = ScoreCalculator.calculate_pillar_score(
                critical_count=critical_count,
                warning_count=warning_count,
                has_missing_core=has_missing_core,
            )

        return pillar_scores

    @staticmethod
    def _derive_pillar_status(score: int, critical: int, warning: int, has_missing_core: bool) -> str:
        """Leite den anzeigbaren Säulen-Status aus den gezählten Issues ab (v4.0)."""
        if has_missing_core or score == 0:
            return PillarStatus.NON_COMPLIANT
        if critical or warning:
            return PillarStatus.PARTIAL
        return PillarStatus.COMPLIANT

    @staticmethod
    def compute_with_status(
        issues: List[ComplianceIssue],
        unverified_pillars: "set[str] | None" = None,
    ) -> Dict[str, Any]:
        """
        Evidenz-basierte Score-Berechnung (v4.0) — liefert zusätzlich pro Säule
        einen Status (compliant / partial / non_compliant / unverified).

        UNVERIFIED-Prinzip: Wenn der zuständige Check für eine Säule NICHT sauber
        durchlaufen ist (z.B. Exception, Seite nur per JS, Timeout) und deshalb
        KEINE Evidenz vorliegt, gilt die Säule als "ungeprüft" → Score 0, Status
        UNVERIFIED. So kann eine nicht prüfbare Säule nie als 100 (bestanden)
        durchrutschen. Liegen dennoch Issues vor, gewinnen die Issues (echte Evidenz).

        Args:
            issues: alle erkannten ComplianceIssues
            unverified_pillars: Säulen-IDs, deren Primär-Check nicht auswertbar war

        Returns:
            {
                "overall_score": int,
                "pillar_scores": {pillar_id: int, ...},
                "pillar_status": {pillar_id: PillarStatus, ...}
            }
        """
        unverified = set(unverified_pillars or [])
        buckets: Dict[str, list] = {pillar: [] for pillar in ScoreCalculator.PILLAR_IDS}
        for issue in issues:
            buckets[ScoreCalculator.categorize(issue.category)].append(issue)

        pillar_scores: Dict[str, int] = {}
        pillar_status: Dict[str, str] = {}
        for pillar_id, pillar_issues in buckets.items():
            critical_count = sum(1 for i in pillar_issues if i.severity == "critical")
            warning_count = sum(1 for i in pillar_issues if i.severity == "warning")
            has_missing_core = any(
                getattr(i, "is_missing", False) and i.severity == "critical"
                for i in pillar_issues
            )

            # Ungeprüft UND keine Evidenz → 0 Credit, transparent als "ungeprüft"
            if pillar_id in unverified and not pillar_issues:
                pillar_scores[pillar_id] = 0
                pillar_status[pillar_id] = PillarStatus.UNVERIFIED
                continue

            score = ScoreCalculator.calculate_pillar_score(
                critical_count=critical_count,
                warning_count=warning_count,
                has_missing_core=has_missing_core,
            )
            pillar_scores[pillar_id] = score
            pillar_status[pillar_id] = ScoreCalculator._derive_pillar_status(
                score, critical_count, warning_count, has_missing_core
            )

        return {
            "overall_score": ScoreCalculator.calculate_overall_score(pillar_scores),
            "pillar_scores": pillar_scores,
            "pillar_status": pillar_status,
        }

    @staticmethod
    def compute(issues: List[ComplianceIssue]) -> Dict[str, Any]:
        """
        Einziger Einstiegspunkt für vollständige Score-Berechnung (v4.0).

        Liefert Säulen-Scores, Säulen-Status UND den daraus gleichgewichtet
        gemittelten Gesamtscore in EINEM konsistenten Aufruf — so können Gesamt
        und Säulen nie auseinanderlaufen.

        Returns:
            {
                "overall_score": int,                  # = Mittelwert der Säulen
                "pillar_scores": {pillar_id: int, ...},# 4 Säulen
                "pillar_status": {pillar_id: str, ...} # evidenz-basierter Status
            }
        """
        return ScoreCalculator.compute_with_status(issues)
    
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

        pillar_scores = ScoreCalculator.calculate_pillar_scores(issues)
        overall = ScoreCalculator.calculate_overall_score(pillar_scores)

        return {
            "overall_score": overall,
            "base_issues": {
                "critical_count": len(critical),
                "warning_count": len(warning),
                "info_count": len(info),
                "total_issues": len(issues)
            },
            "pillar_scores": pillar_scores,
            "formula_used": (
                "Gesamtscore = Mittelwert(4 Säulen); "
                "Säule = max(0, 100 - (critical*25 + warning*8))"
            )
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
