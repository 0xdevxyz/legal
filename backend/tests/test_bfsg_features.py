"""
Test Suite für BFSG Features
Testet alle neuen Barrierefreiheits-Features

Features:
1. Feature-Engine (Issue-zu-Feature-Mapping)
2. Patch-Service (LLM-Prompts)
3. axe-core Scanner
4. Media Accessibility Check
5. Git Integration
"""

import asyncio
import pytest
from datetime import datetime


# =============================================================================
# Test: Feature-Engine
# =============================================================================

def test_feature_engine_categorization():
    """Test: Feature-Engine kategorisiert Issues korrekt"""
    from compliance_engine.feature_engine import feature_engine, FeatureId, Difficulty
    
    # Test-Issue: Alt-Text fehlt
    alt_text_issue = {
        "id": "test_1",
        "title": "Bild ohne Alt-Text",
        "description": "Ein Bild hat keinen alternativen Text",
        "category": "barrierefreiheit",
        "severity": "warning"
    }
    
    result = feature_engine.categorize_issue(alt_text_issue)
    
    assert result.feature_id == FeatureId.ALT_TEXT
    assert result.difficulty == Difficulty.EASY
    assert "1.1.1" in str(result.wcag_criteria)
    print(f"✅ Alt-Text Issue korrekt kategorisiert: {result.feature_id.value}")


def test_feature_engine_summary():
    """Test: Feature-Engine erstellt korrekte Zusammenfassung"""
    from compliance_engine.feature_engine import feature_engine
    
    test_issues = [
        {"title": "Bild ohne Alt-Text", "severity": "warning"},
        {"title": "Kontrast zu niedrig", "severity": "error"},
        {"title": "Formular ohne Label", "severity": "warning"},
    ]
    
    structured = feature_engine.categorize_issues(test_issues)
    summary = feature_engine.get_summary(structured)
    
    assert summary["total_issues"] == 3
    assert "by_difficulty" in summary
    assert "recommendation" in summary
    print(f"✅ Summary erstellt: {summary['total_issues']} Issues, Empfehlung: {summary['recommendation'][:50]}...")


# =============================================================================
# Test: Patch-Service Prompts
# =============================================================================

def test_bfsg_prompts():
    """Test: BFSG-Prompts werden korrekt generiert"""
    from compliance_engine.prompts.bfsg_prompts import (
        bfsg_prompt_builder, PromptTemplate, PromptContext
    )
    
    context = PromptContext(
        file_path="src/components/ProductCard.tsx",
        file_content="<img src='product.jpg' />",
        findings=[{
            "line": 23,
            "selector": "img.product-image",
            "description": "Bild hat keinen Alt-Text"
        }]
    )
    
    prompt = bfsg_prompt_builder.build_prompt(PromptTemplate.ALT_TEXT, context)
    
    assert "WCAG 1.1.1" in prompt
    assert "Unified Diff" in prompt
    assert "ProductCard.tsx" in prompt
    print(f"✅ ALT_TEXT Prompt generiert ({len(prompt)} Zeichen)")


# =============================================================================
# Test: Media Accessibility Check
# =============================================================================

@pytest.mark.asyncio
async def test_media_accessibility_check():
    """Test: Media-Check findet Videos ohne Untertitel"""
    from compliance_engine.checks.media_accessibility_check import check_media_accessibility
    
    test_html = """
    <html>
    <body>
        <video src="video.mp4" controls></video>
        <audio src="podcast.mp3" autoplay></audio>
        <iframe src="https://www.youtube.com/embed/abc123"></iframe>
    </body>
    </html>
    """
    
    issues = await check_media_accessibility("https://example.com", test_html)
    
    # Sollte mehrere Issues finden
    assert len(issues) > 0
    
    # Prüfe Issue-Typen
    issue_titles = [i["title"] for i in issues]
    print(f"✅ Media-Check gefunden: {issue_titles}")
    
    # Video ohne Untertitel sollte gefunden werden
    assert any("Untertitel" in title for title in issue_titles)


# =============================================================================
# Test: axe-core Scanner (Mock)
# =============================================================================

def test_axe_rule_mapping():
    """Test: axe-core Rules werden korrekt gemappt"""
    from compliance_engine.axe_scanner import AXE_RULE_TO_FEATURE, AXE_TAG_TO_WCAG
    
    # Prüfe wichtige Mappings
    assert AXE_RULE_TO_FEATURE.get("image-alt") == "ALT_TEXT"
    assert AXE_RULE_TO_FEATURE.get("color-contrast") == "CONTRAST"
    assert AXE_RULE_TO_FEATURE.get("label") == "FORM_LABELS"
    
    # Prüfe WCAG-Mappings
    assert AXE_TAG_TO_WCAG.get("wcag111") == "1.1.1"
    assert AXE_TAG_TO_WCAG.get("wcag143") == "1.4.3"
    
    print(f"✅ axe-core Mappings korrekt ({len(AXE_RULE_TO_FEATURE)} Rules, {len(AXE_TAG_TO_WCAG)} WCAG Tags)")


# =============================================================================
# Test: Git Service
# =============================================================================

def test_git_service_pr_content():
    """Test: Git-Service generiert korrekten PR-Content"""
    from git_service import git_service
    
    test_patches = [
        {
            "feature_id": "ALT_TEXT",
            "description": "Alt-Text für Produktbild hinzugefügt",
            "wcag_criteria": ["1.1.1"]
        },
        {
            "feature_id": "CONTRAST",
            "description": "Kontrast für Buttons verbessert",
            "wcag_criteria": ["1.4.3"]
        }
    ]
    
    title, body = git_service._generate_pr_content(
        test_patches,
        ["ALT_TEXT", "CONTRAST"],
        ["src/ProductCard.tsx", "src/Button.tsx"]
    )
    
    assert "Barrierefreiheit" in title
    assert "WCAG" in body
    assert "BFSG" in body
    print(f"✅ PR Content generiert: '{title}'")


# =============================================================================
# Test: Enhanced Check Integration
# =============================================================================

@pytest.mark.asyncio
async def test_enhanced_check():
    """Test: Enhanced Check kombiniert alle Checker"""
    from compliance_engine.checks.barrierefreiheit_check import check_barrierefreiheit_enhanced
    
    test_url = "https://example.com"
    test_html = """
    <html>
    <body>
        <img src="test.jpg">
        <video src="video.mp4"></video>
        <button></button>
    </body>
    </html>
    """
    
    # Ohne axe-core (da Playwright evtl. nicht installiert)
    issues = await check_barrierefreiheit_enhanced(
        test_url,
        html=test_html,
        use_axe_core=False,
        check_media=True
    )
    
    assert len(issues) > 0
    print(f"✅ Enhanced Check: {len(issues)} Issues gefunden")


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 BFSG Feature Tests")
    print("=" * 60)
    
    # Synchrone Tests
    test_feature_engine_categorization()
    test_feature_engine_summary()
    test_bfsg_prompts()
    test_axe_rule_mapping()
    test_git_service_pr_content()
    
    # Async Tests
    print("\n📡 Async Tests...")
    asyncio.run(test_media_accessibility_check())
    asyncio.run(test_enhanced_check())
    
    print("\n" + "=" * 60)
    print("✅ Alle Tests bestanden!")
    print("=" * 60)
