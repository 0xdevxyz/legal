# -*- coding: utf-8 -*-
"""
Eine knappe Datenschutzerklaerung ist eine Erklaerung, keine Nicht-Erklaerung.

Gefunden im Pruefstand vom 02.10.2026 und am 07.10.2026 nachgemessen an
einer Kundenseite (Ingenieurbuero): Die Seite /datenschutzerklaerung/ ist eine Standardvorlage
mit Titel und H1 "Datenschutzerklaerung", acht Abschnitten und rund 5.000
Zeichen Text. Sie nennt aber weniger als zwei der neun Merkmale, die die
Inhaltsschranke verlangt (Verantwortlicher, Rechtsgrundlage, Betroffenenrechte
und so weiter). Die Schranke lehnte sie ab, und der Kunde las kritisch
(5.000 EUR) "Datenschutz-Link fuehrt zu keiner Datenschutzerklaerung". Das ist
falsch: die Erklaerung existiert, sie ist knapp.

Verhalten vorher: critical "Datenschutz-Link fuehrt zu keiner Datenschutz-
erklaerung". Verhalten jetzt: Hinweis "Datenschutzerklaerung gefunden, aber
sehr knapp" (info, 0 EUR) mit den gemessenen Stichworten, und die Seite geht
durch dieselbe Auswertung wie jede andere Erklaerung.

Die Fixtures bilden die Struktur der Seite nach (Titel mit Seitennamen, H1,
Abschnitte, Menue und Fusszeile), nicht ihren Text.

Gegenproben, damit die Nachschaerfung die Schranke nicht aushoehlt:
  * eine kurze, aber vollstaendige Erklaerung gilt nicht als knapp
  * Behoerdenseite, Cookie-Einstellungen, Platzhalter, Startseite bleiben
    "keine Erklaerung"
  * die Schranke selbst bleibt streng (knapp ist eine eigene, zweite Stufe)
"""

import asyncio
import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks import datenschutz_check as dsc
from compliance_engine.checks import rechtsseiten_links as rl
from compliance_engine.checks import rechtsseiten_text as rt

TITEL_KEIN_RECHTSTEXT = 'Datenschutz-Link führt zu keiner Datenschutzerklärung'
TITEL_KNAPP = 'Datenschutzerklärung gefunden, aber sehr knapp'


