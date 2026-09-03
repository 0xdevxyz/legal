"""
Tests fuer die Pre-Consent-Evidenz-Hierarchie und Planet49-Toggles (Tier 3 A).

Kern: Das 10k-Issue "Tracking vor Consent" stuetzt sich primaer auf den
Netzwerk-Mitschnitt des Consent-freien Renders (request_urls) und faellt nur
ohne Render auf den statischen <script src>-Scan zurueck.
"""

import pytest
from bs4 import BeautifulSoup

from compliance_engine.checks.cookie_check import (
    check_cookie_compliance,
    _find_prechecked_toggles,
)
from compliance_engine.tracker_catalog import (
    match_tracking_request,
    match_tracking_script_src,
)
from compliance_engine.automated_cookie_scanner import _guess_category


BANNER_HTML = """
<html><body>
<div class="cookie-banner" id="cb">
  <p>Wir verwenden Cookies.</p>
  <button id="acc">Alle akzeptieren</button>
  <button id="rej">Alle ablehnen</button>
  <a href="/cookie-einstellungen">Cookie-Einstellungen</a>
  <span>Statistik Marketing</span>
  <span>Einwilligung jederzeit widerrufen</span>
</div>
{extra}
</body></html>
"""


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _titles(issues):
    return [i["title"] for i in issues]


def _has_preconsent_issue(issues):
    return any("vor Consent geladen" in t for t in _titles(issues))


# ---------------- Netzwerk-Evidenz (Evidenz A) ----------------

@pytest.mark.asyncio
async def test_network_evidence_fires_10k_issue():
    soup = _soup(BANNER_HTML.format(extra=""))
    issues = await check_cookie_compliance(
        "https://example.com", soup,
        request_urls=["https://region1.google-analytics.com/g/collect?v=2&tid=G-1"],
    )
    assert _has_preconsent_issue(issues)
    issue = next(i for i in issues if "vor Consent geladen" in i["title"])
    assert "Netzwerk-Mitschnitt" in issue["description"]
    assert issue["risk_euro"] == 10000


@pytest.mark.asyncio
async def test_functional_requests_do_not_fire():
    soup = _soup(BANNER_HTML.format(extra=""))
    issues = await check_cookie_compliance(
        "https://example.com", soup,
        request_urls=["https://fonts.googleapis.com/css2?family=Roboto"],
    )
    assert not _has_preconsent_issue(issues)


@pytest.mark.asyncio
async def test_blocked_scripts_with_empty_network_do_not_fire():
    # Render lief (request_urls=[]), GA-Script steht als text/plain im HTML
    # (Blocker aktiv) -> kein Issue, weil real nichts geladen wurde.
    extra = '<script type="text/plain" src="https://www.googletagmanager.com/gtag/js?id=G-1"></script>'
    soup = _soup(BANNER_HTML.format(extra=extra))
    issues = await check_cookie_compliance(
        "https://example.com", soup, request_urls=[],
    )
    assert not _has_preconsent_issue(issues)


@pytest.mark.asyncio
async def test_consent_mode_loader_alone_is_not_network_evidence():
    soup = _soup(BANNER_HTML.format(extra=""))
    issues = await check_cookie_compliance(
        "https://example.com", soup,
        request_urls=["https://www.googletagmanager.com/gtag/js?id=G-1"],
    )
    assert not _has_preconsent_issue(issues)


# ---------------- Statischer Fallback (Evidenz B) ----------------

@pytest.mark.asyncio
async def test_static_fallback_without_render():
    extra = '<script src="https://www.googletagmanager.com/gtag/js?id=G-1"></script>'
    soup = _soup(BANNER_HTML.format(extra=extra))
    issues = await check_cookie_compliance("https://example.com", soup)  # request_urls=None
    assert _has_preconsent_issue(issues)


@pytest.mark.asyncio
async def test_legacy_positional_call_signature():
    soup = _soup(BANNER_HTML.format(extra=""))
    issues = await check_cookie_compliance("https://example.com", soup, None)
    assert isinstance(issues, list)


# ---------------- Katalog-Verhalten ----------------

def test_catalog_collect_endpoint_is_evidence():
    assert match_tracking_request("https://google-analytics.com/g/collect?x=1") is not None
    assert match_tracking_request("https://www.facebook.com/tr?id=1") is not None


def test_catalog_excludes_video_embeds():
    assert match_tracking_request("https://www.youtube.com/embed/abc") is None
    assert match_tracking_script_src("https://www.youtube.com/embed/abc") is None


def test_static_match_includes_google_loader():
    assert match_tracking_script_src("https://www.googletagmanager.com/gtag/js?id=G-1") is not None


# ---------------- Planet49: vorangekreuzte Toggles ----------------

def test_prechecked_marketing_toggle_flagged():
    banner = _soup(
        '<div class="cookie-banner">'
        '<input type="checkbox" checked name="marketing"><label>Marketing</label>'
        "</div>"
    ).find("div")
    assert len(_find_prechecked_toggles(banner)) == 1


def test_prechecked_disabled_necessary_not_flagged():
    banner = _soup(
        '<div class="cookie-banner">'
        '<input type="checkbox" checked disabled name="necessary">'
        '<input type="checkbox" checked id="ess"><label for="ess">Technisch erforderlich</label>'
        "</div>"
    ).find("div")
    assert _find_prechecked_toggles(banner) == []


@pytest.mark.asyncio
async def test_prechecked_toggle_creates_warning_issue():
    extra = ""
    html = BANNER_HTML.format(extra=extra).replace(
        "<p>Wir verwenden Cookies.</p>",
        '<p>Wir verwenden Cookies.</p><input type="checkbox" checked name="statistik-cookies">',
    )
    issues = await check_cookie_compliance("https://example.com", _soup(html), request_urls=[])
    toggle_issues = [i for i in issues if "Vorangekreuzte" in i["title"]]
    assert len(toggle_issues) == 1
    assert toggle_issues[0]["severity"] == "warning"


# ---------------- uncategorized-Default ----------------

def test_unknown_cookie_uncategorized():
    assert _guess_category("xyz_random_cookie") == "uncategorized"


def test_known_cookie_categories_unchanged():
    assert _guess_category("_ga") == "analytics"
    assert _guess_category("csrftoken") == "necessary"
