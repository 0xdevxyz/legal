"""
Tests fuer das Vollstaendigkeits-Versprechen (Tier 4):
Jedes Scan-Ergebnis liefert manuelle Pruef-Anleitungen fuer die Kriterien,
die keine Automatik pruefen kann — und jede Anleitung ist substanziell.
"""

from compliance_engine.score_calculator import ScoreCalculator, MANUAL_CHECKS


def test_manual_checks_in_scan_result():
    result = ScoreCalculator.compute_with_status([])
    checks = result.get("manual_checks")
    assert checks and checks is MANUAL_CHECKS


def test_manual_checks_cover_key_gaps():
    ids = {c["id"] for c in MANUAL_CHECKS}
    # Die vier wichtigsten Automatik-Grenzen muessen angeleitet sein:
    assert "manual-keyboard" in ids       # Tastatur/Fokus (A11y)
    assert "manual-reject-test" in ids    # Consent-Klick-Test (Cookies)
    assert "manual-avv" in ids            # AVV (DSGVO, extern unsichtbar)
    assert "manual-branche" in ids        # Branchenpflichten (Impressum)


def test_every_manual_check_is_substantial():
    valid_pillars = set(ScoreCalculator.PILLAR_IDS)
    for c in MANUAL_CHECKS:
        assert c["pillar"] in valid_pillars, c["id"]
        assert len(c["title"]) >= 10, c["id"]
        # Anleitung muss echte Schritte enthalten, keine Floskel
        assert len(c["anleitung"]) >= 80, c["id"]
        assert "Prüf" in c["anleitung"] or "prüfen" in c["anleitung"].lower(), c["id"]
