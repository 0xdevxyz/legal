"""
Tests fuer das Qualitaets-Gate des deklarativen Check-Layers (Tier 3 E).

Fixtures stammen aus dem realen Prod-Altbestand (Audit 2026-07):
- google-fonts-lokal-hosting (id 71): invertierte Logik
- speicherfristen-datenschutzerklaerung: neutralisierte Detection
"""

import pytest

from compliance_engine.check_spec_rules import (
    detection_is_weak,
    detection_is_inverted,
    AUTO_CHECK_RISK_CAP,
)
from compliance_engine.check_generator import _validate_spec, _is_same_topic
from compliance_engine.declarative_check_runner import _issue_dict, _run_single_check
from bs4 import BeautifulSoup


def _base_spec(**overrides):
    spec = {
        "slug": "test-check",
        "category": "datenschutz",
        "title": "Testpflicht",
        "description": "d",
        "recommendation": "r",
        "legal_basis": "Art. 13 DSGVO",
        "severity": "warning",
        "risk_euro": 2000,
        "applies_when": {"always": True},
        "detection": {
            "type": "required_element",
            "html_patterns": [r"speicher(frist|dauer)"],
            "link_href_keywords": [],
            "link_text_keywords": [],
            "url_paths": [],
        },
    }
    spec.update(overrides)
    return spec


# Reale Prod-Spec (id 71) — invertierte Logik
GOOGLE_FONTS_DETECTION = {
    "type": "required_element",
    "url_paths": [],
    "html_patterns": [
        "@import\\s+url\\(['\"]?https?://fonts\\.googleapis\\.com",
        "href=['\"]https?://fonts\\.googleapis\\.com",
        "src=['\"]https?://fonts\\.gstatic\\.com",
    ],
    "link_href_keywords": ["fonts.googleapis.com", "fonts.gstatic.com"],
    "link_text_keywords": [],
}

# Reale neutralisierte Detection (z.B. speicherfristen-datenschutzerklaerung)
NEUTRALIZED_DETECTION = {
    "type": "required_element",
    "html_patterns": ["speicher(frist|dauer|zeitraum)"],
    "link_href_keywords": ["datenschutz", "privacy", "dsgvo"],
    "link_text_keywords": ["datenschutz", "datenschutzerklärung", "privacy"],
    "url_paths": ["/datenschutz", "/privacy"],
}


def test_inverted_google_fonts_spec_rejected():
    err = _validate_spec(_base_spec(detection=GOOGLE_FONTS_DETECTION))
    assert err is not None and "inverted" in err


def test_neutralized_spec_rejected():
    err = _validate_spec(_base_spec(detection=NEUTRALIZED_DETECTION))
    assert err is not None and "weak detection" in err


def test_neutralized_plus_content_requirements_passes():
    det = dict(NEUTRALIZED_DETECTION)
    det["content_requirements"] = {"Speicherdauer": "speicherdauer|aufbewahrung"}
    assert _validate_spec(_base_spec(detection=det)) is None


def test_specific_html_pattern_only_passes():
    assert _validate_spec(_base_spec()) is None


def test_risk_cap_rejected():
    err = _validate_spec(_base_spec(risk_euro=300000))
    assert err is not None and "Deckel" in err


def test_rules_directly():
    assert detection_is_inverted(GOOGLE_FONTS_DETECTION) is not None
    assert detection_is_weak(NEUTRALIZED_DETECTION) is True
    assert detection_is_weak({"type": "required_element", "html_patterns": ["x"],
                              "link_href_keywords": ["barrierefreiheitserklaerung-xyz-2026"]}) is False


# ---------------- Dedup-Regression (reale DSA-Zwillinge) ----------------

def _spec_like(slug, title, legal_basis="Art. 16 DSA"):
    return {"slug": slug, "title": title, "legal_basis": legal_basis}


@pytest.mark.parametrize("slug_a,slug_b", [
    ("dsa-meldemechanismus-rechtswidrige-inhalte", "dsa-meldewege-illegale-inhalte"),
    ("dsa-meldemechanismus-rechtswidrige-inhalte", "dsa-meldesystem-illegale-inhalte"),
    ("dsa-transparenzbericht-online-plattform", "dsa-transparenzbericht-hosting"),
])
def test_dsa_topic_twins_detected(slug_a, slug_b):
    a = _spec_like(slug_a, "Meldemechanismus für rechtswidrige Inhalte fehlt")
    b = _spec_like(slug_b, "Meldemechanismus für illegale Inhalte fehlt")
    assert _is_same_topic(a, b) is True


def test_different_norms_not_deduped():
    a = _spec_like("ai-act-kennzeichnung-ki-inhalte", "KI-Kennzeichnung fehlt", "Art. 50 AI Act")
    b = _spec_like("ai-act-kennzeichnung-hochrisiko", "KI-Kennzeichnung fehlt", "Art. 13 AI Act")
    assert _is_same_topic(a, b) is False


