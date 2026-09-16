"""Der Pruefstand darf 127.0.0.1 abrufen. Sonst niemand.

tools/ground_truth_validation.py serviert vier Fixture-Seiten auf Loopback und
schickt sie durch die echte Pipeline. Seit die SSRF-Schranke jeden Abruf
prueft (065f6cd, 09.09.2026), kam dort nichts mehr an: null Befunde auf allen
vier Fixtures, und das sah aus wie ein bestandener Lauf. Eine Woche lang war
das Release-Gate offen, ohne dass es jemand merkte.
"""

import ipaddress
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ssrf_protection import SSRFError, _check_ip


@pytest.fixture
def ohne_freigabe(monkeypatch):
    monkeypatch.delenv("SSRF_PRUEFSTAND_LOOPBACK", raising=False)


@pytest.fixture
def mit_freigabe(monkeypatch):
    monkeypatch.setenv("SSRF_PRUEFSTAND_LOOPBACK", "1")


def test_ohne_freigabe_bleibt_loopback_gesperrt(ohne_freigabe):
    with pytest.raises(SSRFError):
        _check_ip(ipaddress.ip_address("127.0.0.1"))


def test_nur_der_wert_1_gibt_frei(monkeypatch):
    monkeypatch.setenv("SSRF_PRUEFSTAND_LOOPBACK", "true")
    with pytest.raises(SSRFError):
        _check_ip(ipaddress.ip_address("127.0.0.1"))


def test_mit_freigabe_geht_loopback(mit_freigabe):
    _check_ip(ipaddress.ip_address("127.0.0.1"))
    _check_ip(ipaddress.ip_address("::1"))


@pytest.mark.parametrize("ip", ["169.254.169.254", "10.0.0.1", "172.17.0.2",
                                "192.168.1.1", "0.0.0.0", "fd00::1"])
def test_die_freigabe_oeffnet_sonst_nichts(mit_freigabe, ip):
    """Genau die Adressen, um die es der Schranke geht: Metadaten-Dienst,
    Docker-Netz, private Bereiche. Bleiben zu, Freigabe hin oder her."""
    with pytest.raises(SSRFError):
        _check_ip(ipaddress.ip_address(ip))


def test_der_pruefstand_setzt_die_freigabe_selbst():
    src = open(os.path.join(os.path.dirname(__file__), "..", "tools",
                            "ground_truth_validation.py"), encoding="utf-8").read()
    assert 'os.environ["SSRF_PRUEFSTAND_LOOPBACK"] = "1"' in src


def test_compose_setzt_die_freigabe_nirgends():
    """Die Freigabe gehoert in keinen Dienst, nur in den Pruefstand-Prozess."""
    wurzel = os.path.join(os.path.dirname(__file__), "..", "..")
    for name in ("docker-compose.yml", "docker-compose.sentry.yml"):
        pfad = os.path.join(wurzel, name)
        if os.path.exists(pfad):
            assert "SSRF_PRUEFSTAND_LOOPBACK" not in open(pfad, encoding="utf-8").read()
