"""
AGB Check (BGB §305 ff., UWG)
Prüft Allgemeine Geschäftsbedingungen auf Vorhandensein und grundlegende Pflichtinhalte.

Wichtig: AGB sind nur für Shops/gewerbliche Angebote mit Vertragsschluss rechtlich relevant.
Reine Informations- oder Unternehmenswebsites MÜSSEN keine AGB haben.
Der Check meldet fehlende AGB daher nur als optionalen Hinweis, wenn kein Shop erkannt wird.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, urljoin
import re
import logging
import aiohttp
import ssl
import certifi

logger = logging.getLogger(__name__)

SHOP_SIGNALS = [
    'warenkorb', 'in den warenkorb', 'add to cart', 'checkout', 'zur kasse',
    'shop', 'produkt', 'preis', '€', 'eur', 'kaufen', 'bestellen', 'bestellung',
    'lieferung', 'versandkosten', 'artikel', 'menge', 'anzahl',
    'payment', 'zahlung', 'stripe', 'paypal', 'rechnung',
]

def _is_shop(soup: BeautifulSoup) -> bool:
    text = soup.get_text(separator=' ', strip=True).lower()
    html_lower = str(soup).lower()
    hits = sum(1 for s in SHOP_SIGNALS if s in text or s in html_lower)
    return hits >= 3


@dataclass
class AGBIssue:
    category: str
    severity: str
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool = False
    is_missing: bool = False


def _find_agb_links(soup: BeautifulSoup) -> List:
    href_keywords = [
        'agb', 'allgemeine-geschaeftsbedingungen', 'allgemeine_geschaeftsbedingungen',
        'terms', 'terms-of-service', 'terms-of-use', 'terms_of_service',
        'nutzungsbedingungen', 'nutzungs-bedingungen', 'geschaeftsbedingungen',
        'tos', 'gtc', '/legal/terms',
    ]
    text_keywords = [
        'agb', 'allgemeine geschäftsbedingungen', 'nutzungsbedingungen',
        'terms of service', 'terms of use', 'terms & conditions',
        'geschäftsbedingungen', 'nutzungshinweise',
    ]

    all_links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '').lower()
        link_text = a_tag.get_text(strip=True).lower()
        aria_label = (a_tag.get('aria-label') or '').lower()
        title_attr = (a_tag.get('title') or '').lower()

        if any(kw in href for kw in href_keywords):
            all_links.append(a_tag)
        elif any(kw in link_text for kw in text_keywords):
            all_links.append(a_tag)
        elif any(kw in aria_label for kw in text_keywords):
            all_links.append(a_tag)
        elif any(kw in title_attr for kw in text_keywords):
            all_links.append(a_tag)

    return all_links


async def _check_agb_url_exists(base_url: str, session=None) -> str | None:
    """
    Prüft direkt bekannte AGB-Pfade per HTTP-Request.
    Gibt die funktionierende URL zurück oder None.
    """
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    candidate_paths = [
        '/agb', '/allgemeine-geschaeftsbedingungen', '/nutzungsbedingungen',
        '/terms', '/terms-of-service', '/terms-of-use', '/tos', '/gtc',
        '/legal/terms', '/legal/agb',
    ]

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())

    for path in candidate_paths:
        candidate_url = base + path
        try:
            if session:
                async with session.get(
                    candidate_url,
                    timeout=aiohttp.ClientTimeout(total=8),
                    allow_redirects=True
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"AGB-URL direkt gefunden: {candidate_url}")
                        return candidate_url
            else:
                connector = aiohttp.TCPConnector(ssl=ssl_ctx)
                async with aiohttp.ClientSession(connector=connector) as tmp:
                    async with tmp.get(
                        candidate_url,
                        timeout=aiohttp.ClientTimeout(total=8),
                        allow_redirects=True
                    ) as resp:
                        if resp.status == 200:
                            logger.info(f"AGB-URL direkt gefunden: {candidate_url}")
                            return candidate_url
        except Exception:
            continue

    return None


def _analyze_agb_content(text: str) -> Dict[str, bool]:
    """
    Prüft ob grundlegende Pflichtklauseln nach BGB §305 ff. vorhanden sind.
    AGB-Inhalte sind individuell — nur grobe Strukturprüfung möglich.
    """
    text_lower = text.lower()

    checks = {
        'geltungsbereich': bool(re.search(
            r'geltungsbereich|anwendungsbereich|these agb gelten|diese bedingungen gelten',
            text_lower
        )),
        'vertragsschluss': bool(re.search(
            r'vertragsschluss|vertragsabschluss|angebot und annahme|bestellung|auftrag',
            text_lower
        )),
        'widerrufsrecht': bool(re.search(
            r'widerrufsrecht|widerruf|14.tage|14 tage|widerrufsbelehrung|rücktritt',
            text_lower
        )),
        'haftung': bool(re.search(
            r'haftung|haftungsausschluss|haftungsbeschränkung|gewährleistung|garantie',
            text_lower
        )),
        'gerichtsstand': bool(re.search(
            r'gerichtsstand|erfüllungsort|anwendbares recht|deutsches recht|rechtsordnung',
            text_lower
        )),
    }

    return checks


async def check_agb_compliance(url: str, soup: BeautifulSoup, session=None, is_shop: bool | None = None) -> List[Dict[str, Any]]:
    """
    Prüft AGB-Compliance:
    1. Shop-Erkennung: Nur Shops/gewerbliche Seiten mit Vertragsschluss benötigen AGB zwingend.
    2. AGB-Link vorhanden (im HTML oder als direkt erreichbare URL)
    3. Grundlegende Pflichtklauseln vorhanden (BGB §305 ff.)

    Nicht-Shop-Seiten erhalten bei fehlenden AGB nur einen optionalen Hinweis (severity='info'),
    da AGB für reine Informations- oder Unternehmenswebsites nicht verpflichtend sind.
    """
    issues = []

    shop_detected = is_shop if is_shop is not None else _is_shop(soup)
    logger.info(f"AGB-Check: shop_detected={shop_detected}, url={url}")

    agb_links = _find_agb_links(soup)
    logger.info(f"AGB-Links gefunden: {len(agb_links)}")

    agb_url: str | None = None

    if agb_links:
        href = agb_links[0].get('href', '')
        agb_url = urljoin(url, href) if href else None
    else:
        agb_url = await _check_agb_url_exists(url, session)

    if not agb_url:
        if shop_detected:
            issues.append(asdict(AGBIssue(
                category='agb',
                severity='warning',
                title='Keine AGB gefunden',
                description=(
                    'Es wurden keine Allgemeinen Geschäftsbedingungen gefunden. '
                    'Für Shops und gewerbliche Websites mit Vertragsschluss sind AGB '
                    'rechtlich notwendig (BGB §305 ff., UWG).'
                ),
                risk_euro=2000,
                recommendation=(
                    'Erstellen Sie AGB die mindestens folgende Punkte abdecken: '
                    'Geltungsbereich, Vertragsschluss, Preise & Zahlungsbedingungen, '
                    'Widerrufsrecht, Gewährleistung, Haftungsbeschränkung, Gerichtsstand.'
                ),
                legal_basis='BGB §305 ff. (AGB-Recht), UWG §3a',
                auto_fixable=False,
                is_missing=True,
            )))
        else:
            issues.append(asdict(AGBIssue(
                category='agb',
                severity='info',
                title='Keine AGB gefunden (optional)',
                description=(
                    'Es wurden keine Allgemeinen Geschäftsbedingungen gefunden. '
                    'Für reine Informations- oder Unternehmenswebsites ohne Verkauf/Vertragsschluss '
                    'sind AGB nicht gesetzlich vorgeschrieben. '
                    'Wenn Sie Dienstleistungen oder Produkte anbieten, können AGB sinnvoll sein.'
                ),
                risk_euro=0,
                recommendation=(
                    'Prüfen Sie, ob Ihre Website Verträge mit Nutzern schließt (z.B. Käufe, Abonnements, Buchungen). '
                    'Falls ja, sollten Sie AGB erstellen. Falls nein, ist dieser Punkt nicht relevant für Sie. '
                    'Sie können diesen Hinweis im Dashboard ignorieren.'
                ),
                legal_basis='BGB §305 ff. (nur relevant bei Vertragsschluss)',
                auto_fixable=False,
                is_missing=True,
            )))
        return issues

    # AGB gefunden — Inhaltsanalyse (nur relevant für Shops)
    if not shop_detected:
        return issues

    try:
        if session and agb_url:
            async with session.get(agb_url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as resp:
                if resp.status == 200:
                    agb_html = await resp.text()
                    agb_soup = BeautifulSoup(agb_html, 'html.parser')
                    agb_text = agb_soup.get_text(separator=' ', strip=True)

                    checks = _analyze_agb_content(agb_text)
                    missing_clauses = [k for k, found in checks.items() if not found]

                    if len(missing_clauses) >= 3:
                        issues.append(asdict(AGBIssue(
                            category='agb',
                            severity='warning',
                            title='AGB unvollständig — mehrere Pflichtbereiche fehlen',
                            description=(
                                f'Die AGB wurden gefunden, enthalten aber keine erkennbaren Angaben zu: '
                                f'{", ".join(missing_clauses)}. '
                                f'Vollständige AGB schützen vor Abmahnungen und Haftungsrisiken.'
                            ),
                            risk_euro=1500,
                            recommendation=(
                                'Ergänzen Sie Ihre AGB um die fehlenden Bereiche. '
                                'Lassen Sie die AGB von einem Rechtsanwalt prüfen.'
                            ),
                            legal_basis='BGB §305 ff., BGH-Rechtsprechung zu AGB-Kontrolle',
                            auto_fixable=False,
                            is_missing=False,
                        )))
    except Exception as e:
        logger.warning(f"AGB-Inhaltsanalyse fehlgeschlagen: {e}")

    return issues
