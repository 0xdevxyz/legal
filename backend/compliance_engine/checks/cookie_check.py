"""
Cookie Check (TTDSG §25)
Prüft Cookie-Banner und Consent-Compliance
Inkludiert TCF 2.2 (Transparency & Consent Framework) Support
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import re

# TCF 2.2 Support
try:
    from compliance_engine.checks.tcf_check import check_tcf_compliance
    TCF_AVAILABLE = True
except ImportError:
    TCF_AVAILABLE = False
    print("⚠️ TCF Check module not available")

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
    
    # Suche bekannte Cookie-Banner
    cookie_banner_patterns = [
        r'cookie.*banner',
        r'cookie.*consent',
        r'cookie.*notice',
        r'gdpr.*banner',
        r'privacy.*banner'
    ]
    
    has_cookie_banner = False
    has_visible_banner = False
    
    # Prüfe DIVs mit Cookie-bezogenen Klassen/IDs
    for pattern in cookie_banner_patterns:
        divs = soup.find_all(['div', 'aside', 'section'], class_=re.compile(pattern, re.I))
        for div in divs:
            # Prüfe ob Element sichtbar ist (nicht display:none oder visibility:hidden)
            style = div.get('style', '').lower()
            if 'display:none' not in style.replace(' ', '') and 'display: none' not in style:
                if 'visibility:hidden' not in style.replace(' ', '') and 'visibility: hidden' not in style:
                    has_cookie_banner = True
                    has_visible_banner = True
                    break
        
        if not has_cookie_banner:
            divs_by_id = soup.find_all(['div', 'aside', 'section'], id=re.compile(pattern, re.I))
            for div in divs_by_id:
                style = div.get('style', '').lower()
                if 'display:none' not in style.replace(' ', '') and 'display: none' not in style:
                    if 'visibility:hidden' not in style.replace(' ', '') and 'visibility: hidden' not in style:
                        has_cookie_banner = True
                        has_visible_banner = True
                        break
        
        if has_cookie_banner:
            break
    
    # Prüfe bekannte Cookie-Consent-Tools
    consent_tools = [
        r'cookiebot',
        r'onetrust',
        r'usercentrics',
        r'cookiefirst',
        r'consentmanager'
    ]
    
    scripts = soup.find_all('script', src=True)
    for script in scripts:
        src = script.get('src', '').lower()
        for tool in consent_tools:
            if re.search(tool, src, re.I):
                has_cookie_banner = True
                break
    
    # Prüfe auch auf JavaScript die Cookie-Consent-Management implementiert
    # (React Apps zeigen Banner dynamisch)
    # ABER: Ignoriere Meta-Tags und reine Beschreibungen
    if not has_cookie_banner:
        inline_scripts = soup.find_all('script', src=False)
        for script in inline_scripts:
            script_content = script.string or ''
            # WICHTIG: Ignoriere Next.js Meta-Daten (enthalten Keywords aber keine Funktionalität)
            if 'meta' in script_content.lower() and 'keywords' in script_content.lower():
                continue
            
            # Suche nach ECHTER Cookie-Consent-IMPLEMENTIERUNG (nicht nur Erwähnung)
            if any(keyword in script_content.lower() for keyword in [
                'cookieconsent.init',  # Echte CookieConsent.js Initialisierung
                'usercentrics.init',   # Usercentrics Init
                'cookiebot.renew',     # Cookiebot
                'onetrust.onconsentchanged',  # OneTrust
                'window.gtag && consent',  # Google Consent Mode
                'setcookie.*consent',  # Consent-Cookie wird gesetzt
                'localstorage.setitem.*consent'  # LocalStorage Consent
            ]):
                has_cookie_banner = True
                break
    
    # ✅ WICHTIG: Cookie-Banner ist IMMER Pflicht für geschäftliche Websites
    if not has_cookie_banner:
        # ✅ HAUPTELEMENT FEHLT: Generiere alle Sub-Issues mit is_missing=True
        
        # Prüfe ob Tracking-Scripts vorhanden sind (erhöht das Risiko)
        has_tracking = False
        tracking_patterns = [
            r'google-analytics',
            r'googletagmanager',
            r'facebook.*pixel',
            r'hotjar',
            r'matomo',
            r'analytics',
            r'tracking'
        ]
        
        for script in scripts:
            src = script.get('src', '').lower()
            for pattern in tracking_patterns:
                if re.search(pattern, src, re.I):
                    has_tracking = True
                    break
        
        # Hauptproblem: Kein Cookie-Banner
        issues.append(asdict(CookieIssue(
            category='cookies',
            severity='critical',
            title='Kein Cookie-Consent-Banner vorhanden',
            description='Es wurde kein Cookie-Consent-Banner gefunden. Ein Cookie-Banner mit Opt-In ist nach '
                       'TTDSG §25 verpflichtend für alle Websites die Cookies (außer technisch notwendige) setzen. '
                       + ('⚠️ Es wurden Tracking-Scripts gefunden - Tracking ohne Einwilligung ist illegal!' if has_tracking else ''),
            risk_euro=5000 if has_tracking else 4000,
            recommendation='Implementieren Sie sofort einen DSGVO/TTDSG-konformen Cookie-Consent-Banner '
                         '(z.B. eRecht24 Cookie Manager, Cookiebot, Usercentrics) mit Opt-In-Funktion.',
            legal_basis='TTDSG §25, DSGVO Art. 7 (Einwilligung)',
            auto_fixable=True,
            is_missing=True
        )))
        
        # Alle TTDSG-Anforderungen als fehlend markieren
        issues.append(asdict(CookieIssue(
            category='cookies',
            severity='critical',
            title='Opt-In Mechanismus fehlt',
            description='Es fehlt ein aktiver Opt-In Mechanismus. Cookies dürfen nur nach ausdrücklicher Einwilligung gesetzt werden.',
            risk_euro=3000,
            recommendation='Implementieren Sie einen Cookie-Banner, der Cookies nur nach aktiver Zustimmung (Opt-In) setzt.',
            legal_basis='TTDSG §25 Abs. 1',
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
            legal_basis='TTDSG §25 Abs. 1, DSGVO Art. 7 Abs. 3',
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
        # Banner vorhanden - prüfe auf erweiterte Compliance
        # TODO: Erweiterte Prüfung - wenn Banner vorhanden ist, aber unvollständig
        pass
    
    # ========================================
    # TCF 2.2 Check (optional, informational)
    # ========================================
    if TCF_AVAILABLE:
        try:
            tcf_data = await check_tcf_compliance(url, soup, page_content="")
            
            # TCF Issues hinzufügen (falls vorhanden)
            if tcf_data.get("issues"):
                issues.extend(tcf_data["issues"])
                
        except Exception as e:
            print(f"⚠️ TCF Check failed: {e}")
            # Fehler nicht zum Absturz führen lassen
    
    return issues

