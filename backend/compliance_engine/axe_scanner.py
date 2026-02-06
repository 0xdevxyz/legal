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
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# axe-core CDN URL (wird in Playwright injiziert)
AXE_CORE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.4/axe.min.js"


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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "timestamp": self.timestamp,
            "violations": [asdict(v) for v in self.violations],
            "passes": self.passes,
            "incomplete": self.incomplete,
            "inapplicable": self.inapplicable,
            "total_violations": self.total_violations,
            "by_impact": self.by_impact,
            "by_wcag": self.by_wcag
        }


# =============================================================================
# axe Rule to Feature Mapping
# =============================================================================

AXE_RULE_TO_FEATURE: Dict[str, str] = {
    # Alt-Text (WCAG 1.1.1)
    "image-alt": "ALT_TEXT",
    "input-image-alt": "ALT_TEXT",
    "area-alt": "ALT_TEXT",
    "object-alt": "ALT_TEXT",
    "svg-img-alt": "ALT_TEXT",
    "role-img-alt": "ALT_TEXT",
    
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
    
    # Focus (WCAG 2.4.7)
    "focus-visible": "FOCUS",
    
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
        timeout: int = 30000
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
                # Lade Seite
                await page.goto(url, timeout=timeout, wait_until="networkidle")
                
                # Injiziere axe-core
                await page.add_script_tag(url=AXE_CORE_CDN)
                
                # Warte kurz auf Script-Laden
                await page.wait_for_function("typeof axe !== 'undefined'", timeout=5000)
                
                # Führe axe-core aus
                axe_config = {
                    "runOnly": {
                        "type": "tag",
                        "values": [wcag_level, "best-practice"]
                    }
                }
                
                results = await page.evaluate(f"""
                    async () => {{
                        const results = await axe.run(document, {json.dumps(axe_config)});
                        return results;
                    }}
                """)
                
                # Parse Ergebnisse
                return self._parse_results(url, results)
            
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
        
        for violation in scan_result.violations:
            # Für jeden betroffenen Node ein Issue
            for node in violation.nodes:
                severity = self._impact_to_severity(violation.impact)
                
                issues.append({
                    "id": f"{violation.id}_{hash(node.get('target', []))}"[:32],
                    "title": violation.help,
                    "description": violation.description,
                    "category": "barrierefreiheit",
                    "severity": severity,
                    "feature_id": violation.feature_id,
                    "wcag_criteria": violation.wcag_criteria,
                    "legal_basis": f"WCAG 2.1 ({', '.join(violation.wcag_criteria)})",
                    "page_url": scan_result.url,
                    "selector": node.get("target", [""])[0] if node.get("target") else "",
                    "element_html": node.get("html", ""),
                    "recommendation": node.get("failureSummary", ""),
                    "auto_fixable": violation.feature_id in ["ALT_TEXT", "CONTRAST", "FOCUS", "LANDMARKS"],
                    "metadata": {
                        "axe_rule_id": violation.id,
                        "axe_impact": violation.impact,
                        "axe_help_url": violation.help_url,
                        "axe_tags": violation.tags
                    }
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


# Globale Instanz
axe_scanner = AxeScanner()


# =============================================================================
# Convenience Function
# =============================================================================

async def run_axe_scan(
    url: str,
    wcag_level: str = "wcag21aa"
) -> Tuple[AxeScanResult, List[Dict[str, Any]]]:
    """
    Führt axe-core Scan durch und gibt Ergebnisse zurück
    
    Args:
        url: URL zum Scannen
        wcag_level: WCAG Level
        
    Returns:
        Tuple von (AxeScanResult, strukturierte Issues)
    """
    result = await axe_scanner.scan_page(url, wcag_level)
    issues = axe_scanner.convert_to_structured_issues(result)
    
    logger.info(f"✅ axe-core Scan abgeschlossen: {result.total_violations} Violations, {len(issues)} Issues")
    
    return result, issues
