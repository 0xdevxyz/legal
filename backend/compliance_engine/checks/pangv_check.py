"""
PAngV Check (Preisangabenverordnung §§3, 4, 11)
Prüft Preisangaben-Compliance für Online-Shops.
Nur relevant wenn Shop-Indikatoren erkannt werden.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class PAngVIssue:
    category: str
    severity: str
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool = False
    is_missing: bool = False


def _has_shop_context(soup: BeautifulSoup) -> bool:
    html_lower = str(soup).lower()
    shop_patterns = [
        r'warenkorb', r'shopping.cart', r'checkout', r'jetzt kaufen', r'buy now',
        r'in den warenkorb', r'add to cart', r'preis.*€', r'€.*preis',
        r'woocommerce', r'shopify', r'magento', r'opencart',
    ]
    return sum(1 for p in shop_patterns if re.search(p, html_lower)) >= 2


async def check_pangv_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Prüft PAngV-Compliance für Online-Shops.
    Gibt leere Liste zurück wenn keine Shop-Indikatoren erkannt.
    """
    issues = []

    if not _has_shop_context(soup):
        logger.info("Keine Shop-Indikatoren — PAngV nicht relevant")
        return issues

    html_text = str(soup).lower()
    html_raw = str(soup)

    # §3 PAngV: Preise müssen MwSt. inkl. ausweisen
    has_prices = bool(re.search(r'\d+[.,]\d{2}\s*€|\d+\s*€', html_raw))
    if has_prices:
        has_mwst = bool(re.search(
            r'inkl\.?\s*(mwst|mwst\.|mehrwertsteuer|ust|umsatzsteuer)|'
            r'incl\.?\s*vat|including\s*vat|brutto',
            html_text
        ))
        if not has_mwst:
            issues.append(asdict(PAngVIssue(
                category='preisangaben',
                severity='warning',
                title='Preisangabe ohne MwSt.-Hinweis',
                description=(
                    'Preise werden angezeigt, aber es fehlt der Hinweis "inkl. MwSt." '
                    '(Bruttopreisangabe). §3 PAngV verpflichtet dazu, Endpreise einschließlich '
                    'aller Steuern anzugeben.'
                ),
                risk_euro=1500,
                recommendation='Ergänzen Sie bei allen Preisen den Zusatz "inkl. MwSt." und ggf. "zzgl. Versandkosten".',
                legal_basis='PAngV §3 Abs. 1, UWG §3a',
                auto_fixable=False,
                is_missing=False,
            )))

    # §3 PAngV: Versandkostenhinweis
    if has_prices:
        has_shipping_info = bool(re.search(
            r'versandkosten|versand.*kosten|lieferkosten|shipping.*cost|zzgl\..*versand|'
            r'kostenloser versand|free shipping|versandkostenfrei',
            html_text
        ))
        if not has_shipping_info:
            issues.append(asdict(PAngVIssue(
                category='preisangaben',
                severity='warning',
                title='Kein Versandkostenhinweis gefunden',
                description=(
                    'Bei Preisangaben fehlt ein Hinweis auf Versand- und Lieferkosten. '
                    'Nach §3 PAngV müssen entweder die genauen Versandkosten angegeben werden '
                    'oder ein Hinweis "zzgl. Versandkosten" mit Link zu den Kosten.'
                ),
                risk_euro=1000,
                recommendation='Fügen Sie bei Produktpreisen "zzgl. Versandkosten" (mit Link) oder "inkl. Versandkosten" hinzu.',
                legal_basis='PAngV §3 Abs. 2',
                auto_fixable=False,
                is_missing=False,
            )))

    # §11 PAngV: Preisreduzierungen müssen 30-Tage-Tiefstpreis zeigen
    has_discount = bool(re.search(
        r'sale|rabatt|%\s*off|angebot|reduziert|statt\s+\d|war\s+\d|ursprünglich|'
        r'<del|<s>|text-decoration.*line-through',
        html_text
    ))
    if has_discount:
        has_reference_price = bool(re.search(
            r'(tiefstpreis|günstigster preis|niedrigster preis|lowest price|'
            r'30.tag|30-tage|preishistorie|war\s+\d+[.,]\d{2})',
            html_text
        ))
        if not has_reference_price:
            issues.append(asdict(PAngVIssue(
                category='preisangaben',
                severity='critical',
                title='Preisreduzierung ohne 30-Tage-Referenzpreis (§11 PAngV)',
                description=(
                    'Die Website zeigt Preisreduzierungen oder durchgestrichene Preise, ohne den '
                    'günstigsten Preis der letzten 30 Tage als Referenz anzuzeigen. '
                    'Dies ist seit Umsetzung der Omnibus-Richtlinie verpflichtend (BGH bestätigt 2025).'
                ),
                risk_euro=3000,
                recommendation=(
                    'Zeigen Sie bei jeder Preisreduzierung den niedrigsten Preis der letzten 30 Tage '
                    'als Referenzpreis an, z.B. "Günstigster Preis der letzten 30 Tage: 29,99€".'
                ),
                legal_basis='PAngV §11, Omnibus-Richtlinie 2019/2161/EU, BGH-Urteil 2025',
                auto_fixable=False,
                is_missing=False,
            )))

    # §4 PAngV: Grundpreis für Waren nach Gewicht/Volumen
    measurable_patterns = re.compile(r'\d+\s*(kg|g|ml|l|liter|gramm|kilogramm)\b', re.I)
    if measurable_patterns.search(html_raw):
        has_grundpreis = bool(re.search(
            r'(pro\s*kg|/\s*kg|je\s*kg|per\s*kg|'
            r'pro\s*100\s*g|/\s*100\s*g|'
            r'pro\s*liter|/\s*liter|/\s*l\b|'
            r'grundpreis)',
            html_text
        ))
        if not has_grundpreis:
            issues.append(asdict(PAngVIssue(
                category='preisangaben',
                severity='warning',
                title='Grundpreis fehlt bei Mengenware (§4 PAngV)',
                description=(
                    'Produkte mit Mengenangaben (kg, g, l, ml) wurden erkannt, aber kein Grundpreis '
                    '(Preis pro kg/l/100g) ist sichtbar. Bei mengenbasierter Ware ist der Grundpreis '
                    'direkt neben dem Endpreis anzugeben.'
                ),
                risk_euro=1500,
                recommendation='Zeigen Sie den Grundpreis (z.B. "2,99€ / 100g") unmittelbar neben dem Produktpreis an.',
                legal_basis='PAngV §4',
                auto_fixable=False,
                is_missing=False,
            )))

    return issues