@pytest.fixture(autouse=True)
def ohne_ki(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


def _seite(titel, h1, body_text, menue="Start Leistungen Kontakt Impressum Datenschutz",
           fuss="Muster Ingenieure GmbH, Musterweg 1, 04109 Leipzig"):
    kopf = f"<h1>{h1}</h1>" if h1 else ""
    return (f"<html><head><title>{titel}</title></head><body>"
            f"<nav>{menue}</nav><header>Logo</header><main>{kopf}{body_text}</main>"
            f"<footer>{fuss}</footer></body></html>")


# Eigener Text im Stil einer Standardvorlage (Anrede "du", Abschnitte mit
# Ueberschriften), bewusst ohne die Merkmale der Schranke: kein Verantwortlicher,
# keine Rechtsgrundlage, keine Betroffenenrechte, keine Aufsichtsbehoerde.
_DUENN_ABSCHNITTE = [
    ("Wer wir sind", "Die Adresse unserer Website ist https://beispiel-ingenieure.example. "
     "Wir betreiben diese Seite, um unsere Leistungen vorzustellen und erreichbar zu sein. "
     "Auf diesen Seiten findest du Informationen zu unserem Büro, zu Referenzen und zu "
     "unseren Ansprechpartnern."),
    ("Welche personenbezogenen Daten wir sammeln und warum wir sie sammeln",
     "Kommentare: Wenn Besucher Kommentare auf der Website schreiben, sammeln wir die Daten, "
     "die im Kommentarformular angezeigt werden, außerdem die IP-Adresse des Besuchers und den "
     "User-Agent-String, um das Erkennen von unerwünschten Beiträgen zu erleichtern. "
     "Medien: Wenn du Bilder auf die Website lädst, solltest du vermeiden, Bilder mit "
     "eingebetteten Standort-Informationen hochzuladen."),
    ("Kontaktformulare", "Wenn du uns über das Formular schreibst, speichern wir deine Nachricht "
     "und die angegebene E-Mail-Adresse, damit wir antworten können."),
    ("Cookies", "Wenn du einen Kommentar auf unserer Website schreibst, kannst du einwilligen, "
     "deinen Namen, deine E-Mail-Adresse und Website in Cookies zu speichern. Dies ist eine "
     "Komfortfunktion, damit du diese Daten nicht erneut eingeben musst. Diese Cookies "
     "bleiben ein Jahr lang gültig."),
    ("Eingebettete Inhalte von anderen Websites", "Beiträge auf dieser Website können "
     "eingebettete Inhalte beinhalten, zum Beispiel Videos, Bilder oder Artikel. Eingebettete "
     "Inhalte von anderen Websites verhalten sich exakt so, als ob der Besucher die andere "
     "Website besucht hätte."),
    ("Mit wem wir deine Daten teilen", "Wenn du ein Zurücksetzen deines Passworts beantragst, "
     "wird deine IP-Adresse in der E-Mail zum Zurücksetzen enthalten sein."),
    ("Wie lange wir deine Daten speichern", "Wenn du einen Kommentar schreibst, bleiben "
     "Kommentar und Metadaten unbefristet erhalten."),
    ("Weitere Informationen", "Bei Fragen erreichst du uns über die Angaben im Impressum."),
]


def _duenn_html():
    body = "".join(f"<h2>{h}</h2><p>{t}</p>" for h, t in _DUENN_ABSCHNITTE)
    return _seite("Datenschutzerklärung \u2013 Beispiel Ingenieure GmbH", "Datenschutzerklärung", body)


# Kurz, aber vollstaendig: sechs der neun Merkmale, unter der Mindestlaenge fuer
# "knapp". Muss die Schranke direkt bestehen und darf nie als knapp gelten.
_KURZ_VOLLSTAENDIG = (
    "<p>Verantwortlicher für diese Website ist die Beispiel GmbH, Musterweg 1, 04109 Leipzig, "
    "info@beispiel.example.</p>"
    "<p>Wir verarbeiten personenbezogene Daten (IP-Adresse, Zeitpunkt des Abrufs) in Server-"
    "Logfiles, um die Seite sicher auszuliefern. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO.</p>"
    "<p>Speicherdauer: Die Logfiles werden nach sieben Tagen gelöscht.</p>"
    "<p>Betroffenenrechte: Sie haben das Recht auf Auskunft, Berichtigung und Löschung. "
    "Sie können sich bei einer Aufsichtsbehörde beschweren.</p>"
)


def _kurz_html():
    return _seite("Datenschutzerklärung | Beispiel GmbH", "Datenschutzerklärung", _KURZ_VOLLSTAENDIG)


def _text(html):
    return rl._fliesstext(html)


# --- Voraussetzungen der Fixtures: sonst beweisen die Tests nichts -------------

def test_fixture_duenn_besteht_die_schranke_nicht():
    """Das ist der Auslöser: die Schranke lehnt die Vorlage ab."""
    text = _text(_duenn_html())
    assert dsc._looks_like_datenschutz(text) is False
    assert len(dsc._ds_merkmale(text)[0]) < 2


def test_fixture_duenn_ist_lang_genug_und_kurz_ist_es_nicht():
    assert len(rt.inhaltstext(_duenn_html())) >= rt.DUENN_MINDESTENS["datenschutz"]
    assert len(rt.inhaltstext(_kurz_html())) < rt.DUENN_MINDESTENS["datenschutz"]


def test_fixture_kurz_besteht_die_schranke():
    assert dsc._looks_like_datenschutz(_text(_kurz_html())) is True


# --- Die Auswahl: ist_duenne_erklaerung ----------------------------------------

def test_titel_und_h1_beide_passen():
    assert rt.ist_duenne_erklaerung(_duenn_html(), "datenschutz") is True


def test_nur_h1_genuegt():
    html = _seite("Beispiel GmbH", "Datenschutzerklärung", "<p>" + "Text zur Sache. " * 100 + "</p>")
    assert rt.ist_duenne_erklaerung(html, "datenschutz") is True


def test_nur_titel_genuegt_vor_dem_seitennamen():
    html = _seite("Datenschutz | Beispiel GmbH", "", "<p>" + "Text zur Sache. " * 100 + "</p>")
    assert rt.ist_duenne_erklaerung(html, "datenschutz") is True


def test_seitenname_im_titel_zaehlt_nicht():
    """Der Titel wird vor dem Trenner gelesen: 'Datenschutz' hinter dem Seitennamen ist keiner."""
    html = _seite("Startseite | Datenschutzerklärung Beispiel", "Willkommen",
                  "<p>" + "Text zur Sache. " * 100 + "</p>")
    assert rt.ist_duenne_erklaerung(html, "datenschutz") is False


@pytest.mark.parametrize("titel,h1", [
    ("Sächsischer Datenschutz- und Transparenzbeauftragter", "Sächsischer Datenschutz- und Transparenzbeauftragter"),
    ("Datenschutz- und Transparenzbeauftragter", "Datenschutz- und Transparenzbeauftragter"),
    ("Datenschutz-Einstellungen", "Datenschutz-Einstellungen"),
    ("Cookie-Einstellungen | Beispiel", "Datenschutz Einstellungen und Cookies"),
    ("Willkommen bei Beispiel", "Willkommen"),
    ("Kontakt", "Kontakt"),
])
def test_gegenprobe_andere_seiten_sind_nicht_knapp(titel, h1):
    """Lang genug und das Wort Datenschutz im Text, aber die Ueberschrift sagt etwas anderes."""
    body = ("<p>Zum Thema Datenschutz informieren wir hier. " + "Weitere Hinweise folgen. " * 80 + "</p>")
    assert rt.ist_duenne_erklaerung(_seite(titel, h1, body), "datenschutz") is False


def test_gegenprobe_platzhalter_unter_der_mindestlaenge():
    html = _seite("Datenschutzerklärung", "Datenschutzerklärung",
                  "<p>Unsere Datenschutzerklärung folgt in Kürze.</p>")
    assert rt.ist_duenne_erklaerung(html, "datenschutz") is False


def test_menue_und_fusszeile_zaehlen_nicht_zur_laenge():
    html = _seite("Datenschutzerklärung", "Datenschutzerklärung", "<p>Kurzer Platzhalter.</p>",
                  menue="Menüpunkt " * 400, fuss="Fußzeilentext " * 400)
    assert len(rl._fliesstext(html)) > 5000
    assert rt.ist_duenne_erklaerung(html, "datenschutz") is False


def test_schwelle_genau_an_der_grenze():
    mindestens = rt.DUENN_MINDESTENS["datenschutz"]

    def html_mit_laenge(n):
        leer = _seite("Datenschutzerklärung", "Datenschutzerklärung", "<p></p>")
        fehlt = n - len(rt.inhaltstext(leer)) - 1  # ein Leerzeichen trennt H1 und Absatz
        return _seite("Datenschutzerklärung", "Datenschutzerklärung", f"<p>{'x' * fehlt}</p>")

    assert len(rt.inhaltstext(html_mit_laenge(mindestens))) == mindestens
    assert rt.ist_duenne_erklaerung(html_mit_laenge(mindestens), "datenschutz") is True
    assert rt.ist_duenne_erklaerung(html_mit_laenge(mindestens - 1), "datenschutz") is False


def test_impressum_hat_keine_schwelle():
    """Fuer das Impressum zeigt der Bestand keinen Fall; die Schranke bleibt, wie sie ist."""
    assert rt.ist_duenne_erklaerung(_seite("Impressum", "Impressum", "<p>" + "x " * 800 + "</p>"),
                                    "impressum") is False


# --- Die Merkmale: gebeugte Formen ---------------------------------------------

@pytest.mark.parametrize("satz", [
    "Die Verarbeitung personenbezogener Daten erfolgt auf dieser Seite.",
    "Wir schützen Ihre personenbezogenen Daten.",
    "Welche personenbezogene Daten wir sammeln.",
])
def test_personenbezogene_daten_in_jeder_beugung(satz):
    assert "personenbezogene Daten" in dsc._ds_merkmale(satz)[0]


def test_eine_beugung_allein_reicht_der_schranke_nicht():
    """Stichwort plus nur ein Merkmal bleibt abgelehnt: die Schranke wurde nicht gelockert."""
    assert dsc._looks_like_datenschutz("Datenschutz: wir schützen Ihre personenbezogenen Daten.") is False


def test_zwei_merkmale_in_gebeugter_form_bestehen():
    assert dsc._looks_like_datenschutz(
        "Datenschutz: Verantwortlicher ist die Beispiel GmbH. Wir schützen personenbezogener Daten.") is True


# --- Die ganze Kette: lade_rechtsseite und der Check ----------------------------

class _Antwort:
    def __init__(self, status, text):
        self.status, self._text = status, text

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False


class _Session:
    def __init__(self, seiten):
        self.seiten = seiten
        self.abrufe = []

    def get(self, url, **_):
        self.abrufe.append(url)
        for pfad, html in self.seiten.items():
            if url.rstrip("/") == pfad.rstrip("/"):
                return _Antwort(200, html)
        return _Antwort(404, "<html><body>nicht gefunden</body></html>")


STARTSEITE = ("<html><body><h1>Beispiel GmbH</h1><p>Wir beraten.</p>"
              '<footer><a href="/datenschutzerklaerung/">Datenschutz</a></footer></body></html>')
BASIS = "https://beispiel.example"
DS_URL = BASIS + "/datenschutzerklaerung/"


def _check(seitenhtml):
    session = _Session({DS_URL: seitenhtml})
    soup = BeautifulSoup(STARTSEITE, "html.parser")
    return asyncio.run(dsc.check_datenschutz_compliance(BASIS + "/", soup, session))


def _titel(befunde):
    return [b["title"] for b in befunde]


def test_vorher_nachher_duenne_erklaerung_ist_kein_kritischer_befund():
    """Der Fall des Ingenieurbueros: nicht mehr 'fuehrt zu keiner Datenschutzerklaerung'."""
    befunde = _check(_duenn_html())
    titel = _titel(befunde)
    assert TITEL_KEIN_RECHTSTEXT not in titel
    assert TITEL_KNAPP in titel
    assert not [b for b in befunde if b["category"] == "datenschutz" and b["severity"] == "critical"
                and "fehl" in b["title"].lower()], titel


def test_knapp_ist_ein_hinweis_ohne_betrag_mit_gemessenen_stichworten():
    knapp = [b for b in _check(_duenn_html()) if b["title"] == TITEL_KNAPP][0]
    assert knapp["severity"] == "info"
    assert knapp["risk_euro"] == 0
    assert knapp["is_missing"] is False
    gefunden, fehlt = dsc._ds_merkmale(rt.inhaltstext(_duenn_html()))
    assert f"{len(gefunden)} von {len(dsc._DS_MERKMALE)}" in knapp["description"]
    assert DS_URL in knapp["description"]
    for name in fehlt:
        assert name in knapp["description"]
    assert "keine Feststellung eines Mangels" in knapp["description"]


def test_knappe_erklaerung_geht_durch_die_normale_auswertung():
    """Gelesen heisst bewertet: der Validator sieht den Text und meldet, was er nicht pruefen konnte."""
    titel = _titel(_check(_duenn_html()))
    assert any(t.startswith("Datenschutzerklärung:") and "nicht abschliessend geprueft" in t for t in titel), titel


def test_gegenprobe_kurze_vollstaendige_erklaerung_ist_nicht_knapp():
    befunde = _check(_kurz_html())
    titel = _titel(befunde)
    assert TITEL_KNAPP not in titel
    assert TITEL_KEIN_RECHTSTEXT not in titel


@pytest.mark.parametrize("name,html", [
    ("behoerde", _seite("Sächsischer Datenschutz- und Transparenzbeauftragter",
                        "Sächsischer Datenschutz- und Transparenzbeauftragter",
                        "<p>" + "Informationen zum Thema Datenschutz für Bürger. " * 60 + "</p>")),
    ("cookie-dialog", _seite("Datenschutz-Einstellungen", "Datenschutz-Einstellungen",
                             "<p>" + "Wählen Sie, welche Cookies Sie zulassen. " * 60 + "</p>")),
    ("platzhalter", _seite("Datenschutzerklärung", "Datenschutzerklärung",
                           "<p>Folgt in Kürze, Datenschutz ist uns wichtig.</p>")),
    ("startseite", _seite("Beispiel GmbH", "Willkommen bei Beispiel",
                          "<p>" + "Wir beraten Sie in Fragen des Datenschutz. " * 60 + "</p>")),
])
def test_gegenprobe_keine_erklaerung_bleibt_kritisch(name, html):
    titel = _titel(_check(html))
    assert TITEL_KEIN_RECHTSTEXT in titel, (name, titel)
    assert TITEL_KNAPP not in titel, (name, titel)


def test_lade_rechtsseite_ohne_duenn_funktion_bleibt_ganz_oder_gar_nicht():
    session = _Session({DS_URL: _duenn_html()})
    soup = BeautifulSoup(STARTSEITE, "html.parser")
    g = asyncio.run(rl.lade_rechtsseite(BASIS + "/", "/datenschutzerklaerung/", soup, session,
                                        dsc._looks_like_datenschutz))
    assert g.ok is False and g.problem == rl.PROBLEM_KEIN_RECHTSTEXT and g.duenn is False


def test_lade_rechtsseite_mit_duenn_funktion_liefert_den_text():
    session = _Session({DS_URL: _duenn_html()})
    soup = BeautifulSoup(STARTSEITE, "html.parser")
    g = asyncio.run(rl.lade_rechtsseite(BASIS + "/", "/datenschutzerklaerung/", soup, session,
                                        dsc._looks_like_datenschutz, duenn_aus_wie=dsc._duenn_aus_wie))
    assert g.ok is True and g.duenn is True and "Wer wir sind" in g.html


def test_vollstaendige_seite_wird_nie_als_duenn_markiert():
    session = _Session({DS_URL: _kurz_html()})
    soup = BeautifulSoup(STARTSEITE, "html.parser")
    g = asyncio.run(rl.lade_rechtsseite(BASIS + "/", "/datenschutzerklaerung/", soup, session,
                                        dsc._looks_like_datenschutz, duenn_aus_wie=dsc._duenn_aus_wie))
    assert g.ok is True and g.duenn is False


# --- Direkt-URL-Fallback (kein Link auf der Seite) ------------------------------

def _existiert(seitenhtml):
    session = _Session({BASIS + "/datenschutz": seitenhtml})
    return asyncio.run(dsc._check_datenschutz_url_exists(BASIS + "/", session))


def test_direkt_url_knappe_erklaerung_zaehlt_als_vorhanden():
    assert _existiert(_duenn_html()) is True


def test_direkt_url_gegenprobe_platzhalter_und_startseite_zaehlen_nicht():
    platzhalter = _seite("Datenschutzerklärung", "Datenschutzerklärung", "<p>Folgt in Kürze.</p>")
    startseite = _seite("Beispiel GmbH", "Willkommen", "<p>" + "Datenschutz ist uns wichtig. " * 80 + "</p>")
    assert _existiert(platzhalter) is False
    assert _existiert(startseite) is False
