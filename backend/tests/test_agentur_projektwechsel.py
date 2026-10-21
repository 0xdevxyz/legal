"""
Waechter: bei Agenturkonten folgt jede Unterseite dem aktiven Projekt.

Befund 21.10.2026: links im SiteSwitcher rru-chemnitz gewaehlt, "Cookies"
geoeffnet, und die Seite arbeitete auf steinhau.de. Die Cookie-Seite, die
Abmahnpruefung und der Deep-Scanner bestimmten ihre Website jeweils selbst
(Primaerseite oder erste der Liste) und wussten nichts vom SiteSwitcher.

Jetzt lesen alle drei `useActiveSite()`; die Cookie-Seite reagiert in einem
Effekt auf `activeSite` und spiegelt ihre eigene Auswahl per `setActiveSite`
zurueck, damit die naechste Unterseite nicht wieder woanders steht. Dieser
Test liest den Quelltext, wie test_cookie_seite_gewaehlte_website.py.
"""
import os
import re

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DASHBOARD_SRC = os.path.abspath(
    os.getenv("COMPLYO_DASHBOARD_SRC")
    or os.path.join(_BACKEND, "..", "dashboard-react", "src")
)

SEITEN = {
    "cookie-compliance": os.path.join(_DASHBOARD_SRC, "app", "cookie-compliance", "page.tsx"),
    "abmahnung": os.path.join(_DASHBOARD_SRC, "app", "abmahnung", "page.tsx"),
    "deep-cookie-scanner": os.path.join(_DASHBOARD_SRC, "app", "deep-cookie-scanner", "page.tsx"),
}


def _quelle(name):
    pfad = SEITEN[name]
    if not os.path.exists(pfad):
        pytest.skip(f"{pfad} nicht vorhanden; Dashboard-Quelltext mounten oder COMPLYO_DASHBOARD_SRC setzen")
    return open(pfad, encoding="utf-8").read()


@pytest.mark.parametrize("seite", sorted(SEITEN))
def test_unterseite_liest_das_aktive_projekt(seite):
    src = _quelle(seite)
    assert "useActiveSite()" in src, f"{seite}: kennt den SiteSwitcher nicht (useActiveSite fehlt)"
    assert re.search(r"\bactiveSite\b", src), f"{seite}: liest activeSite nicht"


def test_cookie_seite_wechselt_mit_dem_projekt():
    src = _quelle("cookie-compliance")
    # Ein Effekt, der auf activeSite reagiert und die Konfiguration des
    # gewaehlten Projekts laedt.
    m = re.search(r"useEffect\(\(\) => \{(.*?)\}, \[isAgency, activeSite\?\.id", src, re.S)
    assert m, "kein Effekt auf activeSite"
    assert "loadSiteConfig(sid, activeSite.url)" in m.group(1)


def test_cookie_seite_spiegelt_ihre_auswahl_zurueck():
    src = _quelle("cookie-compliance")
    assert "setActiveSite(projekt)" in src, "die eigene Auswahl erreicht den SiteSwitcher nicht"


def test_cookie_seite_startet_mit_dem_aktiven_projekt():
    src = _quelle("cookie-compliance")
    assert "list.find((s) => s.site_id === aktiv)" in src, (
        "loadAgencySites nimmt wieder die Primaerseite statt des aktiven Projekts"
    )
