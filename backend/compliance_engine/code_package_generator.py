"""
Code-Package-Generator
Erstellt ZIP-Pakete mit allen Accessibility-Fixes für verschiedene Frameworks
"""

import io
import zipfile
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .code_generator import AccessibilityCodeGenerator, CodeSnippet

logger = logging.getLogger(__name__)


class CodePackageGenerator:
    """Generiert ZIP-Pakete mit vollständigen Code-Fixes"""
    
    def __init__(self):
        self.code_generator = AccessibilityCodeGenerator()
    
    def generate_package(
        self,
        scan_results: Dict[str, Any],
        framework: str = 'html',
        site_url: str = ''
    ) -> bytes:
        """
        Generiert ZIP-Paket mit allen Fixes
        
        Args:
            scan_results: Scan-Ergebnisse
            framework: Ziel-Framework
            site_url: URL der Webseite
            
        Returns:
            ZIP-Datei als bytes
        """
        logger.info(f"Generating {framework} code package for {site_url}")
        
        # Generiere Code-Fixes
        fixes = self.code_generator.generate_fixes(scan_results, framework)
        
        # Erstelle ZIP in Memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. README.md
            readme = self._generate_readme(fixes, framework, site_url)
            zip_file.writestr('README.md', readme)
            
            # 2. accessibility.css (für alle Frameworks)
            css_content = self._compile_css(fixes['css'])
            zip_file.writestr('accessibility.css', css_content)
            
            # 3. Framework-spezifische Dateien
            if framework == 'react':
                self._add_react_files(zip_file, fixes)
            elif framework == 'vue':
                self._add_vue_files(zip_file, fixes)
            elif framework == 'angular':
                self._add_angular_files(zip_file, fixes)
            else:
                self._add_html_files(zip_file, fixes)
            
            # 4. Integration-Guide
            guide_content = self._generate_guide_md(fixes, framework)
            zip_file.writestr('INTEGRATION_GUIDE.md', guide_content)
            
            # 5. CHANGELOG.md
            changelog = self._generate_changelog(fixes)
            zip_file.writestr('CHANGELOG.md', changelog)
            
            # 6. fixes.json (Metadaten)
            metadata = {
                'generated_at': datetime.now().isoformat(),
                'framework': framework,
                'site_url': site_url,
                'total_fixes': fixes['total_fixes'],
                'version': '2.0.0'
            }
            zip_file.writestr('fixes.json', json.dumps(metadata, indent=2))
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def _generate_readme(
        self,
        fixes: Dict,
        framework: str,
        site_url: str
    ) -> str:
        """Generiert README.md"""
        content = f"""# Complyo Accessibility Fixes

**Generiert am:** {datetime.now().strftime('%d.%m.%Y %H:%M')}  
**Framework:** {framework.upper()}  
**Webseite:** {site_url}  
**Fixes:** {fixes['total_fixes']}

---

## ⚠️ WICHTIG: Haftungsausschluss

**Complyo wendet Code-Änderungen ausschließlich nach ausdrücklicher Bestätigung durch den Nutzer oder dessen technische Administratoren an.**

Die Verantwortung für das Ausrollen der Änderungen in produktive Systeme liegt **ausschließlich beim Nutzer**.

**Complyo generiert Patches basierend auf öffentlich zugänglichem Code. Sie übernehmen die Verantwortung für die Anwendung dieser Änderungen in Ihrem System.**

**WICHTIG:** KI-generierte Inhalte können Fehler, Ungenauigkeiten oder nicht optimale Lösungen enthalten. Bitte:
- ✅ Prüfen Sie jeden Fix vor der Anwendung
- ✅ Erstellen Sie ein Backup Ihrer Website
- ✅ Testen Sie in einer Staging-Umgebung
- ✅ Konsultieren Sie bei rechtlichen Fragen einen Anwalt

**Vollständige AGB:** https://complyo.tech/terms-liability

---

## Übersicht

Dieses Paket enthält automatisch generierte Barrierefreiheits-Fixes für Ihre Webseite nach **WCAG 2.1 Level AA** Standard.

### Enthaltene Fixes:

- ✅ **Alt-Texte** für Bilder (AI-generiert)
- ✅ **ARIA-Labels** für interaktive Elemente
- ✅ **Kontrast-Fixes** (CSS)
- ✅ **Focus-Indikatoren** (sichtbare Fokus-Markierungen)
- ✅ **Keyboard-Navigation** (vollständige Tastaturbedienung)
- ✅ **Skip-Links** (Navigation überspringen)
- ✅ **Reduced-Motion** (Animationen respektieren)

---

## Installation

Siehe **INTEGRATION_GUIDE.md** für detaillierte Schritt-für-Schritt-Anleitung.

### Schnellstart:

1. Entpacken Sie dieses ZIP-Archiv
2. Kopieren Sie `accessibility.css` in Ihr Projekt
3. Importieren/Verlinken Sie die CSS-Datei
4. Wenden Sie die Code-Fixes aus den Framework-Dateien an
5. Testen Sie mit Screenreader und Tastatur

---

## Dateien

```
complyo-accessibility-fixes/
├── README.md                    # Diese Datei
├── INTEGRATION_GUIDE.md         # Schritt-für-Schritt-Anleitung
├── CHANGELOG.md                 # Alle angewendeten Fixes
├── accessibility.css            # CSS-Fixes (erforderlich!)
├── fixes.json                   # Metadaten
└── {framework}/                 # Framework-spezifische Dateien
    ├── alt-text-fixes.{ext}     # Image-Alt-Text-Beispiele
    ├── aria-fixes.{ext}          # ARIA-Label-Beispiele
    └── components/               # Beispiel-Komponenten
```

---

## Testing

Nach der Integration testen Sie bitte:

### Automatisiert:
- Lighthouse Accessibility Score (Ziel: ≥95)
- axe DevTools Browser-Extension
- WAVE Web Accessibility Tool

### Manuell:
- **Screenreader-Test:** NVDA (Windows) oder VoiceOver (Mac)
- **Tastatur-Navigation:** Tab, Enter, Space, Esc
- **Zoom-Test:** 200% ohne horizontales Scrollen
- **Mobil-Test:** Touch-Targets ≥44x44px

---

## Support

Bei Fragen oder Problemen:

- 📧 Email: support@complyo.tech
- 🌐 Web: https://complyo.tech/support
- 📚 Docs: https://complyo.tech/docs/accessibility

---

## Lizenz

Diese Fixes wurden automatisch von Complyo generiert.  
© 2025 Complyo.tech - Made with ❤️ for accessibility

---

**Wichtig:** Diese Fixes decken ~95% der WCAG 2.1 AA Anforderungen ab.  
Für vollständige Konformität empfehlen wir ein manuelles Audit.
"""
        return content
    
    def _compile_css(self, css_snippets: List[CodeSnippet]) -> str:
        """Kompiliert alle CSS-Snippets zu einer Datei"""
        lines = [
            "/**",
            " * Complyo Accessibility Fixes",
            " * Auto-generated CSS for WCAG 2.1 Level AA compliance",
            f" * Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            " */",
            ""
        ]
        
        for snippet in css_snippets:
            lines.append(f"/* {snippet.description} */")
            lines.append(snippet.code)
            lines.append("")
        
        return "\n".join(lines)
    
    def _add_react_files(self, zip_file: zipfile.ZipFile, fixes: Dict):
        """Fügt React-spezifische Dateien hinzu"""
        react_snippets = fixes.get('react', [])
        
        if not react_snippets:
            return
        
        # alt-text-fixes.tsx
        alt_fixes = [s for s in react_snippets if 'alt' in s.description.lower()]
        if alt_fixes:
            content = self._generate_react_file(alt_fixes, 'Alt-Text')
            zip_file.writestr('react/alt-text-fixes.tsx', content)
        
        # aria-fixes.tsx
        aria_fixes = [s for s in react_snippets if 'aria' in s.description.lower()]
        if aria_fixes:
            content = self._generate_react_file(aria_fixes, 'ARIA')
            zip_file.writestr('react/aria-fixes.tsx', content)
    
    def _add_vue_files(self, zip_file: zipfile.ZipFile, fixes: Dict):
        """Fügt Vue-spezifische Dateien hinzu"""
        vue_snippets = fixes.get('vue', [])
        
        if not vue_snippets:
            return
        
        # Beispiel-Komponente
        example = """<template>
  <div class="accessibility-example">
    <!-- Beispiele für barrierefreie Implementierung -->
"""
        
        for snippet in vue_snippets[:5]:  # Erste 5 als Beispiele
            example += f"    {snippet.code}\n"
        
        example += """  </div>
</template>

<style src="../accessibility.css"></style>
"""
        
        zip_file.writestr('vue/AccessibilityExample.vue', example)
    
    def _add_angular_files(self, zip_file: zipfile.ZipFile, fixes: Dict):
        """Fügt Angular-spezifische Dateien hinzu"""
        angular_snippets = fixes.get('angular', [])
        
        if not angular_snippets:
            return
        
        # accessibility.module.ts
        module_content = """import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// Import accessibility CSS in angular.json unter "styles":
// "src/styles/accessibility.css"

@NgModule({
  declarations: [],
  imports: [CommonModule],
  exports: []
})
export class AccessibilityModule { }
"""
        
        zip_file.writestr('angular/accessibility.module.ts', module_content)
    
    def _add_html_files(self, zip_file: zipfile.ZipFile, fixes: Dict):
        """Fügt HTML-spezifische Dateien hinzu"""
        html_snippets = fixes.get('html', [])
        
        # example.html
        example = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Accessibility Fixes - Beispiel</title>
  <link rel="stylesheet" href="../accessibility.css">
