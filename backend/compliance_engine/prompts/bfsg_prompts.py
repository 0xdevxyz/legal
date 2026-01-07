"""
BFSG Prompt-Templates für LLM-basierte Accessibility-Fixes

Diese Prompts sind optimiert für:
- Unified Diff Output (git patch format)
- Minimal-invasive Änderungen
- Deutsche Sprache für Alt-Texte und Labels
- Kompatibilität mit React/Next.js/HTML
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum


class PromptTemplate(str, Enum):
    """Verfügbare Prompt-Templates"""
    ALT_TEXT = "ALT_TEXT"
    CONTRAST = "CONTRAST"
    FORM_LABELS = "FORM_LABELS"
    LANDMARKS = "LANDMARKS"
    KEYBOARD = "KEYBOARD"
    FOCUS = "FOCUS"
    ARIA = "ARIA"
    HEADINGS = "HEADINGS"
    GENERIC = "GENERIC"


@dataclass
class PromptContext:
    """Kontext für Prompt-Generierung"""
    file_path: str
    file_content: str
    findings: List[Dict[str, Any]]
    language: str = "de"
    project_type: str = "html"  # html, react, nextjs, vue
    company_name: Optional[str] = None
    
    def format_findings(self) -> str:
        """Formatiert Findings für den Prompt"""
        lines = []
        for i, finding in enumerate(self.findings, 1):
            lines.append(f"{i}) Zeile {finding.get('line', '?')}, Selector: {finding.get('selector', '?')}")
            if finding.get('snippet'):
                lines.append(f"   Snippet: {finding.get('snippet', '')[:100]}")
            if finding.get('description'):
                lines.append(f"   Beschreibung: {finding.get('description', '')}")
            lines.append("")
        return "\n".join(lines)


# =============================================================================
# System-Nachrichten
# =============================================================================

SYSTEM_MESSAGE_DE = """Du bist ein Experte für Web-Barrierefreiheit (WCAG 2.1, BFSG).
Deine Aufgabe ist es, Code-Fixes zu generieren, die Barrierefreiheitsprobleme beheben.

WICHTIGE REGELN:
1. Generiere AUSSCHLIESSLICH Unified Diffs (git patch format)
2. Ändere NUR die Stellen, die in den Findings angegeben sind
3. Keine anderen Code-Optimierungen oder Refactorings
4. Schreibe deutsche Texte für Alt-Texte, Labels etc.
5. Behalte die bestehende Code-Struktur bei
6. Füge KEINE neuen Dependencies hinzu"""

SYSTEM_MESSAGE_CODE = """Du bist ein Assistenzsystem, das Barrierefreiheitsprobleme im Code behebt.

OUTPUT-FORMAT:
Du gibst AUSSCHLIESSLICH einen Unified Diff zurück. Keine Erklärungen, keine Kommentare.
Der Diff muss direkt anwendbar sein (git apply).

Beispiel-Format:
--- a/src/components/Example.tsx
+++ b/src/components/Example.tsx
@@ -10,3 +10,4 @@
 <div>
-  <img src="image.jpg" />
+  <img src="image.jpg" alt="Beschreibung des Bildes" />
 </div>"""


# =============================================================================
# Prompt-Templates
# =============================================================================

PROMPT_ALT_TEXT = """Du bist ein Assistenzsystem, das Barrierefreiheitsprobleme im Code behebt.

AUFGABE:
Behebe ausschließlich Verstöße gegen fehlende oder unzureichende Alternativtexte für Bilder (WCAG 1.1.1).

REGELN:
- Erzeuge ausschließlich einen Unified Diff (git patch).
- Ändere nur die Stellen, die in den Findings angegeben sind.
- Für Bilder mit inhaltlicher Relevanz: sinnvolle alt-Texte erzeugen.
- Für dekorative Bilder: alt="" setzen und aria-hidden="true" hinzufügen.
- Keine anderen Code-Optimierungen durchführen.
- Schreibe alt-Texte in der Sprache des Projekts (Deutsch).

