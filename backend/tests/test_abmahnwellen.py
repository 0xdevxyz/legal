"""
Tests für den Abmahn-Radar (abmahnwellen.py + Route /api/pflichten-report/abmahnwellen).

Drei Ebenen:
1. Katalog-Wächter: jede Welle hängt an einer Pflicht aus pflichten_katalog,
   trägt Stichwörter für die Befund-Zuordnung und eine plausible Spanne.
2. Betroffenheitslogik mit Beispielprofilen und Säulenwerten.
3. Route mit Auth-Override und gemocktem Pool (Muster: test_backoffice_ehrlichkeit.py).
"""
import json
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from abmahnwellen import (  # noqa: E402
    ABMAHNWELLEN, ART_ABMAHNUNG, ART_BUSSGELD, ART_BEIDES,
    WAHRSCHEINLICH, PRUEFEN, UNWAHRSCHEINLICH, UNBEKANNT,
    betroffenheit_bestimmen, wellen_anreichern, teaser_anwenden,
)
from pflichten_katalog import PFLICHTEN, APPLIES, CHECK, NOT_INDICATED, evaluate_pflichten  # noqa: E402
from dependencies import get_current_user, get_db  # noqa: E402
import pflichten_report_routes  # noqa: E402


# ---------------------------------------------------------------------------
# 1. Katalog-Wächter
# ---------------------------------------------------------------------------

KATALOG_IDS = {r["id"] for r in PFLICHTEN}
KATALOG_PILLARS = {r["scan_pillar"] for r in PFLICHTEN}
PFLICHTFELDER = {
    "id", "titel", "beschreibung", "rule_id", "scan_pillar", "stichwoerter",
    "art", "wer_fordert", "typische_forderung_euro", "forderung_quelle", "seit", "quelle_url",
}


def test_mindestens_die_geforderten_wellen_vorhanden():
    ids = {w["id"] for w in ABMAHNWELLEN}
    for erwartet in ("google_fonts", "cookie_banner_ablehnen", "datenschutzerklaerung",
                     "impressum", "widerruf_shop", "bfsg_barrierefreiheit",
                     "newsletter_ohne_double_opt_in"):
        assert erwartet in ids, f"Welle {erwartet} fehlt"
    assert len(ids) == len(ABMAHNWELLEN), "Wellen-IDs müssen eindeutig sein"


def test_jede_welle_haengt_an_einer_katalogpflicht():
    for w in ABMAHNWELLEN:
        assert PFLICHTFELDER <= set(w.keys()), f"{w['id']}: Felder fehlen {PFLICHTFELDER - set(w.keys())}"
        assert w["rule_id"] in KATALOG_IDS, f"{w['id']}: rule_id {w['rule_id']} nicht im Katalog"
        assert w["scan_pillar"] in KATALOG_PILLARS, f"{w['id']}: unbekannte Säule {w['scan_pillar']}"
        assert w["stichwoerter"] and all(s == s.lower() for s in w["stichwoerter"]), \
            f"{w['id']}: Stichwörter fehlen oder sind nicht kleingeschrieben"
        assert w["art"] in (ART_ABMAHNUNG, ART_BUSSGELD, ART_BEIDES)
        assert len(w["beschreibung"]) > 80 and len(w["titel"]) < 90
        assert w["seit"] and len(w["seit"]) == 7 and w["seit"][4] == "-", f"{w['id']}: seit als JJJJ-MM"


def test_forderungsspanne_plausibel_und_begruendet():
    for w in ABMAHNWELLEN:
        spanne = w["typische_forderung_euro"]
        assert w["forderung_quelle"], f"{w['id']}: Begründung der Spanne fehlt (auch bei null)"
        if spanne is None:
            continue
        assert len(spanne) == 2 and 0 < spanne[0] <= spanne[1] <= 5000, \
            f"{w['id']}: Spanne {spanne} unplausibel (Abmahnkosten, kein Bußgeldrahmen)"


