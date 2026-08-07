"""
Test: Der Post-Scan-Alt-Text-Pfad nutzt echte Vision (AIAltTextGenerator)
und faellt nur bei Nicht-Verfuegbarkeit auf die Kontext-Heuristik zurueck.
Regression gegen den frueheren Zustand (nur Dateiname-Raten, TODO-Kommentar).
"""

import pytest
import compliance_engine.ai_alt_text_generator as altgen
from accessibility_post_scan_processor import AccessibilityPostScanProcessor


@pytest.mark.asyncio
async def test_alt_text_uses_claude_vision(monkeypatch):
    async def fake(self, image_url, context="", language="de"):
        return {"alt_text": "Rote Katze auf blauem Sofa", "confidence": 0.95, "source": "claude_vision"}

    monkeypatch.setattr(altgen.AIAltTextGenerator, "generate_alt_text", fake)
    proc = AccessibilityPostScanProcessor(db_pool=None)
    issues = [{"image_src": "https://example.com/cat.jpg", "page_url": "https://example.com/"}]

    fixes = await proc._generate_alt_text_fixes(issues, "https://example.com/")

    assert len(fixes) == 1
    assert fixes[0]["alt_text_source"] == "claude_vision"
    assert fixes[0]["suggested_alt"] == "Rote Katze auf blauem Sofa"
    assert fixes[0]["confidence"] == 0.95


@pytest.mark.asyncio
async def test_alt_text_falls_back_when_vision_unavailable(monkeypatch):
    async def fake(self, image_url, context="", language="de"):
        return {"alt_text": "Bild", "confidence": 0.2, "source": "fallback"}

    monkeypatch.setattr(altgen.AIAltTextGenerator, "generate_alt_text", fake)
    proc = AccessibilityPostScanProcessor(db_pool=None)
    issues = [{"image_src": "https://example.com/logo-firma.png", "page_url": "https://example.com/"}]

    fixes = await proc._generate_alt_text_fixes(issues, "https://example.com/")

    assert fixes[0]["alt_text_source"] == "heuristic"
    assert fixes[0]["suggested_alt"]  # nicht leer
    # Die Heuristik erkennt 'logo' im Dateinamen
    assert "Logo" in fixes[0]["suggested_alt"]


@pytest.mark.asyncio
async def test_befund_ohne_bildadresse_erzeugt_keinen_vorschlag(monkeypatch):
    """
    Frueher entstand hier ein Heuristik-Vorschlag fuer einen erfundenen
    Dateinamen (`/image-{idx}.jpg`). Die Vision bekam einen 404, die Heuristik
    machte "Bild: Image 20" daraus, und der Text landete als freigebbarer
    Vorschlag in der Worklist — bei spedition-mahn.de 5 von 14.

    Neue Zusage: ohne ermittelbare Bildadresse gibt es keinen Vorschlag. Kein
    Vorschlag ist besser als einer fuer ein Bild, das nicht existiert.
    """
    calls = {"n": 0}

    async def fake(self, image_url, context="", language="de"):
        calls["n"] += 1
        return {"alt_text": "x", "confidence": 0.9, "source": "claude_vision"}

    monkeypatch.setattr(altgen.AIAltTextGenerator, "generate_alt_text", fake)
    proc = AccessibilityPostScanProcessor(db_pool=None)
    issues = [{"image_src": "", "page_url": ""}]

    fixes = await proc._generate_alt_text_fixes(issues, "")

    assert calls["n"] == 0     # Vision gar nicht erst gefragt
    assert fixes == []         # und nichts erfunden


@pytest.mark.asyncio
async def test_adresse_aus_dem_markup_rettet_den_befund(monkeypatch):
    """
    axe liefert das Markup in `element_html` — auch wenn `image_src` fehlt,
    steht die Adresse dort. Genau diese Befunde gingen frueher verloren und
    kamen als Phantom zurueck.
    """
    calls = {"n": 0}

    async def fake(self, image_url, context="", language="de"):
        calls["n"] += 1
        return {"alt_text": "Gelber Sattelzug", "confidence": 0.9,
                "source": "claude_vision"}

    monkeypatch.setattr(altgen.AIAltTextGenerator, "generate_alt_text", fake)
    proc = AccessibilityPostScanProcessor(db_pool=None)
    issues = [{"element_html": '<img src="/uploads/lkw.jpg" class="hero">',
               "page_url": "https://kunde.de/"}]

    fixes = await proc._generate_alt_text_fixes(issues, "https://kunde.de/")

    assert calls["n"] == 1
    assert fixes[0]["image_filename"] == "lkw.jpg"
    assert fixes[0]["suggested_alt"] == "Gelber Sattelzug"
