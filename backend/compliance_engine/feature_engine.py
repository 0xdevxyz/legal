"""
BFSG Feature-Engine
Mapping von Scanner-Issues zu strukturierten Features mit WCAG-Referenzen

Diese Engine ist das Herzstück der anfängerfreundlichen Fix-Pipeline:
1. Kategorisiert Issues nach Feature-Typ
2. Ordnet WCAG-Kriterien zu
3. Bestimmt Auto-Fix-Level
4. Wählt passende Prompt-Templates
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Literal
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Enums und Konstanten
# =============================================================================

class FeatureId(str, Enum):
    """Feature-IDs für Barrierefreiheit"""
    ALT_TEXT = "ALT_TEXT"
    CONTRAST = "CONTRAST"
    FORM_LABELS = "FORM_LABELS"
    LANDMARKS = "LANDMARKS"
    KEYBOARD = "KEYBOARD"
    ARIA = "ARIA"
    HEADINGS = "HEADINGS"
    MEDIA = "MEDIA"
    FOCUS = "FOCUS"
    UNKNOWN = "UNKNOWN"


class AutoFixLevel(str, Enum):
    """Wie gut kann dieses Feature automatisch gefixt werden?"""
    HIGH = "HIGH"       # Widget oder einfacher Code-Patch
    MEDIUM = "MEDIUM"   # Code-Patch mit Kontext nötig
    LOW = "LOW"         # Teilweise automatisch, Rest manuell
    MANUAL = "MANUAL"   # Nur Anleitung, kein Auto-Fix


class Difficulty(str, Enum):
    """Schwierigkeitsgrad für den Nutzer"""
    EASY = "easy"       # One-Click oder Copy-Paste
    MEDIUM = "medium"   # Anleitung folgen
    HARD = "hard"       # Technisches Verständnis nötig


class FixType(str, Enum):
    """Art des Fixes"""
    WIDGET = "widget"   # Widget aktivieren (One-Click)
    CODE = "code"       # Code-Patch (Download)
    MANUAL = "manual"   # Nur Anleitung


# =============================================================================
# Feature-Definitionen
# =============================================================================

@dataclass
class WCAGCriterion:
    """WCAG-Kriterium"""
    id: str           # z.B. "1.1.1"
    name: str         # z.B. "Non-text Content"
    level: str        # "A", "AA", "AAA"
    url: str = ""


@dataclass
class FeatureDefinition:
    """Definition eines Features"""
    id: FeatureId
    title: str
    description: str
    wcag_criteria: List[WCAGCriterion]
    legal_refs: List[str]
    auto_fix_level: AutoFixLevel
    difficulty: Difficulty
    fix_types: List[FixType]
    prompt_template: str  # Name des Prompt-Templates
    keywords: List[str]   # Keywords für Issue-Matching
    risk_euro_base: int   # Basis-Risiko in Euro


# Feature-Definitionen (statisch)
FEATURE_DEFINITIONS: Dict[FeatureId, FeatureDefinition] = {
    FeatureId.ALT_TEXT: FeatureDefinition(
        id=FeatureId.ALT_TEXT,
        title="Alternativtexte für Bilder",
        description="Bilder und Grafiken benötigen beschreibende Alt-Texte für Screenreader.",
        wcag_criteria=[
            WCAGCriterion("1.1.1", "Non-text Content", "A", 
                         "https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html")
        ],
        legal_refs=["BFSG §12", "BITV 2.0", "EN 301 549"],
        auto_fix_level=AutoFixLevel.HIGH,
        difficulty=Difficulty.EASY,
        fix_types=[FixType.WIDGET, FixType.CODE],
        prompt_template="ALT_TEXT",
        keywords=["alt", "bild", "image", "img", "grafik", "icon", "alt-text", "alternativtext"],
        risk_euro_base=500
    ),
    
    FeatureId.CONTRAST: FeatureDefinition(
        id=FeatureId.CONTRAST,
        title="Farbkontrast",
        description="Text muss ausreichend Kontrast zum Hintergrund haben (mind. 4.5:1).",
        wcag_criteria=[
            WCAGCriterion("1.4.3", "Contrast (Minimum)", "AA",
                         "https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html"),
            WCAGCriterion("1.4.11", "Non-text Contrast", "AA",
                         "https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html")
        ],
        legal_refs=["BFSG §12", "BITV 2.0"],
        auto_fix_level=AutoFixLevel.HIGH,
        difficulty=Difficulty.EASY,
        fix_types=[FixType.WIDGET, FixType.CODE],
        prompt_template="CONTRAST",
        keywords=["kontrast", "contrast", "farbe", "color", "lesbar", "hintergrund"],
        risk_euro_base=800
    ),
    
    FeatureId.FORM_LABELS: FeatureDefinition(
        id=FeatureId.FORM_LABELS,
        title="Formular-Labels",
        description="Eingabefelder benötigen sichtbare Labels oder ARIA-Beschriftungen.",
        wcag_criteria=[
            WCAGCriterion("1.3.1", "Info and Relationships", "A",
                         "https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html"),
            WCAGCriterion("3.3.2", "Labels or Instructions", "A",
                         "https://www.w3.org/WAI/WCAG21/Understanding/labels-or-instructions.html"),
            WCAGCriterion("4.1.2", "Name, Role, Value", "A",
                         "https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html")
        ],
        legal_refs=["BFSG §12", "BITV 2.0"],
        auto_fix_level=AutoFixLevel.MEDIUM,
        difficulty=Difficulty.MEDIUM,
        fix_types=[FixType.CODE],
        prompt_template="FORM_LABELS",
        keywords=["label", "formular", "form", "input", "eingabe", "feld", "beschriftung"],
        risk_euro_base=600
    ),
    
    FeatureId.LANDMARKS: FeatureDefinition(
        id=FeatureId.LANDMARKS,
        title="Landmarks & Seitenstruktur",
        description="Die Seite benötigt semantische Regionen (main, nav, header, footer).",
        wcag_criteria=[
            WCAGCriterion("1.3.1", "Info and Relationships", "A",
                         "https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html"),
            WCAGCriterion("2.4.1", "Bypass Blocks", "A",
                         "https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html")
        ],
        legal_refs=["BFSG §12", "BITV 2.0"],
        auto_fix_level=AutoFixLevel.HIGH,
        difficulty=Difficulty.EASY,
        fix_types=[FixType.WIDGET, FixType.CODE],
        prompt_template="LANDMARKS",
        keywords=["landmark", "main", "nav", "header", "footer", "region", "semantisch", "struktur"],
        risk_euro_base=400
    ),
    
    FeatureId.KEYBOARD: FeatureDefinition(
        id=FeatureId.KEYBOARD,
        title="Tastaturbedienung",
        description="Alle Funktionen müssen per Tastatur bedienbar sein.",
        wcag_criteria=[
            WCAGCriterion("2.1.1", "Keyboard", "A",
                         "https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html"),
            WCAGCriterion("2.1.2", "No Keyboard Trap", "A",
                         "https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap.html")
        ],
        legal_refs=["BFSG §12", "BITV 2.0"],
        auto_fix_level=AutoFixLevel.MEDIUM,
        difficulty=Difficulty.MEDIUM,
        fix_types=[FixType.WIDGET, FixType.CODE],
        prompt_template="KEYBOARD",
        keywords=["tastatur", "keyboard", "tab", "focus", "tabindex", "bedienung"],
        risk_euro_base=1000
    ),
    
    FeatureId.FOCUS: FeatureDefinition(
        id=FeatureId.FOCUS,
        title="Fokus-Sichtbarkeit",
        description="Der Tastaturfokus muss sichtbar sein.",
        wcag_criteria=[
            WCAGCriterion("2.4.7", "Focus Visible", "AA",
                         "https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html")
        ],
        legal_refs=["BFSG §12", "BITV 2.0"],
        auto_fix_level=AutoFixLevel.HIGH,
        difficulty=Difficulty.EASY,
        fix_types=[FixType.WIDGET, FixType.CODE],
        prompt_template="FOCUS",
        keywords=["focus", "fokus", "sichtbar", "visible", "outline"],
        risk_euro_base=500
    ),
    
    FeatureId.ARIA: FeatureDefinition(
        id=FeatureId.ARIA,
        title="ARIA-Labels & Rollen",
        description="Interaktive Elemente benötigen korrekten Namen, Rolle und Wert.",
        wcag_criteria=[
            WCAGCriterion("4.1.2", "Name, Role, Value", "A",
                         "https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html")
        ],
        legal_refs=["BFSG §12", "BITV 2.0"],
        auto_fix_level=AutoFixLevel.MEDIUM,
        difficulty=Difficulty.MEDIUM,
        fix_types=[FixType.CODE],
        prompt_template="ARIA",
        keywords=["aria", "role", "label", "button", "screenreader"],
        risk_euro_base=700
    ),
    
    FeatureId.HEADINGS: FeatureDefinition(
        id=FeatureId.HEADINGS,
        title="Überschriften-Hierarchie",
        description="Überschriften müssen in logischer Reihenfolge verwendet werden (H1-H6).",
        wcag_criteria=[
            WCAGCriterion("1.3.1", "Info and Relationships", "A",
                         "https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html"),
            WCAGCriterion("2.4.6", "Headings and Labels", "AA",
                         "https://www.w3.org/WAI/WCAG21/Understanding/headings-and-labels.html")
        ],
        legal_refs=["BFSG §12", "BITV 2.0"],
        auto_fix_level=AutoFixLevel.MEDIUM,
        difficulty=Difficulty.MEDIUM,
        fix_types=[FixType.CODE, FixType.MANUAL],
        prompt_template="HEADINGS",
        keywords=["heading", "überschrift", "h1", "h2", "h3", "hierarchie"],
        risk_euro_base=300
    ),
    
    FeatureId.MEDIA: FeatureDefinition(
        id=FeatureId.MEDIA,
        title="Medien-Barrierefreiheit",
        description="Videos und Audio benötigen Untertitel und Transkripte.",
        wcag_criteria=[
            WCAGCriterion("1.2.1", "Audio-only and Video-only", "A",
                         "https://www.w3.org/WAI/WCAG21/Understanding/audio-only-and-video-only-prerecorded.html"),
            WCAGCriterion("1.2.2", "Captions", "A",
                         "https://www.w3.org/WAI/WCAG21/Understanding/captions-prerecorded.html")
        ],
        legal_refs=["BFSG §12", "BITV 2.0"],
        auto_fix_level=AutoFixLevel.LOW,
        difficulty=Difficulty.HARD,
        fix_types=[FixType.MANUAL],
        prompt_template="MEDIA",
        keywords=["video", "audio", "media", "untertitel", "caption", "transkript"],
        risk_euro_base=1500
    ),
}


# =============================================================================
# Strukturiertes Issue mit Feature-Zuordnung
# =============================================================================

@dataclass
class StructuredIssue:
    """Ein Issue mit vollständiger Feature-Zuordnung"""
    id: str
    feature_id: FeatureId
    title: str
    description: str
    severity: str
    
    # WCAG & Legal
    wcag_criteria: List[str]
    legal_refs: List[str]
    
    # Fix-Informationen
    auto_fix_level: AutoFixLevel
    difficulty: Difficulty
    fix_types: List[FixType]
    recommended_fix_type: FixType
    
    # Kontext
    element_html: Optional[str] = None
    selector: Optional[str] = None
    page_url: Optional[str] = None
    
    # AI-generierte Inhalte
    suggested_fix: Optional[str] = None
    fix_code: Optional[str] = None
    
    # Risiko
    risk_euro: int = 0
    
    # Metadaten
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary für API-Response"""
        return {
            "id": self.id,
            "feature_id": self.feature_id.value,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "wcag_criteria": self.wcag_criteria,
            "legal_refs": self.legal_refs,
            "auto_fix_level": self.auto_fix_level.value,
            "difficulty": self.difficulty.value,
            "fix_types": [ft.value for ft in self.fix_types],
            "recommended_fix_type": self.recommended_fix_type.value,
            "element_html": self.element_html,
            "selector": self.selector,
            "page_url": self.page_url,
            "suggested_fix": self.suggested_fix,
            "fix_code": self.fix_code,
            "risk_euro": self.risk_euro,
            "metadata": self.metadata
        }


