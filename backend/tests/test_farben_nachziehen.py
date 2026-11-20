"""
Bannerfarben folgen der Website (Kennzeichen farben_automatisch).

Anlass (Daniel, 10./20.11.2026): Die Farben des Banners sollen sich aus der Seite
ergeben, von complyos Erkennung gelesen. Der Scan schrieb sie nur beim Anlegen;
complyo.de stand seit September auf Tuerkis. Bewacht wird hier:
1. die Entscheidung (nachziehen nur mit Kennzeichen, Schwelle gegen Flackern,
   nichts erkannt heisst nichts aendern),
2. dass eine von Hand gewaehlte Farbe nie ueberschrieben wird,
3. dass eine fehlende Spalte nie einen 500 macht,
4. die Verdrahtung (Scan, Designer, Abruf) und die Migration.
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.farben_nachziehen import (  # noqa: E402
    FELDER, SCHWELLE, abweichende_felder, kennzeichen_nach_speichern, nachziehen,
    setze_automatisch, vorschlag_aus_scan,
)

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _lies(*teile):
    with open(os.path.join(BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


def _lauf(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


GERENDERT = {"scraped": True, "primary_color": "#4b5563", "accent_color": "#111827",
             "text_color": "#1f2937", "bg_color": "#ffffff"}
TUERKIS = {"primary_color": "#25bac8", "accent_color": "#1597a3",
           "text_color": "#134e4a", "bg_color": "#f0fdfa"}


class FakePool:
    """Minimaler asyncpg-Ersatz: eine Zeile, alle Schreibvorgaenge werden gemerkt."""

    def __init__(self, zeile=None, lesefehler=None, schreibfehler=None):
        self.zeile, self.lesefehler, self.schreibfehler = zeile, lesefehler, schreibfehler
        self.geschrieben = []

    async def fetchrow(self, abfrage, *args):
        if self.lesefehler:
            raise self.lesefehler
        return self.zeile

    async def fetchval(self, abfrage, *args):
        if self.lesefehler:
            raise self.lesefehler
        return None if self.zeile is None else self.zeile.get("farben_automatisch")

    async def execute(self, abfrage, *args):
        if self.schreibfehler:
            raise self.schreibfehler
        self.geschrieben.append((abfrage, args))
        return "UPDATE 1"


def _zeile(automatisch, **farben):
    z = dict(TUERKIS)
    z.update(farben)
    z["farben_automatisch"] = automatisch
    return z


class TestVorschlag:
    def test_aus_der_erkennung_kommen_vier_kleingeschriebene_farben(self):
        v = vorschlag_aus_scan({**GERENDERT, "primary_color": "#4B5563"})
        assert set(v) == set(FELDER)
        assert v["primary_color"] == "#4b5563"

    def test_nichts_erkannt_heisst_kein_vorschlag(self):
        assert vorschlag_aus_scan(None) is None
        assert vorschlag_aus_scan({"scraped": False}) is None

    def test_standardfarben_sind_kein_vorschlag(self):
        # farbvorschlag() faellt ohne eigene Farben auf STANDARD zurueck: das darf
        # eine bestehende Konfiguration nie auf Violett zuruecksetzen.
        assert vorschlag_aus_scan({"scraped": False, "primary_color": "#123456"}) is None


class TestSchwelle:
    def test_kleine_schwankung_gilt_als_gleich(self):
        alt = {**TUERKIS}
        neu = {f: alt[f] for f in FELDER}
        neu["primary_color"] = "#26bbc9"  # eine Stufe je Kanal
        assert abweichende_felder(alt, neu) == []

    def test_echter_wechsel_wird_erkannt(self):
        neu = {f: GERENDERT[f] for f in FELDER}
        # Haupt-, Akzent- und Textfarbe wechseln; der Grund (#f0fdfa gegen #ffffff, Abstand
        # 22) ist fast gleich und zaehlt zu Recht nicht als Aenderung.
        assert set(abweichende_felder(TUERKIS, neu)) == {"primary_color", "accent_color", "text_color"}

    def test_schwelle_ist_klein_genug_fuer_einen_relaunch(self):
        assert 0 < SCHWELLE <= 60


class TestNachziehen:
    def test_ohne_kennzeichen_wird_nie_geschrieben(self):
        pool = FakePool(_zeile(False))
        erg = _lauf(nachziehen(pool, "s-de", GERENDERT))
        assert erg["zustand"] == "manuell"
        assert pool.geschrieben == []

    def test_mit_kennzeichen_wird_nachgezogen(self):
        pool = FakePool(_zeile(True))
        erg = _lauf(nachziehen(pool, "s-de", GERENDERT))
        assert erg["zustand"] == "nachgezogen"
        assert len(pool.geschrieben) == 1
        abfrage, args = pool.geschrieben[0]
        assert "farben_automatisch = TRUE" in abfrage  # nur, solange das Kennzeichen steht
        assert args[0] == "s-de" and args[1] == "#4b5563"

    def test_trockenlauf_schreibt_nichts(self):
        pool = FakePool(_zeile(True))
        erg = _lauf(nachziehen(pool, "s-de", GERENDERT, anwenden=False))
        assert erg["zustand"] == "vorschlag" and pool.geschrieben == []

    def test_nichts_erkannt_laesst_alles_wie_es_ist(self):
        pool = FakePool(_zeile(True))
        erg = _lauf(nachziehen(pool, "s-de", {"scraped": False}))
        assert erg["zustand"] == "nicht_erkannt" and pool.geschrieben == []

    def test_gleiche_farben_werden_nicht_neu_geschrieben(self):
        pool = FakePool(_zeile(True, **{f: GERENDERT[f] for f in FELDER}))
        erg = _lauf(nachziehen(pool, "s-de", GERENDERT))
        assert erg["zustand"] == "unveraendert" and pool.geschrieben == []

    def test_keine_konfiguration(self):
        assert _lauf(nachziehen(FakePool(None), "s-de", GERENDERT))["zustand"] == "keine_konfiguration"

    def test_fehlende_spalte_ist_kein_absturz(self):
        pool = FakePool(lesefehler=RuntimeError('column "farben_automatisch" does not exist'))
        assert _lauf(nachziehen(pool, "s-de", GERENDERT))["zustand"] == "spalte_fehlt"

    def test_schreibfehler_ist_kein_absturz(self):
        pool = FakePool(_zeile(True), schreibfehler=RuntimeError("db weg"))
        assert _lauf(nachziehen(pool, "s-de", GERENDERT))["zustand"] == "spalte_fehlt"


class TestKennzeichenNachSpeichern:
    def test_neue_farben_fallen_das_kennzeichen(self):
        assert kennzeichen_nach_speichern(True, None, True) is False

    def test_echo_des_dashboards_hebelt_die_farbaenderung_nicht_aus(self):
        # Das Dashboard schickt farben_automatisch=True so zurueck, wie es geladen wurde.
        assert kennzeichen_nach_speichern(True, True, True) is False

    def test_bewusst_eingeschaltet_gewinnt(self):
        assert kennzeichen_nach_speichern(False, True, False) is True
        assert kennzeichen_nach_speichern(False, True, True) is True  # Farben mitgeaendert, aber Schalter an

    def test_bewusst_ausgeschaltet_gewinnt(self):
        assert kennzeichen_nach_speichern(True, False, False) is False

    def test_nichts_geaendert_nichts_geschrieben(self):
        assert kennzeichen_nach_speichern(True, None, False) is None
        assert kennzeichen_nach_speichern(False, False, False) is None
        assert kennzeichen_nach_speichern(True, True, False) is None

    def test_ohne_lesbare_spalte_zaehlt_die_eingabe(self):
        assert kennzeichen_nach_speichern(None, True, False) is True


class TestKennzeichen:
    def test_none_laesst_das_kennzeichen_wie_es_ist(self):
        pool = FakePool(_zeile(True))
        assert _lauf(setze_automatisch(pool, "s-de", None)) is False and pool.geschrieben == []

    def test_fehlende_spalte_verhindert_das_speichern_nicht(self):
        pool = FakePool(_zeile(True), schreibfehler=RuntimeError("no column"))
        assert _lauf(setze_automatisch(pool, "s-de", False)) is False

    def test_anzeige_ohne_spalte_liefert_die_konfiguration_ohne_feld(self):
        import cookie_compliance_routes as r
        cfg = {"site_id": "s-de"}
        _lauf(r._farben_auto_feld(FakePool(lesefehler=RuntimeError("no column")), cfg))
        assert "farben_automatisch" not in cfg

    def test_anzeige_nennt_das_kennzeichen(self):
        import cookie_compliance_routes as r
        cfg = {"site_id": "s-de"}
        _lauf(r._farben_auto_feld(FakePool(_zeile(True)), cfg))
        assert cfg["farben_automatisch"] is True


class TestVerdrahtung:
    QUELLE = _lies("cookie_compliance_routes.py")

    def test_beide_abrufwege_liefern_das_kennzeichen(self):
        assert self.QUELLE.count("await _farben_auto_feld(db_pool, config)") == 2

    def test_kennzeichen_steht_nicht_im_grossen_select(self):
        # Backend vor der Migration darf nicht mit 500 antworten.
        for stelle in self.QUELLE.split("query = \"\"\"")[1:]:
            select = stelle.split("\"\"\"")[0]
            assert "farben_automatisch" not in select

    def test_scan_legt_an_mit_kennzeichen_und_zieht_bestehende_nach(self):
        assert "await _auto(db_pool, site_id, True)" in self.QUELLE
        assert "if config_updated and not farben_gespeichert and gerendert:" in self.QUELLE
        assert "_nachziehen(db_pool, site_id, gerendert)" in self.QUELLE

    def test_designer_entscheidet_ueber_die_funktion(self):
        assert "kennzeichen_nach_speichern(\n                _gespeichert, config.farben_automatisch," in self.QUELLE
        assert "any(str(existing.get(f)" in self.QUELLE

    def test_patch_entscheidet_ueber_dieselbe_funktion_und_liefert_die_revision(self):
        assert "any(getattr(updates, f, None) is not None for f in _FARBFELDER)" in self.QUELLE
        assert "RETURNING id, revision" in self.QUELLE

    def test_kennzeichen_ist_nie_eine_spalte_im_dynamischen_update(self):
        assert 'if field == "farben_automatisch":' in self.QUELLE


class TestMigration:
    M = _lies("alembic", "versions", "20261120_0039_farben_automatisch.py")

    def test_kette_und_voreinstellung(self):
        assert 'revision: str = "0039_farben_automatisch"' in self.M
        assert '"0038_marken_stil"' in self.M
        assert "BOOLEAN NOT NULL DEFAULT FALSE" in self.M

    def test_bestand_nur_bei_plattform_standardfarbe(self):
        # revision zaehlt auch Scans: daran laesst sich Handarbeit nicht erkennen.
        assert "lower(primary_color) IN ('#7c3aed', '#6366f1')" in self.M

    def test_genau_ein_kopf(self):
        koepfe = [d for d in os.listdir(os.path.join(BACKEND, "alembic", "versions"))
                  if d.endswith(".py")]
        down = set()
        for d in koepfe:
            t = _lies("alembic", "versions", d)
            for z in t.splitlines():
                if z.startswith("down_revision"):
                    down.add(z.split("=", 1)[1].strip().strip('"\' ').split(":")[-1].strip().strip('"\''))
        assert "0038_marken_stil" in down  # 0039 haengt an 0038, kein zweiter Zweig
