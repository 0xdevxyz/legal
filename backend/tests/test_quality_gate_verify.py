"""
Tests fuer das gehaertete Quality-Gate:
- echtes In-place-Apply (Attribut-Merge) statt Anhaengen
- 'validated' nur bei echter Re-Scan-Verifikation
- kein Silent-Pass mehr, wenn original_html fehlt
"""

import pytest
from ai_fix_engine.fix_quality_gate import FixQualityGate

ALT_FIX = {"fix_code": '<img src="a.jpg" alt="Ein Hund spielt im Park">'}


def test_apply_fix_in_place_merges_attribute():
    g = FixQualityGate()
    patched, applied = g._apply_fix_to_html(ALT_FIX, '<img src="a.jpg">')
    assert applied is True
    assert 'alt="Ein Hund spielt im Park"' in patched
    # kein Append-Marker
    assert "fix applied" not in patched


def test_apply_fix_appends_when_no_matching_target():
    g = FixQualityGate()
    patched, applied = g._apply_fix_to_html(ALT_FIX, '<img src="other.jpg">')
    assert applied is False
    assert "fix applied" in patched


@pytest.mark.asyncio
async def test_validated_requires_real_verification():
    g = FixQualityGate()
    res = await g.run(ALT_FIX, '<img src="a.jpg">')
    assert res.final_status == "validated"
    s2 = next(s for s in res.stage_results if s.stage == 2)
    assert s2.details.get("verified") is True
    assert s2.details.get("applied_in_place") is True


@pytest.mark.asyncio
async def test_missing_original_html_not_silently_validated():
    g = FixQualityGate()
    res = await g.run(ALT_FIX, "")
    assert res.final_status == "pending_review"
    s2 = next(s for s in res.stage_results if s.stage == 2)
    assert s2.details.get("verified") is False


@pytest.mark.asyncio
async def test_append_only_fix_goes_to_review():
    g = FixQualityGate()
    res = await g.run(ALT_FIX, '<img src="other.jpg">')
    assert res.final_status == "pending_review"
