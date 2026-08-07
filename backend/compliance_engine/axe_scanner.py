"""
axe-core Scanner Integration
Vollständige WCAG 2.1 Prüfung mit axe-core via Playwright

Features:
- axe-core 4.x Integration
- Vollständige WCAG 2.1 Level A/AA Abdeckung
- Multi-Page-Scanning
- Issue-zu-Feature-Mapping
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

from compliance_engine.axe_translations import uebersetze as uebersetze_axe

# axe-core wird lokal gebundelt und zur Scan-Zeit injiziert — kein externes CDN
# (SPOF vermieden; vendored axe-core 4.11.4).
_AXE_CORE_PATH = os.path.join(os.path.dirname(__file__), "vendor", "axe.min.js")
try:
    with open(_AXE_CORE_PATH, "r", encoding="utf-8") as _axe_f:
        AXE_CORE_JS = _axe_f.read()
except OSError as _axe_err:  # pragma: no cover - Deploy-Fehlkonfiguration
    AXE_CORE_JS = ""
    logger.error(f"axe-core Bundle nicht gefunden unter {_AXE_CORE_PATH}: {_axe_err}")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AxeViolation:
    """Ein einzelner axe-core Verstoß"""
    id: str
    impact: str  # critical, serious, moderate, minor
    description: str
    help: str
    help_url: str
    tags: List[str]
    nodes: List[Dict[str, Any]]
    
    # Mapping zu internem Feature
    feature_id: Optional[str] = None
    wcag_criteria: List[str] = field(default_factory=list)


@dataclass
class AxeScanResult:
    """Ergebnis eines axe-core Scans"""
    url: str
    timestamp: str
    violations: List[AxeViolation]
    passes: int
    incomplete: int
    inapplicable: int
    
    # Statistiken
    total_violations: int = 0
    by_impact: Dict[str, int] = field(default_factory=dict)
    by_wcag: Dict[str, int] = field(default_factory=dict)

    # Im Browser verifizierte Kontrast-Reparaturen (siehe kontrast_verifizierer).
    # Entstehen waehrend des Scans, weil sie die geoeffnete Seite brauchen: der
    # Vorschlag wird eingespielt und nachgemessen. Ein zweiter Browserlauf
    # spaeter waere dieselbe Arbeit ein zweites Mal.
    kontrast_fixes: Optional[Dict[str, Any]] = None
    # Ebenso die Struktur-Reparatur (role=main, viewport, iframe-Titel …).
    # Laeuft im selben Lauf, weil sie denselben geoeffneten Baum braucht.
    struktur_fixes: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "timestamp": self.timestamp,
            "violations": [asdict(v) for v in self.violations],
            "passes": self.passes,
            "incomplete": self.incomplete,
            "inapplicable": self.inapplicable,
            "kontrast_fixes": self.kontrast_fixes,
            "struktur_fixes": self.struktur_fixes,
            "total_violations": self.total_violations,
            "by_impact": self.by_impact,
            "by_wcag": self.by_wcag
        }


# =============================================================================
# axe Rule to Feature Mapping
# =============================================================================

# =============================================================================
# WCAG-Stufen -> axe-Tags
# =============================================================================
#
# axe-Tags sind FLACH, nicht hierarchisch. `wcag21aa` bezeichnet ausschliesslich
# die Regeln, die WCAG 2.1 auf Stufe AA NEU eingefuehrt hat — nicht die aus 2.0
# uebernommenen. Wer nur diesen einen Tag setzt, prueft einen Bruchteil.
#
# Genau das war hier der Fall: `runOnly: [wcag21aa, best-practice]` liess
# `image-alt`, `link-name`, `label`, `color-contrast`, `button-name`,
# `html-has-lang` und die gesamte ARIA-Familie aus — allesamt WCAG 2.0. Auf
# spedition-mahn.de meldete der Scan 35 Befunde, samt und sonders
# "best-practice", und uebersah 13x link-name, 7x color-contrast, 6x
# nested-interactive (serious) sowie 3x aria-required-parent (critical).
# Das Feature-Mapping unten kennt diese Regeln laengst — sie konnten nur nie
# feuern. Der Fehler war der Filter, nicht das Modell.
#
# EN 301 549 (und damit das BFSG) verweist auf WCAG 2.1 Stufe AA. Das schliesst
# 2.0 A und AA vollstaendig ein; die Mengen sind deshalb kumulativ. WCAG 2.2
# bleibt bewusst draussen: rechtlich nicht gefordert, und ein Befund, den
# niemand einfordern kann, gehoert nicht in einen Pflichten-Report.
WCAG_TAG_MENGEN: Dict[str, List[str]] = {
    "wcag2a":   ["wcag2a"],
    "wcag2aa":  ["wcag2a", "wcag2aa"],
    "wcag21a":  ["wcag2a", "wcag21a"],
    "wcag21aa": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
}


def axe_tags_fuer(wcag_level: str, mit_best_practice: bool = True) -> List[str]:
    """Vollstaendige Tag-Liste fuer eine WCAG-Stufe.

    `best-practice` bleibt drin, weil Landmark- und Ueberschriften-Befunde
    echten Nutzen haben — sie muessen im Bericht aber als Empfehlung kenntlich
    sein und nicht als Rechtspflicht (siehe `ist_rechtspflicht`).
    """
    tags = list(WCAG_TAG_MENGEN.get(wcag_level, WCAG_TAG_MENGEN["wcag21aa"]))
    if mit_best_practice:
        tags.append("best-practice")
    return tags


def ist_rechtspflicht(tags: List[str]) -> bool:
    """Faellt dieser Befund unter WCAG 2.1 AA — oder ist er nur Empfehlung?

    Der Unterschied ist der Kern der Glaubwuerdigkeit: `region` und
    `heading-order` sind best-practice und keine BFSG-Pflicht. Sie als Verstoss
    zu verkaufen waere genau die Angstmacherei, die man einem
    Compliance-Anbieter am schnellsten uebelnimmt.
    """
    rechtlich = set(WCAG_TAG_MENGEN["wcag21aa"])
    return any(t in rechtlich for t in tags)


AXE_RULE_TO_FEATURE: Dict[str, str] = {
    # Alt-Text (WCAG 1.1.1)
    "image-alt": "ALT_TEXT",
    "input-image-alt": "ALT_TEXT",
    "area-alt": "ALT_TEXT",
    "object-alt": "ALT_TEXT",
    "svg-img-alt": "ALT_TEXT",
    "role-img-alt": "ALT_TEXT",
    
    # Sprache (WCAG 3.1.1, 3.1.2) — der Patch-Builder setzt lang mechanisch,
    # die Regeln hatten aber keine Feature-Zuordnung und galten damit als
    # "nicht auto-fixable", obwohl genau dieser Fix existiert.
    "html-has-lang": "LANGUAGE",
    "html-lang-valid": "LANGUAGE",
    "html-xml-lang-mismatch": "LANGUAGE",
    "valid-lang": "LANGUAGE",

    # Kontrast (WCAG 1.4.3, 1.4.11)
    "color-contrast": "CONTRAST",
    "color-contrast-enhanced": "CONTRAST",
    "link-in-text-block": "CONTRAST",
    
    # Form Labels (WCAG 1.3.1, 3.3.2, 4.1.2)
    "label": "FORM_LABELS",
    "label-title-only": "FORM_LABELS",
    "input-button-name": "FORM_LABELS",
    "select-name": "FORM_LABELS",
    "form-field-multiple-labels": "FORM_LABELS",
    
    # Landmarks (WCAG 1.3.1, 2.4.1)
    "landmark-banner-is-top-level": "LANDMARKS",
    "landmark-complementary-is-top-level": "LANDMARKS",
    "landmark-contentinfo-is-top-level": "LANDMARKS",
    "landmark-main-is-top-level": "LANDMARKS",
    "landmark-no-duplicate-banner": "LANDMARKS",
    "landmark-no-duplicate-contentinfo": "LANDMARKS",
    "landmark-no-duplicate-main": "LANDMARKS",
    "landmark-one-main": "LANDMARKS",
    "landmark-unique": "LANDMARKS",
    "region": "LANDMARKS",
    "bypass": "LANDMARKS",
    
    # Keyboard (WCAG 2.1.1, 2.1.2)
    "accesskeys": "KEYBOARD",
    "focus-order-semantics": "KEYBOARD",
    "focusable-content": "KEYBOARD",
    "focusable-disabled": "KEYBOARD",
    "focusable-no-name": "KEYBOARD",
    "frame-focusable-content": "KEYBOARD",
    "scrollable-region-focusable": "KEYBOARD",
    "tabindex": "KEYBOARD",
    
    # Hinweis: 2.4.7 (focus-visible) existiert als axe-Regel NICHT —
    # das fruehere Mapping war tot und taeuschte Abdeckung vor.

    # ARIA (WCAG 4.1.2)
    "aria-allowed-attr": "ARIA",
    "aria-allowed-role": "ARIA",
    "aria-command-name": "ARIA",
    "aria-dialog-name": "ARIA",
    "aria-hidden-body": "ARIA",
    "aria-hidden-focus": "ARIA",
    "aria-input-field-name": "ARIA",
    "aria-meter-name": "ARIA",
    "aria-progressbar-name": "ARIA",
    "aria-required-attr": "ARIA",
    "aria-required-children": "ARIA",
    "aria-required-parent": "ARIA",
    # Verschachtelte Bedienelemente (Link im Button o. ae.) — auf echten
    # WordPress-Seiten haeufig und bisher ohne Zuordnung.
    "nested-interactive": "ARIA",
    "aria-roledescription": "ARIA",
    "aria-roles": "ARIA",
    "aria-text": "ARIA",
    "aria-toggle-field-name": "ARIA",
    "aria-tooltip-name": "ARIA",
    "aria-valid-attr-value": "ARIA",
    "aria-valid-attr": "ARIA",
    "button-name": "ARIA",
    "link-name": "ARIA",
    
    # Headings (WCAG 1.3.1, 2.4.6)
    "heading-order": "HEADINGS",
    "empty-heading": "HEADINGS",
    "page-has-heading-one": "HEADINGS",
    
    # Media (WCAG 1.2.x)
    "audio-caption": "MEDIA",
    "video-caption": "MEDIA",
    "video-description": "MEDIA",
    "no-autoplay-audio": "MEDIA",
}

# WCAG Kriterium Mapping
AXE_TAG_TO_WCAG: Dict[str, str] = {
    "wcag111": "1.1.1",
    "wcag121": "1.2.1",
    "wcag122": "1.2.2",
    "wcag123": "1.2.3",
    "wcag124": "1.2.4",
    "wcag125": "1.2.5",
    "wcag131": "1.3.1",
    "wcag132": "1.3.2",
    "wcag133": "1.3.3",
    "wcag134": "1.3.4",
    "wcag135": "1.3.5",
    "wcag141": "1.4.1",
    "wcag142": "1.4.2",
    "wcag143": "1.4.3",
    "wcag144": "1.4.4",
    "wcag145": "1.4.5",
    "wcag1410": "1.4.10",
    "wcag1411": "1.4.11",
    "wcag1412": "1.4.12",
    "wcag1413": "1.4.13",
    "wcag211": "2.1.1",
    "wcag212": "2.1.2",
    "wcag214": "2.1.4",
    "wcag221": "2.2.1",
    "wcag222": "2.2.2",
    "wcag231": "2.3.1",
    "wcag241": "2.4.1",
    "wcag242": "2.4.2",
    "wcag243": "2.4.3",
    "wcag244": "2.4.4",
    "wcag245": "2.4.5",
    "wcag246": "2.4.6",
    "wcag247": "2.4.7",
    "wcag251": "2.5.1",
    "wcag252": "2.5.2",
    "wcag253": "2.5.3",
    "wcag254": "2.5.4",
    "wcag311": "3.1.1",
    "wcag312": "3.1.2",
    "wcag321": "3.2.1",
    "wcag322": "3.2.2",
    "wcag331": "3.3.1",
    "wcag332": "3.3.2",
    "wcag333": "3.3.3",
    "wcag334": "3.3.4",
    "wcag411": "4.1.1",
    "wcag412": "4.1.2",
    "wcag413": "4.1.3",
}


# =============================================================================
# axe-core Scanner
# =============================================================================

class AxeScanner:
    """
    axe-core Scanner für vollständige WCAG-Prüfung
    
    Nutzt Playwright um axe-core im Browser auszuführen.
    """
    
    def __init__(self):
        self.browser = None
        self.context = None
        logger.info("🔧 AxeScanner initialisiert")
    
    async def scan_page(
        self,
        url: str,
        wcag_level: str = "wcag21aa",
        timeout: int = 30000,
        mit_kontrast_fixes: bool = False,
    ) -> AxeScanResult:
        """
        Scannt eine einzelne Seite mit axe-core
        
        Args:
            url: URL der zu scannenden Seite
            wcag_level: WCAG Level (wcag2a, wcag2aa, wcag21aa)
            timeout: Timeout in Millisekunden
            
        Returns:
            AxeScanResult mit allen Violations
        """
        logger.info(f"🔍 axe-core Scan: {url}")
        
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright nicht installiert. Bitte 'pip install playwright' ausführen.")
            return self._create_empty_result(url, "Playwright nicht installiert")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Seite laden. "networkidle" ist bewusst NICHT das primaere
                # Kriterium: Seiten mit dauerhaftem Polling, Chat-Widgets oder
                # Werbung erreichen nie Netzwerkruhe und liefen damit garantiert
                # in den Timeout ("Timeout 30000ms exceeded"). DOM-ready reicht
                # fuer axe; danach geben wir Netzwerkruhe eine kurze Chance,
                # ohne den Scan daran scheitern zu lassen.
                await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                try:
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    # Kein Fehler: die Seite laedt dauerhaft nach — axe laeuft
                    # auf dem Stand von jetzt.
                    logger.info(f"axe-core: {url} erreicht keine Netzwerkruhe — scanne den aktuellen Stand")
                
                # Injiziere axe-core (lokal gebundelt)
                await page.add_script_tag(content=AXE_CORE_JS)
                
                # Warte kurz auf Script-Laden
                await page.wait_for_function("typeof axe !== 'undefined'", timeout=5000)
                
                # Führe axe-core aus. Die Tag-Menge wird aufgeloest, nicht
                # durchgereicht — axe-Tags sind flach (siehe WCAG_TAG_MENGEN).
                axe_config = {
                    "runOnly": {
                        "type": "tag",
                        "values": axe_tags_fuer(wcag_level)
                    }
                }
                logger.info(f"axe-core Regelsatz: {', '.join(axe_config['runOnly']['values'])}")
                
                results = await page.evaluate(f"""
                    async () => {{
                        const results = await axe.run(document, {json.dumps(axe_config)});
                        return results;
                    }}
                """)
                
                ergebnis = self._parse_results(url, results)

                # Kontrast-Reparatur solange die Seite offen ist. Danach ist
                # das Dokument veraendert (eingespieltes CSS) — deshalb erst
                # NACH dem regulaeren Parsen, und nichts darf danach noch
                # gemessen werden.
                if mit_kontrast_fixes:
                    # Struktur ZUERST: sie setzt Attribute am Baum, der
                    # Kontrast-Schritt spielt danach CSS ein und veraendert die
                    # Farben. Andersherum wuerde die Struktur-Nachmessung auf
                    # einer bereits umgefaerbten Seite laufen.
                    try:
                        from compliance_engine.struktur_verifizierer import (
                            verifizierte_struktur_fixes,
                        )
                        ergebnis.struktur_fixes = await verifizierte_struktur_fixes(page)
                    except Exception as e:
                        logger.warning(f"Struktur-Fixes uebersprungen: {e}")
                    try:
                        from compliance_engine.kontrast_verifizierer import (
                            verifizierte_kontrast_fixes,
                        )
                        ergebnis.kontrast_fixes = await verifizierte_kontrast_fixes(page)
                    except Exception as e:
                        # Fail-open wie der Rest des Scans: ohne Kontrast-Fixes
                        # ist der Scan schlechter, aber nicht kaputt.
                        logger.warning(f"Kontrast-Fixes uebersprungen: {e}")

                return ergebnis
            
            except Exception as e:
                logger.error(f"❌ axe-core Scan fehlgeschlagen: {e}")
                return self._create_empty_result(url, str(e))
            
            finally:
                await browser.close()
    
    async def scan_multiple_pages(
        self,
        urls: List[str],
        wcag_level: str = "wcag21aa",
        max_concurrent: int = 5
    ) -> List[AxeScanResult]:
        """
        Scannt mehrere Seiten parallel
        
        Args:
            urls: Liste von URLs
            wcag_level: WCAG Level
            max_concurrent: Maximale parallele Scans
            
        Returns:
            Liste von AxeScanResults
        """
        logger.info(f"🔍 axe-core Multi-Page Scan: {len(urls)} Seiten")
        
        results = []
        
        # Batchweise scannen
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            tasks = [self.scan_page(url, wcag_level) for url in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Scan-Fehler: {result}")
                else:
                    results.append(result)
        
        return results
    
    def _parse_results(self, url: str, raw_results: Dict[str, Any]) -> AxeScanResult:
        """Parst axe-core Ergebnisse in internes Format"""
        
        violations = []
        by_impact = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        by_wcag: Dict[str, int] = {}
        
        for violation in raw_results.get("violations", []):
            # Feature-ID ermitteln
            rule_id = violation.get("id", "")
            feature_id = AXE_RULE_TO_FEATURE.get(rule_id)
            
            # WCAG-Kriterien extrahieren
            wcag_criteria = []
            for tag in violation.get("tags", []):
                if tag.startswith("wcag"):
                    wcag_id = AXE_TAG_TO_WCAG.get(tag)
                    if wcag_id:
                        wcag_criteria.append(wcag_id)
                        by_wcag[wcag_id] = by_wcag.get(wcag_id, 0) + 1
            
            # Impact zählen
            impact = violation.get("impact", "moderate")
            by_impact[impact] = by_impact.get(impact, 0) + 1
            
            violations.append(AxeViolation(
                id=rule_id,
                impact=impact,
                description=violation.get("description", ""),
                help=violation.get("help", ""),
                help_url=violation.get("helpUrl", ""),
                tags=violation.get("tags", []),
                nodes=violation.get("nodes", []),
                feature_id=feature_id,
                wcag_criteria=wcag_criteria
            ))
        
        return AxeScanResult(
            url=url,
            timestamp=datetime.now().isoformat(),
            violations=violations,
            passes=len(raw_results.get("passes", [])),
            incomplete=len(raw_results.get("incomplete", [])),
            inapplicable=len(raw_results.get("inapplicable", [])),
            total_violations=len(violations),
            by_impact=by_impact,
            by_wcag=by_wcag
        )
    
    def _create_empty_result(self, url: str, error: str) -> AxeScanResult:
        """Erstellt leeres Ergebnis bei Fehler"""
        return AxeScanResult(
            url=url,
            timestamp=datetime.now().isoformat(),
            violations=[],
            passes=0,
            incomplete=0,
            inapplicable=0,
            total_violations=0,
            by_impact={"error": error}
        )
    
    def convert_to_structured_issues(
        self,
        scan_result: AxeScanResult
    ) -> List[Dict[str, Any]]:
        """
        Konvertiert axe-core Violations zu strukturierten Issues
        für die Feature-Engine
        
        Args:
            scan_result: AxeScanResult
            
        Returns:
            Liste von Issue-Dictionaries
        """
        issues = []

        # Pro Regel die betroffenen Knoten deckeln, damit ein einzelner
        # Massen-Verstoß (z. B. 80 Elemente mit zu wenig Kontrast) nicht den
        # Score und die Risiko-Summe sprengt.
        MAX_NODES_PER_RULE = 10

        for violation in scan_result.violations:
            extra = max(0, len(violation.nodes) - MAX_NODES_PER_RULE)
            # Trennt Rechtspflicht von Empfehlung. Vorher trug JEDER Befund
            # "BFSG §12" — auch `region` und `heading-order`, die reine
            # axe-Empfehlungen sind. Einem Compliance-Anbieter nimmt man
            # nichts schneller uebel als eine erfundene Pflicht.
            pflicht = ist_rechtspflicht(violation.tags)
            for idx, node in enumerate(violation.nodes[:MAX_NODES_PER_RULE]):
                severity = self._impact_to_severity(violation.impact)
                if not pflicht:
                    # Empfehlungen erzeugen keinen Rechtsdruck: hoechstens
                    # Hinweis-Rang, kein Bussgeldrisiko in der Summe.
                    severity = "info" if severity in ("critical", "high") else severity

                # target ist eine Liste von Selektoren → ersten als String verwenden
                target = node.get("target") or []
                selector = target[0] if target else ""

                wcag_str = ", ".join(violation.wcag_criteria) if violation.wcag_criteria else "Name, Role, Value"
                failure = (node.get("failureSummary") or violation.help or "").strip()

                # axe-core liefert help/description nur auf Englisch — in einer
                # deutschsprachigen Anwendung standen Saetze wie "All page content
                # should be contained by landmarks" unuebersetzt im Report.
                titel_de, beschreibung_de = uebersetze_axe(
                    violation.id, violation.help, violation.description
                )

                description = beschreibung_de
                if idx == 0 and extra > 0:
                    description = f"{description} (und {extra} weitere Element(e) mit demselben Problem)"

                issues.append({
                    "category": "barrierefreiheit",
                    "severity": severity,
                    "title": titel_de or violation.id,
                    "description": description,
                    "risk_euro": self._impact_to_risk_euro(violation.impact) if pflicht else 0,
                    "recommendation": failure,
                    "legal_basis": (
                        f"WCAG 2.1 ({wcag_str}), BFSG §12" if pflicht
                        else "Empfehlung (axe best-practice) — nicht aus WCAG 2.1 AA gefordert"
                    ),
                    "auto_fixable": violation.feature_id in ["ALT_TEXT", "CONTRAST", "FOCUS", "LANDMARKS"],
                    "is_missing": False,
                    "element_html": node.get("html", ""),
                    "rechtspflicht": pflicht,
                    "metadata": {
                        "source": "axe-core",
                        "rechtspflicht": pflicht,
                        "axe_rule_id": violation.id,
                        "axe_impact": violation.impact,
                        "axe_help_url": violation.help_url,
                        "axe_tags": violation.tags,
                        "wcag_criteria": violation.wcag_criteria,
                        "feature_id": violation.feature_id,
                        "selector": selector,
                        "page_url": scan_result.url,
                        "extra_affected": extra if idx == 0 else 0,
                    },
                })

        return issues
    
    def _impact_to_severity(self, impact: str) -> str:
        """Konvertiert axe Impact zu interner Severity"""
        mapping = {
            "critical": "critical",
            "serious": "error",
            "moderate": "warning",
            "minor": "info"
        }
        return mapping.get(impact, "warning")

    def _impact_to_risk_euro(self, impact: str) -> int:
        """Schätzt das Bußgeld-/Abmahnrisiko je axe-Impact (für Score & Reporting)."""
        mapping = {
            "critical": 2000,
            "serious": 1500,
            "moderate": 800,
            "minor": 300,
        }
        return mapping.get(impact, 800)


# Globale Instanz
axe_scanner = AxeScanner()


# =============================================================================
# Convenience Function
# =============================================================================

async def run_axe_scan(
    url: str,
    wcag_level: str = "wcag21aa",
    mit_kontrast_fixes: bool = True,
) -> Tuple[AxeScanResult, List[Dict[str, Any]]]:
    """
    Führt axe-core Scan durch und gibt Ergebnisse zurück
    
    Args:
        url: URL zum Scannen
        wcag_level: WCAG Level
        
    Returns:
        Tuple von (AxeScanResult, strukturierte Issues)
    """
    result = await axe_scanner.scan_page(url, wcag_level, mit_kontrast_fixes=mit_kontrast_fixes)
    issues = axe_scanner.convert_to_structured_issues(result)
    
    logger.info(f"✅ axe-core Scan abgeschlossen: {result.total_violations} Violations, {len(issues)} Issues")
    
    return result, issues