KONTEXT:
Dateipfad: {file_path}

Dateiinhalt:
<<<FILE
{file_content}
>>>

Accessibility-Findings:
<<<FINDINGS
{findings}
>>>

ANTWORTFORMAT:
<<<PATCH
(Unified Diff)
>>>"""


PROMPT_CONTRAST = """Aufgabe:
Behebe ausschließlich Farbkontrast-Probleme gemäß WCAG 1.4.3 und 1.4.11.

Regeln:
- Nur Farben modifizieren, die in den Findings genannt werden.
- Sorge für mindestens 4.5:1 (normaler Text) bzw. 3:1 (großer Text).
- Passe die Farbe minimal an, aber ausreichend, um die Kontrastanforderung zu erfüllen.
- Keine Neustrukturierung, keine generelle Designänderung.
- Gib ausschließlich einen Unified Diff aus.

Kontext:
Datei: {file_path}

Dateiinhalt:
<<<FILE
{file_content}
>>>

Findings:
<<<FINDINGS
{findings}
>>>

Antwortformat:
<<<PATCH
(Unified Diff)
>>>"""


PROMPT_FORM_LABELS = """Aufgabe:
Behebe ausschließlich Probleme im Zusammenhang mit Formularfeldern und Labels:
- Inputs ohne sichtbares Label
- Inputs ohne aria-label
- fehlende aria-describedby für Fehlermeldungen
- Buttons ohne Beschriftung

Regeln:
- Erzeuge ausschließlich einen Unified Diff.
- Labels in deutscher Sprache.
- Bestehende Design-Struktur beibehalten.
- Wenn kein Label existiert, Label-Element hinzufügen.
- Wenn kein sichtbares Label gewünscht ist, aria-label verwenden.
- aria-required setzen, wenn im Finding angegeben.

Kontext:
Pfad: {file_path}

Dateiinhalt:
<<<FILE
{file_content}
>>>

Findings:
<<<FINDINGS
{findings}
>>>

Antwortformat:
<<<PATCH
(Unified Diff)
>>>"""


PROMPT_LANDMARKS = """Aufgabe:
Behebe ausschließlich Probleme im Zusammenhang mit fehlenden oder falschen Landmarks/Regionen:
- Hauptinhalt ohne <main>
- Navigation ohne <nav> oder aria-label
- Header/Footer-Struktur
- Seitenbereiche, die semantisch ausgezeichnet werden müssen

Regeln:
- Nur die in den Findings angegebenen Container anpassen.
- Erzeuge ausschließlich einen Unified Diff.
- Keine Layout- oder Klassenänderungen.

Kontext:
Datei: {file_path}

Dateiinhalt:
<<<FILE
{file_content}
>>>

Findings:
<<<FINDINGS
{findings}
>>>

Antwortformat:
<<<PATCH
(Unified Diff)
>>>"""


PROMPT_KEYBOARD = """Aufgabe:
Behebe ausschließlich Tastaturbedienbarkeits-Probleme (WCAG 2.1.1, 2.1.2):
- Interaktive Elemente ohne tabindex
- onclick-Handler auf nicht-fokussierbaren Elementen
- fehlende Keyboard-Event-Handler

Regeln:
- Erzeuge ausschließlich einen Unified Diff.
- Füge tabindex="0" zu interaktiven Elementen hinzu.
- Füge role="button" zu klickbaren Divs/Spans hinzu.
- Füge onKeyDown-Handler für Enter/Space hinzu.
- Keine Änderungen an der visuellen Darstellung.

Kontext:
Datei: {file_path}

Dateiinhalt:
<<<FILE
{file_content}
>>>

Findings:
<<<FINDINGS
{findings}
>>>

