"""
Real Website Scanner Engine für Complyo
Comprehensive website analysis using Playwright and BeautifulSoup
"""
import asyncio
import aiohttp
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib
from playwright.async_api import async_playwright

class WebsiteScanner:
    """
    Real website scanner that analyzes compliance issues
    """
    
    def __init__(self):
        self.session = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def scan_website(self, url: str) -> Dict[str, Any]:
        """
        Comprehensive website compliance scan
        Returns detailed analysis results
        """
        
        scan_id = hashlib.md5(f"{url}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        try:
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            # Initialize browser for JavaScript analysis
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = await self.context.new_page()
            
            # Load the page
            response = await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            if not response:
                raise Exception("Failed to load page")
            
            # Get page content
            html_content = await self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Perform comprehensive analysis
            analysis_results = {
                "scan_id": scan_id,
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "status_code": response.status,
                "page_size": len(html_content),
                "load_time": await self._measure_load_time(),
            }
            
            # Run all compliance checks
            checks = await asyncio.gather(
                self._check_gdpr_compliance(soup, self.page),
                self._check_impressum_compliance(soup),
                self._check_cookie_compliance(soup, self.page),
                self._check_accessibility_compliance(soup, self.page),
                self._check_ssl_security(url),
                self._check_meta_tags(soup),
                self._analyze_forms(soup),
                self._check_external_resources(soup, url),
                return_exceptions=True
            )
            
            # Combine results
            gdpr_result, impressum_result, cookie_result, accessibility_result, ssl_result, meta_result, forms_result, external_result = checks
            
            # Calculate overall compliance score
            results = [
                gdpr_result if isinstance(gdpr_result, dict) else {"score": 0, "status": "error"},
                impressum_result if isinstance(impressum_result, dict) else {"score": 0, "status": "error"},
                cookie_result if isinstance(cookie_result, dict) else {"score": 0, "status": "error"},
                accessibility_result if isinstance(accessibility_result, dict) else {"score": 0, "status": "error"}
            ]
            
            overall_score = sum([r.get("score", 0) for r in results]) / len(results)
            total_risk = sum([r.get("risk_euro", 0) for r in results])
            
            critical_issues = len([r for r in results if r.get("status") == "fail"])
            warning_issues = len([r for r in results if r.get("status") == "warning"])
            
            analysis_results.update({
                "overall_score": round(overall_score, 1),
                "total_risk_euro": total_risk,
                "critical_issues": critical_issues,
                "warning_issues": warning_issues,
                "total_issues": critical_issues + warning_issues,
                "results": results,
                "technical_analysis": {
                    "ssl": ssl_result if isinstance(ssl_result, dict) else {},
                    "meta_tags": meta_result if isinstance(meta_result, dict) else {},
                    "forms": forms_result if isinstance(forms_result, dict) else {},
                    "external_resources": external_result if isinstance(external_result, dict) else {}
                },
                "recommendations": self._generate_recommendations(results),
                "next_steps": self._generate_next_steps(results)
            })
            
            await playwright.stop()
            return analysis_results
            
        except Exception as e:
            return {
                "scan_id": scan_id,
                "url": url,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
    
    async def _measure_load_time(self) -> float:
        """Measure page load performance"""
        try:
            # Get navigation timing
            timing = await self.page.evaluate("""
                () => {
                    const timing = performance.getEntriesByType('navigation')[0];
                    return {
                        domContentLoaded: timing.domContentLoadedEventEnd - timing.domContentLoadedEventStart,
                        loadComplete: timing.loadEventEnd - timing.loadEventStart,
                        total: timing.loadEventEnd - timing.navigationStart
                    };
                }
            """)
            return timing.get('total', 0) / 1000  # Convert to seconds
        except:
            return 0.0
    
    async def _check_gdpr_compliance(self, soup: BeautifulSoup, page) -> Dict[str, Any]:
        """Check GDPR/DSGVO compliance"""
        
        score = 100
        issues = []
        risk_euro = 0
        
        # Check for privacy policy
        privacy_links = soup.find_all('a', href=True)
        privacy_found = False
        
        privacy_keywords = ['datenschutz', 'privacy', 'data-protection', 'dsgvo', 'gdpr']
        for link in privacy_links:
            if any(keyword in link.get('href', '').lower() or 
                  keyword in link.get_text().lower() 
                  for keyword in privacy_keywords):
                privacy_found = True
                break
        
        if not privacy_found:
            score -= 40
            risk_euro += 5000
            issues.append("Keine Datenschutzerklärung gefunden")
        
        # Check for cookie consent
        cookie_consent = await self._detect_cookie_consent(page, soup)
        if not cookie_consent:
            score -= 30
            risk_euro += 3000
            issues.append("Kein Cookie-Consent-Banner gefunden")
        
        # Check for contact information in privacy context
        contact_info = self._find_contact_information(soup)
        if not contact_info.get('email') and not contact_info.get('address'):
            score -= 20
            risk_euro += 2000
            issues.append("Kontaktinformationen für Datenschutzanfragen fehlen")
        
        # Check for data processing information
        data_processing_info = self._analyze_data_processing_disclosure(soup)
        if not data_processing_info:
            score -= 10
            risk_euro += 1000
            issues.append("Informationen zur Datenverarbeitung unvollständig")
        
        status = "fail" if score < 50 else "warning" if score < 80 else "pass"
        
        return {
            "category": "Datenschutz (DSGVO)",
            "score": max(0, score),
            "status": status,
            "risk_euro": risk_euro,
            "issues": issues,
            "message": f"DSGVO-Compliance: {score}% erfüllt",
            "description": "; ".join(issues) if issues else "DSGVO-Anforderungen größtenteils erfüllt",
            "legal_basis": "Art. 13, 14 DSGVO - Informationspflichten",
            "recommendation": "Vollständige Datenschutzerklärung mit allen Pflichtangaben implementieren",
            "auto_fixable": True
        }
    
    async def _check_impressum_compliance(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check Impressum compliance (TMG)"""
        
        score = 100
        issues = []
        risk_euro = 0
        
        # Look for impressum
        impressum_found = False
        impressum_links = soup.find_all('a', href=True)
        
        for link in impressum_links:
            if 'impressum' in link.get('href', '').lower() or \
               'impressum' in link.get_text().lower():
                impressum_found = True
                break
        
        if not impressum_found:
            score -= 50
            risk_euro += 5000
            issues.append("Kein Impressum gefunden")
        
        # Check for required business information
        contact_info = self._find_contact_information(soup)
        
        if not contact_info.get('company_name'):
            score -= 20
            risk_euro += 2000
            issues.append("Firmenname/Betreiber nicht eindeutig identifizierbar")
        
        if not contact_info.get('address'):
            score -= 20
            risk_euro += 2000
            issues.append("Geschäftsadresse fehlt")
        
        if not contact_info.get('email') and not contact_info.get('phone'):
            score -= 10
            risk_euro += 1000
            issues.append("Kontaktmöglichkeiten unvollständig")
        
        status = "fail" if score < 50 else "warning" if score < 80 else "pass"
        
        return {
            "category": "Impressum",
            "score": max(0, score),
            "status": status,
            "risk_euro": risk_euro,
            "issues": issues,
            "message": f"Impressum: {score}% der Pflichtangaben gefunden",
            "description": "; ".join(issues) if issues else "Impressum-Pflichtangaben vorhanden",
            "legal_basis": "§ 5 TMG - Allgemeine Informationspflichten",
            "recommendation": "Vollständiges Impressum mit allen Pflichtangaben nach § 5 TMG erstellen",
            "auto_fixable": True
        }
    
    async def _check_cookie_compliance(self, soup: BeautifulSoup, page) -> Dict[str, Any]:
        """Check Cookie compliance (TTDSG)"""
        
        score = 100
        issues = []
        risk_euro = 0
        
        # Detect cookies
        try:
            cookies = await page.context.cookies()
            cookie_count = len(cookies)
        except:
            cookie_count = 0
        
        # Check for cookie consent banner
        consent_banner = await self._detect_cookie_consent(page, soup)
        
        if cookie_count > 0 and not consent_banner:
            score -= 50
            risk_euro += 4000
            issues.append("Cookies werden gesetzt ohne Einwilligung")
        
        # Check for tracking scripts
        tracking_scripts = self._detect_tracking_scripts(soup)
        if tracking_scripts and not consent_banner:
            score -= 30
            risk_euro += 3000
            issues.append("Tracking-Scripts ohne Einwilligung aktiv")
        
        # Check for third-party integrations
        third_party = self._detect_third_party_integrations(soup)
        if third_party and not consent_banner:
            score -= 20
            risk_euro += 2000
            issues.append("Drittanbieter-Integrationen ohne Einwilligung")
        
        status = "fail" if score < 50 else "warning" if score < 80 else "pass"
        
        return {
            "category": "Cookie-Compliance",
            "score": max(0, score),
            "status": status,
            "risk_euro": risk_euro,
            "issues": issues,
            "message": f"Cookie-Compliance: {score}% TTDSG-konform",
            "description": "; ".join(issues) if issues else "Cookie-Handling TTDSG-konform",
            "legal_basis": "TTDSG § 25 - Schutz der Privatsphäre bei Endeinrichtungen",
            "recommendation": "TTDSG-konformen Cookie-Banner mit Consent Management implementieren",
            "auto_fixable": True,
            "technical_details": {
                "cookies_found": cookie_count,
                "tracking_scripts": len(tracking_scripts),
                "third_party_integrations": len(third_party)
            }
        }
    
    async def _check_accessibility_compliance(self, soup: BeautifulSoup, page) -> Dict[str, Any]:
        """Check Accessibility compliance (WCAG 2.1 AA)"""
        
        score = 100
        issues = []
        risk_euro = 0
        
        # Check images for alt text
        images = soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt')]
        
        if images_without_alt:
            missing_ratio = len(images_without_alt) / len(images) if images else 0
            score_reduction = int(missing_ratio * 30)
            score -= score_reduction
            risk_euro += score_reduction * 50
            issues.append(f"{len(images_without_alt)} Bilder ohne Alt-Text gefunden")
        
        # Check for proper heading structure
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        h1_count = len(soup.find_all('h1'))
        
        if h1_count == 0:
            score -= 15
            risk_euro += 500
            issues.append("Keine H1-Überschrift gefunden")
        elif h1_count > 1:
            score -= 10
            risk_euro += 300
            issues.append("Mehrere H1-Überschriften gefunden")
        
        # Check form labels
        forms = soup.find_all('form')
        form_inputs = soup.find_all(['input', 'select', 'textarea'])
        inputs_without_labels = []
        
        for input_elem in form_inputs:
            if input_elem.get('type') not in ['hidden', 'submit', 'button']:
                label_found = False
                input_id = input_elem.get('id')
                
                # Check for associated label
                if input_id:
                    label = soup.find('label', {'for': input_id})
                    if label:
                        label_found = True
                
                # Check for aria-label
                if input_elem.get('aria-label'):
                    label_found = True
                
                if not label_found:
                    inputs_without_labels.append(input_elem)
        
        if inputs_without_labels:
            score -= 20
            risk_euro += len(inputs_without_labels) * 200
            issues.append(f"{len(inputs_without_labels)} Formularfelder ohne Labels")
        
        # Check contrast (simplified)
        try:
            contrast_issues = await self._check_color_contrast(page)
            if contrast_issues:
                score -= 10
                risk_euro += 500
                issues.append("Mögliche Kontrastprobleme erkannt")
        except:
            pass
        
        status = "pass" if score >= 80 else "warning" if score >= 60 else "fail"
        
        return {
            "category": "Barrierefreiheit",
            "score": max(0, score),
            "status": status,
            "risk_euro": risk_euro,
            "issues": issues,
            "message": f"Barrierefreiheit: {score}% WCAG 2.1 AA konform",
            "description": "; ".join(issues) if issues else "Barrierefreiheits-Standards größtenteils erfüllt",
            "legal_basis": "WCAG 2.1 AA, BITV 2.0",
            "recommendation": "Alt-Texte, Labels und Überschriftenstruktur optimieren",
            "auto_fixable": True,
            "technical_details": {
                "total_images": len(images),
                "images_without_alt": len(images_without_alt),
                "total_headings": len(headings),
                "h1_count": h1_count,
                "form_inputs": len(form_inputs),
                "inputs_without_labels": len(inputs_without_labels)
            }
        }
    
    async def _check_ssl_security(self, url: str) -> Dict[str, Any]:
        """Check SSL/TLS security"""
        
        try:
            parsed = urlparse(url)
            is_https = parsed.scheme == 'https'
            
            return {
                "https_enabled": is_https,
                "security_score": 100 if is_https else 0,
                "recommendation": "HTTPS verwenden" if not is_https else "SSL/TLS korrekt konfiguriert"
            }
        except:
            return {"https_enabled": False, "security_score": 0}
    
    async def _check_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze meta tags"""
        
        meta_tags = {}
        
        # Title
        title = soup.find('title')
        meta_tags['title'] = title.get_text().strip() if title else None
        
        # Description
        description = soup.find('meta', attrs={'name': 'description'})
        meta_tags['description'] = description.get('content') if description else None
        
        # Viewport
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        meta_tags['viewport'] = viewport.get('content') if viewport else None
        
        # Language
        html_tag = soup.find('html')
        meta_tags['language'] = html_tag.get('lang') if html_tag else None
        
        return meta_tags
    
    async def _analyze_forms(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze forms for compliance issues"""
        
        forms = soup.find_all('form')
        form_analysis = {
            "total_forms": len(forms),
            "forms_with_ssl": 0,
            "forms_with_privacy": 0,
            "contact_forms": 0
        }
        
        for form in forms:
            # Check if form action uses HTTPS
            action = form.get('action', '')
            if action.startswith('https://') or not action:
                form_analysis["forms_with_ssl"] += 1
            
            # Look for privacy-related checkboxes or notices
            privacy_elements = form.find_all(text=re.compile(r'datenschutz|privacy|dsgvo', re.I))
            if privacy_elements:
                form_analysis["forms_with_privacy"] += 1
            
            # Detect contact forms
            if any(input_elem.get('type') in ['email'] or 
                  'email' in input_elem.get('name', '').lower() or
                  'mail' in input_elem.get('name', '').lower()
                  for input_elem in form.find_all('input')):
                form_analysis["contact_forms"] += 1
        
        return form_analysis
    
    async def _check_external_resources(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Check external resources and third-party integrations"""
        
        external_resources = {
            "external_scripts": [],
            "external_stylesheets": [],
            "external_images": [],
            "tracking_domains": set(),
            "social_media": set()
        }
        
        # Scripts
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            src = script.get('src')
            if src and not self._is_same_domain(src, base_url):
                external_resources["external_scripts"].append(src)
                domain = urlparse(src).netloc
                if self._is_tracking_domain(domain):
                    external_resources["tracking_domains"].add(domain)
        
        # Stylesheets
        links = soup.find_all('link', rel='stylesheet', href=True)
        for link in links:
            href = link.get('href')
            if href and not self._is_same_domain(href, base_url):
                external_resources["external_stylesheets"].append(href)
        
        # Images
        images = soup.find_all('img', src=True)
        for img in images:
            src = img.get('src')
            if src and not self._is_same_domain(src, base_url):
                external_resources["external_images"].append(src)
        
        # Convert sets to lists for JSON serialization
        external_resources["tracking_domains"] = list(external_resources["tracking_domains"])
        external_resources["social_media"] = list(external_resources["social_media"])
        
        return external_resources
    
    # Helper methods
    
    def _is_same_domain(self, url: str, base_url: str) -> bool:
        """Check if URL is from the same domain"""
        try:
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                return True
            elif not url.startswith(('http://', 'https://')):
                return True
            
            base_domain = urlparse(base_url).netloc
            url_domain = urlparse(url).netloc
            
            return base_domain == url_domain
        except:
            return True
    
    def _is_tracking_domain(self, domain: str) -> bool:
        """Check if domain is known for tracking"""
        tracking_domains = [
            'google-analytics.com', 'googletagmanager.com', 'facebook.com',
            'doubleclick.net', 'googlesyndication.com', 'youtube.com',
            'twitter.com', 'linkedin.com', 'instagram.com'
        ]
        return any(track_domain in domain for track_domain in tracking_domains)
    
    async def _detect_cookie_consent(self, page, soup: BeautifulSoup) -> bool:
        """Detect cookie consent banner"""
        
        # Check HTML for cookie-related text
        consent_keywords = [
            'cookie', 'datenschutz', 'privacy', 'einwilligung', 'consent',
            'akzeptieren', 'accept', 'zustimmen', 'agree'
        ]
        
        text_content = soup.get_text().lower()
        has_cookie_text = any(keyword in text_content for keyword in consent_keywords)
        
        if not has_cookie_text:
            return False
        
        # Check for interactive elements (buttons, forms)
        buttons = soup.find_all(['button', 'input'])
        cookie_buttons = []
        
        for button in buttons:
            button_text = button.get_text().lower() + str(button.get('value', '')).lower()
            if any(keyword in button_text for keyword in consent_keywords):
                cookie_buttons.append(button)
        
        return len(cookie_buttons) > 0
    
    def _detect_tracking_scripts(self, soup: BeautifulSoup) -> List[str]:
        """Detect tracking scripts"""
        
        tracking_scripts = []
        scripts = soup.find_all('script')
        
        tracking_patterns = [
            r'google-analytics\.com',
            r'googletagmanager\.com',
            r'facebook\.net',
            r'doubleclick\.net',
            r'googlesyndication\.com'
        ]
        
        for script in scripts:
            src = script.get('src', '')
            content = script.get_text()
            
            for pattern in tracking_patterns:
                if re.search(pattern, src + content, re.I):
                    tracking_scripts.append(src or 'inline')
                    break
        
        return tracking_scripts
    
    def _detect_third_party_integrations(self, soup: BeautifulSoup) -> List[str]:
        """Detect third-party integrations"""
        
        integrations = []
        
        # Common third-party services
        patterns = {
            'Google Maps': r'maps\.google\.|googleapis\.com',
            'YouTube': r'youtube\.com|youtu\.be',
            'Facebook': r'facebook\.com|fb\.com',
            'Twitter': r'twitter\.com|t\.co',
            'Instagram': r'instagram\.com',
            'LinkedIn': r'linkedin\.com'
        }
        
        all_content = str(soup)
        
        for service, pattern in patterns.items():
            if re.search(pattern, all_content, re.I):
                integrations.append(service)
        
        return integrations
    
    def _find_contact_information(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Extract contact information"""
        
        text_content = soup.get_text()
        
        # Email pattern
        email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
        emails = re.findall(email_pattern, text_content)
        
        # Phone pattern (German)
        phone_pattern = r'\\b(?:\\+49|0)[\\d\\s\\-\\/\\(\\)]{8,}\\b'
        phones = re.findall(phone_pattern, text_content)
        
        # Address pattern (simplified)
        address_pattern = r'\\d{5}\\s+[A-ZÄÖÜ][a-zäöüß]+(?:\\s+[A-ZÄÖÜ][a-zäöüß]+)*'
        addresses = re.findall(address_pattern, text_content)
        
        # Company name (look for GmbH, AG, etc.)
        company_pattern = r'[A-ZÄÖÜ][a-zäöüß\\s]+(?:GmbH|AG|UG|e\\.V\\.|KG|OHG)'
        companies = re.findall(company_pattern, text_content)
        
        return {
            'email': emails[0] if emails else None,
            'phone': phones[0] if phones else None,
            'address': addresses[0] if addresses else None,
            'company_name': companies[0] if companies else None
        }
    
    def _analyze_data_processing_disclosure(self, soup: BeautifulSoup) -> bool:
        """Check for data processing information disclosure"""
        
        text_content = soup.get_text().lower()
        
        # Look for GDPR-related terms
        gdpr_terms = [
            'datenverarbeitung', 'data processing', 'rechtsgrundlage',
            'legal basis', 'betroffenenrechte', 'data subject rights',
            'widerruf', 'withdrawal', 'löschung', 'deletion'
        ]
        
        return any(term in text_content for term in gdpr_terms)
    
    async def _check_color_contrast(self, page) -> List[str]:
        """Basic color contrast check"""
        
        try:
            # This is a simplified check - in production, use specialized tools
            contrast_issues = await page.evaluate("""
                () => {
                    const issues = [];
                    const elements = document.querySelectorAll('*');
                    
                    for (let i = 0; i < Math.min(elements.length, 50); i++) {
                        const element = elements[i];
                        const style = window.getComputedStyle(element);
                        const color = style.color;
                        const backgroundColor = style.backgroundColor;
                        
                        // Simple heuristic: if both are very light or very dark, potential issue
                        if (color && backgroundColor) {
                            if ((color.includes('rgb(255') && backgroundColor.includes('rgb(255')) ||
                                (color.includes('rgb(0') && backgroundColor.includes('rgb(0'))) {
                                issues.push('Potential contrast issue detected');
                                break;
                            }
                        }
                    }
                    
                    return issues;
                }
            """)
            return contrast_issues
        except:
            return []
    
    def _generate_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        for result in results:
            if result.get("status") == "fail":
                recommendations.append(f"🚨 {result.get('category')}: {result.get('recommendation', 'Sofortige Maßnahmen erforderlich')}")
            elif result.get("status") == "warning":
                recommendations.append(f"⚠️ {result.get('category')}: {result.get('recommendation', 'Verbesserungen empfohlen')}")
        
        if not recommendations:
            recommendations.append("✅ Alle Compliance-Bereiche erfüllen die grundlegenden Anforderungen")
        
        return recommendations
    
    def _generate_next_steps(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Generate next steps based on analysis"""
        
        next_steps = []
        
        # Count fixable issues
        auto_fixable_count = sum(1 for r in results if r.get("auto_fixable", False) and r.get("status") in ["fail", "warning"])
        
        if auto_fixable_count > 0:
            next_steps.append({
                "title": "KI-Automatisierung nutzen",
                "description": f"Automatische Fixes für {auto_fixable_count} erkannte Probleme",
                "action": "ai_fix",
                "count": auto_fixable_count,
                "priority": "high"
            })
        
        # Check for critical issues
        critical_count = sum(1 for r in results if r.get("status") == "fail")
        if critical_count > 0:
            next_steps.append({
                "title": "Expert Service beauftragen",
                "description": f"Professionelle Beratung für {critical_count} kritische Compliance-Probleme",
                "action": "expert_service",
                "count": critical_count,
                "priority": "critical"
            })
        
        # Add monitoring if score is good
        overall_score = sum(r.get("score", 0) for r in results) / len(results) if results else 0
        if overall_score >= 70:
            next_steps.append({
                "title": "24/7 Monitoring aktivieren",
                "description": "Kontinuierliche Überwachung für dauerhafte Compliance",
                "action": "monitoring",
                "count": 1,
                "priority": "medium"
            })
        
        return next_steps


# Global scanner instance for reuse
website_scanner = WebsiteScanner()