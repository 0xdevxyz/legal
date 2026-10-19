"""Prüfstufe des Banner-Scans: Zuordnung ohne Fehlbehauptung, Last unter Kontrolle.

Zwei Dinge dürfen nie passieren, und diese Tests halten sie fest:

1. Ein Dienst im Banner, den die Seite gar nicht lädt (falsche Zuordnung kostet
   Vertrauen). Deshalb gibt es hier so viele Fälle für google.com, googleapis.com,
   Teilstrings und Cookie-Namen, die in der Praxis mehrdeutig sind.
2. Ein Browser zu viel. Bei 100 gleichzeitigen Nutzern darf nie mehr laufen, als
   die Arbeiter und der gemeinsame Browser-Semaphor zulassen, und kein Auftrag
   darf hängen bleiben.
"""

import asyncio
import json
import os
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine import cookie_pruefstufe as ps

# Ausschnitt des Live-Katalogs (Stand 19.10.2026), genau die Fälle, die Ärger machen.
KATALOG = [
    {"service_key": "google_fonts", "name": "Google Fonts", "domains": ["fonts.googleapis.com", "fonts.gstatic.com"]},
    {"service_key": "google_maps", "name": "Google Maps", "domains": ["google.com", "googleapis.com"]},
    {"service_key": "google_recaptcha", "name": "reCAPTCHA", "domains": ["google.com", "recaptcha.net"]},
    {"service_key": "google_analytics_ga4", "name": "GA4", "domains": ["google-analytics.com", "googletagmanager.com"]},
    {"service_key": "google_tag_manager", "name": "GTM", "domains": ["googletagmanager.com"]},
    {"service_key": "youtube", "name": "YouTube", "domains": ["youtube.com", "youtube-nocookie.com"]},
    {"service_key": "facebook_pixel", "name": "FB Pixel", "domains": ["facebook.com", "connect.facebook.net"]},
    {"service_key": "facebook_plugin", "name": "FB Plugin", "domains": ["facebook.com"]},
    {"service_key": "hotjar", "name": "Hotjar", "domains": ["hotjar.com", "static.hotjar.com"]},
    {"service_key": "matomo", "name": "Matomo", "domains": ["custom"]},
    {"service_key": "wordpress", "name": "WordPress", "domains": []},
]
INDEX = ps.baue_index(KATALOG)


def zu(url):
    return ps.zuordnen(url, INDEX)


# --------------------------------------------------------------------------
# Zuordnung
# --------------------------------------------------------------------------

class TestZuordnung:
    def test_genaueste_domain_gewinnt(self):
        assert zu("https://fonts.googleapis.com/css2?family=Jost")[:2] == ("eindeutig", "google_fonts")
        assert zu("https://fonts.gstatic.com/s/jost.woff2")[:2] == ("eindeutig", "google_fonts")

    def test_fonts_werden_nie_zu_maps(self):
        # googleapis.com steht im Katalog bei Maps. Ein Fonts-Aufruf darf nicht dort landen.
        assert zu("https://fonts.googleapis.com/css")[1] != "google_maps"

    def test_breiter_host_ordnet_nie_von_selbst_zu(self):
        status, dienst, _ = zu("https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js")
        assert (status, dienst) == ("breit", None)
        assert zu("https://www.google.com/search?q=x")[:2] == ("breit", None)
        assert zu("https://bucket.s3.amazonaws.com/a.js")[0] != "eindeutig"

    def test_pfadregel_trennt_google_dienste(self):
        assert zu("https://www.google.com/recaptcha/api.js")[:2] == ("eindeutig", "google_recaptcha")
        assert zu("https://www.google.com/maps/embed?pb=1")[:2] == ("eindeutig", "google_maps")
        assert zu("https://maps.googleapis.com/maps/api/js?key=x")[:2] == ("eindeutig", "google_maps")

    def test_tag_manager_nur_mit_ausdruecklicher_kennung(self):
        assert zu("https://www.googletagmanager.com/gtag/js?id=G-ABC123")[:2] == ("eindeutig", "google_analytics_ga4")
        assert zu("https://www.googletagmanager.com/gtm.js?id=GTM-XYZ")[:2] == ("eindeutig", "google_tag_manager")
        # Google-Ads-Kennung: weder GA4 noch GTM behaupten
        status, dienst, kand = zu("https://www.googletagmanager.com/gtag/js?id=AW-123")
        assert status == "mehrdeutig" and dienst is None
        assert set(kand) == {"google_analytics_ga4", "google_tag_manager"}

    def test_mehrfach_belegte_domain_ist_mehrdeutig(self):
        status, dienst, kand = zu("https://www.facebook.com/tr?id=1")
        assert (status, dienst) == ("mehrdeutig", None)
        assert set(kand) == {"facebook_pixel", "facebook_plugin"}
        # Der speziellere Host gehört nur dem Pixel
        assert zu("https://connect.facebook.net/en_US/fbevents.js")[:2] == ("eindeutig", "facebook_pixel")

    def test_teilstring_in_der_url_zaehlt_nicht(self):
        # Der Katalog-Treffer des Premium-Scanners wäre hier "youtube".
        assert zu("https://shop.example.com/share?u=https://youtube.com/watch")[0] == "unbekannt"
        assert zu("https://youtube.com.evil.example/x")[0] == "unbekannt"
        assert zu("https://notyoutube.com/x")[0] == "unbekannt"

    def test_unterdomain_eines_katalogdienstes_trifft(self):
        assert zu("https://static.hotjar.com/c/hotjar.js")[:2] == ("eindeutig", "hotjar")
        assert zu("https://script.hotjar.com/modules.js")[:2] == ("eindeutig", "hotjar")

    def test_platzhalter_domains_werden_ignoriert(self):
        assert "custom" not in INDEX and "first-party" not in INDEX
        assert zu("https://custom/x")[0] == "unbekannt"

    def test_kaputte_url_wirft_nicht(self):
        assert zu("")[0] == "unbekannt"
        assert zu("not a url")[0] == "unbekannt"


