"""Konto-Zurechnung fuer KI-Kosten: explizite user_id schlaegt Kontext, Kontext schlaegt nichts.

Ausgeloest durch den Fund vom 08.09.2026: website_monitor und scan_arbeiter
riefen budget_frei/kosten_buchen ohne user_id auf, obwohl der Auftrag einen
Besitzer hatte - die Kosten landeten deshalb im Anonym-Topf statt beim
zahlenden Konto. konto_setzen() traegt das Konto stattdessen ueber eine
ContextVar durch den Aufrufpfad.
"""
from compliance_engine import ai_budget


def test_ohne_kontext_bleibt_konto_leer():
    assert ai_budget._konto_aufloesen(None, "free") == (None, "free")


def test_explizite_user_id_gewinnt_ohne_kontext():
    assert ai_budget._konto_aufloesen("42", "pro") == ("42", "pro")


def test_kontext_greift_wenn_keine_user_id_uebergeben_wird():
    with ai_budget.konto_setzen("99", "agency"):
        assert ai_budget._konto_aufloesen(None, "free") == ("99", "agency")


def test_explizite_user_id_schlaegt_kontext():
    with ai_budget.konto_setzen("99", "agency"):
        assert ai_budget._konto_aufloesen("7", "single") == ("7", "single")


def test_kontext_wird_nach_dem_block_wieder_zurueckgesetzt():
    with ai_budget.konto_setzen("99", "agency"):
        pass
    assert ai_budget._konto_aufloesen(None, "free") == (None, "free")


def test_verschachtelte_kontexte_stoeren_sich_nicht():
    with ai_budget.konto_setzen("1", "single"):
        with ai_budget.konto_setzen("2", "agency"):
            assert ai_budget._konto_aufloesen(None, "free") == ("2", "agency")
        assert ai_budget._konto_aufloesen(None, "free") == ("1", "single")
    assert ai_budget._konto_aufloesen(None, "free") == (None, "free")


def test_kein_plan_type_faellt_auf_free_zurueck():
    with ai_budget.konto_setzen("5", None):
        assert ai_budget._konto_aufloesen(None, "free") == ("5", "free")
