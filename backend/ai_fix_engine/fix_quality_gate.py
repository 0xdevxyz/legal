"""
Fix Quality Gate
3-stufige automatische Prüfpipeline für KI-generierte Fixes.

Stufe 1 — Syntax-Validator  (< 200ms): HTML/CSS/JS, ARIA-Korrektheit, keine gefährlichen Konstrukte
Stufe 2 — Re-Scanner        (< 5s):    Vorher/Nachher Score, Issue tatsächlich behoben?
Stufe 3 — Regression        (< 10s):   Keine neuen Issues durch den Fix entstanden?

Ergebnis:
    Alle 3 grün → fix["quality_gate_status"] = "validated"
    Mind. 1 rot  → fix["quality_gate_status"] = "pending_review"

Task 3 — Quality Process Implementation
"""

import re
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result Data Classes
# ---------------------------------------------------------------------------

@dataclass
class StageResult:
    stage: int
    name: str
    passed: bool
    duration_ms: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityGateResult:
    final_status: str  # "validated" | "pending_review"
    stage_results: List[StageResult]
    total_duration_ms: int
    summary: str


# ---------------------------------------------------------------------------
# Dangerous patterns that must never appear in a fix
# ---------------------------------------------------------------------------

_DANGEROUS_HTML = re.compile(
    r"(<script\b(?!.*type=['\"]application/ld\+json)[^>]*>.*?</script>)|"
    r"(on\w+\s*=\s*['\"])|"
    r"(javascript\s*:)|"
    r"(<iframe\b)|"
    r"(<object\b)|"
    r"(<embed\b)",
    re.IGNORECASE | re.DOTALL,
)

_DANGEROUS_JS = re.compile(
    r"(eval\s*\()|"
    r"(document\.write\s*\()|"
    r"(innerHTML\s*=)|"
    r"(\.exec\s*\()",
    re.IGNORECASE,
)

_BROKEN_ARIA = re.compile(
    r'role\s*=\s*["\'][^"\']*["\']',
    re.IGNORECASE,
)

_VALID_ARIA_ROLES = {
    "alert", "alertdialog", "application", "article", "banner", "button",
    "cell", "checkbox", "columnheader", "combobox", "complementary",
    "contentinfo", "definition", "dialog", "directory", "document",
    "feed", "figure", "form", "grid", "gridcell", "group", "heading",
    "img", "link", "list", "listbox", "listitem", "log", "main",
    "marquee", "math", "menu", "menubar", "menuitem", "menuitemcheckbox",
    "menuitemradio", "navigation", "none", "note", "option", "presentation",
    "progressbar", "radio", "radiogroup", "region", "row", "rowgroup",
    "rowheader", "scrollbar", "search", "searchbox", "separator",
    "slider", "spinbutton", "status", "switch", "tab", "table", "tablist",
    "tabpanel", "term", "textbox", "timer", "toolbar", "tooltip", "tree",
    "treegrid", "treeitem",
}


