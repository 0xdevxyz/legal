"""
Wächter für den öffentlichen Prüfnachweis.

Der Nachweis ist ohne Anmeldung abrufbar — das ist Absicht und zugleich die
Stelle, an der ein Fehler am teuersten wäre. Drei Zusagen stehen hier fest:

  1. Ohne passenden Schlüssel gibt es nichts, und die Abweisung verrät nicht,
     ob es zu der Domain überhaupt einen Nachweis gibt.
  2. Ohne konfiguriertes Server-Geheimnis ist der Nachweis ganz aus. Ein
     ratbarer Schlüssel wäre schlimmer als kein Nachweis.
  3. Nur freigegebene Reparaturen erscheinen. Ein Protokoll über Fixes, die
     nie live gingen, wäre eine Fälschung.
"""
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import nachweis_routes as nw  # noqa: E402
from compliance_engine.nachweis_generator import nachweis_token  # noqa: E402

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


class TestZugriff:
    def test_falscher_schluessel_gibt_nicht_gefunden(self):
        """
        404 statt 403: dass es zu einer Domain einen Nachweis gibt, ist selbst
        eine Auskunft.
        """
        src = _lese("nachweis_routes.py")
        block = src[src.index("async def oeffentlicher_nachweis"):]
        assert "status_code=404" in block
        assert "status_code=403" not in block

    def test_schluesselvergleich_ist_zeitkonstant(self):
        """Ein Vergleich mit == verraet ueber die Laufzeit den Schluessel."""
        assert "hmac.compare_digest" in _lese("nachweis_routes.py")

    def test_ohne_geheimnis_kein_nachweis(self):
        assert nachweis_token("beispiel-de", "") == ""
        src = _lese("nachweis_routes.py")
        block = src[src.index("async def oeffentlicher_nachweis"):]
        assert "if not geheim:" in block

    def test_schluessel_ist_stabil(self):
        """Er steht in der Barrierefreiheitserklaerung — er darf nicht verfallen."""
        a = nachweis_token("beispiel-de", "s3cret")
        b = nachweis_token("beispiel-de", "s3cret")
        assert a == b and len(a) == 32


class TestNurFreigegebenes:
    def test_nicht_freigegebene_zeilen_werden_uebersprungen(self):
        src = _lese("nachweis_routes.py")
        assert 'z["status"] != "approved"' in src

    def test_nicht_freigegebene_farben_werden_uebersprungen(self):
        src = _lese("nachweis_routes.py")
        assert 'e.get("freigabe") != "approved"' in src


class TestDatensparsam:
    def test_keine_kundendaten_im_protokoll(self):
        """
        Der Nachweis ist oeffentlich. Was nicht hineingehoert, darf gar nicht
        erst abgefragt werden.
        """
        src = _lese("nachweis_routes.py")
        for verboten in ("email", "user_id", "client_name", "password"):
            assert verboten not in src.lower(), verboten


class TestRegistrierung:
    def test_router_haengt_in_der_anwendung(self):
        src = _lese("main_production.py")
        assert "app.include_router(nachweis_router)" in src
        assert "init_nachweis_routes(db_pool)" in src

    def test_beide_endpunkte_existieren(self):
        pfade = [r.path for r in nw.router.routes]
        assert "/api/nachweis/{site_id}/{token}" in pfade
        assert "/api/nachweis/{site_id}/{token}/erklaerung" in pfade
