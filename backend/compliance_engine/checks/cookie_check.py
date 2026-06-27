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


# ---------------------------------------------------------------------------
# Funktionale Consent-Button-Klassifikation
# ---------------------------------------------------------------------------
# Statt den gesamten HTML-Text nach Schlüsselwörtern zu durchsuchen, werden die
# tatsächlichen interaktiven Elemente (button/a/[role=button]/input) im Banner
# anhand ihrer ROLLE/AKTION klassifiziert: id, class, data-*-Attribute,
# aria-label, onclick — und erst nachrangig der sichtbare Text. Dadurch ist die
# Erkennung unabhängig von der konkreten Beschriftung (z.B. einer serverseitig
# konfigurierten "Nur essentielle Cookies erlauben"-Variante).

_REJECT_ATTR_RE = re.compile(
    r'reject|decline|deny|refuse|ablehn|only[-_]?necessary|necessary[-_]?only'
    r'|nur[-_]?notwendig|essenziell|essentiell|deny[-_]?all|reject[-_]?all'
    r'|continue[-_]?without|without[-_]?cookies|ohne[-_]?cookies|nur[-_]?technisch',
    re.I,
)
_REJECT_TEXT_RE = re.compile(
    r'ablehn|verweigern|nicht zustimmen|nein danke|no thanks|reject|decline|refuse'
    r'|nur notwendig|nur erforderlich|nur essen[zt]iell|nur technisch'
    r'|essen[zt]ielle cookies|notwendige cookies|erforderliche cookies'
    r'|only necessary|only essential|essential only|necessary only|ohne cookies'
    r'|alle ablehnen',
    re.I,
)
_ACCEPT_ATTR_RE = re.compile(
    r'accept|agree|allow|consent[-_]?all|accept[-_]?all|allow[-_]?all|zustimm|einwillig',
    re.I,
)
_ACCEPT_TEXT_RE = re.compile(
    r'akzeptier|zustimm|einwillig|agree|allow all|alle akzeptieren|alle erlauben'
    r'|accept|verstanden|einverstanden',
    re.I,
)
_SETTINGS_ATTR_RE = re.compile(
    r'setting|preference|customize|manage|config|detail|option|einstellung|anpass',
    re.I,
)
_SETTINGS_TEXT_RE = re.compile(
    r'einstellung|anpassen|individuell|auswahl|details|optionen|konfigurier'
    r'|customize|manage|preferences|settings',
    re.I,
)
# Widerruf/Verwalten ist weder Accept noch Reject — vor Accept prüfen, sonst
# würde "Einwilligungen widerrufen" wegen "einwillig" als Accept zählen.
_REVOKE_RE = re.compile(r'widerruf|revoke|consent.*history|historie.*einwillig', re.I)


def _btn_signature(el):
    """Attribut-Blob (id/class/data-*/onclick/aria/title/value) + sichtbarer Text."""
    attrs = el.attrs or {}
    cls = attrs.get('class', [])
    cls = ' '.join(cls) if isinstance(cls, list) else str(cls)
    parts = [
        str(attrs.get('id', '')), cls, str(attrs.get('onclick', '')),
        str(attrs.get('aria-label', '')), str(attrs.get('title', '')),
        str(attrs.get('value', '')), str(attrs.get('name', '')),
    ]
    for k, v in attrs.items():
        if k.startswith('data-'):
            parts.append('%s %s' % (k, v))
    attr_blob = ' '.join(parts).lower()
    text = el.get_text(' ', strip=True).lower()
    return attr_blob, text


