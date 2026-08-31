"""
Erkennung der Pflichtangaben in Impressum und Datenschutzerklaerung.

Hintergrund: Der Scanner meldete vorhandene Pflichtangaben monatelang als
fehlend — complyo.de stand deshalb bei 17 %, obwohl alle acht Impressums-
angaben auf der Seite standen. Drei Ursachen, die diese Tests festhalten:

1. Die Check-Module reichten die rohe HTML-Antwort in einen Parameter namens
   `text_content`. In HTML stehen "Musterstrasse 123" und "10115 Berlin" in
   getrennten <p>-Elementen; kein Adressmuster greift darueber hinweg.
2. Die Schwellen (`min_confidence`) lagen ueber dem, was
   `_calculate_match_confidence` ueberhaupt erreichen kann.
3. Gesucht wurde durchgehend mit re.IGNORECASE, obwohl deutsche Eigennamen an
   der Grossschreibung erkannt werden: "Als Diensteanbieter sind wir gemaess"
   ergab den Firmennamen "sind wir gemaess".

Der Gegentest ist so wichtig wie der Positivtest: eine Seite ohne die Angaben
darf sie nicht ploetzlich als vorhanden melden, sonst versteckt der Scanner
echte Maengel.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks.deep_content_analyzer import DeepContentAnalyzer
from compliance_engine.hybrid_validator import zu_fliesstext


IMPRESSUM_HTML = """
<html><head><style>.a{color:red}</style></head><body>
<h1>Impressum</h1>
<h2>Angaben gem&auml;&szlig; &sect; 5 TMG</h2>
<div><p class="font-semibold">Complyo GmbH</p><p>Musterstra&szlig;e 123</p>
<p>10115 Berlin</p><p>Deutschland</p></div>
<h2>Kontakt</h2><p>+49 (0) 30 1234567</p><p>info@complyo.de</p>
<h2>Rechtliche Angaben</h2>
<p>Handelsregister: HRB 123456 B</p>
<p>Registergericht: Amtsgericht Berlin-Charlottenburg</p>
<p>Umsatzsteuer-ID: DE123456789</p>
<p>Gesch&auml;ftsf&uuml;hrer: Max Mustermann</p>
<h2>Haftungsausschluss</h2>
<p>Als Diensteanbieter sind wir gem&auml;&szlig; &sect; 7 Abs.1 TMG f&uuml;r eigene
Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich.</p>
</body></html>
"""

# Eine Seite ohne jede Pflichtangabe. Enthaelt bewusst Ziffernfolgen und
# Rechtstext-Floskeln, an denen sich die Muster frueher verschluckt haben.
OHNE_ANGABEN = """
Startseite Leistungen Kontakt. Wir bauen Gartenzaeune in Sachsen seit 1998.
Rufen Sie uns an oder nutzen Sie das Formular. Oeffnungszeiten Montag bis
Freitag 8 bis 17 Uhr. Referenzen finden Sie in der Galerie.
Steuer-Nr. 221/204/01878 Haftungsausschluss Haftung fuer Inhalte.
Als Diensteanbieter sind wir gemaess den allgemeinen Gesetzen verantwortlich.
"""

PFLICHTFELDER_IMPRESSUM = ["firmenname", "adresse", "plz_ort", "email", "telefon"]


@pytest.fixture(scope="module")
def analyzer():
    return DeepContentAnalyzer()


class TestFliesstext:
    """zu_fliesstext ist die Schranke gegen rohes HTML im Validator."""

    def test_html_wird_zu_text(self):
        text = zu_fliesstext(IMPRESSUM_HTML)
        assert "<p>" not in text
        # Getrennte Elemente stehen danach in einer Zeile beieinander
        assert "Musterstraße 123 10115 Berlin" in text

    def test_skript_und_stil_fliegen_raus(self):
        assert "color:red" not in zu_fliesstext(IMPRESSUM_HTML)

    def test_reiner_text_bleibt_unveraendert(self):
        assert zu_fliesstext(OHNE_ANGABEN) == OHNE_ANGABEN

    def test_leereingabe(self):
        assert zu_fliesstext("") == ""
        assert zu_fliesstext(None) == ""


class TestImpressumsangabenWerdenGefunden:
    """Alle acht Angaben stehen im Beispiel — keine darf als fehlend gelten."""

    @pytest.mark.parametrize("feld", [
        "firmenname", "adresse", "plz_ort", "email",
        "telefon", "handelsregister", "ust_id", "geschaeftsfuehrer",
    ])
    def test_feld_wird_erkannt(self, analyzer, feld):
        text = zu_fliesstext(IMPRESSUM_HTML)
        cfg = analyzer.impressum_patterns[feld]
        ergebnis = analyzer._validate_field(feld, cfg, text, None)
        assert ergebnis.found, (
            f"{feld} steht auf der Seite, wurde aber als fehlend gemeldet "
            f"(Confidence {ergebnis.confidence:.2f} < Schwelle {cfg['min_confidence']}, "
            f"Wert {ergebnis.extracted_value!r})"
        )

    def test_rohes_html_scheitert_nicht_mehr_am_aufrufer(self, analyzer):
        """Der Weg ueber zu_fliesstext ist gleichwertig, egal was hereinkommt."""
        for feld in PFLICHTFELDER_IMPRESSUM:
            cfg = analyzer.impressum_patterns[feld]
            assert analyzer._validate_field(
                feld, cfg, zu_fliesstext(IMPRESSUM_HTML), None
            ).found, feld

    def test_firmenname_ist_kein_satzfragment(self, analyzer):
        """"Als Diensteanbieter sind wir gemäß" ergab frueher den Firmennamen."""
        cfg = analyzer.impressum_patterns["firmenname"]
        wert = analyzer._validate_field(
            "firmenname", cfg, zu_fliesstext(IMPRESSUM_HTML), None
        ).extracted_value
        assert wert and "Complyo" in wert, f"unbrauchbarer Firmenname: {wert!r}"


class TestSchwellenSindErreichbar:
    """
    Jede Schwelle muss unter der Obergrenze liegen, die die Confidence-Rechnung
    erreichen kann — sonst ist das Feld strukturell immer "fehlend".
    Obergrenze ohne Formatprobe: 0.5 * 1.3 (Laenge) * 1.2 (Kontext) = 0.78.
    """

    OBERGRENZE_OHNE_FORMATPROBE = 0.78
    MIT_FORMATPROBE = {
        "firmenname", "adresse", "plz_ort", "email",
        "telefon", "handelsregister", "ust_id",
    }

    @pytest.mark.parametrize("satz", ["impressum_patterns", "datenschutz_patterns"])
    def test_schwelle_ist_erreichbar(self, analyzer, satz):
        for feld, cfg in getattr(analyzer, satz).items():
            if feld in self.MIT_FORMATPROBE:
                continue
            assert cfg["min_confidence"] <= self.OBERGRENZE_OHNE_FORMATPROBE, (
                f"{feld}: Schwelle {cfg['min_confidence']} liegt ueber der "
                f"erreichbaren Obergrenze {self.OBERGRENZE_OHNE_FORMATPROBE}"
            )


class TestKeineFalschtreffer:
    """Eine Seite ohne die Angaben darf keine melden — sonst verschwindet ein
    echter Mangel aus dem Befund."""

    @pytest.mark.parametrize("feld", [
        "firmenname", "adresse", "plz_ort", "email",
        "telefon", "handelsregister", "ust_id", "geschaeftsfuehrer",
    ])
    def test_nichts_wird_erfunden(self, analyzer, feld):
        cfg = analyzer.impressum_patterns[feld]
        ergebnis = analyzer._validate_field(feld, cfg, OHNE_ANGABEN, None)
        assert not ergebnis.found, (
            f"{feld} wurde auf einer Seite ohne Pflichtangaben gemeldet: "
            f"{ergebnis.extracted_value!r}"
        )

    def test_steuernummer_ist_keine_postleitzahl(self, analyzer):
        """"Steuer-Nr. 221/204/01878" wurde als "01878 Haftungsausschluss" gelesen."""
        cfg = analyzer.impressum_patterns["plz_ort"]
        ergebnis = analyzer._validate_field("plz_ort", cfg, OHNE_ANGABEN, None)
        assert not ergebnis.found


class TestEchteMaengelBleibenStehen:
    """Die Datenschutzerklaerung von complyo.de nennt weder Zwecke noch
    Rechtsgrundlage, Speicherdauer oder Beschwerderecht. Das sind echte
    Maengel und muessen es bleiben."""

    KURZE_ERKLAERUNG = """
    Datenschutzerklaerung. 2. Hinweis zur verantwortlichen Stelle
    Die verantwortliche Stelle fuer die Datenverarbeitung auf dieser Website
    ist: Complyo GmbH Musterstrasse 123 10115 Berlin.
    3. Datenerfassung auf dieser Website Cookies. Server-Log-Dateien.
    4. Ihre Rechte Sie haben folgende Rechte: Recht auf Auskunft (Art. 15 DSGVO)
    Recht auf Berichtigung (Art. 16 DSGVO) Recht auf Loeschung (Art. 17 DSGVO)
    """

    @pytest.mark.parametrize("feld", [
        "zwecke", "rechtsgrundlage", "speicherdauer", "beschwerderecht",
    ])
    def test_fehlende_angabe_wird_weiterhin_gemeldet(self, analyzer, feld):
        cfg = analyzer.datenschutz_patterns[feld]
        ergebnis = analyzer._validate_field(feld, cfg, self.KURZE_ERKLAERUNG, None)
        assert not ergebnis.found, (
            f"{feld} fehlt in der Erklaerung, wurde aber als vorhanden gemeldet: "
            f"{ergebnis.extracted_value!r}"
        )

    @pytest.mark.parametrize("feld", ["verantwortlicher", "betroffenenrechte"])
    def test_vorhandene_angabe_wird_erkannt(self, analyzer, feld):
        cfg = analyzer.datenschutz_patterns[feld]
        assert analyzer._validate_field(feld, cfg, self.KURZE_ERKLAERUNG, None).found, feld
