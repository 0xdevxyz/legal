"""
Datenschutz Check (DSGVO)
Prüft Datenschutzerklärung-Compliance
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import re

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
    is_missing: bool = False  # True wenn komplettes Element fehlt (nicht nur Unterpunkt)

async def check_datenschutz_compliance(url: str, soup: BeautifulSoup, session=None) -> List[Dict[str, Any]]:
    """
    Prüft Datenschutzerklärung-Compliance
    
    1. Datenschutz-Link vorhanden
    2. Datenschutzerklärung-Inhalte (wenn erreichbar)
    """
    issues = []
    
    # Suche Datenschutz-Link
    datenschutz_patterns = [
        r'datenschutz',
        r'privacy\s+policy',
        r'data\s+protection',
        r'dsgvo'
    ]
    
    datenschutz_links = []
    for pattern in datenschutz_patterns:
        links = soup.find_all('a', text=re.compile(pattern, re.I))
        datenschutz_links.extend(links)
        
        href_links = soup.find_all('a', href=re.compile(pattern, re.I))
        datenschutz_links.extend(href_links)
    
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
        # TODO: Erweiterte Prüfung - Datenschutzerklärung crawlen und Pflichtangaben prüfen
        # wenn Link vorhanden ist, aber Inhalte unvollständig sind
        pass
    
    return issues