def test_quelle_urls_nur_bekannte_adressen():
    erlaubt = ("https://www.gesetze-im-internet.de/", "https://eur-lex.europa.eu/",
               "https://www.datenschutzkonferenz-de.de/")
    for w in ABMAHNWELLEN:
        url = w["quelle_url"]
        if url is None:
            continue
        assert url.startswith(erlaubt), f"{w['id']}: {url} ist keine bekannte Behörden-/Gesetzesadresse"


def test_beschreibung_ohne_panikmache_und_ohne_lange_striche():
    for w in ABMAHNWELLEN:
        text = w["beschreibung"] + w["titel"] + w["forderung_quelle"]
        assert "—" not in text and "–" not in text, f"{w['id']}: langer Strich im Text"
        for wort in ("sofort", "dringend", "!!!", "Alarm"):
            assert wort not in text, f"{w['id']}: Panikwort {wort!r}"


def test_stichwoerter_treffen_echte_befundtitel():
    """Die Zuordnung im Dashboard läuft über diese Stichwörter; sie müssen
    die tatsächlichen Scanner-Titel treffen, sonst zeigt der Radar nie einen Befund."""
    beispiele = {
        "google_fonts": "Google Fonts (extern geladen)",
        "cookie_banner_ablehnen": "Ablehnen-Knopf fehlt",
        "tracking_vor_einwilligung": "Tracking vor Consent geladen (Google Analytics)",
        "impressum": "Impressum unvollständig",
        "datenschutzerklaerung": "Keine Datenschutzerklärung gefunden",
        "widerruf_shop": "Widerrufsbelehrung fehlt (Online-Shop erkannt)",
        "bfsg_barrierefreiheit": "WCAG 1.1.1: Bild ohne Alt-Text",
        "newsletter_ohne_double_opt_in": "Newsletter-Anmeldung ohne erkennbare Einwilligung",
    }
    by_id = {w["id"]: w for w in ABMAHNWELLEN}
    for wid, titel in beispiele.items():
        assert any(s in titel.lower() for s in by_id[wid]["stichwoerter"]), \
            f"{wid}: kein Stichwort trifft {titel!r}"


# ---------------------------------------------------------------------------
# 2. Betroffenheitslogik
# ---------------------------------------------------------------------------

def test_betroffenheit_grundregeln():
    assert betroffenheit_bestimmen(None, None) == UNBEKANNT
    assert betroffenheit_bestimmen(None, 20) == UNBEKANNT
    assert betroffenheit_bestimmen(NOT_INDICATED, 10) == UNWAHRSCHEINLICH
    assert betroffenheit_bestimmen(APPLIES, 79) == WAHRSCHEINLICH
    assert betroffenheit_bestimmen(APPLIES, 80) == PRUEFEN
    assert betroffenheit_bestimmen(APPLIES, None) == PRUEFEN
    assert betroffenheit_bestimmen(CHECK, None) == PRUEFEN
    # Unklares Profil plus schlechter Scan bleibt „prüfen": kein Rechtsurteil aus dem Scan allein
    assert betroffenheit_bestimmen(CHECK, 30) == PRUEFEN


SHOP_PROFIL = {"employees": "10-49", "revenue": "2-10m", "b2c": True, "online_shop": True, "newsletter": False}
SCAN_SCHLECHT = {
    "url": "https://shop.example.de", "scan_date": "2026-09-10T20:00:00",
    "pillars": {"accessibility": 41.0, "cookies": 55.0, "legal": 90.0, "gdpr": 72.0},
    "overall": 60.0,
}


