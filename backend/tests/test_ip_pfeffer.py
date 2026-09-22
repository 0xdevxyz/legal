"""Der Hashwert der IP-Adresse darf nicht rueckrechenbar sein.

Anlass (23.09.2026): Anlage 2 des Auftragsverarbeitungsvertrages beschrieb
einen "gekuerzten Hashwert der IP-Adresse". Gespeichert wurde der
vollstaendige SHA-256 ohne Zusatzwert. Weder gekuerzt noch anonym: bei IPv4
gibt es rund 4,3 Milliarden Moeglichkeiten, das rechnet handelsuebliche
Hardware in Minuten durch. Wer den Datenbankabzug hat, haette damit die
Klartext-Adressen der Besucher aller Kundenwebsites gehabt.

Diese Pruefungen halten drei Eigenschaften fest, die zusammengehoeren:

1. Mit Pfeffer unterscheidet sich der Wert vom blanken Hash. Sonst wirkt die
   Massnahme nicht, egal was in der Anlage steht.
2. Derselbe Besucher ergibt innerhalb einer Pfeffer-Periode denselben Wert.
   Ohne diese Eigenschaft waere das Einwilligungsprotokoll als Nachweis
   wertlos, weil sich zwei Zeilen desselben Besuchers nicht mehr zuordnen
   liessen.
3. Ohne Pfeffer laeuft die Protokollierung weiter. Das ist Absicht: eine
   Einwilligung, die gar nicht erst festgehalten wird, vernichtet den
   Nachweis nach Art. 7 Abs. 1 DSGVO sofort. Ein schwacher Hashwert ist ein
   Mangel, ein fehlender Nachweis ist ein Ausfall.
"""
import hashlib
import importlib
import os

import pytest

ccr = importlib.import_module("cookie_compliance_routes")

IP = "203.0.113.47"
BLANK = hashlib.sha256(IP.encode()).hexdigest()


@pytest.fixture
def ohne_pfeffer(monkeypatch):
    monkeypatch.delenv("COMPLYO_IP_PFEFFER", raising=False)


@pytest.fixture
def mit_pfeffer(monkeypatch):
    monkeypatch.setenv("COMPLYO_IP_PFEFFER", "probe-pfeffer-2026-09")


def test_leere_adresse_bleibt_leer(mit_pfeffer):
    assert ccr.hash_ip_address("") == ""
    assert ccr.hash_ip_address(None) == ""


def test_mit_pfeffer_nicht_der_blanke_hash(mit_pfeffer):
    wert = ccr.hash_ip_address(IP)
    assert wert != BLANK, (
        "Der Pfeffer wirkt nicht. Der gespeicherte Wert waere weiterhin durch "
        "Durchrechnen aller IPv4-Adressen aufloesbar."
    )
    assert len(wert) == 64


def test_gleicher_besucher_gleicher_wert(mit_pfeffer):
    assert ccr.hash_ip_address(IP) == ccr.hash_ip_address(IP)


def test_anderer_pfeffer_anderer_wert(monkeypatch):
    monkeypatch.setenv("COMPLYO_IP_PFEFFER", "periode-a")
    a = ccr.hash_ip_address(IP)
    monkeypatch.setenv("COMPLYO_IP_PFEFFER", "periode-b")
    b = ccr.hash_ip_address(IP)
    assert a != b, "Ein Wechsel des Pfeffers muss den Wert aendern."


def test_ohne_pfeffer_wird_weiter_protokolliert(ohne_pfeffer, caplog):
    """Fail-open, aber laut.

    Der Rueckfall auf den blanken Hash ist gewollt. Er darf nur nicht still
    passieren, sonst laeuft die Anlage 2 des AVV wieder an der Wirklichkeit
    vorbei, ohne dass es jemand merkt.
    """
    with caplog.at_level("WARNING"):
        wert = ccr.hash_ip_address(IP)
    assert wert == BLANK
    assert any("COMPLYO_IP_PFEFFER" in satz.message for satz in caplog.records), (
        "Ohne Pfeffer muss eine Warnung im Log stehen."
    )
