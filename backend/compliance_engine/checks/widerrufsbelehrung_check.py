"""
Widerrufsbelehrung Check (BGB §355 ff., EGBGB Art. 246a)
Prüft ob eine Widerrufsbelehrung für B2C-Online-Shops vorhanden ist.
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


@dataclass
class WiderrufsbelehrungIssue:
    category: str
    severity: str
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool = False
    is_missing: bool = False


def _has_shop_indicators(soup: BeautifulSoup) -> bool:
    html_lower = str(soup).lower()
    shop_patterns = [
        r'in den warenkorb', r'add to cart', r'zum warenkorb', r'jetzt kaufen',
        r'kaufen', r'bestellen', r'checkout', r'warenkorb', r'cart',
        r'woocommerce', r'shopify', r'magento', r'opencart', r'prestashop',
    ]
    return sum(1 for p in shop_patterns if re.search(p, html_lower)) >= 3


def _find_widerrufsbelehrung_links(soup: BeautifulSoup) -> List:
    href_keywords = [
        'widerrufsbelehrung', 'widerrufsrecht', 'widerruf',
        'cancellation', 'right-of-withdrawal', 'right_of_withdrawal',
        'rueckgabe', 'return-policy', 'returns', 'refund-policy',
        '/legal/widerruf', '/legal/cancellation',
    ]
    text_keywords = [
        'widerrufsbelehrung', 'widerrufsrecht', 'widerruf',
        'right of withdrawal', 'cancellation policy', 'rückgaberecht',
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


async def _check_widerruf_url_exists(base_url: str, session=None) -> str | None:
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    candidate_paths = [
        '/widerrufsbelehrung', '/widerrufsrecht', '/widerruf',
        '/cancellation', '/right-of-withdrawal', '/rueckgabe',
        '/return-policy', '/returns', '/refund-policy',
        '/legal/widerruf', '/legal/cancellation',
    ]
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    for path in candidate_paths:
        candidate_url = base + path
        try:
            if session:
                async with session.get(candidate_url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as resp:
                    if resp.status == 200:
                        return candidate_url
            else:
                connector = aiohttp.TCPConnector(ssl=ssl_ctx)
                async with aiohttp.ClientSession(connector=connector) as tmp:
                    async with tmp.get(candidate_url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as resp:
                        if resp.status == 200:
                            return candidate_url
        except Exception:
            continue
    return None


def _analyze_widerruf_content(text: str) -> Dict[str, bool]:
    text_lower = text.lower()
    return {
        'widerrufsfrist': bool(re.search(r'14.tag|vierzehn.tag|14\s*tage|widerrufsfrist', text_lower)),
        'widerrufsform': bool(re.search(r'eindeutige erkl|formular|muster|schriftlich|e-mail.*widerruf|widerruf.*e-mail', text_lower)),
        'ruecksendung': bool(re.search(r'rücksend|zurücksend|rückgabe|kosten.*rücksend', text_lower)),
        'erstattung': bool(re.search(r'erstatt|rückzahl|spätestens.*14|unverzüglich', text_lower)),
        'kontaktdaten': bool(re.search(r'@|telefon|adresse|anschrift', text_lower)),
    }


async def check_widerrufsbelehrung_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Prüft Widerrufsbelehrung-Compliance.
    Gibt nur Issues zurück wenn Shop-Indikatoren erkannt werden.
    """
    issues = []

    if not _has_shop_indicators(soup):
        logger.info("Keine Shop-Indikatoren — Widerrufsbelehrung nicht relevant")
        return issues

    widerruf_links = _find_widerrufsbelehrung_links(soup)
    logger.info(f"Widerrufsbelehrung-Links gefunden: {len(widerruf_links)}")

    widerruf_url: str | None = None
    if widerruf_links:
        href = widerruf_links[0].get('href', '')
        widerruf_url = urljoin(url, href) if href else None
    else:
        widerruf_url = await _check_widerruf_url_exists(url, session)

    if not widerruf_url:
        issues.append(asdict(WiderrufsbelehrungIssue(
            category='widerrufsbelehrung',
            severity='critical',
            title='Widerrufsbelehrung fehlt',
            description=(
                'Für Online-Shops mit B2C-Verkäufen ist eine vollständige Widerrufsbelehrung '
                'gesetzlich verpflichtend. Fehlt die Belehrung, verlängert sich das Widerrufsrecht '
                'auf 12 Monate + 14 Tage.'
            ),
            risk_euro=3000,
            recommendation=(
                'Fügen Sie eine Widerrufsbelehrung nach dem gesetzlichen Muster (EGBGB Anlage 1) hinzu. '
                'Pflichtangaben: Widerrufsfrist (14 Tage), Widerrufsform, Rücksendungskosten, '
                'Erstattungsbedingungen, Kontaktdaten.'
            ),
            legal_basis='BGB §355 ff., EGBGB Art. 246a §1, EU-Verbraucherrechterichtlinie 2011/83/EU',
            auto_fixable=False,
            is_missing=True,
        )))
        return issues

    # Inhaltsanalyse
    try:
        if session and widerruf_url:
            async with session.get(widerruf_url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    page_soup = BeautifulSoup(html, 'html.parser')
                    text = page_soup.get_text(separator=' ', strip=True)
                    checks = _analyze_widerruf_content(text)
                    missing = [k for k, found in checks.items() if not found]
                    if missing:
                        issues.append(asdict(WiderrufsbelehrungIssue(
                            category='widerrufsbelehrung',
                            severity='warning',
                            title='Widerrufsbelehrung unvollständig',
                            description=(
                                f'Die Widerrufsbelehrung wurde gefunden, enthält aber keine erkennbaren '
                                f'Angaben zu: {", ".join(missing)}. Unvollständige Belehrungen können '
                                f'das Widerrufsrecht auf 12 Monate + 14 Tage verlängern.'
                            ),
                            risk_euro=2000,
                            recommendation='Ergänzen Sie die fehlenden Pflichtangaben nach EGBGB Anlage 1.',
                            legal_basis='BGB §355 Abs. 2, EGBGB Art. 246a §1',
                            auto_fixable=False,
                            is_missing=False,
                        )))
    except Exception as e:
        logger.warning(f"Widerrufsbelehrung-Inhaltsanalyse fehlgeschlagen: {e}")

    return issues
