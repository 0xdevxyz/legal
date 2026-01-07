"""
TCF 2.2 Compliance Check
Prüft IAB Transparency & Consent Framework v2.2 Compliance
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import re
import json

@dataclass
class TCFIssue:
    category: str
    severity: str
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool = False
    tcf_specific: bool = True

async def check_tcf_compliance(url: str, soup: BeautifulSoup, page_content: str = "") -> Dict[str, Any]:
    """
    Prüft TCF 2.2 Compliance
    
    Returns:
        dict with:
        - has_tcf: bool
        - tcf_version: str | None
        - cmp_id: int | None
        - cmp_name: str | None
        - issues: List[Dict]
        - tc_string_found: bool
        - vendor_count: int
    """
    
    issues = []
    tcf_data = {
        "has_tcf": False,
        "tcf_version": None,
        "cmp_id": None,
        "cmp_name": None,
        "tc_string_found": False,
        "vendor_count": 0,
        "issues": []
    }
    
    # 1. Prüfe ob __tcfapi vorhanden ist
    has_tcfapi = False
    
    # Suche nach __tcfapi in Inline-Scripts
    inline_scripts = soup.find_all('script', src=False)
    for script in inline_scripts:
        script_content = script.string or ''
        if '__tcfapi' in script_content or 'window.__tcfapi' in script_content:
            has_tcfapi = True
            tcf_data["has_tcf"] = True
            break
    
    # Suche nach __tcfapi in externen Scripts (häufig bei CMPs)
    if not has_tcfapi:
        external_scripts = soup.find_all('script', src=True)
        for script in external_scripts:
            src = script.get('src', '').lower()
            # Bekannte TCF CMPs
            tcf_patterns = [
                r'consent\.cookiebot\.com',
                r'cdn\.privacy-mgmt\.com',  # Sourcepoint
                r'quantcast\.mgr\.consensu\.org',  # Quantcast Choice
                r'cmp\.uniconsent\.com',
                r'cdn\.consentmanager\.mgr\.consensu\.org'
            ]
            
            for pattern in tcf_patterns:
                if re.search(pattern, src):
                    has_tcfapi = True
                    tcf_data["has_tcf"] = True
                    
                    # Erkenne CMP
                    if 'cookiebot' in src:
                        tcf_data["cmp_name"] = "Cookiebot"
                        tcf_data["cmp_id"] = 11  # Cookiebot CMP ID
                    elif 'privacy-mgmt' in src or 'sourcepoint' in src:
                        tcf_data["cmp_name"] = "Sourcepoint"
                        tcf_data["cmp_id"] = 6
                    elif 'quantcast' in src:
                        tcf_data["cmp_name"] = "Quantcast Choice"
                        tcf_data["cmp_id"] = 10
                    elif 'uniconsent' in src:
                        tcf_data["cmp_name"] = "UniConsent"
                        tcf_data["cmp_id"] = 42
                    elif 'consentmanager' in src:
                        tcf_data["cmp_name"] = "consentmanager"
                        tcf_data["cmp_id"] = 31
                    
                    break
    
    # 2. Prüfe auf TC String (Consent String v2)
    # TC Strings können in verschiedenen Orten gespeichert sein:
    # - Cookie: euconsent-v2
    # - localStorage: euconsent-v2
    # - Als Data Attribute
    
    # Suche nach TC String Referenzen im JavaScript
    tc_string_patterns = [
        r'euconsent-v2',
        r'IABTCF_TCString',
        r'tcString',
        r'getTCData',
        r'__tcfapi\([\'"]getTCData'
    ]
    
    for script in inline_scripts:
        script_content = script.string or ''
        for pattern in tc_string_patterns:
            if re.search(pattern, script_content, re.I):
                tcf_data["tc_string_found"] = True
                break
        if tcf_data["tc_string_found"]:
            break
    
    # 3. Prüfe TCF Version
    # TCF v2.2 ist der aktuelle Standard (seit 2021)
    tcf_version_patterns = [
        r'tcfPolicyVersion["\']?\s*:\s*["\']?(\d+)',
        r'TCF\s+v?(\d\.\d)',
        r'__tcfapi.*version.*?(\d\.\d)'
    ]
    
    for script in inline_scripts:
        script_content = script.string or ''
        for pattern in tcf_version_patterns:
            match = re.search(pattern, script_content, re.I)
            if match:
                version = match.group(1)
                tcf_data["tcf_version"] = version
                break
        if tcf_data["tcf_version"]:
            break
    
    # 4. Generiere Issues basierend auf Findings
    
    if not has_tcfapi:
        # Kein TCF gefunden - das ist kein Fehler per se, aber eine Info
        # Nur Issue erstellen wenn bereits ein CMP vorhanden ist (z.B. nicht-TCF)
        
        # Prüfe ob ein nicht-TCF CMP vorhanden ist
        non_tcf_cmps = [
            r'onetrust',  # OneTrust hat TCF-Support, aber nicht immer aktiviert
            r'usercentrics',  # Usercentrics kann mit/ohne TCF laufen
            r'cookiefirst',
            r'osano',
            r'complianz'
        ]
        
        has_non_tcf_cmp = False
        cmp_name = None
        
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            src = script.get('src', '').lower()
            for cmp in non_tcf_cmps:
                if cmp in src:
                    has_non_tcf_cmp = True
                    cmp_name = cmp.title()
                    break
            if has_non_tcf_cmp:
                break
        
        if has_non_tcf_cmp:
            issues.append(asdict(TCFIssue(
                category='cookies',
                severity='info',
                title='TCF 2.2 nicht implementiert',
                description=f'Sie nutzen {cmp_name}, aber ohne TCF 2.2 Framework. '
                           f'Für Publisher und Websites mit vielen Werbepartnern ist TCF 2.2 empfohlen, '
                           f'da es standardisierte Consent-Weitergabe ermöglicht.',
                risk_euro=0,
                recommendation=f'Erwägen Sie die Aktivierung von TCF 2.2 in {cmp_name}, wenn Sie mit '
                             f'Werbenetzwerken arbeiten oder programmatic advertising nutzen.',
                legal_basis='DSGVO Art. 7, ePrivacy Directive',
                auto_fixable=False
            )))
    else:
        # TCF gefunden - prüfe Vollständigkeit
        
        if not tcf_data["tc_string_found"]:
            issues.append(asdict(TCFIssue(
                category='cookies',
                severity='warning',
                title='TCF Consent String nicht gefunden',
                description='__tcfapi wurde gefunden, aber kein TC String (euconsent-v2). '
                           'Dies deutet auf eine unvollständige TCF-Implementation hin.',
                risk_euro=1000,
                recommendation='Stellen Sie sicher, dass Ihre CMP korrekt initialisiert wird und '
                             'TC Strings generiert werden. Prüfen Sie die CMP-Konfiguration.',
                legal_basis='TCF v2.2 Technical Specifications',
                auto_fixable=False
            )))
        
        if not tcf_data["tcf_version"]:
            issues.append(asdict(TCFIssue(
                category='cookies',
                severity='info',
                title='TCF Version nicht erkennbar',
                description='Die TCF Version konnte nicht automatisch ermittelt werden. '
                           'Stellen Sie sicher, dass Sie TCF v2.2 (aktueller Standard) verwenden.',
                risk_euro=0,
                recommendation='Prüfen Sie in Ihrer CMP-Konfiguration, welche TCF Version aktiv ist. '
                             'TCF v2.2 ist seit 2021 der Standard.',
                legal_basis='TCF Policy',
                auto_fixable=False
            )))
        elif tcf_data["tcf_version"] and tcf_data["tcf_version"] != "2.2":
            # Ältere Version gefunden
            issues.append(asdict(TCFIssue(
                category='cookies',
                severity='warning',
                title=f'Veraltete TCF Version ({tcf_data["tcf_version"]})',
                description=f'Sie verwenden TCF v{tcf_data["tcf_version"]}, aber der aktuelle Standard ist v2.2. '
                           f'Ältere Versionen werden möglicherweise nicht mehr von allen Vendors unterstützt.',
                risk_euro=500,
                recommendation='Aktualisieren Sie Ihre CMP auf TCF v2.2 um Kompatibilität mit allen '
                             'IAB-registrierten Vendors sicherzustellen.',
                legal_basis='TCF Policy',
                auto_fixable=False
            )))
        
        # Prüfe ob CMP ID bekannt ist
        if not tcf_data["cmp_id"]:
            issues.append(asdict(TCFIssue(
                category='cookies',
                severity='info',
                title='CMP nicht erkannt',
                description='Die verwendete Consent Management Platform konnte nicht automatisch identifiziert werden.',
                risk_euro=0,
                recommendation='Dies ist kein Problem, aber für detaillierte Analysen wäre die CMP-Identifikation hilfreich.',
                legal_basis='Informational',
                auto_fixable=False
            )))
    
    # 5. Prüfe auf Google Consent Mode v2 (ergänzt TCF)
    has_google_consent_mode = False
    google_consent_patterns = [
        r'gtag\([\'"]consent[\'"]',
        r'gtagConsent',
        r'consent\s*mode',
        r'ad_storage.*analytics_storage'
    ]
    
    for script in inline_scripts:
        script_content = script.string or ''
        for pattern in google_consent_patterns:
            if re.search(pattern, script_content, re.I):
                has_google_consent_mode = True
                break
        if has_google_consent_mode:
            break
    
    if has_tcfapi and not has_google_consent_mode:
        issues.append(asdict(TCFIssue(
            category='cookies',
            severity='info',
            title='Google Consent Mode nicht gefunden',
            description='Sie verwenden TCF, aber kein Google Consent Mode v2. '
                       'Google Consent Mode ist optional, aber empfohlen für Google-Dienste.',
            risk_euro=0,
            recommendation='Wenn Sie Google Analytics oder Google Ads nutzen, implementieren Sie '
                         'zusätzlich Google Consent Mode v2 für optimale Integration.',
            legal_basis='Google Ads Terms',
            auto_fixable=False
        )))
    
    tcf_data["issues"] = issues
    
    return tcf_data


def detect_cmp_from_scripts(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    Hilfsfunktion: Erkenne CMP aus Script-Tags
    """
    cmp_signatures = {
        "Cookiebot": {
            "patterns": [r'consent\.cookiebot\.com', r'cookiebot\.com/uc\.js'],
            "cmp_id": 11
        },
        "OneTrust": {
            "patterns": [r'cdn\.cookielaw\.org', r'onetrust\.com'],
            "cmp_id": 28
        },
        "Usercentrics": {
            "patterns": [r'app\.usercentrics\.eu', r'usercentrics\.com'],
            "cmp_id": 41
        },
        "Sourcepoint": {
            "patterns": [r'cdn\.privacy-mgmt\.com', r'sourcepoint\.com'],
            "cmp_id": 6
        },
        "Quantcast": {
            "patterns": [r'quantcast\.mgr\.consensu\.org', r'quantcast\.com'],
            "cmp_id": 10
        },
        "Didomi": {
            "patterns": [r'sdk\.privacy-center\.org', r'didomi\.io'],
            "cmp_id": 64
        },
        "TrustArc": {
            "patterns": [r'consent\.trustarc\.com', r'trustarc\.com'],
            "cmp_id": 55
        }
    }
    
    scripts = soup.find_all('script', src=True)
    
    for script in scripts:
        src = script.get('src', '').lower()
        
        for cmp_name, data in cmp_signatures.items():
            for pattern in data["patterns"]:
                if re.search(pattern, src, re.I):
                    return {
                        "name": cmp_name,
                        "cmp_id": data["cmp_id"],
                        "detected_from": "script_src"
                    }
    
    return None


