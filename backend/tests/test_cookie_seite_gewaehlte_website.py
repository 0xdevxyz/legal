"""
Waechter: die Cookie-Seite bleibt bei der gewaehlten Website.

Befund 19.10.2026 (Agenturkonto, 10 Websites): spedition-mahn.de analysiert,
Cookies geoeffnet, der Einrichtungsassistent scannte spedition-mahn.de, und
danach las der Designer die Markenfarben von steinhau.de. Ursache: nach dem
Assistenten lud die Seite ueber `loadConfig()` neu, und der fragt
`/api/cookie-compliance/my-config`, also die zuletzt angelegte Konfiguration
des Kontos, egal welche Website gerade gewaehlt ist. Bei einem Konto mit
mehreren Websites ist das irgendeine andere.

Nach dem Assistenten muss die Seite die Konfiguration DERSELBEN Website neu
laden (`loadSiteConfig(siteId, ...)`); `loadConfig()` bleibt nur der Rueckfall
fuer den Fall, dass noch keine Website gewaehlt ist.
"""
import os
import re

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DASHBOARD_SRC = os.path.abspath(
    os.getenv("COMPLYO_DASHBOARD_SRC")
    or os.path.join(_BACKEND, "..", "dashboard-react", "src")
)
_SEITE = os.path.join(_DASHBOARD_SRC, "app", "cookie-compliance", "page.tsx")


def _assistent_abschluss(src: str) -> str:
    """Der onComplete-Handler des Einrichtungsassistenten, als Text."""
    start = src.index("<CookieSetupWizard")
    block = src[start:]
    m = re.search(r"onComplete=\{", block)
    assert m, "CookieSetupWizard ohne onComplete"
    tiefe, i = 0, m.end() - 1
    while i < len(block):
        if block[i] == "{":
            tiefe += 1
        elif block[i] == "}":
            tiefe -= 1
            if tiefe == 0:
                return block[m.end():i]
        i += 1
    raise AssertionError("onComplete nicht abgeschlossen")


class TestAssistentBleibtBeiDerWebsite:
    def test_nach_dem_assistenten_wird_dieselbe_website_geladen(self):
        if not os.path.exists(_SEITE):
            pytest.skip(f"Dashboard-Quelle nicht gefunden: {_SEITE}")
        with open(_SEITE, encoding="utf-8") as fh:
            src = fh.read()
        handler = _assistent_abschluss(src)
        # Kommentare raus, sonst zaehlt ein erklaerender Satz als Aufruf.
        handler = re.sub(r"//[^\n]*", "", handler)
        assert "loadSiteConfig(siteId" in handler, (
            "Nach dem Einrichtungsassistenten muss die Konfiguration der "
            "gewaehlten Website neu geladen werden (loadSiteConfig(siteId, ...)). "
            f"Handler:\n{handler}"
        )
        # loadConfig() (= /my-config, zuletzt angelegte Konfiguration des Kontos)
        # darf nur als Rueckfall ohne gewaehlte Website laufen.
        for m in re.finditer(r"loadConfig\(\)", handler):
            davor = handler[: m.start()]
            assert re.search(r"else\s*$", davor), (
                "loadConfig() laeuft hier ohne Rueckfall-Bedingung und springt bei "
                "Konten mit mehreren Websites auf eine fremde Website. "
                f"Handler:\n{handler}"
            )
