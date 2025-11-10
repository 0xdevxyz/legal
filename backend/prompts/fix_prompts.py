"""
AI Prompt Templates für personalisierte Compliance-Fixes
Generiert kinderleichte Anleitungen basierend auf echter Website-Struktur
"""

IMPRESSUM_FIX_PROMPT = """
Du bist ein deutscher Compliance-Experte. Analysiere diese Website und erstelle eine kinderleichte Schritt-für-Schritt-Anleitung zur Behebung von Impressums-Problemen.

WEBSITE-STRUKTUR:
{website_structure}

FIRMENDATEN:
{company_data}

PROBLEM:
{issue_description}

DEINE AUFGABE:
Erstelle eine so einfache Anleitung, dass ein Kind sie verstehen könnte. Verwende:
- Kurze, klare Sätze (maximal 15 Wörter)
- Nummerierte Schritte (maximal 7 Schritte)
- Konkrete Anweisungen ohne Fachchinesisch
- Visuelle Beschreibungen ("Klicke auf den blauen Button oben rechts")

ERSTELLE:
1. Schritte: Nummerierte Liste von Aktionen in SEHR EINFACHER Sprache
2. Code: Fertiger HTML/JS Code zum Copy-Paste
3. Platzierung: Genau wo der Code eingefügt werden muss
4. Test: Wie man prüft ob es funktioniert (in 1-2 Sätzen)
5. Troubleshooting: Was schiefgehen könnte + einfache Lösung

WICHTIG:
- Berücksichtige das erkannte CMS: {cms_type}
- Passe die Anleitung an die vorhandene Struktur an
- Verwende die erkannte Technologie: {technology_stack}
- Gebe CMS-spezifische Hinweise (WordPress-Admin, Shopify-Theme-Editor, etc.)

TRANSPARENCY:
Erkläre dem User kurz und verständlich:
- WARUM Complyo nicht automatisch in die Website eingreift
- WIE dies die Sicherheit & Kontrolle gewährleistet
- WAS die Vorteile der manuellen Umsetzung sind

AUSGABEFORMAT (JSON):
{{
  "steps": [
    {{"number": 1, "title": "Kurztitel", "description": "Sehr einfache Beschreibung", "visual_hint": "Wo klicken/tippen"}},
    ...
  ],
  "code": "Fertiger Code",
  "placement": "Genau wo einfügen (z.B. 'Vor dem </footer>-Tag' oder 'WordPress: Design → Customizer → Footer')",
  "test_instructions": ["Schritt 1 zum Testen", "Schritt 2 zum Testen"],
  "troubleshooting": [
    {{"problem": "Was könnte schiefgehen", "solution": "Einfache Lösung"}},
    ...
  ],
  "transparency_note": "Kurze Erklärung warum manuelle Umsetzung besser ist (2-3 Sätze)",
  "estimated_time": "5-10 Minuten",
  "difficulty": "Einfach"
}}

ANTWORTE NUR MIT DEM JSON, KEIN ZUSÄTZLICHER TEXT.
"""

DATENSCHUTZ_FIX_PROMPT = """
Du bist ein deutscher DSGVO-Experte. Erstelle eine kinderleichte Anleitung zur Behebung von Datenschutz-Problemen.

WEBSITE-STRUKTUR:
{website_structure}

ERKANNTE TRACKING-DIENSTE:
{tracking_services}

FIRMENDATEN:
{company_data}

PROBLEM:
{issue_description}

DEINE AUFGABE:
Erstelle eine Datenschutzerklärung, die:
- Alle erkannten Dienste abdeckt (Google Analytics, Facebook Pixel, etc.)
- Rechtlich korrekt ist (DSGVO Art. 13-14)
- Für den User einfach zu implementieren ist

ERSTELLE:
1. Personalisierte Datenschutzerklärung (vollständiger HTML-Text)
2. Schritt-für-Schritt Anleitung zum Einfügen
3. Checkl ist für fehlende Dienste
4. Hinweise zur Aktualisierung

WICHTIG:
- CMS: {cms_type}
- Erkannte Dienste: {detected_services}
- Sprache: Deutsch, verständlich für Laien

TRANSPARENCY:
Erkläre dem User:
- Warum Complyo keine automatischen Änderungen vornimmt
- Wie dies Sicherheit & rechtliche Kontrolle garantiert
- Dass Sie volle Transparenz über jeden Schritt haben

AUSGABEFORMAT (JSON):
{{
  "steps": [...],
  "code": "Vollständiger Datenschutztext als HTML",
  "placement": "Wo einfügen",
  "test_instructions": [...],
  "troubleshooting": [...],
  "missing_services_checklist": ["Dienst 1", "Dienst 2"],
  "update_hints": "Wann aktualisieren",
  "transparency_note": "Kurze Erklärung zu manueller Umsetzung (2-3 Sätze)",
  "estimated_time": "10-15 Minuten",
  "difficulty": "Mittel"
}}

ANTWORTE NUR MIT DEM JSON, KEIN ZUSÄTZLICHER TEXT.
"""

