"""
Barrierefreiheit Check (BFSG)
Prüft Website auf Barrierefreiheitsstärkungsgesetz-Compliance
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
import re
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

@dataclass
class BarrierefreiheitIssue:
    category: str
    severity: str
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool = False
    is_missing: bool = False  # True wenn komplettes Element fehlt (nicht nur Unterpunkt)
    screenshot_url: Optional[str] = None  # NEU: Screenshot des problematischen Elements
    element_html: Optional[str] = None  # NEU: HTML des Elements
    fix_code: Optional[str] = None  # NEU: Vorgeschlagener Fix-Code
    suggested_alt: Optional[str] = None  # NEU: AI-generierter Alt-Text
    image_src: Optional[str] = None  # NEU: Bild-URL
    metadata: Dict[str, Any] = field(default_factory=dict)  # NEU: Zusätzliche Metadaten

async def check_barrierefreiheit_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Umfassender Barrierefreiheits-Check
    
    Prüft:
    1. Accessibility-Widget/Tool vorhanden
    2. Kontrast-Verhältnisse
    3. Alt-Texte für Bilder
    4. ARIA-Labels und Rollen
    5. Tastaturbedienung
    6. Semantisches HTML
    7. Screenreader-Kompatibilität
    """
    issues = []
    
    # 1. Check für Accessibility-Tools/Widgets
    widget_issue = await _check_accessibility_widget(soup)
    if widget_issue:
        issues.append(widget_issue)
        
        # ✅ HAUPTELEMENT FEHLT: Wenn kein Widget vorhanden, generiere alle WCAG-Kriterien als fehlend
        # Alle kritischen WCAG 2.1 Level A/AA Kriterien als fehlend markieren
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='critical',
            title='WCAG 1.1.1: Text-Alternativen fehlen',
            description='Es fehlen vermutlich Text-Alternativen (Alt-Texte) für nicht-textuelle Inhalte wie Bilder, '
                       'Grafiken und Icons. Dies verhindert die Nutzung durch Screenreader.',
            risk_euro=2000,
            recommendation='Fügen Sie beschreibende Alt-Texte für alle Bilder und Grafiken hinzu.',
            legal_basis='WCAG 2.1 Level A (1.1.1), BFSG §12',
            auto_fixable=False,
            is_missing=True
        ))
        
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='critical',
            title='WCAG 1.4.3: Kontrast-Verhältnis nicht ausreichend',
            description='Die Kontrast-Verhältnisse zwischen Text und Hintergrund erfüllen vermutlich nicht das erforderliche '
                       'Minimum von 4.5:1 (normaler Text) bzw. 3:1 (großer Text).',
            risk_euro=2000,
            recommendation='Stellen Sie ausreichende Kontraste sicher (mindestens 4.5:1 für normalen Text).',
            legal_basis='WCAG 2.1 Level AA (1.4.3), BFSG §12',
            auto_fixable=False,
            is_missing=True
        ))
        
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='critical',
            title='WCAG 2.1.1: Tastaturbedienung nicht vollständig',
            description='Die Website ist vermutlich nicht vollständig per Tastatur bedienbar. Alle Funktionen müssen '
                       'ohne Maus zugänglich sein.',
            risk_euro=2500,
            recommendation='Stellen Sie sicher, dass alle interaktiven Elemente per Tastatur erreichbar und bedienbar sind.',
            legal_basis='WCAG 2.1 Level A (2.1.1), BFSG §12',
            auto_fixable=False,
            is_missing=True
        ))
        
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='critical',
            title='WCAG 2.4.7: Focus-Sichtbarkeit nicht gewährleistet',
            description='Der Tastaturfokus ist vermutlich nicht durchgängig sichtbar. Nutzer müssen erkennen können, '
                       'welches Element aktuell den Fokus hat.',
            risk_euro=1500,
            recommendation='Fügen Sie deutliche visuelle Fokus-Indikatoren für alle interaktiven Elemente hinzu.',
            legal_basis='WCAG 2.1 Level AA (2.4.7), BFSG §12',
            auto_fixable=False,
            is_missing=True
        ))
        
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='warning',
            title='WCAG 4.1.2: ARIA-Labels und Rollen fehlen',
            description='Es fehlen vermutlich ARIA-Labels und semantische Rollen für interaktive Komponenten. '
                       'Dies erschwert die Nutzung mit assistiven Technologien.',
            risk_euro=1500,
            recommendation='Fügen Sie ARIA-Labels, Rollen und Properties für alle interaktiven Elemente hinzu.',
            legal_basis='WCAG 2.1 Level A (4.1.2), BFSG §12',
            auto_fixable=False,
            is_missing=True
        ))
        
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='warning',
            title='WCAG 1.3.1: Semantisches HTML nicht genutzt',
            description='Die Website nutzt vermutlich kein semantisches HTML5 (header, nav, main, aside, footer). '
                       'Dies erschwert die Navigation mit Screenreadern.',
            risk_euro=1000,
            recommendation='Verwenden Sie semantische HTML5-Elemente zur Strukturierung der Seite.',
            legal_basis='WCAG 2.1 Level A (1.3.1), BFSG §12',
            auto_fixable=False,
            is_missing=True
        ))
    else:
        # Widget vorhanden, führe detaillierte Checks durch
        # 2. Alt-Texte prüfen (mit Screenshot & AI)
        alt_issues = await _check_alt_texts_enhanced(url, soup, session)
        issues.extend(alt_issues)
        
        # 3. ARIA-Labels prüfen
        aria_issues = await _check_aria_labels(soup)
        issues.extend(aria_issues)
        
        # 4. Semantisches HTML prüfen
        semantic_issues = await _check_semantic_html(soup)
        issues.extend(semantic_issues)
        
        # 5. Tastaturbedienung prüfen
        keyboard_issues = await _check_keyboard_navigation(soup)
        issues.extend(keyboard_issues)
        
        # 6. Kontraste prüfen (basiert auf inline-styles)
        contrast_issues = await _check_color_contrast(soup)
        issues.extend(contrast_issues)
    
    return [asdict(issue) for issue in issues]

