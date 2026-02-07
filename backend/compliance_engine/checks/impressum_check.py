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
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '').lower()
        link_text = a_tag.get_text(strip=True).lower()
        aria_label = (a_tag.get('aria-label') or '').lower()
        title = (a_tag.get('title') or '').lower()
        
        if any(kw in href for kw in ['impressum', 'imprint', 'legal-notice', 'legal_notice']):
            all_links.append(a_tag)
        elif any(kw in link_text for kw in ['impressum', 'imprint', 'legal notice', 'rechtliche hinweise']):
            all_links.append(a_tag)
        elif any(kw in aria_label for kw in ['impressum', 'imprint']):
            all_links.append(a_tag)
        elif any(kw in title for kw in ['impressum', 'imprint']):
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


async def check_impressum_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Prüft Impressum-Compliance
    
    1. Impressum-Link vorhanden
    2. Impressum-Inhalte (wenn erreichbar)
    """
    issues = []
    
    all_impressum_links = _find_impressum_links(soup)
    
    logger.info(f"🔍 Impressum-Links gefunden: {len(all_impressum_links)}")
    for link in all_impressum_links[:3]:
        logger.info(f"   → {link.get('href', 'N/A')}: {link.get_text(strip=True)[:50]}")
    
    if not all_impressum_links:
        # ✅ HAUPTELEMENT FEHLT: Generiere alle Sub-Issues mit is_missing=True
        issues.append(asdict(ImpressumIssue(
            category='impressum',
            severity='critical',
            title='Kein Impressum-Link gefunden',
            description='Es wurde kein Link zum Impressum gefunden. Ein Impressum ist gesetzlich verpflichtend für alle geschäftsmäßigen Telemedien.',
            risk_euro=3000,
            recommendation='Fügen Sie einen deutlich sichtbaren Impressum-Link im Footer hinzu.',
            legal_basis='§5 TMG (Telemediengesetz)',
            auto_fixable=True,
            is_missing=True
        )))
        
        # Alle Pflichtangaben als fehlend markieren
        issues.append(asdict(ImpressumIssue(
            category='impressum',
            severity='critical',
            title='Firmenname/Name fehlt',
            description='Die Angabe des vollständigen Firmennamens (bei Unternehmen) oder des vollständigen Namens (bei Einzelpersonen) fehlt im Impressum.',
            risk_euro=2000,
            recommendation='Fügen Sie den vollständigen Firmennamen bzw. Ihren Namen zum Impressum hinzu.',
            legal_basis='§5 Abs. 1 Nr. 1 TMG',
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
            legal_basis='§5 Abs. 1 Nr. 2 TMG',
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
            legal_basis='§5 Abs. 1 Nr. 2 TMG',
            auto_fixable=False,
            is_missing=True
        )))
        
        issues.append(asdict(ImpressumIssue(
            category='impressum',
            severity='critical',
            title='Telefonnummer fehlt',
            description='Es fehlt eine Telefonnummer für eine schnelle Kontaktaufnahme im Impressum.',
            risk_euro=1500,
            recommendation='Fügen Sie eine erreichbare Telefonnummer zum Impressum hinzu.',
            legal_basis='§5 Abs. 1 Nr. 2 TMG',
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
            legal_basis='§5 Abs. 1 Nr. 3 TMG',
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
            legal_basis='§5 Abs. 1 Nr. 6 TMG, §27a UStG',
            auto_fixable=False,
            is_missing=True
        )))
    else:
        # ✅ DEEP-ANALYSE: Link gefunden → Crawle und analysiere Impressum-Seite
        logger.info(f"✅ Impressum-Link gefunden, starte Deep-Analyse")
        
        try:
            from ..hybrid_validator import HybridValidator
            
            # Hole Impressum-URL
            impressum_link = all_impressum_links[0]
            impressum_href = impressum_link.get('href', '')
            
            # Erstelle absolute URL
            from urllib.parse import urljoin
            impressum_url = urljoin(url, impressum_href)
            
            # Fetche Impressum-Seite
            if session:
                try:
                    async with session.get(impressum_url, timeout=10) as response:
                        if response.status == 200:
                            impressum_html = await response.text()
                            
                            # Deep-Analyse mit Hybrid-Validator
                            validator = HybridValidator()
                            analysis = await validator.validate_page(
                                page_type="impressum",
                                text_content=impressum_html,
                                url=impressum_url
                            )
                            
                            # Generiere Issues basierend auf fehlenden Feldern
                            for field_result in analysis["results"]:
                                if not field_result["found"] and field_result["field"] in ["firmenname", "adresse", "email", "telefon"]:
                                    
                                    # Nur kritische Pflichtfelder als Issues
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
                                        legal_basis='§5 TMG',
                                        auto_fixable=False,
                                        is_missing=False  # Link existiert, nur Inhalt fehlt
                                    )))
                            
                            # Qualitäts-Warnung bei niedriger Qualität
                            if analysis["quality"] in ["poor", "insufficient"]:
                                issues.append(asdict(ImpressumIssue(
                                    category='impressum',
                                    severity='warning',
                                    title='Impressum unvollständig',
                                    description=f'Das Impressum wurde gefunden, ist aber unvollständig (Qualität: {analysis["quality"]}). Mehrere Pflichtangaben fehlen oder sind unzureichend.',
                                    risk_euro=3000,
                                    recommendation='Vervollständigen Sie Ihr Impressum mit allen Pflichtangaben nach §5 TMG.',
                                    legal_basis='§5 TMG',
                                    auto_fixable=True,
                                    is_missing=False
                                )))
                            
                            logger.info(f"✅ Deep-Analyse abgeschlossen: {analysis['quality']} ({len(issues)} Issues)")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Deep-Analyse fehlgeschlagen: {e}")
                    # Fallback: Keine zusätzlichen Issues, nur Link-Check war erfolgreich
        
        except ImportError:
            logger.warning("⚠️ HybridValidator nicht verfügbar - überspringe Deep-Analyse")
    
    return issues

