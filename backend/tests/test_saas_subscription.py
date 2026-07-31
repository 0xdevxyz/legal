"""
Tests fuer die SaaS-/Abo-Luecke (Tier 3 C): Widerruf (§355 BGB) und
Kündigungsbutton (§312k BGB) muessen auch OHNE Warenkorb-Vokabular feuern.
"""

import pytest
from bs4 import BeautifulSoup

from compliance_engine.checks.shop_check import (
    detect_shop,
    detect_subscription,
    check_shop_compliance,
)
from legal_text_generator import validate_document_content, DocumentType


SAAS_PAGE = """
<html><body>
  <h1>Unser SaaS-Tool</h1>
  <p>Jetzt im Abonnement: 29 Euro pro Monat, monatlich kündbar.</p>
  <a href="/preise">Tarif wählen</a>
  <p>Registrieren und loslegen.</p>
</body></html>
"""

BROCHURE_PAGE = """
<html><body>
  <h1>Malermeister Muster</h1>
  <p>Wir streichen Ihre Wände. Rufen Sie uns an für ein Angebot.</p>
  <p>Referenzen und Leistungen im Überblick.</p>
</body></html>
"""


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def test_saas_page_is_subscription_not_shop():
    assert detect_shop(_soup(SAAS_PAGE)) is False
    assert detect_subscription(_soup(SAAS_PAGE)) is True


def test_brochure_page_is_neither():
    assert detect_shop(_soup(BROCHURE_PAGE)) is False
    assert detect_subscription(_soup(BROCHURE_PAGE)) is False


@pytest.mark.asyncio
async def test_saas_gets_widerruf_and_312k_checks():
    issues = await check_shop_compliance("https://saas.example.com", _soup(SAAS_PAGE))
    titles = [i["title"] for i in issues]
    # Widerrufsbelehrung fehlt -> Issue (SaaS-Seite hat keine)
    assert any("Widerruf" in t for t in titles)
    # Abo-Signal ohne Kuendigungsbutton -> §312k-Issue
    assert any("Kündigungsbutton" in t for t in titles)
    # AGB/PAngV sind shop-gebunden und duerfen bei reinem Abo NICHT feuern
    assert not any("AGB" in t for t in titles)
    assert not any("MwSt" in t or "Versand" in t for t in titles)


@pytest.mark.asyncio
async def test_brochure_gets_no_shop_issues():
    issues = await check_shop_compliance("https://maler.example.com", _soup(BROCHURE_PAGE))
    assert issues == []


# ---------------- Generator-Marker ----------------

def test_tos_marker_requires_kuendigung_and_preis():
    html = "<h1>AGB</h1><p>Geltungsbereich: alle Verträge über unsere Leistung.</p>"
    missing = validate_document_content(DocumentType.TOS, html)
    assert "Kündigung/Laufzeit" in missing
    assert "Preise/Vergütung" in missing


def test_tos_complete_passes():
    html = (
        "<h1>AGB</h1><p>Geltungsbereich: alle Verträge über unsere Leistung.</p>"
        "<p>Kündigung: monatlich, Laufzeit 1 Monat.</p><p>Preise: 29 Euro, Zahlung per Karte.</p>"
    )
    assert validate_document_content(DocumentType.TOS, html) == []


def test_imprint_marker_flags_missing_ustid_register():
    html = (
        "<h1>Impressum</h1><p>Muster GmbH, Musterweg 1, 04109 Leipzig</p>"
        "<p>Kontakt: info@muster.de, Telefon 0341-123</p><p>Verantwortlich: M. Muster</p>"
    )
    missing = validate_document_content(DocumentType.IMPRINT, html)
    assert "USt-IdNr" in missing
    assert "Registereintrag" in missing


def test_imprint_with_ustid_register_passes():
    html = (
        "<h1>Impressum</h1><p>Muster GmbH, Musterweg 1, 04109 Leipzig</p>"
        "<p>Kontakt: info@muster.de</p><p>Verantwortlich: M. Muster</p>"
        "<p>USt-ID: DE123456789</p><p>Handelsregister: Amtsgericht Leipzig, HRB 12345</p>"
    )
    assert validate_document_content(DocumentType.IMPRINT, html) == []
