"""
Shop-Compliance Check — Zentrale Prüfung für Online-Shops
Bündelt alle shop-spezifischen Rechtsanforderungen:
  - BGB §305 ff. (AGB)
  - BGB §355 ff. / EGBGB Art. 246a (Widerrufsbelehrung)
  - PAngV §§3, 4, 11 (Preisangaben)
  - BGB §312k (Kündigungsbutton)

Gibt leere Liste zurück wenn keine Shop-Indikatoren erkannt werden.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, urljoin
import re
import logging
import aiohttp
import ssl
import certifi

logger = logging.getLogger(__name__)


SHOP_PATTERNS = [
    r'in den warenkorb', r'add to cart', r'zum warenkorb', r'jetzt kaufen',
    r'buy now', r'jetzt bestellen', r'kaufen', r'bestellen', r'checkout',
    r'warenkorb', r'\bcart\b', r'woocommerce', r'shopify', r'magento',
    r'opencart', r'prestashop', r'shopware', r'wix.*shop', r'oxid',
]

SHOP_THRESHOLD = 3


def detect_shop(soup: BeautifulSoup) -> bool:
    """
    Zentrale Shop-Erkennung. Threshold: mindestens 3 übereinstimmende Patterns.
    Einzige Shop-Detection für alle Shop-Checks — kein Duplikat-Code.
    """
    html_lower = str(soup).lower()
    matches = sum(1 for p in SHOP_PATTERNS if re.search(p, html_lower))
    logger.info(f"Shop-Detection: {matches}/{SHOP_THRESHOLD} Patterns")
    return matches >= SHOP_THRESHOLD


@dataclass
class ShopIssue:
    category: str
    severity: str
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool = False
    is_missing: bool = False


async def _url_exists(url: str, session=None) -> bool:
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        if session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as r:
                return r.status == 200
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        async with aiohttp.ClientSession(connector=connector) as tmp:
            async with tmp.get(url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as r:
                return r.status == 200
    except Exception:
        return False


async def _fetch_page_text(url: str, session=None) -> Optional[str]:
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        if session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as r:
                if r.status == 200:
                    return await r.text()
        else:
            connector = aiohttp.TCPConnector(ssl=ssl_ctx)
            async with aiohttp.ClientSession(connector=connector) as tmp:
                async with tmp.get(url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as r:
                    if r.status == 200:
                        return await r.text()
    except Exception:
        pass
    return None


async def _check_agb(base_url: str, soup: BeautifulSoup, session) -> List[ShopIssue]:
    issues = []
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    href_kw = ['agb', 'allgemeine-geschaeftsbedingungen', 'terms', 'terms-of-service',
               'nutzungsbedingungen', 'geschaeftsbedingungen', 'tos', 'gtc', '/legal/terms']
    text_kw = ['agb', 'allgemeine geschäftsbedingungen', 'nutzungsbedingungen',
               'terms of service', 'terms & conditions', 'geschäftsbedingungen']

    agb_url = None
    for a in soup.find_all('a', href=True):
        href = a.get('href', '').lower()
        text = a.get_text(strip=True).lower()
        if any(k in href for k in href_kw) or any(k in text for k in text_kw):
            agb_url = urljoin(base_url, a.get('href', ''))
            break

    if not agb_url:
        for path in ['/agb', '/allgemeine-geschaeftsbedingungen', '/terms',
                     '/terms-of-service', '/nutzungsbedingungen', '/tos', '/gtc']:
            if await _url_exists(base + path, session):
                agb_url = base + path
                break

    if not agb_url:
        issues.append(ShopIssue(
            category='shop',
            severity='critical',
            title='AGB fehlen (Online-Shop erkannt)',
            description=(
                'Ein Online-Shop wurde erkannt, aber keine AGB gefunden. '
                'Ohne AGB gelten die für den Unternehmer ungünstigsten gesetzlichen Regelungen.'
            ),
            risk_euro=3000,
            recommendation=(
                'Erstellen Sie AGB mit: Geltungsbereich, Vertragsschluss, Preise & Zahlung, '
                'Widerrufsrecht, Gewährleistung, Haftung, Gerichtsstand. '
                'Verlinken im Footer und als Pflicht-Checkbox im Checkout.'
            ),
            legal_basis='BGB §305 ff. (AGB-Recht), UWG §3a',
            auto_fixable=False,
            is_missing=True,
        ))
        return issues

    text = await _fetch_page_text(agb_url, session)
    if text:
        t = BeautifulSoup(text, 'html.parser').get_text(separator=' ', strip=True).lower()
        checks = {
            'Geltungsbereich': bool(re.search(r'geltungsbereich|anwendungsbereich|diese agb gelten', t)),
            'Vertragsschluss': bool(re.search(r'vertragsschluss|vertragsabschluss|bestellung|angebot', t)),
            'Widerrufsrecht':  bool(re.search(r'widerrufsrecht|widerruf|14.tag', t)),
            'Haftung':         bool(re.search(r'haftung|haftungsausschluss|gewährleistung', t)),
            'Gerichtsstand':   bool(re.search(r'gerichtsstand|anwendbares recht|deutsches recht', t)),
        }
        missing = [k for k, found in checks.items() if not found]
        if len(missing) >= 3:
            issues.append(ShopIssue(
                category='shop',
                severity='warning',
                title='AGB unvollständig — mehrere Pflichtbereiche fehlen',
                description=f'AGB gefunden, aber keine erkennbaren Angaben zu: {", ".join(missing)}.',
                risk_euro=1500,
                recommendation='Ergänzen Sie die fehlenden Bereiche. Lassen Sie die AGB von einem Anwalt prüfen.',
                legal_basis='BGB §305 ff.',
                auto_fixable=False,
                is_missing=False,
            ))
    return issues


async def _check_widerruf(base_url: str, soup: BeautifulSoup, session) -> List[ShopIssue]:
    issues = []
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    href_kw = ['widerrufsbelehrung', 'widerrufsrecht', 'widerruf', 'cancellation',
               'right-of-withdrawal', 'rueckgabe', 'return-policy', 'returns', 'refund-policy']
    text_kw = ['widerrufsbelehrung', 'widerrufsrecht', 'widerruf',
               'right of withdrawal', 'cancellation policy', 'rückgaberecht']

    widerruf_url = None
    for a in soup.find_all('a', href=True):
        href = a.get('href', '').lower()
        text = a.get_text(strip=True).lower()
        if any(k in href for k in href_kw) or any(k in text for k in text_kw):
            widerruf_url = urljoin(base_url, a.get('href', ''))
            break

    if not widerruf_url:
        for path in ['/widerrufsbelehrung', '/widerrufsrecht', '/widerruf',
                     '/cancellation', '/right-of-withdrawal', '/returns', '/return-policy']:
            if await _url_exists(base + path, session):
                widerruf_url = base + path
                break

    if not widerruf_url:
        issues.append(ShopIssue(
            category='shop',
            severity='critical',
            title='Widerrufsbelehrung fehlt (Online-Shop erkannt)',
            description=(
                'Online-Shop erkannt, aber keine Widerrufsbelehrung gefunden. '
                'Ohne Widerrufsbelehrung verlängert sich das Widerrufsrecht auf 12 Monate + 14 Tage.'
            ),
            risk_euro=3000,
            recommendation=(
                'Erstellen Sie eine Widerrufsbelehrung nach EGBGB Anlage 1 mit: '
                '14-tägiger Frist, Widerrufsform, Rücksendungskosten, Erstattung, Kontaktdaten. '
                'Verlinken im Footer und in Bestellbestätigungen.'
            ),
            legal_basis='BGB §355 ff., EGBGB Art. 246a §1, EU-Verbraucherrechterichtlinie 2011/83/EU',
            auto_fixable=False,
            is_missing=True,
        ))
        return issues

    text = await _fetch_page_text(widerruf_url, session)
    if text:
        t = BeautifulSoup(text, 'html.parser').get_text(separator=' ', strip=True).lower()
        checks = {
            'Widerrufsfrist (14 Tage)': bool(re.search(r'14.tag|vierzehn.tag|14\s*tage|widerrufsfrist', t)),
            'Widerrufsform':            bool(re.search(r'eindeutige erkl|formular|muster|schriftlich|e-mail.*widerruf', t)),
            'Rücksendung':              bool(re.search(r'rücksend|zurücksend|rückgabe|kosten.*rücksend', t)),
            'Erstattung':               bool(re.search(r'erstatt|rückzahl|spätestens.*14|unverzüglich', t)),
            'Kontaktdaten':             bool(re.search(r'@|telefon|adresse|anschrift', t)),
        }
        missing = [k for k, found in checks.items() if not found]
        if missing:
            issues.append(ShopIssue(
                category='shop',
                severity='warning',
                title='Widerrufsbelehrung unvollständig',
                description=(
                    f'Widerrufsbelehrung gefunden, aber keine Angaben zu: {", ".join(missing)}. '
                    f'Unvollständige Belehrungen können das Widerrufsrecht auf 12 Monate + 14 Tage verlängern.'
                ),
                risk_euro=2000,
                recommendation='Ergänzen Sie die fehlenden Pflichtangaben nach EGBGB Anlage 1.',
                legal_basis='BGB §355 Abs. 2, EGBGB Art. 246a §1',
                auto_fixable=False,
                is_missing=False,
            ))
    return issues


async def _check_pangv(soup: BeautifulSoup) -> List[ShopIssue]:
    issues = []
    html_text = str(soup).lower()
    html_raw = str(soup)

    has_prices = bool(re.search(r'\d+[.,]\d{2}\s*€|\d+\s*€', html_raw))
    if has_prices:
        if not re.search(r'inkl\.?\s*(mwst|mehrwertsteuer|ust)|incl\.?\s*vat|brutto', html_text):
            issues.append(ShopIssue(
                category='shop',
                severity='warning',
                title='Preisangabe ohne MwSt.-Hinweis (§3 PAngV)',
                description='Preise ohne "inkl. MwSt." — §3 PAngV verlangt Endpreise inkl. aller Steuern.',
                risk_euro=1500,
                recommendation='Ergänzen Sie bei allen Preisen den Zusatz "inkl. MwSt.".',
                legal_basis='PAngV §3 Abs. 1, UWG §3a',
                auto_fixable=False,
                is_missing=False,
            ))
        if not re.search(r'versandkosten|versand.*kosten|lieferkosten|zzgl.*versand|kostenloser versand|versandkostenfrei|free shipping', html_text):
            issues.append(ShopIssue(
                category='shop',
                severity='warning',
                title='Kein Versandkostenhinweis (§3 PAngV)',
                description='Bei Preisen fehlt der Hinweis auf Versandkosten.',
                risk_euro=1000,
                recommendation='Fügen Sie "zzgl. Versandkosten" (mit Link) oder "inkl. Versandkosten" hinzu.',
                legal_basis='PAngV §3 Abs. 2',
                auto_fixable=False,
                is_missing=False,
            ))

    if re.search(r'sale|rabatt|%\s*off|angebot|reduziert|statt\s+\d|war\s+\d|ursprünglich|<del|<s>', html_text):
        if not re.search(r'tiefstpreis|günstigster preis|niedrigster preis|30.tag|30-tage|war\s+\d+[.,]\d{2}', html_text):
            issues.append(ShopIssue(
                category='shop',
                severity='critical',
                title='Preisreduzierung ohne 30-Tage-Referenzpreis (§11 PAngV)',
                description='Preisreduzierungen ohne den günstigsten Preis der letzten 30 Tage — seit Omnibus-Richtlinie Pflicht.',
                risk_euro=3000,
                recommendation='Zeigen Sie bei Rabatten: "Günstigster Preis der letzten 30 Tage: X€".',
                legal_basis='PAngV §11, Omnibus-Richtlinie 2019/2161/EU',
                auto_fixable=False,
                is_missing=False,
            ))

    if re.search(r'\d+\s*(kg|g|ml|l|liter|gramm)\b', html_raw, re.I):
        if not re.search(r'pro\s*kg|/\s*kg|je\s*kg|pro\s*100\s*g|/\s*100\s*g|pro\s*liter|/\s*l\b|grundpreis', html_text):
            issues.append(ShopIssue(
                category='shop',
                severity='warning',
                title='Grundpreis fehlt bei Mengenware (§4 PAngV)',
                description='Produkte mit Mengenangaben ohne sichtbaren Grundpreis.',
                risk_euro=1500,
                recommendation='Grundpreis direkt neben Produktpreis anzeigen (z.B. "2,99€ / 100g").',
                legal_basis='PAngV §4',
                auto_fixable=False,
                is_missing=False,
            ))
    return issues


async def _check_kuendigungsbutton(soup: BeautifulSoup) -> List[ShopIssue]:
    issues = []
    html_text = str(soup).lower()
    if not re.search(r'abonnement|\babo\b|subscription|monatlich|jährlich|recurring|mitgliedschaft|membership', html_text):
        return issues
    if not re.search(r'verträge hier kündigen|vertrag kündigen|abo.*kündigen|subscription.*cancel|cancel.*subscription', html_text):
        issues.append(ShopIssue(
            category='shop',
            severity='warning',
            title='Kündigungsbutton fehlt bei Abo-Dienst (BGB §312k)',
            description=(
                'Abo-Indikatoren erkannt, aber kein "Verträge hier kündigen"-Button gefunden. '
                'Seit 01.07.2022 müssen online abgeschlossene Dauerschuldverhältnisse online kündbar sein.'
            ),
            risk_euro=2000,
            recommendation='Fügen Sie einen "Verträge hier kündigen"-Button hinzu (max. 2 Klicks zum Kündigungsformular).',
            legal_basis='BGB §312k (in Kraft seit 01.07.2022)',
            auto_fixable=False,
            is_missing=False,
        ))
    return issues


async def check_shop_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Zentrale Shop-Compliance-Prüfung.
    Gibt leere Liste zurück wenn keine Shop-Indikatoren erkannt werden (SHOP_THRESHOLD=3).
    Prüft: AGB, Widerrufsbelehrung, PAngV-Preisangaben, Kündigungsbutton.
    """
    if not detect_shop(soup):
        logger.info(f"Kein Shop erkannt auf {url} — Shop-Checks übersprungen")
        return []

    logger.info(f"Shop erkannt auf {url} — starte Shop-Compliance-Checks")
    issues: List[ShopIssue] = []

    issues.extend(await _check_agb(url, soup, session))
    issues.extend(await _check_widerruf(url, soup, session))
    issues.extend(await _check_pangv(soup))
    issues.extend(await _check_kuendigungsbutton(soup))

    logger.info(f"Shop-Checks: {len(issues)} Issues gefunden")
    return [asdict(i) for i in issues]
