"""
Waechter: der Post-Scan-Prozessor muss die ROHEN Befunde bekommen.

Zwei Dinge haengen daran, und beide sind lange unbemerkt geblieben, weil der
Aufruf erfolgreich aussieht — der Prozessor findet die Marker nicht und meldet
schlicht null erzeugte Fixes:

  1. `metadata.source` == "complyo-kontrast-fix" / "complyo-struktur-fix".
     Ohne die werden die im Browser verifizierten Reparaturen NIE gespeichert.
  2. `element.src` des Bildes. Ohne die greift die Notloesung `/image-N.jpg`,
     und Claude Vision beschreibt eine Datei, die es nicht gibt — daher die
     Vorschlaege der Sorte "Bild: Image 20".

`structured_issues` ist fuer das Dashboard zurechtgeschnitten
(`_fundstellen_metadata` laesst absichtlich fast nichts durch). Das ist dort
richtig — nur darf es nicht die Quelle fuer den Prozessor sein.
"""
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


def _nur_code(quelltext: str) -> str:
    ohne = re.sub(r'"""[\s\S]*?"""', "", quelltext)
    return "\n".join(re.sub(r"#.*$", "", z) for z in ohne.splitlines())


class TestRoheBefundeErreichenDenProzessor:
    def test_aufruf_nutzt_die_rohen_befunde(self):
        src = _nur_code(_lese("public_routes.py"))
        block = src[src.index("process_scan_results("):]
        block = block[:block.index("site_url=")]
        assert 'scan_result.get("issues")' in block

    def test_nicht_die_zurechtgeschnittenen(self):
        src = _nur_code(_lese("public_routes.py"))
        block = src[src.index("process_scan_results("):]
        block = block[:block.index("site_url=")]
        assert "for i in structured_issues" not in block

    def test_der_grund_steht_dabei(self):
        """Sonst 'vereinfacht' es jemand zurueck."""
        src = _lese("public_routes.py")
        block = src[src.index("process_scan_results("):]
        assert "complyo-kontrast-fix" in block[:2500]


class TestDerProzessorBrauchtGenauDas:
    def test_er_sucht_nach_den_markern(self):
        src = _lese("accessibility_post_scan_processor.py")
        assert "complyo-kontrast-fix" in src
        assert "complyo-struktur-fix" in src

    def test_er_liest_die_bild_src_aus_dem_element(self):
        src = _lese("accessibility_post_scan_processor.py")
        assert "get('element', {}).get('src'" in src or 'get("element", {}).get("src"' in src


class TestDashboardBleibtSchlank:
    def test_fundstellen_metadata_filtert_weiter(self):
        """
        Die Beschraenkung fuers Frontend ist Absicht und bleibt — sie war nie
        das Problem, nur ihre Verwendung als Quelle fuer den Prozessor.
        """
        src = _lese("public_routes.py")
        assert "def _fundstellen_metadata" in src
        block = src[src.index("def _fundstellen_metadata"):]
        assert "seiten_betroffen" in block[:900]
