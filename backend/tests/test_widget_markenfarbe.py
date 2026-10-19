"""
Barrierefreiheits-Widget in der Markenfarbe des Kunden.

Das Widget hatte keine Farboption: accessibility-v6.js setzte fest den
complyo-Akzent. Jetzt folgt es der Primaerfarbe des Cookie-Banners (die seit
dem ersten Scan aus der Kundenseite kommt). Die Token werden serverseitig
berechnet und lesbar gemacht; das Widget prueft nur noch Hex, setzt sie auf
das Wurzelelement und misst gegen den Seitenhintergrund.

Bewacht wird:
1. Token-Regeln (Schriftrolle 4,5:1 gegen Weiss, Knopfschrift je nach Flaeche,
   Rueckfall auf die dunkle Stufe).
2. Widget-Konfigroute liefert die Token nur, wenn eine Banner-Farbe gesetzt ist.
3. Das JS wendet sie vor dem Einhaengen an und laesst nur Hex in den Stil.
"""

import os
import re
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.markenfarben import kontrast, widget_farbtoken  # noqa: E402

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JS = open(os.path.join(BACKEND, "widgets", "accessibility-v6.js"), encoding="utf-8").read()


# ============================================================================
# 1) Token-Regeln
# ============================================================================

class TestWidgetFarbtoken:
    def test_dunkle_markenfarbe_bleibt_knopf_mit_weisser_schrift(self):
        t = widget_farbtoken("#1d4ed8")
        assert t["accent_solid"] == "#1d4ed8"
        assert t["on_accent_solid"] == "#ffffff"
        assert t["accent"] == "#1d4ed8"
        assert t["kontrast_knopf"] >= 4.5 and t["kontrast_schrift"] >= 4.5

    def test_helle_markenfarbe_knopf_mit_dunkler_schrift_text_abgedunkelt(self):
        """complyo-Cyan: als Flaeche bleibt es, die Schrift darauf wird dunkel;
        als Schrift auf Weiss wird es zur dunklen Stufe (vgl. CSS-Kommentar)."""
        t = widget_farbtoken("#00FFF7")
        assert t["accent_solid"] == "#00fff7"
        assert t["on_accent_solid"] == "#111827"
        assert t["accent"] != "#00fff7"
        assert kontrast(t["accent"], "#ffffff") >= 4.5
        assert kontrast(t["accent_solid"], t["on_accent_solid"]) >= 4.5

    def test_mittelgrau_faellt_auf_dunkle_stufe_zurueck(self):
        """#808080: 3,95:1 gegen Weiss, 4,4:1 gegen Dunkel. Keine Schrift
        erreicht 4,5:1, also dunkle Stufe mit weisser Schrift."""
        t = widget_farbtoken("#808080")
        assert t["accent_solid"] != "#808080"
        assert t["on_accent_solid"] == "#ffffff"
        assert t["kontrast_knopf"] >= 4.5

    def test_kurzform_und_grossschreibung(self):
        assert widget_farbtoken("#ABC")["primary_color"] == "#aabbcc"

    def test_ungueltig_oder_leer_ist_none(self):
        assert widget_farbtoken(None) is None
        assert widget_farbtoken("") is None
        assert widget_farbtoken("blau") is None

    def test_alle_token_sind_hex(self):
        t = widget_farbtoken("#f97316")
        for k in ("accent", "accent_hover", "accent_tint", "accent_border",
                  "accent_solid", "accent_solid_hover", "on_accent_solid"):
            assert re.fullmatch(r"#[0-9a-f]{6}", t[k]), (k, t[k])

    def test_hover_ist_dunkler_tint_ist_heller(self):
        from compliance_engine.markenfarben import relative_leuchtdichte as L
        t = widget_farbtoken("#1d4ed8")
        assert L(t["accent_hover"]) < L(t["accent"])
        assert L(t["accent_tint"]) > 0.8


