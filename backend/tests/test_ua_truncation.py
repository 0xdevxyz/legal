"""Unit tests for truncate_user_agent (AUDIT-03 — DSGVO-compliant UA truncation)."""
from cookie_compliance_routes import truncate_user_agent


def test_empty_returns_unknown():
    assert truncate_user_agent("") == "unknown"


def test_none_returns_unknown():
    assert truncate_user_agent(None) == "unknown"


def test_chrome_ua():
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    assert truncate_user_agent(ua) == "Chrome/120"


def test_firefox_ua():
    ua = "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
    assert truncate_user_agent(ua) == "Firefox/121"


def test_edge_ua_matches_edge_not_chrome():
    # Edge UA contains both Edg/ and Chrome/ — regex MUST match Edge first
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.144")
    assert truncate_user_agent(ua) == "Edge/120"


def test_opera_ua():
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0")
    assert truncate_user_agent(ua) == "OPR/106"


def test_mobile_chrome_ios():
    ua = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
          "AppleWebKit/605.1.15 CriOS/120.0.6099.119")
    assert truncate_user_agent(ua) == "CriOS/120"


def test_safari_macos():
    ua = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15")
    result = truncate_user_agent(ua)
    # Safari major version comes from "Safari/605" token (not "Version/17")
    assert result == "Safari/605"


def test_curl_unknown():
    assert truncate_user_agent("curl/7.81.0") == "unknown"


def test_custom_bot_unknown():
    assert truncate_user_agent("MyCustomBot/2.5") == "unknown"


def test_result_is_short():
    """Result must be drastically shorter than input — no PII leakage."""
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    result = truncate_user_agent(ua)
    assert len(result) <= 25
    assert "Windows" not in result
    assert "WebKit" not in result
