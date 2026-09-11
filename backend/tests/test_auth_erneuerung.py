# -*- coding: utf-8 -*-
"""Ohne Sitzung antwortet die Erneuerung leer — und hoert dann auf zu fragen.

Zwei Fehler, die sich gegenseitig verstaerkten. Gemessen am 09.09.2026 an einer
echten Sitzung im Backoffice:

1. `JSONResponse(status_code=204, content=None)` schrieb die vier Bytes `null`
   in eine Antwort, fuer die Starlette bewusst kein Content-Length setzt. Die
   ASGI-Schicht brach ab: "Response content longer than Content-Length" —
   VIER Tracebacks je Aufruf, 40 an einem Nachmittag. Der Browser bekam eine
   Antwort, an der `res.json()` scheiterte.

2. Der Client behandelte 204 wie ein leeres Ergebnis statt wie eine Absage.
   Ohne refresh_token-Cookie findet aber auch der naechste Versuch nichts, und
   jede weitere 401-Antwort loeste einen neuen aus: 13 Anlaeufe in 44 Minuten,
   die letzten drei mit 429 vom Rate-Limit.

Keiner der beiden faellt in einem gruenen Testlauf auf: der Endpunkt
"funktioniert", der Statuscode stimmt, und die Schleife sieht von aussen aus
wie ein Nutzer, der oft neu laedt.
"""

import os
import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth_routes import router as auth_router

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    # Der Endpunkt haengt an @limiter.limit; ohne diesen Zustand wirft slowapi.
    app.state.limiter = Limiter(key_func=get_remote_address)
    app.include_router(auth_router)
    return TestClient(app)


class TestOhneCookie:
    def test_antwortet_204(self, client):
        r = client.post("/api/auth/refresh-cookie")
        assert r.status_code == 204

    def test_traegt_keinen_rumpf(self, client):
        """Der eigentliche Fehler: 204 mit Inhalt bricht die Antwort ab."""
        r = client.post("/api/auth/refresh-cookie")
        assert r.content == b"", f"204 mit Rumpf: {r.content!r}"

    def test_setzt_kein_content_length(self, client):
        r = client.post("/api/auth/refresh-cookie")
        assert "content-length" not in {k.lower() for k in r.headers}


class TestQuelltext:
    def test_kein_json_rumpf_mehr_im_204_zweig(self):
        s = open(os.path.join(BACKEND, "auth_routes.py"), encoding="utf-8").read()
        assert "JSONResponse(status_code=204" not in s


_FRONTEND = os.path.join(BACKEND, "..", "dashboard-react")
ohne_frontend = pytest.mark.skipif(
    not os.path.isdir(_FRONTEND),
    reason="Frontend-Quelltext liegt nicht neben backend/ (z. B. im Container) — laeuft in CI",
)


@ohne_frontend
class TestClientHoertAuf:
    def _quelle(self):
        pfad = os.path.join(_FRONTEND, "src", "lib", "auth-refresh.ts")
        return open(pfad, encoding="utf-8").read()

    def test_204_wird_als_absage_gelesen(self):
        s = self._quelle()
        assert "res.status === 204" in s

    def test_absage_stoppt_weitere_versuche(self):
        """Die Absage gilt nur fuer den Cookie-Weg. Seit dem 11.09.2026 kommt
        davor der Sitzungsweg (serverseitige Verlaengerung), und der darf von
        einer frueheren 204 nicht blockiert werden: sonst bliebe die
        Verlaengerung tot, sobald einmal kein Cookie da war."""
        s = self._quelle()
        block = s[s.index("export async function refreshAccessToken"):]
        assert block.index("getSession()") < block.index("if (_ohneSitzung)")
        assert block.index("if (_ohneSitzung)") < block.index("refresh-cookie")

    def test_absage_wird_nach_anmeldung_zurueckgenommen(self):
        """Sonst bliebe die Erneuerung nach dem naechsten Login tot."""
        s = self._quelle()
        block = s[s.index("export function setAccessToken"):]
        block = block[:block.index("\n}")]
        assert "_ohneSitzung = false" in block

    def test_204_wird_nicht_mehr_als_json_gelesen(self):
        """res.json() auf einem leeren Rumpf wirft — der Fehler verschwand
        vorher still im catch und sah aus wie ein Netzproblem."""
        s = self._quelle()
        assert s.index("res.status === 204") < s.index("await res.json()")