class TestEigenerHost:
    def test_eigene_domain_und_unterdomains(self):
        assert ps.ist_eigener_host("cdn.kunde.de", "www.kunde.de")
        assert ps.ist_eigener_host("kunde.de", "kunde.de")

    def test_fremde_domain_mit_gleichem_namen_ist_fremd(self):
        assert not ps.ist_eigener_host("kunde.de.evil.com", "kunde.de")
        assert not ps.ist_eigener_host("kunde.com", "kunde.de")

    def test_zweite_ebene(self):
        assert ps.registrierbar("shop.example.co.uk") == "example.co.uk"
        assert ps.registrierbar("www.example.de") == "example.de"


class TestBewertung:
    def _lauf(self, urls, bekannt, cookies=()):
        return ps.bewerte([{"url": u} for u in urls], [{"name": c} for c in cookies],
                          "https://www.kunde.de/", INDEX, bekannt)

    def test_neu_bestaetigt_und_nur_html(self):
        b = self._lauf(
            ["https://www.kunde.de/a.js", "https://static.hotjar.com/c/h.js",
             "https://fonts.googleapis.com/css", "https://fonts.googleapis.com/css2"],
            bekannt=["google_fonts", "wordpress"],
        )
        assert b["browser_keys"] == ["google_fonts", "hotjar"]
        assert b["bestaetigt"] == ["google_fonts"]
        assert b["neu"] == ["hotjar"]
        assert b["nur_html"] == ["wordpress"]
        assert b["requests_eigene"] == 1

    def test_eigene_requests_erzeugen_nie_einen_dienst(self):
        b = self._lauf(["https://www.kunde.de/wp-content/x.js", "https://cdn.kunde.de/y.css"], bekannt=[])
        assert b["browser_keys"] == [] and b["neu"] == []

    def test_mehrdeutiges_ergaenzt_nichts_bestaetigt_aber_bekanntes(self):
        b = self._lauf(["https://www.facebook.com/tr?id=1"], bekannt=["facebook_pixel"])
        assert b["neu"] == []
        assert "facebook.com" in "".join(b["mehrdeutig"]) or "www.facebook.com" in b["mehrdeutig"]
        assert "facebook_pixel" not in b["nur_html"]

    def test_cookie_namen_allein_fuegen_nichts_hinzu(self):
        b = self._lauf([], bekannt=[], cookies=["NID", "ts", "sid", "PHPSESSID"])
        assert b["neu"] == [] and b["browser_keys"] == []
        assert b["cookies_gesamt"] == 4

    def test_unbekannte_fremdhosts_kommen_in_die_pruefliste(self):
        b = self._lauf(["https://tracker.unbekannt.io/p.gif"] * 3 + ["https://cdn.andere.net/x.js"], bekannt=[])
        assert b["unbekannte_fremdhosts"]["tracker.unbekannt.io"] == 3
        assert b["neu"] == []

    def test_kaputte_eintraege_werfen_nicht(self):
        b = ps.bewerte([{}, {"url": None}, {"url": "::::"}], [{}], "https://kunde.de", INDEX, [])
        assert b["browser_keys"] == []


