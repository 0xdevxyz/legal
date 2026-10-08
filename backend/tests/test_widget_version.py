# -*- coding: utf-8 -*-
"""Die Versionsnummer des Barrierefreiheits-Widgets steht an genau zwei
Stellen: im Widget (Fusszeile des Bedienfelds, WIDGET_VERSION) und im
Antwortkopf X-Complyo-Widget-Version der Route, die es ausliefert. Beide
muessen gleich sein, sonst sagt der Support-Blick in den Kopf etwas anderes
als die Kundin im Bedienfeld sieht.

Die Groesse der Fusszeile steht im Isolationsblock des Widget-CSS: dort setzt
ein revert !important jede Schrift im Widget zurueck. Die fruehere Angabe von
11px stand nur bei .complyo-version und verlor dagegen, gemessen wurden 16px.
"""

import os
import re

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _lies(*teile):
    return open(os.path.join(BACKEND, *teile), encoding="utf-8").read()


def _widget_version():
    t = re.search(r"const WIDGET_VERSION = '([^']+)'", _lies("widgets", "accessibility-v6.js"))
    assert t, "WIDGET_VERSION nicht gefunden"
    return t.group(1)


def test_kopf_nennt_dieselbe_version():
    t = re.search(r"'X-Complyo-Widget-Version':\s*'([^']+)'", _lies("widget_routes.py"))
    assert t, "Antwortkopf X-Complyo-Widget-Version nicht gefunden"
    assert t.group(1) == _widget_version()


def test_versionszeile_ist_klein_gegen_den_revert():
    css = _lies("widgets", "accessibility-v6.js")
    t = re.search(r"#complyo-a11y-widget \.complyo-version\s*\{[^}]*font-size:\s*(\d+)px\s*!important",
                  css)
    assert t, ("Groesse der Versionszeile fehlt im Isolationsblock: ohne "
               "'#complyo-a11y-widget .complyo-version { font-size: … !important }' "
               "gilt das revert, und die Zeile steht in 16px da.")
    assert int(t.group(1)) <= 10