# ============================================================================
# 2) Widget-Konfigroute
# ============================================================================

def _client_mit_zeile(monkeypatch, zeile):
    import widget_routes
    from widget_routes import router
    conn = MagicMock()
    conn.fetchrow = AsyncMock(return_value=zeile)
    pool = MagicMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = False
    monkeypatch.setattr(widget_routes, "db_pool", pool)

    async def lizenz_ok(*a, **k):
        return {"status": "active", "enforced": False, "active": True, "message": None}
    import license_check
    monkeypatch.setattr(license_check, "evaluate_license", lizenz_ok)

    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def test_konfig_liefert_token_wenn_bannerfarbe_gesetzt(monkeypatch):
    client = _client_mit_zeile(monkeypatch, {
        "layout": "banner_bottom", "primary_color": "#1d4ed8", "accent_color": "#1e40af",
        "position": "bottom", "language": "de",
    })
    resp = client.get("/api/widgets/config/kunde-de")
    assert resp.status_code == 200, resp.text
    a11y = resp.json()["config"]["accessibility"]
    assert a11y["farben"]["accent_solid"] == "#1d4ed8"
    assert a11y["farben"]["quelle"] == "banner"
    assert resp.json()["config"]["cookie_consent"]["primaryColor"] == "#1d4ed8"


def test_konfig_ohne_zeile_bleibt_complyo_standard(monkeypatch):
    client = _client_mit_zeile(monkeypatch, None)
    resp = client.get("/api/widgets/config/kunde-de")
    assert resp.status_code == 200, resp.text
    assert "farben" not in resp.json()["config"]["accessibility"]


def test_konfig_mit_zeile_ohne_farbe_bleibt_standard(monkeypatch):
    client = _client_mit_zeile(monkeypatch, {
        "layout": None, "primary_color": None, "accent_color": None, "position": None, "language": None,
    })
    assert "farben" not in client.get("/api/widgets/config/kunde-de").json()["config"]["accessibility"]


# ============================================================================
# 3) Widget-JS
# ============================================================================

class TestWidgetJs:
    def test_liest_token_aus_der_konfig(self):
        assert "data.config.accessibility.farben" in JS
        assert "this.config.farben = farben" in JS

    def test_wendet_farben_vor_dem_einhaengen_an(self):
        anwenden = JS.index("this.applyBrandColors(container);")
        einhaengen = JS.index("document.documentElement.appendChild(container);")
        assert anwenden < einhaengen

    def test_nur_hex_kommt_in_den_stil(self):
        rumpf = JS[JS.index("applyBrandColors(container) {"):JS.index("_mfRgb(hex)")]
        assert "/^#[0-9a-f]{6}$/i" in rumpf
        assert "HEX.test(wert)" in rumpf
        assert "setProperty(name, wert.toLowerCase())" in rumpf

    def test_setzt_alle_sieben_token(self):
        rumpf = JS[JS.index("applyBrandColors(container) {"):JS.index("_mfRgb(hex)")]
        for token in ("--c-accent", "--c-accent-hover", "--c-accent-tint", "--c-accent-border",
                      "--c-accent-solid", "--c-accent-solid-hover", "--c-on-accent-solid"):
            assert f"'{token}'" in rumpf, token

    def test_ring_bei_zu_wenig_kontrast_zur_seite(self):
        rumpf = JS[JS.index("applyBrandColors(container) {"):JS.index("_mfRgb(hex)")]
        assert "this._mfKontrast(solid, seite) < 3" in rumpf
        assert "btn.style.border = '2px solid ' + ring" in rumpf

    def test_stylesheet_token_unveraendert(self):
        """Die Standardwerte im Stylesheet bleiben; die Kundenfarbe liegt nur
        als Inline-Token auf dem Wurzelelement (keine Konflikte mit #11/#28)."""
        assert "--c-accent: #00706c;" in JS
        assert "--c-accent-solid: #00fff7;" in JS
