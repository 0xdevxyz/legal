# -*- coding: utf-8 -*-
"""
Ohne Auftragsverarbeitungsvertrag darf kein Kunde complyo einsetzen.

Sobald das Widget auf einer Kundenwebsite laeuft, verarbeitet complyo Daten der
Besucher DIESER Website: Einwilligungsprotokolle, die Verbindungsdaten beim
Laden der Widgets und die Inhalte der geprueften Seiten. Das ist
Auftragsverarbeitung nach Art. 28 DSGVO. Bis zum 10.09.2026 gab es dafuer
keinen Vertrag — weder als Seite noch im Onboarding. Damit verstiess jeder
Kunde gegen Art. 28 Abs. 3, und complyo haftete als Auftragsverarbeiter daneben
(Art. 83 Abs. 4 lit. a DSGVO).

Der Test haelt fest, dass es den Vertrag gibt, dass er den Pflichtinhalt
abdeckt und dass seine Annahme nachweisbar protokolliert wird. Ob der Wortlaut
juristisch traegt, kann er nicht pruefen — das bleibt anwaltliche Arbeit.
"""

import os
import re

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WURZEL = os.path.dirname(BACKEND)
AVV_SEITE = os.path.join(WURZEL, "landing-react", "src", "app", "avv", "page.tsx")
AGB_SEITE = os.path.join(WURZEL, "landing-react", "src", "app", "agb", "page.tsx")
DSE_SEITE = os.path.join(WURZEL, "landing-react", "src", "app", "datenschutz", "page.tsx")
REGISTRIERUNG = os.path.join(WURZEL, "dashboard-react", "src", "app", "register", "page.tsx")
# Seit dem 11.09.2026 steht die Fassung im Dashboard an EINER Stelle; die
# Registrierung und das Gate fuer Bestandskonten importieren sie von dort.
DASHBOARD_STAND = os.path.join(WURZEL, "dashboard-react", "src", "lib", "vertragsstand.ts")

frontend_da = pytest.mark.skipif(
    not os.path.exists(AVV_SEITE), reason="landing-react nicht eingehaengt")


@frontend_da
@pytest.mark.parametrize("pflicht,fundstelle", [
    ("Weisung", "Art. 28 Abs. 3 lit. a — Verarbeitung nur auf Weisung"),
    ("Vertraulichkeit", "lit. b — Verpflichtung zur Vertraulichkeit"),
    ("Art. 32", "lit. c — Sicherheit der Verarbeitung"),
    ("Unterauftragsverarbeiter", "Abs. 2 und Abs. 4 — weitere Auftragsverarbeiter"),
    ("betroffener Personen", "lit. e — Unterstuetzung bei Betroffenenrechten"),
    ("Art. 33", "lit. f — Meldung von Verletzungen"),
    ("Löschung", "lit. g — Loeschung oder Rueckgabe"),
    ("Überprüfungen", "lit. h — Nachweise und Kontrollen"),
])
def test_avv_deckt_den_pflichtinhalt_ab(pflicht, fundstelle):
    text = open(AVV_SEITE, encoding="utf-8").read()
    assert pflicht in text, f"Im AVV fehlt: {fundstelle}"


@frontend_da
def test_unterauftragsverarbeiter_sind_vollstaendig_benannt():
    """
    Wer Sprachmodelle einsetzt, muss sie nennen. Die Inhalte der geprueften
    Seiten gehen an OpenRouter und von dort an Anthropic und OpenAI, alle in
    den USA.
    """
    text = open(AVV_SEITE, encoding="utf-8").read()
    for name in ("IONOS", "OpenRouter", "Anthropic", "OpenAI"):
        assert name in text, f"{name} fehlt in der Liste der Unterauftragsverarbeiter"
    assert "Standardvertragsklauseln" in text


@frontend_da
def test_datenschutzerklaerung_behauptet_keine_eu_grenze_mehr():
    """
    Die Erklaerung sagte "Eine Übermittlung in Länder außerhalb der
    Europäischen Union findet nicht statt" — waehrend die Inhalte der
    geprueften Seiten an Sprachmodelle in den USA gingen. Eine falsche Angabe
    an dieser Stelle ist selbst ein Verstoss (Art. 13 Abs. 1 lit. f DSGVO).
    """
    text = open(DSE_SEITE, encoding="utf-8").read()
    assert "findet nicht statt" not in text, (
        "Die Datenschutzerklaerung behauptet wieder, es gebe keine "
        "Drittlandsuebermittlung.")
    assert "USA" in text and "Art. 46" in text


@frontend_da
def test_agb_verweisen_auf_den_avv():
    text = open(AGB_SEITE, encoding="utf-8").read()
    assert "/avv" in text, "Die AGB nennen den Auftragsverarbeitungsvertrag nicht"


@pytest.mark.skipif(not os.path.exists(REGISTRIERUNG), reason="dashboard-react nicht eingehaengt")
def test_registrierung_schliesst_den_avv_mit_ab():
    text = open(REGISTRIERUNG, encoding="utf-8").read()
    assert "AVV_VERSION" in text and "avv_version: AVV_VERSION" in text, (
        "Die Registrierung schickt die angenommene AVV-Fassung nicht mit")
    assert "Art. 28" in text, "Der Bestaetigungstext nennt den AVV nicht"


def test_backend_protokolliert_die_avv_fassung():
    quelle = open(os.path.join(BACKEND, "auth_routes.py"), encoding="utf-8").read()
    assert "avv_version" in quelle
    einfuegung = quelle[quelle.index("INSERT INTO vertragsannahmen"):]
    assert "avv_version" in einfuegung[:400], (
        "Die AVV-Fassung wird nicht in vertragsannahmen geschrieben")


def test_fassungen_stimmen_ueberein():
    """Registrierung und Vertragstext duerfen nicht auseinanderlaufen."""
    if not (os.path.exists(DASHBOARD_STAND) and os.path.exists(AVV_SEITE)):
        pytest.skip("Frontends nicht eingehaengt")
    reg = open(DASHBOARD_STAND, encoding="utf-8").read()
    treffer = re.search(r"const AVV_VERSION = '([\d-]+)'", reg)
    assert treffer, "AVV_VERSION fehlt in lib/vertragsstand.ts"
    fassung = treffer.group(1)
    jahr, monat, tag = fassung.split("-")
    seite = open(AVV_SEITE, encoding="utf-8").read()
    monate = {"09": "September", "10": "Oktober", "11": "November", "12": "Dezember",
              "01": "Januar", "02": "Februar", "03": "März", "04": "April",
              "05": "Mai", "06": "Juni", "07": "Juli", "08": "August"}
    erwartet = f"{int(tag)}. {monate[monat]} {jahr}"
    assert erwartet in seite, (
        f"Die Registrierung protokolliert Fassung {fassung}, die Seite nennt einen "
        f"anderen Stand als '{erwartet}'")
