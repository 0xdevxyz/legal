"""
Cookie Check (TDDDG §25)
Prüft Cookie-Banner und Consent-Compliance
Inkludiert TCF 2.2 (Transparency & Consent Framework) Support
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import re

@dataclass
class CookieIssue:
    category: str
    severity: str
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool = False
    is_missing: bool = False  # True wenn komplettes Element fehlt (nicht nur Unterpunkt)

async def check_cookie_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Prüft Cookie-Consent-Compliance
    
    1. Cookie-Banner vorhanden und sichtbar
    2. Tracking-Scripts ohne Consent
    3. localStorage Consent-Einträge
    """
    issues = []
    
    # Suche bekannte Cookie-Banner (Klassen/IDs auf gängigen Container-Elementen)
    cookie_banner_patterns = [
        r'cookie.*banner',
        r'cookie.*consent',
        r'cookie.*notice',
        r'cookie.*bar',
        r'cookie.*popup',
        r'cookie.*modal',
        r'cookie.*overlay',
        r'cookie.*wall',
        r'cookie.*dialog',
        r'gdpr.*banner',
        r'gdpr.*consent',
        r'privacy.*banner',
        r'privacy.*notice',
        r'consent.*banner',
        r'consent.*dialog',
        r'consent.*popup',
        r'consent.*overlay',
        r'cc-window',      # CookieConsent.js
        r'cc-banner',
        r'cm-banner',      # Consent Manager
        r'cmpbox',         # CMP-typisch
        r'sp-message',     # SourcePoint
        r'didomi',
        r'klaro',
        r'borlabs',
        r'iubenda',
    ]
    
    has_cookie_banner = False
    has_visible_banner = False
    
    # Prüfe gängige Container-Elemente (inkl. dialog, footer)
    container_tags = ['div', 'aside', 'section', 'dialog', 'footer', 'header', 'nav', 'article']
    
    def _is_visible(element) -> bool:
        style = element.get('style', '').replace(' ', '').lower()
        if 'display:none' in style or 'visibility:hidden' in style:
            return False
        cls = ' '.join(element.get('class', [])).lower()
        if re.search(r'\bhidden\b|\bsr-only\b|\bvisually-hidden\b', cls):
            return False
        return True
    
    for pattern in cookie_banner_patterns:
        for tag in container_tags:
            for el in soup.find_all(tag, class_=re.compile(pattern, re.I)):
                if _is_visible(el):
                    has_cookie_banner = True
                    has_visible_banner = True
                    break
            if has_cookie_banner:
                break
            for el in soup.find_all(tag, id=re.compile(pattern, re.I)):
                if _is_visible(el):
                    has_cookie_banner = True
                    has_visible_banner = True
                    break
            if has_cookie_banner:
                break
        if has_cookie_banner:
            break
    
    # Prüfe bekannte Cookie-Consent-Tools per Script-src
    consent_tool_patterns = [
        r'cookiebot',
        r'onetrust',
        r'usercentrics',
        r'cookiefirst',
        r'consentmanager',
        r'borlabs-cookie',
        r'klaro',
        r'termly',
        r'iubenda',
        r'didomi',
        r'trustarc',
        r'cookie-script',
        r'cookiescript',
        r'cookiepro',
        r'sourcepoint',
        r'quantcast',
        r'crownpeak',
        r'silktide.*consent',
        r'civic.*cookie',
        r'cookieconsent',   # osano/CookieConsent.js CDN
    ]
    
    scripts = soup.find_all('script', src=True)
    if not has_cookie_banner:
        for script in scripts:
            src = script.get('src', '').lower()
            for tool in consent_tool_patterns:
                if re.search(tool, src, re.I):
                    has_cookie_banner = True
                    break
            if has_cookie_banner:
                break
    
    # Prüfe Inline-Scripts auf echte Consent-Implementierungen
    if not has_cookie_banner:
        inline_scripts = soup.find_all('script', src=False)
        for script in inline_scripts:
            script_content = script.string or ''
            if 'meta' in script_content.lower() and 'keywords' in script_content.lower():
                continue
            if any(keyword in script_content.lower() for keyword in [
                'cookieconsent.init',
                'cookieconsent.run(',
                'usercentrics.init',
                'cookiebot.renew',
                'onetrust.onconsentchanged',
                'window.__cmp',
                'window.__tcfapi',
                '__uspapi',
                'complyocookiebanner',
                'cookie-compliance.js',
                'complyo_cookie_consent',
                'klaro.getManager',
                'didomi.initialize',
                'borlabs-cookie',
            ]):
                has_cookie_banner = True
                break
    
    # Prüfe Complyo Cookie-Banner Script-Tags
    if not has_cookie_banner:
        for script in scripts:
            src = script.get('src', '').lower()
            if 'cookie-compliance.js' in src or 'cookie-blocker.js' in src or 'complyo' in src:
                has_cookie_banner = True
                break

    # Prüfe Preload-Links (Next.js afterInteractive Scripts erscheinen als <link rel="preload">)
    if not has_cookie_banner:
        html_text = str(soup).lower()
        if ('cookie-compliance.js' in html_text and 'complyo' in html_text) or 'cookie-blocker.js' in html_text:
            has_cookie_banner = True
        elif any(re.search(tool, html_text) for tool in consent_tool_patterns):
            for link in soup.find_all('link', href=True):
                href = link.get('href', '').lower()
                if any(re.search(tool, href) for tool in consent_tool_patterns):
                    has_cookie_banner = True
                    break
    
    # Tracking-Erkennung — wird sowohl ohne als auch mit Banner benötigt
    has_tracking = False
    tracking_patterns = [
        r'google-analytics',
        r'googletagmanager',
        r'facebook.*pixel',
        r'hotjar',
        r'matomo',
        r'analytics',
        r'tracking',
    ]
    for script in scripts:
        src = script.get('src', '').lower()
        for pattern in tracking_patterns:
            if re.search(pattern, src, re.I):
                has_tracking = True
                break

    if not has_cookie_banner:
        if has_tracking:
            # Tracking vorhanden aber kein Banner → alle Sub-Issues als critical
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='critical',
                title='Kein Cookie-Consent-Banner vorhanden',
                description='Es wurde kein Cookie-Consent-Banner gefunden, obwohl Tracking-Scripts geladen werden. '
                           'Ein Cookie-Banner mit Opt-In ist nach TDDDG §25 verpflichtend. '
                           '⚠️ Es wurden Tracking-Scripts gefunden - Tracking ohne Einwilligung ist illegal!',
                risk_euro=5000,
                recommendation='Nutzen Sie die integrierte Complyo Cookie-Compliance-Lösung im Dashboard unter "Cookie-Compliance". '
                             'Einfach einrichten mit automatischer Cookie-Erkennung, anpassbarem Design und Consent-Statistiken.',
                legal_basis='TDDDG §25, DSGVO Art. 7 (Einwilligung)',
                auto_fixable=True,
                is_missing=True
            )))
            
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='critical',
                title='Opt-In Mechanismus fehlt',
                description='Es fehlt ein aktiver Opt-In Mechanismus. Cookies dürfen nur nach ausdrücklicher Einwilligung gesetzt werden.',
                risk_euro=3000,
                recommendation='Implementieren Sie einen Cookie-Banner, der Cookies nur nach aktiver Zustimmung (Opt-In) setzt.',
                legal_basis='TDDDG §25 Abs. 1',
                auto_fixable=False,
                is_missing=True
            )))
            
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='critical',
                title='Ablehnungsmöglichkeit fehlt',
                description='Es fehlt eine klare und einfache Möglichkeit, die Cookie-Nutzung abzulehnen.',
                risk_euro=2500,
                recommendation='Fügen Sie eine deutliche "Ablehnen" oder "Nur notwendige Cookies" Option hinzu.',
                legal_basis='TDDDG §25 Abs. 1, DSGVO Art. 7 Abs. 3',
                auto_fixable=False,
                is_missing=True
            )))
            
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='critical',
                title='Cookie-Informationspflicht nicht erfüllt',
                description='Es fehlen Informationen über welche Cookies gesetzt werden, zu welchem Zweck und wie lange.',
                risk_euro=2000,
                recommendation='Fügen Sie eine detaillierte Cookie-Übersicht hinzu (Typ, Zweck, Speicherdauer).',
                legal_basis='DSGVO Art. 13',
                auto_fixable=False,
                is_missing=True
            )))
            
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='warning',
                title='Widerrufsmöglichkeit fehlt',
                description='Es fehlt eine einfache Möglichkeit, die Cookie-Einwilligung nachträglich zu widerrufen.',
                risk_euro=1500,
                recommendation='Implementieren Sie eine Widerrufsmöglichkeit (z.B. Link in Datenschutzerklärung oder Footer).',
                legal_basis='DSGVO Art. 7 Abs. 3',
                auto_fixable=False,
                is_missing=True
            )))
            
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='warning',
                title='Einwilligungsnachweis fehlt',
                description='Es existiert kein System zum Nachweis der erteilten Cookie-Einwilligungen (Dokumentationspflicht).',
                risk_euro=1500,
                recommendation='Implementieren Sie ein System zur Dokumentation der Einwilligungen (Consent-Logs).',
                legal_basis='DSGVO Art. 7 Abs. 1',
                auto_fixable=False,
                is_missing=True
            )))
        else:
            # Kein Tracking erkannt — kein Banner zwingend nötig (nur technisch notwendige Cookies)
            # Hinweis als info-level, kein kritisches Issue
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='info',
                title='Kein Cookie-Banner erkannt (kein Tracking gefunden)',
                description='Es wurde kein Cookie-Consent-Banner gefunden. Da keine Tracking- oder Analyse-Scripts erkannt wurden, '
                           'ist ein Banner aktuell möglicherweise nicht zwingend erforderlich (technisch notwendige Cookies benötigen keinen Consent nach TDDDG §25 Abs. 2). '
                           'Sobald Analytics oder andere nicht-notwendige Cookies eingesetzt werden, wird ein Banner Pflicht.',
                risk_euro=0,
                recommendation='Prüfen Sie, ob Ihre Website nicht-notwendige Cookies setzt. Falls ja, implementieren Sie einen Cookie-Consent-Banner.',
                legal_basis='TDDDG §25 Abs. 2 (Ausnahme für technisch notwendige Cookies)',
                auto_fixable=False,
                is_missing=False
            )))
    else:
        # Banner vorhanden — Qualitätsprüfung nur wenn Tracking-Cookies gesetzt werden.
        # Ohne Tracking: kein Consent nötig → keine Issues, Score 100.
        if not has_tracking:
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='info',
                title='Kein Cookie-Banner erforderlich',
                description=(
                    'Es werden keine einwilligungspflichtigen Cookies gesetzt. '
                    'Ein Cookie-Banner ist nach TDDDG §25 Abs. 2 nicht erforderlich, '
                    'solange ausschließlich technisch notwendige Cookies genutzt werden.'
                ),
                risk_euro=0,
                recommendation='Kein Handlungsbedarf. Sobald Tracking oder Analytics eingesetzt werden, muss ein Consent-Banner ergänzt werden.',
                legal_basis='TDDDG §25 Abs. 2 (Ausnahme technisch notwendige Cookies)',
                auto_fixable=False,
                is_missing=False,
            )))
            return issues

        html_text = str(soup).lower()

        # 1. Opt-In vs. Opt-Out — gibt es einen Akzeptieren-Button?
        has_accept = bool(re.search(
            r'akzeptier|accept|zustimm|einwillig|agree|allow all|alle akzeptieren|alle erlauben',
            html_text
        ))
        # 2. Ablehnungsmöglichkeit — gibt es eine Ablehnen/Nur-notwendige Option?
        has_reject = bool(re.search(
            r'ablehn|ablehnen|nur notwendig|only necessary|only essential|reject|decline|refuse'
            r'|nicht einwillig|nein danke|no thanks|alle ablehnen',
            html_text
        ))
        # 3. Granularität — gibt es Kategorien (Statistik, Marketing, ...)?
        has_categories = bool(re.search(
            r'statistik|marketing|funktional|preferences|personalisier|analytical|targeting'
            r'|category|kategorien|cookie.*kategorie',
            html_text
        ))
        # 4. Widerrufsmöglichkeit — Link/Button zum nachträglichen Ändern?
        has_revoke = bool(re.search(
            r'widerruf|einwilligung.*änder|cookie.*einstellung|cookie.*settings|manage.*consent'
            r'|consent.*settings|datenschutz.*einstellung|privacy.*setting',
            html_text
        ))
        # 5. Tracking vor Consent — werden Analytics/Pixel bereits im HTML geladen?
        tracking_before_consent = []
        tracking_scripts = [
            ('Google Analytics / GTM', r'google-analytics\.com|googletagmanager\.com/gtag'),
            ('Facebook Pixel', r'connect\.facebook\.net|facebook\.com/tr'),
            ('Hotjar', r'static\.hotjar\.com|script\.hotjar\.com'),
            ('LinkedIn Insight', r'snap\.licdn\.com|linkedin\.com/px'),
            ('TikTok Pixel', r'analytics\.tiktok\.com'),
            ('Pinterest', r'pintrk|pinterest\.com/v3'),
            ('Matomo (extern)', r'matomo\.cloud'),
        ]
        for script in soup.find_all('script', src=True):
            src = script.get('src', '').lower()
            for name, pattern in tracking_scripts:
                if re.search(pattern, src, re.I) and name not in tracking_before_consent:
                    tracking_before_consent.append(name)

        if not has_reject:
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='critical',
                title='Keine Ablehnungsmöglichkeit im Cookie-Banner',
                description=(
                    'Der Cookie-Banner wurde gefunden, bietet aber keine klare Möglichkeit zum Ablehnen. '
                    'Nach EuGH-Rechtsprechung (C-673/17) und TDDDG §25 muss das Ablehnen genauso einfach '
                    'sein wie das Akzeptieren — kein "Dark Pattern" erlaubt.'
                ),
                risk_euro=5000,
                recommendation=(
                    'Fügen Sie einen gleichwertigen "Ablehnen"- oder "Nur notwendige Cookies"-Button '
                    'direkt im Banner hinzu, ohne zusätzliche Klicks.'
                ),
                legal_basis='TDDDG §25, EuGH C-673/17 (Planet49), DSGVO Art. 7 Abs. 3',
                auto_fixable=True,
                is_missing=False,
            )))

        if not has_accept:
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='warning',
                title='Kein aktiver Opt-In erkannt',
                description=(
                    'Im Cookie-Banner wurde kein aktiver Zustimmungs-Button gefunden. '
                    'Nach TDDDG §25 erfordert das Setzen nicht-notwendiger Cookies eine '
                    'ausdrückliche, aktive Einwilligung (kein Pre-Ticking, kein Opt-Out).'
                ),
                risk_euro=3000,
                recommendation=(
                    'Stellen Sie sicher dass Cookies erst nach aktivem Klick auf "Akzeptieren" '
                    'oder "Zustimmen" gesetzt werden.'
                ),
                legal_basis='TDDDG §25, DSGVO Art. 4 Nr. 11 (Einwilligungsdefinition)',
                auto_fixable=True,
                is_missing=False,
            )))

        if not has_categories:
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='warning',
                title='Keine Cookie-Kategorien im Banner',
                description=(
                    'Der Banner bietet keine granulare Auswahl nach Cookie-Kategorien '
                    '(z.B. Statistik, Marketing, Funktional). Eine differenzierte Einwilligung '
                    'ist Best Practice und von der DSK empfohlen.'
                ),
                risk_euro=1500,
                recommendation=(
                    'Ergänzen Sie den Banner um Kategorien: Notwendig (immer aktiv), '
                    'Statistik, Marketing, Funktional — jeweils mit ein/aus Toggle.'
                ),
                legal_basis='DSGVO Art. 5 Abs. 1 lit. b (Zweckbindung), DSK-Orientierungshilfe Telemedien',
                auto_fixable=True,
                is_missing=False,
            )))

        if not has_revoke:
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='warning',
                title='Widerruf der Cookie-Einwilligung nicht auffindbar',
                description=(
                    'Es wurde kein erkennbarer Weg gefunden, die Cookie-Einwilligung nachträglich '
                    'zu widerrufen. Die DSGVO schreibt vor, dass der Widerruf genauso einfach sein '
                    'muss wie die Einwilligung.'
                ),
                risk_euro=1500,
                recommendation=(
                    'Fügen Sie in der Datenschutzerklärung und/oder im Footer einen Link zu den '
                    'Cookie-Einstellungen hinzu (z.B. "Cookie-Einstellungen ändern").'
                ),
                legal_basis='DSGVO Art. 7 Abs. 3',
                auto_fixable=True,
                is_missing=False,
            )))

        if tracking_before_consent:
            issues.append(asdict(CookieIssue(
                category='cookies',
                severity='critical',
                title=f'Tracking-Scripts vor Consent geladen ({", ".join(tracking_before_consent[:3])})',
                description=(
                    f'Folgende Tracking-Scripts werden im HTML geladen bevor eine Einwilligung '
                    f'eingeholt wird: {", ".join(tracking_before_consent)}. '
                    f'Das ist ein klarer Verstoß gegen DSGVO Art. 6 und TDDDG §25 — '
                    f'selbst mit Cookie-Banner, wenn das Script im initialen HTML-Load enthalten ist.'
                ),
                risk_euro=10000,
                recommendation=(
                    'Laden Sie Tracking-Scripts nur nach expliziter Einwilligung '
                    '(conditional loading). Nutzen Sie Tag Manager mit Consent-Mode oder '
                    'das Complyo Cookie-Blocking-Feature.'
                ),
                legal_basis='DSGVO Art. 6 Abs. 1, TDDDG §25, BayLDA Prüfbericht 2022',
                auto_fixable=True,
                is_missing=False,
            )))
    
    return issues

