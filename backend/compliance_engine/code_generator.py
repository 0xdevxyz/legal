"""
Code Generator für Barrierefreiheits-Fixes
Generiert Code-Snippets in verschiedenen Frameworks (React, Vue, HTML)
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeSnippet:
    """Repräsentiert ein Code-Snippet"""
    framework: str  # 'react', 'vue', 'html', 'angular'
    code: str
    description: str
    file_path: Optional[str] = None


class AccessibilityCodeGenerator:
    """Generiert Code-Fixes für verschiedene Frameworks"""
    
    def __init__(self):
        self.supported_frameworks = ['react', 'vue', 'html', 'angular']
    
    def generate_fixes(
        self,
        scan_results: Dict[str, Any],
        framework: str = 'html'
    ) -> Dict[str, Any]:
        """
        Generiert Code-Fixes basierend auf Scan-Ergebnissen
        
        Args:
            scan_results: Ergebnisse des Compliance-Scans
            framework: Ziel-Framework ('react', 'vue', 'html', 'angular')
            
        Returns:
            Dict mit Code-Snippets und Integration-Guide
        """
        if framework not in self.supported_frameworks:
            framework = 'html'
        
        logger.info(f"Generating {framework} code fixes from scan results")
        
        issues = scan_results.get('issues', [])
        
        fixes = {
            'react': [],
            'vue': [],
            'html': [],
            'angular': [],
            'css': []
        }
        
        # Generiere Fixes für jedes Issue
        for issue in issues:
            if issue.get('category') != 'barrierefreiheit':
                continue
            
            # Alt-Text Fixes
            if 'alt' in issue.get('title', '').lower() and issue.get('image_src'):
                snippet = self._generate_alt_text_fix(issue, framework)
                if snippet:
                    fixes[framework].append(snippet)
            
            # ARIA Fixes
            elif 'aria' in issue.get('title', '').lower():
                snippet = self._generate_aria_fix(issue, framework)
                if snippet:
                    fixes[framework].append(snippet)
            
            # Kontrast Fixes
            elif 'kontrast' in issue.get('title', '').lower():
                snippet = self._generate_contrast_fix(issue)
                if snippet:
                    fixes['css'].append(snippet)
        
        # Generiere globale Accessibility-Features
        fixes['css'].extend(self._generate_global_css_fixes())
        
        return {
            'code_snippets': fixes,
            'integration_guide': self._generate_integration_guide(fixes, framework),
            'framework': framework,
            'total_fixes': sum(len(v) for v in fixes.values())
        }
    
    def _generate_alt_text_fix(
        self,
        issue: Dict[str, Any],
        framework: str
    ) -> Optional[CodeSnippet]:
        """Generiert Alt-Text-Fix"""
        src = issue.get('image_src', '')
        alt = issue.get('suggested_alt', 'Bild')
        
        if not src:
            return None
        
        if framework == 'react':
            code = f'<Image src="{src}" alt="{alt}" />'
            description = f'React-Image-Komponente mit Alt-Text für {src}'
        
        elif framework == 'vue':
            code = f'<img :src="{src}" alt="{alt}" />'
            description = f'Vue-Image mit Alt-Text für {src}'
        
        elif framework == 'angular':
            code = f'<img [src]="{src}" alt="{alt}" />'
            description = f'Angular-Image mit Alt-Text für {src}'
        
        else:  # html
            code = f'<img src="{src}" alt="{alt}" />'
            description = f'HTML-Image mit Alt-Text für {src}'
        
        return CodeSnippet(
            framework=framework,
            code=code,
            description=description
        )
    
    def _generate_aria_fix(
        self,
        issue: Dict[str, Any],
        framework: str
    ) -> Optional[CodeSnippet]:
        """Generiert ARIA-Label-Fix"""
        element_html = issue.get('element_html', '')
        
        if 'button' in element_html.lower():
            aria_label = "Aktion ausführen"
            
            if framework == 'react':
                code = '<button aria-label="' + aria_label + '">...</button>'
            elif framework == 'vue':
                code = '<button aria-label="' + aria_label + '">...</button>'
            elif framework == 'angular':
                code = '<button aria-label="' + aria_label + '">...</button>'
            else:
                code = '<button aria-label="' + aria_label + '">...</button>'
            
            return CodeSnippet(
                framework=framework,
                code=code,
                description="Button mit ARIA-Label für Screenreader"
            )
        
        return None
    
    def _generate_contrast_fix(self, issue: Dict[str, Any]) -> CodeSnippet:
        """Generiert CSS-Kontrast-Fix"""
        code = """
/* Kontrast-Fixes für WCAG 2.1 AA */
.text-gray-400,
.text-gray-500 {
  color: #1f2937; /* Dunkler für besseren Kontrast */
}

/* Link-Kontrast */
a {
  color: #1d4ed8; /* Ausreichender Kontrast auf Weiß */
}

