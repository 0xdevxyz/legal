# -*- coding: utf-8 -*-
"""
Welche Routen ohne Anmeldung erreichbar sind, ist eine Entscheidung — keine
Nebenwirkung.

Die Kartierung am 09.09.2026 fand 262 Routen, davon 48 ohne jeden
Auth-Hinweis. Die meisten zu Recht: das Widget laeuft auf fremden Domains und
kann sich nicht anmelden. Drei waren es nicht:

  * `GET /api/widgets/analytics/{site_id}` gab die Nutzungszahlen jeder Site
    heraus, deren Kennung man kennt — und die steht im Einbaucode jeder
    Kundenseite.
  * `POST /news/fetch` loeste ohne Anmeldung den Abruf aller RSS-Feeds aus.
  * `POST /api/widgets/analytics` schrieb ungebremst in die Analytics-Tabelle.

Damit das nicht wieder unbemerkt waechst, steht hier die vollstaendige Liste
der absichtlich oeffentlichen Routen mit Grund. Eine neue oeffentliche Route
laesst diesen Test fallen, bis jemand sie eintraegt.
"""

import ast
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AUTH_HINWEISE = (
    "get_current_user", "require_admin", "require_role", "current_user",
    "require_site_access", "require_site_ownership", "require_module",
    "credentials", "HTTPAuthorizationCredentials", "admin_key", "api_key",
    "construct_event", "compare_digest", "nachweis_token", "token",
)

# Absichtlich ohne Anmeldung erreichbar. Der Grund gehoert dazu.
ERLAUBT = {
    # --- Anmeldung selbst
    ("POST", "/login"), ("POST", "/register"), ("POST", "/refresh"),
    ("POST", "/logout"), ("POST", "/logout-all"), ("POST", "/verify-credentials"),
    ("POST", "/oauth-pickup"),
    ("GET", "/google"), ("GET", "/google/callback"),
    ("GET", "/apple"), ("POST", "/apple/callback"),
    # --- Betriebszustand
    ("GET", "/"), ("GET", "/health"), ("GET", "/metrics"),
    ("GET", "/api/cookie-compliance/health"),
    # --- Das Widget laeuft auf fremden Domains und hat dort keine Anmeldung
    ("GET", "/api/widgets/cookie-compliance.js"),
    ("GET", "/api/widgets/privacy-manager.js"),
    ("GET", "/api/widgets/accessibility.js"),
    ("GET", "/api/widgets/a11y-fixes.js"),
    ("GET", "/api/widgets/config/{site_id}"),
    ("GET", "/api/widgets/accessibility-templates"),
    ("GET", "/api/widgets/accessibility-templates/{template_id}"),
    ("POST", "/api/widgets/analytics"),          # gebremst, siehe rate_limit
    ("GET", "/api/accessibility/alt-text-fixes"),
    ("GET", "/api/accessibility/fix-manifest/{site_id}"),
    ("GET", "/api/accessibility/widget/status"),
    ("POST", "/{site_id}"),                       # Wirkungsmeldung des Widgets
    ("GET", "/assign/{site_id}/{visitor_id}"),    # A/B-Variante fuer den Besucher
    ("POST", "/track"),                           # A/B-Ergebnis vom Besucher
    # --- Der Website-Besucher, nicht der Kunde
    ("POST", "/api/cookie-compliance/consent"),
    ("POST", "/api/cookie-compliance/revoke"),
    ("GET", "/api/cookie-compliance/config/{site_id}"),
    ("GET", "/api/cookie-compliance/blocking-config/{site_id}"),
    ("GET", "/api/cookie-compliance/consent-mode-config/{site_id}"),
    ("GET", "/api/cookie-compliance/reconsent-check/{site_id}"),
    ("GET", "/api/cookie-compliance/geo-check"),
    ("GET", "/api/cookie-compliance/policy/{site_id}"),
    ("GET", "/cookie-richtlinie/{site_id}"),
    # --- Oeffentliche Nachschlagewerke ohne Personenbezug
    ("GET", "/api/cookie-compliance/services"),
    ("GET", "/api/cookie-compliance/services/{service_key}"),
    ("GET", "/api/cookie-compliance/tcf/vendors"),
    ("GET", "/api/cookie-compliance/scan/capabilities"),
    ("GET", "/gvl/vendors"), ("GET", "/gvl/purposes"),
    ("GET", "/act/requirements"), ("GET", "/act/requirements/{risk_category}"),
    ("GET", "/catalog"), ("GET", "/plans"),
    ("GET", "/laws"), ("GET", "/search"), ("GET", "/stats"),
    ("GET", "/updates"), ("GET", "/updates/{update_id}"),
    ("GET", "/news"), ("GET", "/news/stats"),
    # --- Nicht erreichbar ohne Kenntnis eines Tiefenscans; deaktiviert
    ("POST", "/api/cookie-compliance/scan/deep"),
}


def _routen():
    gefunden = []
    for wurzel, ordner, dateien in os.walk(BACKEND):
        teile = wurzel.split(os.sep)
        if any(t in ("_archive_pre_baseline", "venv", "node_modules", "tests",
                     "alembic", "__pycache__", "tools") for t in teile):
            continue
        for name in dateien:
            if not name.endswith(".py") or ".bak" in name:
                continue
            pfad = os.path.join(wurzel, name)
            try:
                quelle = open(pfad, encoding="utf-8", errors="replace").read()
                baum = ast.parse(quelle)
            except Exception:
                continue
            for knoten in ast.walk(baum):
                if not isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for dek in knoten.decorator_list:
                    if not (isinstance(dek, ast.Call) and isinstance(dek.func, ast.Attribute)):
                        continue
                    if dek.func.attr not in ("get", "post", "put", "delete", "patch"):
                        continue
                    if not (isinstance(dek.func.value, ast.Name) and dek.func.value.id in ("router", "app")):
                        continue
                    pfad_wert = ""
                    if dek.args and isinstance(dek.args[0], ast.Constant):
                        pfad_wert = str(dek.args[0].value)
                    abschnitt = ast.get_source_segment(quelle, knoten) or ""
                    geschuetzt = any(h in abschnitt for h in AUTH_HINWEISE)
                    gefunden.append((dek.func.attr.upper(), pfad_wert, geschuetzt,
                                     os.path.relpath(pfad, BACKEND), knoten.lineno))
    return gefunden


def test_keine_unbeabsichtigt_oeffentliche_route():
    offen = [(m, p, d, z) for m, p, g, d, z in _routen() if not g]
    unerwartet = [(m, p, d, z) for m, p, d, z in offen if (m, p) not in ERLAUBT]
    assert not unerwartet, (
        "Ohne Anmeldung erreichbar und nicht in der Liste:\n"
        + "\n".join(f"  {m:5s} {p:55s} {d}:{z}" for m, p, d, z in unerwartet)
        + "\n\nEntweder eine Auth-Pruefung ergaenzen oder die Route mit Grund "
          "in ERLAUBT eintragen."
    )


def test_liste_enthaelt_nichts_totes():
    """Eine Ausnahme fuer eine Route, die es nicht mehr gibt, ist Ballast."""
    vorhanden = {(m, p) for m, p, _g, _d, _z in _routen()}
    tot = sorted(x for x in ERLAUBT if x not in vorhanden)
    assert not tot, f"In ERLAUBT stehen Routen, die es nicht mehr gibt: {tot}"
