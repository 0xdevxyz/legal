"""
Wächter für die Selbstabschaltung des Banners.

Anlass (07.10.2026): steinhau.de zeigte einen Banner mit "Wir benötigen Ihre
Einwilligung, bevor Sie unsere Website weiter besuchen können", obwohl gemessen
weder Cookies noch Browser-Speicher noch fremde Hosts im Spiel waren.

Der Banner lässt sich jetzt selbst weg, aber nur unter ZWEI Schranken:

  1. Server (banner_anlass.banner_auto_aus_erlaubt): Scan abgeschlossen, keine
     Dienste, nicht erzwungen, kein Tag Manager, keine eigenen Dienste.
  2. Browser (cookie_banner_v2.js, sammleAnlass): die Seite selbst zeigt nach dem
     Laden nichts. Jede Unsicherheit heißt Banner.

Diese Datei hält die Regel und die Verdrahtung fest. Das Verhalten im Browser
steht in test_banner_anlass_browser.py.

Zwei Dinge sind hier bewusst festgenagelt, weil sie sich leise verschieben
lassen und dann Kunden ohne Banner zurücklassen:

  * `banner_erzwingen` steht NICHT im großen SELECT der öffentlichen
    Konfiguration. Stünde es dort, bekäme jede Website einen 500, sobald das
    Backend vor der Migration 0037 ausgerollt wird.
  * Jeder Fehler beim Lesen heißt Banner. Eine Abschaltung auf Grundlage eines
    fehlgeschlagenen Lesevorgangs wäre die falsche Richtung.
"""
import asyncio
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from banner_anlass import banner_auto_aus_erlaubt  # noqa: E402

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


def _nur_js_code(quelltext: str) -> str:
    """Block- und Zeilenkommentare aus JavaScript entfernen.

    Ein Zeilenkommentar zählt nur, wenn vor `//` weder Doppelpunkt noch Wortzeichen
    steht, damit `http://` im Code bleibt.
    """
    ohne_block = re.sub(r"/\*[\s\S]*?\*/", "", quelltext)
    return "\n".join(re.sub(r"(?<![:\w])//.*$", "", z) for z in ohne_block.splitlines())


def _methode(code: str, name: str) -> str:
    """Der Quelltext einer Methode der Banner-Klasse, bis zur nächsten gleich eingerückten Methode."""
    treffer = re.search(rf"^        (?:async )?{re.escape(name)}\(", code, re.M)
    assert treffer, f"Methode {name} nicht gefunden"
    start = treffer.start()
    rest = code[start + 1:]
    ende = re.search(r"\n        (?:async )?[a-zA-Z_]+\([^)]*\) \{", rest)
    return code[start:start + 1 + (ende.start() if ende else len(rest))]


GUT = {
    "is_active": True,
    "scan_completed": True,
    "services": [],
    "banner_erzwingen": False,
    "gtm_enabled": False,
    "gtm_container_id": None,
}


# ---------------------------------------------------------------------------
# Schranke 1: die Regel
# ---------------------------------------------------------------------------
class TestRegel:
    def test_erlaubt_bei_abgeschlossenem_scan_ohne_dienste(self):
        assert banner_auto_aus_erlaubt(GUT) is True

    @pytest.mark.parametrize("feld,wert", [
        ("is_active", False),
        ("scan_completed", False),
        ("services", ["google_analytics_ga4"]),
        ("banner_erzwingen", True),
        ("gtm_enabled", True),
        ("gtm_container_id", "GTM-ABC123"),
    ])
    def test_jede_bedingung_allein_haelt_den_banner(self, feld, wert):
        assert banner_auto_aus_erlaubt({**GUT, feld: wert}) is False, feld

    def test_eigene_dienste_halten_den_banner(self):
        assert banner_auto_aus_erlaubt(GUT, eigene_dienste=1) is False

    def test_ohne_scan_heisst_leer_nie_nachgesehen(self):
        """osteopathie-limbach.de, spedition-mahn.de, loqal.io: aktiv, nie gescannt,
        services = []. Das ist kein Befund."""
        assert banner_auto_aus_erlaubt({**GUT, "scan_completed": False}) is False

    def test_fehlende_felder_gelten_als_nicht_erfuellt(self):
        assert banner_auto_aus_erlaubt({}) is False
        assert banner_auto_aus_erlaubt({"services": []}) is False

    def test_aktiv_muss_wirklich_true_sein(self):
        """Ein 1 oder ein String ist kein is_active."""
        assert banner_auto_aus_erlaubt({**GUT, "is_active": 1}) is False
        assert banner_auto_aus_erlaubt({**GUT, "is_active": "true"}) is False


# ---------------------------------------------------------------------------
# Anbindung an die Route
# ---------------------------------------------------------------------------
class FakePool:
    def __init__(self, erzwingen=False, eigene=0, fehler=None):
        self.erzwingen, self.eigene, self.fehler = erzwingen, eigene, fehler
        self.abfragen = []
        self.writes = []

    async def fetchval(self, sql, *args):
        self.abfragen.append(" ".join(sql.split()))
        if self.fehler:
            raise self.fehler
        return self.erzwingen if "banner_erzwingen" in sql else self.eigene

    async def execute(self, sql, *args):
        if self.fehler:
            raise self.fehler
        self.writes.append((" ".join(sql.split()), args))