async def _check_accessibility_widget(soup: BeautifulSoup) -> BarrierefreiheitIssue | None:
    """
    Prüft ob ein Accessibility-Widget/Tool vorhanden ist
    
    Bekannte Widgets:
    - UserWay
    - AccessiBe
    - Eye-Able
    - EqualWeb
    - AudioEye
    """
    widget_patterns = [
        r'userway',
        r'accessibe',
        r'eye-able',
        r'equalweb',
        r'audioeye',
        r'accessibility.*widget',
        r'a11y.*widget'
    ]
    
    # Suche in Scripts
    scripts = soup.find_all('script', src=True)
    for script in scripts:
        src = script.get('src', '').lower()
        for pattern in widget_patterns:
            if re.search(pattern, src, re.I):
                return None  # Widget gefunden, kein Issue
    
    # Suche in Script-Content
    script_contents = soup.find_all('script', src=False)
    for script in script_contents:
        content = script.string or ''
        for pattern in widget_patterns:
            if re.search(pattern, content, re.I):
                return None
    
    # Suche nach DIV-Containern mit accessibility-Klassen
    accessibility_divs = soup.find_all(['div', 'aside'], class_=re.compile(r'accessibility|a11y|barrier.*free', re.I))
    if accessibility_divs:
        return None
    
    # Kein Widget gefunden - HAUPTELEMENT FEHLT
    return BarrierefreiheitIssue(
        category='barrierefreiheit',
        severity='critical',
        title='Kein Barrierefreiheits-Tool/Widget gefunden',
        description='Es wurde kein Accessibility-Widget (UserWay, AccessiBe, Eye-Able etc.) gefunden. '
                    'Solche Tools erleichtern die Barrierefreiheit erheblich durch Funktionen wie Schriftvergrößerung, '
                    'Kontraständerung, Vorlese-Funktion etc.',
        risk_euro=8000,
        recommendation='Implementieren Sie ein Accessibility-Widget wie UserWay, AccessiBe oder Eye-Able. '
                      'Diese bieten sofortige Barrierefreiheit-Features für Ihre Nutzer.',
        legal_basis='BFSG §12-15',
        auto_fixable=True,
        is_missing=True  # ✅ Hauptelement fehlt komplett
    )

