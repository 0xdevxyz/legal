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


class TestSubdomains:
    """
    Unterbereiche einer gebuchten Domain sind dieselbe Website.

    Ausloeser: complyo selbst. Gebucht ist `complyo.de`, das Widget laeuft auf
    `app.complyo.de` — die Pruefung meldete den eigenen Betrieb als Verstoss.
    Unter `enforcement=block` haette complyo sein eigenes Widget abgeschaltet,
    und jeder Kunde mit Shop- oder Redaktions-Subdomain ebenso.
    """

    @pytest.mark.asyncio
    async def test_subdomain_der_gebuchten_domain_ist_zulaessig(self):
        pool = _kunde(("https://kunde.de",))
        req = FakeRequest({"origin": "https://shop.kunde.de"})
        assert (await evaluate_license(pool, "kunde-de", req))["status"] == "active"

    @pytest.mark.asyncio
    async def test_der_eigene_fall_app_complyo_de(self):
        pool = FakePool({"user_id": 1}, ["https://complyo.de"])
        req = FakeRequest({"origin": "https://app.complyo.de"})
        assert (await evaluate_license(pool, "complyo-de", req))["status"] == "active"

    @pytest.mark.asyncio
    async def test_mehrstufige_subdomain_zaehlt_auch(self):
        pool = _kunde(("https://kunde.de",))
        req = FakeRequest({"origin": "https://a.b.kunde.de"})
        assert (await evaluate_license(pool, "kunde-de", req))["status"] == "active"

    @pytest.mark.asyncio
    async def test_angehaengter_name_ist_keine_subdomain(self):
        """`boesekunde.de` endet auf `kunde.de` — als Text, nicht als Domain."""
        pool = _kunde(("https://kunde.de",))
        req = FakeRequest({"origin": "https://boesekunde.de"})
        assert (await evaluate_license(pool, "kunde-de", req))["status"] == "unlicensed_domain"

    @pytest.mark.asyncio
    async def test_die_domain_selbst_bleibt_bei_gebuchter_subdomain_draussen(self):
        """
        Gebucht ist die Subdomain, aufgerufen die Hauptdomain: das ist eine
        andere, groessere Website und nicht mitgebucht.
        """
        pool = FakePool({"user_id": 7}, ["https://shop.kunde.de"])
        req = FakeRequest({"origin": "https://kunde.de"})
        assert (await evaluate_license(pool, "shop-kunde-de", req))["status"] == "unlicensed_domain"

    @pytest.mark.asyncio
    async def test_fremde_domain_bleibt_ein_verstoss(self):
        pool = _kunde(("https://kunde.de",))
        req = FakeRequest({"origin": "https://ganz-woanders.de"})
        assert (await evaluate_license(pool, "kunde-de", req))["status"] == "unlicensed_domain"


class TestHostVonUrl:
    def test_nur_fuehrendes_www_faellt_weg(self):
        assert license_check.host_von_url("https://www.kunde.de/pfad") == "kunde.de"
        # url_to_site_id entfernt `www.` ueberall im String — hier nicht.
        assert license_check.host_von_url("https://wwww.kunde.de") == "wwww.kunde.de"

    def test_port_und_grossschreibung(self):
        assert license_check.host_von_url("HTTPS://Kunde.DE:8443/x") == "kunde.de"

    def test_leer_bleibt_leer(self):
        assert license_check.host_von_url("") == ""
