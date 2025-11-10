"""
Impressum Check (TMG §5)
Prüft Impressum-Compliance
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import re

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

async def check_impressum_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Prüft Impressum-Compliance
    
    1. Impressum-Link vorhanden
    2. Impressum-Inhalte (wenn erreichbar)
    """
    issues = []
    
    # Suche Impressum-Link
    impressum_links = soup.find_all('a', text=re.compile(r'impressum|imprint|legal\s+notice', re.I))
    footer_links = soup.find_all('a', href=re.compile(r'impressum|imprint|legal', re.I))
    
    all_impressum_links = impressum_links + footer_links
    
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
        # TODO: Erweiterte Prüfung - Impressum-Seite crawlen und Pflichtangaben prüfen
        # wenn Link vorhanden ist, aber Inhalte unvollständig sind
        pass
    
    return issues

