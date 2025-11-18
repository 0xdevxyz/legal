"""
Complyo AI Fix Engine - Prompt Management System v2.0

Strukturierte Prompts mit JSON-Schema-Validation für alle Fix-Typen.
Optimiert für Claude 3.5 Sonnet und GPT-4.

© 2025 Complyo.tech
"""

import json
from typing import Dict, Any, List, Optional
from enum import Enum


class FixType(Enum):
    """Typen von Fixes"""
    CODE = "code"
    TEXT = "text"
    WIDGET = "widget"
    GUIDE = "guide"


class AIModel(Enum):
    """Unterstützte AI-Modelle"""
    CLAUDE_SONNET = "anthropic/claude-3.5-sonnet"
    GPT4 = "openai/gpt-4"
    GPT4_TURBO = "openai/gpt-4-turbo-preview"


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
        
        tech_stack = context.get("technology", {})
        cms = ", ".join(tech_stack.get("cms", [])) or "Unbekannt"
        frameworks = ", ".join(tech_stack.get("frameworks", [])) or "Keine"
        
        prompt = f"""Du bist ein Experte für Web-Compliance und modernes Frontend-Development.

**AUFGABE:** Generiere einen CODE-FIX für folgendes Compliance-Problem.

**PROBLEM:**
- Titel: {issue_title}
- Beschreibung: {issue_description}
- Kategorie: {issue_category}

**WEBSITE-KONTEXT:**
- URL: {context.get("url", "N/A")}
- CMS: {cms}
- Framework: {frameworks}
- User-Level: {user_skill}

**ANFORDERUNGEN:**
1. Der Code MUSS syntaktisch korrekt und direkt einsetzbar sein
2. Verwende moderne Best Practices (ES6+, Semantic HTML, WCAG 2.1)
3. Code MUSS für das erkannte CMS/Framework optimiert sein
4. Füge aussagekräftige Kommentare hinzu
5. Gib KLARE Integrations-Anweisungen

**OUTPUT-FORMAT (strikt einhalten!):**

```json
{{
  "fix_id": "{issue.get('id', 'unknown')}",
  "title": "Kurzer, prägnanter Titel des Fixes",
  "description": "Was wird gefixt und warum",
  "code": "DER KOMPLETTE, FERTIGE CODE HIER",
  "language": "html|css|javascript|php",
  "before_code": "Optional: Alter Code falls ersetzt wird",
  "after_code": "Optional: Neuer Code für Diff-Ansicht",
  "integration": {{
    "file": "Ziel-Datei (z.B. 'index.html', 'style.css')",
    "line_number": null,
    "instructions": "Schritt-für-Schritt wo und wie einfügen",
    "where": "Kurze Ortsbeschreibung (z.B. 'vor </body>')"
  }},
  "explanation": "Technische Erklärung was der Code macht",
  "estimated_time": "5-10 Minuten",
  "priority": "medium|high|critical",
  "tags": ["html", "accessibility", "wcag"]
}}
```

**WICHTIG:**
- Ausgabe NUR das JSON, keine zusätzlichen Texte
- Code darf KEINE Platzhalter wie [HIER EINFÜGEN] enthalten
- Bei fehlenden Infos: Realistische Beispiele verwenden
- Code MUSS produktionsreif sein

Generiere jetzt den Fix:"""

        return {
            "prompt": prompt,
            "model": AIModel.CLAUDE_SONNET.value,
            "temperature": 0.2,
            "max_tokens": 2500,
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
        
        cookies = context.get("cookies", [])
        cookie_names = [c.get("name", "Unknown") for c in cookies[:10]]
        analytics = context.get("technology", {}).get("analytics", [])
        
        text_type_lower = text_type.lower()
        
        if text_type_lower == "impressum":
            prompt = f"""Du bist ein Fachanwalt für IT-Recht und Experte für deutsches Telemediengesetz (TMG).

**AUFGABE:** Erstelle ein VOLLSTÄNDIGES, RECHTSSICHERES Impressum nach § 5 TMG.

**FIRMENDATEN:**
- Firmenname: {company_name}
- Adresse: {address}
- E-Mail: {email}
- Telefon: {phone}

**ANFORDERUNGEN (TMG § 5):**
1. Name und Anschrift des Unternehmens
2. Kontaktdaten (E-Mail, Telefon)
3. Vertretungsberechtigte Person(en)
4. Handelsregister/Vereinsregister (falls zutreffend)
5. Umsatzsteuer-ID (falls vorhanden)
6. Aufsichtsbehörde (bei erlaubnispflichtigen Tätigkeiten)
7. Berufsbezeichnung und Kammer (bei reglementierten Berufen)

**OUTPUT-FORMAT:**

```json
{{
  "fix_id": "{issue.get('id', 'impressum_fix')}",
  "title": "Rechtssicheres Impressum nach § 5 TMG",
  "description": "Vollständiges Impressum mit allen Pflichtangaben",
  "text_content": "DER KOMPLETTE HTML-TEXT DES IMPRESSUMS",
  "text_type": "impressum",
  "format": "html",
  "placeholders": ["[REGISTERGERICHT]", "[HRB-NUMMER]", "[UST-ID]"],
  "integration": {{
    "filename": "impressum.html",
    "instructions": "1. Datei impressum.html erstellen\\n2. Text einfügen\\n3. Im Footer verlinken: <a href='/impressum.html'>Impressum</a>\\n4. Platzhalter durch echte Daten ersetzen"
  }},
  "estimated_time": "5 Minuten",
  "legal_references": ["§ 5 TMG", "§ 55 RStV"]
}}
```

**WICHTIG:**
- Text MUSS in HTML formatiert sein (mit <h1>, <p>, <strong> Tags)
- Verwende die ECHTEN Firmendaten, nicht nur Platzhalter
- Für fehlende Daten: Platzhalter in [ECKIGEN KLAMMERN]
- Text MUSS rechtlich aktuell sein (2025)
- Füge Disclaimer hinzu: "Erstellt mit Complyo.tech"

Erstelle jetzt das Impressum:"""

        elif text_type_lower == "datenschutz":
            cookie_list = "\n".join([f"- {name}" for name in cookie_names]) if cookie_names else "Keine Cookies erkannt"
            analytics_list = "\n".join([f"- {tool}" for tool in analytics]) if analytics else "Keine Analytics erkannt"
            
            prompt = f"""Du bist ein Datenschutzbeauftragter und DSGVO-Experte.

**AUFGABE:** Erstelle eine VOLLSTÄNDIGE, DSGVO-KONFORME Datenschutzerklärung.

**WEBSITE-DATEN:**
- URL: {context.get("url", "N/A")}
- Firma: {company_name}
- Kontakt: {email}

**ERKANNTE DATENVERARBEITUNG:**
Cookies:
{cookie_list}

Analytics/Tracking:
{analytics_list}

**DSGVO-PFLICHTANGABEN (Art. 13, 14):**
1. Name und Kontakt des Verantwortlichen
2. Zwecke und Rechtsgrundlagen der Verarbeitung
3. Betroffenenrechte (Auskunft, Löschung, Widerspruch, etc.)
4. Dauer der Speicherung
5. Empfänger der Daten
6. Drittlandtransfer (falls zutreffend)
7. Widerrufsrecht
8. Beschwerderecht bei Aufsichtsbehörde

**SPEZIELLE ABSCHNITTE:**
- Server-Log-Dateien
- Kontaktformular
- Cookies und Tracking (basierend auf erkannten Cookies)
- SSL/TLS-Verschlüsselung
- Hosting-Dienstleister

**OUTPUT-FORMAT:**

```json
{{
  "fix_id": "{issue.get('id', 'datenschutz_fix')}",
  "title": "DSGVO-konforme Datenschutzerklärung",
  "description": "Vollständige Datenschutzerklärung mit allen Pflichtangaben",
  "text_content": "DER KOMPLETTE HTML-TEXT DER DATENSCHUTZERKLÄRUNG",
  "text_type": "datenschutz",
  "format": "html",
  "placeholders": ["[HOSTING-ANBIETER]", "[DATENSCHUTZBEAUFTRAGTER]"],
  "integration": {{
    "filename": "datenschutz.html",
    "instructions": "1. Datei datenschutz.html erstellen\\n2. Text einfügen\\n3. Im Footer verlinken\\n4. Auf JEDER Seite erreichbar machen\\n5. Bei Änderungen aktualisieren"
  }},
  "estimated_time": "10 Minuten",
  "legal_references": ["Art. 13 DSGVO", "Art. 15 DSGVO", "§ 25 TTDSG"]
}}
```

**WICHTIG:**
- Text MUSS alle erkannten Cookies/Tracking-Tools erwähnen
- Konkrete Rechtsgrundlagen nennen (Art. 6 Abs. 1 lit. a/b/f DSGVO)
- Speicherfristen konkret angeben (z.B. "7 Tage", "bis Widerruf")
- Betroffenenrechte VOLLSTÄNDIG auflisten
- Kontaktdaten für Datenschutzanfragen angeben

Erstelle jetzt die Datenschutzerklärung:"""

        else:
            prompt = f"""Erstelle rechtssicheren Text für: {text_type}"""
        
        return {
            "prompt": prompt,
            "model": AIModel.CLAUDE_SONNET.value,
            "temperature": 0.1,  # Sehr niedrig für rechtliche Texte
            "max_tokens": 4000,
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
        
        skill_instructions = {
            "beginner": "Erkläre JEDEN Schritt detailliert. Verwende Screenshots-Beschreibungen. Keine Fachbegriffe ohne Erklärung.",
            "intermediate": "Gib klare Anweisungen mit technischen Details. User kennt HTML/CSS Basics.",
            "advanced": "Konzise technische Anleitung. User ist Web-Developer."
        }
        
        prompt = f"""Du bist ein technischer Autor und Web-Compliance-Experte.

**AUFGABE:** Erstelle eine SCHRITT-FÜR-SCHRITT-ANLEITUNG zur Behebung eines Compliance-Problems.

**PROBLEM:**
- Titel: {issue_title}
- Beschreibung: {issue_description}
- Empfehlung: {recommendation}

**USER-LEVEL:** {user_skill}
**ANPASSUNG:** {skill_instructions.get(user_skill, "")}

**WEBSITE-KONTEXT:**
- URL: {context.get("url", "N/A")}
- CMS: {", ".join(context.get("technology", {}).get("cms", [])) or "Unbekannt"}

**ANFORDERUNGEN:**
1. Minimum 3 Schritte, klar nummeriert
2. Jeder Schritt mit Titel und Beschreibung
3. Code-Beispiele wo sinnvoll
4. Validierungs-Hinweise (wie prüfen ob erfolgreich?)
5. Realistische Zeitschätzung

**OUTPUT-FORMAT:**

```json
{{
  "fix_id": "{issue.get('id', 'guide_fix')}",
  "title": "Anleitung: {issue_title}",
  "description": "Schritt-für-Schritt zur Compliance",
  "steps": [
    {{
      "step_number": 1,
      "title": "Schritt-Titel",
      "description": "Detaillierte Beschreibung was zu tun ist",
      "code_example": "Optional: Code-Snippet",
      "screenshot_url": null,
      "validation": "Wie prüfen ob dieser Schritt erfolgreich war"
    }}
  ],
  "difficulty": "beginner|intermediate|advanced",
  "estimated_time": "10-15 Minuten",
  "resources": {{
    "documentation_links": ["https://..."],
    "video_tutorials": [],
    "tools_needed": ["Text-Editor", "FTP-Client"]
  }}
}}
```

**WICHTIG:**
- Schritte MÜSSEN umsetzbar und spezifisch sein
- Code-Beispiele MÜSSEN funktionieren
- Validation MUSS konkret sein (nicht "prüfen Sie")
- Bei CMS-spezifischen Anleitungen: CMS-Namen verwenden

Erstelle jetzt die Anleitung:"""
        
        return {
            "prompt": prompt,
            "model": AIModel.CLAUDE_SONNET.value,
            "temperature": 0.3,
            "max_tokens": 3000,
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


