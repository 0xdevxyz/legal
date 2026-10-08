# -*- coding: utf-8 -*-
"""
Ein Treffer unter der Feldschwelle ist eine Vermutung, kein "fehlt".

Gemessen im Pruefstand vom 07.10.2026 (ohne KI) an Kundenseiten, je mit
Belegzitat von der Seite (die Zitate stehen in der Auswertung, nicht im Repo):
  * zwei Seiten mit eigenem Text zum Beschwerderecht bei der Aufsichtsbehoerde,
    Scanner: kritisch "Beschwerderecht fehlt"
  * eine Seite mit "Recht auf Auskunft, Recht auf Berichtigung oder Loeschung",
    Scanner: kritisch "Betroffenenrechte fehlen"
  * zwei Impressen mit Telefonnummer (Mindestschwelle des Feldes 0,8, Treffer
    0,78), Scanner: kritisch "Telefonnummer fehlt im Impressum"

Ursache: `_calculate_match_confidence` vergibt den Laengenbonus nur fuer Werte
von 10 bis 200 Zeichen. Ein Treffer mit 201 bis 500 Zeichen ohne Punkt (ein
langer Satz, wie ihn Datenschutzerklaerungen schreiben) bleibt bei 0,5 mal
Kontextbonus 1,2 = 0,6, also unter der Feldschwelle 0,65/0,7. Der Validator
behandelte alles ab 0,6 als "Grenzfall" und reichte `found=False` als
Feststellung weiter. Die Laengenregel zu aendern wuerde alle Felder verschieben;
die Regel hier ist enger: wer etwas gefunden hat und sich nicht sicher ist,
sagt nicht "fehlt".

Alle Laeufe ohne KI und ohne Netz.
"""

import asyncio
import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine import ai_budget
from compliance_engine.checks import datenschutz_check as dsc
from compliance_engine.checks import impressum_check as imc
from compliance_engine.checks.deep_content_analyzer import DeepContentAnalyzer
from compliance_engine.hybrid_validator import HybridValidator


