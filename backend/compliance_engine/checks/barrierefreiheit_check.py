"""
Barrierefreiheit Check (BFSG)
Prüft Website auf Barrierefreiheitsstärkungsgesetz-Compliance

✨ NEU: Browser-basiertes Rendering für moderne JavaScript-Websites
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
import re
from urllib.parse import urljoin, urlparse
import logging
import aiohttp
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


async def check_barrierefreiheit_compliance_smart(url: str, html: str = None, session=None) -> List[Dict[str, Any]]:
    """
    🚀 SMART Barrierefreiheits-Check mit automatischer Browser-Erkennung
    
    Nutzt Browser-Rendering für Client-Side-gerenderte Websites (React, Vue, etc.)
    Nutzt einfaches HTTP für Server-rendered Websites (schneller)
    
    Args:
        url: URL der zu prüfenden Website
        html: Optional bereits gefetchtes HTML (sonst wird es geholt)
        session: Optional aiohttp Session für Requests
        
    Returns:
        Liste von Issues (wie check_barrierefreiheit_compliance)
    """
    from ..browser_renderer import smart_fetch_html, detect_client_rendering
    
    # ✅ FIX: URL-Normalisierung (falls direkt aufgerufen, ohne Scanner)
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        logger.info(f"✅ URL normalized to: {url}")
    
    logger.info(f"🔍 Smart Barrierefreiheits-Check für: {url}")
    
    try:
        # 1. Hole HTML (smart mit Browser wenn nötig)
        if html is None:
            # Fetch initial HTML
            import ssl
            import certifi
            
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as temp_session:
                async with temp_session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    html = await response.text()
        
        # 2. Prüfe ob Browser nötig ist
        needs_browser, reason = detect_client_rendering(html)
        
        if needs_browser:
            logger.info(f"🌐 Browser needed: {reason}")
            # Hole vollständig gerendertes HTML
            html, metadata = await smart_fetch_html(url, html)
            logger.info(f"✅ Browser rendering completed: {metadata.get('rendering_type', 'unknown')}")
        else:
            logger.info(f"⚡ Server-rendered detected, using simple HTML")
        
        # 3. Führe normalen Check mit (potenziell gerenderten) HTML durch
        soup = BeautifulSoup(html, 'html.parser')
        issues = await check_barrierefreiheit_compliance(url, soup, session)
        
        # 4. Füge Metadaten hinzu
        for issue_dict in issues:
            if 'metadata' not in issue_dict:
                issue_dict['metadata'] = {}
            issue_dict['metadata']['used_browser_rendering'] = needs_browser
            issue_dict['metadata']['detection_reason'] = reason
        
        return issues
        
    except Exception as e:
        logger.error(f"❌ Smart compliance check failed: {e}")
        # Fallback zu normalem Check
        logger.info("📋 Falling back to simple check")
        soup = BeautifulSoup(html if html else "", 'html.parser')
        return await check_barrierefreiheit_compliance(url, soup, session)


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
    Umfassender Barrierefreiheits-Check mit Multi-Page Scanning
    
    Prüft:
    1. Accessibility-Widget/Tool vorhanden
    2. Kontrast-Verhältnisse
    3. Alt-Texte für Bilder (ALLE Seiten!)
    4. ARIA-Labels und Rollen
    5. Tastaturbedienung
    6. Semantisches HTML
    7. Screenreader-Kompatibilität
    """
    # ✅ FIX: URL-Normalisierung (falls direkt aufgerufen)
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        logger.info(f"✅ URL normalized to: {url}")
    
    issues = []
    
    # 1. Check für Accessibility-Tools/Widgets
    widget_issue = await _check_accessibility_widget(soup)
    if widget_issue:
        issues.append(widget_issue)

        # Nur konkret prüfbare WCAG-Kriterien direkt am vorliegenden HTML auswerten
        # (keine pauschalen "vermutlich fehlt"-Issues)

        # WCAG 1.1.1: Bilder ohne Alt-Text — pro Bild ein eigenes Issue mit KI-Vorschlag
        alt_issues = await _check_alt_texts_enhanced(url, soup, session)
        issues.extend(alt_issues)

        # WCAG 3.1.1: Sprache nicht gesetzt
        html_tag = soup.find('html')
        if not html_tag or not html_tag.get('lang'):
            issues.append(BarrierefreiheitIssue(
                category='barrierefreiheit',
                severity='critical',
                title='WCAG 3.1.1: Sprache der Seite nicht angegeben (lang-Attribut fehlt)',
                description='Das <html>-Tag hat kein lang-Attribut. Screenreader können die Sprache '
                           'nicht korrekt erkennen.',
                risk_euro=1000,
                recommendation='Fügen Sie lang="de" (oder die jeweilige Sprache) zum <html>-Tag hinzu.',
                legal_basis='WCAG 2.1 Level A (3.1.1), BFSG §12',
                auto_fixable=True,
                is_missing=False
            ))

        # WCAG 4.1.2: Inputs ohne Label
        inputs_without_label = []
        for inp in soup.find_all(['input', 'select', 'textarea']):
            inp_id = inp.get('id')
            inp_type = inp.get('type', '').lower()
            if inp_type in ('hidden', 'submit', 'button', 'reset'):
                continue
            has_label = (
                inp.get('aria-label') or
                inp.get('aria-labelledby') or
                inp.get('title') or
                (inp_id and soup.find('label', attrs={'for': inp_id}))
            )
            if not has_label:
                inputs_without_label.append(inp)
        if inputs_without_label:
            issues.append(BarrierefreiheitIssue(
                category='barrierefreiheit',
                severity='warning',
                title=f'WCAG 4.1.2: {len(inputs_without_label)} Formularfeld(er) ohne Label',
                description=f'{len(inputs_without_label)} Eingabefeld(er) haben kein zugehöriges Label. '
                           'Screenreader können den Zweck des Felds nicht vermitteln.',
                risk_euro=1500,
                recommendation='Verknüpfen Sie jedes Formularfeld mit einem <label for="...">-Element oder aria-label.',
                legal_basis='WCAG 2.1 Level A (4.1.2), BFSG §12',
                auto_fixable=False,
                is_missing=False
            ))

        # WCAG 1.3.1: Keine semantischen HTML5-Strukturelemente
        has_semantic = bool(soup.find(['main', 'nav', 'header', 'footer', 'aside', 'article', 'section']))
        if not has_semantic:
            issues.append(BarrierefreiheitIssue(
                category='barrierefreiheit',
                severity='warning',
                title='WCAG 1.3.1: Keine semantischen HTML5-Strukturelemente gefunden',
                description='Die Seite verwendet keine semantischen HTML5-Elemente (main, nav, header, footer). '
                           'Dies erschwert die Navigation mit Screenreadern.',
                risk_euro=1000,
                recommendation='Verwenden Sie semantische HTML5-Elemente zur Strukturierung der Seite.',
                legal_basis='WCAG 2.1 Level A (1.3.1), BFSG §12',
                auto_fixable=False,
                is_missing=False
            ))

    else:
        # Widget vorhanden — führe detaillierte Checks durch
        # Multi-Page Scan für Bilder
        logger.info(f"🔍 Starting multi-page accessibility scan for {url}")
        if session:
            all_pages = await _discover_pages(url, session)
            logger.info(f"📄 Discovered {len(all_pages)} pages to scan")
            for page_url in all_pages[:50]:
                try:
                    page_content = await _fetch_page(page_url, session)
                    if page_content:
                        page_soup = BeautifulSoup(page_content, 'html.parser')
                        page_issues = await _check_images_for_alt_text(page_url, page_soup)
                        issues.extend(page_issues)
                        logger.info(f"  ✓ {page_url}: {len(page_issues)} issues found")
                except Exception as e:
                    logger.warning(f"  ✗ Failed to scan {page_url}: {e}")
                    continue
        else:
            alt_issues = await _check_alt_texts_enhanced(url, soup, session)
            issues.extend(alt_issues)

    # Detaillierte WCAG-Struktur-Checks laufen immer — unabhängig vom Widget
    aria_issues = await _check_aria_labels(soup)
    issues.extend(aria_issues)

    semantic_issues = await _check_semantic_html(soup)
    issues.extend(semantic_issues)

    keyboard_issues = await _check_keyboard_navigation(soup)
    issues.extend(keyboard_issues)

    contrast_issues = await _check_color_contrast(soup)
    issues.extend(contrast_issues)
    
    # BFSG §14: Barrierefreiheitserklärung (für B2C-Dienste ab 28.06.2025 Pflicht)
    html_text_full = str(soup).lower()
    has_a11y_statement = bool(re.search(
        r'barrierefreiheit(?:serkl[äa]rung)?|accessibility.statement|erkl[äa]rung.zur.barrierefreiheit',
        html_text_full, re.I
    ))
    # Prüfe auch ob es einen Link zur Erklärung gibt
    if not has_a11y_statement:
        for a in soup.find_all('a', href=True):
            href = a.get('href', '').lower()
            text = a.get_text(strip=True).lower()
            if 'barrierefreiheit' in href or 'accessibility' in href or 'barrierefreiheit' in text:
                has_a11y_statement = True
                break

    if not has_a11y_statement:
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='warning',
            title='Barrierefreiheitserklärung fehlt (BFSG §14)',
            description=(
                'Es wurde keine Barrierefreiheitserklärung gefunden. Ab 28.06.2025 sind '
                'B2C-Dienste (Online-Shops, Buchungssysteme, digitale Services) verpflichtet, '
                'eine Erklärung zur Barrierefreiheit zu veröffentlichen, die den Konformitätsstatus, '
                'bekannte Mängel und einen Feedback-Mechanismus enthält.'
            ),
            risk_euro=2000,
            recommendation=(
                'Erstellen Sie eine Barrierefreiheitserklärung gemäß BFSG §14 und verlinken Sie diese '
                'im Footer. Die Erklärung muss enthalten: Konformitätsstatus (WCAG 2.1 AA), '
                'nicht konforme Bereiche, Alternativen, Feedback-Kontakt.'
            ),
            legal_basis='BFSG §14, EU-Richtlinie 2019/882 (European Accessibility Act)',
            auto_fixable=False,
            is_missing=False,
        ))

    # WCAG 3.1.1: Sprache der Seite (lang-Attribut)
    html_tag = soup.find('html')
    if html_tag and not html_tag.get('lang'):
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='warning',
            title='WCAG 3.1.1: Sprache der Seite nicht angegeben (lang-Attribut fehlt)',
            description=(
                'Das HTML-Element hat kein lang-Attribut. Screenreader können die Sprache '
                'nicht automatisch erkennen und lesen den Text möglicherweise mit falscher Aussprache vor.'
            ),
            risk_euro=500,
            recommendation='Fügen Sie dem <html>-Element ein lang-Attribut hinzu, z.B. <html lang="de">.',
            legal_basis='WCAG 2.1 Level A (3.1.1), BFSG §12',
            auto_fixable=True,
            is_missing=False,
        ))

    # WCAG 2.4.2: Seitentitel vorhanden und sinnvoll
    title_tag = soup.find('title')
    if not title_tag or not title_tag.get_text(strip=True):
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='warning',
            title='WCAG 2.4.2: Seitentitel fehlt oder ist leer',
            description=(
                'Die Seite hat keinen oder einen leeren <title>-Tag. '
                'Screenreader-Nutzer hören den Seitentitel beim Laden — er ist essenziell zur Orientierung.'
            ),
            risk_euro=300,
            recommendation='Fügen Sie einen aussagekräftigen <title> hinzu, der Seite und Website beschreibt.',
            legal_basis='WCAG 2.1 Level A (2.4.2), BFSG §12',
            auto_fixable=True,
            is_missing=False,
        ))

    # WCAG 2.4.1: Skip-Navigation-Link
    has_skip_link = bool(soup.find('a', href=re.compile(r'^#(main|content|inhalt|skip)', re.I)))
    if not has_skip_link:
        # Prüfe auch auf aria-label skip patterns
        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True).lower()
            if re.search(r'skip.*(content|navigation|main)|zum inhalt|zur navigation springen', text):
                has_skip_link = True
                break
    if not has_skip_link:
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='info',
            title='WCAG 2.4.1: Kein Skip-Navigation-Link gefunden',
            description=(
                'Es wurde kein "Zum Inhalt springen"-Link gefunden. '
                'Tastatur- und Screenreader-Nutzer müssen ohne diesen Link die gesamte Navigation '
                'auf jeder Seite durchlaufen, bevor sie zum Hauptinhalt gelangen.'
            ),
            risk_euro=200,
            recommendation='Fügen Sie am Seitenanfang einen versteckten Skip-Link ein: <a href="#main" class="skip-link">Zum Inhalt springen</a>.',
            legal_basis='WCAG 2.1 Level A (2.4.1), BFSG §12',
            auto_fixable=True,
            is_missing=False,
        ))

    # WCAG 2.4.4: Nichtssagende Linktexte ("hier klicken", "mehr", "weiterlesen")
    vague_link_patterns = re.compile(
        r'^(hier|here|click here|hier klicken|mehr|more|weiterlesen|read more|details|link|weiter|next|›|»|\.{3})$',
        re.I
    )
    vague_links = []
    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        aria = a.get('aria-label', '').strip()
        title_attr = a.get('title', '').strip()
        if text and vague_link_patterns.match(text) and not aria and not title_attr:
            vague_links.append(text)
    if vague_links:
        count = len(vague_links)
        issues.append(BarrierefreiheitIssue(
            category='barrierefreiheit',
            severity='warning',
            title=f'WCAG 2.4.4: {count} nichtssagende Linktexte gefunden',
            description=(
                f'{count} Links haben nichtssagende Texte wie "hier", "mehr", "weiterlesen". '
                'Screenreader-Nutzer navigieren häufig durch Sprung von Link zu Link — '
                'ohne Kontext sind diese Links unverständlich.'
            ),
            risk_euro=500,
            recommendation=(
                'Ersetzen Sie vage Linktexte durch beschreibende Alternativen, z.B. '
                '"Mehr über unsere Datenschutzrichtlinie" statt "hier". '
                'Oder ergänzen Sie aria-label mit dem vollständigen Kontext.'
            ),
            legal_basis='WCAG 2.1 Level A (2.4.4), BFSG §12',
            auto_fixable=False,
            is_missing=False,
        ))

    return [asdict(issue) for issue in issues]

