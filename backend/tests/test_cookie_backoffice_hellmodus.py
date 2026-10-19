"""
Waechter: das Cookie-Backoffice ist im hellen Modus lesbar.

Befund Daniel 19.10.2026 (Screenshot, heller Modus): Eingabefelder im
Banner-Designer dunkelgrau mit dunkler Schrift, das Label „Beschreibung" fast
unsichtbar. Die Komponenten unter components/cookie-compliance waren nur fuer
den dunklen Modus gebaut: bg-gray-700, border-gray-600, text-gray-200 ohne
dark:-Praefix. Dieselbe Klasse Fehler wie am 04.08.2026 in acht anderen Dateien
(siehe Memory complyo-dashboard-ui-fallen).

Regel: Eine dunkle gray-Klasse (Flaeche 700+, Rand 600+, Schrift 200 bis 400)
braucht das dark:-Praefix. Ausgenommen ist die bewusst dunkle Banner-Vorschau
im Designer (Attrappe einer Website).
"""
import os
import re

import pytest

_DASHBOARD_SRC = os.path.abspath(
    os.getenv("COMPLYO_DASHBOARD_SRC")
    or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "dashboard-react", "src")
)
_ORDNER = os.path.join(_DASHBOARD_SRC, "components", "cookie-compliance")
_SEITE = os.path.join(_DASHBOARD_SRC, "app", "cookie-compliance", "page.tsx")

DUNKEL = re.compile(
    r"(?<![:\w-])(bg-gray-[789]00(?:/\d+)?|border-gray-[67]00|text-gray-[234]00"
    r"|hover:bg-gray-[678]00|placeholder:text-gray-400)(?![\w/-])"
)


def _vorschau_zeilen(zeilen):
    """Zeilen der dunklen Banner-Vorschau im Designer (Website-Attrappe)."""
    start = next((i for i, z in enumerate(zeilen) if "from-gray-900 to-gray-800" in z), None)
    if start is None:
        return set()
    ende = next((i for i in range(start, len(zeilen)) if "EyeOff" in zeilen[i]), len(zeilen) - 1)
    return set(range(start, ende + 4))


def _funde(pfad):
    with open(pfad, encoding="utf-8") as fh:
        zeilen = fh.read().split("\n")
    aus = _vorschau_zeilen(zeilen) if pfad.endswith("CookieBannerDesigner.tsx") else set()
    funde = []
    for i, z in enumerate(zeilen):
        if i in aus:
            continue
        for m in DUNKEL.finditer(z):
            if z[max(0, m.start() - 5):m.start()] == "dark:":
                continue
            funde.append(f"{os.path.basename(pfad)}:{i + 1}: {m.group(1)}")
    return funde


class TestHellmodus:
    def test_keine_dunkle_klasse_ohne_dark_praefix(self):
        if not os.path.isdir(_ORDNER):
            pytest.skip(f"Dashboard-Quellen nicht gefunden: {_ORDNER}")
        dateien = sorted(
            os.path.join(_ORDNER, n) for n in os.listdir(_ORDNER) if n.endswith(".tsx")
        ) + [_SEITE]
        funde = [f for p in dateien if os.path.exists(p) for f in _funde(p)]
        assert not funde, (
            f"{len(funde)} dunkle Klassen ohne dark:-Praefix im Cookie-Backoffice "
            "(im hellen Modus unlesbar):\n  " + "\n  ".join(funde[:40])
        )
