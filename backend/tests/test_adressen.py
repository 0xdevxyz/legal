# -*- coding: utf-8 -*-
"""Links ins Dashboard zeigen aufs Dashboard, nicht auf die Startseite.

Am 29.09.2026 gemessen: FRONTEND_URL war im Backend https://complyo.de, weil
docker-compose sie zweimal setzte und der harte Eintrag gewann. Passwortmail,
Kontobestaetigung, Google-/Apple-Ruecksprung, Stripe-Ruecksprung der Add-ons
und Loeschankuendigung liefen dadurch in 404. Siehe adressen.py.
"""

import os
import re
import sys

import pytest

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WURZEL = os.path.abspath(os.path.join(BACKEND, ".."))
sys.path.insert(0, BACKEND)

# Hier ist mit FRONTEND_URL die Startseite gemeint, und nur hier.
STARTSEITE_ERLAUBT = {
    "adressen.py",          # startseite_url()
    "email_service.py",     # Lead-Verifizierung und Preise liegen auf der Startseite
    "lead_routes.py",       # Warteliste: Ruecksprung auf die Herkunftsseite
    "auth_service.py",      # JWT-Aussteller
    "dependencies.py",      # JWT-Aussteller
}


def _python_dateien():
    for ordner, unter, dateien in os.walk(BACKEND):
        unter[:] = [u for u in unter if u not in {"tests", "__pycache__", "venv", ".venv",
                                                   "_archive_pre_baseline", "archive"}]
        for d in dateien:
            if d.endswith(".py"):
                yield os.path.join(ordner, d)


def test_frontend_url_nur_wo_die_startseite_gemeint_ist():
    treffer = []
    for pfad in _python_dateien():
        quelle = open(pfad, encoding="utf-8", errors="ignore").read()
        if re.search(r"getenv\(\s*['\"]FRONTEND_URL['\"]", quelle):
            if os.path.basename(pfad) not in STARTSEITE_ERLAUBT:
                treffer.append(os.path.relpath(pfad, BACKEND))
    assert not treffer, (
        "FRONTEND_URL ist die Startseite. Links ins Dashboard (Konto, Login, "
        "Add-ons, KI-Systeme) mit adressen.dashboard_url() bauen: "
        + ", ".join(sorted(treffer))
    )


def _backend_umgebung() -> list:
    compose = open(os.path.join(WURZEL, "docker-compose.yml"), encoding="utf-8").read()
    teil = compose.split("\n  backend:", 1)[1]
    teil = re.split(r"\n  [a-z][a-z-]*:\n", teil, maxsplit=1)[0]
    return re.findall(r"^\s*-\s*([A-Z_]+)=", teil, re.MULTILINE)


def test_compose_setzt_jede_adresse_einmal():
    namen = _backend_umgebung()
    assert namen, "Umgebung des Backend-Dienstes nicht gefunden"
    assert namen.count("FRONTEND_URL") == 1, (
        "FRONTEND_URL steht mehrfach im Backend-Dienst; der letzte Eintrag gewinnt "
        "still, so liefen die Kontolinks auf die Startseite."
    )
    assert namen.count("DASHBOARD_URL") == 1


def test_kontolinks_zeigen_aufs_dashboard(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://complyo.de")
    monkeypatch.delenv("DASHBOARD_URL", raising=False)
    import adressen
    assert adressen.dashboard_url() == "https://app.complyo.de"
    assert adressen.startseite_url() == "https://complyo.de"


def test_auth_nutzt_dashboard(monkeypatch):
    for k, v in {"JWT_SECRET": "t", "DATABASE_URL": "postgresql://x",
                 "ENVIRONMENT": "test"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("FRONTEND_URL", "https://complyo.de")
    monkeypatch.delenv("DASHBOARD_URL", raising=False)
    auth_routes = pytest.importorskip("auth_routes")
    assert auth_routes._frontend_url() == "https://app.complyo.de"
