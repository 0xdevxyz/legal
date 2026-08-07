"""
Wächter für die Kette der Struktur-Reparatur.

Dieselbe Lehre wie beim Kontrast: ein Fix-Generator ohne Antriebsstrang faellt
beim Testen der Teile nicht auf. Hier kommt eine Reihenfolge dazu, die leicht
unbemerkt kippt — und deren Umdrehen beide Messungen wertlos macht.
"""
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*teile: str) -> str:
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


def _ohne_kommentare(quelltext: str) -> str:
    """`//`-Kommentare entfernen.

    Ein Reihenfolge-Test darf nicht die Erwaehnung im erklaerenden Kommentar
    treffen — genau dieser Fehler steckte im Waechter von test_admin_auth.py
    und ist hier beim ersten Lauf sofort wieder passiert.
    """
    return "\n".join(re.sub(r"//.*$", "", z) for z in quelltext.splitlines())


class TestScanner:
    def test_ergebnis_traegt_das_feld(self):
        from compliance_engine.axe_scanner import AxeScanResult
        assert "struktur_fixes" in AxeScanResult.__dataclass_fields__

    def test_struktur_laeuft_vor_dem_kontrast(self):
        """
        Struktur setzt Attribute am Baum, Kontrast spielt danach CSS ein und
        faerbt um. Andersherum wuerde die Struktur-Nachmessung auf einer
        bereits umgefaerbten Seite laufen — beide Zahlen waeren dann wertlos.
        """
        src = "\n".join(
            re.sub(r"#.*$", "", z)
            for z in _lese("compliance_engine", "axe_scanner.py").splitlines()
        )
        assert src.index("verifizierte_struktur_fixes") < src.index("verifizierte_kontrast_fixes")


class TestKette:
    def test_check_reicht_den_befund_weiter(self):
        src = _lese("compliance_engine", "checks", "barrierefreiheit_check.py")
        assert "complyo-struktur-fix" in src

    def test_prozessor_macht_daraus_einen_fix(self):
        src = _lese("accessibility_post_scan_processor.py")
        assert "_struktur_fix_aus_issues" in src
        assert '"fix_type": "struktur"' in src

    def test_manifest_liefert_attribute_und_css_getrennt(self):
        """Markup und Darstellung sind verschiedene Kanaele im Runtime."""
        src = _lese("widget_routes.py")
        assert '"struktur_fixes": next(' in src
        block = src[src.index("css_rules = ["):]
        assert '"struktur"' in block[:800]

    def test_struktur_taucht_nicht_doppelt_als_document_fix_auf(self):
        src = _lese("widget_routes.py")
        block = src[src.index('"struktur_fixes": next('):]
        assert 'f.get("fix_type") == "struktur"' in block[:400]


class TestRuntime:
    def test_runtime_wendet_attribute_an(self):
        src = _lese("widgets", "a11y_remediation.js")
        assert "function applyStrukturFixes" in src
        assert "strukturFixes = d.struktur_fixes" in src

    def test_struktur_laeuft_vor_dem_sprunglink(self):
        """
        Erst setzt die Struktur role="main" (und notfalls eine id), dann findet
        applySkipLink() ein aufloesbares Ziel. Umgekehrt wuerde der Sprunglink
        gar nicht erst injiziert.
        """
        src = _lese("widgets", "a11y_remediation.js")
        block = _ohne_kommentare(src[src.index("function apply() {"):])
        block = block[:block.index("var scheduled")]
        assert block.index("applyStrukturFixes()") < block.index("applySkipLink()")

    def test_gemessenes_ziel_schlaegt_die_rateliste(self):
        src = _lese("widgets", "a11y_remediation.js")
        block = _ohne_kommentare(src[src.index("function resolveMainTarget"):])
        block = block[:block.index("function applySkipLink")]
        assert block.index("strukturFixes") < block.index("#content, #content-main")

    def test_nur_das_viewport_meta_wird_ueberschrieben(self):
        """Ueberall sonst gilt guarded — nur die Zoom-Sperre soll weichen."""
        src = _lese("widgets", "a11y_remediation.js")
        block = src[src.index("function applyStrukturFixes"):]
        block = block[:block.index("// CSS einmalig")]
        assert "el.tagName === 'META'" in block
        assert "!el.getAttribute(f.attribut)" in block