# ---------------- Runner-Haertung ----------------

def test_runner_risk_cap():
    check = {
        "id": 1, "slug": "x", "category": "cookie", "title": "t", "description": "d",
        "recommendation": "r", "legal_basis": "l",
    }
    issue = _issue_dict(check, title="t", description="d", severity="warning",
                        risk_euro=300000, is_missing=True)
    assert issue["risk_euro"] == AUTO_CHECK_RISK_CAP


@pytest.mark.asyncio
async def test_runner_skips_weak_check():
    check = {
        "id": 2, "slug": "neutralized", "category": "datenschutz", "title": "t",
        "description": "d", "recommendation": "r", "legal_basis": "l",
        "severity": "warning", "risk_euro": 2000,
        "detection": NEUTRALIZED_DETECTION,
    }
    soup = BeautifulSoup("<html><body><p>x</p></body></html>", "html.parser")
    issues = await _run_single_check(check, "https://example.com", soup, "<html>", None)
    assert issues == []


@pytest.mark.asyncio
async def test_runner_strong_check_still_fires():
    check = {
        "id": 3, "slug": "strong", "category": "datenschutz", "title": "Pflicht fehlt",
        "description": "d", "recommendation": "r", "legal_basis": "l",
        "severity": "warning", "risk_euro": 2000,
        "detection": {"type": "required_element",
                      "html_patterns": [r"barrierefreiheitserkl(ae|ä)rung"],
                      "link_href_keywords": [], "link_text_keywords": [], "url_paths": []},
    }
    soup = BeautifulSoup("<html><body><p>nichts</p></body></html>", "html.parser")
    issues = await _run_single_check(check, "https://example.com", soup,
                                     "<html><body><p>nichts</p></body></html>", None)
    assert len(issues) == 1 and issues[0]["is_missing"] is True


# ---------------- Kurze Gate-Keywords (Audit 2026-08) ----------------
# Realer Prod-Fall: Check #278 trug "ki"/"ai" als Gate-Keywords. Die
# Wortanfang-Regel des Runners machte daraus Treffer auf "Kindermobiliar" und
# "Kieferorthopaedie" — eine Ferienpark-Seite ohne jede KI bekam einen
# AI-Act-Befund ueber 15.000 EUR, eine Zahnarztseite 20.000 EUR.

from compliance_engine.check_spec_rules import (
    gate_keyword_too_short,
    MIN_GATE_KEYWORD_LEN,
)
from compliance_engine.declarative_check_runner import _keyword_trifft, _gate_passes

AI_ACT_278_GATE = {
    "keywords_any": ["ki", "ai", "chatbot", "assistent", "assistant", "bot",
                     "generiert", "generated", "deepfake", "synthetisch"]
}


def test_kurzes_gate_keyword_abgelehnt():
    err = _validate_spec(_base_spec(applies_when=AI_ACT_278_GATE))
    assert err is not None and "zu kurz" in err


def test_regel_findet_kurzes_keyword():
    assert gate_keyword_too_short(AI_ACT_278_GATE) == "ki"
    assert gate_keyword_too_short({"keywords_all": ["ai"]}) == "ai"
    assert gate_keyword_too_short({"keywords_any": ["chatbot", "ki-assistent"]}) is None
    assert gate_keyword_too_short({"always": True}) is None
    assert gate_keyword_too_short(None) is None


def test_langes_gate_keyword_bleibt_erlaubt():
    assert _validate_spec(_base_spec(applies_when={"keywords_any": ["chatbot"]})) is None
    # Drei Zeichen sind die Untergrenze, nicht darunter (ga4, gtag bleiben nutzbar)
    assert gate_keyword_too_short({"keywords_any": ["ga4"]}) is None
    assert MIN_GATE_KEYWORD_LEN == 3


@pytest.mark.parametrize("keyword,text,erwartet", [
    ("ki", "kinderbetreuung mit kindermobiliar", False),
    ("ki", "kieferorthopaedie und kiefergelenk", False),
    ("ki", "wir setzen ki fuer empfehlungen ein", True),
    ("ki", "unser ki-assistent hilft", True),
    ("bot", "die botschaft der stadt", False),
    ("bot", "unser bot antwortet", True),
    # Ab vier Zeichen bleibt der Wortanfang, damit Komposita treffen
    ("kuendigung", "kuendigungsbutton fehlt", True),
    ("shop", "shopsystem mit warenkorb", True),
    ("gruen", "gruenstrom tarif", True),
    ("gruen", "im hintergrund", False),
])
def test_keyword_trifft_wortgrenzen(keyword, text, erwartet):
    assert _keyword_trifft(keyword, text) is erwartet


def test_ferienpark_gate_faellt_nicht_mehr_auf_kinder():
    html = "<html><body><p>Zusaetzliche Ausstattung: Kindermobiliar, Babybett.</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    assert _gate_passes(AI_ACT_278_GATE, soup, html.lower()) is False