class FixQualityGate:
    """
    3-stufiges Quality Gate für KI-generierte Fixes.

    Usage:
        gate = FixQualityGate()
        result = await gate.run(fix_dict, original_html)
        fix_dict["quality_gate_status"] = result.final_status
        fix_dict["quality_gate_log"]    = [vars(s) for s in result.stage_results]
    """

    async def run(
        self,
        fix: Dict[str, Any],
        original_html: str = "",
    ) -> QualityGateResult:
        """
        Führt alle 3 Stufen aus und gibt ein QualityGateResult zurück.
        Bei einem kritischen Fehler in Stufe 1 werden Stufen 2+3 übersprungen.
        """
        t_start = time.time()
        stages: List[StageResult] = []

        s1 = await self._stage1_syntax(fix)
        stages.append(s1)

        if not s1.passed:
            total_ms = int((time.time() - t_start) * 1000)
            return QualityGateResult(
                final_status="pending_review",
                stage_results=stages,
                total_duration_ms=total_ms,
                summary=f"Stage 1 (Syntax) fehlgeschlagen: {'; '.join(s1.errors)}",
            )

        s2 = await self._stage2_rescan(fix, original_html)
        stages.append(s2)

        s3 = await self._stage3_regression(fix)
        stages.append(s3)

        all_passed = all(s.passed for s in stages)
        total_ms = int((time.time() - t_start) * 1000)

        failed_names = [s.name for s in stages if not s.passed]
        verified = bool(s2.details.get("verified"))
        if all_passed and verified:
            summary = "Alle 3 Stufen bestanden + re-scan-verifiziert — Fix validiert"
            status = "validated"
        elif all_passed:
            summary = "Syntax+Regression OK, aber nicht re-scan-verifiziert — manuelle Prüfung erforderlich"
            status = "pending_review"
        else:
            summary = f"Fehlgeschlagen: {', '.join(failed_names)} — manuelle Prüfung erforderlich"
            status = "pending_review"

        return QualityGateResult(
            final_status=status,
            stage_results=stages,
            total_duration_ms=total_ms,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Stage 1 — Syntax & Safety
    # ------------------------------------------------------------------

    async def _stage1_syntax(self, fix: Dict[str, Any]) -> StageResult:
        t = time.time()
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        code_content = self._extract_code(fix)

        if not code_content:
            return StageResult(
                stage=1,
                name="Syntax & Safety",
                passed=True,
                duration_ms=int((time.time() - t) * 1000),
                warnings=["Kein Code-Inhalt gefunden — Syntax-Check übersprungen"],
                details={"code_length": 0},
            )

        # Dangerous HTML constructs
        if _DANGEROUS_HTML.search(code_content):
            errors.append("Gefährliche HTML-Konstrukte gefunden (script/iframe/onerror/…)")

        # Dangerous JS
        if _DANGEROUS_JS.search(code_content):
            errors.append("Gefährliche JS-Konstrukte gefunden (eval/innerHTML/…)")

        # ARIA role validation
        for match in _BROKEN_ARIA.finditer(code_content):
            role_str = match.group(0)
            role_val_match = re.search(r'["\']([^"\']+)["\']', role_str)
            if role_val_match:
                role_val = role_val_match.group(1).strip().lower()
                if role_val not in _VALID_ARIA_ROLES:
                    errors.append(f"Ungültiger ARIA-Role-Wert: '{role_val}'")

        # Unclosed HTML tags heuristic
        open_tags = re.findall(r"<([a-zA-Z][a-zA-Z0-9]*)\b[^/]*>", code_content)
        close_tags = re.findall(r"</([a-zA-Z][a-zA-Z0-9]*)>", code_content)
        void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input",
                     "link", "meta", "param", "source", "track", "wbr"}
        non_void_open = [t.lower() for t in open_tags if t.lower() not in void_tags]
        if len(non_void_open) > len(close_tags) + 3:
            warnings.append(
                f"Möglicherweise nicht geschlossene Tags: {len(non_void_open)} offen, {len(close_tags)} geschlossen"
            )

        details["code_length"] = len(code_content)
        details["open_tags"] = len(non_void_open)
        details["close_tags"] = len(close_tags)

        return StageResult(
            stage=1,
            name="Syntax & Safety",
            passed=len(errors) == 0,
            duration_ms=int((time.time() - t) * 1000),
            errors=errors,
            warnings=warnings,
            details=details,
        )

    # ------------------------------------------------------------------
    # Stage 2 — Re-Scanner (Vorher/Nachher)
    # ------------------------------------------------------------------

    async def _stage2_rescan(
        self, fix: Dict[str, Any], original_html: str
    ) -> StageResult:
        t = time.time()
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        if not original_html:
            return StageResult(
                stage=2,
                name="Re-Scanner",
                passed=True,
                duration_ms=int((time.time() - t) * 1000),
                warnings=["Kein original_html übergeben — Fix nicht verifizierbar"],
                details={"verified": False, "applied_in_place": False},
            )

        try:
            from bs4 import BeautifulSoup

            original_score = self._quick_accessibility_score(original_html)

            # Apply fix to HTML (echt in-place, wenn moeglich)
            patched_html, applied_in_place = self._apply_fix_to_html(fix, original_html)
            patched_score = self._quick_accessibility_score(patched_html)

            details["original_score"] = original_score
            details["patched_score"] = patched_score
            details["score_delta"] = patched_score - original_score
            details["applied_in_place"] = applied_in_place
            # Verifiziert nur, wenn der Fix echt in-place angewandt wurde UND
            # den Score messbar verbessert. Angehaengte Snippets gelten NIE als
            # verifiziert (Vorher/Nachher waere sonst aussagelos).
            details["verified"] = bool(applied_in_place and patched_score > original_score)

            if not applied_in_place:
                warnings.append(
                    "Fix nur angehaengt statt in-place angewandt — nicht re-scan-verifiziert"
                )

            if patched_score < original_score - 2:
                errors.append(
                    f"Fix verschlechtert den Score: {original_score} → {patched_score}"
                )
            elif patched_score <= original_score:
                warnings.append(
                    f"Score unverändert oder minimal schlechter: {original_score} → {patched_score}"
                )

        except ImportError:
            warnings.append("BeautifulSoup nicht verfügbar — Re-Scanner übersprungen")
        except Exception as e:
            warnings.append(f"Re-Scanner Fehler (nicht blockierend): {e}")

        return StageResult(
            stage=2,
            name="Re-Scanner",
            passed=len(errors) == 0,
            duration_ms=int((time.time() - t) * 1000),
            errors=errors,
            warnings=warnings,
            details=details,
        )

    # ------------------------------------------------------------------
    # Stage 3 — Regression
    # ------------------------------------------------------------------

    async def _stage3_regression(self, fix: Dict[str, Any]) -> StageResult:
        t = time.time()
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        code_content = self._extract_code(fix)

        if not code_content:
            return StageResult(
                stage=3,
                name="Regression",
                passed=True,
                duration_ms=int((time.time() - t) * 1000),
                warnings=["Kein Code — Regression-Test übersprungen"],
            )

        # Fixture-Regression: prüft gegen bekannte Problemmuster
        regression_checks = [
            (
                r'<img\b(?![^>]*\balt\s*=)[^>]*>',
                "Fix fügt <img> ohne alt-Attribut ein",
            ),
            (
                r'<(button|a)\b(?![^>]*(?:aria-label|aria-labelledby|title))[^>]*>\s*</\1>',
                "Fix fügt leeres interaktives Element ohne Label ein",
            ),
            (
                r'<(table)\b(?![^>]*role)[^>]*>(?!.*?<(th|caption))',
                "Fix fügt Tabelle ohne Header oder Caption ein",
            ),
            (
                r'color:\s*#([0-9a-fA-F]{3,6})\s*;[^}]*background(?:-color)?:\s*#([0-9a-fA-F]{3,6})',
                "Mögliches Kontrast-Problem in Fix-CSS erkannt",
            ),
        ]

        for pattern, message in regression_checks:
            if re.search(pattern, code_content, re.IGNORECASE | re.DOTALL):
                warnings.append(message)

        # Placeholder detection
        if re.search(r'\[PLACEHOLDER\]|\[TODO\]|\[YOUR_', code_content, re.IGNORECASE):
            errors.append("Fix enthält unausgefüllte Platzhalter")

        details["regression_checks_run"] = len(regression_checks)
        details["warnings_found"] = len(warnings)

        return StageResult(
            stage=3,
            name="Regression",
            passed=len(errors) == 0,
            duration_ms=int((time.time() - t) * 1000),
            errors=errors,
            warnings=warnings,
            details=details,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_code(self, fix: Dict[str, Any]) -> str:
        """Extrahiert den Code-Inhalt aus verschiedenen Fix-Strukturen."""
        data = fix.get("data", fix)

        candidates = [
            data.get("fix_code", ""),
            data.get("code", ""),
            data.get("html_fix", ""),
            data.get("css_fix", ""),
            data.get("js_fix", ""),
            data.get("implementation", ""),
        ]

        # Also check nested code_changes dict
        code_changes = data.get("code_changes", {})
        if isinstance(code_changes, dict):
            candidates.extend(code_changes.values())

        return "\n".join(str(c) for c in candidates if c)

    def _quick_accessibility_score(self, html: str) -> int:
        """
        Schnelle, heuristische Accessibility-Bewertung für Vorher/Nachher-Vergleich.
        Gibt eine Zahl 0–100 zurück (höher = besser).
        """
        score = 100
        if not html:
            return score

        # Penalize missing alt on images
        imgs = re.findall(r'<img\b[^>]*>', html, re.IGNORECASE)
        for img in imgs:
            if 'alt=' not in img.lower():
                score -= 5

        # Penalize missing lang on html
        if '<html' in html.lower() and 'lang=' not in html.lower():
            score -= 10

        # Penalize empty links/buttons
        empty_interactive = re.findall(
            r'<(a|button)\b[^>]*>\s*</\1>', html, re.IGNORECASE
        )
        score -= len(empty_interactive) * 5

        # Penalize missing form labels
        inputs = re.findall(r'<input\b[^>]*>', html, re.IGNORECASE)
        labels = re.findall(r'<label\b', html, re.IGNORECASE)
        if len(inputs) > len(labels):
            score -= min((len(inputs) - len(labels)) * 3, 15)

        return max(0, score)

    def _apply_fix_to_html(self, fix: Dict[str, Any], original_html: str) -> Tuple[str, bool]:
        """
        Wendet einen Fix auf das HTML an und meldet, ob das ECHT in-place
        geschah (Attribute an ein vorhandenes Element gemergt) oder nur als
        Fallback angehaengt wurde. Nur ein echtes In-place-Apply erlaubt einen
        belastbaren Vorher/Nachher-Vergleich (siehe _stage2_rescan.verified).
        """
        data = fix.get("data", fix)
        fix_code = data.get("fix_code") or data.get("html_fix") or data.get("code")
        if not fix_code or len(fix_code) < 10:
            return original_html, False

        try:
            from bs4 import BeautifulSoup

            frag = BeautifulSoup(fix_code, "html.parser")
            new_el = frag.find(True)
            if new_el is not None:
                soup = BeautifulSoup(original_html, "html.parser")
                target = self._locate_target(soup, new_el)
                if target is not None:
                    # Fehlende/korrigierte Attribute auf das echte Element mergen
                    # (z.B. alt, lang, aria-label). Bestehende Kinder bleiben.
                    for attr, val in new_el.attrs.items():
                        target[attr] = val
                    return str(soup), True
        except Exception:
            pass

        # Fallback: anhaengen — kann NICHT als verifiziert gelten.
        return original_html + "\n<!-- fix applied -->\n" + fix_code, False

    @staticmethod
    def _locate_target(soup, new_el):
        """
        Findet im Original das Element, das der Fix korrigiert — ueber stabile
        Identitaet (id, src, href) oder, fuer Dokument-Fixes, das <html>-Tag.
        Gibt None zurueck, wenn kein eindeutiges Ziel existiert.
        """
        tag = new_el.name
        el_id = new_el.get("id")
        if el_id:
            found = soup.find(tag, id=el_id) or soup.find(id=el_id)
            if found is not None:
                return found
        src = new_el.get("src")
        if src:
            found = soup.find(tag, src=src)
            if found is not None:
                return found
        href = new_el.get("href")
        if href:
            found = soup.find(tag, href=href)
            if found is not None:
                return found
        if tag == "html":
            return soup.find("html")
        return None
