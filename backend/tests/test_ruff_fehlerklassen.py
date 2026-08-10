"""
Undefinierte Namen, verdeckte Definitionen, doppelte Schluessel — nie wieder.

Dieses Audit hat gezeigt, wie teuer diese Klasse ist. Sie faellt nicht beim
Start auf, sondern erst, wenn ein Kunde die betroffene Zeile ausloest:

  * `re` fehlte in public_routes.py  -> JEDER Scan brach ab, im oeffentlichen
    Hauptendpunkt, mit "name 're' is not defined" fuer den Kunden
  * `io` fehlte ebendort             -> ZIP-Download brach ab
  * `datetime` in email_service.py   -> vier Mail-Vorlagen wurden nie verschickt
  * `logger` in widget_routes.py     -> drei Stellen der Widget-Auslieferung
  * `scan_result` in public_routes   -> der RUECKFALL fuer gescheiterte Scans
                                        stuerzte selbst ab
  * `count_query` in ai_legal_routes -> Archiv-Endpunkt bei jedem Aufruf tot
  * `ext` im Paketgenerator          -> README-Erzeugung brach ab
  * `demo_fixes` in widget_routes    -> Patch-Download brach ab
  * `rollback` doppelt definiert     -> die erste Fassung unerreichbar
  * zwei doppelte Dict-Schluessel    -> stille Ueberschreibung in einer
                                        Zuordnungstabelle fuer Rechtsbereiche

Elf Stueck, alle in Nutzerpfaden, keiner von 1250 Tests erfasst — weil kein
Test diese Zeilen ausfuehrt. Ein Linter braucht dafuer keine Ausfuehrung.

Der Test laeuft nur, wenn `ruff` installiert ist, und ueberspringt sonst mit
Hinweis. So blockiert er niemanden, meldet sich aber ueberall dort, wo die
Werkzeugkette vollstaendig ist.
"""
import os
import subprocess
import sys

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Nur die Regeln, die echte Laufzeitfehler bedeuten — bewusst KEIN Stilkram.
# Ein Waechter, der ueber unbenutzte Importe meckert, wird abgeschaltet und
# faengt dann auch die echten Fehler nicht mehr.
REGELN = ",".join([
    "F821",  # undefinierter Name       -> NameError zur Laufzeit
    "F811",  # Definition ueberdeckt    -> die falsche Fassung gewinnt
    "F601",  # doppelter Dict-Schluessel-> stille Ueberschreibung
    "F502",  # Formatierungsfehler
    "F522",  # unbekanntes Format-Feld
    "E999",  # Syntaxfehler
])


def _ruff_da() -> bool:
    try:
        subprocess.run(["ruff", "--version"], capture_output=True, timeout=20)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


@pytest.mark.skipif(
    not _ruff_da(),
    reason=("ruff nicht installiert — `pip install ruff`, dann faengt dieser "
            "Test undefinierte Namen ab, bevor ein Kunde sie ausloest"),
)
def test_keine_laufzeitfehler_im_quelltext():
    ergebnis = subprocess.run(
        ["ruff", "check", ".", "--select", REGELN, "--output-format", "concise"],
        cwd=WURZEL, capture_output=True, text=True, timeout=300,
    )
    if ergebnis.returncode != 0:
        zeilen = [z for z in ergebnis.stdout.splitlines() if z.strip()]
        pytest.fail(
            "Laufzeitfehler im Quelltext — diese Zeilen brechen ab, sobald sie "
            "ausgefuehrt werden:\n  " + "\n  ".join(zeilen[:25])
        )


class TestDieRegelauswahlBleibtEng:
    """
    Die Auswahl darf nicht zum Stil-Linter wachsen. Sonst wird er
    abgeschaltet — und faengt dann auch die echten Fehler nicht mehr.
    """

    def test_nur_fehlerklassen(self):
        for regel in REGELN.split(","):
            assert regel.startswith(("F", "E9")), regel

    def test_die_wichtigste_ist_dabei(self):
        assert "F821" in REGELN, "undefinierte Namen sind der Grund fuer diesen Test"

    def test_kein_stil(self):
        for stil in ("E501", "W", "I", "N", "D", "COM", "Q"):
            assert stil not in REGELN.split(","), stil
