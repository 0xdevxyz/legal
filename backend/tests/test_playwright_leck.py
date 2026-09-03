"""Der Playwright-Treiber muss beendet werden, nicht nur der Browser.

ScreenshotService.__aenter__ hielt das Objekt aus async_playwright().start()
in einer lokalen Variablen. Nach dem Verlassen von __aenter__ war es nicht
mehr erreichbar, `.stop()` konnte gar nicht aufgerufen werden. Zurueck blieb
je Aufruf ein node-Prozess von rund 60 MB.

Der Dienst laeuft bei JEDEM Barrierefreiheits-Scan. Gemessen am 03.09.2026:
elf solcher Prozesse nach acht Stunden, Grundverbrauch 142 MiB -> 545 MiB bei
1 GiB Limit. Nicht die Gleichzeitigkeit war zu hoch, der Grundverbrauch war es.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.screenshot_service import ScreenshotService


class FakePlaywright:
    def __init__(self):
        self.gestoppt = 0
        self.chromium = MagicMock()
        self.chromium.launch = AsyncMock(return_value=FakeBrowser())

    async def stop(self):
        self.gestoppt += 1


class FakeBrowser:
    def __init__(self):
        self.geschlossen = 0

    async def close(self):
        self.geschlossen += 1


class FakeStarter:
    """Ersetzt async_playwright(); merkt sich jede erzeugte Instanz."""

    def __init__(self):
        self.instanzen = []

    def __call__(self):
        self._naechste = FakePlaywright()
        self.instanzen.append(self._naechste)
        return self

    async def start(self):
        return self._naechste


@pytest.fixture
def starter():
    s = FakeStarter()
    with patch("compliance_engine.screenshot_service.async_playwright", s):
        yield s


@pytest.mark.asyncio
class TestTreiberWirdBeendet:
    async def test_stop_wird_aufgerufen(self, starter):
        async with ScreenshotService():
            pass
        assert starter.instanzen[0].gestoppt == 1, \
            "Der Playwright-Treiber blieb laufen — genau das Leck"

    async def test_browser_wird_geschlossen(self, starter):
        async with ScreenshotService() as svc:
            browser = svc.browser
        assert browser.geschlossen == 1

    async def test_kein_prozess_bleibt_bei_zehn_durchlaeufen(self, starter):
        """Zehn Scans hintereinander duerfen keine zehn Treiber hinterlassen."""
        for _ in range(10):
            async with ScreenshotService():
                pass
        offen = [p for p in starter.instanzen if p.gestoppt == 0]
        assert not offen, f"{len(offen)} Treiber blieben laufen"


@pytest.mark.asyncio
class TestAufraeumenIstRobust:
    async def test_treiber_endet_auch_wenn_browser_schliessen_scheitert(self, starter):
        """Sonst entsteht das Leck bei jedem Fehlerfall neu."""
        svc = ScreenshotService()
        await svc.__aenter__()
        svc.browser.close = AsyncMock(side_effect=RuntimeError("kaputt"))
        await svc.__aexit__(None, None, None)
        assert starter.instanzen[0].gestoppt == 1

    async def test_ausnahme_im_block_raeumt_trotzdem_auf(self, starter):
        with pytest.raises(ValueError):
            async with ScreenshotService():
                raise ValueError("Scan fehlgeschlagen")
        assert starter.instanzen[0].gestoppt == 1

    async def test_zweites_aexit_faellt_nicht_um(self, starter):
        svc = ScreenshotService()
        await svc.__aenter__()
        await svc.__aexit__(None, None, None)
        await svc.__aexit__(None, None, None)   # darf nicht werfen
        assert starter.instanzen[0].gestoppt == 1

    async def test_referenzen_werden_geloest(self, starter):
        svc = ScreenshotService()
        await svc.__aenter__()
        await svc.__aexit__(None, None, None)
        assert svc.browser is None
        assert svc._playwright is None