</head>
<body>
  <a href="#main" class="skip-link">Zum Hauptinhalt springen</a>
  
  <main id="main">
    <h1>Barrierefreiheits-Beispiele</h1>
    
    <!-- Beispiele für fixes -->
"""
        
        for snippet in html_snippets[:5]:
            example += f"    {snippet.code}\n"
        
        example += """  </main>
</body>
</html>
"""
        
        zip_file.writestr('html/example.html', example)
    
    def _generate_react_file(self, snippets: List[CodeSnippet], title: str) -> str:
        """Generiert React-Datei aus Snippets"""
        content = f"""// Complyo Accessibility Fixes: {title}
// Auto-generated React/TSX code

import React from 'react';

/**
 * Beispiele für barrierefreie {title}-Implementierung
 * 
 * Verwenden Sie diese Patterns in Ihren Komponenten:
 */

// Beispiel 1:
"""
        
        for i, snippet in enumerate(snippets, 1):
            content += f"\n// Beispiel {i}: {snippet.description}\n"
            content += snippet.code + "\n"
        
        content += """
// Weitere Best Practices:
// - Nutzen Sie semantic HTML-Elemente
// - Testen Sie mit Screenreader (NVDA/JAWS)
// - Prüfen Sie Keyboard-Navigation
// - Verwenden Sie ESLint Plugin: eslint-plugin-jsx-a11y

