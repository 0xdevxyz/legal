"""
Complyo Website Compliance Scanner
Comprehensive scanner for German website compliance (DSGVO, Impressum, Cookies, Accessibility)
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import json
from dataclasses import dataclass, asdict
import ssl
import certifi

@dataclass
class ComplianceIssue:
    category: str
    severity: str  # "critical", "warning", "info"
    title: str
    description: str
    risk_euro: int
    recommendation: str
    legal_basis: str
    auto_fixable: bool = False

class ComplianceScanner:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        # Create SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=connector,
            headers={
                'User-Agent': 'Complyo-Scanner/2.0 (Compliance Bot; +https://complyo.tech/scanner)'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def scan_website(self, url: str) -> Dict[str, Any]:
        """
        Comprehensive compliance scan of a website
        Returns detailed compliance report with risk assessment
        """
        start_time = datetime.now()
        issues = []
        
        try:
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Fetch main page
            main_page = await self._fetch_page(url)
            if not main_page:
                return self._create_error_response(url, "Website nicht erreichbar")
            
            soup = BeautifulSoup(main_page['content'], 'html.parser')
            
            # Run all compliance checks
            issues.extend(await self._check_impressum(url, soup))
            issues.extend(await self._check_privacy_policy(url, soup))
            issues.extend(await self._check_cookie_compliance(url, soup))
            issues.extend(await self._check_accessibility(url, soup))
            issues.extend(await self._check_ssl_security(url))
            issues.extend(await self._check_contact_data(url, soup))
            issues.extend(await self._check_social_media_plugins(url, soup))
            
            # Calculate overall compliance score and risk
            total_risk_euro = sum(issue.risk_euro for issue in issues)
            critical_issues = len([i for i in issues if i.severity == "critical"])
            warning_issues = len([i for i in issues if i.severity == "warning"])
            
            # Score calculation (0-100)
            max_possible_issues = 15  # Rough estimate of maximum issues
            compliance_score = max(0, 100 - (critical_issues * 20 + warning_issues * 5))
            
            # End timing
            end_time = datetime.now()
            scan_duration = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "url": url,
                "scan_timestamp": start_time,
                "scan_duration_ms": scan_duration,
                "compliance_score": compliance_score,
                "total_risk_euro": total_risk_euro,
                "critical_issues": critical_issues,
                "warning_issues": warning_issues,
                "total_issues": len(issues),
                "issues": [asdict(issue) for issue in issues],
                "recommendations": self._generate_recommendations(issues),
                "next_steps": self._generate_next_steps(issues)
            }
            
        except Exception as e:
            return self._create_error_response(url, f"Scanner-Fehler: {str(e)}")
    
    async def _fetch_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch webpage content with error handling"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return {
                        'url': url,
                        'status_code': response.status,
                        'content': content,
                        'headers': dict(response.headers)
                    }
                else:
                    return None
        except Exception:
            return None
    
    async def _check_impressum(self, base_url: str, soup: BeautifulSoup) -> List[ComplianceIssue]:
        """Check for legal notice (Impressum) compliance"""
        issues = []
        
        # Look for Impressum links
        impressum_links = soup.find_all('a', text=re.compile(r'impressum|imprint|rechtliche hinweise', re.I))
        
        if not impressum_links:
            # Check for footer links that might be impressum
            footer_links = soup.find_all('a', href=re.compile(r'impressum|imprint|legal', re.I))
            impressum_links.extend(footer_links)
        
        if not impressum_links:
            issues.append(ComplianceIssue(
                category="Impressum",
                severity="critical",
                title="Kein Impressum gefunden",
                description="Es wurde kein Link zum Impressum gefunden. Dies ist gesetzlich verpflichtend.",
                risk_euro=3000,
                legal_basis="§ 5 TMG (Telemediengesetz)",
                recommendation="Fügen Sie ein vollständiges Impressum mit allen Pflichtangaben hinzu",
                auto_fixable=True
            ))
        else:
            # Check impressum content
            impressum_url = urljoin(base_url, impressum_links[0].get('href', ''))
            impressum_page = await self._fetch_page(impressum_url)
            
            if impressum_page:
                issues.extend(await self._validate_impressum_content(impressum_page['content']))
            else:
                issues.append(ComplianceIssue(
                    category="Impressum", 
                    severity="critical",
                    title="Impressum nicht erreichbar",
                    description="Der Link zum Impressum führt zu einer nicht erreichbaren Seite",
                    risk_euro=2500,
                    legal_basis="§ 5 TMG",
                    recommendation="Stellen Sie sicher, dass das Impressum über einen funktionierenden Link erreichbar ist"
                ))
        
        return issues
    
    async def _validate_impressum_content(self, content: str) -> List[ComplianceIssue]:
        """Validate impressum content for required information"""
        issues = []
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text().lower()
        
        required_elements = {
            "name": r'(name|firma|gesellschaft|unternehmen)',
            "address": r'(straße|str\.|adresse|anschrift)',
            "city": r'(\d{5}\s*[a-zäöüß]+|[a-zäöüß]+\s*\d{5})',
            "contact": r'(telefon|tel\.|e-mail|email|kontakt)',
            "registration": r'(handelsregister|hr[ab]|registergericht|ust-id|umsatzsteuer-identifikationsnummer)'
        }
        
        for element, pattern in required_elements.items():
            if not re.search(pattern, text, re.I):
                issues.append(ComplianceIssue(
                    category="Impressum",
                    severity="warning",
                    title=f"Fehlende Angabe: {element}",
                    description=f"Im Impressum fehlt die Angabe zu: {element}",
                    risk_euro=1500,
                    legal_basis="§ 5 TMG",
                    recommendation=f"Ergänzen Sie die fehlende Angabe zu {element} im Impressum",
                    auto_fixable=True
                ))
        
        return issues
    
    async def _check_privacy_policy(self, base_url: str, soup: BeautifulSoup) -> List[ComplianceIssue]:
        """Check for privacy policy (Datenschutzerklärung) compliance"""
        issues = []
        
        # Look for privacy policy links
        privacy_links = soup.find_all('a', text=re.compile(r'datenschutz|privacy|datenschutzerklärung', re.I))
        
        if not privacy_links:
            footer_links = soup.find_all('a', href=re.compile(r'datenschutz|privacy|dsgvo', re.I))
            privacy_links.extend(footer_links)
        
        if not privacy_links:
            issues.append(ComplianceIssue(
                category="Datenschutz",
                severity="critical", 
                title="Keine Datenschutzerklärung gefunden",
                description="Es wurde keine Datenschutzerklärung gefunden. Dies ist DSGVO-Pflicht.",
                risk_euro=5000,
                legal_basis="Art. 13, 14 DSGVO",
                recommendation="Erstellen Sie eine vollständige Datenschutzerklärung gemäß DSGVO",
                auto_fixable=True
            ))
        else:
            # Check privacy policy content
            privacy_url = urljoin(base_url, privacy_links[0].get('href', ''))
            privacy_page = await self._fetch_page(privacy_url)
            
            if privacy_page:
                issues.extend(await self._validate_privacy_content(privacy_page['content']))
        
        return issues
    
    async def _validate_privacy_content(self, content: str) -> List[ComplianceIssue]:
        """Validate privacy policy content for GDPR compliance"""
        issues = []
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text().lower()
        
        required_gdpr_elements = {
            "controller_info": r'(verantwortlicher|controller|datenverarbeitung)',
            "legal_basis": r'(rechtsgrundlage|legal basis|artikel 6)',
            "data_categories": r'(welche daten|art der daten|kategorien)',
            "retention": r'(speicherdauer|aufbewahrung|löschung)',
            "rights": r'(betroffenenrechte|auskunft|löschung|widerspruch)',
            "dpo": r'(datenschutzbeauftragte|data protection officer|dpo)'
        }
        
        for element, pattern in required_gdpr_elements.items():
            if not re.search(pattern, text, re.I):
                issues.append(ComplianceIssue(
                    category="Datenschutz",
                    severity="warning",
                    title=f"DSGVO-Element fehlt: {element}",
                    description=f"Die Datenschutzerklärung sollte Informationen zu '{element}' enthalten",
                    risk_euro=2000,
                    legal_basis="DSGVO Art. 13, 14",
                    recommendation=f"Ergänzen Sie Informationen zu {element} in der Datenschutzerklärung",
                    auto_fixable=True
                ))
        
        return issues
    
    async def _check_cookie_compliance(self, base_url: str, soup: BeautifulSoup) -> List[ComplianceIssue]:
        """Check for cookie banner and consent compliance"""
        issues = []
        
        # Check for cookie banner
        cookie_banner_selectors = [
            '[class*="cookie"]', '[id*="cookie"]', '[class*="consent"]', 
            '[id*="consent"]', '[class*="gdpr"]', '[id*="gdpr"]'
        ]
        
        has_cookie_banner = False
        for selector in cookie_banner_selectors:
            if soup.select(selector):
                has_cookie_banner = True
                break
        
        if not has_cookie_banner:
            issues.append(ComplianceIssue(
                category="Cookie-Compliance",
                severity="critical",
                title="Kein Cookie-Banner gefunden",
                description="Es wurde kein Cookie-Consent-Banner gefunden",
                risk_euro=4000,
                legal_basis="TTDSG § 25, DSGVO Art. 7",
                recommendation="Implementieren Sie einen DSGVO-konformen Cookie-Banner",
                auto_fixable=True
            ))
        
        # Check for tracking scripts without consent
        tracking_scripts = soup.find_all('script')
        problematic_trackers = []
        
        for script in tracking_scripts:
            src = script.get('src', '')
            content = script.string or ''
            
            # Common tracking services
            if any(tracker in src.lower() or tracker in content.lower() for tracker in 
                   ['google-analytics', 'gtag', 'facebook', 'fbq', 'doubleclick']):
                problematic_trackers.append(script)
        
        if problematic_trackers and not has_cookie_banner:
            issues.append(ComplianceIssue(
                category="Cookie-Compliance",
                severity="critical",
                title="Tracking ohne Einwilligung",
                description=f"{len(problematic_trackers)} Tracking-Skripte ohne Cookie-Consent erkannt",
                risk_euro=3000,
                legal_basis="TTDSG § 25",
                recommendation="Tracking-Skripte nur nach expliziter Nutzereinwilligung laden",
                auto_fixable=True
            ))
        
        return issues
    
    async def _check_accessibility(self, base_url: str, soup: BeautifulSoup) -> List[ComplianceIssue]:
        """Check basic accessibility compliance (WCAG 2.1 AA)"""
        issues = []
        
        # Check for alt attributes on images
        images_without_alt = soup.find_all('img', alt=False)
        if images_without_alt:
            issues.append(ComplianceIssue(
                category="Barrierefreiheit",
                severity="warning",
                title="Bilder ohne Alt-Text",
                description=f"{len(images_without_alt)} Bilder haben keinen Alt-Text für Screenreader",
                risk_euro=1000,
                legal_basis="WCAG 2.1 AA, BITV 2.0",
                recommendation="Fügen Sie beschreibende Alt-Texte für alle Bilder hinzu",
                auto_fixable=True
            ))
        
        # Check for form labels
        inputs_without_labels = soup.find_all('input', {'type': ['text', 'email', 'password']})
        unlabeled_inputs = []
        for inp in inputs_without_labels:
            input_id = inp.get('id')
            aria_label = inp.get('aria-label')
            associated_label = soup.find('label', {'for': input_id}) if input_id else None
            
            if not (aria_label or associated_label):
                unlabeled_inputs.append(inp)
        
        if unlabeled_inputs:
            issues.append(ComplianceIssue(
                category="Barrierefreiheit",
                severity="warning",
                title="Formulare ohne Labels",
                description=f"{len(unlabeled_inputs)} Eingabefelder haben keine beschreibenden Labels",
                risk_euro=800,
                legal_basis="WCAG 2.1 AA",
                recommendation="Fügen Sie Labels oder aria-label für alle Eingabefelder hinzu",
                auto_fixable=True
            ))
        
        # Check color contrast (simplified check)
        if not soup.find_all(attrs={'style': re.compile(r'color\s*:', re.I)}):
            # This is a very basic check - in production, you'd use tools like axe-core
            pass
        
        return issues
    
    async def _check_ssl_security(self, url: str) -> List[ComplianceIssue]:
        """Check SSL/TLS security"""
        issues = []
        
        if not url.startswith('https://'):
            issues.append(ComplianceIssue(
                category="Sicherheit",
                severity="critical",
                title="Keine SSL-Verschlüsselung",
                description="Die Website verwendet keine HTTPS-Verschlüsselung",
                risk_euro=2000,
                legal_basis="DSGVO Art. 32",
                recommendation="Implementieren Sie SSL/TLS-Verschlüsselung (HTTPS)"
            ))
        
        return issues
    
    async def _check_contact_data(self, base_url: str, soup: BeautifulSoup) -> List[ComplianceIssue]:
        """Check for required contact information"""
        issues = []
        
        # This would be expanded with more sophisticated contact data detection
        text = soup.get_text()
        
        # Basic email detection
        if not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            issues.append(ComplianceIssue(
                category="Kontaktdaten",
                severity="warning", 
                title="Keine E-Mail-Adresse gefunden",
                description="Es wurde keine E-Mail-Adresse für Kontaktaufnahme gefunden",
                risk_euro=500,
                legal_basis="TMG § 5",
                recommendation="Fügen Sie eine E-Mail-Adresse für Anfragen hinzu"
            ))
        
        return issues
    
    async def _check_social_media_plugins(self, base_url: str, soup: BeautifulSoup) -> List[ComplianceIssue]:
        """Check for problematic social media plugins"""
        issues = []
        
        # Check for direct Facebook/Twitter embeds without consent
        social_embeds = soup.find_all(['iframe', 'script'], 
                                    src=re.compile(r'(facebook|twitter|youtube|instagram)', re.I))
        
        if social_embeds:
            issues.append(ComplianceIssue(
                category="Social Media",
                severity="warning",
                title="Social Media Plugins ohne Einwilligung",
                description=f"{len(social_embeds)} Social Media Plugins gefunden, die Daten übertragen könnten",
                risk_euro=1500,
                legal_basis="DSGVO Art. 6",
                recommendation="Implementieren Sie Zwei-Klick-Lösung für Social Media Plugins"
            ))
        
        return issues
    
    def _generate_recommendations(self, issues: List[ComplianceIssue]) -> List[str]:
        """Generate prioritized recommendations based on issues found"""
        recommendations = []
        
        # Group by severity
        critical_issues = [i for i in issues if i.severity == "critical"]
        warning_issues = [i for i in issues if i.severity == "warning"]
        
        if critical_issues:
            recommendations.append("🚨 Kritische Probleme sofort beheben:")
            for issue in critical_issues[:3]:  # Top 3 critical
                recommendations.append(f"   • {issue.recommendation}")
        
        if warning_issues:
            recommendations.append("⚠️ Weitere Verbesserungen:")
            for issue in warning_issues[:3]:  # Top 3 warnings
                recommendations.append(f"   • {issue.recommendation}")
        
        return recommendations
    
    def _generate_next_steps(self, issues: List[ComplianceIssue]) -> List[Dict[str, Any]]:
        """Generate actionable next steps"""
        steps = []
        
        auto_fixable_issues = [i for i in issues if i.auto_fixable and i.severity == "critical"]
        
        if auto_fixable_issues:
            steps.append({
                "title": "KI-Automatisierung nutzen",
                "description": "Diese Probleme können automatisch behoben werden",
                "action": "ai_fix",
                "count": len(auto_fixable_issues)
            })
        
        manual_issues = [i for i in issues if not i.auto_fixable]
        if manual_issues:
            steps.append({
                "title": "Experten-Beratung empfohlen", 
                "description": "Diese Probleme erfordern individuelle Beratung",
                "action": "expert_consultation",
                "count": len(manual_issues)
            })
        
        return steps
    
    def _create_error_response(self, url: str, error_message: str) -> Dict[str, Any]:
        """Create error response structure"""
        return {
            "url": url,
            "scan_timestamp": datetime.now(),
            "error": True,
            "error_message": error_message,
            "compliance_score": 0,
            "total_risk_euro": 0,
            "issues": [],
            "recommendations": [f"Fehler beim Scannen: {error_message}"]
        }

# Async context manager usage example:
# async with ComplianceScanner() as scanner:
#     result = await scanner.scan_website("https://example.com")