def test_shop_mit_schlechtem_scan():
    items = evaluate_pflichten(SHOP_PROFIL)["items"]
    wellen = {w["id"]: w for w in wellen_anreichern(items, SCAN_SCHLECHT)}
    # BFSG trifft zu (B2C-Shop, nicht Kleinstunternehmen) und Säule 41 → wahrscheinlich
    assert wellen["bfsg_barrierefreiheit"]["betroffenheit"] == WAHRSCHEINLICH
    assert wellen["bfsg_barrierefreiheit"]["relevanz"]["pillar_score"] == 41.0
    assert wellen["bfsg_barrierefreiheit"]["relevanz"]["scanned_url"] == "https://shop.example.de"
    # Cookies 55 → wahrscheinlich
    assert wellen["cookie_banner_ablehnen"]["betroffenheit"] == WAHRSCHEINLICH
    # Impressum trifft zu, Säule legal 90 → prüfen
    assert wellen["impressum"]["betroffenheit"] == PRUEFEN
    assert wellen["impressum"]["relevanz"]["rule_status"] == APPLIES
    # Newsletter laut Profil nicht → unwahrscheinlich, keine Säule
    assert wellen["newsletter_ohne_double_opt_in"]["betroffenheit"] == UNWAHRSCHEINLICH
    assert wellen["newsletter_ohne_double_opt_in"]["relevanz"]["pillar_score"] is None
    assert wellen["newsletter_ohne_double_opt_in"]["relevanz"]["scan_date"] is None


def test_dienstleister_ohne_shop_ohne_scan():
    profil = {"employees": "1-9", "revenue": "<=2m", "b2c": False, "newsletter": True}
    items = evaluate_pflichten(profil)["items"]
    wellen = {w["id"]: w for w in wellen_anreichern(items, None)}
    assert wellen["widerruf_shop"]["betroffenheit"] == UNWAHRSCHEINLICH
    assert wellen["bfsg_barrierefreiheit"]["betroffenheit"] == UNWAHRSCHEINLICH
    # Trifft zu, aber nichts gemessen → prüfen, nie wahrscheinlich
    assert wellen["impressum"]["betroffenheit"] == PRUEFEN
    assert wellen["google_fonts"]["betroffenheit"] == PRUEFEN
    assert wellen["newsletter_ohne_double_opt_in"]["betroffenheit"] == PRUEFEN
    assert all(w["relevanz"]["pillar_score"] is None for w in wellen.values())


def test_ohne_profil_alles_unbekannt_auch_mit_scan():
    wellen = wellen_anreichern(None, SCAN_SCHLECHT)
    assert len(wellen) == len(ABMAHNWELLEN)
    assert all(w["betroffenheit"] == UNBEKANNT for w in wellen)
    # Der Säulenwert darf trotzdem gezeigt werden: er ist gemessen, nur die Pflicht ist unklar
    by_id = {w["id"]: w for w in wellen}
    assert by_id["bfsg_barrierefreiheit"]["relevanz"]["pillar_score"] == 41.0


def test_sortierung_wahrscheinlich_zuerst_unwahrscheinlich_zuletzt():
    items = evaluate_pflichten(SHOP_PROFIL)["items"]
    reihenfolge = [w["betroffenheit"] for w in wellen_anreichern(items, SCAN_SCHLECHT)]
    rang = {WAHRSCHEINLICH: 0, PRUEFEN: 1, UNBEKANNT: 2, UNWAHRSCHEINLICH: 3}
    assert reihenfolge == sorted(reihenfolge, key=rang.get)
    assert reihenfolge[0] == WAHRSCHEINLICH


def test_teaser_sperrt_ab_der_dritten_welle():
    items = evaluate_pflichten(SHOP_PROFIL)["items"]
    wellen = teaser_anwenden(wellen_anreichern(items, SCAN_SCHLECHT), 2)
    assert [w["locked"] for w in wellen[:2]] == [False, False]
    assert all(w["locked"] and w["betroffenheit"] is None and w["relevanz"] is None for w in wellen[2:])
    # Titel und Beschreibung bleiben sichtbar
    assert all(w["titel"] and w["beschreibung"] for w in wellen)


