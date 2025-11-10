"""
Quick Scanner for instant compliance feedback (10-20 seconds)
Runs parallel checks for critical issues only
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from datetime import datetime
import ssl
import certifi

class QuickScanner:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15),  # Shorter timeout for quick scan
            connector=connector,
            headers={
                'User-Agent': 'Complyo-QuickScanner/1.0 (Compliance Bot; +https://complyo.tech/scanner)'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def quick_scan(self, url: str) -> Dict[str, Any]:
        """
        Fast parallel scan for critical issues only
        Returns results in 10-20 seconds
        """
        start_time = datetime.now()
        
        try:
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Fetch main page
            main_page = await self._fetch_page(url)
            if not main_page:
                return self._create_error_response(url, "Website nicht erreichbar")
            
            soup = BeautifulSoup(main_page['content'], 'html.parser')
            
            # Run quick checks IN PARALLEL
            results = await asyncio.gather(
                self._quick_ssl_check(url),
                self._quick_impressum_check(url, soup),
                self._quick_cookie_check(url, soup),
                self._quick_datenschutz_check(url, soup),
                return_exceptions=True
            )
            
            # Collect issues
            issues = []
            for result in results:
                if isinstance(result, list):
                    issues.extend(result)
                elif isinstance(result, Exception):
                    # Log error but continue
                    pass
            
            # Calculate quick metrics
            critical_count = len([i for i in issues if i.get('severity') == 'critical'])
            warning_count = len([i for i in issues if i.get('severity') == 'warning'])
            total_risk = sum(i.get('risk_euro', 0) for i in issues)
            
            # Quick score (simplified)
            compliance_score = max(0, 100 - (critical_count * 25 + warning_count * 10))
            
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "url": url,
                "scan_type": "quick",
                "scan_timestamp": start_time.isoformat(),
                "scan_duration_ms": duration_ms,
                "compliance_score": compliance_score,
                "total_risk_euro": total_risk,
                "critical_issues": critical_count,
                "warning_issues": warning_count,
                "total_issues": len(issues),
                "issues": issues,
                "is_complete": False,  # Indicates more detailed scan recommended
                "next_steps": self._generate_quick_next_steps(issues, critical_count)
            }
            
        except Exception as e:
            return self._create_error_response(url, f"Quick-Scan Fehler: {str(e)}")
    
    async def _fetch_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch webpage with short timeout"""
        try:
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    content = await response.text()
                    return {
                        'url': str(response.url),
                        'status_code': response.status,
                        'content': content,
                        'headers': dict(response.headers)
                    }
        except:
            return None
    
    async def _quick_ssl_check(self, url: str) -> List[Dict[str, Any]]:
        """Quick SSL/HTTPS check"""
        issues = []
        
        if not url.startswith('https://'):
            issues.append({
                "category": "security",
                "severity": "critical",
                "title": "Keine HTTPS-Verschlüsselung",
                "description": "Website nutzt kein HTTPS. Daten werden unverschlüsselt übertragen.",
                "risk_euro": 5000,
                "recommendation": "SSL-Zertifikat installieren und HTTPS aktivieren",
                "legal_basis": "DSGVO Art. 32 (Datensicherheit)",
                "auto_fixable": False,
                "ai_explanation": "HTTPS verschlüsselt die Verbindung zwischen Browser und Server. Ohne HTTPS können Dritte sensible Daten mitlesen."
            })
        
        return issues
    
    async def _quick_impressum_check(self, url: str, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Quick check if impressum exists"""
        issues = []
        
        # Look for impressum links
        impressum_found = False
        impressum_keywords = ['impressum', 'imprint', 'anbieterkennzeichnung']
        
        links = soup.find_all('a', href=True)
        for link in links:
            link_text = link.get_text().lower()
            href = link.get('href', '').lower()
            if any(keyword in link_text or keyword in href for keyword in impressum_keywords):
                impressum_found = True
                break
        
        if not impressum_found:
            issues.append({
                "category": "impressum",
                "severity": "critical",
                "title": "Impressum fehlt",
                "description": "Es wurde kein Impressum gefunden. Dies ist gesetzlich vorgeschrieben.",
                "risk_euro": 5000,
                "recommendation": "Impressum mit vollständigen Anbieterdaten erstellen",
                "legal_basis": "TMG § 5",
                "auto_fixable": True,
                "is_missing": True,
                "ai_explanation": "Das Impressum muss Name, Adresse und Kontaktdaten des Betreibers enthalten. Es schützt Nutzer und ist für alle gewerblichen Websites Pflicht."
            })
        
        return issues
    
    async def _quick_cookie_check(self, url: str, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Quick check for cookie consent"""
        issues = []
        
        # Check for common cookie consent tools
        consent_found = False
        consent_patterns = [
            'cookie-consent', 'cookie-banner', 'cookiebanner', 
            'gdpr-cookie', 'cookie-notice', 'usercentrics',
            'onetrust', 'cookiebot', 'borlabs'
        ]
        
        html_content = str(soup).lower()
        for pattern in consent_patterns:
            if pattern in html_content:
                consent_found = True
                break
        
        # Check for actual cookies set
        scripts = soup.find_all('script')
        tracking_found = False
        tracking_tools = ['google-analytics', 'gtag', 'googletagmanager', 'facebook', 'fbq']
        
        for script in scripts:
            script_content = script.string or ''
            if any(tool in script_content.lower() for tool in tracking_tools):
                tracking_found = True
                break
        
        if tracking_found and not consent_found:
            issues.append({
                "category": "cookies",
                "severity": "critical",
                "title": "Cookie-Consent fehlt",
                "description": "Tracking-Tools gefunden, aber kein Cookie-Consent-Banner. Nutzer müssen zustimmen, bevor Cookies gesetzt werden.",
                "risk_euro": 50000,
                "recommendation": "Cookie-Consent-Banner implementieren (z.B. Usercentrics, CookieBot)",
                "legal_basis": "TTDSG § 25, DSGVO Art. 7",
                "auto_fixable": True,
                "ai_explanation": "Seit 2021 müssen Nutzer aktiv zustimmen, bevor Tracking-Cookies gesetzt werden. Ein Cookie-Banner ist Pflicht für alle Websites mit Tracking."
            })
        
        return issues
    
    async def _quick_datenschutz_check(self, url: str, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Quick check for privacy policy"""
        issues = []
        
        # Look for privacy policy links
        datenschutz_found = False
        privacy_keywords = ['datenschutz', 'privacy', 'data protection', 'dsgvo']
        
        links = soup.find_all('a', href=True)
        for link in links:
            link_text = link.get_text().lower()
            href = link.get('href', '').lower()
            if any(keyword in link_text or keyword in href for keyword in privacy_keywords):
                datenschutz_found = True
                break
        
        if not datenschutz_found:
            issues.append({
                "category": "datenschutz",
                "severity": "critical",
                "title": "Datenschutzerklärung fehlt",
                "description": "Es wurde keine Datenschutzerklärung gefunden.",
                "risk_euro": 10000,
                "recommendation": "DSGVO-konforme Datenschutzerklärung erstellen",
                "legal_basis": "DSGVO Art. 13",
                "auto_fixable": True,
                "is_missing": True,
                "ai_explanation": "Die Datenschutzerklärung informiert Nutzer darüber, welche Daten erhoben werden und wie sie verarbeitet werden. Sie ist für alle Websites Pflicht."
            })
        
        return issues
    
    def _generate_quick_next_steps(self, issues: List[Dict], critical_count: int) -> List[str]:
        """Generate actionable next steps"""
        steps = []
        
        if critical_count > 0:
            steps.append(f"🚨 {critical_count} kritische Probleme sofort beheben")
            steps.append("💡 KI-Fix generieren für schnelle Lösungen")
        else:
            steps.append("✅ Keine kritischen Probleme gefunden")
            steps.append("🔍 Starten Sie eine tiefere Analyse für Details")
        
        steps.append("📋 Detaillierten Report herunterladen")
        
        return steps
    
    def _create_error_response(self, url: str, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "error": True,
            "error_message": error_message,
            "url": url,
            "scan_type": "quick",
            "scan_timestamp": datetime.now().isoformat(),
            "compliance_score": 0,
            "issues": []
        }