# --------------------------------------------------------------------------
# Banner-Konfiguration: nur hinzufügen
# --------------------------------------------------------------------------

class FakePool:
    """Bildet cookie_services und cookie_banner_configs gerade weit genug nach."""

    def __init__(self, services=None, konfigurationen=None):
        self.cfg = {k: list(v) for k, v in (konfigurationen or {}).items()}
        self.katalog_aufrufe = 0
        self.schreibzugriffe = 0
        self.vor_dem_schreiben = None  # Hook: simuliert parallele Änderung

    async def fetch(self, sql, *a):
        if "FROM cookie_services" in sql:
            self.katalog_aufrufe += 1
            return [{"service_key": s["service_key"], "name": s["name"], "category": "functional",
                     "provider": "", "template": json.dumps({"domains": s["domains"]})} for s in KATALOG]
        if "FROM cookie_banner_configs" in sql:
            return [{"site_id": k, "last_scan_url": f"https://{k}"} for k in self.cfg]
        raise AssertionError(sql)

    async def fetchrow(self, sql, site_id):
        if site_id not in self.cfg:
            return None
        return {"services": json.dumps(self.cfg[site_id])}

    async def execute(self, sql, site_id, neu_json, alt_json):
        if self.vor_dem_schreiben:
            self.vor_dem_schreiben(self)
            self.vor_dem_schreiben = None
        if self.cfg.get(site_id) != json.loads(alt_json):
            return "UPDATE 0"
        self.cfg[site_id] = json.loads(neu_json)
        self.schreibzugriffe += 1
        return "UPDATE 1"


@pytest.mark.asyncio
class TestAnwenden:
    async def test_fuegt_nur_hinzu_und_behaelt_bestand(self):
        pool = FakePool(konfigurationen={"kunde-de": ["wordpress", "google_fonts"]})
        zusatz = await ps.anwenden(pool, "kunde-de", ["hotjar"])
        assert zusatz == ["hotjar"]
        assert pool.cfg["kunde-de"] == ["wordpress", "google_fonts", "hotjar"]

    async def test_nichts_neues_schreibt_nichts(self):
        pool = FakePool(konfigurationen={"kunde-de": ["hotjar"]})
        assert await ps.anwenden(pool, "kunde-de", ["hotjar"]) == []
        assert pool.schreibzugriffe == 0

    async def test_ohne_konfiguration_wird_keine_angelegt(self):
        pool = FakePool()
        assert await ps.anwenden(pool, "gibt-es-nicht", ["hotjar"]) == []
        assert pool.cfg == {}

    async def test_parallele_aenderung_geht_nicht_verloren(self):
        pool = FakePool(konfigurationen={"kunde-de": ["wordpress"]})
        # Zwischen Lesen und Schreiben setzt der HTML-Scan die Liste neu.
        pool.vor_dem_schreiben = lambda p: p.cfg.__setitem__("kunde-de", ["wordpress", "youtube"])
        zusatz = await ps.anwenden(pool, "kunde-de", ["hotjar"])
        assert zusatz == ["hotjar"]
        assert pool.cfg["kunde-de"] == ["wordpress", "youtube", "hotjar"]


# --------------------------------------------------------------------------
# Schlange und Arbeiter
# --------------------------------------------------------------------------

class Messung:
    """Zählt, wie viele Browser gleichzeitig liefen."""

    def __init__(self, dauer=0.05):
        self.dauer = dauer
        self.jetzt = 0
        self.spitze = 0
        self.gestartet = []
        self.urls = {}

    async def lauf(self, url, katalog):
        self.jetzt += 1
        self.spitze = max(self.spitze, self.jetzt)
        self.gestartet.append(url)
        try:
            await asyncio.sleep(self.dauer)
            reqs = self.urls.get(url, ["https://static.hotjar.com/c/hotjar.js"])
            return SimpleNamespace(error=None, requests=[SimpleNamespace(url=u) for u in reqs], cookies=[])
        finally:
            self.jetzt -= 1


