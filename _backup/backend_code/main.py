from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiohttp
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import Dict, List, Any
import logging
import asyncio

# INTEGRIERTE ENHANCED ENGINE - Google Fonts Focus
class GoogleFontsEnhancedEngine:
    def __init__(self):
        logging.info("Google Fonts Enhanced Engine initialized")
        
    async def analyze_website_comprehensive(self, url: str) -> Dict[str, Any]:
        """Complete website analysis with Google Fonts priority"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    content = await response.text()
            
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text().lower()
            
            # Google Fonts Analysis - HIGHEST PRIORITY
            google_fonts_result = await self._analyze_google_fonts_comprehensive(url, content, soup)
            
            # Basic compliance checks
            impressum_result = self._analyze_impressum_basic(text)
            datenschutz_result = self._analyze_datenschutz_basic(text)
            cookies_result = self._analyze_cookies_basic(soup, text)
            
            # Calculate overall score (Google Fonts = 45% weight!)
            overall_score = self._calculate_weighted_score(
                google_fonts_result, impressum_result, datenschutz_result, cookies_result
            )
            
            return {
                "url": url, 
                "scan_timestamp": datetime.now().isoformat(),
                "overall_score": overall_score,
                "enhanced_engine_active": True,
                "analysis_version": "2.2.0_integrated",
                "google_fonts": google_fonts_result,
                "impressum": impressum_result,
                "datenschutz": datenschutz_result,
                "cookie_tracking": cookies_result
            }
            
        except Exception as e:
            logging.error(f"Enhanced analysis failed for {url}: {str(e)}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "url": url,
                "fallback_available": True
            }

    async def _analyze_google_fonts_comprehensive(self, url: str, content: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Comprehensive Google Fonts DSGVO violation detection"""
        violations = []
        fonts_found = []
        total_violations = 0
        
        # HTML Link Tags Analysis
        for link in soup.find_all('link', href=True):
            href = link.get('href', '')
            if any(domain in href for domain in ['fonts.googleapis.com', 'fonts.gstatic.com']):
                total_violations += 1
                
                # Extract font families from URL
                font_families = []
                family_match = re.search(r'family=([^&]+)', href)
                if family_match:
                    families_raw = family_match.group(1)
                    for family_part in families_raw.split('|'):
                        font_name = family_part.split(':')[0].replace('+', ' ')
                        font_families.append(font_name)
                        fonts_found.append(font_name)
                
                violations.append(f"Link-Tag lädt Google Fonts: {', '.join(font_families) if font_families else 'unbekannte Schriften'}")
        
        # CSS @import Statements
        for style_tag in soup.find_all('style'):
            css_content = style_tag.get_text()
            import_matches = re.findall(r'@import\s+(?:url\()?["\']?(https?://fonts\.googleapis\.com[^"\';\)]+)', css_content, re.IGNORECASE)
            for import_url in import_matches:
                total_violations += 1
                violations.append("CSS @import Statement lädt Google Fonts")
        
        # JavaScript-based Font Loading
        js_patterns = [r'WebFont\.load', r'fonts\.googleapis\.com', r'GoogleFonts']
        for script in soup.find_all('script'):
            script_content = script.get_text()
            for pattern in js_patterns:
                if re.search(pattern, script_content, re.IGNORECASE):
                    total_violations += 1
                    violations.append(f"JavaScript lädt Google Fonts")
                    break
        
        # Assessment
        if total_violations == 0:
            return {
                "status": "pass",
                "score": 100,
                "message": "✅ Keine Google Fonts gefunden - DSGVO-konform",
                "total_violations": 0,
                "fonts_found": [],
                "violations": [],
                "abmahn_risk": "Niedrig",
                "legal_status": "DSGVO-konform"
            }
        
        unique_fonts = list(set(fonts_found))
        risk_level = "Sehr Hoch" if total_violations >= 3 else "Hoch" if total_violations >= 1 else "Mittel"
        
        return {
            "status": "critical",
            "score": 0,
            "message": f"🚨 {total_violations} Google Fonts DSGVO-Verstöße erkannt - Kritisches Abmahnrisiko!",
            "total_violations": total_violations,
            "fonts_found": unique_fonts,
            "violations": violations,
            "abmahn_risk": risk_level,
            "legal_status": "SCHWERWIEGENDER DSGVO-Verstoß",
            "potential_costs": {
                "risk_level": risk_level,
                "cost_range": "2500-6000€" if risk_level == "Sehr Hoch" else "1200-3500€",
                "typical_case": "4000€" if risk_level == "Sehr Hoch" else "2000€"
            },
            "immediate_remediation": [
                "🚨 SOFORT: Alle <link> Tags zu Google Fonts aus HTML entfernen",
                "💾 Schriftarten von fonts.google.com herunterladen",
                "📁 Fonts lokal auf Server speichern (/assets/fonts/)",
                "🔧 @font-face CSS-Regeln für lokale Schriftarten erstellen"
            ]
        }

    def _analyze_impressum_basic(self, text: str) -> Dict[str, Any]:
        """Basic Impressum compliance check"""
        required_elements = ['impressum', 'name', 'adresse', 'telefon', 'email']
        found_count = sum(1 for element in required_elements if element in text)
        score = int((found_count / len(required_elements)) * 100)
        
        return {
            "status": "pass" if score >= 80 else "warning" if score >= 60 else "fail",
            "score": score,
            "found_elements": found_count,
            "total_elements": len(required_elements),
            "issues": [f"{len(required_elements) - found_count} Pflichtangaben fehlen"] if found_count < len(required_elements) else [],
            "legal_basis": "§ 5 TMG, § 18 MStV"
        }

    def _analyze_datenschutz_basic(self, text: str) -> Dict[str, Any]:
        """Basic privacy policy compliance check"""
        required_elements = ['datenschutz', 'dsgvo', 'verantwortlich', 'zweck', 'rechtsgrundlage']
        found_count = sum(1 for element in required_elements if element in text)
        score = int((found_count / len(required_elements)) * 100)
        
        return {
            "status": "pass" if score >= 80 else "warning" if score >= 60 else "fail",
            "score": score,
            "found_elements": found_count,
            "total_elements": len(required_elements),
            "issues": [f"{len(required_elements) - found_count} DSGVO-Pflichtangaben fehlen"] if found_count < len(required_elements) else [],
            "legal_basis": "Art. 13, 14 DSGVO"
        }

    def _analyze_cookies_basic(self, soup: BeautifulSoup, text: str) -> Dict[str, Any]:
        """Basic cookie compliance analysis"""
        cookie_banner_selectors = ['[class*="cookie"]', '[id*="cookie"]', '[class*="consent"]']
        cookie_banner_found = any(soup.select(selector) for selector in cookie_banner_selectors)
        
        tracking_scripts = []
        for script in soup.find_all('script'):
            script_content = script.get_text() + (script.get('src') or '')
            script_lower = script_content.lower()
            
            if 'google-analytics' in script_lower or 'gtag' in script_lower:
                tracking_scripts.append('Google Analytics')
            if 'facebook' in script_lower and 'pixel' in script_lower:
                tracking_scripts.append('Facebook Pixel')
        
        score = 70 if cookie_banner_found and not tracking_scripts else 40
        
        return {
            "cookie_banner_found": cookie_banner_found,
            "tracking_scripts": list(set(tracking_scripts)),
            "score": score,
            "status": "pass" if score >= 70 else "warning"
        }

    def _calculate_weighted_score(self, google_fonts: Dict, impressum: Dict, datenschutz: Dict, cookies: Dict) -> int:
        """Calculate overall score with Google Fonts having maximum weight"""
        weights = {"google_fonts": 0.45, "impressum": 0.25, "datenschutz": 0.25, "cookies": 0.05}
        
        weighted_score = (
            google_fonts.get("score", 0) * weights["google_fonts"] +
            impressum.get("score", 0) * weights["impressum"] +
            datenschutz.get("score", 0) * weights["datenschutz"] +
            cookies.get("score", 50) * weights["cookies"]
        )
        
        return int(weighted_score)


