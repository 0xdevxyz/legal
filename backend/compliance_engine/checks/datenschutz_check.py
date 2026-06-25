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


def _find_datenschutz_links(soup: BeautifulSoup) -> List:
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
    
    return all_links


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
            async with aiohttp.ClientSession(connector=connector) as temp_session:
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


def _looks_like_datenschutz(text: str) -> bool:
    """
    Inhalts-Heuristik gegen Soft-404 / Catch-all: Sieht der Seitentext wirklich
    wie eine Datenschutzerklärung aus? Erfordert einen DSGVO-Schlüsselbegriff UND
    mindestens ein typisches inhaltliches Pflichtmerkmal.
    """
    if not text:
        return False
    low = text.lower()
    keyword = any(k in low for k in (
        'datenschutz', 'privacy policy', 'data protection', 'dsgvo', 'gdpr',
    ))
    if not keyword:
        return False
    markers = (
        'verantwortlich', 'personenbezogene daten', 'rechtsgrundlage',
        'art. 6', 'betroffenenrechte', 'auskunftsrecht', 'speicherdauer',
        'verarbeitung', 'aufsichtsbehörde',
    )
    return sum(1 for m in markers if m in low) >= 2


async def _fetch_candidate_text(candidate_url: str, session, ssl_context) -> "tuple[int, str] | None":
    """Lädt eine Kandidaten-URL und gibt (status, text) zurück; None bei Fehler."""
    try:
        if session:
            async with session.get(candidate_url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as resp:
                return resp.status, (await resp.text() if resp.status == 200 else "")
        else:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as tmp:
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
    if probe and probe[0] == 200 and len(probe[1].strip()) > 200:
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
        if _looks_like_datenschutz(result[1]):
            logger.info(f"✅ Datenschutz-URL mit validem Inhalt gefunden: {candidate_url}")
            return True
        logger.info(f"↪️ {candidate_url} liefert 200, aber Inhalt ist keine Datenschutzerklärung — ignoriert")

    return False


async def check_datenschutz_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Prüft Datenschutzerklärung-Compliance
    
    1. Datenschutz-Link vorhanden (im gerenderten HTML oder als direkt erreichbare URL)
    2. Datenschutzerklärung-Inhalte (wenn erreichbar)
    """
    issues = []
    
    datenschutz_links = _find_datenschutz_links(soup)
    
    logger.info(f"🔍 Datenschutz-Links gefunden: {len(datenschutz_links)}")
    for link in datenschutz_links[:3]:
        logger.info(f"   → {link.get('href', 'N/A')}: {link.get_text(strip=True)[:50]}")
    
    if not datenschutz_links:
        datenschutz_url_exists = await _check_datenschutz_url_exists(url, session)
        if datenschutz_url_exists:
            logger.info("✅ Datenschutz per Direkt-URL-Check gefunden — kein Issue")
            return issues
        # ✅ HAUPTELEMENT FEHLT: Generiere alle Sub-Issues mit is_missing=True
        issues.append(asdict(DatenschutzIssue(
            category='datenschutz',
            severity='critical',
            title='Keine Datenschutzerklärung gefunden',
            description='Es wurde kein Link zur Datenschutzerklärung gefunden. Eine Datenschutzerklärung ist nach DSGVO verpflichtend.',
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
            
            # Hole Datenschutz-URL
            datenschutz_link = datenschutz_links[0]
            datenschutz_href = datenschutz_link.get('href', '')
            
            # Erstelle absolute URL
            from urllib.parse import urljoin
            datenschutz_url = urljoin(url, datenschutz_href)
            
            # Fetche Datenschutz-Seite
            if session:
                try:
                    async with session.get(datenschutz_url, timeout=10) as response:
                        if response.status == 200:
                            datenschutz_html = await response.text()
                            
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
                    # Fallback: Keine zusätzlichen Issues
        
        except ImportError:
            logger.warning("⚠️ HybridValidator nicht verfügbar - überspringe Deep-Analyse")
    
    html_raw = str(soup)
    html_text = html_raw.lower()

    # Drittlandtransfer ohne Einwilligung (Google Fonts, reCAPTCHA, Maps, YouTube,
    # Adobe/Typekit ...) — cookielose IP-Übertragung in die USA, der klassische
    # 100%-abmahnbare DSGVO-Verstoß, den ein reiner Cookie-Scanner nicht sieht.
    # Einzige Quelle: compliance_engine/privacy_transfer_findings (SSOT).
    from ..privacy_transfer_findings import detect_transfers
    transfer_findings = detect_transfers(html=html_raw)
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
        # Prüfe ob US-Dienste in der Datenschutzerklärung erwähnt werden
        # (Heuristik: Prüfe ob Schlüsselwörter wie 'standardvertragsklauseln', 'dsgvo-e.u.s.a.', 'dpf' vorhanden)
        has_transfer_basis = bool(re.search(
            r'standardvertragsklausel|standard contractual clause|scc|data privacy framework|dpf|'
            r'angemessenheitsbeschluss|adequacy decision',
            html_text, re.I
        ))
        has_privacy_shield_only = bool(re.search(r'privacy.shield', html_text, re.I)) and not has_transfer_basis
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