COOKIE_BANNER_FIX_PROMPT = """
Du bist ein Cookie-Consent-Experte. Erstelle eine kinderleichte Anleitung für einen DSGVO/TTDSG-konformen Cookie-Banner.

WEBSITE-STRUKTUR:
{website_structure}

ERKANNTE COOKIES/TRACKING:
{cookie_info}

PROBLEM:
{issue_description}

DEINE AUFGABE:
Implementiere einen rechtskonformen Cookie-Banner, der:
- Vor dem Setzen von Cookies die Einwilligung einholt (§25 TTDSG)
- Opt-in für nicht-essenzielle Cookies bietet
- Einfach zu verstehen ist

ERSTELLE:
1. Fertigen Cookie-Banner Code (HTML + JavaScript)
2. Anleitung zur Integration
3. Test-Schritte zur Prüfung der Funktionalität
4. Hinweise zur Cookie-Dokumentation

WICHTIG:
- CMS: {cms_type}
- Erkannte Tracking-Dienste: {tracking_services}
- Banner muss VOR dem Setzen von Cookies erscheinen
- Opt-out-Möglichkeit erforderlich

TRANSPARENCY:
Erkläre dem User:
- Warum keine automatischen Code-Änderungen
- Wie dies die Website-Integrität schützt
- Dass manuelle Umsetzung mehr Kontrolle bietet

AUSGABEFORMAT (JSON):
{{
  "steps": [...],
  "code": "Cookie-Banner HTML + JavaScript",
  "placement": "Wo einfügen (z.B. vor </body>)",
  "test_instructions": [
    "Öffne Browser-DevTools → Application → Cookies",
    "Prüfe: Keine Tracking-Cookies vor Zustimmung",
    "Klicke 'Akzeptieren' → Cookies werden gesetzt",
    "Klicke 'Ablehnen' → Keine Tracking-Cookies"
  ],
  "troubleshooting": [...],
  "cookie_documentation": "Was in Datenschutzerklärung ergänzen",
  "transparency_note": "Kurze Erklärung zu manueller Umsetzung (2-3 Sätze)",
  "estimated_time": "15-20 Minuten",
  "difficulty": "Mittel"
}}

ANTWORTE NUR MIT DEM JSON, KEIN ZUSÄTZLICHER TEXT.
"""

BARRIEREFREIHEIT_FIX_PROMPT = """
Du bist ein Barrierefreiheits-Experte (BFSG). Erstelle eine kinderleichte Anleitung zur Behebung von Barrierefreiheits-Problemen.

WEBSITE-STRUKTUR:
{website_structure}

BARRIEREFREIHEITS-STATUS:
{accessibility_info}

PROBLEM:
{issue_description}

DEINE AUFGABE:
Behebe Barrierefreiheits-Probleme gemäß BFSG (Barrierefreiheitsstärkungsgesetz):
- Alt-Texte für Bilder
- Tastatur-Navigation
- Kontraste
- Semantisches HTML
- ARIA-Labels

ERSTELLE:
1. Code-Fixes für die erkannten Probleme
2. Schritt-für-Schritt Anleitung
3. Test-Anweisungen
4. Langfristige Best Practices

WICHTIG:
- CMS: {cms_type}
- Aktueller Alt-Text Coverage: {alt_text_coverage}%
- Fehlende Alt-Texte: {images_without_alt}
- Heading-Struktur: {heading_structure}

TRANSPARENCY:
Erkläre dem User:
- Warum Complyo nicht direkt im Code eingreift
- Wie dies Sicherheit & Nachvollziehbarkeit sicherstellt
- Dass Sie jede Änderung verstehen & kontrollieren

AUSGABEFORMAT (JSON):
{{
  "steps": [...],
  "code": "HTML/CSS Code für Fixes",
  "placement": "Wo einfügen",
  "test_instructions": [
    "Teste mit Tab-Taste: Alle Elemente erreichbar?",
    "Teste mit Screen-Reader (NVDA/JAWS)",
    "Prüfe Kontraste mit WebAIM Contrast Checker"
  ],
  "troubleshooting": [...],
  "best_practices": "Zukünftig beachten",
  "transparency_note": "Kurze Erklärung zu manueller Umsetzung (2-3 Sätze)",
  "estimated_time": "20-30 Minuten",
  "difficulty": "Mittel bis Schwer"
}}

ANTWORTE NUR MIT DEM JSON, KEIN ZUSÄTZLICHER TEXT.
"""

