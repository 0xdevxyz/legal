# -*- coding: utf-8 -*-
"""
Der Ratenzaehler muss den Besucher zaehlen, nicht den Proxy.

Gemessen am 09.09.2026: hinter nginx kommt JEDE Anfrage als 172.22.0.1 an.
`slowapi.util.get_remote_address` liefert genau diese Adresse. Alle drei
Zaehler des Backends benutzten sie — also teilten sich saemtliche Besucher
einen Eimer:

  * `POST /api/auth/register` mit 3/hour: nach drei Registrierungen war die
    Anmeldung fuer die ganze Plattform eine Stunde dicht. Waehrend einer
    Early-Access-Kampagne faellt das als "niemand meldet sich an" auf, nicht
    als Fehler.
  * `POST /api/auth/login` mit 5/minute: fuenf Fehlversuche eines Angreifers
    sperren die Anmeldung fuer alle anderen.

Der Test haelt beides fest: die Schluesselfunktion UND das Ergebnis.
"""

import os
import re

import pytest

from dependencies import get_client_ip

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIT_ZAEHLER = ("main_production.py", "auth_routes.py", "fix_routes.py")


class Anfrage:
    """Minimale Request-Attrappe: direkter Peer plus Kopfzeilen."""

    def __init__(self, peer, headers=None):
        self.client = type("C", (), {"host": peer})()
        self.headers = headers or {}


@pytest.mark.parametrize("datei", MIT_ZAEHLER)
def test_kein_zaehler_auf_der_proxy_adresse(datei):
    quelle = open(os.path.join(BACKEND, datei), encoding="utf-8").read()
    treffer = re.findall(r"Limiter\(key_func=(\w+)\)", quelle)
    assert treffer, f"{datei}: kein Limiter gefunden — Liste veraltet?"
    for f in treffer:
        assert f != "get_remote_address", (
            f"{datei} zaehlt mit get_remote_address. Hinter nginx ist das fuer "
            "alle Besucher dieselbe Adresse; das Limit gilt dann global."
        )


def test_besucher_ip_hinter_bekanntem_proxy(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXIES", "172.22.0.1,127.0.0.1")
    a = Anfrage("172.22.0.1", {"X-Forwarded-For": "203.0.113.9"})
    assert get_client_ip(a) == "203.0.113.9"


def test_selbst_gesetzter_header_zaehlt_nicht(monkeypatch):
    """
    nginx haengt an, statt zu ersetzen. Wer selbst X-Forwarded-For schickt,
    steht links; genommen wird der rechteste Eintrag, der kein Proxy ist.
    """
    monkeypatch.setenv("TRUSTED_PROXIES", "172.22.0.1")
    a = Anfrage("172.22.0.1", {"X-Forwarded-For": "9.9.9.9, 203.0.113.9"})
    assert get_client_ip(a) == "203.0.113.9"


def test_ohne_proxy_bleibt_der_direkte_peer(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXIES", "172.22.0.1")
    a = Anfrage("198.51.100.4", {})
    assert get_client_ip(a) == "198.51.100.4"