async def _check_alt_texts(soup: BeautifulSoup) -> List[BarrierefreiheitIssue]:
    """Prüft ob alle Bilder Alt-Texte haben (Legacy-Version ohne Screenshots)"""
    issues = []
    
    images = soup.find_all('img')
    if not images:
        return issues
    
    images_without_alt = []
    for img in images:
        alt = img.get('alt', '').strip()
        src = img.get('src', '')
        
        # Skip decorative images (aria-hidden, role="presentation")
        if img.get('aria-hidden') == 'true' or img.get('role') == 'presentation':
            continue
        
        # Skip tracking pixels
        if any(x in src.lower() for x in ['pixel', 'tracking', '1x1', 'analytics']):
            continue
        
        if not alt:
            images_without_alt.append(src[:50])  # Truncate long URLs
    
    if images_without_alt:
        count = len(images_without_alt)
        examples = ', '.join(images_without_alt[:3])
        
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='warning' if count < 5 else 'critical',
            title=f'{count} Bilder ohne Alt-Text',
            description=f'{count} Bilder haben keinen Alt-Text für Screenreader. '
                       f'Beispiele: {examples}{"..." if count > 3 else ""}. '
                       f'Alt-Texte sind essentiell für blinde und sehbehinderte Nutzer.',
            risk_euro=500 * min(count, 5),  # Max 2500€
            recommendation='Fügen Sie aussagekräftige alt-Attribute zu allen Bildern hinzu. '
                          'Beschreiben Sie, was auf dem Bild zu sehen ist.',
            legal_basis='BFSG §12, WCAG 2.1 Level AA',
            auto_fixable=False
        ))
    
    return issues


async def _check_alt_texts_enhanced(url: str, soup: BeautifulSoup, session=None) -> List[BarrierefreiheitIssue]:
    """
    Erweiterte Alt-Text-Prüfung mit Screenshots und AI-Vorschlägen
    
    Args:
        url: URL der zu prüfenden Seite
        soup: BeautifulSoup-Objekt der Seite
        session: HTTP-Session für API-Calls
        
    Returns:
        Liste von detaillierten Issues mit Screenshots und AI-Vorschlägen
    """
    issues = []
    
    # Importiere Services dynamisch (lazy import)
    try:
        from ..screenshot_service import ScreenshotService
        from ..ai_alt_text_generator import AIAltTextGenerator
        screenshot_available = True
    except ImportError as e:
        logger.warning(f"Screenshot/AI services not available: {e}")
        screenshot_available = False
        # Fallback auf legacy Check
        return await _check_alt_texts(soup)
    
    # Nutze Screenshot-Service wenn verfügbar
    screenshot_data = []
    if screenshot_available:
        try:
            async with ScreenshotService() as screenshot_svc:
                screenshot_data = await screenshot_svc.capture_images(url)
                logger.info(f"📸 Captured {len(screenshot_data)} images")
        except Exception as e:
            logger.warning(f"Screenshot capture failed: {e}, falling back to basic check")
            return await _check_alt_texts(soup)
    
    # Erstelle Issues für jedes Bild ohne Alt-Text
    for img_data in screenshot_data:
        if not img_data.get('has_alt') and not img_data.get('is_decorative'):
            # Bild hat keinen Alt-Text und ist nicht dekorativ
            
            src = img_data.get('src', '')
            suggested_alt = img_data.get('suggested_alt', 'Bild')
            
            # Erstelle detailliertes Issue
            issues.append(BarrierefreiheitIssue(
                category='barrierefreiheit',
                severity='error',
                title=f'Bild ohne Alt-Text',
                description=f'Dieses Bild hat keinen Alt-Text und ist nicht als dekorativ markiert. '
                           f'Screenreader können das Bild nicht beschreiben.',
                risk_euro=500,
                recommendation=f'Fügen Sie einen Alt-Text hinzu. AI-Vorschlag: "{suggested_alt}"',
                legal_basis='WCAG 2.1 Level A (1.1.1), BFSG §12',
                auto_fixable=True,  # Via Widget fixbar!
                screenshot_url=img_data.get('screenshot_data_url'),
                element_html=f'<img src="{src}" ... />',
                fix_code=f'<img src="{src}" alt="{suggested_alt}" />',
                suggested_alt=suggested_alt,
                image_src=src,
                metadata={
                    'width': img_data.get('width'),
                    'height': img_data.get('height'),
                    'context': img_data.get('context'),
                    'is_visible': img_data.get('is_visible'),
                    'has_title': img_data.get('has_title'),
                    'has_aria_label': img_data.get('has_aria_label')
                }
            ))
    
    # Wenn viele Bilder ohne Alt-Text: Erstelle Zusammenfassung
    if len(issues) > 10:
        summary = BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='critical',
            title=f'{len(issues)} Bilder ohne Alt-Text gefunden',
            description=f'Die Seite enthält {len(issues)} Bilder ohne Alt-Text. '
                       f'Dies ist ein kritisches Barrierefreiheitsproblem.',
            risk_euro=min(len(issues) * 500, 5000),  # Max 5000€
            recommendation='Nutzen Sie das Complyo Smart-Widget für automatische Alt-Text-Fixes.',
            legal_basis='WCAG 2.1 Level A (1.1.1), BFSG §12',
            auto_fixable=True
        )
        issues.insert(0, summary)  # Am Anfang einfügen
    
    return issues

