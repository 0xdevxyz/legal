"""Die Engine liest den Rechtsraum, und zwar vollstaendig.

Bis zum 23.09.2026 lief jede Website durch dieselben deutschen Pruefungen. Das
Fundament dafuer lag seit Monaten da (context.py, jurisdictions.py, Spalten in
der Datenbank) und war an nichts angeschlossen: `active_checks` wurde nirgends
aufgerufen.

Diese Pruefungen halten drei Dinge fest:

1. **Deutschland bleibt, wie es war.** Das Profil `de` fuehrt genau die
   Pruefungen, die vorher fest verdrahtet waren. Eine fehlende waere eine
   stille Verschlechterung fuer jeden Bestandskunden.
2. **Die Registry und der Scanner sagen dasselbe.** Steht eine Pruefung im
   Profil, muss der Scanner sie auch verdrahten, sonst ist sie still
   abgeschaltet. Bis zum 23.09. nannte das Profil `de` neun Pruefungen,
   waehrend der Scanner vierzehn ausfuehrte.
3. **Ausserhalb Deutschlands laufen die nationalen Pruefungen nicht**, und die
   Saeule, zu der sie gehoeren, wird nicht gewertet. Sonst zoege eine Pflicht,
   die es dort nicht gibt, den Punktestand nach unten.
"""
import pathlib
import re

import pytest

from compliance_engine.context import ScanContext
from compliance_engine.jurisdictions import (
    DEFAULT_JURISDICTION,
    JURISDICTION_PROFILES,
    UNIONSWEIT,
    active_checks,
    active_pillars,
)
from compliance_engine.score_calculator import ScoreCalculator

QUELLE = (pathlib.Path(__file__).resolve().parent.parent
          / "compliance_engine" / "scanner.py").read_text(encoding="utf-8")

# Die Pruefungen, die vor dem Umbau fest im Scanner standen. Abgeschrieben aus
# dem asyncio.gather-Aufruf der Fassung vom 22.09.2026, plus tcf, das schon
# damals gesondert lief.
FRUEHER_FEST_VERDRAHTET = {
    "barrierefreiheit", "impressum", "datenschutz", "cookie", "agb",
    "pangv", "widerruf",          # beide ueber shop_check
    "deklarativ", "uwg", "ssl", "kontakt", "social", "ai_act", "ki_bild",
    "tcf",
}


def test_deutschland_fuehrt_weiter_alle_frueheren_pruefungen():
    fehlt = FRUEHER_FEST_VERDRAHTET - set(active_checks("de"))
    assert not fehlt, (
        f"Das Profil 'de' fuehrt diese frueher fest verdrahteten Pruefungen nicht "
        f"mehr: {sorted(fehlt)}. Fuer jeden Bestandskunden waere das eine stille "
        f"Verschlechterung.")


def test_registry_und_scanner_sagen_dasselbe():
    """Jede Pruefung im Profil muss im Scanner verdrahtet sein.

    Sonst steht sie in der Registry, laeuft aber nicht, und niemand merkt es,
    weil ein fehlender Befund aussieht wie ein bestandener Check.
    """
    from compliance_engine.scanner import MODUL_DECKT_AB
    verdrahtet = set(re.findall(r'_wenn\(\s*"([a-z_]+)"', QUELLE))
    verdrahtet |= set(re.findall(r'aufgaben\[\s*"([a-z_]+)"\s*\]\s*=', QUELLE))
    # Module, die mehrere Registry-Namen mitbedienen.
    for namen in MODUL_DECKT_AB.values():
        verdrahtet |= set(namen)
    # tcf laeuft in einem eigenen Block weiter unten, ohne _wenn.
    verdrahtet.add("tcf")

    fehlt = set(active_checks("de")) - verdrahtet
    assert not fehlt, (
        f"Diese Pruefungen stehen im Profil 'de', der Scanner verdrahtet sie "
        f"aber nicht: {sorted(fehlt)}")

    # Die Schluessel von MODUL_DECKT_AB sind Modulnamen, keine Registry-Namen.
    zuviel = verdrahtet - set(active_checks("de")) - {"tcf"} - set(MODUL_DECKT_AB)
    assert not zuviel, (
        f"Der Scanner verdrahtet Pruefungen, die in keinem Profil stehen: "
        f"{sorted(zuviel)}. Dann entscheidet der Rechtsraum ueber sie nicht.")


@pytest.mark.parametrize("pruefung", ["impressum", "agb", "uwg", "pangv", "widerruf"])
def test_nationale_pruefungen_laufen_im_eu_profil_nicht(pruefung):
    assert pruefung in active_checks("de")
    assert pruefung not in active_checks("eu"), (
        f"{pruefung} ist nationales Recht und darf im generischen EU-Profil "
        f"nicht laufen: der Befund waere gegen ein Gesetz gemessen, das dort "
        f"nicht gilt.")


@pytest.mark.parametrize("pruefung", UNIONSWEIT)
def test_unionsweite_pruefungen_stehen_in_jedem_profil(pruefung):
    for name in JURISDICTION_PROFILES:
        assert pruefung in active_checks(name), (
            f"{pruefung} beruht auf unionsweit geltendem Recht und fehlt im "
            f"Profil {name}.")