def _classify_consent_buttons(container):
    """Klassifiziert echte Buttons im Banner-Container in accept/reject/settings.

    Reihenfolge ist wichtig: Reject wird zuerst geprüft, damit z.B.
    "Nur essentielle Cookies erlauben" nicht wegen "erlauben/allow" als
    Accept fehlklassifiziert wird.
    """
    result = {'accept': False, 'reject': False, 'settings': False}
    if container is None:
        return result
    candidates = container.find_all(['button', 'a'])
    candidates += container.find_all(attrs={'role': 'button'})
    candidates += container.find_all('input', attrs={'type': re.compile(r'submit|button', re.I)})
    seen = set()
    for el in candidates:
        if id(el) in seen:
            continue
        seen.add(id(el))
        attr_blob, text = _btn_signature(el)
        if _REJECT_ATTR_RE.search(attr_blob) or _REJECT_TEXT_RE.search(text):
            result['reject'] = True
        elif _REVOKE_RE.search(text) or _REVOKE_RE.search(attr_blob):
            result['settings'] = True
        elif _ACCEPT_ATTR_RE.search(attr_blob) or _ACCEPT_TEXT_RE.search(text):
            result['accept'] = True
        elif _SETTINGS_ATTR_RE.search(attr_blob) or _SETTINGS_TEXT_RE.search(text):
            result['settings'] = True
    return result


def _classify_button_dict(b):
    """Klassifiziert ein Button-Dict (aus dem Renderer) in accept/reject/settings."""
    attr_blob = ' '.join([
        str(b.get('id', '')), str(b.get('cls', '')), str(b.get('onclick', '')),
        str(b.get('aria', '')), str(b.get('name', '')), str(b.get('value', '')),
    ]).lower()
    text = str(b.get('text', '')).lower()
    if _REJECT_ATTR_RE.search(attr_blob) or _REJECT_TEXT_RE.search(text):
        return 'reject'
    if _REVOKE_RE.search(text) or _REVOKE_RE.search(attr_blob):
        return 'settings'
    if _ACCEPT_ATTR_RE.search(attr_blob) or _ACCEPT_TEXT_RE.search(text):
        return 'accept'
    if _SETTINGS_ATTR_RE.search(attr_blob) or _SETTINGS_TEXT_RE.search(text):
        return 'settings'
    return None


def _has_fill(bg):
    """True, wenn der Button eine sichtbare Hintergrundfüllung hat (nicht transparent)."""
    if not bg:
        return False
    s = str(bg).lower().replace(' ', '')
    if s in ('transparent', 'none', ''):
        return False
    m = re.match(r'rgba?\(([^)]+)\)', s)
    if m:
        parts = m.group(1).split(',')
        if len(parts) >= 4:
            try:
                return float(parts[3]) > 0.05
            except ValueError:
                return True
        return True
    return True


def _has_border(b):
    """True, wenn der Button einen sichtbaren Rahmen hat (echter Button, kein Link)."""
    style = str(b.get('borderStyle', '')).lower()
    if not style or style == 'none':
        return False
    return _px(b.get('borderWidth')) > 0


def _px(val):
    """'14px' -> 14.0; robust gegen leere/ungültige Werte."""
    try:
        return float(re.sub(r'[^0-9.]', '', str(val)) or 0)
    except ValueError:
        return 0.0