@pytest_asyncio.fixture
async def umgebung(monkeypatch):
    """Frischer Zustand, kein Redis, kleiner Semaphor, Messung statt Browser."""
    m = Messung()
    sem = asyncio.Semaphore(6)
    monkeypatch.setattr(ps, "_browser_lauf", m.lauf)
    monkeypatch.setattr(ps, "_browser_semaphor", lambda: sem)

    async def kein_redis():
        return None
    monkeypatch.setattr(ps, "_redis", kein_redis)
    monkeypatch.setattr(ps, "ARBEITER_ANZAHL", 2)
    monkeypatch.setattr(ps, "SCHLANGE_MAX", 200)
    monkeypatch.setattr(ps, "JOB_ZEIT_S", 10)
    monkeypatch.setattr(ps, "WIEDERHOLSPERRE_S", 600)
    monkeypatch.setattr(ps, "WOCHE_AKTIV", False)
    ps._jobs.clear()
    ps._katalog_cache.update(zeit=0.0, katalog=[], index={})
    ps._dauern.clear()
    umg = SimpleNamespace(m=m, sem=sem, monkeypatch=monkeypatch)
    yield umg
    await ps.beende()
    ps._jobs.clear()


async def warte_fertig(site_ids, timeout=20):
    ende = time.time() + timeout
    while time.time() < ende:
        if all(ps._jobs.get(s, {}).get("zustand") in (ps.FERTIG, ps.FEHLGESCHLAGEN) for s in site_ids):
            return
        await asyncio.sleep(0.02)
    offen = [s for s in site_ids if ps._jobs.get(s, {}).get("zustand") not in (ps.FERTIG, ps.FEHLGESCHLAGEN)]
    raise AssertionError(f"{len(offen)} Auftraege nicht fertig: {offen[:5]}")


@pytest.mark.asyncio
class TestLast:
    async def test_hundert_gleichzeitige_nutzer_nie_mehr_als_zwei_browser(self, umgebung):
        pool = FakePool(konfigurationen={f"kunde-{i}-de": ["wordpress"] for i in range(100)})
        await ps.starte()
        ids = [f"kunde-{i}-de" for i in range(100)]
        antworten = await asyncio.gather(*[
            ps.einreihen(s, f"https://{s}/", pool=pool, html_keys=["wordpress"]) for s in ids
        ])
        assert all(a["zustand"] in ("wartend", "laeuft") for a in antworten)
        await warte_fertig(ids)
        assert umgebung.m.spitze <= 2
        assert len(umgebung.m.gestartet) == 100                    # keiner verloren
        assert all(ps._jobs[s]["zustand"] == ps.FERTIG for s in ids)
        assert all("hotjar" in pool.cfg[s] for s in ids)           # Ergebnis angewendet

    async def test_gemeinsamer_semaphor_begrenzt_zusaetzlich(self, umgebung):
        # Die Landing-Scans halten vier der sechs Plätze: für die Prüfstufe bleibt einer.
        umgebung.monkeypatch.setattr(ps, "_browser_semaphor", lambda: sem1)
        sem1 = asyncio.Semaphore(1)
        pool = FakePool(konfigurationen={f"s{i}-de": [] for i in range(10)})
        await ps.starte()
        ids = [f"s{i}-de" for i in range(10)]
        for s in ids:
            await ps.einreihen(s, f"https://{s}/", pool=pool)
        await warte_fertig(ids)
        assert umgebung.m.spitze == 1

    async def test_selbe_seite_mehrfach_laeuft_nur_einmal(self, umgebung):
        pool = FakePool(konfigurationen={"kunde-de": []})
        await ps.starte()
        antworten = await asyncio.gather(*[ps.einreihen("kunde-de", "https://kunde.de/", pool=pool) for _ in range(20)])
        await warte_fertig(["kunde-de"])
        assert len(umgebung.m.gestartet) == 1
        assert sum(1 for a in antworten if a.get("bereits_im_auftrag")) == 19

    async def test_frisches_ergebnis_wird_wiederverwendet(self, umgebung):
        pool = FakePool(konfigurationen={"kunde-de": []})
        await ps.starte()
        await ps.einreihen("kunde-de", "https://kunde.de/", pool=pool)
        await warte_fertig(["kunde-de"])
        zweite = await ps.einreihen("kunde-de", "https://kunde.de/", pool=pool)
        assert zweite == {"zustand": ps.FERTIG, "zwischengespeichert": True}
        assert len(umgebung.m.gestartet) == 1

    async def test_nach_der_sperrfrist_laeuft_er_neu(self, umgebung):
        umgebung.monkeypatch.setattr(ps, "WIEDERHOLSPERRE_S", 0)
        pool = FakePool(konfigurationen={"kunde-de": []})
        await ps.starte()
        await ps.einreihen("kunde-de", "https://kunde.de/", pool=pool)
        await warte_fertig(["kunde-de"])
        await asyncio.sleep(0.01)
        await ps.einreihen("kunde-de", "https://kunde.de/", pool=pool)
        await warte_fertig(["kunde-de"])
        assert len(umgebung.m.gestartet) == 2

    async def test_volle_schlange_meldet_voll_und_haelt_den_rest(self, umgebung):
        umgebung.monkeypatch.setattr(ps, "SCHLANGE_MAX", 5)
        umgebung.m.dauer = 0.3
        pool = FakePool(konfigurationen={f"s{i}-de": [] for i in range(30)})
        await ps.starte()
        antworten = [await ps.einreihen(f"s{i}-de", f"https://s{i}.de/", pool=pool) for i in range(30)]
        zustaende = [a["zustand"] for a in antworten]
        assert "voll" in zustaende
        angenommen = [f"s{i}-de" for i, a in enumerate(antworten) if a["zustand"] != "voll"]
        assert len(angenommen) >= 5
        await warte_fertig(angenommen)
        assert umgebung.m.spitze <= 2

    async def test_aus_schalter_nimmt_nichts_an(self, umgebung):
        umgebung.monkeypatch.setattr(ps, "AKTIV", False)
        assert (await ps.einreihen("x-de", "https://x.de/"))["zustand"] == "aus"

    async def test_ohne_gestartete_arbeiter_ist_es_aus_nicht_fehler(self, umgebung):
        assert (await ps.einreihen("x-de", "https://x.de/"))["zustand"] == "aus"


