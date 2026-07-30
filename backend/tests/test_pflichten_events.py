"""Tests für das Legal-Update→Pflichten-Mapping (Phase 7.3)."""
from pflichten_events import map_update_to_rules, RULE_KEYWORDS
from pflichten_katalog import PFLICHTEN


def test_alle_keyword_regeln_existieren_im_katalog():
    katalog_ids = {r["id"] for r in PFLICHTEN}
    assert set(RULE_KEYWORDS.keys()) <= katalog_ids


def test_ai_act_chatbot_meldung_trifft_transparenz():
    rules = map_update_to_rules(
        "EU AI Act: Kennzeichnungspflicht für KI-Chatbots auf Websites",
        "Neue Transparenzpflichten nach Art. 50", "high",
    )
    assert "ai_act_transparenz" in rules
    assert "bfsg" not in rules


def test_bfsg_meldung_trifft_bfsg():
    rules = map_update_to_rules(
        "BFSG-Marktüberwachung startet Prüfwelle", "WCAG-Konformität im Fokus", "bfsg",
    )
    assert rules == ["bfsg"]


def test_newsletter_meldung_trifft_uwg():
    rules = map_update_to_rules(
        "DSK-Beschluss: Verschärfte Anforderungen an Newsletter-Anmeldungen",
        "Double-Opt-in-Nachweis", "medium",
    )
    assert "uwg_newsletter" in rules


def test_update_type_hint_ergaenzt_ohne_keywords():
    rules = map_update_to_rules("Neues Urteil", "Ohne Schlagworte", "cookie_compliance")
    assert rules == ["ttdsg_cookie_consent"]


def test_irrelevante_meldung_leer():
    assert map_update_to_rules("Wetterbericht", "Sonnig", "info") == []