def _assess_dark_pattern(consent_buttons):
    """Vergleicht Prominenz von Akzeptieren- vs. Ablehnen-Button im gerenderten
    Banner. Gibt eine Liste konkreter Befunde zurück (leer = unauffällig).
    Bewusst KONSERVATIV — nur klare Ungleichheiten werden gemeldet, damit legitime
    Designs nicht fälschlich als Dark Pattern markiert werden."""
    if not consent_buttons:
        return []
    accepts, rejects = [], []
    for b in consent_buttons:
        kind = _classify_button_dict(b)
        if kind == 'accept':
            accepts.append(b)
        elif kind == 'reject':
            rejects.append(b)
    if not accepts or not rejects:
        return []  # Fehlender Button wird an anderer Stelle behandelt

    def area(b):
        return max(0, int(b.get('w', 0))) * max(0, int(b.get('h', 0)))

    acc = max(accepts, key=area)
    rej = max(rejects, key=area)
    acc_area, rej_area = area(acc), area(rej)
    if acc_area <= 0 or rej_area <= 0:
        return []

    findings = []
    ratio = rej_area / acc_area
    # 1. Größe: Ablehnen deutlich kleiner als Akzeptieren
    if ratio < 0.6:
        findings.append(
            f'Der Ablehnen-Button ist deutlich kleiner als der Akzeptieren-Button '
            f'(ca. {int(ratio * 100)}% der Fläche: {rej.get("w")}×{rej.get("h")}px '
            f'vs. {acc.get("w")}×{acc.get("h")}px).'
        )
    # 2. Farbliche Hervorhebung: Akzeptieren gefüllt, Ablehnen weder gefüllt noch
    #    umrandet (= unauffälliger Text-Link). Gleich große Outline-Buttons mit
    #    sichtbarem Rahmen gelten als zulässig und werden NICHT geflaggt.
    acc_fill, rej_fill = _has_fill(acc.get('bg')), _has_fill(rej.get('bg'))
    if acc_fill and not rej_fill and not _has_border(rej) and ratio < 1.1:
        findings.append(
            'Der Akzeptieren-Button ist farblich hervorgehoben (gefüllte Fläche), '
            'während der Ablehnen-Button nur als unauffälliger Text-Link ohne Rahmen '
            'gestaltet ist.'
        )
    # 3. Schriftgröße: Ablehnen merklich kleiner
    acc_fs, rej_fs = _px(acc.get('fontSize')), _px(rej.get('fontSize'))
    if acc_fs > 0 and rej_fs > 0 and rej_fs < acc_fs * 0.8:
        findings.append(
            f'Die Schrift des Ablehnen-Buttons ist kleiner ({rej_fs:.0f}px) als die '
            f'des Akzeptieren-Buttons ({acc_fs:.0f}px).'
        )
    return findings


# Bekannte CMP-Loader-/CDN-Signaturen (auch ohne Herstellername im Klartext).
_CONSENT_SCRIPT_PATTERNS = [
    r'cookiebot', r'cybotcookiebot', r'consent\.cookiebot',
    r'onetrust', r'cookielaw', r'optanon', r'otsdkstub', r'cookiepro',
    r'usercentrics', r'app\.usercentrics',
    r'cookiefirst',
    r'consentmanager', r'cmpv2\.consentmanager', r'cdn\.consentmanager',
    r'borlabs-cookie', r'borlabs',
    r'klaro', r'kiprotect',
    r'termly', r'iubenda',
    r'didomi', r'privacy-center\.org',
    r'trustarc', r'truste',
    r'cookie-script', r'cookiescript',
    r'sourcepoint', r'sp-prod\.net', r'sp-message',
    r'quantcast', r'quantcount', r'choice\.consent',
    r'crownpeak', r'silktide.*consent', r'civic.*cookie',
    r'osano', r'cookieyes', r'cky-consent',
    r'real-cookie-banner', r'devowl', r'complianz',
    r'tarteaucitron', r'orejime', r'cookieconsent',
    r'cookie-compliance\.js', r'cookie-blocker\.js', r'complyo',
]

# Container-IDs/-Klassen, die CMPs in den (gerenderten) DOM injizieren — damit der
# Banner-Container für die funktionale Button-Analyse zuverlässig gefunden wird.
_CMP_CONTAINER_PATTERNS = [
    r'onetrust', r'optanon', r'ot-sdk', r'cybotcookiebot', r'usercentrics',
    r'uc-banner', r'cmplz', r'cky-', r'cookieyes', r'borlabs-cookie',
    r'klaro', r'didomi', r'cmpbox', r'cmpwrapper', r'sp_message', r'sp-message',
    r'iubenda', r'cookiefirst', r'termly', r'osano', r'complyo',
    r'cookie', r'consent', r'gdpr', r'cmp',
]

# Hinweise auf Tracking/Consent im statischen HTML — Trigger fürs Browser-Rendern.
_TRACKING_CONSENT_HINT_RE = re.compile(
    r'google-analytics|googletagmanager|gtag|gtm[-.]|fbevents|connect\.facebook'
    r'|hotjar|matomo|piwik|doubleclick|clarity\.ms|cdn\.segment|mixpanel|amplitude'
    r'|tiktok|linkedin\.com/(px|insight)|cookie|consent|gdpr|dsgvo|einwillig|tracking',
    re.I,
)


