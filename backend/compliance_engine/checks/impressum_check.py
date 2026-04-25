"""
Impressum Check (TMG §5)
Prüft Impressum-Compliance

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
class ImpressumIssue:
    category: str
    severity: str
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool = False
    is_missing: bool = False  # True wenn komplettes Element fehlt (nicht nur Unterpunkt)


def _find_impressum_links(soup: BeautifulSoup) -> List:
    """
    Verbesserte Suche nach Impressum-Links
    Findet auch Links in modernen JS-Frameworks (React, Vue, Next.js)
    """
    all_links = []
    
    href_keywords = [
        'impressum', 'imprint', 'legal-notice', 'legal_notice',
        'legal-information', 'legal_information', 'site-notice', 'site_notice',
        'disclosure', 'pflichtangaben', 'anbieterkennzeichnung',
        '/legal', '/about/legal',
    ]
    text_keywords = [
        'impressum', 'imprint', 'legal notice', 'rechtliche hinweise',
        'anbieterkennzeichnung', 'pflichtangaben', 'site notice',
    ]
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '').lower()
        link_text = a_tag.get_text(strip=True).lower()
        aria_label = (a_tag.get('aria-label') or '').lower()
        title = (a_tag.get('title') or '').lower()
        
        if any(kw in href for kw in href_keywords):
            all_links.append(a_tag)
        elif any(kw in link_text for kw in text_keywords):
            all_links.append(a_tag)
        elif any(kw in aria_label for kw in text_keywords):
            all_links.append(a_tag)
        elif any(kw in title for kw in text_keywords):
            all_links.append(a_tag)
    
    return all_links


async def check_impressum_compliance_smart(url: str, html: str = None, session=None) -> List[Dict[str, Any]]:
    """
    SMART Impressum-Check mit Browser-Rendering für JS-Websites
    
    Erkennt automatisch Client-Side-Rendering (React, Vue, Next.js)
    und rendert die Seite vollständig im Browser.
    """
    from ..browser_renderer import smart_fetch_html, detect_client_rendering
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        logger.info(f"✅ URL normalized to: {url}")
    
    logger.info(f"🔍 Smart Impressum-Check für: {url}")
    
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
            logger.info(f"🌐 Browser needed for Impressum check: {reason}")
            html, metadata = await smart_fetch_html(url, html)
            logger.info(f"✅ Browser rendering completed: {metadata.get('rendering_type', 'unknown')}")
        else:
            logger.info(f"⚡ Server-rendered detected, using simple HTML for Impressum check")
        
        soup = BeautifulSoup(html, 'html.parser')
        return await check_impressum_compliance(url, soup, session)
        
    except Exception as e:
        logger.error(f"❌ Smart Impressum check failed: {e}")
        soup = BeautifulSoup(html if html else "", 'html.parser')
        return await check_impressum_compliance(url, soup, session)


async def _check_impressum_url_exists(base_url: str, session=None) -> bool:
    """
    Prüft direkt bekannte Impressum-Pfade per HTTP-Request.
    Fallback für clientseitig gerenderte Seiten (Next.js, React SPA).
    """
    from urllib.parse import urlparse, urljoin
    import ssl
    import certifi

    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    candidate_paths = ['/impressum', '/imprint', '/legal-notice', '/legal', '/ueber-uns/impressum', '/about/imprint']

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    for path in candidate_paths:
        candidate_url = base + path
        try:
            if session:
                async with session.get(candidate_url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Impressum-URL direkt gefunden: {candidate_url}")
                        return True
            else:
                import aiohttp as _aiohttp
                connector = _aiohttp.TCPConnector(ssl=ssl_context)
                async with _aiohttp.ClientSession(connector=connector) as tmp:
                    async with tmp.get(candidate_url, timeout=_aiohttp.ClientTimeout(total=8), allow_redirects=True) as resp:
                        if resp.status == 200:
                            logger.info(f"✅ Impressum-URL direkt gefunden: {candidate_url}")
                            return True
        except Exception:
            continue

    return False


async def check_impressum_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Prüft Impressum-Compliance
    
    1. Impressum-Link vorhanden (im gerenderten HTML oder als direkt erreichbare URL)
    2. Impressum-Inhalte (wenn erreichbar)
    """
    issues = []
    impressum_html: str | None = None
    impressum_found: bool = False

    all_impressum_links = _find_impressum_links(soup)
    
    logger.info(f"🔍 Impressum-Links gefunden: {len(all_impressum_links)}")
    for link in all_impressum_links[:3]:
        logger.info(f"   → {link.get('href', 'N/A')}: {link.get_text(strip=True)[:50]}")
    
    if not all_impressum_links:
        impressum_url_exists = await _check_impressum_url_exists(url, session)
        if impressum_url_exists:
            logger.info("✅ Impressum per Direkt-URL-Check gefunden — kein Issue")
            impressum_found = True
        else:
            issues.append(asdict(ImpressumIssue(
                category='impressum',
                severity='critical',
                title='Kein Impressum-Link gefunden',
                description='Es wurde kein Link zum Impressum gefunden. Ein Impressum ist gesetzlich verpflichtend für alle geschäftsmäßigen Telemedien.',
                risk_euro=3000,
                recommendation='Fügen Sie einen deutlich sichtbaren Impressum-Link im Footer hinzu.',
                legal_basis='DDG §5 (Digitale-Dienste-Gesetz)',
                auto_fixable=True,
                is_missing=True
            )))
            
            issues.append(asdict(ImpressumIssue(
                category='impressum',
                severity='critical',
                title='Firmenname/Name fehlt',
                description='Die Angabe des vollständigen Firmennamens (bei Unternehmen) oder des vollständigen Namens (bei Einzelpersonen) fehlt im Impressum.',
                risk_euro=2000,
                recommendation='Fügen Sie den vollständigen Firmennamen bzw. Ihren Namen zum Impressum hinzu.',
                legal_basis='DDG §5 Abs. 1 Nr. 1',
                auto_fixable=False,
                is_missing=True
            )))
            
            issues.append(asdict(ImpressumIssue(
                category='impressum',
                severity='critical',
                title='Anschrift fehlt',
                description='Die vollständige Postanschrift (Straße, Hausnummer, PLZ, Ort) fehlt im Impressum. Postfächer sind nicht ausreichend.',
                risk_euro=2000,
                recommendation='Fügen Sie die vollständige Geschäftsadresse zum Impressum hinzu.',
                legal_basis='DDG §5 Abs. 1 Nr. 2',
                auto_fixable=False,
                is_missing=True
            )))
            
            issues.append(asdict(ImpressumIssue(
                category='impressum',
                severity='critical',
                title='E-Mail-Adresse fehlt',
                description='Es fehlt eine E-Mail-Adresse für eine schnelle elektronische Kontaktaufnahme im Impressum.',
                risk_euro=1500,
                recommendation='Fügen Sie eine gültige E-Mail-Adresse zum Impressum hinzu.',
                legal_basis='DDG §5 Abs. 1 Nr. 2',
                auto_fixable=False,
                is_missing=True
            )))
            
            issues.append(asdict(ImpressumIssue(
                category='impressum',
                severity='warning',
                title='Telefonnummer fehlt',
                description='Es fehlt eine Telefonnummer im Impressum. Laut BGH (I ZR 214/14) reicht eine E-Mail-Adresse als schnelle elektronische Kontaktmöglichkeit aus — Telefon ist empfohlen aber nicht zwingend.',
                risk_euro=500,
                recommendation='Fügen Sie eine erreichbare Telefonnummer zum Impressum hinzu (empfohlen).',
                legal_basis='DDG §5 Abs. 1 Nr. 2, BGH I ZR 214/14',
                auto_fixable=False,
                is_missing=True
            )))
            
            issues.append(asdict(ImpressumIssue(
                category='impressum',
                severity='warning',
                title='Handelsregister/Registernummer fehlt',
                description='Die Angabe der Rechtsform und ggf. Registernummer (Handelsregister, Vereinsregister, etc.) fehlt im Impressum.',
                risk_euro=1000,
                recommendation='Fügen Sie die Rechtsform und Registernummer (falls vorhanden) zum Impressum hinzu.',
                legal_basis='DDG §5 Abs. 1 Nr. 3',
                auto_fixable=False,
                is_missing=True
            )))
            
            issues.append(asdict(ImpressumIssue(
                category='impressum',
                severity='warning',
                title='Umsatzsteuer-ID fehlt',
                description='Die Umsatzsteuer-Identifikationsnummer fehlt im Impressum (falls vorhanden).',
                risk_euro=1000,
                recommendation='Fügen Sie Ihre Umsatzsteuer-ID zum Impressum hinzu (falls Sie eine besitzen).',
                legal_basis='DDG §5 Abs. 1 Nr. 6, §27a UStG',
                auto_fixable=False,
                is_missing=True
            )))
    else:
        impressum_found = True
        logger.info(f"✅ Impressum-Link gefunden, starte Deep-Analyse")
        
        try:
            from ..hybrid_validator import HybridValidator
            
            impressum_link = all_impressum_links[0]
            impressum_href = impressum_link.get('href', '')
            
            from urllib.parse import urljoin
            impressum_url = urljoin(url, impressum_href)
            
            if session:
                try:
                    async with session.get(impressum_url, timeout=10) as response:
                        if response.status == 200:
                            impressum_html = await response.text()
                            
                            validator = HybridValidator()
                            analysis = await validator.validate_page(
                                page_type="impressum",
                                text_content=impressum_html,
                                url=impressum_url
                            )
                            
                            for field_result in analysis["results"]:
                                if not field_result["found"] and field_result["field"] in ["firmenname", "adresse", "email", "telefon"]:
                                    risk_euros = {
                                        "firmenname": 2000,
                                        "adresse": 2000,
                                        "email": 1500,
                                        "telefon": 1500
                                    }
                                    titles = {
                                        "firmenname": "Firmenname/Name fehlt im Impressum",
                                        "adresse": "Anschrift fehlt im Impressum",
                                        "email": "E-Mail-Adresse fehlt im Impressum",
                                        "telefon": "Telefonnummer fehlt im Impressum"
                                    }
                                    descriptions = {
                                        "firmenname": "Die Angabe des vollständigen Firmennamens fehlt im Impressum.",
                                        "adresse": "Die vollständige Postanschrift fehlt im Impressum.",
                                        "email": "Es fehlt eine E-Mail-Adresse für Kontaktaufnahme.",
                                        "telefon": "Es fehlt eine Telefonnummer für Kontaktaufnahme."
                                    }
                                    issues.append(asdict(ImpressumIssue(
                                        category='impressum',
                                        severity='critical',
                                        title=titles[field_result["field"]],
                                        description=descriptions[field_result["field"]],
                                        risk_euro=risk_euros[field_result["field"]],
                                        recommendation=f'Fügen Sie {field_result["field"]} zum Impressum hinzu.',
                                        legal_basis='DDG §5',
                                        auto_fixable=False,
                                        is_missing=False
                                    )))
                            
                            if analysis["quality"] in ["poor", "insufficient"]:
                                issues.append(asdict(ImpressumIssue(
                                    category='impressum',
                                    severity='warning',
                                    title='Impressum unvollständig',
                                    description=f'Das Impressum wurde gefunden, ist aber unvollständig (Qualität: {analysis["quality"]}). Mehrere Pflichtangaben fehlen oder sind unzureichend.',
                                    risk_euro=3000,
                                    recommendation='Vervollständigen Sie Ihr Impressum mit allen Pflichtangaben nach DDG §5.',
                                    legal_basis='DDG §5',
                                    auto_fixable=True,
                                    is_missing=False
                                )))
                            
                            logger.info(f"✅ Deep-Analyse abgeschlossen: {analysis['quality']} ({len(issues)} Issues)")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Deep-Analyse fehlgeschlagen: {e}")
        
        except ImportError:
            logger.warning("⚠️ HybridValidator nicht verfügbar - überspringe Deep-Analyse")

    # DDG-spezifische Zusatzchecks
    html_text = str(soup).lower()

    # OS-Plattform-Link nach 20.07.2025 muss entfernt werden (ganzer Seiten-HTML ist korrekt)
    if 'ec.europa.eu/consumers/odr' in html_text or 'webgate.ec.europa.eu/odr' in html_text:
        issues.append(asdict(ImpressumIssue(
            category='impressum',
            severity='warning',
            title='Veralteter OS-Plattform-Link muss entfernt werden',
            description=(
                'Die Website enthält noch einen Link zur EU-OS-Plattform (ec.europa.eu/consumers/odr). '
                'Die ODR-Verordnung wurde zum 20.07.2025 aufgehoben. Ab diesem Datum ist der Link '
                'nicht mehr nur überflüssig, sondern kann irreführend wirken.'
            ),
            risk_euro=500,
            recommendation='Entfernen Sie den Link zur EU-OS-Plattform aus Impressum und Datenschutzerklärung.',
            legal_basis='Verordnung (EU) Nr. 524/2013, aufgehoben ab 20.07.2025',
            auto_fixable=True,
            is_missing=False,
        )))

    # Rechtsform-spezifische Checks: nur wenn Impressum vorhanden und dessen Inhalt gecrawlt wurde
    if impressum_found and impressum_html is not None:
        imp_text = impressum_html.lower()

        # Rechtsform erkennen
        is_gmbh_ug = bool(re.search(r'\b(gmbh|ug\s*\(haftungsbeschränkt\))\b', imp_text, re.I))
        is_ag_se    = bool(re.search(r'\b(ag\b|aktiengesellschaft|se\b|societas europaea)\b', imp_text, re.I))
        is_ohg_kg   = bool(re.search(r'\b(ohg|offene handelsgesellschaft|kg\b|kommanditgesellschaft|e\.k\.|eingetragener kaufmann)\b', imp_text, re.I))
        is_ev       = bool(re.search(r'\b(e\.v\.|eingetragener verein)\b', imp_text, re.I))
        is_gbr      = bool(re.search(r'\b(gbr|gesellschaft bürgerlichen rechts|gesellschaft des bürgerlichen rechts)\b', imp_text, re.I))

        has_hr_entry     = bool(re.search(r'\b(hrb|hra|amtsgericht|registergericht|handelsregister)\b', imp_text, re.I))
        has_vr_entry     = bool(re.search(r'\b(vr\s*\d|vereinsregister|amtsgericht)\b', imp_text, re.I))
        has_geschaeftsfuehrer = bool(re.search(r'\b(geschäftsführer|geschaeftsfuehrer|managing director|vertreten durch)\b', imp_text, re.I))
        has_vorstand     = bool(re.search(r'\b(vorstand|vorstandsvorsitzender|ceo|aufsichtsrat)\b', imp_text, re.I))
        has_gesellschafter = bool(re.search(r'\b(gesellschafter|partner)\b', imp_text, re.I))
        has_inhaber      = bool(re.search(r'\b(inhaber|inh\.|einzelunternehmen)\b', imp_text, re.I))

        if is_gmbh_ug:
            # Handelsregister (HRB) Pflicht
            if not has_hr_entry:
                issues.append(asdict(ImpressumIssue(
                    category='impressum',
                    severity='warning',
                    title='Handelsregisternummer fehlt (GmbH/UG erkannt)',
                    description=(
                        'Das Impressum enthält eine GmbH oder UG, jedoch fehlt die Handelsregisternummer '
                        '(HRB) und das Registergericht. Diese Angaben sind für eingetragene Gesellschaften '
                        'nach DDG §5 Abs. 1 Nr. 4 verpflichtend.'
                    ),
                    risk_euro=1500,
                    recommendation='Fügen Sie Handelsregisternummer (z.B. HRB 12345) und Registergericht (z.B. Amtsgericht München) zum Impressum hinzu.',
                    legal_basis='DDG §5 Abs. 1 Nr. 4',
                    auto_fixable=False,
                    is_missing=False,
                )))
            # Geschäftsführer Pflicht
            if not has_geschaeftsfuehrer:
                issues.append(asdict(ImpressumIssue(
                    category='impressum',
                    severity='warning',
                    title='Geschäftsführer nicht angegeben (GmbH/UG erkannt)',
                    description=(
                        'Das Impressum enthält eine GmbH oder UG, jedoch wurde kein Geschäftsführer gefunden. '
                        'Bei GmbH und UG muss der/die Geschäftsführer namentlich im Impressum genannt werden.'
                    ),
                    risk_euro=1000,
                    recommendation='Nennen Sie alle Geschäftsführer namentlich im Impressum.',
                    legal_basis='DDG §5 Abs. 1 Nr. 1, GmbHG §35',
                    auto_fixable=False,
                    is_missing=False,
                )))

        elif is_ag_se:
            # Handelsregister (HRB) + Vorstand + Aufsichtsrat Pflicht
            if not has_hr_entry:
                issues.append(asdict(ImpressumIssue(
                    category='impressum',
                    severity='warning',
                    title='Handelsregisternummer fehlt (AG/SE erkannt)',
                    description=(
                        'Das Impressum enthält eine AG oder SE, jedoch fehlt die Handelsregisternummer '
                        '(HRB) und das Registergericht.'
                    ),
                    risk_euro=1500,
                    recommendation='Fügen Sie Handelsregisternummer (z.B. HRB 12345) und Registergericht zum Impressum hinzu.',
                    legal_basis='DDG §5 Abs. 1 Nr. 4, AktG §80',
                    auto_fixable=False,
                    is_missing=False,
                )))
            if not has_vorstand:
                issues.append(asdict(ImpressumIssue(
                    category='impressum',
                    severity='warning',
                    title='Vorstand/Aufsichtsrat nicht angegeben (AG/SE erkannt)',
                    description=(
                        'Das Impressum enthält eine AG oder SE, jedoch fehlen Angaben zum Vorstand und '
                        'Aufsichtsratsvorsitzenden. Diese sind nach AktG §80 und DDG §5 verpflichtend.'
                    ),
                    risk_euro=1000,
                    recommendation='Nennen Sie Vorstandsmitglieder und den Aufsichtsratsvorsitzenden namentlich im Impressum.',
                    legal_basis='DDG §5 Abs. 1 Nr. 1, AktG §80',
                    auto_fixable=False,
                    is_missing=False,
                )))

        elif is_ohg_kg:
            # Handelsregister (HRA) + vertretungsberechtigte Gesellschafter Pflicht
            if not has_hr_entry:
                issues.append(asdict(ImpressumIssue(
                    category='impressum',
                    severity='warning',
                    title='Handelsregisternummer fehlt (OHG/KG/e.K. erkannt)',
                    description=(
                        'Das Impressum enthält eine OHG, KG oder einen eingetragenen Kaufmann, jedoch fehlt '
                        'die Handelsregisternummer (HRA) und das Registergericht.'
                    ),
                    risk_euro=1500,
                    recommendation='Fügen Sie Handelsregisternummer (z.B. HRA 12345) und Registergericht zum Impressum hinzu.',
                    legal_basis='DDG §5 Abs. 1 Nr. 4',
                    auto_fixable=False,
                    is_missing=False,
                )))
            if not has_gesellschafter and not has_inhaber and not has_geschaeftsfuehrer:
                issues.append(asdict(ImpressumIssue(
                    category='impressum',
                    severity='warning',
                    title='Vertretungsberechtigte Person nicht angegeben (OHG/KG/e.K. erkannt)',
                    description=(
                        'Das Impressum enthält eine OHG, KG oder einen eingetragenen Kaufmann, jedoch fehlt '
                        'die Angabe der vertretungsberechtigten Person(en) bzw. des Inhabers.'
                    ),
                    risk_euro=1000,
                    recommendation='Nennen Sie alle vertretungsberechtigten Gesellschafter bzw. den Inhaber namentlich im Impressum.',
                    legal_basis='DDG §5 Abs. 1 Nr. 1',
                    auto_fixable=False,
                    is_missing=False,
                )))

        elif is_ev:
            # Vereinsregister (VR) + Vorstand Pflicht
            if not has_vr_entry:
                issues.append(asdict(ImpressumIssue(
                    category='impressum',
                    severity='warning',
                    title='Vereinsregisternummer fehlt (e.V. erkannt)',
                    description=(
                        'Das Impressum enthält einen eingetragenen Verein, jedoch fehlt die Vereinsregisternummer '
                        '(VR) und das Registergericht.'
                    ),
                    risk_euro=1000,
                    recommendation='Fügen Sie Vereinsregisternummer (z.B. VR 12345) und Registergericht zum Impressum hinzu.',
                    legal_basis='DDG §5 Abs. 1 Nr. 4',
                    auto_fixable=False,
                    is_missing=False,
                )))
            if not has_vorstand:
                issues.append(asdict(ImpressumIssue(
                    category='impressum',
                    severity='warning',
                    title='Vorstand nicht angegeben (e.V. erkannt)',
                    description=(
                        'Das Impressum enthält einen eingetragenen Verein, jedoch fehlen Angaben zum vertretungsberechtigten Vorstand.'
                    ),
                    risk_euro=800,
                    recommendation='Nennen Sie den vertretungsberechtigten Vorstand namentlich im Impressum.',
                    legal_basis='DDG §5 Abs. 1 Nr. 1, BGB §26',
                    auto_fixable=False,
                    is_missing=False,
                )))

        elif is_gbr:
            # GbR: kein Handelsregister, aber alle Gesellschafter Pflicht
            if not has_gesellschafter:
                issues.append(asdict(ImpressumIssue(
                    category='impressum',
                    severity='warning',
                    title='Gesellschafter nicht angegeben (GbR erkannt)',
                    description=(
                        'Das Impressum enthält eine GbR. Alle Gesellschafter müssen namentlich mit vollständiger '
                        'Anschrift genannt werden. Ein Handelsregistereintrag ist für die GbR nicht erforderlich.'
                    ),
                    risk_euro=800,
                    recommendation='Nennen Sie alle Gesellschafter der GbR mit vollständigem Namen und Anschrift im Impressum.',
                    legal_basis='DDG §5 Abs. 1 Nr. 1',
                    auto_fixable=False,
                    is_missing=False,
                )))

    return issues