Antwortformat:
<<<PATCH
(Unified Diff)
>>>"""


PROMPT_FOCUS = """Aufgabe:
Behebe ausschließlich Fokus-Sichtbarkeits-Probleme (WCAG 2.4.7):
- Elemente mit outline: none ohne Alternative
- Fehlende :focus-visible Styles
- Fokus-Indikatoren nicht deutlich genug

Regeln:
- Erzeuge ausschließlich einen Unified Diff.
- Entferne outline: none oder ergänze einen sichtbaren Fokus-Indikator.
- Nutze :focus-visible für moderne Browser.
- Mindestens 3px outline oder equivalenter Fokus-Stil.

Kontext:
Datei: {file_path}

Dateiinhalt:
<<<FILE
{file_content}
>>>

Findings:
<<<FINDINGS
{findings}
>>>

Antwortformat:
<<<PATCH
(Unified Diff)
>>>"""


PROMPT_ARIA = """Aufgabe:
Behebe ausschließlich ARIA-bezogene Probleme (WCAG 4.1.2):
- Fehlende aria-label für interaktive Elemente
- Fehlende oder falsche role-Attribute
- Fehlende aria-expanded, aria-controls etc.
- Icon-Buttons ohne zugänglichen Namen

Regeln:
- Erzeuge ausschließlich einen Unified Diff.
- ARIA-Labels in deutscher Sprache.
- Nutze spezifische Rollen (button, navigation, dialog, etc.).
- Keine redundanten ARIA-Attribute (z.B. role="button" auf <button>).

Kontext:
Datei: {file_path}

Dateiinhalt:
<<<FILE
{file_content}
>>>

Findings:
<<<FINDINGS
{findings}
>>>

Antwortformat:
<<<PATCH
(Unified Diff)
>>>"""


PROMPT_HEADINGS = """Aufgabe:
Behebe ausschließlich Überschriften-Hierarchie-Probleme (WCAG 1.3.1, 2.4.6):
- Fehlende H1-Überschrift
- Übersprungene Heading-Level (z.B. H1 → H3)
- Divs mit heading-ähnlichem Styling ohne semantische Heading-Tags

Regeln:
- Erzeuge ausschließlich einen Unified Diff.
- Korrigiere die Heading-Hierarchie logisch (H1 → H2 → H3).
- Ersetze styled Divs durch echte Heading-Elemente wo nötig.
- Behalte CSS-Klassen bei.

Kontext:
Datei: {file_path}

Dateiinhalt:
<<<FILE
{file_content}
>>>

Findings:
<<<FINDINGS
{findings}
>>>

Antwortformat:
<<<PATCH
(Unified Diff)
>>>"""


PROMPT_GENERIC = """Aufgabe:
Behebe das folgende Barrierefreiheits-Problem gemäß WCAG 2.1 und BFSG.

Regeln:
- Erzeuge ausschließlich einen Unified Diff.
- Ändere nur die minimal notwendigen Stellen.
- Behalte die bestehende Code-Struktur bei.
- Deutsche Texte für Labels und Beschreibungen.

Kontext:
Datei: {file_path}

Dateiinhalt:
<<<FILE
{file_content}
>>>

Findings:
<<<FINDINGS
{findings}
>>>

