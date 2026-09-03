"""Der entkoppelte Prüfweg muss an der CSRF-Schranke vorbeikommen.

Beim ersten Live-Versuch antwortete `POST /api/analyze-auftrag` mit
"CSRF token missing or invalid" — obwohl 13 Tests gruen waren. Die pruefen die
Endpunktfunktion, die Middleware sitzt davor. Aufgefallen ist es erst am
laufenden Dienst.

Der Endpunkt wird von derselben oeffentlichen Landing gerufen wie
/api/analyze-preview: ohne Sitzung, ohne Token. Der Double-Submit-Check kann
dort nie aufgehen.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from csrf_middleware import EXEMPT_PATHS, EXEMPT_PREFIXES


class TestScanwegeSindAusgenommen:
    def test_entkoppelte_annahme_ist_ausgenommen(self):
        assert "/api/analyze-auftrag" in EXEMPT_PATHS

    def test_synchroner_weg_bleibt_ausgenommen(self):
        """Gegenprobe: die bestehende Ausnahme darf nicht verlorengehen."""
        assert "/api/analyze-preview" in EXEMPT_PATHS

    def test_alle_oeffentlichen_scanwege_zusammen(self):
        for pfad in ("/api/analyze", "/api/analyze-preview",
                     "/api/analyze-auftrag", "/api/v2/analyze"):
            assert pfad in EXEMPT_PATHS, f"{pfad} wuerde an CSRF scheitern"


class TestKeinUebermaessigerFreibrief:
    def test_abholweg_braucht_keine_ausnahme(self):
        """GET ist ohnehin nicht CSRF-pflichtig — eine Ausnahme dafuer waere
        nur unnoetige Angriffsflaeche."""
        assert "/api/analyze-auftrag/{kennung}" not in EXEMPT_PATHS

    def test_kein_praefix_fuer_den_ganzen_api_baum(self):
        for p in EXEMPT_PREFIXES:
            assert p not in ("/api/", "/"), f"Praefix {p} hebelt CSRF komplett aus"
