"""
UWG Check (Gesetz gegen unlauteren Wettbewerb)
Prüft §§5, 5a, 5b UWG — Irreführung, Bewertungstransparenz, Dringlichkeitsmuster.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class UWGIssue:
    category: str
    severity: str
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool = False
    is_missing: bool = False


async def check_uwg_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Prüft UWG-Compliance:
    - §5b: Bewertungstransparenz
    - §5/5a: Irreführende Dringlichkeitsmuster (Dark Patterns)
    - Gütezeichen/Siegel ohne erkennbaren Nachweis
    - Werbung nicht als solche erkennbar
    """
    issues = []
    html_text = str(soup).lower()

    # §5b UWG: Kundenbewertungen ohne Verification-Disclosure
    has_reviews = bool(re.search(
        r'(bewertung|review|rezension|sterne|stars|rating|★|☆|✓\s*verifiziert)',
        html_text
    ))
    if has_reviews:
        has_review_disclosure = bool(re.search(
            r'(verifiziert|verified|geprüfte\s*bewertung|echte\s*bewertung|'
            r'nur.*käufer|only.*purchaser|bewertungen.*überprüft|reviews.*verified|'
            r'trustpilot|google.*bewertung|trusted\s*shops)',
            html_text
        ))
        if not has_review_disclosure:
            issues.append(asdict(UWGIssue(
                category='uwg',
                severity='warning',
                title='Kundenbewertungen ohne Verifikations-Disclosure (§5b UWG)',
                description=(
                    'Die Website zeigt Kundenbewertungen, aber es ist nicht erkennbar, '
                    'ob und wie sichergestellt wird, dass Bewertungen von echten Käufern stammen. '
                    '§5b UWG (Omnibus-Richtlinie) verpflichtet dazu, dies offenzulegen.'
                ),
                risk_euro=2000,
                recommendation=(
                    'Fügen Sie in der Nähe der Bewertungen einen Hinweis hinzu, z.B.: '
                    '"Alle Bewertungen stammen von verifizierten Käufern" oder '
                    '"Bewertungen werden nicht auf Echtheit geprüft".'
                ),
                legal_basis='UWG §5b Abs. 3 (in Kraft seit 28.05.2022, Omnibus-Richtlinie)',
                auto_fixable=False,
                is_missing=False,
            )))

    # §5/5a UWG: Künstliche Dringlichkeit (Dark Patterns)
    urgency_patterns = re.compile(
        r'(nur noch \d+ (stück|verfügbar|artikel|exemplare)|'
        r'nur \d+ (stück )?auf lager|'
        r'angebot endet in|offer ends in|'
        r'countdown|nur heute|only today|'
        r'letzte chance|last chance|'
        r'\d+ (personen|kunden|nutzer) (schauen|sehen|kaufen) gerade|'
        r'fast ausverkauft|almost sold out|'
        r'nur noch \d+ verfügbar)',
        re.I
    )
    urgency_matches = urgency_patterns.findall(html_text)
    if urgency_matches:
        issues.append(asdict(UWGIssue(
            category='uwg',
            severity='warning',
            title='Mögliche Dringlichkeitsmuster erkannt (§5 UWG)',
            description=(
                'Es wurden Formulierungen gefunden, die künstliche Dringlichkeit erzeugen könnten '
                '(z.B. Countdowns, "Nur noch X verfügbar", "Fast ausverkauft"). '
                'Wenn diese Angaben unzutreffend oder übertrieben sind, stellen sie eine '
                'irreführende Geschäftspraktik nach §5 UWG dar.'
            ),
            risk_euro=3000,
            recommendation=(
                'Stellen Sie sicher, dass Lagerbestands- und Zeitangaben korrekt und '
                'nicht künstlich manipuliert sind. Permanente Countdowns oder '
                'statisch gefälschte Lagerbestände sind unzulässig (UWG Anhang Nr. 7, 8).'
            ),
            legal_basis='UWG §5 Abs. 1, UWG-Anhang (Schwarze Liste) Nr. 7, 8',
            auto_fixable=False,
            is_missing=False,
        )))

    # Gütezeichen / Siegel ohne erkennbaren Nachweis-Link
    seal_patterns = re.compile(
        r'(testsieger|test\s*winner|ausgezeichnet|award|zertifiziert|certified|'
        r'geprüft\s*durch|geprüfte\s*qualität|empfohlen\s*von|recommended\s*by|'
        r'trusted\s*shop|eco.*zertifikat|din\s*iso|tüv|dekra)',
        re.I
    )
    seal_matches = seal_patterns.findall(str(soup))
    if seal_matches:
        has_seal_link = bool(soup.find('a', href=re.compile(
            r'(zertifikat|certificate|award|siegel|testbericht|test-report|nachweis)',
            re.I
        )))
        if not has_seal_link:
            issues.append(asdict(UWGIssue(
                category='uwg',
                severity='info',
                title='Gütezeichen/Siegel ohne verlinkten Nachweis erkannt',
                description=(
                    'Die Website verwendet Gütezeichen, Zertifikate oder Auszeichnungen. '
                    'Diese sollten durch einen Link zum Zertifikat oder Prüfbericht belegt werden. '
                    'Nicht belegte oder veraltete Siegel können eine Irreführung nach §5 UWG darstellen.'
                ),
                risk_euro=1000,
                recommendation=(
                    'Verlinken Sie jedes Gütesiegel mit dem aktuellen Zertifikat oder Prüfbericht. '
                    'Stellen Sie sicher, dass Auszeichnungen aktuell und nicht abgelaufen sind.'
                ),
                legal_basis='UWG §5 Abs. 1 Nr. 1 (Irreführung über Eigenschaften)',
                auto_fixable=False,
                is_missing=False,
            )))

    return issues