async def _check_aria_labels(soup: BeautifulSoup) -> List[BarrierefreiheitIssue]:
    """Prüft ARIA-Labels für interaktive Elemente"""
    issues = []
    
    # Prüfe Buttons ohne Text/Label
    buttons = soup.find_all(['button', 'a'], role=re.compile(r'button|menuitem', re.I))
    buttons_without_label = []
    
    for button in buttons:
        text = button.get_text(strip=True)
        aria_label = button.get('aria-label', '').strip()
        aria_labelledby = button.get('aria-labelledby', '').strip()
        title = button.get('title', '').strip()
        
        if not any([text, aria_label, aria_labelledby, title]):
            # Button hat kein Label - problematisch für Screenreader
            onclick = button.get('onclick', '')[:30]
            buttons_without_label.append(onclick if onclick else 'unknown')
    
    if buttons_without_label:
        count = len(buttons_without_label)
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='warning',
            title=f'{count} Buttons ohne Label',
            description=f'{count} interaktive Elemente (Buttons) haben weder Text noch ARIA-Label. '
                       f'Screenreader können diese Elemente nicht vorlesen.',
            risk_euro=300 * min(count, 5),
            recommendation='Fügen Sie aria-label oder aussagekräftigen Text zu allen Buttons hinzu.',
            legal_basis='BFSG §12, WCAG 2.1 (Name, Role, Value)',
            auto_fixable=False
        ))
    
    # Prüfe Forms ohne Labels
    inputs = soup.find_all(['input', 'select', 'textarea'])
    inputs_without_label = []
    
    for inp in inputs:
        input_type = inp.get('type', 'text')
        if input_type in ['hidden', 'submit', 'button']:
            continue  # Skip non-input types
        
        input_id = inp.get('id', '')
        aria_label = inp.get('aria-label', '').strip()
        aria_labelledby = inp.get('aria-labelledby', '').strip()
        title = inp.get('title', '').strip()
        placeholder = inp.get('placeholder', '').strip()
        
        # Check if there's a <label for="..."> element
        has_label = False
        if input_id:
            label = soup.find('label', attrs={'for': input_id})
            if label:
                has_label = True
        
        if not any([has_label, aria_label, aria_labelledby, title]) and not placeholder:
            inputs_without_label.append(input_type)
    
    if inputs_without_label:
        count = len(inputs_without_label)
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='warning',
            title=f'{count} Formular-Felder ohne Label',
            description=f'{count} Eingabefelder haben kein zugeordnetes Label. '
                       f'Screenreader-Nutzer wissen nicht, was sie eingeben sollen.',
            risk_euro=400 * min(count, 5),
            recommendation='Verwenden Sie <label for="..."> oder aria-label für alle Formularfelder.',
            legal_basis='BFSG §12, WCAG 2.1 (Labels or Instructions)',
            auto_fixable=False
        ))
    
    return issues

