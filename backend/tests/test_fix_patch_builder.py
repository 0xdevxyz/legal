"""
Tests fuer den deterministischen Patch-Builder.

Dieses Modul schreibt in Kundenrepos — jede Regel hier ist eine
Sicherheitszusage: guarded (nie ueberschreiben), minimal-invasiv (nur die
eine Stelle anfassen), deterministisch (gleiche Eingabe, gleicher PR).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fix_patch_builder import baue_patches, ist_kandidat

MANIFEST = {
    "alt_texts": [
        {"image_src": "https://kunde.de/wp-content/uploads/team.jpg",
         "suggested_alt": 'Unser Team vor dem Firmensitz in "Zwickau"'},
        {"image_src": "/assets/lkw-gelb.png", "suggested_alt": "Gelber LKW der Spedition"},
    ],
    "document_fixes": [
        {"fix_type": "html-lang", "payload": {"value": "de"}},
        {"fix_type": "skip-link", "payload": {"label": "Zum Inhalt springen", "target": "#main"}},
    ],
}


class TestAltTexte:
    def test_ergaenzt_alt_bei_passendem_dateinamen(self):
        dateien = {"index.html": '<html lang="de"><body><img src="/img/team.jpg"></body></html>'}
        patches = baue_patches(MANIFEST, dateien)
        assert len(patches) == 1
        assert 'alt="Unser Team vor dem Firmensitz in &quot;Zwickau&quot;"' in patches[0]["new_content"]
        assert patches[0]["feature_id"] == "ALT_TEXT"

    def test_pfade_egal_dateiname_zaehlt(self):
        """Manifest sagt /wp-content/uploads/, Template sagt {{ base }}/ — der Dateiname verbindet."""
        dateien = {"t.twig": '<html lang="de"><img src="{{ base }}/bilder/team.jpg?v=2"></html>'}
        patches = baue_patches(MANIFEST, dateien)
        assert len(patches) == 1
        assert "alt=" in patches[0]["new_content"]

    def test_echter_alt_text_wird_nie_ueberschrieben(self):
        """Ein gesetzter Alt-Text ist eine getroffene Entscheidung."""
        dateien = {"a.html": '<html lang="de"><img src="team.jpg" alt="Vorhandener Text"></html>'}
        assert baue_patches(MANIFEST, dateien) == []

    def test_leeres_alt_wird_gefuellt(self):
        """
        WordPress schreibt alt="" an jedes Bild ohne hinterlegten Alt-Text —
        das ist keine Dekorativ-Markierung, sondern der Standardfall. Frueher
        blockierte der Guard genau hier und der PR-Weg tat auf WordPress-Seiten
        gar nichts, waehrend das Laufzeit-Widget (`if (img && !img.alt)`) die
        gleichen Fixes laengst anwendete. Beide Kanaele, eine Regel.
        """
        dateien = {"a.html": '<html lang="de"><img src="team.jpg" alt="" class="x"></html>'}
        patches = baue_patches(MANIFEST, dateien)
        assert len(patches) == 1
        neu = patches[0]["new_content"]
        assert 'alt="Unser Team vor dem Firmensitz in &quot;Zwickau&quot;"' in neu
        assert 'class="x"' in neu          # Rest des Tags bleibt
        assert neu.count("alt=") == 1      # kein zweites alt-Attribut

    def test_nichtssagender_vorschlag_wird_nicht_ausgeliefert(self):
        """
        "Bild: Image 20" besteht axe und hilft niemandem. Im echten Bestand
        waren 5 von 14 Vorschlaegen fuer spedition-mahn.de von dieser Sorte.
        """
        manifest = {"alt_texts": [{"image_src": "/img/image-20.jpg",
                                   "suggested_alt": "Bild: Image 20"}]}
        dateien = {"a.html": '<html lang="de"><img src="/img/image-20.jpg" alt=""></html>'}
        assert baue_patches(manifest, dateien) == []

    def test_data_alt_gilt_nicht_als_versorgt(self):
        """data-alt ist ein Lazy-Loader-Attribut, kein Alt-Text."""
        dateien = {"a.html": '<html lang="de"><img data-alt="x" src="team.jpg"></html>'}
        patches = baue_patches(MANIFEST, dateien)
        assert len(patches) == 1
        assert ' alt="Unser Team' in patches[0]["new_content"]

    def test_fremde_bilder_bleiben_unberuehrt(self):
        dateien = {"a.html": '<html lang="de"><img src="logo-anders.svg"></html>'}
        assert baue_patches(MANIFEST, dateien) == []

    def test_selfclosing_tag_bleibt_selfclosing(self):
        dateien = {"a.html": '<html lang="de"><img src="team.jpg" class="x" /></html>'}
        patches = baue_patches(MANIFEST, dateien)
        assert 'alt="Unser Team vor dem Firmensitz in &quot;Zwickau&quot;" />' in patches[0]["new_content"]

    def test_rest_der_datei_bleibt_byte_identisch(self):
        """Minimal-invasiv: nur das img-Tag aendert sich, keine Zeile sonst."""
        original = '<html lang="de">\n  <body>\n    <p>Text &amp; mehr</p>\n    <img src="team.jpg">\n  </body>\n</html>'
        patches = baue_patches(MANIFEST, {"a.html": original})
        geaenderte = [z for z in patches[0]["unified_diff"].splitlines()
                      if z.startswith(("+", "-")) and not z.startswith(("+++", "---"))]
        assert len(geaenderte) == 2  # eine Zeile raus, eine rein


class TestDokumentFixes:
    def test_html_lang_wird_gesetzt(self):
        dateien = {"a.html": '<html><body><p>x</p></body></html>'}
        patches = baue_patches(MANIFEST, dateien)
        assert '<html lang="de">' in patches[0]["new_content"]

    def test_vorhandenes_lang_bleibt(self):
        dateien = {"a.html": '<html lang="en"><body><p>x</p></body></html>'}
        assert baue_patches({"document_fixes": MANIFEST["document_fixes"]}, dateien) == []

    def test_skip_link_nur_wenn_ziel_existiert(self):
        """Ein Sprunglink ins Leere waere selbst ein A11y-Fehler."""
        ohne_ziel = {"a.html": '<html lang="de"><body><p>x</p></body></html>'}
        assert baue_patches({"document_fixes": MANIFEST["document_fixes"]}, ohne_ziel) == []

        mit_main = {"a.html": '<html lang="de"><body><main><p>x</p></main></body></html>'}
        patches = baue_patches({"document_fixes": MANIFEST["document_fixes"]}, mit_main)
        assert len(patches) == 1
        assert 'class="skip-link"' in patches[0]["new_content"]

    def test_vorhandener_skip_link_wird_nicht_dupliziert(self):
        dateien = {"a.html": '<html lang="de"><body><a class="skip-link" href="#main">Skip</a><main></main></body></html>'}
        assert baue_patches({"document_fixes": MANIFEST["document_fixes"]}, dateien) == []

    def test_payload_als_json_string(self):
        """document_fixes kommen aus jsonb — je nach Treiber als String."""
        manifest = {"document_fixes": [{"fix_type": "html-lang", "payload": '{"value": "de"}'}]}
        patches = baue_patches(manifest, {"a.html": "<html><body></body></html>"})
        assert len(patches) == 1


class TestDeterminismusUndForm:
    def test_gleiche_eingabe_gleicher_patch(self):
        dateien = {"a.html": '<html><body><main><img src="team.jpg"></main></body></html>'}
        p1 = baue_patches(MANIFEST, dict(dateien))
        p2 = baue_patches(MANIFEST, dict(dateien))
        assert p1 == p2

    def test_unified_diff_format(self):
        dateien = {"seiten/index.html": '<html><body><img src="lkw-gelb.png"></body></html>'}
        patch = baue_patches(MANIFEST, dateien)[0]
        assert patch["unified_diff"].startswith("--- a/seiten/index.html")
        assert "+++ b/seiten/index.html" in patch["unified_diff"]
        assert patch["file_path"] == "seiten/index.html"

    def test_unveraenderte_dateien_erzeugen_keine_patches(self):
        dateien = {
            "geaendert.html": '<html><body><img src="team.jpg"></body></html>',
            "sauber.html": '<html lang="de"><body><img src="x.jpg" alt="ok"></body></html>',
        }
        patches = baue_patches(MANIFEST, dateien)
        assert [p["file_path"] for p in patches] == ["geaendert.html"]

    def test_leeres_manifest_leere_patches(self):
        assert baue_patches({}, {"a.html": "<html></html>"}) == []


class TestKandidatenFilter:
    def test_html_und_templates_ja(self):
        for p in ("index.html", "kopf.php", "layout.twig", "produkt.liquid"):
            assert ist_kandidat(p), p

    def test_jsx_und_assets_nein(self):
        """JSX rendert Attribute zur Laufzeit — Textoperation traefe Falsches."""
        for p in ("App.jsx", "seite.tsx", "logo.png", "haupt.css", "app.js"):
            assert not ist_kandidat(p), p

    def test_vendor_und_build_nein(self):
        for p in ("node_modules/x/a.html", "vendor/lib/b.php", "dist/index.html"):
            assert not ist_kandidat(p), p

    def test_zu_grosse_dateien_nein(self):
        assert not ist_kandidat("riesig.html", groesse=1_000_000)
        assert ist_kandidat("normal.html", groesse=10_000)
