"""
TCF Vendor Analyzer
Lädt Global Vendor List (GVL) und analysiert Vendor Consents
"""

import httpx
import json
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
import asyncio

# Cache für GVL (Global Vendor List)
_gvl_cache = None
_gvl_cache_time = None
GVL_CACHE_DURATION = timedelta(hours=24)  # Cache für 24 Stunden

GVL_URL = "https://vendor-list.consensu.org/v2/vendor-list.json"
GVL_FALLBACK_URL = "https://iabeurope.eu/vendor-list-tcf-v2-0/"


class TCFVendorAnalyzer:
    """
    Analysiert TCF Vendors und Consent Strings
    """
    
    def __init__(self):
        self.gvl_data = None
    
    async def load_global_vendor_list(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Lädt die Global Vendor List (GVL) von IAB Europe
        """
        global _gvl_cache, _gvl_cache_time
        
        # Prüfe Cache
        if not force_refresh and _gvl_cache and _gvl_cache_time:
            if datetime.now() - _gvl_cache_time < GVL_CACHE_DURATION:
                self.gvl_data = _gvl_cache
                return _gvl_cache
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(GVL_URL)
                response.raise_for_status()
                
                gvl_data = response.json()
                
                # Cache aktualisieren
                _gvl_cache = gvl_data
                _gvl_cache_time = datetime.now()
                self.gvl_data = gvl_data
                
                return gvl_data
        
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Global Vendor List: {e}")
            
            # Fallback: Lade aus lokalem Cache oder verwende Minimal-GVL
            return self._get_fallback_gvl()
    
    def _get_fallback_gvl(self) -> Dict[str, Any]:
        """
        Fallback GVL mit den wichtigsten Vendors
        """
        return {
            "gvlSpecificationVersion": 2,
            "vendorListVersion": 1,
            "tcfPolicyVersion": 2,
            "lastUpdated": datetime.now().isoformat(),
            "purposes": {
                "1": {"name": "Store and/or access information on a device"},
                "2": {"name": "Select basic ads"},
                "3": {"name": "Create a personalised ads profile"},
                "4": {"name": "Select personalised ads"},
                "5": {"name": "Create a personalised content profile"},
                "6": {"name": "Select personalised content"},
                "7": {"name": "Measure ad performance"},
                "8": {"name": "Measure content performance"},
                "9": {"name": "Apply market research"},
                "10": {"name": "Develop and improve products"}
            },
            "vendors": {
                "755": {"name": "Google Advertising Products"},
                "45": {"name": "Facebook"},
                "52": {"name": "The Trade Desk"},
                "754": {"name": "Google Analytics"},
                "61": {"name": "Amazon"},
                "10": {"name": "Criteo"},
                "32": {"name": "Xandr (AppNexus)"},
                "21": {"name": "MediaMath"},
                "76": {"name": "PubMatic"},
                "81": {"name": "Sovrn"}
            }
        }
    
    def get_vendor_by_id(self, vendor_id: int) -> Optional[Dict[str, Any]]:
        """
        Holt Vendor-Informationen aus der GVL
        """
        if not self.gvl_data:
            return None
        
        vendors = self.gvl_data.get("vendors", {})
        return vendors.get(str(vendor_id))
    
    def get_purpose_by_id(self, purpose_id: int) -> Optional[Dict[str, Any]]:
        """
        Holt Purpose-Informationen aus der GVL
        """
        if not self.gvl_data:
            return None
        
        purposes = self.gvl_data.get("purposes", {})
        return purposes.get(str(purpose_id))
    
    def parse_tc_string_basic(self, tc_string: str) -> Dict[str, Any]:
        """
        Basis-Parsing eines TC Strings (vereinfacht)
        
        HINWEIS: Vollständiges TC String Parsing erfordert die IAB TCF Library.
        Dies ist eine vereinfachte Version für grundlegende Informationen.
        """
        
        result = {
            "valid": False,
            "version": None,
            "created": None,
            "updated": None,
            "cmp_id": None,
            "cmp_version": None,
            "vendor_consents": [],
            "vendor_legitimate_interests": [],
            "purpose_consents": [],
            "purpose_legitimate_interests": [],
            "special_feature_opt_ins": [],
            "publisher_restrictions": {},
            "error": None
        }
        
        try:
            # TC String v2 ist Base64-URL encoded
            # Format: Core String enthält Version, Timestamps, CMP ID, etc.
            
            # Entferne Segmente (. getrennt)
            segments = tc_string.split('.')
            core_string = segments[0] if segments else tc_string
            
            # Versuche Base64-URL Decode (vereinfacht)
            # In Produktion würde man hier die offizielle IAB TCF Library verwenden
            
            # Für diese Implementation geben wir strukturierte Daten zurück
            # ohne vollständiges Parsing
            
            result["valid"] = True
            result["version"] = "2.2"  # Annahme
            result["tc_string"] = tc_string
            result["segments_count"] = len(segments)
            
            # Info: Für vollständiges Parsing würde man benötigen:
            # - Bit-level Parsing des Base64-decodierten Strings
            # - Field-by-field Extraktion nach TCF v2.2 Spec
            # - Vendor/Purpose Bit Vectors dekodieren
            
            result["note"] = "Vollständiges TC String Parsing erfordert IAB TCF Library"
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def analyze_vendors_on_page(self, soup, page_content: str = "") -> List[Dict[str, Any]]:
        """
        Analysiert welche Vendors auf der Seite aktiv sind
        (basierend auf Script-Tags und bekannten Patterns)
        """
        
        detected_vendors = []
        
        # Lade GVL
        if not self.gvl_data:
            await self.load_global_vendor_list()
        
        # Bekannte Vendor Patterns (Domain-basiert)
        vendor_patterns = {
            "755": {  # Google
                "name": "Google Advertising Products",
                "domains": [r'doubleclick\.net', r'google-analytics\.com', r'googletagmanager\.com', 
                           r'googlesyndication\.com', r'googleadservices\.com']
            },
            "45": {  # Facebook
                "name": "Facebook",
                "domains": [r'facebook\.com/tr', r'facebook\.net', r'connect\.facebook\.net']
            },
            "52": {  # The Trade Desk
                "name": "The Trade Desk",
                "domains": [r'adsrvr\.org', r'thetradedesk\.com']
            },
            "10": {  # Criteo
                "name": "Criteo",
                "domains": [r'criteo\.com', r'criteo\.net']
            },
            "61": {  # Amazon
                "name": "Amazon",
                "domains": [r'amazon-adsystem\.com', r'amazontag\.com']
            },
            "32": {  # Xandr
                "name": "Xandr (AppNexus)",
                "domains": [r'adnxs\.com', r'appnexus\.com']
            },
            "76": {  # PubMatic
                "name": "PubMatic",
                "domains": [r'pubmatic\.com']
            },
            "81": {  # Sovrn
                "name": "Sovrn",
                "domains": [r'lijit\.com', r'sovrn\.com']
            },
            "21": {  # MediaMath
                "name": "MediaMath",
                "domains": [r'mathtag\.com', r'mediamath\.com']
            },
            "754": {  # Google Analytics
                "name": "Google Analytics",
                "domains": [r'google-analytics\.com']
            }
        }
        
        # Suche nach Vendor-Scripts
        scripts = soup.find_all('script', src=True)
        
        for script in scripts:
            src = script.get('src', '').lower()
            
            for vendor_id, vendor_data in vendor_patterns.items():
                for domain_pattern in vendor_data["domains"]:
                    if re.search(domain_pattern, src, re.I):
                        
                        # Prüfe ob bereits hinzugefügt
                        if not any(v["vendor_id"] == vendor_id for v in detected_vendors):
                            detected_vendors.append({
                                "vendor_id": vendor_id,
                                "vendor_name": vendor_data["name"],
                                "detected_from": "script_src",
                                "source": src,
                                "requires_consent": True  # Alle diese Vendors benötigen Consent
                            })
                        
                        break
        
        return detected_vendors
    
    def get_vendor_purposes(self, vendor_id: int) -> List[Dict[str, Any]]:
        """
        Holt die Purposes für einen Vendor
        """
        if not self.gvl_data:
            return []
        
        vendor = self.get_vendor_by_id(vendor_id)
        if not vendor:
            return []
        
        purposes = []
        
        # Purposes mit Consent
        for purpose_id in vendor.get("purposes", []):
            purpose = self.get_purpose_by_id(purpose_id)
            if purpose:
                purposes.append({
                    "id": purpose_id,
                    "name": purpose.get("name"),
                    "legal_basis": "consent"
                })
        
        # Purposes mit Legitimate Interest
        for purpose_id in vendor.get("legIntPurposes", []):
            purpose = self.get_purpose_by_id(purpose_id)
            if purpose:
                purposes.append({
                    "id": purpose_id,
                    "name": purpose.get("name"),
                    "legal_basis": "legitimate_interest"
                })
        
        return purposes
    
    async def generate_vendor_report(self, detected_vendors: List[Dict], tc_string: Optional[str] = None) -> Dict[str, Any]:
        """
        Generiert einen Vendor Compliance Report
        """
        
        report = {
            "total_vendors_detected": len(detected_vendors),
            "vendors_requiring_consent": len([v for v in detected_vendors if v.get("requires_consent")]),
            "tc_string_present": tc_string is not None,
            "vendors": []
        }
        
        # Lade GVL falls noch nicht geladen
        if not self.gvl_data:
            await self.load_global_vendor_list()
        
        for vendor in detected_vendors:
            vendor_id = int(vendor["vendor_id"])
            vendor_info = self.get_vendor_by_id(vendor_id)
            
            vendor_report = {
                "id": vendor_id,
                "name": vendor["vendor_name"],
                "detected_from": vendor.get("detected_from"),
                "requires_consent": vendor.get("requires_consent"),
                "purposes": self.get_vendor_purposes(vendor_id),
                "consent_status": "unknown"  # Würde aus TC String kommen
            }
            
            # Wenn TC String vorhanden, könnte man hier Consent Status prüfen
            # (erfordert vollständiges TC String Parsing)
            
            report["vendors"].append(vendor_report)
        
        return report


# Singleton Instance
tcf_vendor_analyzer = TCFVendorAnalyzer()


# Import für re module (vergessen oben)
import re