# FastAPI Application Setup
app = FastAPI(
    title="Complyo Google Fonts Enhanced API",
    description="Professional Website Compliance Analysis with Google Fonts DSGVO Focus",
    version="2.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Enhanced Engine
enhanced_engine = GoogleFontsEnhancedEngine()

class AnalyzeRequest(BaseModel):
    url: str
    deep_scan: bool = True

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "complyo-google-fonts-enhanced-integrated",
        "version": "2.2.0",
        "google_fonts_scanner": "active_integrated",
        "enhanced_engine": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    return {
        "message": "Complyo Google Fonts Enhanced API - Native Integration",
        "status": "ok",
        "version": "2.2.0",
        "engine_type": "integrated_native"
    }

@app.get("/api/status")
async def api_status():
    return {
        "api_version": "2.2.0",
        "enhanced_engine": True,
        "integration_type": "native_embedded",
        "google_fonts_priority": "maximum",
        "services": {
            "google_fonts_scanner": "active_comprehensive",
            "enhanced_compliance_engine": "native_integrated",
            "abmahn_risk_calculator": "active_detailed"
        }
    }

@app.post("/api/analyze")
async def analyze_website_enhanced(request: AnalyzeRequest):
    """Enhanced Website Compliance Analysis with Google Fonts Priority"""
    try:
        logger.info(f"Starting enhanced analysis for: {request.url}")
        result = await enhanced_engine.analyze_website_comprehensive(request.url)
        logger.info(f"Analysis completed for {request.url}")
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed for {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/demo")
async def get_enhanced_demo():
    """Enhanced Demo Data with Google Fonts Critical Focus"""
    return {
        "url": "https://demo-google-fonts-violations.example.com",
        "scan_timestamp": datetime.now().isoformat(),
        "overall_score": 22,
        "enhanced_engine_active": True,
        "analysis_version": "2.2.0_integrated",
        "google_fonts": {
            "status": "critical",
            "score": 0,
            "message": "🚨 3 Google Fonts DSGVO-Verstöße erkannt - Kritisches Abmahnrisiko!",
            "total_violations": 3,
            "fonts_found": ["Roboto", "Open Sans", "Montserrat"],
            "violations": [
                "Link-Tag lädt Google Fonts: Roboto",
                "Link-Tag lädt Google Fonts: Open Sans", 
                "CSS @import Statement lädt Google Fonts"
            ],
            "abmahn_risk": "Sehr Hoch",
            "legal_status": "SCHWERWIEGENDER DSGVO-Verstoß",
            "potential_costs": {
                "risk_level": "Sehr Hoch",
                "cost_range": "2500-6000€",
                "typical_case": "4000€"
            },
            "immediate_remediation": [
                "🚨 SOFORT: Alle <link> Tags zu Google Fonts aus HTML entfernen",
                "💾 Schriftarten von fonts.google.com herunterladen",
                "📁 Fonts lokal auf Server speichern (/assets/fonts/)",
                "🔧 @font-face CSS-Regeln für lokale Schriftarten erstellen"
            ]
        },
        "impressum": {
            "status": "warning",
            "score": 75,
            "found_elements": 4,
            "total_elements": 5,
            "issues": ["1 Pflichtangaben fehlen"]
        },
        "datenschutz": {
            "status": "pass",
            "score": 85,
            "found_elements": 5,
            "total_elements": 5,
            "issues": []
        },
        "cookie_tracking": {
            "cookie_banner_found": True,
            "tracking_scripts": ["Google Analytics"],
            "score": 70,
            "status": "pass"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