Antwortformat:
<<<PATCH
(Unified Diff)
>>>"""


# =============================================================================
# Prompt-Template-Mapping
# =============================================================================

PROMPT_TEMPLATES: Dict[PromptTemplate, str] = {
    PromptTemplate.ALT_TEXT: PROMPT_ALT_TEXT,
    PromptTemplate.CONTRAST: PROMPT_CONTRAST,
    PromptTemplate.FORM_LABELS: PROMPT_FORM_LABELS,
    PromptTemplate.LANDMARKS: PROMPT_LANDMARKS,
    PromptTemplate.KEYBOARD: PROMPT_KEYBOARD,
    PromptTemplate.FOCUS: PROMPT_FOCUS,
    PromptTemplate.ARIA: PROMPT_ARIA,
    PromptTemplate.HEADINGS: PROMPT_HEADINGS,
    PromptTemplate.GENERIC: PROMPT_GENERIC,
}


# =============================================================================
# Prompt-Builder Klasse
# =============================================================================

class BFSGPromptBuilder:
    """Builder für BFSG-Prompts"""
    
    def __init__(self):
        self.templates = PROMPT_TEMPLATES
    
    def build_prompt(
        self,
        template: PromptTemplate,
        context: PromptContext
    ) -> str:
        """
        Erstellt einen vollständigen Prompt aus Template und Kontext
        
        Args:
            template: Zu verwendendes Prompt-Template
            context: Kontext mit Datei-Inhalt und Findings
            
        Returns:
            Fertiger Prompt-String
        """
        template_str = self.templates.get(template, PROMPT_GENERIC)
        
        return template_str.format(
            file_path=context.file_path,
            file_content=context.file_content,
            findings=context.format_findings()
        )
    
    def get_system_message(self, for_code: bool = True) -> str:
        """
        Gibt die System-Nachricht zurück
        
        Args:
            for_code: True für Code-Fixes, False für Erklärungen
            
        Returns:
            System-Message String
        """
        return SYSTEM_MESSAGE_CODE if for_code else SYSTEM_MESSAGE_DE
    
    def build_alt_text_prompt(
        self,
        image_src: str,
        page_context: str,
        surrounding_text: str,
        filename: str
    ) -> str:
        """
        Erstellt einen Prompt für Alt-Text-Generierung (ohne Unified Diff)
        
        Args:
            image_src: URL oder Pfad des Bildes
            page_context: Kontext der Seite (Title, Meta-Description)
            surrounding_text: Text um das Bild herum
            filename: Dateiname des Bildes
            
        Returns:
            Prompt für Alt-Text-Generierung
        """
        return f"""Generiere einen kurzen, präzisen deutschen Alt-Text für dieses Bild.

KONTEXT:
- Bild-URL: {image_src}
- Dateiname: {filename}
- Seiten-Kontext: {page_context}
- Umgebender Text: {surrounding_text}

REGELN:
- Maximal 125 Zeichen
- Beschreibe, was auf dem Bild zu sehen ist
- Keine Phrasen wie "Bild von..." oder "Foto zeigt..."
- Wenn dekorativ: antworte mit DECORATIVE

ANTWORT (nur der Alt-Text, keine Erklärung):"""

    def build_widget_fix_prompt(
        self,
        issues: List[Dict[str, Any]],
        site_url: str
    ) -> str:
        """
        Erstellt Anleitung für Widget-basierte Fixes
        
        Args:
            issues: Liste der zu behebenden Issues
            site_url: URL der Website
            
        Returns:
            Anleitung für Widget-Integration
        """
        issue_summary = "\n".join([
            f"- {issue.get('title', 'Unbekannt')}: {issue.get('description', '')[:80]}"
            for issue in issues[:10]
        ])
        
        return f"""Das Complyo Accessibility-Widget kann folgende Probleme automatisch beheben:

Website: {site_url}

Probleme:
{issue_summary}

WIDGET-INTEGRATION:
1. Fügen Sie folgenden Code vor </body> ein:

<script src="https://api.complyo.tech/api/widgets/accessibility.js" 
        data-site-id="YOUR_SITE_ID"
        data-auto-fix="true">
</script>

2. Ersetzen Sie YOUR_SITE_ID durch Ihre Site-ID aus dem Complyo Dashboard.

3. Das Widget wird automatisch:
   - Fehlende Alt-Texte ergänzen
   - Skip-Links hinzufügen
   - Focus-Indikatoren verbessern
   - Kontrast-Optionen anbieten

Fertig! Die Fixes werden sofort nach Laden der Seite angewendet."""


# Globale Instanz
bfsg_prompt_builder = BFSGPromptBuilder()

