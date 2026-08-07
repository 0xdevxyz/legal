"""
Waechter gegen erfundene Bildadressen.

Der Post-Scan-Prozessor hatte einen Rueckfall auf `/image-{idx}.jpg`, wenn ein
Befund keine Bildadresse trug. Das erzeugte Eintraege fuer Dateien, die es
nicht gibt: die Vision bekam einen 404, die Kontext-Heuristik machte daraus
"Bild: Image 20" mit Konfidenz 0,7 — und dieser Text landete als
Alt-Text-Vorschlag in der Worklist, wo ein Kunde ihn freigeben konnte.

Im Bestand von spedition-mahn.de waren 5 von 14 Vorschlaegen von dieser Sorte.
Beim ersten echten Scan nach dem Ausrollen stand es sofort wieder im Log
("Bild-Download 404 fuer .../image-1.jpg").
"""
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from accessibility_post_scan_processor import _src_aus_markup  # noqa: E402

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _quelltext() -> str:
    with open(os.path.join(_BACKEND, "accessibility_post_scan_processor.py"),
              encoding="utf-8") as fh:
        s = fh.read()
    ohne = re.sub(r'"""[\s\S]*?"""', "", s)
    return "\n".join(re.sub(r"#.*$", "", z) for z in ohne.splitlines())


class TestKeineErfundenenDateinamen:
    def test_der_rueckfall_ist_weg(self):
        assert "f'/image-{idx + 1}.jpg'" not in _quelltext()
        assert "image-{idx" not in _quelltext()

    def test_ohne_adresse_wird_uebersprungen(self):
        """Kein Vorschlag ist besser als einer fuer ein Bild, das es nicht gibt."""
        code = _quelltext()
        block = code[code.index("async def _generate_alt_text_fixes"):]
        assert "if not image_src:" in block[:2500]
        assert "continue" in block[:2600]


class TestSrcAusMarkup:
    def test_gewoehnliches_bild(self):
        assert _src_aus_markup('<img src="/uploads/team.jpg" width="800">') == "/uploads/team.jpg"

    def test_lazy_loader_mit_data_src(self):
        """ferienpark-waldenburg.de liefert data-src statt src."""
        assert _src_aus_markup('<img data-src="/uploads/markt.png">') == "/uploads/markt.png"

    def test_einfache_anfuehrungszeichen(self):
        assert _src_aus_markup("<img src='/a/b.webp'>") == "/a/b.webp"

    def test_kein_bild_kein_treffer(self):
        assert _src_aus_markup("<div class='srcset'></div>") == ""
        assert _src_aus_markup("") == ""

    def test_fremde_attribute_zaehlen_nicht(self):
        """`data-lazy-srcset` ist keine Bildadresse."""
        assert _src_aus_markup('<img foo-src="x.jpg">') == ""


class TestStatementPaket:
    def test_user_id_wird_umgewandelt(self):
        """
        Die Spalte ist integer, die Aufrufer reichen einen String durch. Ohne
        Umwandlung scheitert JEDER Insert — im Log stand seit jeher
        "Statement-Paket konnte nicht gespeichert werden".
        """
        code = _quelltext()
        # Ab der DEFINITION fenstern, nicht ab dem Aufruf weiter oben.
        block = code[code.index("async def _save_statement_package"):]
        assert "_als_user_id(user_id)" in block[:4000]
        assert "str(user_id), site_id, site_url" not in block[:4000]

    def test_helfer_ist_importiert(self):
        assert "from accessibility_fix_saver import" in _quelltext()
        assert "_als_user_id" in _quelltext()