async def _check_accessibility_widget(soup: BeautifulSoup) -> BarrierefreiheitIssue | None:
    """
    Prüft ob ein Accessibility-Widget/Tool vorhanden ist
    
    Bekannte Widgets:
    - Complyo (eigenes Widget)
    - UserWay
    - AccessiBe
    - Eye-Able
    - EqualWeb
    - AudioEye
    - Recite Me
    - UserZoom
    - Level Access
    """
    widget_patterns = [
        # Complyo eigenes Widget
        r'complyo',
        r'api\.complyo\.tech',
        r'api\.complyo\.de',
        r'complyo.*accessibility',
        r'complyo.*widget',
        r'complyo.*a11y',
        
        # Bekannte Drittanbieter
        r'userway',
        r'accessibe',
        r'acsbapp',
        r'eye-able',
        r'eyeable',
        r'equalweb',
        r'audioeye',
        r'reciteme',
        r'userzoom',
        r'levelaccess',
        r'adally',
        r'max-access',
        r'essl\.ai',
        r'silktide',
        r'siteimprove',
        r'monsido',
        r'texthelp',
        r'readspeaker',
        r'browsealoud',
        r'reciteme',
        r'wcagchecker',
        r'ablenet',
        r'axesslab',
        r'ally\.js',
        
        # Generische Patterns
        r'accessibility.*widget',
        r'accessibility.*tool',
        r'accessibility.*toolbar',
        r'a11y.*widget',
        r'a11y.*tool',
        r'barrier.*free.*widget',
        r'wcag.*widget',
        r'wcag.*toolbar',
    ]
    
    # Suche in Scripts mit src
    scripts = soup.find_all('script', src=True)
    for script in scripts:
        src = script.get('src', '').lower()
        for pattern in widget_patterns:
            if re.search(pattern, src, re.I):
                return None

        # Complyo-spezifische Attribute NUR wenn src auch auf ein Accessibility-Widget deutet
        script_src = script.get('src', '').lower()
        has_site_id = bool(script.get('data-site-id'))
        has_auto_fix = bool(script.get('data-auto-fix'))
        if has_auto_fix and 'accessibility' in script_src:
            return None
        if has_site_id and ('accessibility' in script_src or 'complyo' in script_src or 'widget' in script_src):
            return None
    
    # Suche nach Scripts mit Complyo-spezifischen Attributen (auch ohne src)
    for script in soup.find_all('script'):
        if script.get('data-site-id') and ('complyo' in str(script).lower() or 'accessibility' in str(script).lower()):
            return None
    
    # Suche in Preload-Links (Next.js afterInteractive Scripts)
    for link in soup.find_all('link', href=True):
        href = link.get('href', '').lower()
        for pattern in widget_patterns:
            if re.search(pattern, href, re.I):
                return None
    
    # NEU: Suche im gesamten HTML nach Complyo Widget-URLs (inkl. Preload-Links)
    html_text = str(soup).lower()
    if 'api.complyo.tech/api/widgets/accessibility' in html_text or 'api.complyo.de/api/widgets/accessibility' in html_text:
        return None  # Complyo Widget URL im HTML gefunden (z.B. als <link rel="preload">)

    # Zusätzlich: Suche in allen link-Tags unabhängig von rel-Attribut
    for link in soup.find_all('link', href=True):
        href = link.get('href', '').lower()
        if 'accessibility' in href and ('complyo' in href or 'userway' in href or 'accessibe' in href or 'eye-able' in href):
            return None
    
    # Suche in Script-Content
    script_contents = soup.find_all('script', src=False)
    for script in script_contents:
        content = script.string or ''
        for pattern in widget_patterns:
            if re.search(pattern, content, re.I):
                return None
    
    # Suche nach DIV-Containern mit accessibility-Klassen (inkl. Complyo)
    accessibility_divs = soup.find_all(
        ['div', 'aside', 'section'], 
        class_=re.compile(r'accessibility|a11y|barrier.*free|complyo', re.I)
    )
    if accessibility_divs:
        return None
    
    # Suche nach IDs mit accessibility-Bezug
    accessibility_ids = soup.find_all(
        id=re.compile(r'accessibility|a11y|complyo.*widget|complyo.*a11y', re.I)
    )
    if accessibility_ids:
        return None
    
    # NEU: Suche nach Floating-Buttons (typisch für Accessibility-Widgets)
    # Diese haben oft: fixed position, aria-label mit "Barrierefreiheit" oder "Accessibility"
    floating_buttons = soup.find_all(
        'button',
        attrs={'aria-label': re.compile(r'barrierefreiheit|accessibility|a11y', re.I)}
    )
    if floating_buttons:
        return None
    
    # NEU: Suche nach Buttons mit Settings-Icons (Complyo Widget Pattern)
    # Unser Widget hat: Settings Icon + aria-label "Barrierefreiheits-Einstellungen"
    setting_buttons = soup.find_all(
        'button',
        class_=re.compile(r'fixed|floating|accessibility', re.I)
    )
    for btn in setting_buttons:
        aria = btn.get('aria-label', '').lower()
        if 'barrierefreiheit' in aria or 'accessibility' in aria or 'einstellung' in aria:
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
                severity='critical',
                title=f'WCAG 1.1.1: Bild ohne Alt-Text',
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
    
    # Cookie-Banner Container identifizieren (Inputs darin werden übersprungen)
    cookie_banner_selectors = [
        soup.find(id=re.compile(r'cookie|consent|gdpr|ccm|complyo', re.I)),
        soup.find(class_=re.compile(r'cookie.*banner|cookie.*consent|consent.*banner|ccm|complyo.*cookie', re.I)),
    ]
    cookie_containers = [c for c in cookie_banner_selectors if c is not None]
    
    for inp in inputs:
        input_type = inp.get('type', 'text')
        if input_type in ['hidden', 'submit', 'button', 'image', 'reset']:
            continue  # Skip non-labelable types
        
        # Skip inputs inside known cookie/consent containers
        in_cookie_banner = any(
            cookie_container and inp in cookie_container.find_all(['input', 'select', 'textarea'])
            for cookie_container in cookie_containers
        )
        if in_cookie_banner:
            continue
        
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
        
        # Check if the input is wrapped inside a <label> element (implicit label pattern)
        if not has_label:
            parent = inp.parent
            while parent and parent.name not in ['body', 'form', 'div', 'section']:
                if parent.name == 'label':
                    has_label = True
                    break
                parent = parent.parent
        
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


