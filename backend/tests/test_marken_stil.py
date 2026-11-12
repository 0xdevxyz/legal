"""
Schrift und Ecken der Website im Cookie-Banner (ohne Browser).

Anlass (Daniel, 12.11.2026): Farben und Logo kommen aus dem Design der Website,
Schrift und Ecken waren im Widget fest. Bewacht wird hier:
1. die Bereinigung der Schrift (sie landet in einem <style>),
2. die Auswahl des Eckenradius,
3. der Schreibweg (Scan, Abruf der Konfiguration, fehlende Spalte),
4. die Migration und der Quelltext des Widgets.
Das Verhalten im Browser prueft tests/test_marken_stil_browser.py.
"""
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.marken_stil import (  # noqa: E402
    PILLE,
    bereinige_schrift,
    bewerte_radien,
    bewerte_stilproben,
)

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _lies(*teile):
    with open(os.path.join(BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


def _lauf(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


class TestSchrift:
    def test_webfont_der_seite_wird_uebernommen(self):
        assert bereinige_schrift('"Open Sans", Arial, sans-serif') == '"Open Sans", Arial, sans-serif'

    def test_ohne_generische_familie_kommt_sans_serif_dazu(self):
        assert bereinige_schrift("Lato") == "Lato, sans-serif"

    def test_serifenschrift_behaelt_ihre_generische_familie(self):
        assert bereinige_schrift('"Playfair Display", Georgia, serif').endswith(", serif")

    @pytest.mark.parametrize("boese", [
        'Arial; } body { display:none',
        'x"; background:url(//boese.de/a)',
        'Arial</style><script>alert(1)</script>',
        'Open Sans{color:red}',
        'a/b\\c',
        'Arial) ; (',
    ])
    def test_nichts_gefaehrliches_kommt_durch(self, boese):
        """Ein Eintrag mit Sonderzeichen faellt weg; was bleibt, ist nur sauber."""
        e = bereinige_schrift(boese)
        if e is not None:
            assert all(c.isalnum() or c in ' ,"-_' for c in e), e

    def test_symbolschrift_ist_nie_die_textschrift(self):
        assert bereinige_schrift('"Font Awesome 6 Free", "Font Awesome 5 Free"') is None
        assert bereinige_schrift("dashicons") is None
        assert bereinige_schrift('eicons, "Open Sans"') == '"Open Sans", sans-serif'

    def test_reine_systemschrift_aendert_nichts(self):
        assert bereinige_schrift("-apple-system, system-ui, sans-serif") is None
        assert bereinige_schrift("sans-serif") is None

    @pytest.mark.parametrize("wert", [None, "", "   ", 5, [], {}])
    def test_unbrauchbare_eingabe(self, wert):
        assert bereinige_schrift(wert) is None

    def test_laenge_ist_begrenzt(self):
        lang = ", ".join(f"Name{i}" for i in range(40))
        e = bereinige_schrift(lang)
        assert e is not None and len(e) <= 200 and e.count("Name") <= 4


class TestEcken:
    def test_haeufigster_radius_gewinnt(self):
        k = [{"radius": "6px", "hoehe": 44}] * 3 + [{"radius": "0px", "hoehe": 44}]
        assert bewerte_radien(k) == 6

    def test_pille_ab_halber_knopfhoehe(self):
        assert bewerte_radien([{"radius": "22px", "hoehe": 44}]) == PILLE
        assert bewerte_radien([{"radius": "9999px", "hoehe": 44}]) == PILLE
        assert bewerte_radien([{"radius": "50%", "hoehe": 44}]) == PILLE

    def test_eckig_bleibt_eckig(self):
        assert bewerte_radien([{"radius": "0px", "hoehe": 44}]) == 0

    def test_grosser_radius_wird_begrenzt(self):
        assert bewerte_radien([{"radius": "18px", "hoehe": 80}]) == 18
        assert bewerte_radien([{"radius": "30px", "hoehe": 120}]) == 24

    def test_gleichstand_nimmt_den_kleineren(self):
        k = [{"radius": "4px", "hoehe": 44}, {"radius": "8px", "hoehe": 44}]
        assert bewerte_radien(k) == 4

    @pytest.mark.parametrize("wert", [None, [], "x", [{"radius": "auto", "hoehe": 40}], [None], [{"hoehe": "x"}]])
    def test_nichts_messbar(self, wert):
        assert bewerte_radien(wert) is None


class TestStilproben:
    def test_beides(self):
        e = bewerte_stilproben({"schrift": "Lato, sans-serif", "knoepfe": [{"radius": "4px", "hoehe": 40}]})
        assert e == {"schrift": "Lato, sans-serif", "radius": 4}

    def test_nur_eines_reicht(self):
        assert bewerte_stilproben({"schrift": "sans-serif", "knoepfe": [{"radius": "4px", "hoehe": 40}]}) == \
            {"schrift": None, "radius": 4}

    def test_nichts_brauchbares(self):
        assert bewerte_stilproben({"schrift": "serif", "knoepfe": []}) is None
        assert bewerte_stilproben(None) is None


class TestSchreibweg:
    def _routen(self):
        import cookie_compliance_routes as r
        return r

    def test_speichern_ueberschreibt_nur_was_gemessen_wurde(self):
        r = self._routen()
        pool = MagicMock()
        pool.execute = AsyncMock(return_value="UPDATE 1")
        assert _lauf(r._speichere_markenstil(pool, "s-de", {"schrift": None, "radius": 6})) is True
        sql = pool.execute.call_args.args[0]
        assert "COALESCE($2, marken_schrift)" in sql and "COALESCE($3, marken_radius)" in sql
        assert pool.execute.call_args.args[2:] == ("s-de", None, 6) or pool.execute.call_args.args[1:] == ("s-de", None, 6) \
            or pool.execute.call_args.args[-3:] == ("s-de", None, 6)

    def test_nichts_gemessen_schreibt_nichts(self):
        r = self._routen()
        pool = MagicMock()
        pool.execute = AsyncMock()
        assert _lauf(r._speichere_markenstil(pool, "s-de", None)) is False
        assert _lauf(r._speichere_markenstil(pool, "s-de", {"schrift": None, "radius": None})) is False
        pool.execute.assert_not_called()

    def test_fehlende_spalte_laesst_den_scan_nicht_scheitern(self):
        r = self._routen()
        pool = MagicMock()
        pool.execute = AsyncMock(side_effect=Exception('column "marken_schrift" does not exist'))
        assert _lauf(r._speichere_markenstil(pool, "s-de", {"schrift": "Lato, sans-serif", "radius": 4})) is False

    def test_konfiguration_bekommt_die_felder(self):
        r = self._routen()
        pool = MagicMock()
        pool.fetchrow = AsyncMock(return_value={"marken_schrift": '"Open Sans", sans-serif', "marken_radius": 6})
        cfg = {"site_id": "s-de"}
        _lauf(r._markenstil_felder(pool, cfg))
        assert cfg["marken_schrift"] == '"Open Sans", sans-serif' and cfg["marken_radius"] == 6

    def test_fehlende_spalte_beim_abruf_ist_kein_500(self):
        """Backend vor der Migration ausgerollt: die Konfiguration kommt ohne die Felder."""
        r = self._routen()
        pool = MagicMock()
        pool.fetchrow = AsyncMock(side_effect=Exception("column does not exist"))
        cfg = {"site_id": "s-de", "layout": "box_modal"}
        _lauf(r._markenstil_felder(pool, cfg))
        assert "marken_schrift" not in cfg and "marken_radius" not in cfg and cfg["layout"] == "box_modal"

    def test_manipulierter_wert_in_der_datenbank_wird_nicht_ausgeliefert(self):
        r = self._routen()
        pool = MagicMock()
        pool.fetchrow = AsyncMock(return_value={"marken_schrift": 'x; } body{display:none', "marken_radius": 99})
        cfg = {"site_id": "s-de"}
        _lauf(r._markenstil_felder(pool, cfg))
        assert "display:none" not in str(cfg.get("marken_schrift", ""))
        assert "marken_radius" not in cfg

    def test_konfiguration_ohne_zeile_bleibt_unveraendert(self):
        r = self._routen()
        pool = MagicMock()
        pool.fetchrow = AsyncMock(return_value=None)
        cfg = {"site_id": "s-de"}
        _lauf(r._markenstil_felder(pool, cfg))
        assert cfg == {"site_id": "s-de"}


class TestQuelltext:
    def test_post_config_beruehrt_die_felder_nie(self):
        """Ein Dashboard, das die Felder nicht kennt, darf sie nicht loeschen."""
        q = _lies("cookie_compliance_routes.py")
        for stelle in q.split("async def "):
            if stelle.startswith(("save_banner_config", "save_config", "create_or_update")):
                assert "marken_schrift" not in stelle and "marken_radius" not in stelle

    def test_beide_abrufwege_liefern_die_felder(self):
        assert _lies("cookie_compliance_routes.py").count("await _markenstil_felder(db_pool, config)") == 2

    def test_scan_misst_im_selben_browserdurchlauf(self):
        q = _lies("cookie_compliance_routes.py")
        assert "logo_ziel=logo, stil_ziel=stil" in q
        m = _lies("compliance_engine", "markenfarben_gerendert.py")
        assert "stil_aus_seite(page)" in m

    def test_migration_haengt_an_der_spitze(self):
        m = _lies("alembic", "versions", "20261112_0038_marken_stil.py")
        assert 'revision: str = "0038_marken_stil"' in m
        assert '"0037_kanal_herkunft"' in m
        assert "ADD COLUMN IF NOT EXISTS marken_schrift TEXT" in m and "marken_radius SMALLINT" in m

    def test_widget_prueft_die_schrift_selbst(self):
        w = _lies("widgets", "cookie_banner_v2.js")
        assert "schriftOk" in w and "/^[A-Za-z0-9 ,\"'_-]+$/" in w
        assert "var(--complyo-font," in w and "var(--complyo-radius-card, 12px)" in w
        assert "var(--complyo-radius-btn, 10px)" in w

    def test_widget_ausdrueckliche_wahl_gewinnt(self):
        w = _lies("widgets", "cookie_banner_v2.js")
        assert "this.config.buttonStyle !== 'pill' && this.config.buttonStyle !== 'square'" in w
