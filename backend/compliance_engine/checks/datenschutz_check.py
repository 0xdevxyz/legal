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
    keywords_href = ['datenschutz', 'privacy', 'dsgvo', 'gdpr', 'data-protection']
    keywords_text = ['datenschutz', 'privacy policy', 'dsgvo', 'datenschutzerklärung', 'data protection']
    
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


async def check_datenschutz_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Prüft Datenschutzerklärung-Compliance
    
    1. Datenschutz-Link vorhanden
    2. Datenschutzerklärung-Inhalte (wenn erreichbar)
    """
    issues = []
    
    datenschutz_links = _find_datenschutz_links(soup)
    
    logger.info(f"🔍 Datenschutz-Links gefunden: {len(datenschutz_links)}")
    for link in datenschutz_links[:3]:
        logger.info(f"   → {link.get('href', 'N/A')}: {link.get_text(strip=True)[:50]}")
    
    if not datenschutz_links:
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
    
    return issues