def _felder(pool, **config):
    import cookie_compliance_routes as r
    cfg = {**GUT, "site_id": "test-de", **config}
    asyncio.run(r._banner_auto_aus_felder(pool, cfg))
    return cfg


class TestFelderBerechnung:
    def test_saubere_konfiguration_erlaubt(self):
        cfg = _felder(FakePool())
        assert cfg["banner_auto_aus_erlaubt"] is True
        assert cfg["banner_erzwingen"] is False

    def test_erzwingen_aus_der_datenbank_haelt_den_banner(self):
        cfg = _felder(FakePool(erzwingen=True))
        assert cfg["banner_auto_aus_erlaubt"] is False
        assert cfg["banner_erzwingen"] is True

    def test_eigene_dienste_halten_den_banner(self):
        assert _felder(FakePool(eigene=2))["banner_auto_aus_erlaubt"] is False

    def test_lesefehler_heisst_banner(self):
        """Fehlende Spalte (Migration 0037 noch nicht gelaufen) oder Datenbankausfall."""
        cfg = _felder(FakePool(fehler=RuntimeError('column "banner_erzwingen" does not exist')))
        assert cfg["banner_auto_aus_erlaubt"] is False
        assert cfg["banner_erzwingen"] is False

    def test_zweite_abfrage_nur_wenn_alles_andere_passt(self):
        """Die Konfiguration läuft bei jedem Seitenaufruf eines Besuchers."""
        pool = FakePool()
        _felder(pool, services=["google_analytics_ga4"])
        assert len(pool.abfragen) == 1, pool.abfragen
        pool = FakePool()
        _felder(pool)
        assert len(pool.abfragen) == 2, pool.abfragen

    def test_ohne_site_id_banner(self):
        import cookie_compliance_routes as r
        cfg = {**GUT}
        asyncio.run(r._banner_auto_aus_felder(FakePool(), cfg))
        assert cfg["banner_auto_aus_erlaubt"] is False


class TestSpeichern:
    def test_none_fasst_den_gespeicherten_wert_nicht_an(self):
        import cookie_compliance_routes as r
        pool = FakePool()
        asyncio.run(r._speichere_banner_erzwingen(pool, "test-de", None))
        assert pool.writes == []

    def test_wert_wird_geschrieben(self):
        import cookie_compliance_routes as r
        pool = FakePool()
        asyncio.run(r._speichere_banner_erzwingen(pool, "test-de", True))
        assert len(pool.writes) == 1
        assert "banner_erzwingen" in pool.writes[0][0]
        assert pool.writes[0][1] == ("test-de", True)

    def test_false_wird_geschrieben_nicht_uebersprungen(self):
        import cookie_compliance_routes as r
        pool = FakePool()
        asyncio.run(r._speichere_banner_erzwingen(pool, "test-de", False))
        assert pool.writes[0][1] == ("test-de", False)

    def test_schreibfehler_bricht_das_speichern_nicht_ab(self):
        import cookie_compliance_routes as r
        asyncio.run(r._speichere_banner_erzwingen(
            FakePool(fehler=RuntimeError("Spalte fehlt")), "test-de", True))


class TestVerdrahtung:
    def _quelle(self):
        return _lese("cookie_compliance_routes.py")

    def _funktion(self, name):
        q = self._quelle()
        start = q.index(f"async def {name}(")
        ende = q.index("\n@router.", start)
        return q[start:ende]

    def test_oeffentliche_konfiguration_und_my_config_rechnen_das_feld(self):
        for name in ("get_banner_config", "get_my_config"):
            assert "_banner_auto_aus_felder(db_pool, config)" in self._funktion(name), name

    def test_der_grosse_select_kennt_die_neue_spalte_nicht(self):
        """Sonst: 500 fuer jede Website, sobald das Backend vor der Migration ausgerollt wird."""
        for name in ("get_banner_config", "get_my_config"):
            f = self._funktion(name)
            select = f[f.index("SELECT"):f.index("FROM cookie_banner_configs")]
            assert "banner_erzwingen" not in select, name

    def test_standardkonfiguration_ohne_zeile_erlaubt_nichts(self):
        f = self._funktion("get_banner_config")
        assert '"banner_auto_aus_erlaubt": False' in f

    def test_post_ueberschreibt_das_opt_out_nicht_mit_einem_standardwert(self):
        """Ein Dashboard, das das Feld nicht kennt, schickt None. Das grosse UPDATE
        darf es nicht anfassen, sonst setzt jedes Speichern den Banner zurueck."""
        f = self._funktion("create_or_update_config")
        assert f.count("_speichere_banner_erzwingen(") == 2
        update = f[f.index("UPDATE cookie_banner_configs SET"):f.index("RETURNING id, revision")]
        assert "banner_erzwingen" not in update

    def test_modelle_haben_das_feld_optional(self):
        import cookie_compliance_routes as r
        assert r.BannerConfig.model_fields["banner_erzwingen"].default is None
        assert r.BannerConfigUpdate.model_fields["banner_erzwingen"].default is None