# =============================================================================
# Feature-Engine
# =============================================================================

class FeatureEngine:
    """
    Engine zur Kategorisierung und Strukturierung von Barrierefreiheits-Issues
    
    Hauptaufgaben:
    1. Issues einem Feature zuordnen
    2. WCAG-Kriterien und Schweregrad bestimmen
    3. Empfohlenen Fix-Typ ermitteln
    4. Issues für Patch-Service vorbereiten
    """
    
    def __init__(self):
        self.features = FEATURE_DEFINITIONS
        logger.info(f"🔧 FeatureEngine initialisiert mit {len(self.features)} Features")
    
    def categorize_issue(self, raw_issue: Dict[str, Any]) -> StructuredIssue:
        """
        Kategorisiert ein rohes Scanner-Issue und ordnet es einem Feature zu
        
        Args:
            raw_issue: Issue vom Scanner (z.B. aus barrierefreiheit_check.py)
            
        Returns:
            StructuredIssue mit vollständiger Feature-Zuordnung
        """
        # Feature ermitteln
        feature_id = self._detect_feature(raw_issue)
        feature_def = self.features.get(feature_id, self.features.get(FeatureId.UNKNOWN))
        
        if feature_def is None:
            # Fallback für unbekannte Features
            feature_def = FeatureDefinition(
                id=FeatureId.UNKNOWN,
                title="Unbekanntes Problem",
                description="Dieses Problem konnte keiner Kategorie zugeordnet werden.",
                wcag_criteria=[],
                legal_refs=["BFSG §12"],
                auto_fix_level=AutoFixLevel.MANUAL,
                difficulty=Difficulty.HARD,
                fix_types=[FixType.MANUAL],
                prompt_template="GENERIC",
                keywords=[],
                risk_euro_base=500
            )
        
        # Schweregrad ermitteln
        severity = raw_issue.get('severity', 'warning')
        
        # Risiko berechnen
        risk_multiplier = {'critical': 2.0, 'error': 1.5, 'warning': 1.0, 'info': 0.5}
        risk_euro = int(feature_def.risk_euro_base * risk_multiplier.get(severity, 1.0))
        
        # Empfohlenen Fix-Typ bestimmen
        recommended_fix = self._determine_recommended_fix(feature_def, raw_issue)
        
        # WCAG-Kriterien als Strings
        wcag_strings = [f"{c.id} ({c.level})" for c in feature_def.wcag_criteria]
        
        return StructuredIssue(
            id=raw_issue.get('id', f"{feature_id.value}_{hash(raw_issue.get('title', ''))}")[:32],
            feature_id=feature_id,
            title=raw_issue.get('title', feature_def.title),
            description=raw_issue.get('description', feature_def.description),
            severity=severity,
            wcag_criteria=wcag_strings,
            legal_refs=feature_def.legal_refs,
            auto_fix_level=feature_def.auto_fix_level,
            difficulty=feature_def.difficulty,
            fix_types=feature_def.fix_types,
            recommended_fix_type=recommended_fix,
            element_html=raw_issue.get('element_html'),
            selector=raw_issue.get('selector'),
            page_url=raw_issue.get('page_url', raw_issue.get('metadata', {}).get('page_url')),
            suggested_fix=raw_issue.get('recommendation'),
            fix_code=raw_issue.get('fix_code'),
            risk_euro=risk_euro,
            metadata={
                **raw_issue.get('metadata', {}),
                'original_category': raw_issue.get('category'),
                'image_src': raw_issue.get('image_src'),
                'suggested_alt': raw_issue.get('suggested_alt'),
            }
        )
    
    def categorize_issues(self, raw_issues: List[Dict[str, Any]]) -> List[StructuredIssue]:
        """
        Kategorisiert eine Liste von Issues
        
        Args:
            raw_issues: Liste von Scanner-Issues
            
        Returns:
            Liste von StructuredIssues
        """
        structured = []
        for issue in raw_issues:
            try:
                structured.append(self.categorize_issue(issue))
            except Exception as e:
                logger.warning(f"⚠️ Konnte Issue nicht kategorisieren: {e}")
                continue
        
        logger.info(f"✅ {len(structured)} von {len(raw_issues)} Issues kategorisiert")
        return structured
    
    def group_by_feature(self, issues: List[StructuredIssue]) -> Dict[FeatureId, List[StructuredIssue]]:
        """
        Gruppiert Issues nach Feature
        
        Args:
            issues: Liste von StructuredIssues
            
        Returns:
            Dictionary mit Feature-ID als Key und Liste von Issues als Value
        """
        grouped: Dict[FeatureId, List[StructuredIssue]] = {}
        
        for issue in issues:
            if issue.feature_id not in grouped:
                grouped[issue.feature_id] = []
            grouped[issue.feature_id].append(issue)
        
        return grouped
    
    def group_by_difficulty(self, issues: List[StructuredIssue]) -> Dict[Difficulty, List[StructuredIssue]]:
        """
        Gruppiert Issues nach Schwierigkeit (für anfängerfreundliche Darstellung)
        
        Args:
            issues: Liste von StructuredIssues
            
        Returns:
            Dictionary mit Difficulty als Key
        """
        grouped: Dict[Difficulty, List[StructuredIssue]] = {
            Difficulty.EASY: [],
            Difficulty.MEDIUM: [],
            Difficulty.HARD: []
        }
        
        for issue in issues:
            grouped[issue.difficulty].append(issue)
        
        return grouped
    
    def get_summary(self, issues: List[StructuredIssue]) -> Dict[str, Any]:
        """
        Erstellt eine anfängerfreundliche Zusammenfassung
        
        Args:
            issues: Liste von StructuredIssues
            
        Returns:
            Dictionary mit Statistiken und Empfehlungen
        """
        by_feature = self.group_by_feature(issues)
        by_difficulty = self.group_by_difficulty(issues)
        
        # Zähle auto-fixbare Issues
        auto_fixable = sum(1 for i in issues if i.auto_fix_level in [AutoFixLevel.HIGH, AutoFixLevel.MEDIUM])
        widget_fixable = sum(1 for i in issues if FixType.WIDGET in i.fix_types)
        
        # Gesamt-Risiko
        total_risk = sum(i.risk_euro for i in issues)
        
        return {
            "total_issues": len(issues),
            "auto_fixable": auto_fixable,
            "widget_fixable": widget_fixable,
            "manual_only": len(issues) - auto_fixable,
            "by_difficulty": {
                "easy": len(by_difficulty[Difficulty.EASY]),
                "medium": len(by_difficulty[Difficulty.MEDIUM]),
                "hard": len(by_difficulty[Difficulty.HARD])
            },
            "by_feature": {
                fid.value: len(issues_list) 
                for fid, issues_list in by_feature.items()
            },
            "total_risk_euro": total_risk,
            "recommendation": self._get_recommendation(issues, widget_fixable, auto_fixable)
        }
    
    def _detect_feature(self, raw_issue: Dict[str, Any]) -> FeatureId:
        """Ermittelt Feature-ID basierend auf Issue-Inhalt"""
        
        # Kombiniere alle relevanten Textfelder
        text = " ".join([
            str(raw_issue.get('title', '')),
            str(raw_issue.get('description', '')),
            str(raw_issue.get('category', '')),
            str(raw_issue.get('recommendation', ''))
        ]).lower()
        
        # Direkte Kategorie-Matches
        category = raw_issue.get('category', '').lower()
        if 'kontrast' in category:
            return FeatureId.CONTRAST
        if 'tastaturbedienung' in category:
            return FeatureId.KEYBOARD
        
        # Keyword-basiertes Matching
        best_match = FeatureId.UNKNOWN
        best_score = 0
        
        for feature_id, feature_def in self.features.items():
            score = 0
            for keyword in feature_def.keywords:
                if keyword.lower() in text:
                    score += 1
                    # Bonus für Titel-Match
                    if keyword.lower() in raw_issue.get('title', '').lower():
                        score += 2
            
            if score > best_score:
                best_score = score
                best_match = feature_id
        
        # Spezielle Patterns
        if re.search(r'alt[- ]?text|bild ohne alt|image without alt', text, re.I):
            return FeatureId.ALT_TEXT
        
        if re.search(r'label|formular.*feld|input ohne', text, re.I):
            return FeatureId.FORM_LABELS
        
        if re.search(r'<main>|<nav>|landmark|region', text, re.I):
            return FeatureId.LANDMARKS
        
        if re.search(r'aria-|role=', text, re.I):
            return FeatureId.ARIA
        
        if re.search(r'focus|fokus|outline', text, re.I):
            return FeatureId.FOCUS
        
        if re.search(r'h1|h2|überschrift|heading', text, re.I):
            return FeatureId.HEADINGS
        
        return best_match
    
    def _determine_recommended_fix(self, feature_def: FeatureDefinition, raw_issue: Dict[str, Any]) -> FixType:
        """Bestimmt den empfohlenen Fix-Typ"""
        
        # Wenn Widget-Fix möglich und auto_fixable, dann Widget
        if FixType.WIDGET in feature_def.fix_types and raw_issue.get('auto_fixable', False):
            return FixType.WIDGET
        
        # Wenn Code-Fix möglich
        if FixType.CODE in feature_def.fix_types:
            return FixType.CODE
        
        # Fallback
        return feature_def.fix_types[0] if feature_def.fix_types else FixType.MANUAL
    
    def _get_recommendation(self, issues: List[StructuredIssue], widget_fixable: int, auto_fixable: int) -> str:
        """Generiert eine anfängerfreundliche Empfehlung"""
        
        if len(issues) == 0:
            return "🎉 Keine Barrierefreiheits-Probleme gefunden!"
        
        if widget_fixable > 0:
            return (
                f"💡 Empfehlung: Aktivieren Sie das Complyo-Widget für sofortige Fixes. "
                f"{widget_fixable} Probleme können automatisch behoben werden."
            )
        
        if auto_fixable > 0:
            return (
                f"📦 Empfehlung: Laden Sie das Fix-Paket herunter. "
                f"{auto_fixable} Probleme können mit den Code-Patches behoben werden."
            )
        
        return "📋 Diese Probleme erfordern manuelle Anpassungen. Folgen Sie der Schritt-für-Schritt-Anleitung."
    
    def get_feature_definition(self, feature_id: FeatureId) -> Optional[FeatureDefinition]:
        """Gibt die Feature-Definition zurück"""
        return self.features.get(feature_id)
    
    def get_prompt_template_name(self, feature_id: FeatureId) -> str:
        """Gibt den Namen des Prompt-Templates für ein Feature zurück"""
        feature_def = self.features.get(feature_id)
        if feature_def:
            return feature_def.prompt_template
        return "GENERIC"


# Globale Instanz
feature_engine = FeatureEngine()