a:hover {
  color: #1e40af;
}
""".strip()
        
        return CodeSnippet(
            framework='css',
            code=code,
            description="CSS-Fixes für ausreichende Kontraste (WCAG 2.1 AA)"
        )
    
    def _generate_global_css_fixes(self) -> List[CodeSnippet]:
        """Generiert globale CSS-Fixes für Barrierefreiheit"""
        snippets = []
        
        # Focus-Indikatoren
        snippets.append(CodeSnippet(
            framework='css',
            code="""
/* Focus-Indikatoren (WCAG 2.4.7) */
*:focus-visible {
  outline: 3px solid #3b82f6;
  outline-offset: 2px;
}

/* Focus für Buttons */
button:focus-visible {
  outline: 3px solid #3b82f6;
  outline-offset: 2px;
}

/* Focus für Links */
a:focus-visible {
  outline: 3px solid #3b82f6;
  outline-offset: 2px;
}
""".strip(),
            description="Sichtbare Focus-Indikatoren für Tastaturnavigation"
        ))
        
        # Reduced Motion
        snippets.append(CodeSnippet(
            framework='css',
            code="""
/* Respektiere User-Präferenz für reduzierte Bewegung */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
""".strip(),
            description="Reduzierte Animationen für Nutzer mit Bewegungs-Sensitivität"
        ))
        
        # Skip-Link
        snippets.append(CodeSnippet(
            framework='css',
            code="""
/* Skip-Link für Screenreader */
.skip-link {
  position: absolute;
  top: -100px;
  left: 0;
  background: #3b82f6;
  color: white;
  padding: 0.5rem 1rem;
  text-decoration: none;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
""".strip(),
            description="Skip-Link zum Überspringen der Navigation"
        ))
        
        return snippets
    
    def _generate_integration_guide(
        self,
        fixes: Dict[str, List],
        framework: str
    ) -> Dict[str, Any]:
        """Generiert Integrations-Anleitung"""
        
        guide = {
            "framework": framework,
            "steps": [],
            "files_to_modify": [],
            "new_files": []
        }
        
        if framework == 'react':
            guide["steps"] = [
                "1. Erstellen Sie eine neue Datei `accessibility.css` im `src`-Ordner",
                "2. Kopieren Sie alle CSS-Fixes in diese Datei",
                "3. Importieren Sie die CSS-Datei in Ihrer `App.tsx` oder `index.tsx`",
                "4. Ersetzen Sie die markierten Image-Tags mit den korrigierten Versionen",
                "5. Fügen Sie fehlende ARIA-Labels zu Ihren Komponenten hinzu",
                "6. Testen Sie die Änderungen mit einem Screenreader (NVDA/JAWS)"
            ]
            guide["files_to_modify"] = [
                "src/App.tsx",
                "src/index.tsx",
                "src/components/*.tsx"
            ]
            guide["new_files"] = [
                "src/accessibility.css"
            ]
        
        elif framework == 'vue':
            guide["steps"] = [
                "1. Erstellen Sie `assets/accessibility.css`",
                "2. Importieren Sie die CSS-Datei in `main.js` oder `App.vue`",
                "3. Aktualisieren Sie Image-Tags in Ihren Vue-Komponenten",
                "4. Fügen Sie ARIA-Attribute hinzu",
                "5. Testen Sie mit Vue Devtools und Screenreader"
            ]
            guide["files_to_modify"] = [
                "src/main.js",
                "src/App.vue",
                "src/components/*.vue"
            ]
            guide["new_files"] = [
                "src/assets/accessibility.css"
            ]
        
        elif framework == 'angular':
            guide["steps"] = [
                "1. Erstellen Sie `accessibility.css` in `src/styles/`",
                "2. Fügen Sie die Datei zu `angular.json` unter `styles` hinzu",
                "3. Aktualisieren Sie Template-Dateien mit Fixes",
                "4. Fügen Sie ARIA-Attributes hinzu",
                "5. Testen Sie mit Angular Accessibility Tools"
            ]
            guide["files_to_modify"] = [
                "angular.json",
                "src/app/**/*.html"
            ]
            guide["new_files"] = [
                "src/styles/accessibility.css"
            ]
        
        else:  # HTML
            guide["steps"] = [
                "1. Erstellen Sie eine neue `accessibility.css` Datei",
                "2. Verlinken Sie die CSS-Datei in Ihrem HTML-<head>",
                "3. Ersetzen Sie Image-Tags mit Alt-Texten",
                "4. Fügen Sie ARIA-Labels zu interaktiven Elementen hinzu",
                "5. Fügen Sie einen Skip-Link am Anfang des <body> hinzu",
                "6. Testen Sie mit Browser-DevTools und Screenreader"
            ]
            guide["files_to_modify"] = [
                "index.html",
                "*.html"
            ]
            guide["new_files"] = [
                "css/accessibility.css"
            ]
        
        return guide


def generate_code_package(scan_results: Dict[str, Any], framework: str = 'html') -> Dict[str, Any]:
    """
    Convenience-Funktion zum Generieren eines vollständigen Code-Pakets
    
    Args:
        scan_results: Scan-Ergebnisse
        framework: Ziel-Framework
        
    Returns:
        Komplettes Paket mit Code und Anleitung
    """
    generator = AccessibilityCodeGenerator()
    return generator.generate_fixes(scan_results, framework)