class TestMigration:
    def _datei(self):
        d = os.path.join(_BACKEND, "alembic", "versions")
        treffer = [n for n in os.listdir(d) if "banner_erzwingen" in n]
        assert len(treffer) == 1, treffer
        return _lese("alembic", "versions", treffer[0])

    def test_spalte_mit_vorbelegung_false(self):
        q = self._datei()
        assert "ADD COLUMN IF NOT EXISTS banner_erzwingen BOOLEAN NOT NULL DEFAULT false" in q
        assert "DROP COLUMN IF EXISTS banner_erzwingen" in q

    def test_haengt_an_0036(self):
        """Die Kette im Ganzen (ein Kopf, Namenslänge) prüft test_migrationskette.py."""
        q = self._datei()
        assert 'down_revision: Union[str, None] = "0036_ki_erlaubnis"' in q
        assert 'revision: str = "0037_banner_erzwingen"' in q


# ---------------------------------------------------------------------------
# Schranke 2: das Widget
# ---------------------------------------------------------------------------
class TestWidget:
    def _code(self):
        return _nur_js_code(_lese("widgets", "cookie_banner_v2.js"))

    def test_server_feld_wird_nur_bei_ausdruecklichem_true_gelesen(self):
        assert "serverConfig.banner_auto_aus_erlaubt === true" in self._code()

    def test_vorbelegung_im_widget_ist_aus(self):
        assert "bannerAutoAusErlaubt: false" in self._code()

    def test_abschaltung_hat_alle_vorbedingungen(self):
        code = self._code()
        start = code.index("this.config.bannerAutoAusErlaubt === true")
        kopf = code[start - 120:start + 220]
        for teil in ("!hasTrackingServices", "!this.config.age_verification_enabled", "!this.consent"):
            assert teil in kopf, f"Vorbedingung fehlt: {teil}"

    def test_abschaltung_haengt_am_befund_der_seite(self):
        code = self._code()
        start = code.index("const befund = await this.pruefeAnlass()")
        zweig = code[start:start + 900]
        assert "if (!befund.anlass)" in zweig
        assert "this.beobachteAnlass()" in zweig

    def test_pruefung_sieht_alle_vier_quellen(self):
        m = _methode(self._code(), "sammleAnlass")
        for erwartet in ("data-complyo-blocked", "document.cookie", "localStorage", "sessionStorage",
                         "performance.getEntriesByType('resource')", "'host:'"):
            assert erwartet in m, erwartet

    def test_unsicherheit_heisst_banner(self):
        m = _methode(self._code(), "sammleAnlass")
        assert "eintraege.length >= 250" in m, "Voller Ressourcen-Puffer wird nicht als Unsicherheit gewertet."
        assert "unsicher:timing-voll" in m
        for kennung in ("unsicher:blocker", "unsicher:cookie", "unsicher:timing", "unsicher:dom"):
            assert kennung in m, kennung

    def test_link_hinweise_ohne_abruf_zaehlen_nicht(self):
        """canonical, alternate und das WordPress-Entdeckungs-Link sind kein Abruf."""
        m = _methode(self._code(), "sammleAnlass")
        assert 'link[rel~="stylesheet"]' in m and 'link[rel~="preconnect"]' in m
        assert "link[href]" not in m, "Alle link-Elemente zu zaehlen macht canonical zum Anlass."

    def test_nur_complyo_und_eigene_seite_gelten_als_eigen(self):
        m = _methode(self._code(), "eigeneHosts")
        assert "complyo.de" in m and "location.hostname" in m

    def test_pruefung_und_beobachtung_schreiben_nichts_in_den_browser(self):
        code = self._code()
        for name in ("eigeneHosts", "warteBisGeladen", "sammleAnlass", "pruefeAnlass",
                     "beobachteAnlass", "zeigeBannerNachtraeglich"):
            m = _methode(code, name)
            for verboten in ("setItem", "removeItem", "localStorage.clear", "sessionStorage.clear",
                             "indexedDB", "document.cookie ="):
                assert verboten not in m, f"{name} benutzt {verboten}"

    def test_beobachtung_zeigt_den_banner_nachtraeglich(self):
        m = _methode(self._code(), "beobachteAnlass")
        for erwartet in ("PerformanceObserver", "MutationObserver", "[8000, 20000, 45000]",
                         "pointerdown", "zeigeBannerNachtraeglich"):
            assert erwartet in m, erwartet
        n = _methode(self._code(), "zeigeBannerNachtraeglich")
        assert "this.consent = null" in n and "this.render()" in n

    def test_wachter_liest_den_richtigen_code(self):
        """Ein grüner Wächter über einen leeren Auszug wäre nichts wert."""
        code = self._code()
        assert len(code) > 50000
        assert "async onDOMReady()" in code
