# -*- coding: utf-8 -*-
"""Die IP im Nachweis bestimmt der Server, nicht der Betroffene.

Zwei Fehler derselben Klasse steckten ueber das ganze Backend verteilt:

1. `request.client.host` direkt gelesen. Hinter nginx ist das immer die
   Gateway-Adresse `172.22.0.x`. Ein Audit-Trail, in dem bei jedem Vorgang
   derselbe interne Wert steht, belegt nichts.
2. `X-Forwarded-For` ungeprueft uebernommen. Den Header setzt der Client
   selbst. Ein Nachweis, in den der Betroffene hineinschreiben kann, ist
   gegenueber der Aufsicht und vor Gericht wertlos.

Beide Fehler sind unsichtbar: die Anwendung laeuft, die Spalte ist gefuellt,
nur eben mit einem Wert, der nichts aussagt. Deshalb dieser Test.

`dependencies.get_client_ip` ist die einzige richtige Quelle. Sie glaubt dem
Header nur, wenn die Anfrage von einem Proxy aus TRUSTED_PROXIES kommt, und
meldet eine unbekannte Proxy-IP von sich aus im Log.
"""

import datetime
import hashlib
import os
import re
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

import cookie_compliance_routes
from cookie_compliance_routes import router as cookie_router


BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# dependencies.py DARF beides lesen, dort steht die gepruefte Auswertung.
AUSGENOMMEN = {"dependencies.py"}

# Verzeichnisse ohne Anwendungscode.
UEBERSPRINGEN = ("tests", "migrations", "alembic", "__pycache__", "venv",
                 "node_modules", "scripts")


def produktionsdateien():
    for wurzel, verzeichnisse, dateien in os.walk(BACKEND):
        verzeichnisse[:] = [v for v in verzeichnisse if v not in UEBERSPRINGEN]
        for name in dateien:
            if name.endswith(".py") and name not in AUSGENOMMEN:
                yield os.path.join(wurzel, name)


def codezeilen(pfad):
    """Zeilen ohne reine Kommentare und ohne Docstring-Prosa.

    Die Begruendungen im Code nennen `request.client.host` beim Namen; sie
    sollen den Test nicht ausloesen. Gesucht ist ausfuehrbarer Code.
    """
    with open(pfad, encoding="utf-8") as fh:
        inhalt = fh.read()
    # Docstrings entfernen, danach Kommentarzeilen.
    ohne_docstrings = re.sub(r'"""[\s\S]*?"""', "", inhalt)
    ohne_docstrings = re.sub(r"'''[\s\S]*?'''", "", ohne_docstrings)
    for nr, zeile in enumerate(ohne_docstrings.splitlines(), 1):
        ohne_kommentar = zeile.split("#", 1)[0]
        if ohne_kommentar.strip():
            yield nr, ohne_kommentar


class TestKeineEigeneIpErmittlung:
    """Kein Modul darf die Besucher-IP selbst zusammenbauen."""

    def test_kein_direktes_client_host(self):
        treffer = []
        for pfad in produktionsdateien():
            for nr, zeile in codezeilen(pfad):
                if re.search(r"\brequest\.client\.host\b|\w+_request\.client\.host\b", zeile):
                    treffer.append("%s:%d" % (os.path.relpath(pfad, BACKEND), nr))
        assert not treffer, (
            "Diese Stellen lesen request.client.host direkt: %s. Hinter nginx ist "
            "das immer die Gateway-IP; der Wert belegt nichts. "
            "dependencies.get_client_ip benutzen." % ", ".join(treffer)
        )

    def test_kein_ungepruefter_forwarded_header(self):
        treffer = []
        for pfad in produktionsdateien():
            for nr, zeile in codezeilen(pfad):
                if re.search(r"""headers\.get\(\s*['"][Xx]-[Ff]orwarded-[Ff]or""", zeile):
                    treffer.append("%s:%d" % (os.path.relpath(pfad, BACKEND), nr))
        assert not treffer, (
            "Diese Stellen lesen X-Forwarded-For selbst: %s. Den Header setzt der "
            "Client; ohne Proxy-Pruefung ist jeder daraus abgeleitete Nachweis "
            "faelschbar. dependencies.get_client_ip benutzen." % ", ".join(treffer)
        )