# ============================================================================
# Multi-Page Scanning Helper Functions
# ============================================================================

async def _discover_pages(base_url: str, session: aiohttp.ClientSession, max_pages: int = 50) -> List[str]:
    """
    Entdeckt alle Seiten einer Website (via Sitemap oder Link-Following)
    
    Args:
        base_url: Die Basis-URL der Website
        session: HTTP-Session für Requests
        max_pages: Maximale Anzahl zu scannender Seiten
        
    Returns:
        Liste von URLs
    """
    pages = set()
    pages.add(base_url)  # Hauptseite immer dabei
    
    # 1. Versuche Sitemap zu laden
    sitemap_urls = await _get_sitemap_urls(base_url, session)
    if sitemap_urls:
        logger.info(f"📄 Found {len(sitemap_urls)} URLs in sitemap")
        pages.update(sitemap_urls[:max_pages])
    else:
        # 2. Fallback: Crawle Links rekursiv (begrenzt)
        logger.info("📄 No sitemap found, crawling links...")
        crawled_urls = await _crawl_links_recursive(base_url, session, max_depth=2, max_pages=max_pages)
        pages.update(crawled_urls)
    
    # Begrenze auf max_pages
    return list(pages)[:max_pages]


async def _get_sitemap_urls(base_url: str, session: aiohttp.ClientSession) -> List[str]:
    """
    Versucht URLs aus sitemap.xml zu extrahieren
    
    Args:
        base_url: Die Basis-URL der Website
        session: HTTP-Session
        
    Returns:
        Liste von URLs aus der Sitemap
    """
    sitemap_locations = [
        f"{base_url}/sitemap.xml",
        f"{base_url}/sitemap_index.xml",
        f"{base_url}/sitemap/sitemap.xml",
    ]
    
    for sitemap_url in sitemap_locations:
        try:
            async with session.get(sitemap_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse XML
                    try:
                        root = ET.fromstring(content)
                        
                        # Namespace handling
                        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                        
                        # Extrahiere URLs
                        urls = []
                        for url_elem in root.findall('.//sm:loc', ns):
                            if url_elem.text:
                                urls.append(url_elem.text)
                        
                        # Fallback ohne Namespace
                        if not urls:
                            for url_elem in root.findall('.//{*}loc'):
                                if url_elem.text:
                                    urls.append(url_elem.text)
                        
                        if urls:
                            logger.info(f"✓ Found sitemap at {sitemap_url} with {len(urls)} URLs")
                            return urls
                    except ET.ParseError as e:
                        logger.debug(f"Failed to parse XML from {sitemap_url}: {e}")
                        continue
        except Exception as e:
            logger.debug(f"Failed to fetch sitemap from {sitemap_url}: {e}")
            continue
    
    return []


async def _crawl_links_recursive(
    base_url: str,
    session: aiohttp.ClientSession,
    max_depth: int = 2,
    max_pages: int = 50
) -> List[str]:
    """
    Crawlt Links rekursiv (begrenzt)
    
    Args:
        base_url: Die Basis-URL
        session: HTTP-Session
        max_depth: Maximale Crawl-Tiefe
        max_pages: Maximale Anzahl Seiten
        
    Returns:
        Liste von gefundenen URLs
    """
    visited = set()
    to_visit = [(base_url, 0)]  # (url, depth)
    found_urls = []
    
    base_domain = urlparse(base_url).netloc
    
    while to_visit and len(found_urls) < max_pages:
        current_url, depth = to_visit.pop(0)
        
        if current_url in visited or depth > max_depth:
            continue
        
        visited.add(current_url)
        found_urls.append(current_url)
        
        # Hole Links von dieser Seite
        try:
            content = await _fetch_page(current_url, session)
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(current_url, href)
                    
                    # Nur Links der gleichen Domain
                    if urlparse(absolute_url).netloc == base_domain:
                        # Filter: Nur HTML-Seiten (keine PDFs, Bilder, etc.)
                        if not any(absolute_url.endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.gif', '.zip', '.doc']):
                            if absolute_url not in visited:
                                to_visit.append((absolute_url, depth + 1))
        except Exception as e:
            logger.debug(f"Failed to crawl {current_url}: {e}")
            continue
    
    return found_urls


async def _fetch_page(url: str, session: aiohttp.ClientSession) -> Optional[str]:
    """
    Lädt den HTML-Inhalt einer Seite
    
    Args:
        url: Die URL der Seite
        session: HTTP-Session
        
    Returns:
        HTML-Inhalt oder None bei Fehler
    """
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        logger.debug(f"Failed to fetch {url}: {e}")
    
    return None


async def _check_images_for_alt_text(url: str, soup: BeautifulSoup) -> List[BarrierefreiheitIssue]:
    """
    Findet Bilder ohne Alt-Text und bereitet Daten für KI-Alt-Text-Generation vor
    
    Args:
        url: URL der Seite
        soup: BeautifulSoup-Objekt der Seite
        
    Returns:
        Liste von Issues für Bilder ohne Alt-Text
    """
    issues = []
    
    for img in soup.find_all('img'):
        img_src = img.get('src', '')
        alt_text = img.get('alt')
        
        # Skip decorative images
        if img.get('role') == 'presentation' or img.get('aria-hidden') == 'true':
            continue
        
        # Skip tracking pixels and tiny images
        if any(x in img_src.lower() for x in ['pixel', 'tracking', '1x1', 'analytics']):
            continue
        
        if not alt_text or alt_text.strip() == '':
            # Sammle Kontext für KI-Generierung
            page_title = soup.find('title').get_text() if soup.find('title') else ''
            surrounding_text = _get_surrounding_text(img, soup)
            filename = img_src.split('/')[-1] if '/' in img_src else img_src
            
            context = {
                'page_url': url,
                'page_title': page_title,
                'surrounding_text': surrounding_text,
                'filename': filename,
                'element_html': str(img)
            }
            
            issues.append(BarrierefreiheitIssue(
                category='Barrierefreiheit',
                severity='warning',
                title=f'Bild ohne Alt-Text: {filename[:50]}',
                description=f'Das Bild "{filename}" auf Seite {url} hat keinen Alternativtext für Screenreader.',
                risk_euro=500,
                recommendation='Fügen Sie einen beschreibenden Alt-Text hinzu. KI kann Vorschläge generieren.',
                legal_basis='WCAG 2.1 Level A (1.1.1 Non-text Content), BFSG §12',
                auto_fixable=True,
                image_src=urljoin(url, img_src),  # Make absolute URL
                element_html=str(img),
                metadata={
                    'needs_ai_alt_text': True,
                    'context': context,
                    'page_url': url
                }
            ))
    
    return issues


def _get_surrounding_text(img, soup: BeautifulSoup, max_length: int = 200) -> str:
    """
    Extrahiert den umgebenden Text eines Bildes für Kontext
    
    Args:
        img: Das img-Element
        soup: BeautifulSoup-Objekt
        max_length: Maximale Länge des Texts
        
    Returns:
        Umgebender Text
    """
    surrounding = []
    
    # Text vom parent-Element
    if img.parent:
        parent_text = img.parent.get_text(strip=True)
        if parent_text:
            surrounding.append(parent_text)
    
    # Text von vorherigem Geschwister-Element
    if img.previous_sibling:
        prev_text = img.previous_sibling.get_text(strip=True) if hasattr(img.previous_sibling, 'get_text') else str(img.previous_sibling).strip()
        if prev_text:
            surrounding.append(prev_text)
    
    # Text von nächstem Geschwister-Element
    if img.next_sibling:
        next_text = img.next_sibling.get_text(strip=True) if hasattr(img.next_sibling, 'get_text') else str(img.next_sibling).strip()
        if next_text:
            surrounding.append(next_text)
    
    # Kombiniere und begrenze
    full_text = ' '.join(surrounding)
    return full_text[:max_length] if full_text else ''


# =============================================================================
# Enhanced Check mit axe-core und Media
# =============================================================================

async def check_barrierefreiheit_enhanced(
    url: str,
    html: str = None,
    session=None,
    use_axe_core: bool = True,
    check_media: bool = True
) -> List[Dict[str, Any]]:
    """
    🚀 ENHANCED Barrierefreiheits-Check mit axe-core und Media-Prüfung
    
    Kombiniert:
    1. Eigene Checks (barrierefreiheit_check)
    2. axe-core für vollständige WCAG-Abdeckung
    3. Media-Accessibility-Check (Video/Audio)
    
    Args:
        url: URL der zu prüfenden Website
        html: Optional bereits gefetchtes HTML
        session: Optional aiohttp Session
        use_axe_core: axe-core Scanner verwenden (erfordert Playwright)
        check_media: Media-Elemente prüfen
        
    Returns:
        Kombinierte Liste von Issues
    """
    logger.info(f"🔍 Enhanced Barrierefreiheits-Check für: {url}")
    
    all_issues = []
    
    # 1. Führe Standard-Check durch
    try:
        standard_issues = await check_barrierefreiheit_compliance_smart(url, html, session)
        all_issues.extend(standard_issues)
        logger.info(f"✅ Standard-Check: {len(standard_issues)} Issues")
    except Exception as e:
        logger.error(f"❌ Standard-Check fehlgeschlagen: {e}")
    
    # 2. axe-core Check (optional)
    if use_axe_core:
        try:
            from ..axe_scanner import run_axe_scan
            axe_result, axe_issues = await run_axe_scan(url)
            
            # Dedupliziere: Nur axe-Issues hinzufügen, die nicht schon gefunden wurden
            existing_selectors = {issue.get('selector') for issue in all_issues if issue.get('selector')}
            
            for issue in axe_issues:
                selector = issue.get('selector', '')
                if selector and selector not in existing_selectors:
                    all_issues.append(issue)
                    existing_selectors.add(selector)
            
            logger.info(f"✅ axe-core Check: {len(axe_issues)} Issues ({axe_result.total_violations} Violations)")
        except ImportError:
            logger.warning("⚠️ axe-core nicht verfügbar (Playwright nicht installiert)")
        except Exception as e:
            logger.error(f"❌ axe-core Check fehlgeschlagen: {e}")
    
    # 3. Media-Accessibility-Check (optional)
    if check_media:
        try:
            from .media_accessibility_check import check_media_accessibility
            
            # Hole HTML wenn nicht vorhanden
            if not html:
                import ssl
                import certifi
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                async with aiohttp.ClientSession(connector=connector) as temp_session:
                    async with temp_session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                        html = await response.text()
            
            media_issues = await check_media_accessibility(url, html)
            all_issues.extend(media_issues)
            logger.info(f"✅ Media-Check: {len(media_issues)} Issues")
        except Exception as e:
            logger.error(f"❌ Media-Check fehlgeschlagen: {e}")
    
    # 4. Sortiere nach Severity
    severity_order = {'critical': 0, 'error': 1, 'warning': 2, 'info': 3}
    all_issues.sort(key=lambda x: severity_order.get(x.get('severity', 'info'), 3))
    
    logger.info(f"✅ Enhanced Check abgeschlossen: {len(all_issues)} Issues insgesamt")
    
    return all_issues

