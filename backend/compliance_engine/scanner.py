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
import logging

logger = logging.getLogger(__name__)

# Import modulare Checks
from compliance_engine.checks import (
    check_impressum_compliance,
    check_impressum_compliance_smart,
    check_datenschutz_compliance,
    check_datenschutz_compliance_smart,
    check_cookie_compliance,
    check_barrierefreiheit_compliance,
    check_barrierefreiheit_compliance_smart
)

# Import Legal Update Integration
from compliance_engine.legal_update_integration import legal_update_integration

# Import Issue Grouper
from compliance_engine.issue_grouper import IssueGrouper

# Import TCF 2.2 Support
try:
    from compliance_engine.checks.tcf_check import check_tcf_compliance
    from compliance_engine.tcf_vendor_analyzer import tcf_vendor_analyzer
    TCF_AVAILABLE = True
except ImportError:
    TCF_AVAILABLE = False
    logger.warning("⚠️ TCF 2.2 module not available")

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
    is_missing: bool = False  # True wenn komplettes Hauptelement fehlt
    screenshot_url: Optional[str] = None  # Screenshot des problematischen Elements
    element_html: Optional[str] = None  # HTML des Elements
    fix_code: Optional[str] = None  # Vorgeschlagener Fix-Code
    suggested_alt: Optional[str] = None  # AI-generierter Alt-Text
    image_src: Optional[str] = None  # Bild-URL
    metadata: Dict = None  # Zusätzliche Metadaten
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

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
            
            # Run all compliance checks (using modular check system)
            # Barrierefreiheit (BFSG) - Höchste Priorität
            # ✨ NEU: Nutzt Browser-Rendering für moderne JS-Websites
            barriere_issues = await check_barrierefreiheit_compliance_smart(
                url, 
                html=main_page['content'], 
                session=self.session
            )
            
            # ✅ NEU: Prüfe ob Accessibility-Widget gefunden wurde
            has_accessibility_widget = not any(
                issue.get('title') == 'Kein Barrierefreiheits-Tool/Widget gefunden' 
                for issue in barriere_issues
            )
            
            for issue_dict in barriere_issues:
                issues.append(ComplianceIssue(**issue_dict))
            
            # Impressum (TMG) - mit Browser-Rendering für JS-Seiten
            impressum_issues = await check_impressum_compliance_smart(
                url,
                html=main_page['content'],
                session=self.session
            )
            for issue_dict in impressum_issues:
                issues.append(ComplianceIssue(**issue_dict))
            
            # Datenschutz (DSGVO) - mit Browser-Rendering für JS-Seiten
            datenschutz_issues = await check_datenschutz_compliance_smart(
                url,
                html=main_page['content'],
                session=self.session
            )
            for issue_dict in datenschutz_issues:
                issues.append(ComplianceIssue(**issue_dict))
            
            # Cookie-Compliance (TTDSG) - inkludiert TCF 2.2 Check
            cookie_issues = await check_cookie_compliance(url, soup, self.session)
            for issue_dict in cookie_issues:
                issues.append(ComplianceIssue(**issue_dict))
            
            # ✅ TCF 2.2: Vendor Analysis (optional, additional data)
            tcf_data = {}
            if TCF_AVAILABLE:
                try:
                    tcf_data = await check_tcf_compliance(url, soup, main_page['content'])
                    
                    # Vendor Detection
                    detected_vendors = await tcf_vendor_analyzer.analyze_vendors_on_page(soup, main_page['content'])
                    tcf_data["detected_vendors"] = detected_vendors
                    tcf_data["vendor_count"] = len(detected_vendors)
                    
                    logger.info(f"✅ TCF 2.2 Check completed: {tcf_data.get('cmp_name', 'No CMP')}, {len(detected_vendors)} vendors")
                except Exception as e:
                    logger.warning(f"⚠️ TCF analysis failed: {e}")
                    tcf_data = {"has_tcf": False, "error": str(e)}
            
            # Legacy checks (still useful)
            issues.extend(await self._check_ssl_security(url))
            issues.extend(await self._check_contact_data(url, soup))
            issues.extend(await self._check_social_media_plugins(url, soup))
            
            # ✅ HYBRIDANSATZ: Anreicherung mit eRecht24-Beschreibungen
            issues = await self._enrich_with_erecht24_descriptions(issues)
            
            # Calculate overall compliance score and risk
            total_risk_euro = sum(issue.risk_euro for issue in issues)
            critical_issues = len([i for i in issues if i.severity == "critical"])
            warning_issues = len([i for i in issues if i.severity == "warning"])
            
            # Score calculation (0-100)
            max_possible_issues = 15  # Rough estimate of maximum issues
            compliance_score = max(0, 100 - (critical_issues * 20 + warning_issues * 5))
            
            # ✅ TCF 2.2 Bonus: +5 Punkte für vollständige TCF Implementation
            if tcf_data.get("has_tcf") and tcf_data.get("tc_string_found") and len(tcf_data.get("issues", [])) == 0:
                compliance_score = min(100, compliance_score + 5)
                logger.info(f"✅ TCF 2.2 Bonus: +5 points (TCF fully compliant)")
            
            # End timing
            end_time = datetime.now()
            scan_duration = int((end_time - start_time).total_seconds() * 1000)
            
            scan_results = {
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
                "next_steps": self._generate_next_steps(issues),
                "has_accessibility_widget": has_accessibility_widget,  # ✅ Widget-Status
                "tcf_data": tcf_data  # ✅ NEU: TCF 2.2 Data
            }
            
            # 🆕 LEGAL UPDATE INTEGRATION: Anwendung aktueller Gesetzesänderungen
            if legal_update_integration:
                try:
                    # Lade aktive Legal Updates
                    await legal_update_integration.get_active_legal_updates()
                    # Wende Updates auf Scan-Ergebnisse an
                    scan_results = legal_update_integration.apply_updates_to_scan_results(scan_results)
                    logger.info(f"✅ Legal Updates auf Scan angewendet")
                except Exception as e:
                    logger.warning(f"⚠️ Legal Update Integration fehlgeschlagen: {e}")
            
            # 🆕 ISSUE GROUPING: Intelligente Gruppierung für bessere UX
            try:
                grouper = IssueGrouper()
                scan_results = grouper.enrich_scan_results(scan_results)
                logger.info(f"✅ Issue-Gruppierung abgeschlossen: {scan_results.get('grouping_stats', {}).get('total_groups', 0)} Gruppen, {scan_results.get('grouping_stats', {}).get('grouping_rate', 0):.1f}% gruppiert")
            except Exception as e:
                logger.error(f"❌ Issue-Gruppierung fehlgeschlagen: {e}", exc_info=True)
            
            return scan_results
            
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
        inputs_without_labels = soup.find_all('input', {'type': ['text', 'email', 'password', 'tel', 'url', 'search', 'number']})
        unlabeled_inputs = []
        for inp in inputs_without_labels:
            input_id = inp.get('id')
            aria_label = inp.get('aria-label')
            aria_labelledby = inp.get('aria-labelledby')
            title = inp.get('title')
            placeholder = inp.get('placeholder')
            associated_label = soup.find('label', {'for': input_id}) if input_id else None
            
            if not (aria_label or aria_labelledby or title or placeholder or associated_label):
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
    
    async def _enrich_with_erecht24_descriptions(self, issues: List[ComplianceIssue]) -> List[ComplianceIssue]:
        """
        Hybridansatz: Anreicherung der technisch erkannten Issues mit eRecht24-Beschreibungen
        
        STRATEGIE:
        - Unsere Scanner: ERKENNEN technisch die Probleme
        - eRecht24-API: LIEFERT rechtssichere Beschreibungen & Empfehlungen
        
        Vorteile:
        - Keine Dopplung/Inkonsistenzen
        - Rechtlich abgesichert durch eRecht24
        - Technisch präzise durch unsere Scanner
        """
        try:
            from erecht24_service import erecht24_service
            
            enriched_issues = []
            
            for issue in issues:
                try:
                    # Hole rechtssichere Beschreibung von eRecht24
                    erecht_data = await erecht24_service.get_compliance_description(issue.category)
                    
                    if erecht_data and 'description' in erecht_data:
                        # Bundle: Technische Erkennung + rechtliche Beschreibung
                        enriched_issue = ComplianceIssue(
                            category=issue.category,
                            severity=issue.severity,
                            title=issue.title,  # Unser technischer Titel
                            description=erecht_data['description'],  # eRecht24-Beschreibung
                            risk_euro=issue.risk_euro,  # Unsere Risikoeinschätzung
                            recommendation=erecht_data['recommendation'],  # eRecht24-Empfehlung
                            legal_basis=erecht_data['legal_basis'],  # eRecht24-Rechtsgrundlage
                            auto_fixable=issue.auto_fixable,  # Unsere technische Einschätzung
                            is_missing=issue.is_missing  # ✅ WICHTIG: is_missing beibehalten!
                        )
                        enriched_issues.append(enriched_issue)
                    else:
                        # Fallback: Original Issue wenn eRecht24 nicht verfügbar
                        enriched_issues.append(issue)
                        
                except Exception as e:
                    # Bei Fehler: Original Issue behalten
                    print(f"⚠️ eRecht24 enrichment failed for {issue.category}: {e}")
                    enriched_issues.append(issue)
            
            return enriched_issues
            
        except ImportError:
            # eRecht24-Service nicht verfügbar: Original Issues zurückgeben

            return issues
        except Exception as e:
            print(f"⚠️ Fehler bei eRecht24-Anreicherung: {e}")
            return issues
    
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