AGB_FIX_PROMPT = """
Du bist ein E-Commerce-Rechtsexperte. Erstelle eine kinderleichte Anleitung für rechtskonforme AGB.

WEBSITE-STRUKTUR:
{website_structure}

FIRMENDATEN:
{company_data}

GESCHÄFTSMODELL:
{business_type}

PROBLEM:
{issue_description}

DEINE AUFGABE:
Erstelle AGB, die:
- Rechtlich korrekt sind (BGB, insb. §§ 305ff)
- Keine unzulässigen Klauseln enthalten
- Für das Geschäftsmodell passend sind

ERSTELLE:
1. Personalisierte AGB (vollständiger Text)
2. Anleitung zum Einfügen
3. Hinweise zu individuellen Anpassungen
4. Verknüpfung mit Checkout/Bestellprozess

WICHTIG:
- CMS: {cms_type}
- Geschäftsmodell: {business_type}
- Sprache: Deutsch, juristisch korrekt aber verständlich

TRANSPARENCY:
Erkläre dem User:
- Warum Complyo nicht automatisch AGB einfügt
- Wie dies rechtliche Kontrolle & Anpassbarkeit sicherstellt
- Dass manuelle Prüfung empfohlen ist

AUSGABEFORMAT (JSON):
{{
  "steps": [...],
  "code": "Vollständige AGB als HTML",
  "placement": "Wo einfügen + Verknüpfung im Checkout",
  "test_instructions": [...],
  "troubleshooting": [...],
  "customization_hints": "Was individuell anpassen",
  "checkout_integration": "Wie im Bestellprozess einbinden",
  "transparency_note": "Kurze Erklärung zu manueller Umsetzung (2-3 Sätze)",
  "estimated_time": "15-20 Minuten",
  "difficulty": "Mittel"
}}

ANTWORTE NUR MIT DEM JSON, KEIN ZUSÄTZLICHER TEXT.
"""

WIDERRUFSBELEHRUNG_FIX_PROMPT = """
Du bist ein E-Commerce-Rechtsexperte. Erstelle eine kinderleichte Anleitung für eine Widerrufsbelehrung.

WEBSITE-STRUKTUR:
{website_structure}

FIRMENDATEN:
{company_data}

PROBLEM:
{issue_description}

DEINE AUFGABE:
Erstelle eine Widerrufsbelehrung gemäß BGB §§ 355, 356:
- 14-tägiges Widerrufsrecht
- Widerrufsformular
- Rücksendekosten-Hinweis

ERSTELLE:
1. Widerrufsbelehrung (vollständiger Text)
2. Widerrufsformular (Muster)
3. Anleitung zur Integration
4. Hinweise zur E-Mail-Bereitstellung

WICHTIG:
- CMS: {cms_type}
- Sprache: Deutsch, juristisch korrekt

TRANSPARENCY:
Erkläre dem User:
- Warum keine automatische Integration
- Wie dies rechtliche Sicherheit gewährleistet
- Dass Sie volle Kontrolle über den Text haben

AUSGABEFORMAT (JSON):
{{
  "steps": [...],
  "code": "Widerrufsbelehrung + Formular als HTML",
  "placement": "Wo einfügen (Footer + Bestellbestätigung)",
  "test_instructions": [...],
  "troubleshooting": [...],
  "email_template": "Vorlage für Bestellbestätigung",
  "transparency_note": "Kurze Erklärung zu manueller Umsetzung (2-3 Sätze)",
  "estimated_time": "10-15 Minuten",
  "difficulty": "Einfach bis Mittel"
}}

ANTWORTE NUR MIT DEM JSON, KEIN ZUSÄTZLICHER TEXT.
"""

# Mapping: Kategorie → Prompt Template
PROMPT_TEMPLATES = {
    'impressum': IMPRESSUM_FIX_PROMPT,
    'datenschutz': DATENSCHUTZ_FIX_PROMPT,
    'cookies': COOKIE_BANNER_FIX_PROMPT,
    'cookie-banner': COOKIE_BANNER_FIX_PROMPT,
    'barrierefreiheit': BARRIEREFREIHEIT_FIX_PROMPT,
    'accessibility': BARRIEREFREIHEIT_FIX_PROMPT,
    'agb': AGB_FIX_PROMPT,
    'widerrufsbelehrung': WIDERRUFSBELEHRUNG_FIX_PROMPT,
    'widerruf': WIDERRUFSBELEHRUNG_FIX_PROMPT,
}

def get_prompt_for_category(category: str) -> str:
    """
    Gibt das passende Prompt-Template für eine Kategorie zurück
    
    Args:
        category: Issue-Kategorie (z.B. 'impressum', 'datenschutz')
        
    Returns:
        Prompt-Template als String
    """
    category_lower = category.lower()
    
    # Exaktes Match
    if category_lower in PROMPT_TEMPLATES:
        return PROMPT_TEMPLATES[category_lower]
    
    # Fuzzy Match für Variationen
    for key in PROMPT_TEMPLATES:
        if key in category_lower or category_lower in key:
            return PROMPT_TEMPLATES[key]
    
    # Fallback: Impressum-Template als Standard
    return IMPRESSUM_FIX_PROMPT

