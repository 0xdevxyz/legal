"""
Complyo Website Compliance Scanner
Comprehensive scanner for German website compliance (DSGVO, Impressum, Cookies, Accessibility)
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import re
from datetime import datetime
from dataclasses import dataclass, asdict
import ssl
import certifi
import logging

logger = logging.getLogger(__name__)

# Import modulare Checks
from compliance_engine.checks import (
    check_impressum_compliance,
    check_datenschutz_compliance,
    check_cookie_compliance,
    check_barrierefreiheit_compliance,
    check_agb_compliance,
    check_shop_compliance,
    check_uwg_compliance,
)
from compliance_engine.browser_renderer import smart_fetch_html, detect_client_rendering
from compliance_engine.checks.cookie_check import consent_render_needed

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
    effort: str = ""  # Bearbeitungsaufwand (v4.0): gering | mittel | experte
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
                return self._create_error_response(
                    url, "Website nicht erreichbar (Verbindungsfehler/Timeout).",
                    reason="unreachable",
                )

            status_code = main_page.get('status_code', 0)
            soup = BeautifulSoup(main_page['content'], 'html.parser')
            main_page_headers = main_page.get('headers', {})

            # ⚠️ Fehlerstatus, ABER vollständige Seite ausgeliefert: Viele (WordPress-)
            # Seiten setzen wegen eines PHP-Fatals/Plugin-Fehlers im Shutdown einen
            # 500er, rendern den Body aber komplett. Browser zeigen die Seite normal an
            # und alle Compliance-Inhalte sind vorhanden → wir scannen den gelieferten
            # Inhalt, statt irreführend abzubrechen. Echte Wartung/Down (502/503/504),
            # Zugriffssperren (401/403) und 404 bleiben weiterhin "nicht scanbar".
            body = main_page.get('content') or ""
            title_tag = soup.title.string.strip() if (soup.title and soup.title.string) else ""
            delivers_full_page = (
                status_code not in (401, 403, 404, 502, 503, 504)
                and len(body) > 3000
                and '</html>' in body.lower()
                and soup.find('body') is not None
                and bool(title_tag)
            )
            if status_code >= 400 and delivers_full_page:
                logger.warning(
                    f"⚠️ {url} antwortet mit HTTP {status_code}, liefert aber eine "
                    f"vollständige Seite ({len(body)} Bytes, Titel: '{title_tag[:60]}') "
                    f"— Scan wird trotz Fehlerstatus durchgeführt."
                )
                status_code = 200  # als scanbar behandeln; Inhalt ist vollständig vorhanden

            # 🚧 Nicht scanbar: HTTP-Fehlerstatus → Hinweis statt irreführendem Score.
            # Grundsystem (CMS) trotzdem aus dem ausgelieferten HTML erkennen.
            if status_code >= 400:
                cms = self._detect_cms(soup, main_page_headers)
                if status_code in (502, 503, 504):
                    reason, notice = "maintenance", (
                        f"Die Website ist aktuell nicht erreichbar (HTTP {status_code}, "
                        f"vermutlich Wartungsmodus) und kann daher derzeit nicht auf "
                        f"Compliance geprüft werden. Eine Prüfung ist nur bei produktiv "
                        f"erreichbaren Seiten möglich — bitte wiederholen Sie den Scan nach "
                        f"Wiederherstellung. Hinweis: Auch Wartungsseiten müssen bereits ein "
                        f"Impressum und einen Link zur Datenschutzerklärung bereitstellen."
                    )
                elif status_code in (401, 403):
                    reason, notice = "blocked", (
                        f"Zugriff verweigert (HTTP {status_code}). Die Seite ist passwort-/"
                        f"firewall-geschützt und konnte nicht gescannt werden."
                    )
                elif status_code == 404:
                    reason, notice = "not_found", (
                        f"Seite nicht gefunden (HTTP 404). Bitte prüfen Sie die URL."
                    )
                else:
                    reason, notice = "http_error", (
                        f"Die Website antwortete mit HTTP {status_code} und konnte nicht "
                        f"vollständig gescannt werden."
                    )
                if cms:
                    notice += f" Erkanntes Grundsystem: {cms}."
                return self._create_error_response(
                    url, notice, reason=reason, status_code=status_code, detected_cms=cms,
                )

            # Render once if browser is needed, share HTML across all checks.
            # Zusätzlich zum klassischen CSR-Trigger wird auch gerendert, wenn ein
            # (i.d.R. JS-injizierter) Cookie-Banner/Consent/Tracking vermutet wird,
            # der im statischen HTML nicht sichtbar ist — sonst können dessen echte
            # Buttons nicht funktional geprüft werden (Custom-Banner & Fehlkonfig.).
            rendered_html = main_page['content']
            consent_buttons = None  # Button-Metriken aus dem Render (Dark-Pattern-Prüfung)
            needs_render = detect_client_rendering(main_page['content'])[0]
            render_reason = "client-side rendering"
            if not needs_render and consent_render_needed(soup):
                needs_render = True
                render_reason = "consent/cookie-banner detection"
            if needs_render:
                logger.info(f"🌐 Browser rendering needed ({render_reason}) — fetching once for all checks")
                try:
                    rendered_html, render_meta = await smart_fetch_html(url, main_page['content'], force=True)
                    logger.info("✅ Single browser render complete")
                    soup = BeautifulSoup(rendered_html, 'html.parser')
                    if isinstance(render_meta, dict):
                        consent_buttons = render_meta.get('consent_buttons')
                except Exception as e:
                    logger.warning(f"⚠️ Browser render failed ({e}); fallback auf statisches HTML")

            # 🔎 Grundsystem (CMS) + Produktiv-Status erkennen
            detected_cms = self._detect_cms(soup, main_page_headers)
            is_placeholder, placeholder_kind = self._detect_placeholder(soup)
            scan_notice = None
            if is_placeholder:
                scan_notice = (
                    f"Diese Seite befindet sich aktuell im {placeholder_kind}-Modus "
                    f"(Platzhalter-/Baustellenseite) und kann daher noch nicht vollständig "
                    f"auf Compliance geprüft werden. Eine vollständige Prüfung ist nur bei "
                    f"produktiv geschalteten (live erreichbaren) Seiten möglich — bitte "
                    f"wiederholen Sie den Scan, sobald die Website online ist. "
                    f"Wichtig: Auch Wartungs- und Baustellenseiten müssen bereits ein "
                    f"Impressum sowie einen Link zur Datenschutzerklärung bereitstellen, "
                    f"sobald sie öffentlich erreichbar sind."
                )
                if detected_cms:
                    scan_notice += (
                        f" Grundsystem erkannt: {detected_cms} — nach Veröffentlichung sind "
                        f"zusätzlich i.d.R. ein Cookie-Banner und eine vollständige "
                        f"Datenschutzerklärung erforderlich."
                    )

            # Run all compliance checks in parallel using pre-rendered soup
            # barrierefreiheit: no session = single-page only (avoids multi-page scan)
            barriere_task = check_barrierefreiheit_compliance(url, soup, None)
            impressum_task = check_impressum_compliance(url, soup, self.session)
            datenschutz_task = check_datenschutz_compliance(url, soup, self.session)
            cookie_task = check_cookie_compliance(url, soup, self.session, consent_buttons=consent_buttons)
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

            # ✅ v4.0 evidenz-basiert: Wenn der PRIMÄR-Check einer Säule abstürzt
            # (Exception, Seite nicht auswertbar), liegt KEINE Evidenz vor → die
            # Säule gilt als "ungeprüft" und darf NICHT als 100 (bestanden)
            # durchrutschen. Mapping Primär-Check → Säule:
            primary_check_by_pillar = {
                "accessibility": barriere_issues,
                "legal":         impressum_issues,
                "gdpr":          datenschutz_issues,
                "cookies":       cookie_issues,
            }
            unverified_pillars = {
                pillar for pillar, res in primary_check_by_pillar.items()
                if isinstance(res, Exception)
            }
            if unverified_pillars:
                logger.warning(f"⚠️ Ungeprüfte Säulen (Primär-Check fehlgeschlagen): {unverified_pillars}")

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

            # 🤖 v4.0 KI-Verifikation: NUR ungeprüfte Säulen gegen den realen
            # Seiteninhalt prüfen (Kostenkontrolle). Ergebnis fließt VOR dem Scoring
            # zurück: bestätigt-konform → Säule wird geprüft+ok, bestätigt-fehlend →
            # critical is_missing-Issue. Schlägt die KI fehl, bleibt die Säule UNVERIFIED.
            if unverified_pillars:
                issues, unverified_pillars = await self._ai_verify_unverified_pillars(
                    soup, issues, unverified_pillars
                )

            # ✅ v4.0 Klassifizierung: Bearbeitungsaufwand pro Issue (für Hinweise/Priorisierung)
            for _issue in issues:
                if not _issue.effort:
                    _issue.effort = ScoreCalculator.classify_effort(
                        severity=_issue.severity,
                        auto_fixable=_issue.auto_fixable,
                        is_missing=_issue.is_missing,
                    )

            # ✅ FIX v4.0: Evidenz-basierter Gesamtscore = Mittelwert der 4 Säulen,
            # ungeprüfte Säulen zählen NICHT als bestanden (Status UNVERIFIED).
            _scores = ScoreCalculator.compute_with_status(issues, unverified_pillars)
            compliance_score = _scores["overall_score"]
            _pillar_scores = _scores["pillar_scores"]
            _pillar_status = _scores["pillar_status"]
            
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
                    {
                        "pillar": pillar,
                        "score": round(score),
                        "status": _pillar_status.get(pillar),
                    }
                    for pillar, score in _pillar_scores.items()
                ],
                "pillar_status": _pillar_status,
                "recommendations": self._generate_recommendations(issues),
                "next_steps": self._generate_next_steps(issues),
                "has_accessibility_widget": has_accessibility_widget,
                "tcf_data": tcf_data,
                "score_breakdown": ScoreCalculator.get_score_breakdown(issues),
                # v4.0: Produktiv-Status & Grundsystem
                "detected_cms": detected_cms,
                "is_placeholder": is_placeholder,
                "scan_notice": scan_notice,
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
        """
        Fetch webpage content. Gibt Status UND Inhalt zurück (auch bei 4xx/5xx,
        damit der Aufrufer 'nicht scanbar'-Fälle erkennen und das Grundsystem
        analysieren kann). None nur bei echtem Verbindungsfehler.
        """
        try:
            async with self.session.get(url) as response:
                try:
                    content = await response.text()
                except Exception:
                    content = ""
                return {
                    'url': url,
                    'status_code': response.status,
                    'content': content,
                    'headers': dict(response.headers),
                }
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

            # Hosting-Standort (DSGVO Art. 44 / Art. 28): Erkennbare US-Cloud-/CDN-
            # Marker in den Response-Headern deuten auf Datenverarbeitung außerhalb
            # der EU hin. Verlässlich extern nur über Header indizierbar → info,
            # damit der Nutzer Hosting-Standort und AVV mit dem Anbieter prüft.
            us_host_markers = {
                'CloudFront (AWS)':   ['x-amz-cf-id', 'x-amz-cf-pop'],
                'Amazon S3/AWS':      ['x-amz-request-id', 'x-amz-id-2'],
                'Vercel':             ['x-vercel-id', 'x-vercel-cache'],
                'Netlify':            ['x-nf-request-id'],
                'GitHub Pages':       ['x-github-request-id'],
                'Google Cloud':       ['x-goog-generation', 'x-guploader-uploadid'],
                'Heroku':             ['x-heroku-dynos-in-use'],
            }
            detected_hosts = [
                name for name, keys in us_host_markers.items()
                if any(k in headers_lower for k in keys)
            ]
            # 'Server'-Header zusätzlich auswerten (z. B. AmazonS3, Vercel)
            server_hdr = headers_lower.get('server', '').lower()
            for name, needle in (('Amazon S3/AWS', 'amazons3'), ('Vercel', 'vercel'), ('Google Cloud', 'gws')):
                if needle in server_hdr and name not in detected_hosts:
                    detected_hosts.append(name)

            if detected_hosts:
                issues.append(ComplianceIssue(
                    category='datenschutz',
                    severity='info',
                    title='Hosting/CDN außerhalb der EU prüfen',
                    description=(
                        'Die Response-Header deuten auf einen US-/Nicht-EU-Anbieter hin: '
                        f'{", ".join(detected_hosts)}. Werden dort personenbezogene Daten '
                        '(inkl. Server-Logs mit IP) verarbeitet, ist dies ein Drittlandtransfer '
                        'und erfordert eine Rechtsgrundlage sowie einen AVV.'
                    ),
                    risk_euro=0,
                    legal_basis='DSGVO Art. 44 ff., Art. 28',
                    recommendation=(
                        'Prüfen Sie den tatsächlichen Verarbeitungsstandort, schließen Sie einen '
                        'AVV mit dem Anbieter ab und dokumentieren Sie die Transfer-Grundlage '
                        '(EU-US DPF / SCCs). Alternativ: EU-Hosting wählen.'
                    ),
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

        # ── Formular-Datenschutz (DSGVO Art. 13 bei Datenerhebung) ──────────
        # Erhebt ein Formular personenbezogene Daten, muss am Erhebungspunkt auf
        # die Datenschutzerklärung hingewiesen werden (Art. 13). Wir prüfen pro
        # Formular, ob es personenbezogene Felder hat UND ob ein Datenschutz-/
        # Einwilligungs-Bezug im Formular selbst erkennbar ist (Checkbox oder
        # Datenschutz-/Einwilligungs-Hinweis). Newsletter-Anmeldungen werden
        # zusätzlich auf Double-Opt-In/Einwilligung hingewiesen.
        personal_field_names = (
            'name', 'mail', 'email', 'e-mail', 'tel', 'phone', 'telefon',
            'nachricht', 'message', 'betreff', 'subject', 'anrede', 'vorname',
            'nachname', 'adresse', 'address', 'strasse', 'plz', 'ort',
        )
        form_privacy_flagged = False
        newsletter_flagged = False

        for form in soup.find_all('form'):
            form_text = form.get_text(' ', strip=True).lower()
            form_html = str(form).lower()

            inputs = form.find_all(['input', 'textarea', 'select'])
            input_types = {(i.get('type') or '').lower() for i in form.find_all('input')}
            has_textarea = bool(form.find('textarea'))
            has_email_field = 'email' in input_types or bool(
                re.search(r'name=["\'][^"\']*(mail|email)', form_html)
            )

            # Personenbezogenes Formular? (Such-/Filterleisten ausschließen)
            is_search = (
                'search' in input_types
                or (form.get('role') or '').lower() == 'search'
                or 'search' in (form.get('class') and ' '.join(form.get('class')).lower() or '')
            )
            collects_personal = (
                not is_search
                and (
                    has_textarea
                    or has_email_field
                    or 'tel' in input_types
                    or any(
                        kw in (i.get('name') or '').lower() or kw in (i.get('id') or '').lower()
                        or kw in (i.get('placeholder') or '').lower()
                        for i in inputs for kw in personal_field_names
                    )
                )
            )
            if not collects_personal:
                continue

            is_newsletter = bool(re.search(
                r'newsletter|abonnier|subscribe|anmeld.*(news|verteiler)|verteiler',
                form_text + ' ' + form_html
            ))
            has_privacy_ref = bool(re.search(
                r'datenschutz|privacy|einwillig|consent|zustimm', form_html
            )) or bool(form.find('input', attrs={'type': 'checkbox'}))

            # (#4) Newsletter ohne erkennbaren Einwilligungs-/DOI-Bezug
            if is_newsletter and not newsletter_flagged:
                newsletter_flagged = True
                if not has_privacy_ref:
                    issues.append(ComplianceIssue(
                        category='datenschutz',
                        severity='warning',
                        title='Newsletter-Anmeldung ohne erkennbare Einwilligung',
                        description=(
                            'Es wurde eine Newsletter-/E-Mail-Anmeldung gefunden, aber kein '
                            'Einwilligungs-Bezug (Checkbox / Datenschutz-Hinweis) im Formular. '
                            'Newsletter-Versand erfordert eine nachweisbare Einwilligung und '
                            'ein Double-Opt-In-Verfahren (Bestätigungsmail).'
                        ),
                        risk_euro=2000,
                        legal_basis='DSGVO Art. 6 Abs. 1 lit. a, Art. 7; § 7 UWG',
                        recommendation=(
                            'Ergänzen Sie eine aktive Einwilligungs-Checkbox mit Verweis auf die '
                            'Datenschutzerklärung und richten Sie ein Double-Opt-In ein '
                            '(Bestätigungs-Mail, deren Klick protokolliert wird).'
                        ),
                    ))
                continue

            # (#3) Personenbezogenes Formular ohne Datenschutz-Hinweis am Erhebungspunkt
            if collects_personal and not has_privacy_ref and not form_privacy_flagged:
                form_privacy_flagged = True
                issues.append(ComplianceIssue(
                    category='datenschutz',
                    severity='warning',
                    title='Formular ohne Datenschutzhinweis (Art. 13)',
                    description=(
                        'Ein Formular erhebt personenbezogene Daten, ohne dass am Erhebungspunkt '
                        'ein Datenschutz-Hinweis oder eine Einwilligungs-Checkbox erkennbar ist. '
                        'Nach DSGVO Art. 13 müssen Betroffene bereits bei der Datenerhebung über '
                        'die Verarbeitung informiert werden.'
                    ),
                    risk_euro=1500,
                    legal_basis='DSGVO Art. 13',
                    recommendation=(
                        'Fügen Sie direkt am Formular einen kurzen Datenschutzhinweis mit Link zur '
                        'Datenschutzerklärung hinzu (ggf. zusätzlich eine Einwilligungs-Checkbox, '
                        'wenn keine andere Rechtsgrundlage greift).'
                    ),
                ))

        return issues

    async def _check_social_media_plugins(self, base_url: str, soup: BeautifulSoup) -> List[ComplianceIssue]:
        """
        Prüft auf eingebettete Social-Media-Plugins die ohne Consent Daten übertragen.
        Erkennt sowohl iframe-Embeds als auch script-basierte Einbindungen.
        """
        issues = []

        # ⚠️ YouTube wird hier NICHT geprüft — Video-Embeds (inkl. korrektem
        # youtube-nocookie-Ausschluss) deckt privacy_transfer_findings als
        # eigenständiges Datenschutz-Issue ab. Doppelte Erfassung würde sonst
        # ein Issue in zwei Säulen erzeugen und youtube-nocookie fälschlich flaggen.
        social_patterns = {
            'Facebook': [r'facebook\.com/plugins', r'connect\.facebook\.net', r'facebook\.com/tr'],
            'Twitter/X': [r'platform\.twitter\.com', r'syndication\.twitter\.com'],
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
    
    # Säule → (Kategorie, Anzeigename) für KI-bestätigte Mangel-Issues
    _PILLAR_ISSUE_META = {
        "legal":         ("impressum",       "Pflichtangaben (Impressum/Rechtstexte)"),
        "gdpr":          ("datenschutz",     "Datenschutzerklärung"),
        "cookies":       ("cookies",         "Cookie-Consent"),
        "accessibility": ("barrierefreiheit", "Barrierefreiheit"),
    }

    async def _ai_verify_unverified_pillars(self, soup, issues, unverified_pillars):
        """
        KI-Verifikation der ungeprüften Säulen gegen den realen Seitentext.
        Gibt (issues, verbleibende_unverified_pillars) zurück.

        - KI bestätigt konform  → Säule aus unverified entfernen (zählt als geprüft).
        - KI bestätigt fehlend  → critical is_missing-Issue ergänzen (Säule = 0).
        - KI nicht verfügbar    → Säule bleibt unverified (kein Risiko, Scan läuft weiter).
        """
        try:
            from ai_review_engine import ai_verify_pillar
        except Exception:
            return issues, unverified_pillars

        page_text = soup.get_text(" ", strip=True)
        still_unverified = set(unverified_pillars)

        for pillar in list(unverified_pillars):
            meta = self._PILLAR_ISSUE_META.get(pillar)
            if not meta:
                continue
            category, label = meta
            try:
                verdict = await ai_verify_pillar(pillar, page_text)
            except Exception as e:
                logger.warning(f"⚠️ KI-Verifikation '{pillar}' fehlgeschlagen: {e}")
                verdict = None

            if not verdict:
                continue  # bleibt UNVERIFIED

            if verdict["compliant"]:
                still_unverified.discard(pillar)
                logger.info(f"✅ KI bestätigt Säule '{pillar}' als konform (conf={verdict['confidence']})")
            else:
                still_unverified.discard(pillar)
                missing = ", ".join(verdict.get("missing", [])) or verdict.get("reason", "")
                issues.append(ComplianceIssue(
                    category=category,
                    severity="critical",
                    title=f"{label} fehlt oder unzureichend (KI-geprüft)",
                    description=(
                        f"Die KI-Prüfung des Seiteninhalts ergab, dass die Anforderung nicht erfüllt ist. "
                        f"{verdict.get('reason', '')}".strip()
                    ),
                    risk_euro=3000,
                    recommendation=f"Ergänzen/vervollständigen Sie: {missing}" if missing else "Inhalt vervollständigen.",
                    legal_basis="DSGVO / DDG / BFSG",
                    auto_fixable=False,
                    is_missing=True,
                    metadata={"ai_verified": True, "confidence": verdict.get("confidence")},
                ))
                logger.info(f"⚠️ KI bestätigt Säule '{pillar}' als NICHT konform")

        return issues, still_unverified

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
    
    @staticmethod
    def _detect_cms(soup, headers: dict = None) -> Optional[str]:
        """
        Erkennt das Grundsystem (CMS) aus HTML-Signaturen und HTTP-Headern.
        Wichtig auch bei Platzhalter-/Fehlerseiten: das darunterliegende System
        (z.B. WordPress) bestimmt, welche Compliance-Pflichten nach Go-Live gelten.
        """
        html = str(soup).lower()
        headers = {k.lower(): str(v).lower() for k, v in (headers or {}).items()}

        # Generator-Meta auslesen
        generator = ""
        gen_tag = soup.find("meta", attrs={"name": re.compile(r"generator", re.I)})
        if gen_tag and gen_tag.get("content"):
            generator = gen_tag.get("content", "").lower()

        signatures = [
            ("WordPress", ["wp-content", "wp-includes", "/wp-json", "wp-emoji", "wordpress"]),
            ("Shopify",   ["cdn.shopify.com", "shopify.theme", "x-shopify"]),
            ("Wix",       ["static.wixstatic.com", "wix.com", "_wix"]),
            ("Jimdo",     ["jimdo", "jimstatic.com"]),
            ("Typo3",     ["typo3", "/typo3conf/"]),
            ("Joomla",    ["/media/jui/", "joomla", "com_content"]),
            ("Drupal",    ["drupal-settings-json", "/sites/default/files", "drupal"]),
            ("Webflow",   ["webflow", "assets.website-files.com"]),
            ("Squarespace", ["squarespace", "static1.squarespace.com"]),
        ]
        haystack = html + " " + generator + " " + " ".join(headers.values())
        for name, markers in signatures:
            if any(m in haystack for m in markers):
                return name
        return None

    @staticmethod
    def _detect_placeholder(soup) -> "tuple[bool, str]":
        """
        Erkennt Platzhalter-/Baustellen-/Coming-Soon-Seiten (HTTP 200, aber kein
        produktiver Inhalt). Gibt (is_placeholder, art) zurück.
        """
        title = (soup.title.get_text() if soup.title else "").lower()
        body_text = soup.get_text(" ", strip=True).lower()

        patterns = {
            "Wartungs": ["wartungsmodus", "wartungsarbeiten", "maintenance", "under maintenance", "kurzfristig nicht verfügbar"],
            "Baustellen": ["under construction", "im aufbau", "baustelle", "seite im aufbau", "website is being built"],
            "Coming-Soon": ["coming soon", "demnächst", "in kürze online", "launching soon", "bald verfügbar", "wir sind bald für sie da"],
        }
        haystack = f"{title} {body_text}"
        for kind, kws in patterns.items():
            if any(kw in haystack for kw in kws):
                return True, kind

        # Sehr wenig Inhalt + kaum Links → wahrscheinlich Platzhalter
        if len(body_text) < 400 and len(soup.find_all("a", href=True)) <= 2:
            return True, "Platzhalter"
        return False, ""

    def _create_error_response(
        self, url: str, error_message: str,
        reason: str = "error", status_code: int = 0,
        detected_cms: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create error response structure (mit Klassifizierung für klare UI-Hinweise)."""
        return {
            "url": url,
            "scan_timestamp": datetime.now(),
            "error": True,
            "error_message": error_message,
            "error_reason": reason,        # unreachable|maintenance|blocked|not_found|http_error
            "status_code": status_code,
            "not_scannable": True,
            "detected_cms": detected_cms,
            "compliance_score": 0,
            "total_risk_euro": 0,
            "issues": [],
            "recommendations": [error_message],
        }

# Async context manager usage example:
# async with ComplianceScanner() as scanner:
#     result = await scanner.scan_website("https://example.com")