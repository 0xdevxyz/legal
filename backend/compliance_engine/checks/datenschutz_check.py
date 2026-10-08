"""
Datenschutz Check (DSGVO)
Prüft Datenschutzerklärung-Compliance

✨ UPGRADED: Nutzt Browser-Rendering für JavaScript-Websites (React, Vue, Next.js)
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import re
import logging
import aiohttp
from compliance_engine.sicherer_abruf import sichere_session
from compliance_engine.checks.rechtsseiten_links import (
    ist_seitenlink, attrappen, attrappen_satz, lade_rechtsseite,
    seitenlink_art, ART_ANKER,
    PROBLEM_KEIN_RECHTSTEXT, PROBLEM_NICHT_ERREICHBAR,
)
from compliance_engine.checks.rechtsseiten_text import (
    fremder_host_ohne_klartext, finde_eingebetteten_text, eingebettete_seite,
    ist_duenne_erklaerung, inhaltstext, seiten_ueberschriften,
)

logger = logging.getLogger(__name__)

@dataclass
class DatenschutzIssue:
    category: str
    severity: str
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool = False
    is_missing: bool = False


# Wortteile, die eine Marketing- oder Produktseite verraten. Ein Link auf
# "/dsgvo-website-check/" traegt dieselben Stichwoerter wie die echte
# Erklaerung, meint aber etwas anderes.
_WERBEPFADE = (
    'check', 'test', 'scan', 'tool', 'rechner', 'generator', 'service',
    'leistung', 'produkt', 'preis', 'blog', 'ratgeber', 'wissen', 'lexikon',
    'beratung', 'schulung', 'software', 'loesung', 'losung', 'angebot',
)

# Linktexte, die genau die gesuchte Seite benennen.
_GENAUE_TEXTE = {
    'datenschutz', 'datenschutzerklärung', 'datenschutzerklaerung',
    'datenschutzhinweise', 'datenschutzrichtlinie', 'privacy', 'privacy policy',
    'privacy notice', 'impressum', 'imprint', 'legal notice',
    'anbieterkennzeichnung', 'pflichtangaben',
}

# Pfade, die genau die gesuchte Seite adressieren.
_GENAUE_PFADE = (
    '/datenschutz', '/datenschutzerklaerung', '/datenschutzerklärung',
    '/privacy', '/privacy-policy', '/privacy-notice', '/datenschutzhinweise',
    '/impressum', '/imprint', '/legal-notice', '/anbieterkennzeichnung',
)


def _linkguete(a_tag) -> int:
    """
    Bewertet, wie wahrscheinlich ein Link auf die gesuchte Rechtsseite zeigt.
    Hoeher ist besser; die Aufrufer sortieren absteigend.
    """
    from urllib.parse import urlparse

    href = (a_tag.get('href') or '').lower()
    text = a_tag.get_text(strip=True).lower()
    pfad = urlparse(href).path.rstrip('/') or href.rstrip('/')

    guete = 0
    if text in _GENAUE_TEXTE:
        guete += 10
    if pfad.endswith(_GENAUE_PFADE):
        guete += 8
    # Ein Werbebegriff im Pfad wiegt schwerer als jedes Stichwort davor.
    if any(w in pfad for w in _WERBEPFADE):
        guete -= 15
    # Footer-Links sind die uebliche Stelle fuer Pflichtseiten.
    for eltern in a_tag.parents:
        if getattr(eltern, 'name', None) == 'footer':
            guete += 3
            break
    if len(text) > 40:
        guete -= 3
    return guete


def _nach_guete(links):
    """Sortiert Kandidaten absteigend nach Guete, Reihenfolge bleibt sonst erhalten."""
    return sorted(links, key=_linkguete, reverse=True)


def _find_datenschutz_links(soup: BeautifulSoup, basis_url: str = None) -> List:
    """
    Verbesserte Suche nach Datenschutz-Links
    Findet auch Links in modernen JS-Frameworks (React, Vue, Next.js)
    """
    all_links = []
    keywords_href = [
        'datenschutz', 'privacy', 'dsgvo', 'gdpr', 'data-protection',
        'data_protection', 'privacy-notice', 'privacy_notice', 'privacy-policy',
        'privacy_policy', 'cookie-policy', 'cookie_policy', 'datenschutzhinweis',
        'datenschutzrichtlinie',
    ]
    keywords_text = [
        'datenschutz', 'privacy policy', 'dsgvo', 'datenschutzerklärung',
        'data protection', 'privacy notice', 'cookie-richtlinie', 'datenschutzhinweise',
        'datenschutzrichtlinie',
    ]
    
    for a_tag in soup.find_all('a', href=True):
        # mailto:, tel:, javascript: und leere Ziele fuehren zu keiner Seite;
        # ein so beschrifteter Link ist kein Rechtsseiten-Kandidat.
        if not ist_seitenlink(a_tag.get('href')):
            continue
        # Ein Link auf einen fremden Host ist nur dann die Erklaerung, wenn sein
        # Text sie beim Namen nennt: "www.datenschutz.sachsen.de" ist die
        # Landesbehoerde, nicht die Datenschutzerklaerung dieser Website.
        if fremder_host_ohne_klartext(a_tag, basis_url):
            continue
        href = a_tag.get('href', '').lower()
        link_text = a_tag.get_text(strip=True).lower()
        aria_label = (a_tag.get('aria-label') or '').lower()
        title = (a_tag.get('title') or '').lower()
        
        if any(kw in href for kw in keywords_href):
            all_links.append(a_tag)
        elif any(kw in link_text for kw in keywords_text):
            all_links.append(a_tag)
        elif any(kw in aria_label for kw in keywords_text):
            all_links.append(a_tag)
        elif any(kw in title for kw in keywords_text):
            all_links.append(a_tag)
    
    # Beste Kandidaten zuerst: der erste Treffer war auf complyo.de die
    # Produktseite /dsgvo-website-check/, nicht die Datenschutzerklaerung.
    return _nach_guete(all_links)



def _rechtsseiten_befund(geladen) -> Dict[str, Any]:
    """Befund fuer einen Datenschutz-Link, hinter dem keine Erklaerung steht."""
    if geladen.problem == PROBLEM_NICHT_ERREICHBAR:
        return asdict(DatenschutzIssue(
            category='datenschutz',
            severity='critical',
            title='Datenschutzerklärung nicht erreichbar',
            description=(
                f'Der Datenschutz-Link führt zu {geladen.url}, die Seite antwortet aber '
                f'mit HTTP {geladen.status}. Die Informationspflichten nach Art. 13/14 '
                'DSGVO sind damit nicht erfüllt.'
            ),
            risk_euro=5000,
            recommendation='Stellen Sie sicher, dass die verlinkte Datenschutzerklärung erreichbar ist (HTTP 200).',
            legal_basis='DSGVO Art. 13-14',
            auto_fixable=False,
            is_missing=True,
        ))
    if geladen.problem == PROBLEM_KEIN_RECHTSTEXT:
        return asdict(DatenschutzIssue(
            category='datenschutz',
            severity='critical',
            title='Datenschutz-Link führt zu keiner Datenschutzerklärung',
            description=(
                f'Der Link "Datenschutz" führt zu {geladen.url}. Dort steht aber keine '
                'Datenschutzerklärung: es fehlen Angaben zu Verantwortlichem, '
                'Verarbeitung, Rechtsgrundlage oder Betroffenenrechten. Für Besucher '
                'ist die Erklärung damit nicht erreichbar.'
            ),
            risk_euro=5000,
            recommendation=(
                'Verlinken Sie die Datenschutzerklärung auf eine eigene, direkt '
                'erreichbare Seite mit allen Pflichtangaben nach Art. 13/14 DSGVO.'
            ),
            legal_basis='DSGVO Art. 13-14',
            auto_fixable=False,
            is_missing=True,
        ))
    return asdict(DatenschutzIssue(
        category='datenschutz',
        severity='info',
        title='Inhaltsprüfung der Datenschutzerklärung nicht möglich',
        description=(
            f'Der Datenschutz-Link führt zu {geladen.url}, die Seite ließ sich aber '
            f'nicht laden ({geladen.fehler or "unbekannter Fehler"}). Die Vollständigkeit '
            'nach Art. 13/14 DSGVO ist damit NICHT bestätigt.'
        ),
        risk_euro=0,
        recommendation='Prüfen Sie die Erreichbarkeit der Datenschutzerklärung und wiederholen Sie den Scan.',
        legal_basis='DSGVO Art. 13/14',
        auto_fixable=False,
        is_missing=False,
    ))


async def check_datenschutz_compliance_smart(url: str, html: str = None, session=None) -> List[Dict[str, Any]]:
    """
    SMART Datenschutz-Check mit Browser-Rendering für JS-Websites
    
    Erkennt automatisch Client-Side-Rendering (React, Vue, Next.js)
    und rendert die Seite vollständig im Browser.
    """
    from ..browser_renderer import smart_fetch_html, detect_client_rendering
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        logger.info(f"✅ URL normalized to: {url}")
    
    logger.info(f"🔍 Smart Datenschutz-Check für: {url}")
    
    try:
        if html is None:
            import ssl
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with sichere_session(connector=connector) as temp_session:
                async with temp_session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    html = await response.text()
        
        needs_browser, reason = detect_client_rendering(html)
        
        if needs_browser:
            logger.info(f"🌐 Browser needed for Datenschutz check: {reason}")
            html, metadata = await smart_fetch_html(url, html)
            logger.info(f"✅ Browser rendering completed: {metadata.get('rendering_type', 'unknown')}")
        else:
            logger.info(f"⚡ Server-rendered detected, using simple HTML for Datenschutz check")
        
        soup = BeautifulSoup(html, 'html.parser')
        return await check_datenschutz_compliance(url, soup, session)
        
    except Exception as e:
        logger.error(f"❌ Smart Datenschutz check failed: {e}")
        soup = BeautifulSoup(html if html else "", 'html.parser')
        return await check_datenschutz_compliance(url, soup, session)


# Die neun Merkmale der Inhaltsschranke: Anzeigename und Muster. Die Schranke
# verlangt mindestens zwei; der Befund "Erklaerung knapp" nennt, welche davon
# im Text vorkommen und welche nicht.
#
# 07.10.2026: "personenbezogene daten" war als fester Text eingetragen und traf
# nur die Grundform. Im Fliesstext steht fast immer eine gebeugte Form
# ("Verarbeitung personenbezogener Daten", "Ihre personenbezogenen Daten"). Das
# Muster `personenbezogen\w*\s+daten` trifft alle. Ohne diese Korrektur lag
# eine Erklaerung auf Standardvorlage (Ingenieurbuero) bei null von neun Merkmalen.
_DS_MERKMALE = (
    ('Verantwortlicher', r'verantwortlich'),
    ('personenbezogene Daten', r'personenbezogen\w*\s+daten'),
    ('Rechtsgrundlage', r'rechtsgrundlage'),
    ('Art. 6 DSGVO', r'art\. 6'),
    ('Betroffenenrechte', r'betroffenenrechte'),
    ('Auskunftsrecht', r'auskunftsrecht'),
    ('Speicherdauer', r'speicherdauer'),
    ('Verarbeitung', r'verarbeitung'),
    ('Aufsichtsbehörde', r'aufsichtsbehörde'),
)


def _ds_merkmale(text: str) -> "tuple[List[str], List[str]]":
    """(vorhandene, fehlende) Merkmale aus `_DS_MERKMALE` im Text."""
    low = (text or '').lower()
    da = [name for name, rx in _DS_MERKMALE if re.search(rx, low)]
    fehlt = [name for name, _ in _DS_MERKMALE if name not in da]
    return da, fehlt


def _looks_like_datenschutz(text: str) -> bool:
    """
    Inhalts-Heuristik gegen Soft-404 / Catch-all: Sieht der Seitentext wirklich
    wie eine Datenschutzerklärung aus? Erfordert einen DSGVO-Schlüsselbegriff UND
    mindestens zwei der neun Merkmale aus `_DS_MERKMALE`.
    """
    if not text:
        return False
    low = text.lower()
    keyword = any(k in low for k in (
        'datenschutz', 'privacy policy', 'data protection', 'dsgvo', 'gdpr',
    ))
    if not keyword:
        return False
    return len(_ds_merkmale(text)[0]) >= 2


def _duenn_aus_wie(html: str) -> bool:
    """Knappe Erklaerung: Ueberschrift der Rechtsseite und genug Text."""
    return ist_duenne_erklaerung(html, 'datenschutz')


def _duenn_befund(geladen) -> Dict[str, Any]:
    """Hinweis fuer eine Erklaerung, die die Schranke nicht besteht, aber eine ist.

    Ein Hinweis, keine Beanstandung: gemessen ist nur, welche Stichworte im
    Text vorkommen. Ob die Angaben nach Art. 13/14 DSGVO inhaltlich vollstaendig
    sind, entscheidet diese Stichwortsuche nicht.
    """
    text = inhaltstext(geladen.html)
    da, fehlt = _ds_merkmale(text)
    soup = BeautifulSoup(geladen.html, 'html.parser')
    kopf = seiten_ueberschriften(soup)
    return asdict(DatenschutzIssue(
        category='datenschutz',
        severity='info',
        title='Datenschutzerklärung gefunden, aber sehr knapp',
        description=(
            f'Unter {geladen.url} steht eine Seite mit der Überschrift "{(kopf[0] if kopf else "Datenschutzerklärung")[:60]}" '
            f'({len(text)} Zeichen Text). Eine Stichwortsuche findet darin {len(da)} von '
            f'{len(_DS_MERKMALE)} typischen Merkmalen '
            f'({", ".join(da) if da else "keines"}); nicht gefunden wurden: '
            f'{", ".join(fehlt)}. Das ist ein Hinweis auf eine Standardvorlage oder eine '
            'sehr kurze Erklärung, keine Feststellung eines Mangels.'
        ),
        risk_euro=0,
        recommendation=(
            'Prüfen Sie von Hand, ob die Erklärung Verantwortlichen, Zwecke, '
            'Rechtsgrundlagen, Speicherdauer, Betroffenenrechte und das Beschwerderecht '
            'bei einer Aufsichtsbehörde nennt (Art. 13/14 DSGVO).'
        ),
        legal_basis='DSGVO Art. 13/14',
        auto_fixable=False,
        is_missing=False,
    ))


async def _fetch_candidate_text(candidate_url: str, session, ssl_context) -> "tuple[int, str] | None":
    """Lädt eine Kandidaten-URL und gibt (status, text) zurück; None bei Fehler."""
    try:
        if session:
            async with session.get(candidate_url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as resp:
                return resp.status, (await resp.text() if resp.status == 200 else "")
        else:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with sichere_session(connector=connector) as tmp:
                async with tmp.get(candidate_url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as resp:
                    return resp.status, (await resp.text() if resp.status == 200 else "")
    except Exception:
        return None


async def _check_datenschutz_url_exists(base_url: str, session=None) -> bool:
    """
    Prüft direkt bekannte Datenschutz-Pfade per HTTP-Request.
    Fallback für clientseitig gerenderte Seiten (Next.js, React SPA).

    ⚠️ Soft-404-Guard (v4.0): HTTP 200 allein ist KEIN Nachweis. Catch-all-Probe
    + Inhaltsprüfung verhindern, dass Parking-/Catch-all-Seiten fälschlich als
    "Datenschutz vorhanden" zählen.
    """
    from urllib.parse import urlparse
    import ssl
    import certifi

    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    probe = await _fetch_candidate_text(base + '/__complyo_probe_404__', session, ssl_context)
    is_catch_all = bool(probe and probe[0] == 200 and len(probe[1].strip()) > 200)
    if is_catch_all:
        logger.info("⚠️ Catch-all-Domain erkannt — prüfe Datenschutz-Inhalt strikt")

    candidate_paths = [
        '/datenschutz', '/datenschutzerklaerung', '/privacy', '/privacy-policy',
        '/dsgvo', '/data-protection', '/datenschutz-erklaerung'
    ]

    for path in candidate_paths:
        candidate_url = base + path
        result = await _fetch_candidate_text(candidate_url, session, ssl_context)
        if not result or result[0] != 200:
            continue
        # Eine Catch-all-Domain liefert fuer jeden Pfad dieselbe Seite; die ist
        # kein Rechtstext, auch wenn 'Impressum' und eine E-Mail darin stehen.
        if probe and probe[0] == 200 and result[1].strip() == probe[1].strip():
            continue
        from ..hybrid_validator import zu_fliesstext
        if _looks_like_datenschutz(zu_fliesstext(result[1])) or _duenn_aus_wie(result[1]):
            logger.info(f"✅ Datenschutz-URL mit validem Inhalt gefunden: {candidate_url}")
            return True
        logger.info(f"↪️ {candidate_url} liefert 200, aber Inhalt ist keine Datenschutzerklärung — ignoriert")

    return False


async def _collect_linked_css(url: str, soup: BeautifulSoup, session=None,
                              max_files: int = 10, max_bytes: int = 700_000) -> str:
    """
    Lädt die SAME-ORIGIN <link rel=stylesheet>-Dateien der Seite und gibt deren
    CSS-Text gebündelt zurück.

    Hintergrund: Drittanbieter-Ressourcen mit IP-Transfer (v.a. Google Fonts via
    @font-face/@import) stehen häufig NICHT im HTML, sondern erst im CSS der Seite
    — typisch bei Avada/WordPress (fusion-styles), wo die fonts.gstatic.com-URLs
    in der dynamisch generierten Theme-CSS liegen. Ohne diese Quelle übersieht die
    Drittlandtransfer-Erkennung den Klassiker „Google Fonts extern geladen".
    """
    from urllib.parse import urljoin, urlparse
    own = urlparse(url).netloc.lower()
    if own.startswith('www.'):
        own = own[4:]

    hrefs = []
    for link in soup.find_all('link', href=True):
        rels = ' '.join(link.get('rel', [])).lower() if link.get('rel') else ''
        if 'stylesheet' not in rels:
            continue
        href = (link.get('href') or '').strip()
        if not href:
            continue
        if href.startswith('//'):
            href = 'https:' + href
        full = urljoin(url, href)
        host = urlparse(full).netloc.lower()
        if host.startswith('www.'):
            host = host[4:]
        # Nur eigene CSS-Dateien holen. Fremd-gehostete CSS ist selbst bereits ein
        # Drittanbieter-Request und wird über die URL direkt erkannt.
        if not host or host != own:
            continue
        if full not in hrefs:
            hrefs.append(full)

    hrefs = hrefs[:max_files]
    if not hrefs:
        return ""

    close_session = False
    if session is None:
        import ssl
        import certifi
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        session = sichere_session(connector=aiohttp.TCPConnector(ssl=ssl_ctx))
        close_session = True

    chunks = []
    try:
        for h in hrefs:
            try:
                async with session.get(h, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        chunks.append((await resp.text())[:max_bytes])
            except Exception:
                continue
    finally:
        if close_session:
            await session.close()
    return "\n".join(chunks)


async def check_datenschutz_compliance(url: str, soup: BeautifulSoup, session=None,
                                       request_urls: List[str] = None) -> List[Dict[str, Any]]:
    """
    Prüft Datenschutzerklärung-Compliance

    1. Datenschutz-Link vorhanden (im gerenderten HTML oder als direkt erreichbare URL)
    2. Datenschutzerklärung-Inhalte (wenn erreichbar)
    3. Drittlandtransfer ohne Einwilligung (HTML + verlinkte CSS + echte Requests)
    """
    issues = []
    # Text der Datenschutzerklaerungs-SEITE (nicht Homepage). Wird im
    # Deep-Analyse-Block befuellt und unten fuer die Drittlandtransfer-
    # Rechtsgrundlagen-Pruefung genutzt (SCC/DPF stehen in der DS-Erklaerung,
    # nicht auf der Startseite).
    ds_page_text = None
    
    datenschutz_links = _find_datenschutz_links(soup, url)
    # Steht der Text im Dokument (Overlay, Abschnitt), wird er gelesen, statt
    # "keine Datenschutzerklaerung" zu melden. Fuehrt der beste Link nur auf
    # einen Anker der eigenen Seite, ist der Abschnitt selbst die genauere
    # Quelle als die ganze Seite.
    eingebettet = None
    if (not datenschutz_links
            or seitenlink_art(datenschutz_links[0].get('href')) == ART_ANKER):
        eingebettet = finde_eingebetteten_text(soup, 'datenschutz', _looks_like_datenschutz)
    
    logger.info(f"🔍 Datenschutz-Links gefunden: {len(datenschutz_links)}")
    for link in datenschutz_links[:3]:
        logger.info(f"   → {link.get('href', 'N/A')}: {link.get_text(strip=True)[:50]}")
    
    if not datenschutz_links and not eingebettet:
        datenschutz_url_exists = await _check_datenschutz_url_exists(url, session)
        if datenschutz_url_exists:
            logger.info("✅ Datenschutz per Direkt-URL-Check gefunden — kein Issue")
            return issues
        # ✅ HAUPTELEMENT FEHLT: Generiere alle Sub-Issues mit is_missing=True
        _attrappen = attrappen(soup, text_keywords=(
            'datenschutz', 'privacy', 'dsgvo', 'data protection',
        ))
        issues.append(asdict(DatenschutzIssue(
            category='datenschutz',
            severity='critical',
            title='Keine Datenschutzerklärung gefunden',
            description=('Es wurde kein Link zur Datenschutzerklärung gefunden. Eine Datenschutzerklärung ist nach DSGVO verpflichtend.'
                         + attrappen_satz(_attrappen)),
            risk_euro=5000,
            recommendation='Fügen Sie eine umfassende Datenschutzerklärung hinzu, die alle Pflichtangaben nach Art. 13-14 DSGVO enthält.',
            legal_basis='DSGVO Art. 13-14, DSGVO Art. 83 (Bußgeld bis 20 Mio. € oder 4% des Jahresumsatzes)',
            auto_fixable=True,
            is_missing=True
        )))
        
        # Alle Pflichtangaben als fehlend markieren
        issues.append(asdict(DatenschutzIssue(
            category='datenschutz',
            severity='critical',
            title='Verantwortlicher fehlt',
            description='Die Angabe des Verantwortlichen (Name und Kontaktdaten) fehlt in der Datenschutzerklärung.',
            risk_euro=3000,
            recommendation='Fügen Sie Name und Kontaktdaten des Verantwortlichen zur Datenschutzerklärung hinzu.',
            legal_basis='DSGVO Art. 13 Abs. 1 lit. a',
            auto_fixable=False,
            is_missing=True
        )))
        
        issues.append(asdict(DatenschutzIssue(
            category='datenschutz',
            severity='critical',
            title='Zwecke der Datenverarbeitung fehlen',
            description='Die Zwecke der Datenverarbeitung sind in der Datenschutzerklärung nicht angegeben.',
            risk_euro=3000,
            recommendation='Beschreiben Sie detailliert, zu welchen Zwecken Sie personenbezogene Daten verarbeiten.',
            legal_basis='DSGVO Art. 13 Abs. 1 lit. c',
            auto_fixable=False,
            is_missing=True
        )))
        
        issues.append(asdict(DatenschutzIssue(
            category='datenschutz',
            severity='critical',
            title='Rechtsgrundlagen fehlen',
            description='Die Rechtsgrundlagen für die Datenverarbeitung (Art. 6 DSGVO) fehlen in der Datenschutzerklärung.',
            risk_euro=3000,
            recommendation='Geben Sie die Rechtsgrundlagen (z.B. Einwilligung, Vertragserfüllung, berechtigtes Interesse) an.',
            legal_basis='DSGVO Art. 13 Abs. 1 lit. c',
            auto_fixable=False,
            is_missing=True
        )))
        
        issues.append(asdict(DatenschutzIssue(
            category='datenschutz',
            severity='critical',
            title='Speicherdauer fehlt',
            description='Die Angabe der Speicherdauer oder Kriterien zur Festlegung der Speicherdauer fehlt.',
            risk_euro=2000,
            recommendation='Geben Sie an, wie lange Sie personenbezogene Daten speichern oder nach welchen Kriterien Sie die Speicherdauer festlegen.',
            legal_basis='DSGVO Art. 13 Abs. 2 lit. a',
            auto_fixable=False,
            is_missing=True
        )))
        
        issues.append(asdict(DatenschutzIssue(
            category='datenschutz',
            severity='critical',
            title='Betroffenenrechte fehlen',
            description='Die Information über Betroffenenrechte (Auskunft, Berichtigung, Löschung, Widerruf) fehlt.',
            risk_euro=2500,
            recommendation='Informieren Sie über die Rechte der betroffenen Personen (Auskunft, Berichtigung, Löschung, Widerruf, Datenübertragbarkeit, Widerspruch).',
            legal_basis='DSGVO Art. 13 Abs. 2 lit. b',
            auto_fixable=False,
            is_missing=True
        )))
        
        issues.append(asdict(DatenschutzIssue(
            category='datenschutz',
            severity='critical',
            title='Beschwerderecht fehlt',
            description='Der Hinweis auf das Beschwerderecht bei einer Datenschutz-Aufsichtsbehörde fehlt.',
            risk_euro=2000,
            recommendation='Informieren Sie über das Recht, Beschwerde bei einer Aufsichtsbehörde einzulegen.',
            legal_basis='DSGVO Art. 13 Abs. 2 lit. d',
            auto_fixable=False,
            is_missing=True
        )))
        
        issues.append(asdict(DatenschutzIssue(
            category='datenschutz',
            severity='warning',
            title='Datenschutzbeauftragter fehlt',
            description='Die Kontaktdaten des Datenschutzbeauftragten fehlen (falls eine Benennung erforderlich ist).',
            risk_euro=1500,
            recommendation='Falls Sie einen Datenschutzbeauftragten benennen müssen, geben Sie dessen Kontaktdaten an.',
            legal_basis='DSGVO Art. 13 Abs. 1 lit. b, Art. 37-39 DSGVO',
            auto_fixable=False,
            is_missing=True
        )))
    else:
        # ✅ DEEP-ANALYSE: Link gefunden → Crawle und analysiere Datenschutz-Seite
        logger.info(f"✅ Datenschutz-Link gefunden, starte Deep-Analyse")
        
        try:
            from ..hybrid_validator import HybridValidator
            
            # Hole Datenschutz-URL (oder lies den Text aus dem Dokument)
            from urllib.parse import urljoin
            if eingebettet:
                datenschutz_href, datenschutz_url = '', url
            else:
                datenschutz_href = datenschutz_links[0].get('href', '')
                datenschutz_url = urljoin(url, datenschutz_href)
            
            # Fetche Datenschutz-Seite
            if session or eingebettet:
                if eingebettet:
                    geladen = eingebettete_seite(url, eingebettet)
                else:
                    geladen = await lade_rechtsseite(url, datenschutz_href, soup, session,
                                                     _looks_like_datenschutz,
                                                     duenn_aus_wie=_duenn_aus_wie)
                if not geladen.ok:
                    # Kein stiller Durchlauf, siehe rechtsseiten_links.
                    issues.append(_rechtsseiten_befund(geladen))
                else:
                    datenschutz_html = geladen.html
                    ds_page_text = datenschutz_html
                    if geladen.duenn:
                        issues.append(_duenn_befund(geladen))
                try:
                    if geladen.ok:
                        # Deep-Analyse mit Hybrid-Validator
                        validator = HybridValidator()
                        analysis = await validator.validate_page(
                            page_type="datenschutz",
                            text_content=datenschutz_html,
                            url=datenschutz_url
                        )
                        
                        # Generiere Issues nur für tatsächlich fehlende kritische Felder
                        critical_fields = {
                            "verantwortlicher": {
                                "title": "Verantwortlicher fehlt",
                                "description": "Die Angabe des Verantwortlichen fehlt in der Datenschutzerklärung.",
                                "risk": 3000,
                                "basis": "DSGVO Art. 13 Abs. 1 lit. a"
                            },
                            "zwecke": {
                                "title": "Zwecke der Datenverarbeitung fehlen",
                                "description": "Die Zwecke der Datenverarbeitung sind nicht angegeben.",
                                "risk": 3000,
                                "basis": "DSGVO Art. 13 Abs. 1 lit. c"
                            },
                            "rechtsgrundlage": {
                                "title": "Rechtsgrundlagen fehlen",
                                "description": "Die Rechtsgrundlagen für die Datenverarbeitung fehlen.",
                                "risk": 3000,
                                "basis": "DSGVO Art. 13 Abs. 1 lit. c"
                            },
                            "speicherdauer": {
                                "title": "Speicherdauer fehlt",
                                "description": "Die Angabe der Speicherdauer fehlt.",
                                "risk": 2000,
                                "basis": "DSGVO Art. 13 Abs. 2 lit. a"
                            },
                            "betroffenenrechte": {
                                "title": "Betroffenenrechte fehlen",
                                "description": "Die Information über Betroffenenrechte fehlt.",
                                "risk": 2500,
                                "basis": "DSGVO Art. 13 Abs. 2 lit. b"
                            },
                            "beschwerderecht": {
                                "title": "Beschwerderecht fehlt",
                                "description": "Der Hinweis auf das Beschwerderecht fehlt.",
                                "risk": 2000,
                                "basis": "DSGVO Art. 13 Abs. 2 lit. d"
                            }
                        }
                        
                        for field_result in analysis["results"]:
                            field_name = field_result["field"]
                            
                            # Ein Feld, das niemand nachgesehen hat, ist kein
                            # Mangel. Faellt die KI-Zweitmeinung aus (Budget
                            # gesperrt, Redis weg, kein Schluessel), traegt
                            # das Ergebnis nur noch die Vermutung des
                            # Musters — und unsicher war das Muster bei
                            # genau diesen Feldern. Am 09.09.2026 im
                            # Bestandsdurchlauf gemessen: der Befund
                            # "Zwecke der Datenverarbeitung fehlen" traf
                            # 20 von 24 Seiten ohne KI und 5 von 24 mit ihr.
                            if field_result.get("unverifiziert"):
                                continue

                            if not field_result["found"] and field_name in critical_fields:
                                field_info = critical_fields[field_name]
                                
                                issues.append(asdict(DatenschutzIssue(
                                    category='datenschutz',
                                    severity='critical',
                                    title=field_info["title"],
                                    description=field_info["description"],
                                    risk_euro=field_info["risk"],
                                    recommendation=f'Ergänzen Sie die Angabe zu: {field_name}',
                                    legal_basis=field_info["basis"],
                                    auto_fixable=False,
                                    is_missing=False  # Link existiert, nur Inhalt fehlt
                                )))
                        
                        # Was nicht geprueft werden konnte, gehoert in den Bericht.
                        #
                        # Seit dem 09.09.2026 uebergeht die Schleife oben Felder, deren
                        # KI-Zweitmeinung ausgefallen ist, statt sie als Mangel zu melden.
                        # Das allein waere nur die andere Haelfte des Fehlers: der Kunde saehe
                        # eine bessere Note und wuesste nicht, dass ein Teil ungeprueft blieb.
                        # "Geprueft und nichts gefunden" und "nicht geprueft" duerfen sich
                        # nicht gleich lesen.
                        _ungeprueft = [f["field"] for f in analysis["results"] if f.get("unverifiziert")]
                        if _ungeprueft:
                            issues.append(asdict(DatenschutzIssue(
                                category='datenschutz',
                                severity='info',
                                title='Datenschutzerklärung: {} Angabe(n) nicht abschliessend geprueft'.format(len(_ungeprueft)),
                                description=(
                                    'Diese Angaben liessen sich maschinell nicht sicher feststellen und '
                                    'wurden deshalb weder als vorhanden noch als fehlend gewertet: '
                                    + ', '.join(_ungeprueft) + '. '
                                    'Bitte pruefen Sie sie von Hand. Ein spaeterer Scan kann hier zu '
                                    'einem eindeutigen Ergebnis kommen.'
                                ),
                                risk_euro=0,
                                recommendation='Sehen Sie die genannten Angaben selbst nach.',
                                legal_basis='DSGVO Art. 13',
                                auto_fixable=False,
                                is_missing=False,
                            )))

                        # Qualitäts-Warnung bei niedriger Qualität
                        if analysis["quality"] in ["poor", "insufficient"]:
                            issues.append(asdict(DatenschutzIssue(
                                category='datenschutz',
                                severity='warning',
                                title='Datenschutzerklärung unvollständig',
                                description=f'Die Datenschutzerklärung wurde gefunden, ist aber unvollständig (Qualität: {analysis["quality"]}). Mehrere Pflichtangaben fehlen.',
                                risk_euro=5000,
                                recommendation='Vervollständigen Sie Ihre Datenschutzerklärung mit allen Pflichtangaben nach DSGVO Art. 13-14.',
                                legal_basis='DSGVO Art. 13-14',
                                auto_fixable=True,
                                is_missing=False
                            )))
                        
                        logger.info(f"✅ Deep-Analyse abgeschlossen: {analysis['quality']} ({len(issues)} Issues)")

                except Exception as e:
                    logger.warning(f"⚠️ Deep-Analyse fehlgeschlagen: {e}")
                    # Kein Silent-Pass: Der Nutzer erfaehrt, dass die inhaltliche
                    # Pruefung NICHT stattfand (sonst wirkt eine ungepruefte
                    # Datenschutzerklaerung faelschlich als vollstaendig).
                    issues.append(asdict(DatenschutzIssue(
                        category='datenschutz',
                        severity='info',
                        title='Inhaltsprüfung der Datenschutzerklärung nicht möglich',
                        description=(
                            'Die Datenschutzerklärung wurde gefunden, konnte aber nicht '
                            'inhaltlich geprüft werden (Seite nicht ladbar oder Analyse '
                            'fehlgeschlagen). Die Vollständigkeit nach Art. 13/14 DSGVO '
                            'ist damit NICHT bestätigt.'
                        ),
                        risk_euro=0,
                        recommendation=(
                            'Prüfen Sie die Erreichbarkeit der Datenschutzerklärung und '
                            'wiederholen Sie den Scan.'
                        ),
                        legal_basis='DSGVO Art. 13/14',
                        auto_fixable=False,
                        is_missing=False
                    )))
        
        except ImportError:
            logger.warning("⚠️ HybridValidator nicht verfügbar - überspringe Deep-Analyse")
            # Auch dieser Pfad darf nicht still durchlaufen (siehe oben).
            issues.append(asdict(DatenschutzIssue(
                category="datenschutz",
                severity="info",
                title="Inhaltsprüfung der Datenschutzerklärung nicht möglich",
                description=(
                    "Die Datenschutzerklärung wurde gefunden, konnte aber nicht "
                    "inhaltlich geprüft werden (Analyse-Komponente nicht verfügbar). "
                    "Die Vollständigkeit nach Art. 13/14 DSGVO ist damit NICHT bestätigt."
                ),
                risk_euro=0,
                recommendation="Wiederholen Sie den Scan; bei wiederholtem Auftreten Support kontaktieren.",
                legal_basis="DSGVO Art. 13/14",
                auto_fixable=False,
                is_missing=False
            )))
    
    html_raw = str(soup)
    html_text = html_raw.lower()

    # Drittlandtransfer ohne Einwilligung (Google Fonts, reCAPTCHA, Maps, YouTube,
    # Adobe/Typekit ...) — cookielose IP-Übertragung in die USA, der klassische
    # 100%-abmahnbare DSGVO-Verstoß, den ein reiner Cookie-Scanner nicht sieht.
    # Einzige Quelle: compliance_engine/privacy_transfer_findings (SSOT).
    #
    # Erkennung gegen drei Quellen, damit JS-/CSS-versteckte Transfers nicht
    # durchrutschen:
    #   1) HTML der Seite
    #   2) Inhalt der verlinkten Same-Origin-CSS (Google Fonts liegen oft als
    #      @font-face in der Theme-CSS, nicht im HTML — z.B. Avada/fusion-styles)
    #   3) tatsächlich beobachtete Netzwerk-Requests aus dem Headless-Render
    from ..privacy_transfer_findings import detect_transfers
    try:
        css_text = await _collect_linked_css(url, soup, session)
    except Exception as e:
        logger.warning(f"⚠️ CSS-Sammlung für Transfer-Erkennung fehlgeschlagen: {e}")
        css_text = ""
    transfer_haystack = html_raw if not css_text else (html_raw + "\n" + css_text)
    transfer_findings = detect_transfers(html=transfer_haystack, request_urls=request_urls)
    for finding in transfer_findings:
        issues.append(asdict(DatenschutzIssue(
            category='datenschutz',
            severity=finding['severity'],
            title=finding['title'],
            description=finding['description'],
            risk_euro=finding['risk_euro'],
            recommendation=finding['recommendation'],
            legal_basis=finding['legal_basis'],
            auto_fixable=finding['auto_fixable'],
            is_missing=False,
        )))

    # US-Drittanbieter ohne erkennbare Rechtsgrundlage in Datenschutzerklärung
    us_services = {
        'Google Analytics / GTM': r'google-analytics\.com|googletagmanager\.com',
        'Meta Pixel': r'connect\.facebook\.net|facebook\.com/tr',
        'HubSpot': r'js\.hs-scripts\.com|hubspot\.com',
        'Hotjar': r'static\.hotjar\.com',
        'Intercom': r'widget\.intercom\.io',
        'Salesforce': r'salesforce\.com/analytics',
        'Stripe': r'js\.stripe\.com',
    }
    found_us_services = []
    for name, pattern in us_services.items():
        if re.search(pattern, html_text, re.I):
            found_us_services.append(name)

    if found_us_services:
        # Rechtsgrundlagen-Nachweis (SCC/DPF/Angemessenheit) gehoert in die
        # DATENSCHUTZERKLAERUNG — dort pruefen, wenn die Seite geladen werden
        # konnte. Homepage nur als Fallback (frueher wurde IMMER die Homepage
        # geprueft -> systematische False Positives bei korrekt dokumentierten SCCs).
        transfer_haystack_text = ds_page_text.lower() if ds_page_text else html_text
        has_transfer_basis = bool(re.search(
            r'standardvertragsklausel|standard contractual clause|scc|data privacy framework|dpf|'
            r'angemessenheitsbeschluss|adequacy decision',
            transfer_haystack_text, re.I
        ))
        has_privacy_shield_only = bool(re.search(r'privacy.shield', transfer_haystack_text, re.I)) and not has_transfer_basis
        if not has_transfer_basis:
            if has_privacy_shield_only:
                issues.append(asdict(DatenschutzIssue(
                    category='avv',
                    severity='critical',
                    title=f'Privacy Shield als Transferbasis ungültig (Schrems II)',
                    description=(
                        f'Die Datenschutzerklärung verweist noch auf das Privacy Shield als Rechtsgrundlage '
                        f'für US-Datentransfers. Das Privacy Shield wurde am 16.07.2020 durch den EuGH '
                        f'(Schrems II, C-311/18) für ungültig erklärt. Folgende US-Dienste wurden erkannt: '
                        f'{", ".join(found_us_services)}.'
                    ),
                    risk_euro=5000,
                    recommendation=(
                        'Ersetzen Sie den Privacy-Shield-Verweis durch aktuelle Rechtsgrundlagen: '
                        'Standardvertragsklauseln (SCCs, aktualisiert 04.06.2021) oder das '
                        'EU-US Data Privacy Framework (DPF, gültig seit 10.07.2023).'
                    ),
                    legal_basis='DSGVO Art. 44 ff., EuGH C-311/18 (Schrems II), Art. 13 Abs. 1 lit. f',
                    auto_fixable=False,
                    is_missing=False,
                )))
            else:
                issues.append(asdict(DatenschutzIssue(
                    category='avv',
                    severity='warning',
                    title=f'US-Dienste ohne Drittland-Rechtsgrundlage in DS ({", ".join(found_us_services[:3])})',
                    description=(
                        f'Folgende US-Dienste wurden auf der Seite erkannt: {", ".join(found_us_services)}. '
                        f'In der Datenschutzerklärung fehlt ein erkennbarer Hinweis auf die Rechtsgrundlage '
                        f'für den Datentransfer in die USA (Standardvertragsklauseln, EU-US Data Privacy Framework).'
                    ),
                    risk_euro=3000,
                    recommendation=(
                        'Ergänzen Sie die Datenschutzerklärung um: (1) Nennung jedes US-Dienstes, '
                        '(2) Rechtsgrundlage für den Drittlandtransfer (SCCs oder EU-US DPF), '
                        '(3) Link zu den Garantien des Anbieters.'
                    ),
                    legal_basis='DSGVO Art. 44 ff., Art. 13 Abs. 1 lit. f',
                    auto_fixable=False,
                    is_missing=False,
                )))

    # AVV-Pflicht (DSGVO Art. 28): Sobald externe Dienstleister personenbezogene
    # Daten im Auftrag verarbeiten (Drittland-Transfers, US-Dienste, eingebundene
    # Tools), ist ein Auftragsverarbeitungsvertrag erforderlich. Das lässt sich
    # extern nicht verifizieren → informativer Hinweis (kein Score-Abzug).
    if transfer_findings or found_us_services:
        detected_processors = sorted({
            *(f.get('title', '').split('(')[0].strip() for f in transfer_findings),
            *found_us_services,
        })
        issues.append(asdict(DatenschutzIssue(
            category='avv',
            severity='info',
            title='Auftragsverarbeitungsverträge (AVV) erforderlich',
            description=(
                'Es wurden externe Dienste erkannt, die personenbezogene Daten im Auftrag '
                'verarbeiten könnten: ' + ', '.join(detected_processors[:6]) + '. '
                'Für jeden Auftragsverarbeiter ist ein Vertrag nach Art. 28 DSGVO abzuschließen.'
            ),
            risk_euro=0,
            recommendation=(
                'Schließen Sie mit jedem eingesetzten Dienstleister einen '
                'Auftragsverarbeitungsvertrag (AVV) ab und führen Sie ein Verzeichnis von '
                'Verarbeitungstätigkeiten (Art. 30 DSGVO).'
            ),
            legal_basis='DSGVO Art. 28, Art. 30',
            auto_fixable=False,
            is_missing=False,
        )))

    return issues

