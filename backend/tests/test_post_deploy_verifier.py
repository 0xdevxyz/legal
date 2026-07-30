"""Tests fuer die reine Post-Deploy-Verifikationslogik."""

from post_deploy_verifier import verify_fix, _extract_markers, _imgs_without_alt


def test_alt_fix_verified_when_present_and_clean():
    fix = '<img src="a.jpg" alt="Ein Hund im Park">'
    html = '<html><body><img src="a.jpg" alt="Ein Hund im Park"></body></html>'
    res = verify_fix(html, "barrierefreiheit", fix)
    assert res["verified"] is True
    assert res["deploy_present"] is True
    assert res["category_clean"] is True


def test_alt_fix_not_verified_when_other_img_still_missing_alt():
    fix = '<img src="a.jpg" alt="Ein Hund im Park">'
    # Fix ist da, aber ein anderes Bild hat weiterhin kein alt -> Kategorie nicht sauber
    html = '<img src="a.jpg" alt="Ein Hund im Park"><img src="b.jpg">'
    res = verify_fix(html, "barrierefreiheit", fix)
    assert res["deploy_present"] is True
    assert res["category_clean"] is False
    assert res["verified"] is False


def test_not_verified_when_fix_not_on_live_page():
    fix = '<img src="a.jpg" alt="Ein Hund im Park">'
    html = '<html><body><p>nichts</p></body></html>'
    res = verify_fix(html, "barrierefreiheit", fix)
    assert res["deploy_present"] is False
    assert res["verified"] is False


def test_unknown_category_does_not_block_when_deploy_present():
    fix = '<div aria-label="Sprachumschalter">DE/EN</div>'
    html = '<div aria-label="Sprachumschalter">DE/EN</div>'
    res = verify_fix(html, "irgendeine-unbekannte-kategorie", fix)
    # category_clean None darf die Verifikation nicht scheitern lassen
    assert res["category_clean"] is None
    assert res["deploy_present"] is True
    assert res["verified"] is True


def test_impressum_category():
    fix = '<a href="/impressum">Impressum</a>'
    html = '<footer><a href="/impressum">Impressum</a></footer>'
    res = verify_fix(html, "rechtstexte-impressum", fix)
    assert res["verified"] is True


def test_extract_markers_prefers_semantic():
    markers = _extract_markers('<img src="x.jpg" alt="Rote Katze" type="image">')
    assert "Rote Katze" in markers


def test_imgs_without_alt_counter():
    assert _imgs_without_alt('<img src="a"><img src="b" alt="x">') == 1