@pytest.mark.asyncio
class TestFehlerwege:
    async def test_haengender_browser_wird_nach_dem_zeitbudget_beendet(self, umgebung):
        umgebung.monkeypatch.setattr(ps, "JOB_ZEIT_S", 0.2)
        beendet = []

        async def haengt(url, katalog):
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                beendet.append(url)
                raise
        umgebung.monkeypatch.setattr(ps, "_browser_lauf", haengt)
        pool = FakePool(konfigurationen={"a-de": [], "b-de": []})
        await ps.starte()
        t0 = time.time()
        await ps.einreihen("a-de", "https://a.de/", pool=pool)
        await warte_fertig(["a-de"], timeout=5)
        assert time.time() - t0 < 3
        assert ps._jobs["a-de"]["zustand"] == ps.FEHLGESCHLAGEN
        assert "Zeitbudget" in ps._jobs["a-de"]["fehler"]
        assert beendet == ["https://a.de/"]                      # Browser wurde abgebrochen
        # Der Arbeiter lebt weiter und nimmt den nächsten Auftrag.
        umgebung.monkeypatch.setattr(ps, "_browser_lauf", umgebung.m.lauf)
        await ps.einreihen("b-de", "https://b.de/", pool=pool)
        await warte_fertig(["b-de"])
        assert ps._jobs["b-de"]["zustand"] == ps.FERTIG

    async def test_browserfehler_scheitert_nur_diesen_auftrag(self, umgebung):
        async def kaputt(url, katalog):
            if "boese" in url:
                raise RuntimeError("Chromium abgestuerzt")
            return await umgebung.m.lauf(url, katalog)
        umgebung.monkeypatch.setattr(ps, "_browser_lauf", kaputt)
        pool = FakePool(konfigurationen={"boese-de": [], "gut-de": []})
        await ps.starte()
        await ps.einreihen("boese-de", "https://boese.de/", pool=pool)
        await ps.einreihen("gut-de", "https://gut.de/", pool=pool)
        await warte_fertig(["boese-de", "gut-de"])
        assert ps._jobs["boese-de"]["zustand"] == ps.FEHLGESCHLAGEN
        assert ps._jobs["gut-de"]["zustand"] == ps.FERTIG
        assert "Chromium" not in json.dumps(ps._oeffentlich(ps._jobs["boese-de"]))  # keine Interna nach aussen

    async def test_scanergebnis_mit_fehler_ist_ein_fehlschlag(self, umgebung):
        async def mit_fehler(url, katalog):
            return SimpleNamespace(error="Navigation fehlgeschlagen", requests=[], cookies=[])
        umgebung.monkeypatch.setattr(ps, "_browser_lauf", mit_fehler)
        pool = FakePool(konfigurationen={"a-de": ["wordpress"]})
        await ps.starte()
        await ps.einreihen("a-de", "https://a.de/", pool=pool)
        await warte_fertig(["a-de"])
        assert ps._jobs["a-de"]["zustand"] == ps.FEHLGESCHLAGEN
        assert pool.cfg["a-de"] == ["wordpress"]                  # Bestand unberührt

    async def test_fehlende_datenbank_scheitert_ehrlich(self, umgebung):
        await ps.starte()
        await ps.einreihen("a-de", "https://a.de/", pool=None)
        await warte_fertig(["a-de"])
        assert ps._jobs["a-de"]["zustand"] == ps.FEHLGESCHLAGEN

    async def test_beende_legt_wartende_ehrlich_ab(self, umgebung):
        umgebung.m.dauer = 5
        pool = FakePool(konfigurationen={f"s{i}-de": [] for i in range(6)})
        await ps.starte()
        for i in range(6):
            await ps.einreihen(f"s{i}-de", f"https://s{i}.de/", pool=pool)
        await asyncio.sleep(0.05)
        await ps.beende()
        zustaende = {ps._jobs[f"s{i}-de"]["zustand"] for i in range(6)}
        assert zustaende == {ps.FEHLGESCHLAGEN}


