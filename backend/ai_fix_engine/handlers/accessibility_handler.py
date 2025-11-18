"""
Accessibility Handler - WCAG 2.1 Compliance

Behandelt Barrierefreiheits-Issues mit Widget + Code-Fixes
"""

from typing import Dict, Any, Optional, List
import json


class AccessibilityHandler:
    """Handler für Barrierefreiheits-Fixes"""
    
    def __init__(self, widget_manager=None):
        """
        Args:
            widget_manager: Optional WidgetManager instance
        """
        self.widget_manager = widget_manager
    
    async def handle(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        ai_generated_fix: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generiert Accessibility-Fix
        
        Kombiniert Widget (für User-Präferenzen) + Code-Fixes (für echte Compliance)
        """
        # Analyze issue type
        issue_type = self._determine_accessibility_issue_type(issue)
        
        # Determine if widget is appropriate
        widget_appropriate = self._should_use_widget(issue_type, context)
        
        if widget_appropriate:
            return await self._generate_widget_fix(issue, context, issue_type)
        else:
            return await self._generate_code_fix(issue, context, issue_type, ai_generated_fix)
    
    def _determine_accessibility_issue_type(self, issue: Dict[str, Any]) -> str:
        """Bestimmt den Typ des Accessibility-Problems"""
        title_lower = issue.get("title", "").lower()
        description_lower = issue.get("description", "").lower()
        
        if "alt" in title_lower or "alternativtext" in title_lower:
            return "alt_text"
        elif "aria" in title_lower:
            return "aria_labels"
        elif "kontrast" in title_lower or "contrast" in title_lower:
            return "contrast"
        elif "tastatur" in title_lower or "keyboard" in title_lower:
            return "keyboard_navigation"
        elif "fokus" in title_lower or "focus" in title_lower:
            return "focus_indicators"
        elif "skip" in title_lower or "sprungmarke" in title_lower:
            return "skip_links"
        elif "überschrift" in title_lower or "heading" in title_lower:
            return "headings"
        else:
            return "generic"
    
    def _should_use_widget(self, issue_type: str, context: Dict[str, Any]) -> bool:
        """
        Bestimmt ob Widget sinnvoll ist
        
        Widget NUR für:
        - User-Präferenzen (Schriftgröße, Kontrast)
        - Zusätzliche Hilfsmittel
        
        KEIN Widget für:
        - Alt-Text (muss im Code sein)
        - ARIA-Labels (muss im Code sein)
        - Strukturelle Probleme
        """
        widget_suitable_types = ["contrast", "generic"]
        return issue_type in widget_suitable_types
    
    async def _generate_widget_fix(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        issue_type: str
    ) -> Dict[str, Any]:
        """Generiert Widget-basierte Lösung"""
        
        # Build widget config
        widget_config = {
            "siteId": context.get("site_id", "demo"),
            "autoFix": True,
            "showToolbar": True,
            "features": [
                "contrast",
                "fontsize",
                "line-height",
                "letter-spacing",
                "dyslexia-font",
                "highlight-links",
                "highlight-headings",
                "screen-reader-friendly"
            ],
            "position": "bottom-right",
            "primaryColor": "#7c3aed"
        }
        
        # Generate integration code
        if self.widget_manager:
            integration_code = await self.widget_manager.generate_accessibility_widget_code(
                site_id=context.get("site_id", "demo"),
                config=widget_config
            )
        else:
            config_json = json.dumps(widget_config, ensure_ascii=False)
            integration_code = f'''<!-- Complyo Accessibility Widget -->
<script 
  src="https://widgets.complyo.tech/accessibility-v2.0.0.min.js" 
  data-site-id="{context.get("site_id", "demo")}"
  data-config='{config_json}'
  async
></script>
<!-- End Complyo Accessibility Widget -->'''
        
        return {
            "fix_id": issue.get("id", "a11y_widget_fix"),
            "title": "Barrierefreiheits-Widget Integration",
            "description": "WCAG 2.1 Level AA Compliance durch Widget + automatische Fixes",
            "widget_type": "accessibility",
            "integration_code": integration_code,
            "configuration": widget_config,
            "preview_url": f"https://widgets.complyo.tech/preview/accessibility?site={context.get('site_id', 'demo')}",
            "features": [
                "Kontrast-Anpassung",
                "Schriftgrößen-Kontrolle",
                "Zeilenhöhe & Buchstabenabstand",
                "Lesemodus",
                "Link-Highlighting",
                "Screen-Reader-Optimierung",
                "Tastatur-Navigation-Hilfe"
            ],
            "integration": {
                "instructions": self._get_widget_integration_instructions(),
                "where": "Im <head>-Bereich oder vor </body>",
                "compatibility": "Alle modernen Browser, IE11+"
            },
            "estimated_time": "3 Minuten",
            "wcag_level": "AA",
            "legal_compliance": {
                "bitv": True,
                "en_301_549": True,
                "wcag_21": True
            },
            "limitations": [
                "Widget ersetzt NICHT strukturelle Fixes im Code",
                "Alt-Texte müssen weiterhin manuell gepflegt werden",
                "ARIA-Labels sollten im Code implementiert werden"
            ],
            "next_steps": [
                "Widget integrieren",
                "Toolbar testen",
                "Strukturelle Probleme separat beheben"
            ]
        }
    
    async def _generate_code_fix(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        issue_type: str,
        ai_generated_fix: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generiert Code-basierten Fix"""
        
        # Use AI-generated fix if available
        if ai_generated_fix:
            return self._enrich_code_fix(ai_generated_fix, issue_type)
        
        # Generate type-specific fix
        if issue_type == "alt_text":
            # Check if AI alt-text generation is needed
            if issue.get('metadata', {}).get('needs_ai_alt_text'):
                return await self._generate_ai_alt_text(issue, context)
            else:
                return self._generate_alt_text_fix(issue, context)
        elif issue_type == "aria_labels":
            return self._generate_aria_fix(issue, context)
        elif issue_type == "skip_links":
            return self._generate_skip_links_fix(issue, context)
        elif issue_type == "focus_indicators":
            return self._generate_focus_fix(issue, context)
        elif issue_type == "keyboard_navigation":
            return self._generate_keyboard_fix(issue, context)
        else:
            return self._generate_generic_a11y_fix(issue, context)
    
    def _generate_alt_text_fix(self, issue: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix für fehlende Alt-Texte"""
        code = '''<!-- Barrierefreie Bilder: Alt-Texte hinzufügen -->

<!-- ✅ RICHTIG: Beschreibender Alt-Text -->
<img src="produkt.jpg" alt="Rotes T-Shirt mit V-Ausschnitt, Größe M">

<!-- ✅ RICHTIG: Dekorative Bilder mit leerem Alt -->
<img src="deko.jpg" alt="" role="presentation">

<!-- ✅ RICHTIG: Komplexe Bilder mit Langbeschreibung -->
<img src="chart.png" alt="Umsatzentwicklung 2024" aria-describedby="chart-description">
<p id="chart-description">
  Der Umsatz stieg von Januar (10.000€) bis Dezember (25.000€) kontinuierlich an.
</p>

<!-- ❌ FALSCH: Kein Alt-Text -->
<img src="bild.jpg">

<!-- ❌ FALSCH: Generischer Alt-Text -->
<img src="bild.jpg" alt="Bild">

<!-- JavaScript für automatische Warnung bei fehlenden Alt-Texten (Development) -->
<script>
document.addEventListener('DOMContentLoaded', function() {
  const imagesWithoutAlt = document.querySelectorAll('img:not([alt])');
  imagesWithoutAlt.forEach(img => {
    console.warn('Fehlendes Alt-Attribut:', img.src);
    // In Development: Roten Rahmen setzen
    if (window.location.hostname === 'localhost') {
      img.style.border = '3px solid red';
    }
  });
});
</script>'''
        
        return {
            "fix_id": issue.get("id", "alt_text_fix"),
            "title": "Alt-Texte für Bilder hinzufügen",
            "description": "Beschreibende Alternative für Bilder (WCAG 1.1.1)",
            "code": code,
            "language": "html",
            "integration": {
                "instructions": """1. Alle <img>-Tags im HTML finden
2. Beschreibende Alt-Texte hinzufügen
3. Dekorative Bilder: alt="" verwenden
4. Komplexe Bilder: aria-describedby nutzen
5. CMS: Alt-Text-Feld bei Bildupload pflichtmachen""",
                "where": "Alle HTML-Dateien mit Bildern"
            },
            "estimated_time": f"{context.get('seo', {}).get('img_without_alt', 10) * 2} Minuten",
            "wcag_criteria": ["1.1.1 Non-text Content (Level A)"],
            "priority": "high"
        }
    
    async def _generate_ai_alt_text(self, issue: Dict, context: Dict) -> Dict[str, Any]:
        """
        NEU: Generiert Alt-Text mit KI
        
        Args:
            issue: Das Issue mit Bild-Information und Kontext
            context: Der Context mit site_id etc.
            
        Returns:
            Fix-Dict mit KI-generiertem Alt-Text
        """
        img_context = issue.get('metadata', {}).get('context', {})
        
        # Baue AI-Prompt
        prompt = f"""
Generiere einen WCAG-konformen Alt-Text für folgendes Bild:

KONTEXT:
- Seiten-Titel: {img_context.get('page_title', 'Unbekannt')}
- Umgebender Text: {img_context.get('surrounding_text', 'Kein Text')}
- Dateiname: {img_context.get('filename', 'Unbekannt')}
- URL: {img_context.get('page_url', '')}

ANFORDERUNGEN:
- Max. 125 Zeichen
- Beschreibend, nicht dekorativ
- KEINE Formulierungen wie "Bild von...", "Foto von..."
- Fokus auf Inhalt/Funktion des Bildes
- Deutsche Sprache

AUSGABE als JSON:
{{
  "alt_text": "...",
  "confidence": 0.9,
  "reasoning": "...",
  "is_decorative": false
}}
"""
        
        # Rufe UnifiedFixEngine (bestehend!)
        try:
            from ai_fix_engine.unified_fix_engine import UnifiedFixEngine
            engine = UnifiedFixEngine()
            
            ai_result = await engine.ai_client.call_ai(
                prompt=prompt,
                system_message="Du bist ein WCAG-Experte für Barrierefreiheit und generierst präzise Alt-Texte.",
                model="anthropic/claude-3.5-sonnet",
                temperature=0.3
            )
            
            if ai_result.success and ai_result.content:
                # Parse JSON response
                try:
                    ai_data = json.loads(ai_result.content)
                except json.JSONDecodeError:
                    # Fallback: Extrahiere Alt-Text aus Plain-Text-Antwort
                    ai_data = {
                        "alt_text": ai_result.content[:125],
                        "confidence": 0.7,
                        "reasoning": "Auto-generated from plain text response"
                    }
                
                # Build fix response
                suggested_alt = ai_data['alt_text']
                image_src = issue.get('image_src', '')
                element_html = issue.get('element_html', '')
                
                # Generate code examples
                html_fix = f'<img src="{image_src}" alt="{suggested_alt}" />'
                
                wordpress_instructions = f"""WordPress Alt-Text hinzufügen:

1. Gehe zu: Medien → Mediathek
2. Suche das Bild: {img_context.get('filename', '')}
3. Klicke auf das Bild
4. Füge im Feld "Alternativtext" ein: {suggested_alt}
5. Klicke "Aktualisieren"

✅ Fertig! Der Alt-Text wird automatisch überall übernommen."""
                
                html_instructions = f"""HTML Code ändern:

1. Öffne die Datei: {img_context.get('page_url', '')}
2. Suche nach: {img_context.get('filename', '')}
3. Ändere den Code zu:

{html_fix}

4. Speichere die Datei
5. Lade sie via FTP/cPanel hoch

✅ Fertig!"""
                
                return {
                    "fix_id": issue.get('id'),
                    "fix_type": "alt_text",
                    "title": "KI-generierter Alt-Text",
                    "description": f"KI hat einen beschreibenden Alt-Text für das Bild generiert.",
                    "suggested_alt": suggested_alt,
                    "confidence": ai_data.get('confidence', 0.8),
                    "reasoning": ai_data.get('reasoning', ''),
                    "is_decorative": ai_data.get('is_decorative', False),
                    "image_src": image_src,
                    "page_url": img_context.get('page_url', ''),
                    "filename": img_context.get('filename', ''),
                    "code": html_fix,
                    "language": "html",
                    "deployment_options": [
                        {
                            "method": "wordpress",
                            "title": "WordPress Mediathek",
                            "instructions": wordpress_instructions,
                            "estimated_time": "2 Minuten"
                        },
                        {
                            "method": "html",
                            "title": "HTML Code bearbeiten",
                            "instructions": html_instructions,
                            "estimated_time": "3 Minuten"
                        },
                        {
                            "method": "expert",
                            "title": "Expertservice buchen",
                            "instructions": "Lassen Sie alle Alt-Texte von unseren Experten hinzufügen. Inklusive: Alle 4 Säulen (Barrierefreiheit, DSGVO, Rechtssichere Texte, Cookie Compliance)",
                            "price": "3.000 EUR (einmalig, netto)",
                            "estimated_time": "48 Stunden"
                        }
                    ],
                    "wcag_criteria": ["1.1.1 Non-text Content (Level A)"],
                    "legal_basis": "WCAG 2.1 Level A, BFSG §12",
                    "estimated_time": "2 Minuten (selbst) oder 48h (Expertservice)",
                    "priority": "high",
                    "ai_powered": True,
                    "metadata": {
                        "ai_model": ai_result.model,
                        "tokens_used": ai_result.tokens_used,
                        "original_context": img_context
                    }
                }
        except Exception as e:
            # Fallback bei AI-Fehler
            return {
                "fix_id": issue.get('id'),
                "fix_type": "alt_text",
                "title": "Alt-Text hinzufügen",
                "description": f"Bitte fügen Sie einen beschreibenden Alt-Text für das Bild hinzu.",
                "error": f"KI-Generierung fehlgeschlagen: {str(e)}",
                "suggested_alt": "Bitte manuell beschreiben",
                "image_src": issue.get('image_src', ''),
                "manual_action_required": True
            }
    
    def _generate_aria_fix(self, issue: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix für fehlende ARIA-Labels"""
        code = '''<!-- ARIA-Labels für bessere Zugänglichkeit -->

<!-- ✅ RICHTIG: Input mit Label -->
<label for="email">E-Mail-Adresse</label>
<input type="email" id="email" name="email">

<!-- ✅ RICHTIG: Input ohne visuelles Label (mit aria-label) -->
<input type="search" aria-label="Website durchsuchen" placeholder="Suche...">

<!-- ✅ RICHTIG: Button mit Icon -->
<button aria-label="Menü öffnen">
  <span class="icon-menu" aria-hidden="true"></span>
</button>

<!-- ✅ RICHTIG: Landmark-Regionen -->
<nav aria-label="Hauptnavigation">
  <ul>...</ul>
</nav>

<main aria-label="Hauptinhalt">
  ...
</main>

<aside aria-label="Sidebar">
  ...
</aside>

<!-- ✅ RICHTIG: Formulare -->
<form aria-label="Kontaktformular">
  <fieldset>
    <legend>Ihre Daten</legend>
    ...
  </fieldset>
</form>

<!-- CSS: Screen-Reader-Only Text -->
<style>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>

<!-- Verwendung: -->
<button>
  <span class="sr-only">Zum Warenkorb hinzufügen</span>
  <span class="icon-cart" aria-hidden="true"></span>
</button>'''
        
        return {
            "fix_id": issue.get("id", "aria_fix"),
            "title": "ARIA-Labels für bessere Zugänglichkeit",
            "description": "Semantische Labels für Screen-Reader (WCAG 4.1.2)",
            "code": code,
            "language": "html",
            "integration": {
                "instructions": """1. Alle interaktiven Elemente prüfen (Buttons, Links, Inputs)
2. Fehlende Labels hinzufügen (aria-label oder aria-labelledby)
3. Landmark-Regionen definieren (<nav>, <main>, <aside>)
4. Icons: aria-hidden="true" + beschreibender Text
5. Testen mit Screen-Reader (NVDA, JAWS, VoiceOver)""",
                "where": "Alle HTML-Templates"
            },
            "estimated_time": "20-30 Minuten",
            "wcag_criteria": ["4.1.2 Name, Role, Value (Level A)", "2.4.6 Headings and Labels (Level AA)"],
            "priority": "high"
        }
    
    def _generate_skip_links_fix(self, issue: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix für fehlende Skip-Links"""
        code = '''<!-- Skip-Link für Tastatur-Navigation -->

<!-- HTML: Am Anfang von <body> einfügen -->
<a href="#main-content" class="skip-link">
  Zum Hauptinhalt springen
</a>

<!-- Hauptinhalt markieren -->
<main id="main-content" tabindex="-1">
  <!-- Ihr Hauptinhalt -->
</main>

<!-- CSS: Skip-Link nur bei Fokus sichtbar -->
<style>
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #000;
  color: #fff;
  padding: 8px 16px;
  text-decoration: none;
  font-weight: bold;
  z-index: 10000;
  border-radius: 0 0 4px 0;
}

.skip-link:focus {
  top: 0;
  outline: 2px solid #fff;
  outline-offset: 2px;
}

/* Fokus-Sichtbarkeit für alle interaktiven Elemente */
a:focus,
button:focus,
input:focus,
textarea:focus,
select:focus {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}

/* Fokus-Stil niemals entfernen! */
/* ❌ NIEMALS: *:focus { outline: none; } */
</style>

<!-- Optional: Mehrere Skip-Links -->
<nav class="skip-links" aria-label="Sprungmarken">
  <a href="#main-content">Zum Inhalt</a>
  <a href="#navigation">Zur Navigation</a>
  <a href="#search">Zur Suche</a>
  <a href="#footer">Zum Footer</a>
</nav>'''
        
        return {
            "fix_id": issue.get("id", "skip_links_fix"),
            "title": "Skip-Links für Tastatur-Navigation",
            "description": "Sprungmarken für schnellere Navigation (WCAG 2.4.1)",
            "code": code,
            "language": "html",
            "integration": {
                "instructions": """1. Skip-Link-HTML am Anfang von <body> einfügen
2. CSS in Stylesheet einbinden
3. Hauptinhalt mit id="main-content" markieren
4. Testen: Tab-Taste drücken, Skip-Link sollte erscheinen
5. Optional: Mehrere Skip-Links für Navigation, Suche, etc.""",
                "where": "Haupt-Layout/Template"
            },
            "estimated_time": "10 Minuten",
            "wcag_criteria": ["2.4.1 Bypass Blocks (Level A)", "2.4.4 Link Purpose (Level A)"],
            "priority": "high"
        }
    
    def _generate_focus_fix(self, issue: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix für fehlende Fokus-Indikatoren"""
        code = '''/* Fokus-Indikatoren für Barrierefreiheit */

/* ✅ RICHTIG: Sichtbare Fokus-Indikatoren */
*:focus {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}

/* Alternative: Custom Fokus-Stil */
*:focus-visible {
  outline: 3px solid #7c3aed;
  outline-offset: 3px;
  box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.2);
}

/* Buttons */
button:focus,
.btn:focus {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(0, 95, 204, 0.2);
}

/* Links */
a:focus {
  outline: 2px dashed #005fcc;
  outline-offset: 2px;
  background-color: rgba(0, 95, 204, 0.1);
}

/* Form-Elemente */
input:focus,
textarea:focus,
select:focus {
  outline: 2px solid #005fcc;
  outline-offset: 0;
  border-color: #005fcc;
  box-shadow: 0 0 0 3px rgba(0, 95, 204, 0.2);
}

/* ❌ NIEMALS Fokus komplett entfernen! */
/* Wenn Sie den Standard-Fokus nicht mögen, ersetzen Sie ihn durch einen eigenen */
/* Aber entfernen Sie ihn NIEMALS komplett! */

/* Skip-Fokus nur für Maus-User (optional) */
*:focus:not(:focus-visible) {
  outline: none;
}

/* Fokus-Reihenfolge sicherstellen */
/* Verwenden Sie tabindex nur wenn nötig */
/* tabindex="0" = natürliche Tab-Reihenfolge */
/* tabindex="-1" = programmatisch fokussierbar, aber nicht in Tab-Reihenfolge */
/* tabindex="1+" = VERMEIDEN (ändert natürliche Reihenfolge) */'''
        
        return {
            "fix_id": issue.get("id", "focus_fix"),
            "title": "Fokus-Indikatoren hinzufügen",
            "description": "Sichtbare Fokus-Markierung für Tastatur-Navigation (WCAG 2.4.7)",
            "code": code,
            "language": "css",
            "integration": {
                "instructions": """1. CSS-Code in Haupt-Stylesheet einfügen
2. Bestehende outline: none; entfernen
3. Farben an Corporate Design anpassen
4. Testen: Tab-Taste drücken und durch Seite navigieren
5. Fokus muss immer sichtbar sein!""",
                "where": "Haupt-CSS-Datei (z.B. style.css)"
            },
            "estimated_time": "5-10 Minuten",
            "wcag_criteria": ["2.4.7 Focus Visible (Level AA)", "2.4.11 Focus Appearance (Level AAA)"],
            "priority": "high"
        }
    
    def _generate_keyboard_fix(self, issue: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix für Keyboard-Navigation-Probleme"""
        return self._generate_generic_a11y_fix(issue, context)
    
    def _generate_generic_a11y_fix(self, issue: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generischer A11y-Fix"""
        return {
            "fix_id": issue.get("id", "a11y_generic_fix"),
            "title": f"Barrierefreiheits-Fix: {issue.get('title', 'Allgemein')}",
            "description": issue.get("description", ""),
            "recommendation": issue.get("recommendation", "Bitte beheben Sie das Barrierefreiheits-Problem"),
            "wcag_level": "AA",
            "estimated_time": "15-20 Minuten"
        }
    
    def _enrich_code_fix(self, ai_fix: Dict[str, Any], issue_type: str) -> Dict[str, Any]:
        """Reichert AI-generierten Code-Fix an"""
        enriched = ai_fix.copy()
        enriched["accessibility_type"] = issue_type
        enriched["wcag_level"] = "AA"
        enriched["testing_required"] = True
        return enriched
    
    def _get_widget_integration_instructions(self) -> str:
        """Integration-Anweisungen für A11y-Widget"""
        return """**Integration des Accessibility-Widgets:**

1. **Code einfügen**
   - Im <head>-Bereich ODER vor </body>
   - Widget lädt asynchron (kein Performance-Impact)

2. **Automatische Fixes**
   - Widget analysiert die Seite automatisch
   - Fehlende Alt-Texte werden ergänzt
   - ARIA-Labels werden hinzugefügt
   - Fokus-Indikatoren werden verstärkt

3. **User-Toolbar**
   - Erscheint als Button unten rechts
   - User können Schriftgröße, Kontrast, etc. anpassen
   - Einstellungen werden gespeichert

4. **WICHTIG: Widget ersetzt KEINE strukturellen Fixes!**
   - Alt-Texte sollten trotzdem im Code gepflegt werden
   - ARIA-Labels sollten nativ implementiert werden
   - Widget ist Ergänzung, nicht Ersatz

5. **Testing**
   - Tab durch die Seite navigieren
   - Screen-Reader testen (NVDA, JAWS)
   - Kontrast-Tool verwenden
   - WAVE oder Axe DevTools für Validierung"""