def validate_tc_string_format(tc_string: str) -> Dict[str, Any]:
    """
    Validiert TC String Format (oberflächlich)
    Vollständiges Parsing würde IAB TCF Library benötigen
    """
    
    result = {
        "valid": False,
        "version": None,
        "errors": []
    }
    
    # TC String v2 Format: Base64-URL-encoded
    # Beginnt typischerweise mit "C" für Core String
    
    if not tc_string:
        result["errors"].append("TC String ist leer")
        return result
    
    # Prüfe ob Base64-URL Format
    # TC Strings verwenden URL-safe Base64 (- und _ statt + und /)
    if not re.match(r'^[A-Za-z0-9\-_]+$', tc_string):
        result["errors"].append("TC String enthält ungültige Zeichen für Base64-URL Encoding")
        return result
    
    # TC String v2 beginnt normalerweise mit "C" (Core String)
    if not tc_string.startswith('C'):
        result["errors"].append("TC String beginnt nicht mit 'C' (erwartet für v2.2)")
    
    # Minimale Länge prüfen (TC Strings sind normalerweise >100 Zeichen)
    if len(tc_string) < 50:
        result["errors"].append("TC String ist zu kurz (möglicherweise unvollständig)")
        return result
    
    # Wenn keine Fehler, als valide markieren
    if len(result["errors"]) == 0:
        result["valid"] = True
        result["version"] = "2.2"  # Annahme, da "C" Prefix
    
    return result

