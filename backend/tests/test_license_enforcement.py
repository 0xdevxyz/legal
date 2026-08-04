"""
Lizenzdurchsetzung fuer ausgelieferte Widgets
=============================================

Der Pro-Tarif gilt fuer genau eine Domain; ein Wechsel laeuft ueber den Support.
Wird der Einbettungscode auf eine weitere Seite kopiert, muss das auffallen —
`evaluate_license` erkennt das an der aufrufenden Domain (Origin/Referer).

Die Tests decken vor allem die Fail-open-Regeln ab: Eine faelschlich ausgeloeste
Sperre auf einer zahlenden Kundenseite waere teurer als ein uebersehener
Verstoss. Deshalb gilt bei fehlenden Headern, Legacy-Konfigurationen oder
DB-Fehlern immer "lizenziert".
"""
import os

import pytest

import license_check
from license_check import evaluate_license, host_from_request, url_to_site_id


class FakeRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}


class FakePool:
    """Minimaler asyncpg-Pool-Ersatz: fetchrow -> Config, fetch -> Websites."""

    def __init__(self, cfg_row, urls=(), fail=False):
        self._cfg = cfg_row
        self._urls = list(urls)
        self._fail = fail

    async def fetchrow(self, *args, **kwargs):
        if self._fail:
            raise RuntimeError("DB weg")
        return self._cfg

    async def fetch(self, *args, **kwargs):
        if self._fail:
            raise RuntimeError("DB weg")
        return [{"url": u} for u in self._urls]


@pytest.fixture(autouse=True)
def _standardmodus(monkeypatch):
    """Ohne explizite Angabe gilt der Warnmodus."""
    monkeypatch.delenv("COMPLYO_LICENSE_ENFORCEMENT", raising=False)
    yield


def _kunde(urls=("https://kunde.de",)):
    return FakePool({"user_id": 42}, urls)


class TestHostAbleitung:
    def test_www_und_schema_werden_normalisiert(self):
        assert url_to_site_id("https://www.kunde.de/impressum") == "kunde-de"
        assert url_to_site_id("kunde.de") == "kunde-de"

    def test_port_wird_abgeschnitten(self):
        assert url_to_site_id("http://kunde.de:8080/x") == "kunde-de"

    def test_leere_eingabe_bleibt_leer(self):
        assert url_to_site_id("") == ""
        assert url_to_site_id(None) == ""

    def test_origin_hat_vorrang_vor_referer(self):
        req = FakeRequest({"origin": "https://a.de", "referer": "https://b.de/x"})
        assert host_from_request(req) == "https://a.de"

    def test_referer_springt_ein(self):
        assert host_from_request(FakeRequest({"referer": "https://b.de/x"})) == "https://b.de/x"

    def test_null_origin_zaehlt_nicht(self):
        assert host_from_request(FakeRequest({"origin": "null"})) == ""

    def test_ohne_request_kein_host(self):
        assert host_from_request(None) == ""


@pytest.mark.asyncio
class TestLizenzbewertung:
    async def test_eigene_domain_ist_lizenziert(self):
        req = FakeRequest({"origin": "https://kunde.de"})
        res = await evaluate_license(_kunde(), "kunde-de", req)
        assert res["status"] == "active"
        assert res["active"] is True

    async def test_www_variante_gilt_als_dieselbe_domain(self):
        req = FakeRequest({"origin": "https://www.kunde.de"})
        res = await evaluate_license(_kunde(), "kunde-de", req)
        assert res["status"] == "active"

    async def test_fremde_domain_wird_erkannt(self):
        req = FakeRequest({"origin": "https://andere-seite.de"})
        res = await evaluate_license(_kunde(), "kunde-de", req)
        assert res["status"] == "unlicensed_domain"
        assert res["message"]

    async def test_warnmodus_laesst_den_banner_arbeiten(self):
        req = FakeRequest({"origin": "https://andere-seite.de"})
        res = await evaluate_license(_kunde(), "kunde-de", req)
        assert res["enforced"] is False
        assert res["active"] is True

    async def test_blockmodus_stellt_den_banner_ab(self, monkeypatch):
        monkeypatch.setenv("COMPLYO_LICENSE_ENFORCEMENT", "block")
        req = FakeRequest({"origin": "https://andere-seite.de"})
        res = await evaluate_license(_kunde(), "kunde-de", req)
        assert res["enforced"] is True
        assert res["active"] is False

    async def test_ausschalter_wirkt(self, monkeypatch):
        monkeypatch.setenv("COMPLYO_LICENSE_ENFORCEMENT", "off")
        req = FakeRequest({"origin": "https://andere-seite.de"})
        res = await evaluate_license(_kunde(), "kunde-de", req)
        assert res["status"] == "active"

    async def test_zweite_gebuchte_domain_ist_zulaessig(self):
        pool = _kunde(("https://kunde.de", "https://zweitprojekt.de"))
        req = FakeRequest({"origin": "https://zweitprojekt.de"})
        res = await evaluate_license(pool, "kunde-de", req)
        assert res["status"] == "active"


@pytest.mark.asyncio
class TestFailOpen:
    async def test_ohne_header_keine_sperre(self):
        res = await evaluate_license(_kunde(), "kunde-de", FakeRequest({}))
        assert res["status"] == "active"

    async def test_ohne_pool_keine_sperre(self):
        assert (await evaluate_license(None, "kunde-de", FakeRequest({})))["status"] == "active"

    async def test_ohne_site_id_keine_sperre(self):
        assert (await evaluate_license(_kunde(), "", FakeRequest({})))["status"] == "active"

    async def test_legacy_konfig_ohne_owner_bleibt_unangetastet(self):
        pool = FakePool({"user_id": None}, ["https://kunde.de"])
        req = FakeRequest({"origin": "https://ganz-woanders.de"})
        assert (await evaluate_license(pool, "kunde-de", req))["status"] == "active"

    async def test_unbekannte_site_id_bleibt_unangetastet(self):
        pool = FakePool(None, [])
        req = FakeRequest({"origin": "https://ganz-woanders.de"})
        assert (await evaluate_license(pool, "unbekannt", req))["status"] == "active"

    async def test_db_fehler_bleibt_unangetastet(self):
        pool = FakePool({"user_id": 1}, ["https://kunde.de"], fail=True)
        req = FakeRequest({"origin": "https://ganz-woanders.de"})
        assert (await evaluate_license(pool, "kunde-de", req))["status"] == "active"


@pytest.mark.asyncio
class TestEntzogeneLizenz:
    async def test_geloeschte_website_blockt_immer(self):
        """Der Entzug ist aelter als der Durchsetzungsschalter und darf nicht
        durch den Warnmodus aufgeweicht werden."""
        pool = _kunde(("https://andere.de",))  # kunde-de fehlt in der Liste
        res = await evaluate_license(pool, "kunde-de", FakeRequest({}))
        assert res["status"] == "revoked"
        assert res["enforced"] is True
        assert res["active"] is False

    async def test_entzug_blockt_auch_im_warnmodus(self, monkeypatch):
        monkeypatch.setenv("COMPLYO_LICENSE_ENFORCEMENT", "warn")
        pool = _kunde(("https://andere.de",))
        assert (await evaluate_license(pool, "kunde-de", FakeRequest({})))["active"] is False

    async def test_altfunktion_bleibt_kompatibel(self):
        from license_check import site_has_active_license
        assert await site_has_active_license(_kunde(), "kunde-de") is True
        assert await site_has_active_license(_kunde(("https://x.de",)), "kunde-de") is False
