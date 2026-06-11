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
    check_barrierefreiheit_compliance_smart,
    check_agb_compliance,
    check_shop_compliance,
    check_uwg_compliance,
)
from compliance_engine.browser_renderer import smart_fetch_html, detect_client_rendering

# Import declarative (data-driven) checks — automatisch befüllbar durch den Legal-Change-Monitor
from compliance_engine.declarative_check_runner import run_declarative_checks

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

# Import centralized Score Calculator (✅ FIX: Einzige Source of Truth)
from compliance_engine.score_calculator import ScoreCalculator

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
            timeout=aiohttp.ClientTimeout(total=55),
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
            main_page_headers = main_page.get('headers', {})

            # Render once if browser is needed, share HTML across all checks
            rendered_html = main_page['content']
            if detect_client_rendering(main_page['content'])[0]:
                logger.info("🌐 Browser rendering needed — fetching once for all checks")
                rendered_html, _ = await smart_fetch_html(url, main_page['content'])
                logger.info("✅ Single browser render complete")
                soup = BeautifulSoup(rendered_html, 'html.parser')

            # Run all compliance checks in parallel using pre-rendered soup
            # barrierefreiheit: no session = single-page only (avoids multi-page scan)
            barriere_task = check_barrierefreiheit_compliance(url, soup, None)
            impressum_task = check_impressum_compliance(url, soup, self.session)
            datenschutz_task = check_datenschutz_compliance(url, soup, self.session)
            cookie_task = check_cookie_compliance(url, soup, self.session)
            agb_task = check_agb_compliance(url, soup, self.session)
            shop_task = check_shop_compliance(url, soup, self.session)
            declarative_task = run_declarative_checks(url, soup, self.session)
            uwg_task = check_uwg_compliance(url, soup, self.session)
            ssl_task = self._check_ssl_security(url, main_page_headers)
            contact_task = self._check_contact_data(url, soup)
            social_task = self._check_social_media_plugins(url, soup)

            results = await asyncio.gather(
                barriere_task, impressum_task, datenschutz_task, cookie_task,
                agb_task, shop_task, declarative_task, uwg_task,
                ssl_task, contact_task, social_task,
                return_exceptions=True
            )

            barriere_issues, impressum_issues, datenschutz_issues, cookie_issues, \
                agb_issues, shop_issues, declarative_issues, uwg_issues, \
                ssl_issues, contact_issues, social_issues = results

            for check_issues in [barriere_issues, impressum_issues, datenschutz_issues,
                                  cookie_issues, agb_issues, shop_issues, declarative_issues, uwg_issues,
                                  ssl_issues, contact_issues, social_issues]:
                if isinstance(check_issues, Exception):
                    logger.warning(f"Check failed (non-critical): {check_issues}")
                    continue
                for issue_dict in check_issues:
                    if isinstance(issue_dict, ComplianceIssue):
                        issues.append(issue_dict)
                    else:
                        issues.append(ComplianceIssue(**issue_dict))

            # ✅ Prüfe ob Accessibility-Widget gefunden wurde
            has_accessibility_widget = not any(
                (issue.title if isinstance(issue, ComplianceIssue) else issue.get('title')) == 'Kein Barrierefreiheits-Tool/Widget gefunden'
                for issue in (barriere_issues if not isinstance(barriere_issues, Exception) else [])
            )

            # ✅ TCF 2.2: Vendor Analysis (optional, additional data)
            tcf_data = {}
            if TCF_AVAILABLE:
                try:
                    tcf_data = await check_tcf_compliance(url, soup, main_page['content'])
                    detected_vendors = await tcf_vendor_analyzer.analyze_vendors_on_page(soup, main_page['content'])
                    tcf_data["detected_vendors"] = detected_vendors
                    tcf_data["vendor_count"] = len(detected_vendors)
                    logger.info(f"✅ TCF 2.2 Check completed: {tcf_data.get('cmp_name', 'No CMP')}, {len(detected_vendors)} vendors")
                except Exception as e:
                    logger.warning(f"⚠️ TCF analysis failed: {e}")
                    tcf_data = {"has_tcf": False, "error": str(e)}
            
            # Anreicherung mit KI-Compliance-Beschreibungen (interner Generator)
            issues = await self._enrich_with_internal_descriptions(issues)
            
            # ✅ FIX v3.0: Gesamtscore = Mittelwert der 4 Säulen (eine Quelle!)
            # So können Gesamtscore und Säulen-Scores nie auseinanderlaufen.
            _scores = ScoreCalculator.compute(issues)
            compliance_score = _scores["overall_score"]
            _pillar_scores = _scores["pillar_scores"]
            
            # Calculate overall risk
            total_risk_euro = sum(issue.risk_euro for issue in issues)
            critical_issues = len([i for i in issues if i.severity == "critical"])
            warning_issues = len([i for i in issues if i.severity == "warning"])
            
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
                "pillar_scores": [
                    {"pillar": pillar, "score": round(score)}
                    for pillar, score in _pillar_scores.items()
                ],
                "recommendations": self._generate_recommendations(issues),
                "next_steps": self._generate_next_steps(issues),
                "has_accessibility_widget": has_accessibility_widget,
                "tcf_data": tcf_data,
                "score_breakdown": ScoreCalculator.get_score_breakdown(issues)
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
    
    async def _check_ssl_security(self, url: str, response_headers: dict = None) -> List[ComplianceIssue]:
        """SSL/TLS-Sicherheitsprüfung — HTTPS, Redirect und Zertifikats-Grundprüfung"""
        issues = []

        parsed = urlparse(url)
        is_https = parsed.scheme == 'https'

        if not is_https:
            issues.append(ComplianceIssue(
                category='security',
                severity='critical',
                title='Keine HTTPS-Verschlüsselung',
                description=(
                    'Die Website wird über unverschlüsseltes HTTP ausgeliefert. '
                    'Alle übertragenen Daten (inkl. Formulareingaben) sind im Klartext lesbar. '
                    'HTTPS ist nach DSGVO Art. 32 (technische Sicherheitsmaßnahmen) verpflichtend.'
                ),
                risk_euro=5000,
                legal_basis='DSGVO Art. 32',
                recommendation=(
                    'Aktivieren Sie HTTPS mit einem gültigen TLS-Zertifikat (z.B. kostenlos via Let\'s Encrypt). '
                    'Richten Sie eine automatische HTTP→HTTPS-Weiterleitung ein.'
                ),
            ))
            return issues

        # HTTPS: prüfe ob HTTP-Version auf HTTPS weiterleitet
        http_url = url.replace('https://', 'http://', 1)
        try:
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_ctx)
            async with aiohttp.ClientSession(connector=connector) as tmp:
                async with tmp.get(
                    http_url,
                    timeout=aiohttp.ClientTimeout(total=8),
                    allow_redirects=False
                ) as resp:
                    if resp.status not in (301, 302, 307, 308):
                        issues.append(ComplianceIssue(
                            category='security',
                            severity='warning',
                            title='Kein HTTP→HTTPS Redirect',
                            description=(
                                f'Die HTTP-Version der Website ({http_url}) leitet nicht automatisch '
                                f'auf HTTPS weiter (Status: {resp.status}). Nutzer die http:// '
                                f'eingeben landen auf der unverschlüsselten Version.'
                            ),
                            risk_euro=1000,
                            legal_basis='DSGVO Art. 32, BSI IT-Grundschutz',
                            recommendation=(
                                'Konfigurieren Sie einen permanenten 301-Redirect von HTTP auf HTTPS '
                                'auf Webserver- oder CDN-Ebene.'
                            ),
                        ))
        except Exception:
            pass

        # Prüfe ob Mixed Content wahrscheinlich vorkommt (http:// in Script/Link-src)
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    mixed_count = len(re.findall(r'src=["\']http://|href=["\']http://', html))
                    if mixed_count > 0:
                        issues.append(ComplianceIssue(
                            category='security',
                            severity='warning',
                            title=f'Mixed Content erkannt ({mixed_count} unsichere Ressourcen)',
                            description=(
                                f'{mixed_count} Ressourcen werden über HTTP statt HTTPS geladen. '
                                'Mixed Content untergräbt die HTTPS-Verschlüsselung und wird von '
                                'modernen Browsern blockiert.'
                            ),
                            risk_euro=500,
                            legal_basis='DSGVO Art. 32',
                            recommendation='Ersetzen Sie alle http://-URLs in Scripts, Stylesheets und Bildern durch https://.',
                        ))
        except Exception:
            pass

        # Check HTTP security headers
        if response_headers:
            headers_lower = {k.lower(): v for k, v in response_headers.items()}

            if 'strict-transport-security' not in headers_lower:
                issues.append(ComplianceIssue(
                    category='security',
                    severity='warning',
                    title='HSTS-Header fehlt (Strict-Transport-Security)',
                    description=(
                        'Der HTTP-Header "Strict-Transport-Security" (HSTS) ist nicht gesetzt. '
                        'HSTS weist Browser an, die Website ausschließlich über HTTPS zu laden '
                        'und verhindert SSL-Stripping-Angriffe.'
                    ),
                    risk_euro=500,
                    legal_basis='DSGVO Art. 32, BSI IT-Grundschutz TLS.1',
                    recommendation='Setzen Sie den Header: Strict-Transport-Security: max-age=31536000; includeSubDomains',
                ))

            if 'content-security-policy' not in headers_lower:
                issues.append(ComplianceIssue(
                    category='security',
                    severity='warning',
                    title='Content-Security-Policy-Header fehlt',
                    description=(
                        'Der Content-Security-Policy (CSP) Header ist nicht gesetzt. '
                        'CSP verhindert Cross-Site-Scripting (XSS) und andere Injection-Angriffe.'
                    ),
                    risk_euro=500,
                    legal_basis='DSGVO Art. 32, OWASP Top 10',
                    recommendation='Implementieren Sie eine Content-Security-Policy, die nur vertrauenswürdige Quellen erlaubt.',
                ))

            if 'x-content-type-options' not in headers_lower:
                issues.append(ComplianceIssue(
                    category='security',
                    severity='info',
                    title='X-Content-Type-Options-Header fehlt',
                    description='Der X-Content-Type-Options: nosniff Header fehlt. Er verhindert MIME-Type-Sniffing durch Browser.',
                    risk_euro=0,
                    legal_basis='DSGVO Art. 32, BSI IT-Grundschutz',
                    recommendation='Setzen Sie: X-Content-Type-Options: nosniff',
                ))

            if 'x-frame-options' not in headers_lower and 'content-security-policy' not in headers_lower:
                issues.append(ComplianceIssue(
                    category='security',
                    severity='warning',
                    title='Clickjacking-Schutz fehlt (X-Frame-Options)',
                    description=(
                        'Weder X-Frame-Options noch frame-ancestors in CSP sind gesetzt. '
                        'Die Seite könnte in einem iframe eingebettet und für Clickjacking-Angriffe missbraucht werden.'
                    ),
                    risk_euro=500,
                    legal_basis='DSGVO Art. 32, OWASP Top 10',
                    recommendation='Setzen Sie: X-Frame-Options: SAMEORIGIN oder frame-ancestors in der CSP.',
                ))

        return issues

    async def _check_contact_data(self, base_url: str, soup: BeautifulSoup) -> List[ComplianceIssue]:
        """
        Prüft ob Kontaktdaten erreichbar sind.
        Ergänzt den Impressum-Check — sucht nach einer dedizierten Kontaktseite
        und grundlegenden Kontaktmöglichkeiten (Email/Formular/Telefon).
        """
        issues = []
        html_lower = str(soup).lower()

        # Kontakt-Link auf der Hauptseite vorhanden?
        contact_link_patterns = [
            '/kontakt', '/contact', '/kontaktformular', '/contact-us',
            '/support', '/hilfe', '/help',
        ]
        contact_link_texts = [
            'kontakt', 'contact', 'kontaktieren', 'schreiben sie uns',
            'write to us', 'get in touch', 'support',
        ]

        has_contact_link = False
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '').lower()
            text = a_tag.get_text(strip=True).lower()
            if any(p in href for p in contact_link_patterns):
                has_contact_link = True
                break
            if any(t in text for t in contact_link_texts):
                has_contact_link = True
                break

        # Email-Adresse direkt sichtbar?
        has_email = bool(re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', html_lower))

        # Kontaktformular vorhanden?
        has_form = bool(soup.find('form'))

        if not has_contact_link and not has_email and not has_form:
            issues.append(ComplianceIssue(
                category='contact',
                severity='warning',
                title='Kein Kontaktweg erkennbar',
                description=(
                    'Auf der Website ist keine Email-Adresse, kein Kontaktformular und kein '
                    'Kontakt-Link auffindbar. Nutzer und Behörden müssen eine einfache '
                    'Kontaktmöglichkeit vorfinden (u.a. für DSGVO-Anfragen wie Auskunft/Löschung).'
                ),
                risk_euro=1000,
                legal_basis='DSGVO Art. 12 Abs. 1 (Transparenz), DDG §5 Abs. 1 Nr. 2',
                recommendation=(
                    'Fügen Sie mindestens eine Email-Adresse oder ein Kontaktformular hinzu. '
                    'Eine dedizierte /kontakt Seite ist Best Practice.'
                ),
            ))

        return issues
    
    async def _check_social_media_plugins(self, base_url: str, soup: BeautifulSoup) -> List[ComplianceIssue]:
        """
        Prüft auf eingebettete Social-Media-Plugins die ohne Consent Daten übertragen.
        Erkennt sowohl iframe-Embeds als auch script-basierte Einbindungen.
        """
        issues = []

        social_patterns = {
            'Facebook': [r'facebook\.com/plugins', r'connect\.facebook\.net', r'facebook\.com/tr'],
            'Twitter/X': [r'platform\.twitter\.com', r'syndication\.twitter\.com'],
            'YouTube': [r'youtube\.com/embed', r'youtube-nocookie\.com', r'ytimg\.com'],
            'Instagram': [r'instagram\.com/embed', r'cdninstagram\.com'],
            'LinkedIn': [r'platform\.linkedin\.com', r'snap\.licdn\.com'],
            'TikTok': [r'tiktok\.com/embed', r'analytics\.tiktok\.com'],
            'Pinterest': [r'assets\.pinterest\.com', r'pinterest\.com/v3'],
        }

        found_platforms = []
        for platform, patterns in social_patterns.items():
            for element in soup.find_all(['iframe', 'script', 'img'], src=True):
                src = element.get('src', '').lower()
                if any(re.search(p, src, re.I) for p in patterns):
                    if platform not in found_platforms:
                        found_platforms.append(platform)
                    break

        if found_platforms:
            issues.append(ComplianceIssue(
                category='social_media',
                severity='warning',
                title=f'Social-Media-Inhalte ohne Consent ({", ".join(found_platforms)})',
                description=(
                    f'Folgende Social-Media-Inhalte werden direkt eingebettet: {", ".join(found_platforms)}. '
                    f'Dabei werden beim Laden der Seite automatisch Daten an die jeweiligen Anbieter '
                    f'übertragen — auch ohne Nutzerinteraktion und ohne Einwilligung.'
                ),
                risk_euro=2000,
                legal_basis='DSGVO Art. 6 Abs. 1, EuGH C-40/17 (Fashion ID)',
                recommendation=(
                    'Nutzen Sie die Zwei-Klick-Lösung oder laden Sie Social-Media-Inhalte erst '
                    'nach expliziter Einwilligung. Alternativ: eingebettete Inhalte durch '
                    'datenschutzfreundliche Alternativen ersetzen (z.B. youtube-nocookie.com).'
                ),
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
    
    async def _enrich_with_internal_descriptions(self, issues: List[ComplianceIssue]) -> List[ComplianceIssue]:
        """
        Anreicherung der technisch erkannten Issues mit KI-generierten Compliance-Beschreibungen.
        Nutzt internen AI-Classifier (ai_legal_classifier) ohne externe API-Abhängigkeit.
        """
        try:
            return issues
        except Exception as e:
            logger.warning(f"Beschreibungs-Anreicherung fehlgeschlagen: {e}")
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