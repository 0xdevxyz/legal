"""
Waechter: was auf der Kundenseite ankommt, muss auch die Reparaturen enthalten.

Beim Ausrollen aufgefallen und beinahe uebersehen: `accessibility-v6.js` holt
ausschliesslich Alt-Texte ueber einen eigenen Endpunkt. Kontrast-, Struktur-
und Linkname-Reparaturen laufen ueber das Fix-Manifest, das nur
`a11y_remediation.js` liest — und die liegt unter einer ANDEREN Adresse
(`/api/widgets/a11y-fixes.js`).

Auf allen Kundenseiten steht `accessibility.js`. Alles ausser Alt-Texten
erreichte damit niemanden, ohne dass es auffiel: die Fixes waren gebaut,
verifiziert, freigegeben, im Manifest — und liefen ins Leere.

Diese Datei haelt fest, dass beide Teile aus derselben Adresse kommen.
"""
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


class TestAuslieferung:
    def test_accessibility_js_haengt_die_remediation_an(self):
        src = _lese("widget_routes.py")
        block = src[src.index("async def serve_accessibility_widget"):]
        block = block[:block.index("@router.get", 10)]
        assert "a11y_remediation.js" in block
        assert "content +=" in block

    def test_der_grund_steht_dabei(self):
        """Sonst entfernt es jemand als vermeintliche Doppelung."""
        src = _lese("widget_routes.py")
        block = src[src.index("async def serve_accessibility_widget"):]
        assert "Fix-Manifest" in block[:3000]

    def test_fehlende_datei_wird_nicht_verschwiegen(self):
        src = _lese("widget_routes.py")
        block = src[src.index("async def serve_accessibility_widget"):]
        assert "warning" in block[:3500]


class TestBeideTeileTunWasSieSollen:
    def test_v6_bringt_die_bedienleiste(self):
        v6 = _lese("widgets", "accessibility-v6.js")
        assert "loadAndApplyAltTexts" in v6

    def test_remediation_bringt_das_manifest(self):
        rem = _lese("widgets", "a11y_remediation.js")
        assert "fix-manifest" in rem
        for teil in ("cssRules", "strukturFixes", "linkFixes"):
            assert teil in rem, teil

    def test_remediation_findet_ihre_konfiguration_auch_ohne_eigenes_tag(self):
        """
        Zusammengehaengt laeuft sie unter dem accessibility.js-Tag. Ohne diesen
        Rueckfall auf `script[data-site-id]` wuerde sie dort abbrechen.
        """
        rem = _lese("widgets", "a11y_remediation.js")
        assert "script[data-site-id]" in rem

    def test_alt_texte_werden_nie_ueberschrieben(self):
        """
        Beide Wege setzen Alt-Texte. Das ist nur unbedenklich, solange keiner
        etwas Vorhandenes ueberschreibt — wer zuerst kommt, gewinnt.
        """
        rem = _lese("widgets", "a11y_remediation.js")
        assert "if (cur && cur.trim() !== '') continue" in rem
        v6 = _lese("widgets", "accessibility-v6.js")
        assert "if (img && !img.alt)" in v6
