"""
Issue Grouper
Gruppiert Compliance-Issues intelligent für professionelle Darstellung

Gruppierungs-Strategien:
1. Parent-Child: Hauptproblem mit Sub-Issues
2. Solution-Based: Issues mit gleicher Lösung
3. Legal-Basis: Issues mit gleichem Rechtsgrund
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict

from compliance_engine.jurisdictions import DEFAULT_JURISDICTION
from compliance_engine.rechtsgrundlagen import (
    AGB_KONTROLLE,
    ANBIETERKENNZEICHNUNG,
    BARRIEREFREIHEIT_TECHNISCH,
    COOKIE_EINWILLIGUNG,
    PREISANGABE,
    WIDERRUF,
    grundlage,
)

logger = logging.getLogger(__name__)


@dataclass
class IssueGroup:
    """Gruppierte Issues"""
    group_id: str
    group_type: str  # "parent-child", "solution-based", "legal-basis"
    parent_issue: Optional[Dict[str, Any]] = None
    sub_issues: List[Dict[str, Any]] = field(default_factory=list)
    
    # Gruppierungs-Metadaten
    category: str = ""
    severity: str = "warning"
    solution_type: str = "mixed"  # "code", "text", "guide", "widget", "mixed"
    has_unified_solution: bool = False
    
    # Statistiken
    total_risk_euro: int = 0
    completed_count: int = 0
    total_count: int = 0
    
    # Darstellungs-Hinweise
    title: str = ""
    description: str = ""
    icon: str = "📋"

    # Rechtsgrundlage der Karte. Gemessen am 16.10.2026: 41 von 41 Gruppenkarten
    # der letzten 40 Scans trugen keine, waehrend jeder Einzelbefund eine hatte
    # (1.185 von 1.185). Startseite und Erklaervideo versprechen "jeder Befund
    # mit Rechtsgrundlage"; die Karte ist das, was der Kunde zuerst sieht.
    legal_basis: str = ""


class IssueGrouper:
    """
    Intelligente Issue-Gruppierung
    
    Gruppiert Issues nach verschiedenen Kriterien für bessere UX
    """
    
    def __init__(self):
        """Initialisiert Grouper"""
        
        # Bekannte Gruppierungen
        self.known_groups = {
            # IMPRESSUM: Fehlende Impressum-Seite → Alle Sub-Issues gemeinsam
            "impressum_missing": {
                "title": "Impressum fehlt komplett",
                "description": "Es wurde kein Impressum gefunden. Alle Pflichtangaben müssen erstellt werden.",
                "category": "impressum",
                "solution_type": "text",
                "unified": True,
                "icon": "⚖️"
            },
            
            "impressum_incomplete": {
                "title": "Impressum unvollständig",
                "description": "Das Impressum existiert, aber einige Pflichtangaben fehlen.",
                "category": "impressum",
                "solution_type": "text",
                "unified": True,
                "icon": "⚖️"
            },
            
            # DATENSCHUTZ: Fehlende Datenschutzerklärung → Alle Sub-Issues gemeinsam
            "datenschutz_missing": {
                "title": "Datenschutzerklärung fehlt komplett",
                "description": "Es wurde keine Datenschutzerklärung gefunden. Alle Pflichtangaben müssen erstellt werden.",
                "category": "datenschutz",
                "solution_type": "text",
                "unified": True,
                "icon": "🔒"
            },
            
            "datenschutz_incomplete": {
                "title": "Datenschutzerklärung unvollständig",
                "description": "Die Datenschutzerklärung existiert, aber wichtige Angaben fehlen.",
                "category": "datenschutz",
                "solution_type": "text",
                "unified": True,
                "icon": "🔒"
            },
            
            # BARRIEREFREIHEIT: Alt-Text-Probleme
            "accessibility_images": {
                "title": "Bild-Barrierefreiheit",
                "description": "Mehrere Bilder haben fehlende oder unzureichende Alt-Texte.",
                "category": "accessibility",
                "solution_type": "code",
                "unified": False,  # Jedes Bild separat
                "icon": "🖼️"
            },
            
            "accessibility_contrast": {
                "title": "Kontrast-Probleme",
                "description": "Mehrere Elemente haben unzureichende Farbkontraste.",
                "category": "accessibility",
                "solution_type": "code",
                "unified": False,
                "icon": "🎨"
            },
            
            # COOKIES
            "cookie_consent": {
                "title": "Cookie-Consent fehlt",
                "description": "Es wurde kein Cookie-Banner oder Consent-Management gefunden.",
                "category": "cookies",
                "solution_type": "widget",
                "unified": True,
                "icon": "🍪"
            }
        }
    
    def _feste_rechtsgrundlage(self, category: str, jurisdiction: str) -> str:
        """Rueckfall je Kategorie, wenn kein Mitglied der Gruppe eine traegt.

        Nationale Anker kommen aus rechtsgrundlagen.py, damit der Rechtsraum
        mitwandert; die DSGVO-Angaben gelten unionsweit. Quellen, geoeffnet am
        18.10.2026: Art. 13 DSGVO (Informationspflicht bei Erhebung), § 5 DDG
        (Allgemeine Informationspflichten), § 25 TDDDG (Schutz der Privatsphaere
        bei Endeinrichtungen) mit Art. 6 Abs. 1 lit. a DSGVO (Einwilligung),
        Art. 246a § 1 Abs. 2 EGBGB (Widerrufsbelehrung), § 3 PAngV (Gesamtpreis),
        §§ 305 ff. BGB (AGB-Kontrolle).
        """
        if category == "datenschutz":
            return "DSGVO Art. 13"
        if category == "avv":
            return "DSGVO Art. 28"
        if category == "impressum":
            return grundlage(ANBIETERKENNZEICHNUNG, jurisdiction)
        if category in ("cookie", "cookies"):
            return grundlage(COOKIE_EINWILLIGUNG, jurisdiction) + ", DSGVO Art. 6 Abs. 1 lit. a"
        if category == "shop":
            # Eine Shop-Gruppe mischt Widerruf, Preisangabe und AGB; genannt
            # werden die drei Grundlagen, die shop_check.py selbst verwendet.
            teile = [grundlage(t, jurisdiction) for t in (WIDERRUF, PREISANGABE, AGB_KONTROLLE)]
            return ", ".join(t for t in teile if t)
        if category == "accessibility":
            return grundlage(BARRIEREFREIHEIT_TECHNISCH, jurisdiction, "Level A (1.1.1)")
        return ""

    def _rechtsgrundlage_der_gruppe(
        self,
        category: str,
        parent: Optional[Dict[str, Any]],
        members: List[Dict[str, Any]],
        jurisdiction: str,
    ) -> str:
        """Die Gruppe uebernimmt die Rechtsgrundlage ihres Hauptbefunds.

        Reihenfolge: Hauptbefund, dann das erste Mitglied mit Angabe, zuletzt
        der feste Rueckfall je Kategorie. Nie leer fuer eine bekannte Kategorie;
        eine unbekannte ohne jede Angabe wird protokolliert, nicht erfunden.
        """
        kandidaten = ([parent] if parent else []) + [m for m in members if m is not parent]
        for issue in kandidaten:
            basis = (issue.get("legal_basis") or "").strip()
            if basis:
                return basis
        basis = self._feste_rechtsgrundlage(category, jurisdiction)
        if not basis:
            logger.warning(
                "Gruppenkarte %r ohne Rechtsgrundlage: kein Mitglied traegt eine "
                "und es gibt keinen Rueckfall fuer diese Kategorie", category)
        return basis

    def group_issues(
        self,
        issues: List[Dict[str, Any]],
        jurisdiction: str = DEFAULT_JURISDICTION,
    ) -> Dict[str, Any]:
        """
        Gruppiert Issues intelligent
        
        Args:
            issues: Liste von Issues aus Scanner
        
        Returns:
            Dict mit:
            - "ungrouped_issues": Einzelne Issues
            - "issue_groups": Gruppierte Issues
            - "grouping_stats": Statistiken
        """
        logger.info(f"🔄 Gruppiere {len(issues)} Issues...")
        
        # Sortiere Issues nach Kategorie und is_missing-Flag
        categorized = defaultdict(list)
        for issue in issues:
            category = issue.get("category", "other")
            is_missing = issue.get("is_missing", False)
            
            key = f"{category}_{'missing' if is_missing else 'partial'}"
            categorized[key].append(issue)
        
        groups = []
        ungrouped = []
        
        # STRATEGIE 1: Gruppiere "is_missing" Issues
        for key, category_issues in categorized.items():
            category, status = key.rsplit("_", 1)
            
            if status == "missing" and len(category_issues) > 3:
                # Mehrere fehlende Issues einer Kategorie → Gruppe
                
                group_id = f"{category}_missing"
                group_config = self.known_groups.get(group_id, {})
                
                # Bestimme Parent-Issue (das Haupt-Issue)
                parent = self._find_parent_issue(category_issues)
                
                # Sub-Issues (alles außer Parent)
                sub_issues = [i for i in category_issues if i != parent]
                
                # Berechne Gesamt-Risiko
                total_risk = sum(i.get("risk_euro", 0) for i in category_issues)
                
                # Bestimme Severity (höchste)
                severities = [i.get("severity", "info") for i in category_issues]
                severity = self._highest_severity(severities)
                
                group = IssueGroup(
                    group_id=group_id,
                    group_type="parent-child",
                    parent_issue=parent,
                    sub_issues=sub_issues,
                    category=category,
                    severity=severity,
                    solution_type=group_config.get("solution_type", "mixed"),
                    has_unified_solution=group_config.get("unified", False),
                    total_risk_euro=total_risk,
                    total_count=len(category_issues),
                    completed_count=0,
                    title=group_config.get("title", f"{category.title()} Issues"),
                    description=group_config.get("description", "Mehrere verwandte Probleme"),
                    icon=group_config.get("icon", "📋"),
                    legal_basis=self._rechtsgrundlage_der_gruppe(
                        category, parent, category_issues, jurisdiction),
                )
                
                groups.append(asdict(group))
                
                logger.info(f"✅ Gruppe erstellt: {group_id} ({len(category_issues)} Issues)")
            
            else:
                # Zu wenige Issues oder nicht "missing" → Ungrouped
                ungrouped.extend(category_issues)
        
        # STRATEGIE 2: Gruppiere nach Lösung (z.B. alle Alt-Text-Issues)
        # Suche nach Issues mit ähnlichen Titeln
        alt_text_issues = [
            i for i in ungrouped 
            if "alt" in i.get("title", "").lower() and i.get("category") == "accessibility"
        ]
        
        if len(alt_text_issues) > 2:
            group = IssueGroup(
                group_id="accessibility_images",
                group_type="solution-based",
                parent_issue=None,
                sub_issues=alt_text_issues,
                category="accessibility",
                severity=self._highest_severity([i.get("severity", "info") for i in alt_text_issues]),
                solution_type="code",
                has_unified_solution=False,  # Jedes Bild separat
                total_risk_euro=sum(i.get("risk_euro", 0) for i in alt_text_issues),
                total_count=len(alt_text_issues),
                completed_count=0,
                title="Bild-Barrierefreiheit",
                description=f"{len(alt_text_issues)} Bilder haben fehlende oder unzureichende Alt-Texte",
                icon="🖼️",
                legal_basis=self._rechtsgrundlage_der_gruppe(
                    "accessibility", None, alt_text_issues, jurisdiction),
            )
            
            groups.append(asdict(group))
            
            # Entferne aus ungrouped
            ungrouped = [i for i in ungrouped if i not in alt_text_issues]
            
            logger.info(f"✅ Alt-Text-Gruppe erstellt: {len(alt_text_issues)} Issues")
        
        # Statistiken
        stats = {
            "total_issues": len(issues),
            "grouped_issues": sum(g["total_count"] for g in groups),
            "ungrouped_issues": len(ungrouped),
            "total_groups": len(groups),
            "grouping_rate": (sum(g["total_count"] for g in groups) / len(issues) * 100) if issues else 0
        }
        
        logger.info(f"✅ Gruppierung abgeschlossen: {len(groups)} Gruppen, {len(ungrouped)} einzeln ({stats['grouping_rate']:.1f}% gruppiert)")
        
        return {
            "ungrouped_issues": ungrouped,
            "issue_groups": groups,
            "grouping_stats": stats
        }
    
    def _find_parent_issue(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Findet das Haupt-Issue aus einer Liste
        
        Kriterien:
        - Enthält "fehlt" oder "missing" im Titel
        - Höchste Severity
        - Höchstes Risiko
        """
        # Suche nach "generischem" Issue
        for issue in issues:
            title = issue.get("title", "").lower()
            if "fehlt" in title or "missing" in title or "kein" in title:
                if any(keyword in title for keyword in ["link", "seite", "gefunden", "datenschutz", "impressum"]):
                    return issue
        
        # Fallback: Höchste Severity + Höchstes Risiko
        return max(issues, key=lambda i: (
            {"critical": 3, "warning": 2, "info": 1}.get(i.get("severity", "info"), 0),
            i.get("risk_euro", 0)
        ))
    
    def _highest_severity(self, severities: List[str]) -> str:
        """Gibt die höchste Severity zurück"""
        severity_order = ["critical", "warning", "info"]
        
        for sev in severity_order:
            if sev in severities:
                return sev
        
        return "info"
    
    def enrich_scan_results(
        self,
        scan_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reichert Scanner-Ergebnisse mit Gruppierungen an
        
        Args:
            scan_results: Original Scanner-Output
        
        Returns:
            Angereichertes Result mit issue_groups
        """
        issues = scan_results.get("issues", [])
        
        if not issues:
            return scan_results
        
        # Gruppiere Issues; der Rechtsraum des Scans bestimmt den nationalen
        # Anker der Rueckfall-Rechtsgrundlagen.
        grouped_data = self.group_issues(
            issues, scan_results.get("jurisdiction") or DEFAULT_JURISDICTION)
        
        # Füge zum Result hinzu
        scan_results["issue_groups"] = grouped_data["issue_groups"]
        scan_results["ungrouped_issues"] = grouped_data["ungrouped_issues"]
        scan_results["grouping_stats"] = grouped_data["grouping_stats"]
        
        # Behalte original issues bei (für Rückwärtskompatibilität)
        # scan_results["issues"] bleibt unverändert
        
        return scan_results