def _find_consent_container(soup):
    """Heuristik für selbstgebaute Banner ohne bekannte CMP-Klasse (v.a. im
    gerenderten DOM): kleinster Container mit Cookie-/Consent-Kontext, der einen
    echten Accept- ODER Reject-Button enthält. Die Accept/Reject-Pflicht verhindert
    False Positives durch bloße Footer-Links ("Cookie-Richtlinie", "Widerruf")."""
    keyword_re = re.compile(r'cookie|consent|datenschutz|einwillig|tracking|dsgvo|gdpr', re.I)
    best = None
    best_len = None
    for tag in ('dialog', 'aside', 'section', 'div'):
        for el in soup.find_all(tag):
            interactive = el.find_all(['button', 'a'])
            if not interactive or len(interactive) > 10:
                continue  # kein Control oder zu groß (Seitencontainer)
            cls_id = (' '.join(el.get('class', [])) + ' ' + str(el.get('id', ''))).lower()
            txt = el.get_text(' ', strip=True)
            if len(txt) > 1500:
                continue
            if not (keyword_re.search(cls_id) or keyword_re.search(txt[:800])):
                continue
            cls = _classify_consent_buttons(el)
            if not (cls['accept'] or cls['reject']):
                continue  # echtes Consent-Control nötig, nicht nur ein Policy-Link
            if best is None or len(txt) < best_len:
                best, best_len = el, len(txt)
    return best


def consent_render_needed(soup) -> bool:
    """True, wenn ein (vermutlich JS-injizierter) Cookie-Banner/Consent/Tracking
    vorliegt, der NICHT bereits als sichtbarer Container im statischen HTML steht.
    Dann sollte der Scanner die Seite im Browser rendern, damit die echten Banner-
    Buttons funktional geprüft werden können (auch Custom-Banner & Fehlkonfig.).

    Bewusst NUR auf Script-/Link-Signale geprüft (nicht auf Fließtext) — sonst
    würde jede Seite, die das Wort "Cookie" im Text hat, unnötig gerendert."""
    # Bereits ein sichtbarer Banner-Container mit Buttons im statischen HTML? -> kein Render nötig.
    for pat in _CMP_CONTAINER_PATTERNS:
        for el in soup.find_all(['div', 'aside', 'section', 'dialog'],
                                class_=re.compile(pat, re.I)):
            if el.find('button') or el.find('a') or el.find(attrs={'role': 'button'}):
                return False
    # Signale aus <script src>, Inline-Script-Inhalt und <link href> sammeln.
    blobs = []
    for sc in soup.find_all('script'):
        blobs.append(sc.get('src', '') or '')
        blobs.append(sc.string or '')
    for ln in soup.find_all('link', href=True):
        blobs.append(ln.get('href', '') or '')
    blob = ' '.join(blobs).lower()
    if not blob.strip():
        return False
    if any(re.search(p, blob) for p in _CONSENT_SCRIPT_PATTERNS):
        return True
    if _TRACKING_CONSENT_HINT_RE.search(blob):
        return True
    # Custom-Banner-Loader (z.B. "cookie-banner.js", "consent.js")
    if re.search(r'cookie|consent|gdpr|\bcmp\b|banner', blob):
        return True
    return False


