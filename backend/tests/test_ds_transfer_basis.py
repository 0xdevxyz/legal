"""
Tests fuer Tier 3 D: Die Drittlandtransfer-Rechtsgrundlage (SCC/DPF) wird auf
der DATENSCHUTZERKLAERUNGS-Seite geprueft, nicht auf der Homepage; der
Silent-Fail der Deep-Analyse erzeugt jetzt ein sichtbares info-Issue.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from bs4 import BeautifulSoup

from compliance_engine.checks.datenschutz_check import check_datenschutz_compliance


HOME_WITH_GA = """
<html><body>
  <a href="/datenschutz">Datenschutz</a>
  <script src="https://www.googletagmanager.com/gtag/js?id=G-1"></script>
  <p>Willkommen auf unserer Seite.</p>
</body></html>
"""

DS_PAGE_WITH_SCC = """
<html><body><h1>Datenschutzerklärung</h1>
<p>Verantwortlicher im Sinne der DSGVO: Muster GmbH.</p>
<p>Wir verarbeiten personenbezogene Daten auf Rechtsgrundlage Art. 6.</p>
<p>Ihre Betroffenenrechte: Auskunft, Löschung. Beschwerderecht bei der Aufsichtsbehörde.</p>
<p>Speicherdauer: 30 Tage. Zwecke: Analyse.</p>
<p>Für Google-Dienste bestehen Standardvertragsklauseln (SCC) nach Art. 46 DSGVO.</p>
</body></html>
"""


class _FakeResponse:
    def __init__(self, status, text):
        self.status = status
        self._text = text

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _FakeSession:
    """Liefert fuer /datenschutz die DS-Seite, sonst 404."""

    def __init__(self, ds_html):
        self._ds_html = ds_html

    def get(self, url, **kwargs):
        if "datenschutz" in url:
            return _FakeResponse(200, self._ds_html)
        return _FakeResponse(404, "")


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _titles(issues):
    return [i["title"] for i in issues]


@pytest.mark.asyncio
async def test_scc_on_ds_page_prevents_transfer_basis_issue():
    # SCC-Text steht NUR auf der DS-Seite, nicht auf der Homepage.
    # Frueher: Homepage-Pruefung -> False Positive. Jetzt: kein Issue.
    issues = await check_datenschutz_compliance(
        "https://example.com", _soup(HOME_WITH_GA),
        session=_FakeSession(DS_PAGE_WITH_SCC),
    )
    assert not any(
        "Übermittlungs-Rechtsgrundlage" in t or "Rechtsgrundlage für US" in t or "ohne erkennbare" in t
        for t in _titles(issues)
    ), _titles(issues)


@pytest.mark.asyncio
async def test_without_scc_anywhere_issue_fires():
    ds_no_scc = DS_PAGE_WITH_SCC.replace(
        "<p>Für Google-Dienste bestehen Standardvertragsklauseln (SCC) nach Art. 46 DSGVO.</p>", ""
    )
    issues = await check_datenschutz_compliance(
        "https://example.com", _soup(HOME_WITH_GA),
        session=_FakeSession(ds_no_scc),
    )
    assert any(i["category"] == "avv" and i["severity"] in ("warning", "critical") for i in issues)


@pytest.mark.asyncio
async def test_deep_analysis_failure_is_visible():
    class _BrokenSession:
        def get(self, url, **kwargs):
            if "datenschutz" in url:
                raise RuntimeError("kaputt")
            return _FakeResponse(404, "")

    issues = await check_datenschutz_compliance(
        "https://example.com", _soup(HOME_WITH_GA), session=_BrokenSession(),
    )
    assert any("Inhaltsprüfung" in t and "nicht möglich" in t for t in _titles(issues))
