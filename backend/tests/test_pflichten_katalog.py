"""Tests für den Pflichten-Katalog (Phase 7.2 Pflichtenradar)."""
from pflichten_katalog import evaluate_pflichten, PFLICHTEN, APPLIES, CHECK, NOT_INDICATED


def test_jede_regel_hat_pflichtfelder_und_haftungsdesign():
    for rule in PFLICHTEN:
        assert rule["id"] and rule["law"] and rule["legal_basis"]
        assert 0 < rule["confidence"] <= 1
        assert len(rule["risk_range"]) == 2 and rule["risk_range"][0] <= rule["risk_range"][1]


def test_jedes_ergebnis_traegt_evidence_und_why():
    r = evaluate_pflichten({"employees": "10-49", "revenue": "2-10m", "b2c": True, "online_shop": True})
    assert len(r["items"]) == len(PFLICHTEN)
    for item in r["items"]:
        assert item["status"] in (APPLIES, CHECK, NOT_INDICATED)
        assert item["evidence"], f"{item['id']} ohne evidence"
        assert item["why"], f"{item['id']} ohne Begründung"
    assert "keine Rechtsberatung" in r["disclaimer"]


def test_b2c_shop_loest_bfsg_und_widerruf_aus():
    r = evaluate_pflichten({"employees": "10-49", "revenue": "2-10m", "b2c": True, "online_shop": True})
    by_id = {i["id"]: i for i in r["items"]}
    assert by_id["bfsg"]["status"] == APPLIES
    assert by_id["widerruf_shop"]["status"] == APPLIES


def test_kleinstunternehmen_bfsg_wird_check_nicht_applies():
    r = evaluate_pflichten({"employees": "1-9", "revenue": "<=2m", "b2c": True, "digital_service": True})
    by_id = {i["id"]: i for i in r["items"]}
    assert by_id["bfsg"]["status"] == CHECK
    assert "Kleinstunternehmen" in by_id["bfsg"]["evidence"]


def test_ohne_ki_keine_ai_act_indizien():
    r = evaluate_pflichten({"employees": "1-9", "revenue": "<=2m"})
    by_id = {i["id"]: i for i in r["items"]}
    assert by_id["ai_act_transparenz"]["status"] == NOT_INDICATED
    assert by_id["ai_act_hochrisiko"]["status"] == NOT_INDICATED


def test_ki_entscheidungen_sind_nie_hartes_applies():
    # Hochrisiko-Einordnung ist einzelfallabhängig → höchstens CHECK (RDG-Design)
    r = evaluate_pflichten({"employees": "50-249", "revenue": "10-50m", "uses_ai_decisions": True})
    by_id = {i["id"]: i for i in r["items"]}
    assert by_id["ai_act_hochrisiko"]["status"] == CHECK


def test_nis2_grosses_unternehmen_im_sektor_check_mit_evidence():
    r = evaluate_pflichten({"employees": "250+", "revenue": ">50m", "critical_sector": True})
    by_id = {i["id"]: i for i in r["items"]}
    assert by_id["nis2"]["status"] == CHECK
    assert any("Sektor" in e for e in by_id["nis2"]["evidence"])


def test_sortierung_applies_zuerst():
    r = evaluate_pflichten({"employees": "10-49", "revenue": "2-10m", "b2c": True, "online_shop": True})
    seen_order = [i["status"] for i in r["items"]]
    first_check = seen_order.index(CHECK) if CHECK in seen_order else len(seen_order)
    assert all(s == APPLIES for s in seen_order[:first_check] if s == APPLIES)
    assert seen_order[0] == APPLIES


def test_kaputtes_profil_faellt_auf_check_zurueck():
    r = evaluate_pflichten({"employees": object()})  # unvergleichbarer Typ
    assert len(r["items"]) == len(PFLICHTEN)
    for item in r["items"]:
        assert item["status"] in (APPLIES, CHECK, NOT_INDICATED)