class TestConsentIpKommtVomServer:
    """Das Einwilligungsprotokoll darf die IP nicht aus dem Request-Body nehmen."""

    def _mock_pool(self, monkeypatch):
        pool = MagicMock()
        pool.fetchrow = AsyncMock(side_effect=[
            None,  # cookie_banner_configs
            {"id": 42, "timestamp": datetime.datetime(2026, 9, 2, 12, 0, 0)},
        ])
        pool.execute = AsyncMock(return_value=None)
        monkeypatch.setattr(cookie_compliance_routes, "db_pool", pool)
        return pool

    def _client(self):
        app = FastAPI()
        app.include_router(cookie_router)
        return TestClient(app)

    NUTZLAST = {
        "site_id": "test-site",
        "visitor_id": "visitor-abc",
        "consent_categories": {
            "necessary": True, "functional": False,
            "analytics": False, "marketing": False,
        },
    }

    def test_gefaelschte_ip_im_body_wird_nicht_gespeichert(self, monkeypatch):
        pool = self._mock_pool(monkeypatch)

        with patch.dict(os.environ, {"TRUSTED_PROXIES": "testclient"}):
            antwort = self._client().post(
                "/api/cookie-compliance/consent",
                json={**self.NUTZLAST, "ip_address": "9.9.9.9"},
                headers={"X-Forwarded-For": "203.0.113.7, 172.22.0.1"},
            )

        assert antwort.status_code == 200, antwort.text
        gespeicherter_hash = pool.fetchrow.await_args_list[1].args[5]
        assert gespeicherter_hash == hashlib.sha256(b"203.0.113.7").hexdigest(), (
            "im Einwilligungsprotokoll steht nicht die vom Server ermittelte IP"
        )
        assert gespeicherter_hash != hashlib.sha256(b"9.9.9.9").hexdigest(), (
            "die im Request-Body mitgeschickte IP landet im Nachweis; damit "
            "bestimmt der Einwilligende, was ueber ihn protokolliert wird"
        )

    def test_unbekanntem_proxy_wird_nicht_geglaubt(self, monkeypatch):
        """Gegenprobe: ohne hinterlegten Proxy zaehlt nur die direkte Adresse."""
        pool = self._mock_pool(monkeypatch)

        with patch.dict(os.environ, {"TRUSTED_PROXIES": "10.9.9.9"}):
            antwort = self._client().post(
                "/api/cookie-compliance/consent",
                json=self.NUTZLAST,
                headers={"X-Forwarded-For": "1.2.3.4"},
            )

        assert antwort.status_code == 200, antwort.text
        gespeicherter_hash = pool.fetchrow.await_args_list[1].args[5]
        assert gespeicherter_hash != hashlib.sha256(b"1.2.3.4").hexdigest(), (
            "X-Forwarded-For wird ungeprueft uebernommen"
        )

    def test_ip_address_ist_kein_feld_mehr(self):
        """Das Feld ist entfernt, nicht stillschweigend ignoriert."""
        assert "ip_address" not in cookie_compliance_routes.ConsentLog.model_fields, (
            "ConsentLog nimmt wieder ein ip_address aus dem Request-Body an"
        )

    def test_user_agent_kommt_aus_dem_header(self, monkeypatch):
        """Protokolliert wird, was der Server gesehen hat."""
        pool = self._mock_pool(monkeypatch)

        antwort = self._client().post(
            "/api/cookie-compliance/consent",
            json={**self.NUTZLAST, "user_agent": "frei erfunden"},
            headers={"User-Agent": "Mozilla/5.0 (echt)"},
        )

        assert antwort.status_code == 200, antwort.text
        gespeicherter_ua = pool.fetchrow.await_args_list[1].args[7]
        assert "frei erfunden" not in (gespeicherter_ua or ""), (
            "der User-Agent aus dem Request-Body verdraengt den Header"
        )
