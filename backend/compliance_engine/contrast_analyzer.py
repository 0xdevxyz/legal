"""
Kontrast-Analyzer für automatische Farb-Fixes
Analysiert Farbkontraste und schlägt WCAG-konforme Alternativen vor
"""

import re
import colorsys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ColorInfo:
    """Informationen über eine Farbe"""
    hex: str
    rgb: Tuple[int, int, int]
    luminance: float
    

@dataclass
class ContrastIssue:
    """Ein Kontrast-Problem"""
    foreground: str
    background: str
    contrast_ratio: float
    required_ratio: float
    wcag_level: str
    text_size: str
    selector: str
    suggested_foreground: Optional[str] = None
    suggested_background: Optional[str] = None


class ContrastAnalyzer:
    """Analysiert Farbkontraste und generiert WCAG-konforme Fixes"""
    
    # WCAG 2.1 Kontrast-Anforderungen
    WCAG_AA_NORMAL = 4.5  # Normaler Text
    WCAG_AA_LARGE = 3.0   # Großer Text (≥18pt oder ≥14pt bold)
    WCAG_AAA_NORMAL = 7.0
    WCAG_AAA_LARGE = 4.5
    
    def __init__(self, target_level: str = 'AA'):
        """
        Initialisiert Analyzer
        
        Args:
            target_level: 'AA' oder 'AAA'
        """
        self.target_level = target_level
    
    def analyze_color_pair(
        self,
        foreground: str,
        background: str,
        text_size: str = 'normal'
    ) -> Dict:
        """
        Analysiert ein Farbpaar
        
        Args:
            foreground: Vordergrundfarbe (Hex oder RGB)
            background: Hintergrundfarbe (Hex oder RGB)
            text_size: 'normal' oder 'large'
            
        Returns:
            Dict mit Analyse-Ergebnissen
        """
        try:
            fg_color = self._parse_color(foreground)
            bg_color = self._parse_color(background)
            
            if not fg_color or not bg_color:
                return {
                    'valid': False,
                    'error': 'Invalid color format'
                }
            
            # Berechne Kontrastverhältnis
            contrast_ratio = self._calculate_contrast(
                fg_color.luminance,
                bg_color.luminance
            )
            
            # Bestimme Anforderung
            required_ratio = self._get_required_ratio(text_size)
            
            # Prüfe Konformität
            passes = contrast_ratio >= required_ratio
            
            result = {
                'valid': True,
                'foreground': fg_color.hex,
                'background': bg_color.hex,
                'contrast_ratio': round(contrast_ratio, 2),
                'required_ratio': required_ratio,
                'passes': passes,
                'wcag_level': self.target_level,
                'text_size': text_size
            }
            
            # Generiere Vorschläge wenn nicht konform
            if not passes:
                suggestions = self._generate_suggestions(
                    fg_color,
                    bg_color,
                    required_ratio
                )
                result['suggestions'] = suggestions
            
            return result
            
        except Exception as e:
            logger.error(f"Contrast analysis failed: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def analyze_css_string(self, css_content: str) -> List[ContrastIssue]:
        """
        Analysiert CSS-String und findet Kontrast-Probleme
        
        Args:
            css_content: CSS als String
            
        Returns:
            Liste von ContrastIssues
        """
        issues = []
        
        # Extrahiere CSS-Regeln mit Farben
        rules = self._extract_css_rules(css_content)
        
        for rule in rules:
            selector = rule['selector']
            color = rule.get('color')
            bg_color = rule.get('background-color') or rule.get('background')
            
            if color and bg_color:
                analysis = self.analyze_color_pair(color, bg_color)
                
                if analysis.get('valid') and not analysis.get('passes'):
                    issue = ContrastIssue(
                        foreground=analysis['foreground'],
                        background=analysis['background'],
                        contrast_ratio=analysis['contrast_ratio'],
                        required_ratio=analysis['required_ratio'],
                        wcag_level=self.target_level,
                        text_size='normal',  # TODO: Detect from font-size
                        selector=selector,
                        suggested_foreground=analysis['suggestions']['foreground'] if 'suggestions' in analysis else None,
                        suggested_background=analysis['suggestions']['background'] if 'suggestions' in analysis else None
                    )
                    issues.append(issue)
        
        return issues
    
    def generate_css_fixes(self, issues: List[ContrastIssue]) -> str:
        """
        Generiert CSS-Fixes für Kontrast-Probleme
        
        Args:
            issues: Liste von ContrastIssues
            
        Returns:
            CSS-String mit Fixes
        """
        css_lines = [
            "/* Complyo Auto-Fixes: Kontrast (WCAG 2.1 AA) */",
            ""
        ]
        
        for issue in issues:
            css_lines.append(f"/* Original: {issue.contrast_ratio}:1 - Erforderlich: {issue.required_ratio}:1 */")
            css_lines.append(f"{issue.selector} {{")
            
            if issue.suggested_foreground:
                css_lines.append(f"  color: {issue.suggested_foreground} !important;")
            
            if issue.suggested_background:
                css_lines.append(f"  background-color: {issue.suggested_background} !important;")
            
            css_lines.append("}")
            css_lines.append("")
        
        return "\n".join(css_lines)
    
    def _parse_color(self, color: str) -> Optional[ColorInfo]:
        """
        Parst Farbe aus verschiedenen Formaten
        
        Unterstützt: #RGB, #RRGGBB, rgb(r,g,b), rgba(r,g,b,a)
        """
        color = color.strip().lower()
        
        # Hex-Format
        if color.startswith('#'):
            return self._parse_hex(color)
        
        # RGB/RGBA-Format
        elif color.startswith('rgb'):
            return self._parse_rgb(color)
        
        # Named Colors (basic support)
        elif color in self._get_named_colors():
            hex_color = self._get_named_colors()[color]
            return self._parse_hex(hex_color)
        
        return None
    
    def _parse_hex(self, hex_color: str) -> Optional[ColorInfo]:
        """Parst Hex-Farbe"""
        hex_color = hex_color.lstrip('#')
        
        # Expandiere Kurzform (#RGB -> #RRGGBB)
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        if len(hex_color) != 6:
            return None
        
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            luminance = self._calculate_luminance(r, g, b)
            
            return ColorInfo(
                hex=f'#{hex_color}',
                rgb=(r, g, b),
                luminance=luminance
            )
        except ValueError:
            return None
    
    def _parse_rgb(self, rgb_string: str) -> Optional[ColorInfo]:
        """Parst RGB/RGBA-String"""
        # rgb(255, 255, 255) oder rgba(255, 255, 255, 0.5)
        match = re.search(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', rgb_string)
        
        if not match:
            return None
        
        r = int(match.group(1))
        g = int(match.group(2))
        b = int(match.group(3))
        
        luminance = self._calculate_luminance(r, g, b)
        hex_color = f'#{r:02x}{g:02x}{b:02x}'
        
        return ColorInfo(
            hex=hex_color,
            rgb=(r, g, b),
            luminance=luminance
        )
    
    def _calculate_luminance(self, r: int, g: int, b: int) -> float:
        """
        Berechnet relative Luminanz nach WCAG-Formel
        
        https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
        """
        # Normalisiere auf 0-1
        r_srgb = r / 255.0
        g_srgb = g / 255.0
        b_srgb = b / 255.0
        
        # Linearisiere
        def linearize(channel):
            if channel <= 0.03928:
                return channel / 12.92
            else:
                return ((channel + 0.055) / 1.055) ** 2.4
        
        r_linear = linearize(r_srgb)
        g_linear = linearize(g_srgb)
        b_linear = linearize(b_srgb)
        
        # Berechne Luminanz
        luminance = 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear
        
        return luminance
    
    def _calculate_contrast(self, lum1: float, lum2: float) -> float:
        """
        Berechnet Kontrastverhältnis nach WCAG-Formel
        
        https://www.w3.org/TR/WCAG21/#dfn-contrast-ratio
        """
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        contrast = (lighter + 0.05) / (darker + 0.05)
        
        return contrast
    
    def _get_required_ratio(self, text_size: str) -> float:
        """Gibt erforderliches Kontrastverhältnis zurück"""
        if self.target_level == 'AAA':
            return self.WCAG_AAA_LARGE if text_size == 'large' else self.WCAG_AAA_NORMAL
        else:  # AA
            return self.WCAG_AA_LARGE if text_size == 'large' else self.WCAG_AA_NORMAL
    
    def _generate_suggestions(
        self,
        fg_color: ColorInfo,
        bg_color: ColorInfo,
        required_ratio: float
    ) -> Dict[str, str]:
        """
        Generiert Farbvorschläge für ausreichenden Kontrast
        
        Versucht die Originalfarben so wenig wie möglich zu verändern
        """
        suggestions = {}
        
        # Strategie 1: Verdunkle Vordergrund
        darker_fg = self._adjust_luminance(fg_color, bg_color, required_ratio, darken=True)
        if darker_fg:
            contrast = self._calculate_contrast(
                self._calculate_luminance(*darker_fg),
                bg_color.luminance
            )
            if contrast >= required_ratio:
                suggestions['foreground'] = self._rgb_to_hex(*darker_fg)
        
        # Strategie 2: Helle Hintergrund auf
        lighter_bg = self._adjust_luminance(bg_color, fg_color, required_ratio, darken=False)
        if lighter_bg:
            contrast = self._calculate_contrast(
                fg_color.luminance,
                self._calculate_luminance(*lighter_bg)
            )
            if contrast >= required_ratio:
                suggestions['background'] = self._rgb_to_hex(*lighter_bg)
        
        # Fallback: Nutze schwarzweiß
        if not suggestions:
            if bg_color.luminance > 0.5:
                suggestions['foreground'] = '#000000'
            else:
                suggestions['foreground'] = '#ffffff'
        
        return suggestions
    
    def _adjust_luminance(
        self,
        color: ColorInfo,
        reference: ColorInfo,
        target_ratio: float,
        darken: bool
    ) -> Optional[Tuple[int, int, int]]:
        """Passt Luminanz einer Farbe an"""
        try:
            r, g, b = color.rgb
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            
            # Ändere Value (Helligkeit)
            step = -0.05 if darken else 0.05
            for _ in range(20):  # Max 20 Iterationen
                v += step
                v = max(0, min(1, v))
                
                r_new, g_new, b_new = colorsys.hsv_to_rgb(h, s, v)
                r_new = int(r_new * 255)
                g_new = int(g_new * 255)
                b_new = int(b_new * 255)
                
                new_lum = self._calculate_luminance(r_new, g_new, b_new)
                contrast = self._calculate_contrast(new_lum, reference.luminance)
                
                if contrast >= target_ratio:
                    return (r_new, g_new, b_new)
            
            return None
            
        except Exception as e:
            logger.debug(f"Luminance adjustment failed: {e}")
            return None
    
    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Konvertiert RGB zu Hex"""
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _extract_css_rules(self, css_content: str) -> List[Dict]:
        """Extrahiert CSS-Regeln (vereinfacht)"""
        rules = []
        
        # Sehr vereinfachter CSS-Parser
        # Für Produktion: cssutils oder tinycss2 verwenden
        
        selector_pattern = r'([^{]+)\s*\{([^}]+)\}'
        matches = re.finditer(selector_pattern, css_content)
        
        for match in matches:
            selector = match.group(1).strip()
            properties = match.group(2)
            
            rule = {'selector': selector}
            
            # Extrahiere color
            color_match = re.search(r'color\s*:\s*([^;]+)', properties)
            if color_match:
                rule['color'] = color_match.group(1).strip()
            
            # Extrahiere background-color
            bg_match = re.search(r'background-color\s*:\s*([^;]+)', properties)
            if bg_match:
                rule['background-color'] = bg_match.group(1).strip()
            
            rules.append(rule)
        
        return rules
    
    def _get_named_colors(self) -> Dict[str, str]:
        """Gibt häufige benannte Farben zurück"""
        return {
            'white': '#ffffff',
            'black': '#000000',
            'red': '#ff0000',
            'green': '#008000',
            'blue': '#0000ff',
            'yellow': '#ffff00',
            'cyan': '#00ffff',
            'magenta': '#ff00ff',
            'gray': '#808080',
            'grey': '#808080',
            'silver': '#c0c0c0',
            'maroon': '#800000',
            'olive': '#808000',
            'lime': '#00ff00',
            'aqua': '#00ffff',
            'teal': '#008080',
            'navy': '#000080',
            'fuchsia': '#ff00ff',
            'purple': '#800080'
        }


# Convenience-Funktionen

def check_contrast(foreground: str, background: str, text_size: str = 'normal') -> Dict:
    """
    Schnelle Kontrast-Prüfung
    
    Args:
        foreground: Vordergrundfarbe
        background: Hintergrundfarbe
        text_size: 'normal' oder 'large'
        
    Returns:
        Analyse-Ergebnis
    """
    analyzer = ContrastAnalyzer()
    return analyzer.analyze_color_pair(foreground, background, text_size)


def suggest_accessible_color(
    foreground: str,
    background: str,
    target_level: str = 'AA'
) -> Optional[str]:
    """
    Schlägt zugängliche Vordergrundfarbe vor
    
    Returns:
        Hex-Color oder None
    """
    analyzer = ContrastAnalyzer(target_level)
    result = analyzer.analyze_color_pair(foreground, background)
    
    if result.get('suggestions'):
        return result['suggestions'].get('foreground')
    
    return None