def test_eu_hat_keine_saeule_legal():
    assert "legal" in active_pillars("de")
    assert "legal" not in active_pillars("eu")


def test_fehlende_saeule_zieht_den_punktestand_nicht_nach_unten():
    """Der messbare Kern von Schritt 1.4.

    Ein fehlendes Impressum ist in Deutschland ein Mangel und draengt den
    Gesamtwert. Im generischen EU-Profil gibt es die Pflicht nicht; sie darf
    dort auch nicht als Null in den Mittelwert eingehen.
    """
    werte = {"accessibility": 80, "gdpr": 90, "legal": 0, "cookies": 70}
    deutsch = ScoreCalculator.calculate_overall_score(
        werte, aktive_saeulen=active_pillars("de"))
    europaeisch = ScoreCalculator.calculate_overall_score(
        werte, aktive_saeulen=active_pillars("eu"))
    assert deutsch == 60
    assert europaeisch == 80
    assert europaeisch > deutsch


def test_ohne_angabe_bleibt_alles_wie_bisher():
    """Der Rueckfall muss der alte Zustand sein, nicht ein neuer."""
    werte = {"accessibility": 80, "gdpr": 90, "legal": 0, "cookies": 70}
    assert (ScoreCalculator.calculate_overall_score(werte)
            == ScoreCalculator.calculate_overall_score(
                werte, aktive_saeulen=active_pillars("de")))


# ---------------------------------------------------------------------------
# ScanContext
# ---------------------------------------------------------------------------
def test_scan_website_nimmt_den_rechtsraum_entgegen():
    import inspect
    from compliance_engine.scanner import ComplianceScanner
    sig = inspect.signature(ComplianceScanner.scan_website)
    assert "jurisdiction" in sig.parameters
    assert sig.parameters["jurisdiction"].default == DEFAULT_JURISDICTION, (
        "Die Vorgabe muss der deutsche Rechtsraum bleiben. Jeder Aufrufer, der "
        "nichts angibt, bekommt sonst ein anderes Ergebnis als vorher.")


def test_unbekannter_rechtsraum_faellt_auf_die_vorgabe():
    ctx = ScanContext(url="https://beispiel.de", jurisdiction="kl-ingonisch")
    assert ctx.jurisdiction == DEFAULT_JURISDICTION
    assert ctx.language == "de"


def test_eu_kontext_spricht_englisch():
    ctx = ScanContext(url="https://example.com", jurisdiction="eu")
    assert ctx.jurisdiction == "eu"
    assert ctx.language == "en"


def test_keine_koroutine_bleibt_unerwartet():
    """Eine nicht aktive Pruefung darf keine offene Koroutine hinterlassen.

    Sonst steht bei jedem EU-Scan eine RuntimeWarning im Log, und der Speicher
    fuellt sich langsam mit Koroutinen, die nie laufen.
    """
    assert "koroutine.close()" in QUELLE, (
        "Der Zweig fuer nicht aktive Pruefungen schliesst die Koroutine nicht.")


# ---------------------------------------------------------------------------
# Schritt 1.5: das Landesgatter der deklarativen Pruefungen
# ---------------------------------------------------------------------------
from bs4 import BeautifulSoup  # noqa: E402

from compliance_engine.declarative_check_runner import _gate_passes  # noqa: E402

LEER = BeautifulSoup("<html><body></body></html>", "html.parser")


def test_ohne_land_gilt_eine_pruefung_ueberall():
    """Der Bestand stammt aus unionsweitem Recht und soll weiterlaufen.

    Die 50 erzeugten Pruefungen tragen heute kein `land`. Wuerde ein fehlender
    Schluessel als "nur Deutschland" gelesen, waere der gesamte
    Rechtsupdate-Dienst ausserhalb Deutschlands still abgeschaltet.
    """
    assert _gate_passes({"always": True}, LEER, "", "eu") is True
    assert _gate_passes({}, LEER, "", "eu") is True


def test_land_schlaegt_always():
    """Eine nationale Pflicht ist in ihrem Land ausnahmslos, aber nur dort.

    Waere `always` staerker, wuerde der Widerrufsbutton nach deutschem Recht
    auch einer niederlaendischen Website vorgehalten, und zwar ausnahmslos.
    """
    gatter = {"always": True, "land": ["de"]}
    assert _gate_passes(gatter, LEER, "", "de") is True
    assert _gate_passes(gatter, LEER, "", "eu") is False


def test_land_nimmt_auch_eine_einzelne_zeichenkette():
    """Das Feld kommt aus der Datenbank, also aus fremder Hand."""
    assert _gate_passes({"always": True, "land": "de"}, LEER, "", "eu") is False
    assert _gate_passes({"always": True, "land": "de"}, LEER, "", "de") is True


def test_mehrere_laender_moeglich():
    gatter = {"always": True, "land": ["de", "eu"]}
    assert _gate_passes(gatter, LEER, "", "eu") is True
    assert _gate_passes(gatter, LEER, "", "de") is True