@pytest.fixture(autouse=True)
def ohne_ki(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


# Eigene Saetze mit der Form der Belege: ein langer Satz ohne Punkt, 360 Zeichen.
BESCHWERDE_LANG = (
    "Beschwerderecht bei der Aufsichtsbehörde Unbeschadet anderweitiger Rechtsbehelfe steht Ihnen "
    "ein Beschwerderecht bei einer Datenschutz-Aufsichtsbehörde zu wenn Sie der Ansicht sind dass die "
    "Verarbeitung Ihrer Daten gegen geltendes Recht verstößt und Sie können sich dazu an die für Ihren "
    "Wohnort zuständige Stelle wenden ohne dass Ihnen daraus Nachteile entstehen."
)
RECHTE_LANG = (
    "Ihre Rechte Sie haben das Recht auf Auskunft über die gespeicherten Daten, auf Berichtigung "
    "unrichtiger Daten und auf Löschung sowie auf Einschränkung der Verarbeitung und Sie können der "
    "Verarbeitung widersprechen, außerdem steht Ihnen das Recht auf Datenübertragbarkeit zu soweit die "
    "gesetzlichen Voraussetzungen vorliegen und kein anderer Grund entgegensteht."
)
# Dieselben Angaben kurz: sicherer Treffer (0,78), nie ein Grenzfall.
BESCHWERDE_KURZ = "Beschwerderecht bei der Aufsichtsbehörde: Sie können sich jederzeit an die zuständige Behörde wenden."
RECHTE_KURZ = ("Ihre Rechte: Sie haben das Recht auf Auskunft, Berichtigung und Löschung Ihrer gespeicherten "
               "Daten sowie auf Einschränkung der Verarbeitung.")

# Genug Merkmale, damit die Seite die Inhaltsschranke besteht.
RUMPF = ("Datenschutzerklärung. Verantwortlicher ist die Beispiel GmbH, Musterweg 1, 04109 Leipzig. "
         "Wir verarbeiten personenbezogene Daten zur Auslieferung der Seite. Rechtsgrundlage ist Art. 6 "
         "Abs. 1 lit. f DSGVO. Die Speicherdauer der Logfiles beträgt sieben Tage. ")


def _analyse(text, feld):
    a = DeepContentAnalyzer()
    return a._validate_field(feld, a.datenschutz_patterns[feld], text, None)


def _felder(text):
    res = asyncio.run(HybridValidator().validate_page("datenschutz", text, "https://beispiel.example/ds"))
    return {r["field"]: r for r in res["results"]}


# --- Voraussetzung: der Fehler ist da -------------------------------------------

@pytest.mark.parametrize("text,feld", [(BESCHWERDE_LANG, "beschwerderecht"), (RECHTE_LANG, "betroffenenrechte")])
def test_ausloeser_langer_satz_landet_unter_der_feldschwelle(text, feld):
    """Der Treffer ist da, sein Wert ist lang (201 bis 500 Zeichen), die Confidence bleibt bei 0,6."""
    v = _analyse(text, feld)
    assert v.extracted_value and 200 < len(v.extracted_value) <= 500
    assert v.confidence == pytest.approx(0.6)
    assert v.found is False


@pytest.mark.parametrize("text,feld", [(BESCHWERDE_KURZ, "beschwerderecht"), (RECHTE_KURZ, "betroffenenrechte")])
def test_gegenprobe_kurzer_satz_ist_sicher(text, feld):
    v = _analyse(text, feld)
    assert v.found is True and v.confidence >= 0.7


# --- Der Validator: kein "fehlt" fuer einen unsicheren Treffer ----------------------

@pytest.mark.parametrize("text,feld", [(BESCHWERDE_LANG, "beschwerderecht"), (RECHTE_LANG, "betroffenenrechte")])
def test_unsicherer_treffer_ist_nicht_geprueft_statt_fehlend(text, feld):
    feldergebnis = _felder(RUMPF + text)[feld]
    assert feldergebnis["found"] is False
    assert feldergebnis["unverifiziert"] is True, "ein Treffer unter der Schwelle ist keine Feststellung"


@pytest.mark.parametrize("text,feld", [(BESCHWERDE_KURZ, "beschwerderecht"), (RECHTE_KURZ, "betroffenenrechte")])
def test_gegenprobe_sicherer_treffer_bleibt_gefunden(text, feld):
    feldergebnis = _felder(RUMPF + text)[feld]
    assert feldergebnis["found"] is True and feldergebnis["unverifiziert"] is False


def test_gegenprobe_nichts_gefunden_bleibt_nicht_geprueft():
    """Der Zustand von vorher bleibt: ohne Treffer und ohne KI wird nichts behauptet."""
    f = _felder(RUMPF)["beschwerderecht"]
    assert f["found"] is False and f["unverifiziert"] is True and f["confidence"] == 0.0


# --- Der Check: der Kunde liest kein "fehlt" -----------------------------------------

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

    def get(self, url, **_):
        for pfad, html in self.seiten.items():
            if url.rstrip("/") == pfad.rstrip("/"):
                return _Antwort(200, html)
        return _Antwort(404, "<html><body>nicht gefunden</body></html>")


def _check(absatz):
    ds = f"<html><head><title>Datenschutzerklärung</title></head><body><h1>Datenschutzerklärung</h1><p>{RUMPF}{absatz}</p></body></html>"
    start = '<html><body><h1>Beispiel</h1><footer><a href="/datenschutz/">Datenschutz</a></footer></body></html>'
    session = _Session({"https://beispiel.example/datenschutz/": ds})
    return asyncio.run(dsc.check_datenschutz_compliance(
        "https://beispiel.example/", BeautifulSoup(start, "html.parser"), session))


def test_check_meldet_kein_kritisches_fehlt_bei_langem_satz():
    titel = [b["title"] for b in _check(BESCHWERDE_LANG + " " + RECHTE_LANG)]
    assert "Beschwerderecht fehlt" not in titel
    assert "Betroffenenrechte fehlen" not in titel
    ungeprueft = [b for b in _check(BESCHWERDE_LANG)
                  if b["title"].startswith("Datenschutzerklärung:") and "nicht abschliessend" in b["title"]]
    assert ungeprueft and "beschwerderecht" in ungeprueft[0]["description"]


def test_check_gegenprobe_kurzer_satz_ist_gefunden_und_still():
    befunde = _check(BESCHWERDE_KURZ + " " + RECHTE_KURZ)
    titel = [b["title"] for b in befunde]
    assert "Beschwerderecht fehlt" not in titel and "Betroffenenrechte fehlen" not in titel
    for b in befunde:
        if "nicht abschliessend" in b["title"]:
            assert "beschwerderecht" not in b["description"] and "betroffenenrechte" not in b["description"]


# --- Mit KI: der unsichere Treffer geht zur Zweitmeinung (ohne Netz, KI-Aufruf ersetzt) --

def test_mit_ki_geht_der_unsichere_treffer_zur_zweitmeinung(monkeypatch):
    gesehen = {}

    async def budget_frei(*_a, **_k):
        return True

    async def ki_stapel(self, unsichere_felder, text_content, page_type, user_id):
        gesehen["felder"] = set(unsichere_felder)
        return {n: {"found": True, "confidence": 0.9, "value": "ja", "reasoning": "Test"}
                for n in unsichere_felder}

    monkeypatch.setattr(ai_budget, "budget_frei", budget_frei)
    monkeypatch.setattr(HybridValidator, "_ai_validate_fields_batch", ki_stapel)
    v = HybridValidator()
    monkeypatch.setattr(v, "api_key", "nur-fuer-den-test")
    res = asyncio.run(v.validate_page("datenschutz", RUMPF + BESCHWERDE_LANG, "https://beispiel.example/ds"))
    felder = {r["field"]: r for r in res["results"]}
    assert "beschwerderecht" in gesehen["felder"]
    assert felder["beschwerderecht"]["found"] is True and felder["beschwerderecht"]["method"] == "ai"


def test_mit_ki_gegenprobe_sicherer_treffer_kostet_keinen_aufruf(monkeypatch):
    gesehen = {}

    async def budget_frei(*_a, **_k):
        return True

    async def ki_stapel(self, unsichere_felder, text_content, page_type, user_id):
        gesehen["felder"] = set(unsichere_felder)
        return {}

    monkeypatch.setattr(ai_budget, "budget_frei", budget_frei)
    monkeypatch.setattr(HybridValidator, "_ai_validate_fields_batch", ki_stapel)
    v = HybridValidator()
    monkeypatch.setattr(v, "api_key", "nur-fuer-den-test")
    asyncio.run(v.validate_page("datenschutz", RUMPF + BESCHWERDE_KURZ, "https://beispiel.example/ds"))
    assert "beschwerderecht" not in gesehen.get("felder", set())


# --- Dasselbe im Impressum: Telefonnummer mit Fax oder WhatsApp daneben ---------------

# Zwei Nummern hintereinander machen den Treffer lang (mehr als 20 Zeichen am
# Stueck): Confidence 0,78 gegen die Feldschwelle 0,8. Die Nummer steht da.
IMPRESSUM_MIT_FAX = (
    "Impressum Angaben gemäß § 5 DDG Beispiel GmbH Musterweg 1 04109 Leipzig "
    "Kontakt: Telefon: 0341 / 1234 5678 Fax: 0341 / 1234 5679 E-Mail: info@beispiel.example"
)
IMPRESSUM_EINFACH = (
    "Impressum Beispiel GmbH Musterweg 1 04109 Leipzig Telefon: 0341 123456 E-Mail: info@beispiel.example"
)


def _imp_felder(text):
    res = asyncio.run(HybridValidator().validate_page("impressum", text, "https://beispiel.example/impressum"))
    return {r["field"]: r for r in res["results"]}


def test_impressum_telefon_mit_fax_ist_nicht_geprueft_statt_fehlend():
    t = _imp_felder(IMPRESSUM_MIT_FAX)["telefon"]
    assert t["found"] is False and t["unverifiziert"] is True


def test_impressum_gegenprobe_einfache_nummer_bleibt_gefunden():
    t = _imp_felder(IMPRESSUM_EINFACH)["telefon"]
    assert t["found"] is True and t["unverifiziert"] is False


def _imp_check(impressum_html):
    start = '<html><body><h1>Beispiel</h1><footer><a href="/impressum/">Impressum</a></footer></body></html>'
    session = _Session({"https://beispiel.example/impressum/": f"<html><body><h1>Impressum</h1><p>{impressum_html}</p></body></html>"})
    return asyncio.run(imc.check_impressum_compliance(
        "https://beispiel.example/", BeautifulSoup(start, "html.parser"), session))


def test_impressum_check_meldet_keine_fehlende_telefonnummer_bei_vorhandener():
    titel = [b["title"] for b in _imp_check(IMPRESSUM_MIT_FAX)]
    assert not [t for t in titel if t.startswith("Telefonnummer fehlt")], titel


def test_impressum_gegenprobe_ohne_telefon_wird_nichts_behauptet():
    """Ohne KI bleibt eine fehlende Angabe 'nicht abschliessend geprueft', wie vor der Aenderung."""
    befunde = _imp_check("Impressum Beispiel GmbH Musterweg 1 04109 Leipzig E-Mail: info@beispiel.example")
    assert not [b for b in befunde if b["title"].startswith("Telefonnummer fehlt")]
    ungeprueft = [b for b in befunde if b["title"].startswith("Impressum:") and "nicht abschliessend" in b["title"]]
    assert ungeprueft and "telefon" in ungeprueft[0]["description"]