async def _check_semantic_html(soup: BeautifulSoup) -> List[BarrierefreiheitIssue]:
    """Prüft ob semantisches HTML verwendet wird"""
    issues = []
    
    # Prüfe auf wichtige semantische Elemente
    has_main = soup.find('main') is not None
    has_nav = soup.find('nav') is not None
    has_header = soup.find('header') is not None
    has_footer = soup.find('footer') is not None
    
    missing_elements = []
    if not has_main:
        missing_elements.append('<main>')
    if not has_nav:
        missing_elements.append('<nav>')
    if not has_header:
        missing_elements.append('<header>')
    if not has_footer:
        missing_elements.append('<footer>')
    
    if missing_elements:
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='warning',
            title='Fehlende semantische HTML-Elemente',
            description=f'Die Seite verwendet nicht alle wichtigen semantischen HTML5-Elemente: '
                       f'{", ".join(missing_elements)}. '
                       f'Diese helfen Screenreader-Nutzern bei der Navigation.',
            risk_euro=800,
            recommendation='Verwenden Sie semantische HTML5-Elemente für bessere Struktur und Barrierefreiheit.',
            legal_basis='BFSG §12, WCAG 2.1 (Info and Relationships)',
            auto_fixable=False
        ))
    
    # Prüfe Heading-Struktur
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    has_h1 = any(h.name == 'h1' for h in headings)
    
    if not has_h1:
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='warning',
            title='Keine H1-Überschrift gefunden',
            description='Die Seite hat keine H1-Überschrift. Eine klare Heading-Struktur ist wichtig für Screenreader.',
            risk_euro=300,
            recommendation='Fügen Sie eine H1-Überschrift mit dem Hauptthema der Seite hinzu.',
            legal_basis='BFSG §12, WCAG 2.1 (Headings and Labels)',
            auto_fixable=False
        ))
    
    return issues

async def _check_keyboard_navigation(soup: BeautifulSoup) -> List[BarrierefreiheitIssue]:
    """Prüft Tastaturbedienbarkeit"""
    issues = []
    
    # Prüfe interaktive Elemente mit tabindex=-1
    negative_tabindex = soup.find_all(attrs={'tabindex': '-1'})
    interactive_with_negative_tabindex = []
    
    for elem in negative_tabindex:
        if elem.name in ['a', 'button', 'input', 'select', 'textarea']:
            interactive_with_negative_tabindex.append(elem.name)
    
    if interactive_with_negative_tabindex:
        count = len(interactive_with_negative_tabindex)
        issues.append(BarrierefreiheitIssue(
            category='tastaturbedienung',
            severity='warning',
            title=f'{count} Elemente nicht per Tastatur erreichbar',
            description=f'{count} interaktive Elemente haben tabindex="-1" und sind daher nicht per Tastatur erreichbar.',
            risk_euro=500,
            recommendation='Entfernen Sie tabindex="-1" von interaktiven Elementen oder setzen Sie tabindex="0".',
            legal_basis='BFSG §12, WCAG 2.1 (Keyboard Accessible)',
            auto_fixable=False
        ))
    
    return issues

async def _check_color_contrast(soup: BeautifulSoup) -> List[BarrierefreiheitIssue]:
    """
    Prüft Farbkontraste (vereinfacht, nur für inline-styles)
    Eine vollständige Prüfung würde CSS-Parsing und Rendering benötigen
    """
    issues = []
    
    # Hinweis: Vollständige Kontrast-Prüfung ist komplex
    # Wir prüfen nur, ob Farben definiert sind
    elements_with_colors = soup.find_all(style=re.compile(r'color:|background-color:', re.I))
    
    if len(elements_with_colors) > 0:
        # Wir können hier keine echte Kontrast-Berechnung machen
        # Empfehlung für manuellen Check
        issues.append(BarrierefreiheitIssue(
            category='kontraste',
            severity='info',
            title='Kontrast-Prüfung empfohlen',
            description='Es wurden Farbdefinitionen gefunden. Bitte prüfen Sie manuell mit einem Tool wie '
                       'dem WCAG Contrast Checker, ob alle Texte ausreichend Kontrast haben (mind. 4.5:1).',
            risk_euro=0,
            recommendation='Verwenden Sie Tools wie WebAIM Contrast Checker oder axe DevTools.',
            legal_basis='BFSG §12, WCAG 2.1 Level AA (Contrast Minimum)',
            auto_fixable=False
        ))
    
    return issues