# ---------------------------------------------------------------------------
# 3. Route
# ---------------------------------------------------------------------------

class _FakePool:
    """Beantwortet fetchrow nach dem Tabellennamen in der Abfrage."""

    def __init__(self, profil=None, scan=None, plan="pro"):
        self.profil = profil
        self.scan = scan
        self.plan = plan

    async def fetchrow(self, query, *args):
        if "company_profiles" in query:
            return {"answers": json.dumps(self.profil)} if self.profil is not None else None
        if "scan_history" in query:
            return self.scan
        if "user_limits" in query:
            return {"plan_type": self.plan}
        raise AssertionError(f"unerwartete Abfrage: {query}")


def _client(pool):
    app = FastAPI()
    app.include_router(pflichten_report_routes.router)
    app.dependency_overrides[get_current_user] = lambda: {"id": 7, "email": "t@example.de"}
    app.dependency_overrides[get_db] = lambda: pool
    return TestClient(app)


SCAN_ROW = {
    "url": "https://shop.example.de", "overall_score": 60.0, "accessibility_score": 41.0,
    "cookie_score": 55.0, "legal_score": 90.0, "privacy_score": 72.0,
    "scan_date": datetime(2026, 9, 10, 20, 0, 0),
}


def test_route_ohne_auth_verweigert():
    app = FastAPI()
    app.include_router(pflichten_report_routes.router)
    r = TestClient(app).get("/api/pflichten-report/abmahnwellen")
    assert r.status_code in (401, 403)


def test_route_pro_mit_profil_und_scan():
    r = _client(_FakePool(SHOP_PROFIL, SCAN_ROW, "pro")).get("/api/pflichten-report/abmahnwellen")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["profil_vorhanden"] is True and d["locked"] is False and d["teaser"] is None
    assert d["total"] == len(ABMAHNWELLEN) == len(d["wellen"])
    assert d["scan_context"]["url"] == "https://shop.example.de"
    by_id = {w["id"]: w for w in d["wellen"]}
    assert by_id["bfsg_barrierefreiheit"]["betroffenheit"] == WAHRSCHEINLICH
    assert by_id["bfsg_barrierefreiheit"]["relevanz"]["scan_date"] == "2026-09-10T20:00:00"
    assert by_id["widerruf_shop"]["relevanz"]["rule_status"] == APPLIES
    assert "keine Rechtsberatung" in d["hinweis"]
    assert all(w["locked"] is False for w in d["wellen"])


def test_route_ohne_profil_kein_404():
    r = _client(_FakePool(None, None, "pro")).get("/api/pflichten-report/abmahnwellen")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["profil_vorhanden"] is False
    assert d["scan_context"] is None
    assert all(w["betroffenheit"] == UNBEKANNT for w in d["wellen"])
    assert "Fragebogen" in d["hinweis"]


def test_route_free_teaser():
    r = _client(_FakePool(SHOP_PROFIL, SCAN_ROW, "free")).get("/api/pflichten-report/abmahnwellen")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["locked"] is True
    assert len(d["wellen"]) == len(ABMAHNWELLEN), "Free sieht alle Wellen, nur ohne Einschätzung"
    offen = [w for w in d["wellen"] if not w["locked"]]
    gesperrt = [w for w in d["wellen"] if w["locked"]]
    assert len(offen) == 2 and len(gesperrt) == len(ABMAHNWELLEN) - 2
    assert all(w["betroffenheit"] is None and w["relevanz"] is None for w in gesperrt)
    assert d["teaser"]["hidden_count"] == len(gesperrt)
    # Die beiden offenen sind die relevantesten (Sortierung vor dem Sperren)
    assert offen[0]["betroffenheit"] == WAHRSCHEINLICH


def test_route_liegt_im_pflichten_router():
    pfade = {r.path for r in pflichten_report_routes.router.routes}
    assert "/api/pflichten-report/abmahnwellen" in pfade