@pytest.mark.asyncio
class TestVorrang:
    async def test_nutzer_ueberholt_wochenlauf(self, umgebung):
        umgebung.m.dauer = 0.15
        pool = FakePool(konfigurationen={f"w{i}-de": [] for i in range(6)} | {"nutzer-de": []})
        await ps.starte()
        for i in range(6):
            await ps.einreihen(f"w{i}-de", f"https://w{i}.de/", pool=pool, anwenden_ja=False,
                               prio=ps.PRIO_WOCHE, quelle="woche")
        await ps.einreihen("nutzer-de", "https://nutzer.de/", pool=pool)
        await warte_fertig([f"w{i}-de" for i in range(6)] + ["nutzer-de"])
        reihenfolge = umgebung.m.gestartet
        # Die ersten zwei Wochenläufe laufen schon; danach kommt der Nutzer vor den vier übrigen.
        assert reihenfolge.index("https://nutzer.de/") <= 2

    async def test_wochenlauf_aendert_den_banner_nicht(self, umgebung):
        pool = FakePool(konfigurationen={"kunde-de": ["wordpress"]})
        await ps.starte()
        await ps.einreihen("kunde-de", "https://kunde.de/", pool=pool, anwenden_ja=False,
                           prio=ps.PRIO_WOCHE, quelle="woche")
        await warte_fertig(["kunde-de"])
        assert pool.cfg["kunde-de"] == ["wordpress"]
        assert pool.schreibzugriffe == 0
        assert ps._jobs["kunde-de"]["bewertung"]["neu"] == ["hotjar"]   # aber im Bericht

    async def test_nutzer_auf_laufendem_wochenauftrag_wendet_an(self, umgebung):
        umgebung.m.dauer = 0.2
        pool = FakePool(konfigurationen={"kunde-de": []})
        await ps.starte()
        await ps.einreihen("kunde-de", "https://kunde.de/", pool=pool, anwenden_ja=False,
                           prio=ps.PRIO_WOCHE, quelle="woche")
        await asyncio.sleep(0.05)
        await ps.einreihen("kunde-de", "https://kunde.de/", pool=pool, anwenden_ja=True)
        await warte_fertig(["kunde-de"])
        assert pool.cfg["kunde-de"] == ["hotjar"]
        assert len(umgebung.m.gestartet) == 1

    async def test_nachtraegliche_anwendung_ohne_neuen_browser(self, umgebung):
        pool = FakePool(konfigurationen={"kunde-de": []})
        await ps.starte()
        await ps.einreihen("kunde-de", "https://kunde.de/", pool=pool, anwenden_ja=False,
                           prio=ps.PRIO_WOCHE, quelle="woche")
        await warte_fertig(["kunde-de"])
        antwort = await ps.einreihen("kunde-de", "https://kunde.de/", pool=pool, anwenden_ja=True)
        assert antwort["zwischengespeichert"] is True
        assert pool.cfg["kunde-de"] == ["hotjar"]
        assert len(umgebung.m.gestartet) == 1


