"""
Struktur-Fixes auf Unterseiten (Audit 11.08.2026).

Der gemessene Selektor trägt bei Elementor die Post-ID der gemessenen Seite
(z.B. `div.elementor.elementor-12735`) und traf auf jeder Unterseite nichts:
angewendet=0 bei konstantem verfehlt (spedition-mahn /unternehmen/ 0/63).

Die Lösung bleibt beim Prinzip „gemessen statt geraten":
1. ALTERNATIVEN_JS bestimmt bei der Messung seitenstabile Alternativ-
   Selektoren desselben Containers und verifiziert sie dort auf Eindeutigkeit.
2. baue_struktur_fixes hängt sie als `alternativen` an den role=main-Fix.
3. Das Widget (findeStrukturZiele) nutzt sie nur bei GENAU einem Treffer
   außerhalb der Randbereiche und erzeugt nie eine zweite main-Landmark.
"""
import os
import shutil
import subprocess

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_NODE = shutil.which("node")
_KEIN_NODE = ("node fehlt im Testcontainer — der Funktionstest läuft überall, "
              "wo node installiert ist (z.B. auf dem Host)")


def _lese(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as f:
        return f.read()


def _widget_js():
    return _lese("widgets", "a11y_remediation.js")


def _finde_ziele_block():
    """Extrahiert Randbereichs-Prüfung + findeStrukturZiele aus dem Widget."""
    js = _widget_js()
    start = js.index("var RANDBEREICH_RE")
    ende = js.index("function resolveMainTarget")
    return js[start:ende]


class TestQuelltext:
    """Läuft immer — auch ohne node."""

    def test_messung_liefert_alternativen(self):
        from compliance_engine.struktur_fixes import ALTERNATIVEN_JS, baue_struktur_fixes
        assert "data-elementor-type" in ALTERNATIVEN_JS
        fixes = baue_struktur_fixes(
            {"region": [{"target": ["div"]}]},
            "div.elementor.elementor-12735",
            ["div[data-elementor-type=\"wp-page\"]"],
        )
        haupt = [f for f in fixes if f.get("attribut") == "role"][0]
        assert haupt["alternativen"] == ["div[data-elementor-type=\"wp-page\"]"]

    def test_messung_ohne_alternativen_bleibt_kompatibel(self):
        from compliance_engine.struktur_fixes import baue_struktur_fixes
        fixes = baue_struktur_fixes({"region": [{"target": ["div"]}]}, "#main")
        haupt = [f for f in fixes if f.get("attribut") == "role"][0]
        assert "alternativen" not in haupt

    def test_verifizierer_reicht_alternativen_durch(self):
        quelle = _lese("compliance_engine", "struktur_verifizierer.py")
        assert "ALTERNATIVEN_JS" in quelle
        assert "baue_struktur_fixes(vorher, haupt_selektor, haupt_alternativen)" in quelle

    def test_widget_kennt_alternativen_und_unnoetig(self):
        js = _widget_js()
        assert "findeStrukturZiele" in js
        assert "f.alternativen" in js
        assert "zaehltUnnoetig('struktur'" in js
        # struktur-Bilanz hat den unnoetig-Zähler
        assert "struktur: { angewendet: 0, verfehlt: 0, unnoetig: 0 }" in js


@pytest.mark.skipif(_NODE is None, reason=_KEIN_NODE)
class TestWidgetVerhalten:
    def _lauf(self, quelle):
        lauf = subprocess.run([_NODE, "-e", quelle],
                              capture_output=True, text=True, timeout=30)
        assert lauf.returncode == 0, lauf.stderr or lauf.stdout
        return lauf.stdout

    def _harness(self, seite_js, pruefung_js):
        """DOM-Stub: `seite` bildet Selektoren auf Element-Listen ab."""
        return ("var seite = " + seite_js + ";\n"
                "for (var k in seite) { seite[k].forEach(function (el) {\n"
                "  if (!el.closest) el.closest = function () { return null; };\n"
                "  if (el.className === undefined) el.className = '';\n"
                "  if (el.id === undefined) el.id = '';\n"
                "}); }\n"
                "var document = {\n"
                "  querySelectorAll: function (s) { return seite[s] || []; },\n"
                "  querySelector: function (s) { return (seite[s] || [])[0] || null; }\n"
                "};\n"
                + _finde_ziele_block()
                + "function pruefe(c, m) { if (!c) { console.error('FEHLER: ' + m); process.exit(1); } }\n"
                + pruefung_js
                + "console.log('OK');\n")

    def test_startseite_exakter_selektor_gewinnt(self):
        harness = self._harness(
            "{ 'div.elementor.elementor-12735': [{tag: 'exakt'}] }",
            "var z = findeStrukturZiele({selector: 'div.elementor.elementor-12735',"
            " attribut: 'role', wert: 'main'});\n"
            "pruefe(z.length === 1 && z[0].tag === 'exakt', 'exakter Treffer gewinnt');\n",
        )
        assert "OK" in self._lauf(harness)

    def test_unterseite_verifizierte_alternative_greift(self):
        harness = self._harness(
            "{ 'div[data-elementor-type=\"wp-page\"]': [{tag: 'wrapper'}] }",
            "var z = findeStrukturZiele({selector: 'div.elementor.elementor-12735',"
            " attribut: 'role', wert: 'main',"
            " alternativen: ['div[data-elementor-type=\"wp-page\"]']});\n"
            "pruefe(z.length === 1 && z[0].tag === 'wrapper', 'Alternative greift auf Unterseite');\n",
        )
        assert "OK" in self._lauf(harness)

    def test_unterseite_abgeleiteter_selektor_ohne_postid(self):
        harness = self._harness(
            "{ 'div.elementor': [{tag: 'wrapper'}] }",
            "var z = findeStrukturZiele({selector: 'div.elementor.elementor-12735',"
            " attribut: 'role', wert: 'main'});\n"
            "pruefe(z.length === 1 && z[0].tag === 'wrapper',"
            " 'Ableitung streicht volatile ID-Klasse');\n",
        )
        assert "OK" in self._lauf(harness)

    def test_mehrdeutiger_kandidat_wird_verworfen(self):
        harness = self._harness(
            "{ 'div.elementor': [{tag: 'a'}, {tag: 'b'}] }",
            "var z = findeStrukturZiele({selector: 'div.elementor.elementor-12735',"
            " attribut: 'role', wert: 'main'});\n"
            "pruefe(z !== 'unnoetig' && z.length === 0,"
            " 'zwei Treffer sind kein Ziel — lieber verfehlt als falsch');\n",
        )
        assert "OK" in self._lauf(harness)

    def test_randbereich_wird_verworfen(self):
        harness = self._harness(
            "{ 'div.elementor': [{tag: 'kopf', className: 'elementor-location-header'}] }",
            "var z = findeStrukturZiele({selector: 'div.elementor.elementor-12735',"
            " attribut: 'role', wert: 'main'});\n"
            "pruefe(z !== 'unnoetig' && z.length === 0, 'Randbereich ist kein main');\n",
        )
        assert "OK" in self._lauf(harness)

    def test_vorhandene_main_landmark_heisst_unnoetig(self):
        harness = self._harness(
            "{ 'div.elementor': [{tag: 'wrapper'}],"
            "  'main, [role=\"main\"]': [{tag: 'main'}] }",
            "var z = findeStrukturZiele({selector: 'div.elementor.elementor-12735',"
            " attribut: 'role', wert: 'main'});\n"
            "pruefe(z === 'unnoetig', 'zweite main-Landmark wird nie erzeugt');\n",
        )
        assert "OK" in self._lauf(harness)
