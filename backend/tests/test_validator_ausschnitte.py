# -*- coding: utf-8 -*-
"""
Die KI-Zweitmeinung liest die ganze Seite, nicht nur ihren Anfang.

Gemessen im Pruefstand vom 08.10.2026 gegen von Hand etikettierte Seiten (die
Etiketten liegen nicht im Repo, es sind Kundendomains): bei den falschen
"X fehlt"-Befunden im Datenschutz stand die Angabe jedes Mal weit hinten im Text.
Eine Seite mit eigenem Abschnitt "11. Beschwerderecht bei der Aufsichtsbehoerde"
(Seitentext rund 9.700 Zeichen) bekam kritisch "Beschwerderecht fehlt", eine
zweite "Rechtsgrundlagen fehlen", obwohl Art. 6 DSGVO dort zweimal steht (Text
31.000 Zeichen).

Ursache: `_create_batch_validation_prompt` gab der KI die ersten 6.000 Zeichen
der Seite. Von 21 gefundenen Datenschutzerklaerungen sind 15 laenger. Die KI
antwortete fuer alles dahinter mit "nicht gefunden": zu Recht, bezogen auf den
Auszug. Der Validator gab das als Feststellung ueber die ganze Seite weiter.

Jetzt liest die KI aufeinanderfolgende Auszuege, und "nicht gefunden" gilt nur,
wenn sie die ganze Seite gesehen hat. Alle Tests ersetzen den KI-Aufruf, ohne Netz.
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine import ai_budget
from compliance_engine.checks.deep_content_analyzer import ContentValidation
from compliance_engine.hybrid_validator import HybridValidator


def _text(laenge, einfuegen=None):
    """Fliesstext aus durchnummerierten Woertern, optional mit einem Satz an einer Stelle."""
    teile, n = [], 0
    while sum(len(t) + 1 for t in teile) < laenge:
        teile.append(f"wort{n:05d}")
        n += 1
    text = " ".join(teile)[:laenge]
    if einfuegen:
        pos, satz = einfuegen
        text = text[:pos] + " " + satz + " " + text[pos:]
    return text


def _felder(*namen):
    return {n: ContentValidation(field_name=n, found=False, confidence=0.0, extracted_value=None)
            for n in namen}


class _KI:
    """Ersetzt den OpenRouter-Aufruf: findet ein Feld, wenn sein Merkwort im Auszug steht."""

    def __init__(self, merkwoerter, fehler_bei=None):
        self.merkwoerter = merkwoerter
        self.fehler_bei = fehler_bei
        self.aufrufe = []   # je Aufruf: (Nummer, Felder, Laenge)

    async def __call__(self, hv, offen, teil, page_type, user_id, nr=1, von=1):
        self.aufrufe.append((nr, sorted(offen), len(teil)))
        if self.fehler_bei == nr:
            return {}
        return {f: {"found": self.merkwoerter.get(f, "GIBTESNICHT_ANDERES") in teil, "confidence": 0.9, "value": "x", "reasoning": "Test"}
                for f in offen}


@pytest.fixture
def ki(monkeypatch):
    def setze(merkwoerter, fehler_bei=None):
        k = _KI(merkwoerter, fehler_bei)

        async def ersatz(hv, offen, teil, page_type, user_id, nr=1, von=1):
            return await k(hv, offen, teil, page_type, user_id, nr, von)

        monkeypatch.setattr(HybridValidator, "_ai_batch_ausschnitt", ersatz)
        return k
    return setze


def _batch(text, felder):
    return asyncio.run(HybridValidator()._ai_validate_fields_batch(felder, text, "datenschutz", None))


# --- Auszuege ---------------------------------------------------------------------

def test_kurzer_text_ist_ein_auszug_und_vollstaendig():
    teile, voll = HybridValidator()._batch_ausschnitte("kurz")
    assert teile == ["kurz"] and voll is True


def test_laenger_als_ein_auszug_wird_zerlegt_und_deckt_alles_ab():
    hv = HybridValidator()
    text = _text(20000)
    teile, voll = hv._batch_ausschnitte(text)
    assert voll is True and 2 <= len(teile) <= hv._BATCH_MAX_AUSSCHNITTE
    assert all(len(t) <= hv._BATCH_ZEICHEN for t in teile)
    for wort in text.split():
        assert any(wort in t for t in teile), f"{wort} steht in keinem Auszug"


def test_sehr_langer_text_wird_gekappt_und_ist_nicht_vollstaendig():
    hv = HybridValidator()
    teile, voll = hv._batch_ausschnitte(_text(60000))
    assert len(teile) == hv._BATCH_MAX_AUSSCHNITTE and voll is False


def test_die_laengste_erklaerung_des_bestands_wird_ganz_gelesen():
    """42.500 Zeichen (die laengste der 19 etikettierten Erklaerungen) brauchen acht Auszuege.

    Mit der alten Kappung von vier blieb sie zur Haelfte ungelesen, und vier Felder
    endeten als "nicht abschliessend geprueft".
    """
    teile, voll = HybridValidator()._batch_ausschnitte(_text(42600))
    assert voll is True and len(teile) == 8


def test_die_naht_schneidet_kein_wort_durch():
    hv = HybridValidator()
    text = _text(20000)
    teile, _ = hv._batch_ausschnitte(text)
    woerter = set(text.split())
    for t in teile:
        assert t.split()[0] in woerter and t.split()[-1] in woerter


# --- Der Fehler: die Angabe steht hinter dem ersten Auszug -------------------------

def test_angabe_hinter_dem_ersten_auszug_wird_gefunden(ki):
    k = ki({"beschwerderecht": "BESCHWERDEMARKE"})
    text = _text(12000, (9000, "BESCHWERDEMARKE"))
    r = _batch(text, _felder("beschwerderecht"))
    assert r["beschwerderecht"]["found"] is True, (
        "Die KI hat nur den Anfang gesehen und meldet 'nicht gefunden'.")
    assert not r["beschwerderecht"].get("unvollstaendig")
    assert [a[0] for a in k.aufrufe] == [1, 2]


def test_angabe_im_ersten_auszug_kostet_nur_einen_aufruf(ki):
    k = ki({"beschwerderecht": "BESCHWERDEMARKE"})
    text = _text(12000, (500, "BESCHWERDEMARKE"))
    _batch(text, _felder("beschwerderecht"))
    assert len(k.aufrufe) == 1


def test_spaetere_aufrufe_fragen_nur_noch_offene_felder(ki):
    k = ki({"a": "MARKE_A", "b": "MARKE_B"})
    text = _text(14000, (500, "MARKE_A"))
    text = text[:12000] + " MARKE_B " + text[12000:]
    r = _batch(text, _felder("a", "b"))
    assert r["a"]["found"] and r["b"]["found"]
    assert k.aufrufe[0][1] == ["a", "b"]
    assert all(felder == ["b"] for _, felder, _ in k.aufrufe[1:]), k.aufrufe


# --- Kein "fehlt" ohne die ganze Seite gesehen zu haben ----------------------------

def test_wirklich_fehlend_nach_der_ganzen_seite_bleibt_fehlend(ki):
    ki({"beschwerderecht": "GIBTESNICHT"})
    r = _batch(_text(15000), _felder("beschwerderecht"))
    assert r["beschwerderecht"]["found"] is False
    assert not r["beschwerderecht"].get("unvollstaendig"), "Gegenprobe: echte Luecken muessen Luecken bleiben"


def test_fehlend_bei_zu_langer_seite_ist_nicht_geprueft(ki):
    ki({"beschwerderecht": "GIBTESNICHT"})
    r = _batch(_text(60000), _felder("beschwerderecht"))
    assert r["beschwerderecht"]["found"] is False and r["beschwerderecht"]["unvollstaendig"] is True


def test_scheitert_ein_spaeterer_aufruf_ist_fehlend_nicht_geprueft(ki):
    ki({"beschwerderecht": "GIBTESNICHT"}, fehler_bei=2)
    r = _batch(_text(15000), _felder("beschwerderecht"))
    assert r["beschwerderecht"]["unvollstaendig"] is True


def test_scheitert_der_erste_aufruf_gibt_es_nichts_zurueck(ki):
    ki({"beschwerderecht": "x"}, fehler_bei=1)
    assert _batch(_text(15000), _felder("beschwerderecht")) == {}


# --- Durch validate_page: der Befund -----------------------------------------------

def _validate(monkeypatch, text, ki_antwort):
    async def budget_frei(*_a, **_k):
        return True
    monkeypatch.setattr(ai_budget, "budget_frei", budget_frei)
    monkeypatch.setattr(HybridValidator, "_ai_batch_ausschnitt", ki_antwort)
    v = HybridValidator()
    monkeypatch.setattr(v, "api_key", "nur-fuer-den-test")
    res = asyncio.run(v.validate_page("datenschutz", text, "https://beispiel.example/ds"))
    return {r["field"]: r for r in res["results"]}


def test_validate_page_findet_die_angabe_hinter_dem_ersten_auszug(monkeypatch):
    marke = "Beschwerderecht bei der Aufsichtsbehörde Unbeschadet anderweitiger Rechtsbehelfe steht Ihnen ein Beschwerderecht zu"
    text = _text(14000, (11000, marke))
    k = _KI({"beschwerderecht": "Beschwerderecht bei der Aufsichtsbehörde"})

    async def ki_antwort(hv, offen, teil, page_type, user_id, nr=1, von=1):
        return await k(hv, offen, teil, page_type, user_id, nr, von)

    felder = _validate(monkeypatch, text, ki_antwort)
    b = felder["beschwerderecht"]
    assert b["found"] is True and b["unverifiziert"] is False


def test_validate_page_macht_aus_unvollstaendig_nicht_geprueft(monkeypatch):
    k = _KI({"beschwerderecht": "GIBTESNICHT", "zwecke": "GIBTESNICHT"})

    async def ki_antwort(hv, offen, teil, page_type, user_id, nr=1, von=1):
        return await k(hv, offen, teil, page_type, user_id, nr, von)

    felder = _validate(monkeypatch, _text(60000), ki_antwort)
    b = felder["beschwerderecht"]
    assert b["found"] is False and b["unverifiziert"] is True, (
        "Eine Seite, die die KI nicht ganz gesehen hat, darf nicht als 'fehlt' enden.")


def test_prompt_sagt_der_ki_dass_sie_nur_einen_auszug_sieht():
    hv = HybridValidator()
    p = hv._create_batch_validation_prompt(_felder("zwecke"), "text", "datenschutz", 2, 4)
    assert "Auszug 2 von 4" in p and "DIESEM Auszug" in p
    einzel = hv._create_batch_validation_prompt(_felder("zwecke"), "text", "datenschutz")
    assert "Auszug 1 von" not in einzel


# --- Zeitgrenze ---------------------------------------------------------------------

def test_zeitgrenze_bricht_das_weiterlesen_ab_und_macht_fehlend_zu_nicht_geprueft(monkeypatch):
    """Eine sehr langsame KI darf die Pruefung nicht beliebig dehnen."""
    import compliance_engine.hybrid_validator as modul

    uhr = {"jetzt": 1000.0}
    monkeypatch.setattr(modul.time, "monotonic", lambda: uhr["jetzt"])
    aufrufe = []

    async def ersatz(hv, offen, teil, page_type, user_id, nr=1, von=1):
        aufrufe.append(nr)
        uhr["jetzt"] += 30.0          # jeder Call "dauert" 30 Sekunden
        return {f: {"found": False, "confidence": 0.9, "value": "x", "reasoning": "Test"} for f in offen}

    monkeypatch.setattr(HybridValidator, "_ai_batch_ausschnitt", ersatz)
    r = _batch(_text(30000), _felder("beschwerderecht"))
    assert aufrufe == [1, 2], f"nach 60 Sekunden haette Schluss sein muessen: {aufrufe}"
    assert r["beschwerderecht"]["found"] is False and r["beschwerderecht"]["unvollstaendig"] is True


def test_ohne_zeitdruck_wird_alles_gelesen(monkeypatch):
    k = _KI({"beschwerderecht": "GIBTESNICHT"})

    async def ersatz(hv, offen, teil, page_type, user_id, nr=1, von=1):
        return await k(hv, offen, teil, page_type, user_id, nr, von)

    monkeypatch.setattr(HybridValidator, "_ai_batch_ausschnitt", ersatz)
    r = _batch(_text(30000), _felder("beschwerderecht"))
    assert len(k.aufrufe) == 6 and not r["beschwerderecht"].get("unvollstaendig")