@pytest.mark.asyncio
class TestStatus:
    async def test_status_zeigt_ergebnis_ohne_interna(self, umgebung):
        pool = FakePool(konfigurationen={"kunde-de": ["wordpress"]})
        await ps.starte()
        await ps.einreihen("kunde-de", "https://kunde.de/", pool=pool, html_keys=["wordpress"])
        await warte_fertig(["kunde-de"])
        s = await ps.status("kunde-de")
        assert s["zustand"] == ps.FERTIG and s["bewertung"]["neu"] == ["hotjar"]
        assert "pool" not in s and "html_keys" not in s
        assert await ps.status("unbekannt-de") is None

    async def test_wartezeit_waechst_mit_der_schlange(self, umgebung):
        umgebung.m.dauer = 0.5
        pool = FakePool(konfigurationen={f"s{i}-de": [] for i in range(12)})
        await ps.starte()
        a = [await ps.einreihen(f"s{i}-de", f"https://s{i}.de/", pool=pool) for i in range(12)]
        waits = [x["geschaetzte_wartezeit_s"] for x in a if "geschaetzte_wartezeit_s" in x]
        assert waits == sorted(waits) and waits[-1] > waits[0]


# --------------------------------------------------------------------------
# Härtung des Browser-Scanners
# --------------------------------------------------------------------------

class TestBrowserWache:
    def test_interne_hosts_werden_erkannt(self):
        from compliance_engine.deep_cookie_scanner import DeepCookieScanner as D
        for h in ("localhost", "127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.169.254",
                  "metadata.google.internal", "intranet.internal", "drucker.local", "[::1]", "172.16.4.4"):
            assert D.host_ist_intern(h), h
        for h in ("example.com", "fonts.googleapis.com", "8.8.8.8", "kunde.de"):
            assert not D.host_ist_intern(h), h

    def test_loopback_nur_fuer_den_pruefstand(self, monkeypatch):
        from compliance_engine.deep_cookie_scanner import DeepCookieScanner as D
        monkeypatch.delenv("SSRF_PRUEFSTAND_LOOPBACK", raising=False)
        assert D.host_ist_intern("127.0.0.1")
        monkeypatch.setenv("SSRF_PRUEFSTAND_LOOPBACK", "1")
        assert not D.host_ist_intern("127.0.0.1")
        assert D.host_ist_intern("10.0.0.5")       # nur Loopback wird freigegeben

    @pytest.mark.asyncio
    async def test_scan_startet_keinen_browser_fuer_interne_adressen(self, monkeypatch):
        from compliance_engine import deep_cookie_scanner as d

        def nie():
            raise AssertionError("Browser darf nicht starten")
        monkeypatch.setattr(d, "async_playwright", nie)
        monkeypatch.setattr(d, "PLAYWRIGHT_AVAILABLE", True)
        for url in ("http://127.0.0.1:8080/", "http://169.254.169.254/latest/meta-data", "http://localhost/admin"):
            r = await d.DeepCookieScanner(1, url).scan()
            assert r.error, url

    @pytest.mark.asyncio
    async def test_route_wache_bricht_interne_ziele_und_medien_ab(self):
        from compliance_engine.deep_cookie_scanner import DeepCookieScanner as D

        class Route:
            def __init__(self, url, typ):
                self.request = SimpleNamespace(url=url, resource_type=typ)
                self.aktion = None

            async def abort(self):
                self.aktion = "abort"

            async def continue_(self):
                self.aktion = "weiter"
        s = D(1, "https://kunde.de")
        faelle = [("http://10.0.0.1/x.png", "image", "abort"), ("https://kunde.de/v.mp4", "media", "abort"),
                  ("https://kunde.de/a.js", "script", "weiter"), ("https://fonts.gstatic.com/f.woff2", "font", "weiter")]
        for url, typ, soll in faelle:
            r = Route(url, typ)
            await s._route_wache(r)
            assert r.aktion == soll, url

    def test_requestliste_hat_einen_deckel(self):
        from compliance_engine import deep_cookie_scanner as d
        s = d.DeepCookieScanner(1, "https://kunde.de")
        req = SimpleNamespace(url="https://x.example/a", method="GET", resource_type="script")
        for _ in range(d.MAX_REQUESTS + 500):
            s._on_request(req)
        assert len(s.requests) == d.MAX_REQUESTS