async def check_cookie_compliance(url: str, soup: BeautifulSoup, session=None, consent_buttons=None) -> List[Dict[str, Any]]:
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
        # Vendor-Container-Selektoren (v.a. nach Browser-Rendering sichtbar)
        r'onetrust', r'optanon', r'ot-sdk', r'cybotcookiebot',
        r'usercentrics', r'uc-banner', r'cmplz', r'cky-', r'cookieyes',
        r'cmpwrapper', r'cookiefirst', r'termly', r'osano', r'complyo',
    ]
    
    has_cookie_banner = False
    has_visible_banner = False
    banner_el = None  # sichtbarer Banner-Container (für funktionale Button-Analyse)

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
                    banner_el = el
                    break
            if has_cookie_banner:
                break
            for el in soup.find_all(tag, id=re.compile(pattern, re.I)):
                if _is_visible(el):
                    has_cookie_banner = True
                    has_visible_banner = True
                    banner_el = el
                    break
            if has_cookie_banner:
                break
        if has_cookie_banner:
            break
    
    # Prüfe bekannte Cookie-Consent-Tools per Script-src.
    # WICHTIG: Viele CMPs laden über CDN-Domains/Datei-/Cookie-Namen, die den
    # Hersteller NICHT im Klartext enthalten (z.B. OneTrust -> cookielaw.org /
    # otSDKStub.js / optanon). Solche Aliase müssen mit drin sein, sonst gilt der
    # Banner als "nicht vorhanden" und alle Cookie-Findings feuern fälschlich.
    consent_tool_patterns = _CONSENT_SCRIPT_PATTERNS
    
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

    # Fallback: Banner-Container heuristisch finden, wenn ein Banner erkannt wurde
    # aber keine bekannte Klasse/ID matchte (z.B. selbstgebaute Banner im
    # gerenderten DOM). Ermöglicht die funktionale Button-Analyse auch hier.
    if banner_el is None:
        banner_el = _find_consent_container(soup)
        if banner_el is not None:
            has_cookie_banner = True
            has_visible_banner = True

    # Tracking-Erkennung — wird sowohl ohne als auch mit Banner benötigt.
    # v4.0: deckt jetzt auch GTM-Container, inline-Snippets, Pixel und bekannte
    # Third-Party-Hosts ab (nicht nur <script src>), um False Negatives zu senken.
    has_tracking = False
    tracking_patterns = [
        r'google-analytics', r'googletagmanager', r'gtag\(', r'gtag/js',
        r'\bdatalayer\b', r'ga\(\s*[\'"]create', r'_gaq',
        r'facebook.*pixel', r'connect\.facebook\.net', r'fbq\(',
        r'hotjar', r'\bhj\(', r'matomo', r'piwik',
        r'doubleclick', r'googlesyndication', r'google-adservices',
        r'clarity\.ms', r'cdn\.segment', r'mixpanel', r'amplitude',
        r'fullstory', r'mouseflow', r'plausible', r'\.tiktok\.com',
        r'linkedin\.com/(px|insight)', r'snap\.licdn', r'criteo',
        r'taboola', r'outbrain', r'bing.*uet', r'pinterest.*tag',
        r'analytics', r'tracking', r'gtm\.js', r'gtm-',
    ]
    # 1. <script src> + 2. inline-Script-Inhalt (alle <script>, nicht nur src)
    for script in soup.find_all('script'):
        haystack = (script.get('src', '') + ' ' + (script.string or '')).lower()
        if any(re.search(pattern, haystack, re.I) for pattern in tracking_patterns):
            has_tracking = True
            break

    # 3. Third-Party-Embeds (iframes/img-Pixel) zu bekannten Tracking-Hosts
    if not has_tracking:
        third_party_hosts = (
            'doubleclick.net', 'google-analytics.com', 'googletagmanager.com',
            'facebook.com/tr', 'connect.facebook.net', 'hotjar.com',
            'clarity.ms', 'segment.com', 'youtube.com/embed', 'maps.googleapis',
            'fonts.googleapis',
        )
        for el in soup.find_all(['iframe', 'img', 'link'], src=True) + soup.find_all('link', href=True):
            ref = (el.get('src') or el.get('href') or '').lower()
            if any(host in ref for host in third_party_hosts):
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

        # Managed CMP: Banner wurde nur über Script-/Inline-/Preload-Signaturen
        # erkannt (nicht als sichtbarer DOM-Container). Solche Banner werden per
        # JavaScript injiziert und sind im statischen HTML NICHT enthalten — die
        # Buttons können also weder per Keyword noch funktional aus dem HTML
        # gelesen werden. Bekannte CMPs (Complyo-Widget, Cookiebot, Usercentrics,
        # Borlabs, Klaro, ...) stellen per Design einen gleichwertigen Ablehnen-,
        # Kategorie- und Widerrufs-Pfad bereit. Sie deshalb NICHT als Verstoß
        # werten (sonst False Positives bei legitimen CMP-Nutzern).
        managed_cmp = has_cookie_banner and not has_visible_banner

        # Funktionale Button-Analyse auf dem sichtbaren Banner-Container.
        btn = _classify_consent_buttons(banner_el)

        # Keyword-Fallback auf dem Volltext (nur, wenn weder ein sichtbarer
        # Banner-Container noch ein managed CMP vorliegt — z.B. selbstgebaute,
        # serverseitig gerenderte Banner ohne erkennbare Container-Klasse).
        kw_accept = bool(re.search(
            r'akzeptier|accept|zustimm|einwillig|agree|allow all|alle akzeptieren|alle erlauben',
            html_text
        ))
        kw_reject = bool(re.search(
            r'ablehn|nur notwendig|nur erforderlich|nur essen[zt]iell|nur technisch'
            r'|essen[zt]ielle cookies|notwendige cookies|erforderliche cookies'
            r'|only necessary|only essential|essential only|necessary only|reject|decline|refuse'
            r'|nicht einwillig|nein danke|no thanks|alle ablehnen|verweigern',
            html_text
        ))
        kw_categories = bool(re.search(
            r'statistik|marketing|funktional|preferences|personalisier|analytical|targeting'
            r'|category|kategorien|cookie.*kategorie',
            html_text
        ))
        kw_revoke = bool(re.search(
            r'widerruf|einwilligung.*änder|cookie.*einstellung|cookie.*settings|manage.*consent'
            r'|consent.*settings|datenschutz.*einstellung|privacy.*setting',
            html_text
        ))

        # 1. Opt-In — Akzeptieren-Button (funktional > managed CMP > Keyword)
        has_accept = btn['accept'] or managed_cmp or kw_accept
        # 2. Ablehnungsmöglichkeit — gleichwertiger Ablehnen/Nur-notwendige-Button
        has_reject = btn['reject'] or managed_cmp or kw_reject
        # 3. Granularität — Kategorien/Einstellungen
        has_categories = btn['settings'] or managed_cmp or kw_categories
        # 4. Widerrufsmöglichkeit — nachträgliches Ändern
        has_revoke = managed_cmp or kw_revoke
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
        else:
            # Ablehnen-Button existiert — ist er GLEICHWERTIG gestaltet? Prominenz-/
            # Größenvergleich auf Basis der Computed Styles aus dem Render (Dark Pattern).
            dp_findings = _assess_dark_pattern(consent_buttons)
            if dp_findings:
                issues.append(asdict(CookieIssue(
                    category='cookies',
                    severity='warning',
                    title='Ablehnen-Button nicht gleichwertig gestaltet (Dark Pattern)',
                    description=(
                        'Ein Ablehnen-Button ist zwar vorhanden, aber nicht gleich prominent wie '
                        'der Akzeptieren-Button: ' + ' '.join(dp_findings) + ' '
                        'Nach TDDDG §25 und EuGH C-673/17 muss das Ablehnen genauso einfach und '
                        'sichtbar sein wie das Akzeptieren — eine optische Bevorzugung der '
                        'Zustimmung ist ein unzulässiges Dark Pattern.'
                    ),
                    risk_euro=3000,
                    recommendation=(
                        'Gestalten Sie Ablehnen- und Akzeptieren-Button gleichwertig: gleiche Größe, '
                        'gleiche Schrift und gleiche visuelle Gewichtung (keine farbliche Bevorzugung '
                        'nur des Akzeptieren-Buttons).'
                    ),
                    legal_basis='TDDDG §25, EuGH C-673/17 (Planet49), DSK-Orientierungshilfe',
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

