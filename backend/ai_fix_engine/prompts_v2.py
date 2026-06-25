"""
Complyo AI Fix Engine - Prompt Management System v2.0

Strukturierte Prompts mit JSON-Schema-Validation für alle Fix-Typen.
Optimiert für Claude 3.5 Sonnet und GPT-4.

© 2025 Complyo.tech
"""

import json
from typing import Dict, Any, Optional
from enum import Enum


class FixType(Enum):
    """Typen von Fixes"""
    CODE = "code"
    TEXT = "text"
    WIDGET = "widget"
    GUIDE = "guide"


class AIModel(Enum):
    """Unterstützte AI-Modelle"""
    CLAUDE_SONNET = "moonshotai/kimi-k2.5"
    GPT4 = "moonshotai/kimi-k2.5"
    GPT4_TURBO = "moonshotai/kimi-k2.5"


# =============================================================================
# JSON-Schema-Definitionen für AI-Outputs
# =============================================================================

CODE_FIX_SCHEMA = {
    "type": "object",
    "required": ["fix_id", "title", "code", "language", "integration"],
    "properties": {
        "fix_id": {"type": "string"},
        "title": {"type": "string", "minLength": 5, "maxLength": 200},
        "description": {"type": "string"},
        "code": {"type": "string", "minLength": 10},
        "language": {
            "type": "string",
            "enum": ["html", "css", "javascript", "php", "python"]
        },
        "before_code": {"type": "string"},
        "after_code": {"type": "string"},
        "integration": {
            "type": "object",
            "required": ["instructions"],
            "properties": {
                "file": {"type": "string"},
                "line_number": {"type": ["integer", "null"]},
                "instructions": {"type": "string", "minLength": 10},
                "where": {"type": "string"}
            }
        },
        "explanation": {"type": "string"},
        "estimated_time": {"type": "string"},
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"]
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

TEXT_FIX_SCHEMA = {
    "type": "object",
    "required": ["fix_id", "title", "text_content", "text_type"],
    "properties": {
        "fix_id": {"type": "string"},
        "title": {"type": "string", "minLength": 5, "maxLength": 200},
        "description": {"type": "string"},
        "text_content": {"type": "string", "minLength": 50},
        "text_type": {
            "type": "string",
            "enum": ["impressum", "datenschutz", "agb", "widerruf", "disclaimer", "generic"]
        },
        "format": {
            "type": "string",
            "enum": ["html", "markdown", "plain"]
        },
        "placeholders": {
            "type": "array",
            "items": {"type": "string"}
        },
        "integration": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "instructions": {"type": "string"}
            }
        },
        "estimated_time": {"type": "string"},
        "legal_references": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

WIDGET_FIX_SCHEMA = {
    "type": "object",
    "required": ["fix_id", "title", "widget_type", "integration_code"],
    "properties": {
        "fix_id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "widget_type": {
            "type": "string",
            "enum": ["cookie-consent", "accessibility", "combined"]
        },
        "integration_code": {"type": "string"},
        "configuration": {"type": "object"},
        "preview_url": {"type": "string", "format": "uri"},
        "features": {
            "type": "array",
            "items": {"type": "string"}
        },
        "integration": {
            "type": "object",
            "properties": {
                "instructions": {"type": "string"},
                "where": {"type": "string"}
            }
        },
        "estimated_time": {"type": "string"}
    }
}

GUIDE_FIX_SCHEMA = {
    "type": "object",
    "required": ["fix_id", "title", "steps"],
    "properties": {
        "fix_id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "steps": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["step_number", "title", "description"],
                "properties": {
                    "step_number": {"type": "integer", "minimum": 1},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "code_example": {"type": "string"},
                    "screenshot_url": {"type": "string"},
                    "validation": {"type": "string"}
                }
            }
        },
        "difficulty": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced"]
        },
        "estimated_time": {"type": "string"},
        "resources": {
            "type": "object",
            "properties": {
                "documentation_links": {"type": "array", "items": {"type": "string"}},
                "video_tutorials": {"type": "array", "items": {"type": "string"}},
                "tools_needed": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
}


# =============================================================================
# Prompt Templates
# =============================================================================

class PromptBuilder:
    """Builder für strukturierte AI-Prompts"""
    
    def __init__(self):
        self.legal_keywords_dsgvo = [
            "Datenschutzerklärung", "personenbezogene Daten", "Betroffenenrechte",
            "Artikel 13 DSGVO", "Artikel 15 DSGVO", "Widerrufsrecht",
            "Einwilligung", "Verarbeitungszweck", "Rechtsgrundlage"
        ]
        
        self.legal_keywords_tmg = [
            "Impressum", "§ 5 TMG", "Angaben gemäß", "Verantwortlich",
            "Registergericht", "Umsatzsteuer-ID", "Vertretungsberechtigt"
        ]
        
        self.legal_keywords_ttdsg = [
            "Cookie", "Einwilligung", "Speicherung", "Tracking",
            "Endeinrichtung", "§ 25 TTDSG", "Consent"
        ]
    
    def build_code_fix_prompt(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        user_skill: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Prompt für Code-Fixes (HTML/CSS/JS)
        """
        issue_title = issue.get("title", "Problem")
        issue_description = issue.get("description", "")
        issue_category = issue.get("category", "general")
        recommendation = issue.get("recommendation", "")

        tech_stack = context.get("technology", {})
        cms = ", ".join(tech_stack.get("cms", [])) or "Unbekannt"
        frameworks = ", ".join(tech_stack.get("frameworks", [])) or "Keine"
        analytics = ", ".join(tech_stack.get("analytics", [])) or "Keine"

        tracking = context.get("tracking_services", [])
        tracking_text = ", ".join(tracking) if tracking else "Keine erkannt"

        all_issues = context.get("all_issues", [])
        other_issues = [i for i in all_issues if i.get("title") != issue_title]
        other_issues_text = "\n".join(
            f"  - [{i.get('severity','?').upper()}] {i.get('title','')}" for i in other_issues[:8]
        ) or "  - Keine weiteren"

        skill_instructions = {
            "beginner": "Der User ist kein Entwickler. Erkläre jeden Schritt in einfacher Sprache, vermeide Fachbegriffe ohne Erklärung, und beschreibe genau WO er klicken oder tippen muss.",
            "intermediate": "Der User kennt HTML/CSS-Grundlagen. Technische Begriffe sind ok, aber erkläre das Warum.",
            "advanced": "Konzise technische Anleitung für einen Entwickler. Keine Basics erklären."
        }

        prompt = f"""Du bist ein Experte für Web-Compliance und modernes Frontend-Development.

**WEBSITE:** {context.get("url", "N/A")}
**CMS / Framework:** {cms} / {frameworks}
**Analytics / Tracking auf der Website:** {analytics} | {tracking_text}
**User-Level:** {user_skill} — {skill_instructions.get(user_skill, "")}

**ZU BEHEBENES PROBLEM:**
- Titel: {issue_title}
- Kategorie: {issue_category}
- Beschreibung: {issue_description}
- Empfehlung des Scanners: {recommendation}

**WEITERE OFFENE ISSUES DIESER WEBSITE (zur Orientierung):**
{other_issues_text}

**DEINE AUFGABE:**
Generiere einen vollständigen, sofort einsetzbaren Code-Fix für das genannte Problem.
- Berücksichtige das erkannte CMS ({cms}): Gib CMS-spezifische Hinweise (WordPress → Appearance > Theme Editor, Shopify → Theme Code, etc.)
- Der Code muss produktionsreif und syntaktisch korrekt sein
- Kein Platzhalter-Code — echter, funktionierender Code
- Erkläre in `integration.instructions` präzise: welche Datei, welche Stelle, was genau einfügen

**OUTPUT-FORMAT (strikt JSON, kein Zusatztext):**

```json
{{
  "fix_id": "{issue.get('id', 'unknown')}",
  "title": "Prägnanter Titel des Fixes",
  "description": "Was wird gefixt, warum ist es wichtig",
  "code": "VOLLSTÄNDIGER, PRODUKTIONSREIFER CODE",
  "language": "html|css|javascript|php",
  "before_code": "Alter Code-Zustand (falls ersetzt)",
  "after_code": "Neuer Code-Zustand (für Diff-Ansicht)",
  "integration": {{
    "file": "Ziel-Datei (z.B. 'header.php' bei WordPress, 'theme.liquid' bei Shopify)",
    "line_number": null,
    "instructions": "1. Öffne ...\\n2. Suche nach ...\\n3. Füge direkt VOR/NACH ... ein",
    "where": "Kurze Ortsbeschreibung (z.B. 'vor dem schließenden </head>-Tag')"
  }},
  "explanation": "Technische Erklärung: was der Code macht und warum es das Problem behebt",
  "estimated_time": "5-10 Minuten",
  "priority": "medium|high|critical",
  "tags": ["html", "accessibility", "wcag"]
}}
```"""

        return {
            "prompt": prompt,
            "model": AIModel.CLAUDE_SONNET.value,
            "temperature": 0.2,
            "max_tokens": 3000,
            "schema": CODE_FIX_SCHEMA
        }
    
    def build_legal_text_prompt(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        text_type: str
    ) -> Dict[str, Any]:
        """
        Prompt für Rechtssichere Texte (Impressum, Datenschutz, etc.)
        """
        company = context.get("company", {})
        company_name = company.get("name") or "[FIRMENNAME]"
        address = company.get("address") or "[ADRESSE]"
        email = company.get("email") or "[EMAIL]"
        phone = company.get("phone") or "[TELEFON]"

        site_url = context.get("url", "N/A")
        cms = ", ".join(context.get("technology", {}).get("cms", [])) or "Unbekannt"

        cookies = context.get("detected_cookies", context.get("cookies", []))
        cookie_names = [c.get("name", c) if isinstance(c, dict) else str(c) for c in cookies[:15]]

        analytics = context.get("technology", {}).get("analytics", [])
        tracking = context.get("tracking_services", [])
        all_services = list(set(analytics + tracking))

        issue_description = issue.get("description", "")
        issue_title = issue.get("title", "")
        scanner_findings = issue.get("recommendation", "")

        text_type_lower = text_type.lower()

        if text_type_lower == "impressum":
            prompt = f"""Du bist ein Fachanwalt für IT-Recht, spezialisiert auf deutsches Digitale-Dienste-Gesetz (DDG).

**WEBSITE:** {site_url}
**CMS:** {cms}
**Erkanntes Problem:** {issue_title} — {issue_description}
**Scanner-Hinweis:** {scanner_findings}

**VORLIEGENDE FIRMENDATEN (aus Website-Scan):**
- Firmenname: {company_name}
- Adresse: {address}
- E-Mail: {email}
- Telefon: {phone}

**AUFGABE:**
Erstelle ein VOLLSTÄNDIGES, RECHTSSICHERES Impressum nach § 5 DDG (seit 14.05.2024 gilt das DDG, nicht mehr TMG).
Verwende die oben gefundenen echten Firmendaten direkt. Für fehlende Pflichtangaben: Platzhalter in [ECKIGEN KLAMMERN].

**PFLICHTANGABEN (§ 5 DDG):**
1. Name & vollständige Anschrift (kein Postfach)
2. Schnelle elektronische Kontaktmöglichkeit (E-Mail)
3. Telefon ODER weiteres elektronisches Kommunikationsmittel
4. Vertretungsberechtigte Person(en) bei juristischen Personen
5. Handelsregister + HRB-Nummer (falls GmbH/AG/UG)
6. Umsatzsteuer-ID oder Wirtschafts-ID (falls vorhanden)
7. Aufsichtsbehörde (bei erlaubnispflichtigen Tätigkeiten)

**OUTPUT-FORMAT (strikt JSON, kein Zusatztext):**

```json
{{
  "fix_id": "{issue.get('id', 'impressum_fix')}",
  "title": "Rechtssicheres Impressum nach § 5 DDG",
  "description": "Vollständiges Impressum mit allen Pflichtangaben gemäß § 5 DDG (2024)",
  "text_content": "VOLLSTÄNDIGER HTML-TEXT DES IMPRESSUMS — mit echten Firmendaten",
  "text_type": "impressum",
  "format": "html",
  "placeholders": ["Liste der noch zu ergänzenden Felder, z.B. [REGISTERGERICHT]"],
  "integration": {{
    "filename": "impressum.html",
    "instructions": "CMS-spezifische Schritt-für-Schritt-Anleitung für {cms}"
  }},
  "estimated_time": "5 Minuten",
  "legal_references": ["§ 5 DDG", "§ 18 Abs. 2 MStV"]
}}
```"""

        elif text_type_lower == "datenschutz":
            cookie_list = "\n".join([f"  - {name}" for name in cookie_names]) if cookie_names else "  - Keine Cookies erkannt"
            services_list = "\n".join([f"  - {s}" for s in all_services]) if all_services else "  - Keine externen Dienste erkannt"

            prompt = f"""Du bist ein zertifizierter Datenschutzbeauftragter und DSGVO-Experte.

**WEBSITE:** {site_url}
**CMS:** {cms}
**Erkanntes Problem:** {issue_title} — {issue_description}
**Scanner-Hinweis:** {scanner_findings}

**FIRMENDATEN:**
- Name: {company_name}
- E-Mail (Datenschutzanfragen): {email}

**AUF DER WEBSITE ERKANNTE DIENSTE & COOKIES:**
Cookies:
{cookie_list}

Externe Dienste / Tracking:
{services_list}

**AUFGABE:**
Erstelle eine VOLLSTÄNDIGE, INDIVIDUELL ANGEPASSTE DSGVO-Datenschutzerklärung.
- Erwähne JEDEN erkannten Dienst mit Anbieter, Zweck, Rechtsgrundlage und Speicherdauer
- Für US-Dienste (Google, Meta, etc.): EU-US Data Privacy Framework oder SCCs erwähnen
- Sprache: Deutsch, klar verständlich für Laien

**DSGVO-PFLICHTANGABEN (Art. 13 DSGVO):**
1. Verantwortlicher + Kontakt
2. Zwecke & Rechtsgrundlagen (Art. 6 DSGVO)
3. Empfänger & Drittlandtransfer
4. Speicherdauer
5. Betroffenenrechte (Art. 15–22 DSGVO): Auskunft, Löschung, Widerspruch, Portabilität
6. Beschwerderecht bei Aufsichtsbehörde
7. Abschnitt je erkanntem Dienst

**OUTPUT-FORMAT (strikt JSON, kein Zusatztext):**

```json
{{
  "fix_id": "{issue.get('id', 'datenschutz_fix')}",
  "title": "Individuelle DSGVO-Datenschutzerklärung für {site_url}",
  "description": "Vollständige, auf die Website zugeschnittene Datenschutzerklärung",
  "text_content": "VOLLSTÄNDIGER HTML-TEXT — jeden erkannten Dienst einzeln behandeln",
  "text_type": "datenschutz",
  "format": "html",
  "placeholders": ["Liste der noch zu ergänzenden Felder"],
  "integration": {{
    "filename": "datenschutz.html",
    "instructions": "CMS-spezifische Anleitung für {cms}: Wo einfügen, wie verlinken"
  }},
  "estimated_time": "10-15 Minuten",
  "legal_references": ["Art. 13 DSGVO", "Art. 6 DSGVO", "§ 25 TTDSG"]
}}
```"""

        elif text_type_lower == "agb":
            prompt = f"""Du bist ein E-Commerce-Rechtsexperte, spezialisiert auf BGB §§ 305 ff. (AGB-Recht).

**WEBSITE:** {site_url}
**CMS / Shop-System:** {cms}
**Erkanntes Problem:** {issue_title} — {issue_description}
**Scanner-Hinweis:** {scanner_findings}

**FIRMENDATEN:**
- Name: {company_name}
- Adresse: {address}
- E-Mail: {email}

**AUFGABE:**
Erstelle VOLLSTÄNDIGE, RECHTSSICHERE AGB für einen Online-Shop/Dienstleister.
Berücksichtige: Widerrufsrecht (BGB § 355), Gewährleistung, Haftung, Gerichtsstand.
Keine unzulässigen Klauseln nach AGB-Recht (BGB §§ 307–309).

**OUTPUT-FORMAT (strikt JSON, kein Zusatztext):**

```json
{{
  "fix_id": "{issue.get('id', 'agb_fix')}",
  "title": "Rechtssichere AGB nach BGB §§ 305 ff.",
  "description": "Vollständige AGB für {site_url}",
  "text_content": "VOLLSTÄNDIGER HTML-TEXT DER AGB — mindestens §§ 1-8",
  "text_type": "agb",
  "format": "html",
  "placeholders": ["Liste der anzupassenden Felder"],
  "integration": {{
    "filename": "agb.html",
    "instructions": "1. Seite /agb erstellen\\n2. Im Footer verlinken\\n3. Im Checkout als Pflicht-Checkbox einbinden (Zustimmung vor Kauf)\\n4. CMS-spezifisch: {cms}"
  }},
  "estimated_time": "15-20 Minuten",
  "legal_references": ["BGB §§ 305-310", "BGB § 355", "EGBGB Art. 246a"]
}}
```"""

        elif text_type_lower == "widerrufsbelehrung":
            prompt = f"""Du bist ein E-Commerce-Rechtsexperte für Verbraucherrecht.

**WEBSITE:** {site_url}
**CMS:** {cms}
**Erkanntes Problem:** {issue_title} — {issue_description}

**FIRMENDATEN:**
- Name: {company_name}
- Adresse: {address}
- E-Mail: {email}

**AUFGABE:**
Erstelle eine GESETZESKONFORME WIDERRUFSBELEHRUNG nach BGB §§ 355, 356 + EGBGB Anlage 1 (amtliches Muster).
Inkl. Muster-Widerrufsformular.

**OUTPUT-FORMAT (strikt JSON, kein Zusatztext):**

```json
{{
  "fix_id": "{issue.get('id', 'widerruf_fix')}",
  "title": "Widerrufsbelehrung nach BGB § 355 (amtliches Muster)",
  "description": "Gesetzeskonforme Widerrufsbelehrung inkl. Widerrufsformular",
  "text_content": "VOLLSTÄNDIGER HTML-TEXT inkl. Formular",
  "text_type": "widerruf",
  "format": "html",
  "placeholders": ["[FIRMENNAME]", "[ADRESSE]", "[EMAIL]"],
  "integration": {{
    "filename": "widerrufsbelehrung.html",
    "instructions": "1. Seite /widerrufsbelehrung erstellen\\n2. Im Footer verlinken\\n3. In Bestellbestätigung per E-Mail mitsenden\\n4. CMS: {cms}"
  }},
  "estimated_time": "10 Minuten",
  "legal_references": ["BGB § 355", "BGB § 356", "EGBGB Art. 246a Anlage 1"]
}}
```"""

        else:
            prompt = f"""Erstelle einen rechtssicheren deutschen Compliance-Text für die Website {site_url}.
Problem: {issue_title} — {issue_description}
Texttyp: {text_type}
Antworte NUR mit dem JSON im TEXT_FIX_SCHEMA-Format."""

        return {
            "prompt": prompt,
            "model": AIModel.CLAUDE_SONNET.value,
            "temperature": 0.1,
            "max_tokens": 4500,
            "schema": TEXT_FIX_SCHEMA
        }
    
    def build_widget_fix_prompt(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        widget_type: str
    ) -> Dict[str, Any]:
        """
        Prompt für Widget-Integration
        """
        site_id = context.get("site_id", "demo")
        cookies = context.get("cookies", [])
        issues_list = issue.get("related_issues", [issue])
        
        if widget_type == "cookie-consent":
            detected_tools = context.get("technology", {}).get("analytics", [])
            tools_text = ", ".join(detected_tools) if detected_tools else "Keine"
            
            prompt = f"""Du bist ein Experte für Cookie-Compliance und TTDSG.

**AUFGABE:** Generiere Widget-Integration für Cookie-Consent-Management.

**WEBSITE-KONTEXT:**
- Site-ID: {site_id}
- Erkannte Cookies: {len(cookies)} Cookies
- Analytics/Tracking: {tools_text}

**WIDGET-ANFORDERUNGEN:**
1. DSGVO & TTDSG konform (§ 25 TTDSG: Einwilligung vor Speicherung)
2. Granulare Consent-Verwaltung (Notwendig, Funktional, Statistik, Marketing)
3. Opt-in als Standard (KEIN Pre-Check)
4. Cookie-Details anzeigen
5. Widerrufsrecht prominent

**OUTPUT-FORMAT:**

```json
{{
  "fix_id": "{issue.get('id', 'cookie_widget')}",
  "title": "Cookie-Consent-Widget Integration",
  "description": "DSGVO/TTDSG-konformes Cookie-Banner",
  "widget_type": "cookie-consent",
  "integration_code": "<script src=\\"https://widgets.complyo.tech/cookie-banner-v2.0.0.min.js\\" data-site-id=\\"{site_id}\\" data-config='{{...}}'></script>",
  "configuration": {{
    "cookies": {json.dumps([c.get("name") for c in cookies[:20]])},
    "detected_tools": {json.dumps(detected_tools)},
    "layout": "box_modal",
    "primaryColor": "#7c3aed",
    "autoBlock": true
  }},
  "preview_url": "https://widgets.complyo.tech/preview/cookie-consent?site={site_id}",
  "features": [
    "Granulare Consent-Verwaltung",
    "Auto-Cookie-Blocking",
    "Responsive Design",
    "WCAG 2.1 AA konform"
  ],
  "integration": {{
    "instructions": "1. Code-Snippet kopieren\\n2. Vor dem </body>-Tag einfügen\\n3. Tracking-Scripts an Consent koppeln\\n4. Testen",
    "where": "Vor </body>-Tag in der Hauptvorlage"
  }},
  "estimated_time": "3-5 Minuten"
}}
```

Generiere die Widget-Integration:"""

        elif widget_type == "accessibility":
            prompt = f"""Du bist ein Barrierefreiheits-Experte (WCAG 2.1 Level AA).

**AUFGABE:** Generiere Accessibility-Widget-Integration.

**GEFUNDENE PROBLEME:**
{json.dumps([i.get("title", "") for i in issues_list], indent=2)}

**OUTPUT-FORMAT:**

```json
{{
  "fix_id": "{issue.get('id', 'a11y_widget')}",
  "title": "Accessibility-Widget Integration",
  "description": "WCAG 2.1 AA Compliance durch automatische Fixes",
  "widget_type": "accessibility",
  "integration_code": "<script src=\\"https://widgets.complyo.tech/accessibility-v2.0.0.min.js\\" data-site-id=\\"{site_id}\\" data-auto-fix=\\"true\\"></script>",
  "configuration": {{
    "siteId": "{site_id}",
    "autoFix": true,
    "showToolbar": true,
    "features": ["contrast", "fontsize", "alt-text-fix", "aria-fix", "keyboard-nav"]
  }},
  "preview_url": "https://widgets.complyo.tech/preview/accessibility?site={site_id}",
  "features": [
    "Automatische Alt-Text-Ergänzung",
    "ARIA-Label-Fixes",
    "Kontrast-Verbesserung",
    "Keyboard-Navigation",
    "Skip-Links"
  ],
  "integration": {{
    "instructions": "1. Code-Snippet kopieren\\n2. Im <head>-Bereich einfügen\\n3. Widget konfiguriert sich automatisch",
    "where": "Im <head>-Bereich"
  }},
  "estimated_time": "2 Minuten"
}}
```

Generiere die Widget-Integration:"""
        
        else:
            prompt = f"""Generiere Widget für: {widget_type}"""
        
        return {
            "prompt": prompt,
            "model": AIModel.GPT4_TURBO.value,  # Schneller für einfachere Widget-Tasks
            "temperature": 0.2,
            "max_tokens": 1500,
            "schema": WIDGET_FIX_SCHEMA
        }
    
    def build_guide_fix_prompt(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        user_skill: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Prompt für Schritt-für-Schritt-Anleitungen
        """
        issue_title = issue.get("title", "Problem")
        issue_description = issue.get("description", "")
        recommendation = issue.get("recommendation", "")
        category = issue.get("category", "")
        legal_basis = issue.get("legal_basis", "")

        site_url = context.get("url", "N/A")
        cms = ", ".join(context.get("technology", {}).get("cms", [])) or "Unbekannt"
        analytics = ", ".join(context.get("technology", {}).get("analytics", [])) or "Keine"
        tracking = context.get("tracking_services", [])
        tracking_text = ", ".join(tracking) if tracking else "Keine"

        all_issues = context.get("all_issues", [])
        related = [i for i in all_issues if i.get("category") == category and i.get("title") != issue_title]
        related_text = "\n".join(f"  - {i.get('title')}" for i in related[:5]) or "  - Keine weiteren in dieser Kategorie"

        skill_instructions = {
            "beginner": "Schreibe für jemanden ohne Technikkenntnisse. Erkläre jeden Fachbegriff. Beschreibe genau welche Menüs/Buttons zu klicken sind. Einfache Sprache.",
            "intermediate": "Grundlegende Web-Kenntnisse vorhanden. Technische Begriffe ok, aber erkläre das Warum und Was. Konkrete Handlungsanweisungen.",
            "advanced": "Erfahrener Entwickler. Konzise Anleitung, nur das Wesentliche, mit exakten Konfigurationsdetails."
        }

        prompt = f"""Du bist ein Web-Compliance-Experte und technischer Autor.

**WEBSITE:** {site_url}
**CMS:** {cms}
**Analytics/Tracking:** {analytics} | {tracking_text}
**User-Level:** {user_skill} — {skill_instructions.get(user_skill, "")}

**ZU BEHEBENDES PROBLEM:**
- Titel: {issue_title}
- Kategorie: {category}
- Beschreibung: {issue_description}
- Empfehlung: {recommendation}
- Rechtsgrundlage: {legal_basis or "Siehe Beschreibung"}

**WEITERE OFFENE ISSUES IN DIESER KATEGORIE:**
{related_text}

**DEINE AUFGABE:**
Erstelle eine INDIVIDUELLE, KONKRETE Schritt-für-Schritt-Anleitung für genau dieses Problem auf genau dieser Website.

WICHTIG:
- Beziehe dich auf das erkannte CMS ({cms}) — gib den genauen Pfad im Admin-Panel an
- Wenn Analytics/Tracking erkannt: Diese in der Anleitung konkret erwähnen
- Mindestens 3, maximal 8 Schritte
- Jeder Schritt: konkreter Titel + klare Beschreibung + wie man prüft ob er erfolgreich war
- Code-Beispiele wo sinnvoll (bereit zum Kopieren)
- Am Ende: Wie testen, ob das Problem wirklich behoben ist?

**OUTPUT-FORMAT (strikt JSON, kein Zusatztext):**

```json
{{
  "fix_id": "{issue.get('id', 'guide_fix')}",
  "title": "Schritt-für-Schritt: {issue_title} beheben",
  "description": "Individuelle Anleitung für {site_url} — {cms}",
  "steps": [
    {{
      "step_number": 1,
      "title": "Prägnanter Schritt-Titel",
      "description": "Genaue Beschreibung was zu tun ist — wo klicken, was eingeben, was beachten",
      "code_example": "Optional: fertiger Code-Schnipsel zum Kopieren",
      "screenshot_url": null,
      "validation": "So erkennst du, dass dieser Schritt erfolgreich war"
    }}
  ],
  "difficulty": "beginner|intermediate|advanced",
  "estimated_time": "X-Y Minuten",
  "resources": {{
    "documentation_links": ["https://..."],
    "video_tutorials": [],
    "tools_needed": ["z.B. Texteditor, FTP-Client, Browser-DevTools"]
  }}
}}
```"""

        return {
            "prompt": prompt,
            "model": AIModel.CLAUDE_SONNET.value,
            "temperature": 0.3,
            "max_tokens": 3500,
            "schema": GUIDE_FIX_SCHEMA
        }
    
    def get_system_message(self, fix_type: FixType) -> str:
        """System-Message für AI-Model"""
        base_message = """Du bist ein Experte für deutsche Website-Compliance und Web-Development.

DEINE AUFGABE:
- Generiere praktische, sofort einsetzbare Lösungen
- Halte dich STRIKT an das JSON-Output-Format
- Sei präzise und rechtssicher
- Verwende moderne Web-Standards
- Ausgabe NUR JSON, keine zusätzlichen Texte

RECHTLICHER KONTEXT:
- DSGVO (EU-Datenschutz-Grundverordnung)
- TMG (Telemediengesetz)
- TTDSG (Telekommunikation-Telemedien-Datenschutz-Gesetz)
- WCAG 2.1 Level AA (Barrierefreiheit)
- BITV 2.0 (Barrierefreie-Informationstechnik-Verordnung)

Du bist darauf spezialisiert, deutsches Recht und moderne Web-Technologie zu kombinieren."""
        
        return base_message


# =============================================================================
# Context Builder
# =============================================================================

class ContextBuilder:
    """Baut optimalen Context für AI-Prompts"""
    
    @staticmethod
    def build_full_context(
        scan_result: Dict[str, Any],
        user_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Baut vollständigen Context aus Scan-Ergebnissen
        """
        website_data = scan_result.get("website_data", {})
        tech_stack = scan_result.get("tech_stack", {})
        seo_data = scan_result.get("seo_data", {})
        
        context = {
            "url": scan_result.get("url", ""),
            "site_id": scan_result.get("scan_id", "unknown"),
            "company": {
                "name": website_data.get("company_name"),
                "address": website_data.get("address"),
                "email": website_data.get("email"),
                "phone": website_data.get("phone"),
                "has_impressum": website_data.get("has_impressum", False),
                "has_datenschutz": website_data.get("has_datenschutz", False)
            },
            "shop_system": website_data.get("shop_system"),
            "technology": {
                "cms": tech_stack.get("cms", []),
                "frameworks": tech_stack.get("frameworks", []),
                "analytics": tech_stack.get("analytics", []),
                "hosting": tech_stack.get("hosting")
            },
            "seo": {
                "title": seo_data.get("title"),
                "description": seo_data.get("description"),
                "img_without_alt": seo_data.get("img_without_alt", 0)
            },
            "cookies": scan_result.get("detected_cookies", []),
            "compliance_score": scan_result.get("compliance_score", 0),
            "user_skill": user_info.get("skill_level", "intermediate") if user_info else "intermediate"
        }
        
        return context
    
    @staticmethod
    def extract_legal_info(context: Dict[str, Any]) -> Dict[str, Any]:
        """Extrahiert nur für rechtliche Texte relevante Infos"""
        return {
            "company_name": context.get("company", {}).get("name"),
            "address": context.get("company", {}).get("address"),
            "email": context.get("company", {}).get("email"),
            "phone": context.get("company", {}).get("phone"),
            "url": context.get("url"),
            "cookies": context.get("cookies", []),
            "analytics": context.get("technology", {}).get("analytics", [])
        }