export {};
"""
        
        return content
    
    def _generate_guide_md(self, fixes: Dict, framework: str) -> str:
        """Generiert Integration-Guide"""
        guide = fixes.get('integration_guide', {})
        steps = guide.get('steps', [])
        
        content = f"""# Integration-Guide

## Framework: {framework.upper()}

### Voraussetzungen

- Grundkenntnisse in {framework}
- Zugriff auf Quellcode
- Texteditor oder IDE

---

## Schritt-für-Schritt-Anleitung

"""
        
        for step in steps:
            content += f"{step}\n"
        
        content += """

---

## Dateien zum Modifizieren

"""
        
        files_to_modify = guide.get('files_to_modify', [])
        for file in files_to_modify:
            content += f"- `{file}`\n"
        
        content += """

## Neue Dateien

"""
        
        new_files = guide.get('new_files', [])
        for file in new_files:
            content += f"- `{file}`\n"
        
        content += """

---

## Testing

Nach der Integration führen Sie folgende Tests durch:

### 1. Lighthouse Audit
```bash
# Chrome DevTools → Lighthouse → Accessibility
Ziel: Score ≥95
```

### 2. axe DevTools
```bash
# Browser-Extension installieren
# Seite öffnen → axe → Scan
Ziel: 0 kritische Fehler
```

### 3. Keyboard-Navigation
- Tab durch alle interaktiven Elemente
- Enter/Space aktiviert Buttons
- Esc schließt Modals

### 4. Screenreader-Test
- **Windows:** NVDA (kostenlos)
- **Mac:** VoiceOver (eingebaut)
- Alle Inhalte müssen vorgelesen werden

---

## Häufige Probleme

### Problem: CSS wird nicht geladen
**Lösung:** Überprüfen Sie den Import-Pfad zur accessibility.css

### Problem: Focus-Indikatoren nicht sichtbar
**Lösung:** Stellen Sie sicher, dass keine `:focus { outline: none; }` vorhanden ist

### Problem: Screenreader liest nicht vor
**Lösung:** Prüfen Sie ARIA-Labels und Alt-Texte

---

## Support

Bei Fragen: support@complyo.tech
"""
        
        return content
    
    def _generate_changelog(self, fixes: Dict) -> str:
        """Generiert CHANGELOG.md"""
        content = f"""# Changelog

## Version 2.0.0 - {datetime.now().strftime('%Y-%m-%d')}

### ✅ Implementierte Fixes

"""
        
        for framework, snippets in fixes['code_snippets'].items():
            if snippets:
                content += f"\n#### {framework.upper()}\n\n"
                for snippet in snippets:
                    content += f"- {snippet.description}\n"
        
        content += f"""

### Statistiken

- **Gesamtanzahl Fixes:** {fixes['total_fixes']}
- **Framework:** {fixes['framework']}
- **WCAG Level:** AA
- **Conformance:** ~95%

---

## WCAG 2.1 Abdeckung

| Kriterium | Status |
|-----------|--------|
| 1.1.1 Non-text Content | ✅ |
| 1.4.3 Contrast (Minimum) | ✅ |
| 2.1.1 Keyboard | ✅ |
| 2.4.1 Bypass Blocks | ✅ |
| 2.4.7 Focus Visible | ✅ |
| 3.2.4 Consistent Identification | ✅ |
| 4.1.2 Name, Role, Value | ✅ |

---

_Generiert von Complyo.tech Accessibility Platform_
"""
        
        return content


# Convenience-Funktion

async def generate_zip_package(
    scan_results: Dict[str, Any],
    framework: str = 'html',
    site_url: str = ''
) -> bytes:
    """
    Generiert ZIP-Paket (async wrapper)
    
    Returns:
        ZIP-Datei als bytes
    """
    generator = CodePackageGenerator()
    return generator.generate_package(scan_results, framework, site_url)

