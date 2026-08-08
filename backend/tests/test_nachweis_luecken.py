"""
Waechter fuer drei Luecken im oeffentlichen Pruefnachweis.

Alle drei sind bei einer adversarialen Probe gegen die Live-Endpunkte
aufgefallen, nicht in der Entwicklung — und alle drei betrafen ausgerechnet
das Dokument, das complyos wichtigstes Verkaufsargument ist.

1. Die site_url wurde aus der site_id zurueckgerechnet. `derive_site_id()`
   bildet Punkt UND Bindestrich auf '-' ab, die Kodierung ist also
   verlustbehaftet. Im Nachweis stand `https://loqal-io`; aus `bau-design-de`
   waere die fremde Domain `bau.design.de` geworden. Das LIKE-Muster mit
   Platzhaltern konnte ausserdem die Adresse einer ANDEREN Kundenseite treffen.

2. Eine Website, deren gesamte Arbeit aus Bildbeschreibungen besteht, bekam
   gar keinen Nachweis (404) — der Kern-USP fehlte im einfachsten Kundenfall.
   Von sechs echten Kundenseiten waren drei betroffen.

3. `anbieter` und `kontakt` gingen ungeprueft aus der Abfragezeichenkette in
   einen Markdown-Text, den der Betreiber in seine Website einsetzt.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import nachweis_routes  # noqa: E402
from compliance_engine.nachweis_generator import baue_nachweis  # noqa: E402
from compliance_engine.nachweis_seite import nachweis_als_html  # noqa: E402
from site_id_utils import derive_site_id  # noqa: E402


class TestSiteIdIstVerlustbehaftet:
    """Der Beleg dafuer, dass Zurueckrechnen prinzipiell nicht geht."""

    def test_punkt_und_bindestrich_werden_ununterscheidbar(self):
        assert derive_site_id("https://bau-design.de") == \
               derive_site_id("https://bau.design.de")

    def test_daher_darf_keine_umkehrung_im_code_stehen(self):
        quelle = _quelle_ohne_kommentare("nachweis_routes.py")
        assert '.replace("-de", ".de")' not in quelle, \
            "Ruecktransformation site_id -> Domain ist wieder da"
        assert '.replace("-", "%")' not in quelle, \
            "LIKE-Platzhalter aus der site_id koennen fremde Domains treffen"

    def test_vorwaerts_vergleich_wird_benutzt(self):
        quelle = _quelle_ohne_kommentare("nachweis_routes.py")
        assert "_SITE_ID_AUS_URL" in quelle and "tracked_websites" in quelle


class TestNachweisOhneDokumentFixes:
    """Bildbeschreibungen allein muessen fuer ein Protokoll reichen."""

    def test_nachweis_entsteht_nur_aus_bildbeschreibungen(self):
        n = baue_nachweis(
            site_id="loqal-io", site_url="https://loqal.io",
            messung_vorher={}, messung_nachher={}, fixes=[],
            alt_texte_live=4, alt_texte_offen=0,
        )
        assert n["bildbeschreibungen_live"] == 4
        assert n["summe"]["vorher"] == 0

    def test_offene_bildbeschreibungen_stehen_im_protokoll(self):
        n = baue_nachweis(
            site_id="x-de", site_url="https://x.de",
            messung_vorher={}, messung_nachher={}, fixes=[],
            alt_texte_live=2, alt_texte_offen=13,
        )
        assert n["bildbeschreibungen_offen"] == 13
        html = nachweis_als_html(n)
        assert "13" in html and "nicht beschrieben" in html, \
            "Die Luecke fehlt in der lesbaren Fassung"

    def test_erklaerung_benennt_die_offenen_bilder(self):
        from compliance_engine.nachweis_generator import erklaerung_aus_nachweis
        n = baue_nachweis(
            site_id="x-de", site_url="https://x.de",
            messung_vorher={}, messung_nachher={}, fixes=[],
            alt_texte_live=2, alt_texte_offen=13,
        )
        text = erklaerung_aus_nachweis(n, anbieter="X", kontakt="mail")
        assert "13" in text, \
            "Eine Erklaerung, die eine bekannte Luecke verschweigt, ist falsch"


class TestVorbereiteteReparaturen:
    """
    Eine nachgemessene, aber nicht freigegebene Reparatur darf nie als behoben
    zaehlen — und muss trotzdem sichtbar sein. Vorher fuehrte dieser Zustand
    zu 404: eine Website, an der alles vorbereitet war, hatte gar keinen
    Nachweis. Ausgerechnet complyo.de war betroffen.
    """

    def _nachweis(self):
        return baue_nachweis(
            site_id="complyo-de", site_url="https://complyo.de",
            messung_vorher={"color-contrast": 6},
            messung_nachher={"color-contrast": 6},
            fixes=[],
            vorbereitet=[{"regel": "color-contrast", "fundstellen": 6,
                          "nachgemessen": 0}],
        )

    def test_zaehlt_nicht_als_behoben(self):
        n = self._nachweis()
        assert n["summe"]["behoben"] == 0
        assert n["summe"]["quote"] == 0

    def test_steht_weiter_unter_offen(self):
        assert any(o["regel"] == "color-contrast" for o in self._nachweis()["offen"])

    def test_ist_als_nicht_ausgeliefert_gekennzeichnet(self):
        v = self._nachweis()["vorbereitet"][0]
        assert v["nach_reparatur_gemessen"] == 0
        assert "nicht" in v["stand"].lower()

    def test_html_nennt_es_nicht_aktiv(self):
        html = nachweis_als_html(self._nachweis())
        assert "nicht aktiv" in html and "Freigabe" in html

    def test_erklaerung_behauptet_keine_behebung(self):
        from compliance_engine.nachweis_generator import erklaerung_aus_nachweis
        text = erklaerung_aus_nachweis(self._nachweis(), anbieter="X", kontakt="y")
        assert "6 Abweichungen" in text and "0 davon sind behoben" in text


class TestFremdtextInDerErklaerung:
    def test_spitze_klammern_verschwinden(self):
        assert "<" not in nachweis_routes._fremdtext("<script>alert(1)</script>")

    def test_zeilenumbrueche_brechen_das_markdown_nicht(self):
        assert "\n" not in nachweis_routes._fremdtext("a\n\n# Ueberschrift")

    def test_laenge_begrenzt(self):
        assert len(nachweis_routes._fremdtext("a" * 9000)) <= 200

    def test_leer_bleibt_leer(self):
        assert nachweis_routes._fremdtext("") == ""


def _quelle_ohne_kommentare(name: str) -> str:
    """
    Quelltext ohne Kommentare und Docstrings.

    Ohne das findet ein Waechtertest die verbotene Zeichenkette in der
    Begruendung, die ueber der Reparatur steht — und gilt als bestanden,
    obwohl der Fehler wieder im Code stuende. Das ist hier schon viermal
    passiert.
    """
    import io
    import tokenize

    pfad = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), name)
    with open(pfad, encoding="utf-8") as fh:
        quelle = fh.read()

    stuecke = []
    vorher_typ = tokenize.INDENT
    for tok in tokenize.generate_tokens(io.StringIO(quelle).readline):
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING and vorher_typ in (
                tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE,
                tokenize.NL, tokenize.ENCODING):
            continue  # Docstring
        stuecke.append(tok.string)
        if tok.type not in (tokenize.NL, tokenize.NEWLINE):
            vorher_typ = tok.type
    return " ".join(stuecke)
