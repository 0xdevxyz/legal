# -*- coding: utf-8 -*-
"""Eine abgelaufene Sitzung meldet EINMAL ab, nicht je offener Anfrage.

Gemeldet am 09.09.2026: "nach laengerer Inaktivitaet laedt gefuehlt 20x der
Ladebalken und kommt dann wieder zum Login, sieht buggy aus."

Der Grund steckt nicht im Abmelden selbst, sondern darin, wie oft es passierte.
Nach laengerer Untaetigkeit ist der Zugriffstoken abgelaufen, und das Dashboard
hat ein Dutzend Abfragen gleichzeitig offen. Jede lief in 401, jede rief
signOut() auf, und jedes signOut() holt erst ein CSRF-Token und schickt dann
einen POST — zwei Netzabrufe, in deren Luecke die naechste Anfrage dasselbe
begann. In der Konsole des Nutzers entsprechend: mehrfach
"Fetch API cannot load .../api/auth/csrf" und "getTrackedWebsites failed: 401".

Dazu lief resolveAccessToken() vor JEDER Anfrage und holte ohne Token eine
eigene next-auth-Sitzung, mit bis zu 3 s Wartezeit — zwoelf Anfragen, zwoelf
identische Abrufe.

Beides ist dieselbe Fehlerklasse: nebenlaeufige Arbeit, die nicht gebuendelt
wird. Und beides sieht im Testlauf nach nichts aus, weil ein einzelner Aufruf
sich voellig richtig verhaelt.
"""

import os
import re

import pytest

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_FRONTEND = os.path.join(BACKEND, "..", "dashboard-react")

ohne_frontend = pytest.mark.skipif(
    not os.path.isdir(_FRONTEND),
    reason="Frontend-Quelltext liegt nicht neben backend/ (z. B. im Container) — laeuft in CI",
)


def quelle():
    pfad = os.path.join(_FRONTEND, "src", "lib", "api-client.ts")
    return open(pfad, encoding="utf-8").read()


def ohne_kommentare(s: str) -> str:
    """Kommentare raus: gezaehlt wird Code, nicht die Begruendung darueber."""
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"^\s*//.*$", "", s, flags=re.M)


@ohne_frontend
class TestAbmeldungNurEinmal:
    def test_es_gibt_genau_eine_abmeldestelle(self):
        """signOut darf nur an EINER Stelle stehen — sonst ist der Riegel
        umgehbar, ohne dass es jemandem auffaellt."""
        s = ohne_kommentare(quelle())
        assert s.count("signOut(") == 1

    def test_riegel_faellt_vor_dem_ersten_await(self):
        s = quelle()
        block = s[s.index("async function _abmelden"):]
        block = block[:block.index("\n}\n")]
        riegel = block.index("_isLoggingOut = true")
        erstes_await = block.index("await ")
        assert riegel < erstes_await, "Der Riegel muss vor dem ersten await fallen"

    def test_abmeldung_laeuft_ueber_den_riegel(self):
        s = quelle()
        block = s[s.index("async function _abmelden"):]
        block = block[:block.index("\n}\n")]
        assert "if (_isLoggingOut) return;" in block

    def test_interceptor_meldet_nicht_selbst_ab(self):
        """Der 401-Zweig ruft _abmelden(), nicht signOut() direkt."""
        s = quelle()
        assert "await _abmelden();" in s


@ohne_frontend
class TestSitzungsabfrageGebuendelt:
    def test_parallele_anfragen_teilen_eine_abfrage(self):
        s = quelle()
        assert "if (_inflightSession) return _inflightSession;" in s

    def test_abfrage_wird_danach_freigegeben(self):
        """Ohne finally bliebe die erste Antwort fuer immer stehen — auch die
        nach dem naechsten Login."""
        s = quelle()
        assert "_inflightSession = null;" in s

    def test_waehrend_der_abmeldung_wird_nicht_mehr_gesucht(self):
        s = quelle()
        block = s[s.index("async function resolveAccessToken"):]
        block = block[:block.index("\n}\n")]
        assert "if (_isLoggingOut) return null;" in block
