# -*- coding: utf-8 -*-
"""
Angemeldet ist nicht dasselbe wie berechtigt.

Messung vom 10.09.2026: acht angemeldete Routen nahmen eine site_id aus der
Adresse entgegen, ohne zu pruefen, ob sie dem Konto gehoert. Die Kennung ist
kein Geheimnis — sie steht im Einbaucode auf jeder Kundenseite. Damit konnte
jedes Konto mit gebuchtem Cookie-Modul:

  * die eigenen Dienste fremder Websites lesen, anlegen, aendern und loeschen,
  * deren Einwilligungs- und Widerrufsstatistiken abrufen,
  * deren letztes Scan-Ergebnis samt Cookies und Diensten einsehen,
  * und (mit einem Konto ohne eigene Website) deren Banner umschreiben:
    `if registered_site_id and site_id != registered_site_id` liess durch,
    solange gar keine Website registriert war.

Der Test haelt fest, dass jede solche Route eine Zugehoerigkeitspruefung hat.
"""

import ast
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AUTH = ("get_current_user", "credentials", "require_admin",
        "HTTPAuthorizationCredentials", "get_current_user_required")

BESITZ = ("require_site_access", "require_site_ownership", "require_site_access_user",
          "assert_site_owner", "get_user_site_ids", "require_admin",
          "WHERE user_id", "AND user_id", "user_id = $", "user_id=$")

KENNUNG = re.compile(r"\{(site_id|website_id|scan_id|fix_id|lead_id|config_id|report_id)\}")

# Routen mit Kennung in der Adresse, die absichtlich ohne Zugehoerigkeit
# auskommen. Jede braucht einen Grund.
ERLAUBT = {
    # Das Widget laeuft auf der Kundendomain ohne Anmeldung
    ("GET", "/api/widgets/config/{site_id}"),
    ("GET", "/api/accessibility/fix-manifest/{site_id}"),
    ("GET", "/api/cookie-compliance/config/{site_id}"),
    ("GET", "/api/cookie-compliance/blocking-config/{site_id}"),
    ("GET", "/api/cookie-compliance/consent-mode-config/{site_id}"),
    ("GET", "/api/cookie-compliance/reconsent-check/{site_id}"),
    ("GET", "/api/cookie-compliance/policy/{site_id}"),
    ("GET", "/cookie-richtlinie/{site_id}"),
    ("GET", "/assign/{site_id}/{visitor_id}"),
    ("POST", "/{site_id}"),
    ("POST", "/api/cookie-compliance/monitor/check/{site_id}"),
    # Oeffentlicher Nachweis: der Token IST die Berechtigung
    ("GET", "/{site_id}/{token}"),
    ("GET", "/{site_id}/{token}/seite"),
    ("GET", "/{site_id}/{token}/erklaerung"),
}


def _routen():
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
                    if not (isinstance(dek.func.value, ast.Name)
                            and dek.func.value.id in ("router", "app")):
                        continue
                    adresse = ""
                    if dek.args and isinstance(dek.args[0], ast.Constant):
                        adresse = str(dek.args[0].value)
                    yield (dek.func.attr.upper(), adresse,
                           ast.get_source_segment(quelle, knoten) or "",
                           os.path.relpath(pfad, BACKEND), knoten.lineno)


def test_jede_route_mit_fremder_kennung_prueft_die_zugehoerigkeit():
    offen = []
    for methode, adresse, rumpf, datei, zeile in _routen():
        if not KENNUNG.search(adresse):
            continue
        if (methode, adresse) in ERLAUBT:
            continue
        if not any(a in rumpf for a in AUTH):
            continue          # unangemeldet: das prueft test_oeffentliche_routen
        if any(b in rumpf for b in BESITZ):
            continue
        offen.append(f"  {methode:6s} {adresse:52s} {datei}:{zeile}")
    assert not offen, (
        "Angemeldet, aber ohne Zugehoerigkeitspruefung:\n" + "\n".join(offen)
        + "\n\nDie site_id steht im Einbaucode jeder Kundenseite und ist kein "
          "Geheimnis. Entweder require_site_access/require_site_ownership "
          "ergaenzen oder die Route mit Grund in ERLAUBT eintragen."
    )


def test_teilaenderung_am_banner_prueft_alle_websites_des_kontos():
    """Die alte Pruefung liess ein Konto ohne eigene Website ueberall hin."""
    quelle = open(os.path.join(BACKEND, "cookie_compliance_routes.py"), encoding="utf-8").read()
    assert "if registered_site_id and site_id != registered_site_id" not in quelle, (
        "update_config_partial vergleicht wieder nur mit der primaeren Website "
        "und laesst durch, wenn keine registriert ist."
    )
