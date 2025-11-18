"""
Code Fix Handler - Generic Code Generation

Behandelt technische Code-Fixes (HTML/CSS/JS/PHP)
"""

from typing import Dict, Any, Optional


class CodeFixHandler:
    """Handler für Code-basierte Fixes"""
    
    async def handle(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        ai_generated_fix: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verarbeitet Code-Fixes
        
        Priorisiert AI-generierte Fixes, fällt auf Templates zurück
        """
        # Use AI-generated fix if available and valid
        if ai_generated_fix and ai_generated_fix.get("code"):
            return self._enrich_ai_code_fix(ai_generated_fix, issue, context)
        
        # Fallback: Generate basic code template
        return self._generate_template_code_fix(issue, context)
    
    def _enrich_ai_code_fix(
        self,
        ai_fix: Dict[str, Any],
        issue: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reichert AI-generierten Code-Fix an
        """
        enriched = ai_fix.copy()
        
        # Add CMS-specific instructions if CMS detected
        cms_list = context.get("technology", {}).get("cms", [])
        if cms_list:
            cms = cms_list[0].lower()
            enriched["cms_specific"] = self._get_cms_specific_instructions(cms)
        
        # Add testing checklist
        enriched["testing_checklist"] = self._get_testing_checklist(
            ai_fix.get("language", "html")
        )
        
        # Add validation hints
        enriched["validation"] = {
            "syntax_check": f"Validieren Sie den {ai_fix.get('language', 'Code')} auf Syntax-Fehler",
            "browser_test": "Testen Sie in Chrome, Firefox, Safari",
            "mobile_test": "Prüfen Sie die Mobile-Ansicht",
            "accessibility_test": "Testen Sie mit Tastatur-Navigation"
        }
        
        # Add troubleshooting
        enriched["troubleshooting"] = self._get_common_issues(
            ai_fix.get("language", "html")
        )
        
        return enriched
    
    def _generate_template_code_fix(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generiert Template-basierten Code-Fix als Fallback
        """
        # Determine code type from issue
        code_type = self._determine_code_type(issue)
        
        template_code = self._get_code_template(code_type, issue, context)
        
        return {
            "fix_id": issue.get("id", "code_template_fix"),
            "title": f"Code-Lösung: {issue.get('title', 'Problem beheben')}",
            "description": issue.get("description", ""),
            "code": template_code,
            "language": code_type,
            "integration": {
                "instructions": self._get_generic_integration_instructions(code_type),
                "where": self._get_typical_location(code_type)
            },
            "explanation": "Basis-Template - bitte an Ihre Bedürfnisse anpassen",
            "estimated_time": "15-20 Minuten",
            "priority": "medium",
            "tags": [code_type, "template", "manual-adjustment-needed"]
        }
    
    def _determine_code_type(self, issue: Dict[str, Any]) -> str:
        """Bestimmt Code-Typ aus Issue"""
        title_lower = issue.get("title", "").lower()
        description_lower = issue.get("description", "").lower()
        
        if any(keyword in title_lower or keyword in description_lower 
               for keyword in ["css", "style", "farbe", "design", "layout"]):
            return "css"
        elif any(keyword in title_lower or keyword in description_lower 
                 for keyword in ["javascript", "js", "interaktiv", "dynamisch"]):
            return "javascript"
        elif any(keyword in title_lower or keyword in description_lower 
                 for keyword in ["php", "server", "backend"]):
            return "php"
        else:
            return "html"
    
    def _get_code_template(
        self,
        code_type: str,
        issue: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Gibt Code-Template basierend auf Typ"""
        
        templates = {
            "html": self._get_html_template(issue, context),
            "css": self._get_css_template(issue, context),
            "javascript": self._get_js_template(issue, context),
            "php": self._get_php_template(issue, context)
        }
        
        return templates.get(code_type, "<!-- Code hier einfügen -->")
    
    def _get_html_template(self, issue: Dict[str, Any], context: Dict[str, Any]) -> str:
        """HTML-Template"""
        return f'''<!-- {issue.get("title", "HTML-Fix")} -->

<div class="compliance-fix">
    <h2>{issue.get("title", "Überschrift")}</h2>
    <p>{issue.get("description", "Beschreibung hier einfügen")}</p>
    
    <!-- TODO: An Ihre Bedürfnisse anpassen -->
</div>

<!-- Empfehlung: {issue.get("recommendation", "Siehe Beschreibung")} -->'''
    
    def _get_css_template(self, issue: Dict[str, Any], context: Dict[str, Any]) -> str:
        """CSS-Template"""
        return f'''/* {issue.get("title", "CSS-Fix")} */

.compliance-fix {{
    /* Basis-Styles */
    margin: 20px 0;
    padding: 15px;
    background-color: #f5f5f5;
    border-left: 4px solid #7c3aed;
}}

/* Responsive */
@media (max-width: 768px) {{
    .compliance-fix {{
        padding: 10px;
        margin: 10px 0;
    }}
}}

/* TODO: An Ihr Design anpassen */'''
    
    def _get_js_template(self, issue: Dict[str, Any], context: Dict[str, Any]) -> str:
        """JavaScript-Template"""
        return f'''// {issue.get("title", "JavaScript-Fix")}

document.addEventListener('DOMContentLoaded', function() {{
    // {issue.get("description", "Beschreibung")}
    
    // TODO: Implementierung hier einfügen
    console.log('Compliance-Fix initialisiert');
    
    // Empfehlung: {issue.get("recommendation", "Siehe Beschreibung")}
}});'''
    
    def _get_php_template(self, issue: Dict[str, Any], context: Dict[str, Any]) -> str:
        """PHP-Template"""
        return f'''<?php
/**
 * {issue.get("title", "PHP-Fix")}
 * {issue.get("description", "Beschreibung")}
 */

// TODO: Implementierung hier einfügen

// Empfehlung: {issue.get("recommendation", "Siehe Beschreibung")}

?>'''
    
    def _get_cms_specific_instructions(self, cms: str) -> Dict[str, Any]:
        """CMS-spezifische Anweisungen"""
        
        instructions = {
            "wordpress": {
                "theme_file": "functions.php oder child-theme",
                "plugin_recommended": "Code Snippets Plugin für sicheres Einbinden",
                "hook": "wp_head oder wp_footer Action Hook nutzen",
                "enqueue": "wp_enqueue_script() und wp_enqueue_style() verwenden"
            },
            "drupal": {
                "theme_file": "THEMENAME.theme",
                "module": "Custom Module erstellen empfohlen",
                "hook": "hook_preprocess_html() oder hook_page_attachments()"
            },
            "joomla": {
                "template": "Template-Override in /templates/TEMPLATENAME/",
                "plugin": "System-Plugin erstellen für globale Änderungen"
            },
            "typo3": {
                "typoscript": "setup.typoscript für globale Anpassungen",
                "extension": "Extension erstellen für komplexe Logik"
            },
            "shopify": {
                "theme": "theme.liquid oder entsprechendes Template",
                "section": "Neue Section in /sections/ erstellen",
                "snippet": "Wiederverwendbare Snippets in /snippets/"
            }
        }
        
        return instructions.get(cms, {
            "note": f"CMS '{cms}' erkannt - bitte CMS-Dokumentation für Integration konsultieren"
        })
    
    def _get_testing_checklist(self, language: str) -> List[str]:
        """Testing-Checkliste basierend auf Sprache"""
        
        checklists = {
            "html": [
                "HTML-Validierung (https://validator.w3.org/)",
                "Prüfung der Semantik",
                "Accessibility-Check (WAVE, Axe)",
                "Browser-Kompatibilität",
                "Mobile-Ansicht"
            ],
            "css": [
                "CSS-Validierung (https://jigsaw.w3.org/css-validator/)",
                "Browser-Kompatibilität (Can I Use)",
                "Responsive Design (verschiedene Viewports)",
                "Performance (keine unnötigen !important)",
                "Print-Stylesheet prüfen"
            ],
            "javascript": [
                "JavaScript-Fehler in Browser-Console prüfen",
                "Funktionalität in allen Browsern testen",
                "Performance (keine Blocking-Scripts)",
                "Error-Handling vorhanden",
                "Event-Listener korrekt entfernt"
            ],
            "php": [
                "PHP-Syntax prüfen (php -l datei.php)",
                "Error-Log überprüfen",
                "Security: SQL-Injection-Prevention",
                "Security: XSS-Prevention",
                "Performance: Caching nutzen"
            ]
        }
        
        return checklists.get(language, ["Code testen", "Fehler prüfen"])
    
    def _get_common_issues(self, language: str) -> List[Dict[str, str]]:
        """Häufige Probleme und Lösungen"""
        
        issues = {
            "html": [
                {
                    "problem": "Code wird nicht angezeigt",
                    "solution": "Browser-Cache leeren, HTML-Tags prüfen"
                },
                {
                    "problem": "Layout ist kaputt",
                    "solution": "Schließende Tags prüfen, CSS-Konflikte suchen"
                }
            ],
            "css": [
                {
                    "problem": "Styles werden nicht angewendet",
                    "solution": "Spezifität prüfen, !important vermeiden, Browser-Cache leeren"
                },
                {
                    "problem": "Layout bricht auf Mobile",
                    "solution": "Media Queries prüfen, Viewport Meta-Tag vorhanden?"
                }
            ],
            "javascript": [
                {
                    "problem": "Script funktioniert nicht",
                    "solution": "Console-Errors prüfen, DOM-Ready warten, Syntax prüfen"
                },
                {
                    "problem": "Event-Handler feuert nicht",
                    "solution": "Element existiert im DOM? Event korrekt gebunden?"
                }
            ],
            "php": [
                {
                    "problem": "Weißer Bildschirm (WSOD)",
                    "solution": "Error-Reporting aktivieren, Log-Datei prüfen"
                },
                {
                    "problem": "Änderungen werden nicht übernommen",
                    "solution": "Opcode-Cache leeren (OPcache), Server neu starten"
                }
            ]
        }
        
        return issues.get(language, [])
    
    def _get_generic_integration_instructions(self, code_type: str) -> str:
        """Generische Integrations-Anweisungen"""
        
        instructions = {
            "html": "Fügen Sie den HTML-Code an der gewünschten Stelle in Ihr Template ein",
            "css": "Fügen Sie den CSS-Code in Ihr Haupt-Stylesheet ein (z.B. style.css)",
            "javascript": "Fügen Sie den JavaScript-Code vor dem schließenden </body>-Tag ein",
            "php": "Fügen Sie den PHP-Code in die entsprechende Template-Datei ein"
        }
        
        return instructions.get(code_type, "Fügen Sie den Code an der passenden Stelle ein")
    
    def _get_typical_location(self, code_type: str) -> str:
        """Typische Datei-Location"""
        
        locations = {
            "html": "Template-Dateien (z.B. index.html, header.php)",
            "css": "Stylesheet (z.B. style.css, custom.css)",
            "javascript": "JavaScript-Datei oder vor </body>",
            "php": "Theme-Functions oder Template-Datei"
        }
        
        return locations.get(code_type, "Siehe Anleitung")


