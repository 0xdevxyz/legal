"""
Public API Routes for Unauthenticated Access
Provides website analysis without requiring authentication
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, Optional, List
import logging
import json
import os
import asyncio
import aiohttp
import ipaddress
import socket
from datetime import datetime
from compliance_engine.scanner import ComplianceScanner
from compliance_engine.priority_engine import priority_engine
from compliance_engine.solution_generator import solution_generator
from ai_review_engine import run_ai_review_pass
from compliance_engine.cookie_analyzer import cookie_analyzer
from website_crawler import WebsiteCrawler
from auth_routes import get_current_user
from accessibility_post_scan_processor import AccessibilityPostScanProcessor
from ai_solution_cache_service import AISolutionCache

logger = logging.getLogger(__name__)

# ✅ OpenRouter API für individuelle KI-Lösungen
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

public_router = APIRouter(prefix="/api", tags=["public"])

# Für v1 API (Widget-Support)
v1_router = APIRouter(prefix="/v1", tags=["widget-api"])

# Database pool (wird von main.py gesetzt)
db_pool = None

# ✅ AI Solution Cache (wird von main_production.py initialisiert)
solution_cache: Optional[AISolutionCache] = None

def set_db_pool(pool):
    """Setzt den Database Pool (called from main.py)"""
    global db_pool
    return pool

class AnalyzeRequest(BaseModel):
    url: str
    legal_update_id: Optional[int] = None

class IssueLocation(BaseModel):
    area: str
    hint: str

class IssueSolution(BaseModel):
    code_snippet: str
    steps: List[str]

class ComplianceIssue(BaseModel):
    id: str
    category: str
    severity: str
    title: str
    description: str
    risk_euro_min: float
    risk_euro_max: float
    risk_range: str
    legal_basis: str
    location: IssueLocation
    solution: IssueSolution
    ai_solution: Optional[str] = None  # ✅ Individuelle KI-generierte Lösung
    auto_fixable: bool
    is_missing: bool = False  # True wenn komplettes Hauptelement fehlt (für 0-Score-Logik)

class PillarScore(BaseModel):
    """Score für eine Compliance-Säule"""
    pillar: str  # 'accessibility', 'gdpr', 'legal', 'cookies'
    score: int  # 0-100
    issues_count: int
    critical_count: int
    warning_count: int

class AnalysisResponse(BaseModel):
    success: bool
    url: str
    compliance_score: int
    estimated_risk_euro: str
    issues: List[ComplianceIssue]  # Changed from list to List[ComplianceIssue]
    positive_checks: Optional[List[Dict[str, Any]]] = []  # NEW: Was funktioniert bereits
    pillar_scores: Optional[List[PillarScore]] = []  # NEW: Säulen-Scores
    issue_groups: Optional[List[Dict[str, Any]]] = []  # ✅ NEU: Gruppierte Issues
    grouping_stats: Optional[Dict[str, Any]] = {}  # ✅ NEU: Gruppierungs-Statistiken
    has_accessibility_widget: Optional[bool] = False  # ✅ NEU: Widget-Status
    riskAmount: str
    score: int
    scan_duration_ms: Optional[int] = None
    timestamp: str

@public_router.post("/analyze", response_model=AnalysisResponse)
async def analyze_website_public(request: AnalyzeRequest, http_request: Request, current_user: dict = Depends(get_current_user)):
    """
    Website analysis endpoint (requires authentication)
    
    Performs a compliance scan of a website and returns:
    - Compliance score (0-100)
    - List of compliance issues with risk calculation
    - Estimated risk in EUR
    - Scan metadata
    
    Now saves website and scan results to database for persistence.
    """
    try:
        url = str(request.url)
        legal_update_id = request.legal_update_id
        user_id = current_user.get("id") or current_user.get("user_id")
        
        # ✅ FIX: Normalisiere URL (füge https:// hinzu falls fehlt)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            logger.info(f"✅ URL normalized to: {url}")
        
        logger.info(f"Analysis request for: {url} (User: {user_id})")

        # ✅ Vorab-Prüfung: Ist die Domain überhaupt erreichbar?
        parsed_host = url.split("//")[-1].split("/")[0].split(":")[0]
        try:
            resolved_ip = socket.gethostbyname(parsed_host)
            ip_obj = ipaddress.ip_address(resolved_ip)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                raise HTTPException(status_code=400, detail={
                    "error": "INVALID_DOMAIN",
                    "message": f"Die Domain '{parsed_host}' ist keine öffentlich erreichbare Website.",
                    "suggestions": ["Geben Sie eine echte, öffentlich zugängliche Domain ein (z.B. 'meineshop.de')"]
                })
        except socket.gaierror:
            raise HTTPException(status_code=400, detail={
                "error": "DOMAIN_NOT_FOUND",
                "message": f"Die Domain '{parsed_host}' existiert nicht oder ist nicht erreichbar.",
                "suggestions": [
                    "Prüfen Sie ob die Domain korrekt geschrieben ist",
                    "Stellen Sie sicher, dass die Website online ist"
                ]
            })
        
        # Get risk calculator from app state
        from main_production import db_pool, risk_calculator
        
        # Bei legal_update_id: force-refresh des Legal-Update-Cache
        if legal_update_id:
            try:
                from main_production import legal_update_integration
                if legal_update_integration:
                    await legal_update_integration.get_active_legal_updates(force_refresh=True)
                    logger.info(f"Legal Update Cache refreshed für Update ID {legal_update_id}")
            except Exception as e:
                logger.warning(f"Legal Update Cache refresh fehlgeschlagen (non-critical): {e}")
        
        # Perform compliance scan and crawl in parallel
        try:
            crawler = WebsiteCrawler(timeout=10)
            async with ComplianceScanner() as scanner:
                scan_result, website_structure = await asyncio.gather(
                    scanner.scan_website(url),
                    crawler.crawl_website(url),
                    return_exceptions=True
                )
            
            if isinstance(scan_result, Exception):
                raise scan_result
            
            if isinstance(website_structure, Exception):
                logger.warning(f"Crawler failed (non-critical): {website_structure}")
                website_structure = {}

            if scan_result.get("error"):
                # ❌ NO MOCK DATA! Return clear error to user
                error_message = scan_result.get('error_message', 'Website konnte nicht gescannt werden')
                logger.error(f"Scanner failed for {url}: {error_message}")
                
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "WEBSITE_NOT_REACHABLE",
                        "message": f"Die Website '{url}' konnte nicht erreicht werden.",
                        "details": error_message,
                        "suggestions": [
                            "Prüfen Sie, ob die URL korrekt ist (z.B. 'example.com' statt 'example')",
                            "Stellen Sie sicher, dass die Website online ist",
                            "Versuchen Sie es mit 'www.' Prefix (z.B. 'www.example.com')",
                            "Prüfen Sie, ob die Website eine Firewall hat, die unseren Scanner blockiert"
                        ]
                    }
                )
            
            # Store website structure for later AI fix generation
            scan_result['website_structure'] = website_structure
            
            # Convert string issues to structured objects
            structured_issues = []
            if scan_result.get("issues"):
                for idx, issue in enumerate(scan_result["issues"][:30]):  # Limit to 30 issues (für vollständige Compliance-Prüfung aller 4 Säulen)
                    # ✅ FIX: Prüfe ob Issue bereits strukturiert ist (von Check-Modulen)
                    if isinstance(issue, dict) and 'severity' in issue:
                        # Issue kommt von Check-Modulen - behalte Original-Severity!
                        # ✅ Generiere aussagekräftige ID basierend auf Kategorie und Titel
                        category = issue.get('category', 'compliance')
                        title = issue.get('title', issue.get('description', ''))
                        # Erstelle Slug aus Title (erste 3-4 Worte)
                        title_words = ''.join(c if c.isalnum() or c.isspace() else '' for c in title.lower())
                        title_slug = '-'.join(title_words.split()[:4])
                        issue_id = f"{category}-{title_slug}"[:50]  # Max 50 Zeichen
                        
                        structured_issue = ComplianceIssue(
                            id=issue_id,
                            category=issue.get('category', 'compliance'),
                            severity=issue.get('severity'),  # ✅ Original-Severity beibehalten!
                            title=issue.get('title', issue.get('description', ''))[:100],
                            description=issue.get('description', ''),
                            risk_euro_min=issue.get('risk_euro', 1000),
                            risk_euro_max=issue.get('risk_euro', 1000),
                            risk_range=f"{issue.get('risk_euro', 1000):,}€".replace(',', '.'),
                            legal_basis=issue.get('legal_basis', 'Gesetzliche Anforderung'),
                            location=IssueLocation(
                                area=_determine_issue_area(issue.get('category', 'compliance')),
                                hint=f"{_determine_issue_area(issue.get('category', 'compliance'))} fehlt oder ist fehlerhaft"
                            ),
                            solution=_generate_solution_for_issue(
                                category=issue.get('category', 'compliance'),
                                title=issue.get('title', ''),
                                description=issue.get('description', '')
                            ),
                            auto_fixable=issue.get('auto_fixable', False),
                            is_missing=issue.get('is_missing', False)  # ✅ is_missing von Check-Modulen übernehmen
                        )
                        structured_issues.append(structured_issue)
                    else:
                        # Legacy: String-Issue - verwende risk_calculator
                        issue_text = issue if isinstance(issue, str) else issue.get("description", str(issue))
                        
                        # Calculate risk for this issue
                        risk_data = await risk_calculator.calculate_issue_risk(issue_text)
                        
                        # ✅ Generiere aussagekräftige ID für Legacy-Issues
                        category = risk_data['category']
                        title_words = ''.join(c if c.isalnum() or c.isspace() else '' for c in issue_text[:100].lower())
                        title_slug = '-'.join(title_words.split()[:4])
                        issue_id = f"{category}-{title_slug}"[:50]
                        
                        structured_issue = ComplianceIssue(
                            id=issue_id,
                            category=risk_data['category'],
                            severity=risk_data['severity'],
                            title=issue_text[:100],  # Truncate long titles
                            description=issue_text,
                            risk_euro_min=risk_data['risk_min'],
                            risk_euro_max=risk_data['risk_max'],
                            risk_range=risk_data['risk_range'],
                            legal_basis=risk_data['legal_basis'],
                            location=IssueLocation(
                                area=_determine_issue_area(risk_data['category']),
                                hint=f"{_determine_issue_area(risk_data['category'])} fehlt oder ist fehlerhaft"
                            ),
                            solution=_generate_solution(risk_data['category']),
                            auto_fixable=risk_data['category'] in ['impressum', 'datenschutz', 'cookies', 'agb']
                        )
                        structured_issues.append(structured_issue)
            
            # Calculate total risk
            total_risk_data = await risk_calculator.calculate_total_risk(
                [i.description for i in structured_issues]
            )
            
            # Generate unique scan_id
            import uuid
            scan_id = f"scan-{uuid.uuid4().hex[:12]}"
            
            # Calculate critical and warning issues
            critical_issues_count = sum(1 for issue in structured_issues if issue.severity == 'critical')
            warning_issues_count = sum(1 for issue in structured_issues if issue.severity == 'warning')
            
            # Priorisiere Issues mit Priority Engine
            try:
                issues_as_dicts = [
                    {
                        'id': issue.id,
                        'title': issue.title,
                        'description': issue.description,
                        'category': issue.category,
                        'severity': issue.severity,
                        'risk_euro_max': issue.risk_euro_max,
                        'auto_fixable': issue.auto_fixable
                    }
                    for issue in structured_issues
                ]
                prioritized_issues = priority_engine.calculate_fix_priority(issues_as_dicts)
                
                # Update structured_issues mit Prioritäts-Informationen
                for i, issue in enumerate(structured_issues):
                    if i < len(prioritized_issues):
                        # Füge Prioritäts-Info hinzu (wird im Frontend als zusätzliche Property verfügbar sein)
                        pass  # Pydantic-Modell kann nicht erweitert werden, aber Backend nutzt sortierte Liste
                
                logger.info(f"✅ {len(prioritized_issues)} Issues priorisiert")
            except Exception as e:
                logger.warning(f"Priority Engine Fehler (nicht kritisch): {e}")
            
            # Prepare response
            # Generate positive checks
            positive_checks = _generate_positive_checks(
                structured_issues, 
                scan_result.get("compliance_score", 50)
            )
            
            # ✅ AI Review Pass: Prüft und verfeinert ALLE Issues + generiert individuelle Lösungen
            if OPENROUTER_API_KEY and len(structured_issues) > 0:
                logger.info(f"🤖 AI Review Pass: {len(structured_issues)} Issues werden geprüft...")
                try:
                    structured_issues = await run_ai_review_pass(
                        issues=structured_issues,
                        scan_result={
                            "url": url,
                            "tech_stack": scan_result.get("tech_stack", {}),
                            "tracking_services": scan_result.get("tracking_services", []),
                            "detected_cookies": scan_result.get("detected_cookies", []),
                        },
                        max_reviews=20,
                        max_solutions=15,
                    )
                except Exception as e:
                    logger.warning(f"⚠️ AI Review Pass Fehler (nicht kritisch): {e}")
            else:
                logger.info("ℹ️ AI Review Pass übersprungen (kein API Key)")
            
            # ✅ NEU: Berechne Säulen-Scores nach Backend-Logik
            pillar_scores = _calculate_pillar_scores(structured_issues)
            logger.info(f"✅ Säulen-Scores berechnet: {[(p.pillar, p.score) for p in pillar_scores]}")
            
            # ✅ FIX: Berechne Gesamt-Score als Durchschnitt der 4 Säulen
            overall_compliance_score = int(sum(p.score for p in pillar_scores) / len(pillar_scores)) if pillar_scores else 0
            logger.info(f"✅ Gesamt-Compliance-Score (Durchschnitt): {overall_compliance_score}/100")
            
            # ✅ PERSISTENCE: Save website and scan to database
            from main_production import db_pool
            try:
                async with db_pool.acquire() as conn:
                    # Ensure user_id is integer
                    user_id_int = int(user_id)

                    # 1. Check if website exists, if not create it
                    website = await conn.fetchrow(
                        "SELECT id FROM tracked_websites WHERE user_id = $1 AND url = $2",
                        user_id_int, scan_result.get("url", url)
                    )

                    if not website:
                        # Create new website
                        website_id = await conn.fetchval(
                            """
                            INSERT INTO tracked_websites (user_id, url, name, last_scan_date, last_score, status)
                            VALUES ($1, $2, $3, NOW(), $4, 'active')
                            RETURNING id
                            """,
                            user_id_int,
                            scan_result.get("url", url),
                            scan_result.get("url", url).replace('https://', '').replace('http://', ''),
                            overall_compliance_score
                        )
                        logger.info(f"✅ Created new website ID {website_id} for user {user_id}")
                    else:
                        # Update existing website
                        website_id = website['id']
                        await conn.execute(
                            """
                            UPDATE tracked_websites
                            SET last_scan_date = NOW(), last_score = $1, status = 'active', scan_count = COALESCE(scan_count, 0) + 1
                            WHERE id = $2
                            """,
                            overall_compliance_score,
                            website_id
                        )
                        logger.info(f"✅ Updated website ID {website_id}")
                    
                    # 2. Save scan to scan_history
                    scan_id = f"scan_{user_id_int}_{int(datetime.now().timestamp())}"
                    await conn.execute(
                        """
                        INSERT INTO scan_history (
                            scan_id, user_id, website_id, url, website_name, scan_timestamp,
                            scan_data, compliance_score, total_risk_euro, critical_issues,
                            warning_issues, total_issues, scan_duration_ms, legal_update_id
                        ) VALUES ($1, $2, $3, $4, $5, NOW(), $6, $7, $8, $9, $10, $11, $12, $13)
                        """,
                        scan_id,
                        user_id_int,
                        website_id,
                        scan_result.get("url", url),
                        scan_result.get("url", url).replace('https://', '').replace('http://', ''),
                        json.dumps({
                            'issues': [
                                {
                                    'id': i.id,
                                    'category': i.category,
                                    'severity': i.severity,
                                    'title': i.title,
                                    'description': i.description,
                                    'risk_euro_min': i.risk_euro_min,
                                    'risk_euro_max': i.risk_euro_max
                                }
                                for i in structured_issues
                            ],
                            'positive_checks': positive_checks,
                            'pillar_scores': [{'pillar': p.pillar, 'score': p.score} for p in pillar_scores],
                            'issue_groups': scan_result.get('issue_groups', []),
                            'grouping_stats': scan_result.get('grouping_stats', {})
                        }),
                        overall_compliance_score,
                        total_risk_data.get('total_risk_max', 0),
                        critical_issues_count,
                        warning_issues_count,
                        len(structured_issues),
                        scan_result.get("scan_duration_ms"),
                        legal_update_id
                    )
                    logger.info(f"Saved scan history for website ID {website_id}" + (f" (triggered by legal update {legal_update_id})" if legal_update_id else ""))
                    
                    # 🚀 NEU: Post-Process Accessibility-Issues (Alt-Text-Generierung)
                    try:
                        if db_pool:
                            processor = AccessibilityPostScanProcessor(db_pool)
                            
                            # Generiere scan_id basierend auf website_id + timestamp
                            scan_id = f"scan-{website_id}-{int(datetime.now().timestamp())}"
                            
                            post_process_result = await processor.process_scan_results(
                                scan_id=scan_id,
                                user_id=str(user_id_uuid),
                                scan_data={
                                    'issues': [
                                        {
                                            'id': i.id,
                                            'category': i.category,
                                            'severity': i.severity,
                                            'title': i.title,
                                            'description': i.description
                                        }
                                        for i in structured_issues
                                    ]
                                },
                                site_url=scan_result.get("url", url)
                            )
                            
                            if post_process_result['success']:
                                logger.info(f"✨ Post-processing: {post_process_result['message']}")
                            else:
                                logger.warning(f"⚠️ Post-processing failed: {post_process_result.get('error', 'Unknown')}")
                    except Exception as post_error:
                        logger.error(f"❌ Accessibility post-processing failed: {post_error}")
                        # Don't fail the request if post-processing fails
                    
            except Exception as db_error:
                logger.error(f"❌ Database persistence failed: {db_error}")
                # Don't fail the request if DB save fails
            
            # ✅ FIX: Stelle sicher, dass issue_groups immer eine Liste ist
            issue_groups = scan_result.get("issue_groups", [])
            if not isinstance(issue_groups, list):
                issue_groups = []
            
            grouping_stats = scan_result.get("grouping_stats", {})
            if not isinstance(grouping_stats, dict):
                grouping_stats = {}
            
            response_data = AnalysisResponse(
                success=True,
                url=scan_result.get("url", url),
                compliance_score=overall_compliance_score,  # ✅ Durchschnitt statt Scanner-Score
                estimated_risk_euro=total_risk_data['total_risk_range'],
                issues=structured_issues,
                positive_checks=positive_checks,
                pillar_scores=pillar_scores,  # ✅ NEU: Säulen-Scores
                issue_groups=issue_groups,  # ✅ NEU: Gruppierte Issues (immer Liste)
                grouping_stats=grouping_stats,  # ✅ NEU: Gruppierungs-Statistiken (immer Dict)
                riskAmount=total_risk_data['total_risk_range'],
                score=overall_compliance_score,  # ✅ Durchschnitt statt Scanner-Score
                scan_duration_ms=scan_result.get("scan_duration_ms"),
                timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"✅ Scan completed with {len(response_data.issue_groups)} issue groups")
            
            return response_data
            
        except Exception as scanner_error:
            # ❌ NO MOCK DATA! Return clear error to user
            logger.error(f"Scanner error for {url}: {scanner_error}", exc_info=True)
            
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "SCANNER_ERROR",
                    "message": f"Die Website '{url}' konnte nicht gescannt werden.",
                    "details": str(scanner_error),
                    "suggestions": [
                        "Stellen Sie sicher, dass die Website online ist",
                        "Prüfen Sie, ob die URL korrekt ist",
                        "Versuchen Sie es in ein paar Minuten erneut",
                        "Kontaktieren Sie den Support, falls das Problem weiterhin besteht"
                    ]
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing website: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Fehler bei der Website-Analyse. Bitte versuchen Sie es erneut."
        )

def _calculate_pillar_scores(issues: List[ComplianceIssue]) -> List[PillarScore]:
    """
    Berechnet Säulen-Scores basierend auf Backend-Logik
    Formel: 100 - (critical × 60 + warning × 15), max 40 bei critical > 0
    """
    # Säulen-Mapping (Backend-Logik)
    pillar_mapping = {
        'accessibility': ['barrierefreiheit', 'kontraste', 'tastaturbedienung'],
        'gdpr':          ['datenschutz', 'tracking', 'datenverarbeitung', 'avv'],
        'legal':         ['impressum', 'agb', 'contact', 'uwg'],
        'cookies':       ['cookies'],
        'security':      ['security'],
        'shop':          ['shop', 'widerrufsbelehrung', 'preisangaben'],
    }
    
    pillar_scores = []
    
    for pillar, categories in pillar_mapping.items():
        # Filtere Issues nach Säule
        pillar_issues = [
            issue for issue in issues 
            if issue.category.lower() in categories
        ]
        
        # ✅ NEUE LOGIK: Prüfe ob Hauptelement komplett fehlt
        has_missing_core_element = any(
            getattr(issue, 'is_missing', False) for issue in pillar_issues
        )
        
        if has_missing_core_element:
            # Wenn Hauptelement fehlt (Impressum, Datenschutz, Cookie-Banner, A11y-Widget):
            # Score = 0 Punkte
            score = 0
            critical_count = sum(1 for i in pillar_issues if i.severity == 'critical')
            warning_count = sum(1 for i in pillar_issues if i.severity == 'warning')
        else:
            # Normale Berechnung: Element vorhanden, aber fehlerhaft/unvollständig
            # Zähle Severity
            critical_count = sum(1 for i in pillar_issues if i.severity == 'critical')
            warning_count = sum(1 for i in pillar_issues if i.severity == 'warning')
            
            # Berechne Score nach Backend-Formel
            # CRITICAL: -60 Punkte pro Issue
            # WARNING: -15 Punkte pro Issue
            score = 100 - (critical_count * 60 + warning_count * 15)
            
            # Wenn CRITICAL Issues vorhanden: maximal Score 40
            if critical_count > 0:
                score = min(score, 40)
            
            score = max(0, score)  # Nie negativ
        
        pillar_scores.append(PillarScore(
            pillar=pillar,
            score=score,
            issues_count=len(pillar_issues),
            critical_count=critical_count,
            warning_count=warning_count
        ))
    
    return pillar_scores

def _determine_issue_area(category: str) -> str:
    """Bestimmt den Seitenbereich basierend auf der Kategorie"""
    area_mapping = {
        'impressum': 'Footer',
        'datenschutz': 'Footer',
        'cookies': 'Header/Banner',
        'agb': 'Footer',
        'widerrufsbelehrung': 'Footer/Checkout',
        'contact': 'Footer/Kontaktseite',
        'barrierefreiheit': 'Gesamte Seite',
        'kontraste': 'Gesamte Seite',
        'tastaturbedienung': 'Navigation/Formulare',
        'tracking': 'Header/Scripts',
        'urheberrecht': 'Content/Bilder',
        'markenrecht': 'Content/Logos',
        'preisangaben': 'Produktseiten',
        'uwg': 'Content/Werbung',
        'preisangaben': 'Produktseiten/Shop',
        'shop': 'Online-Shop',
        'widerrufsbelehrung': 'Online-Shop',
        'avv': 'Datenschutz',
        'security': 'HTTP-Header/Server',
    }
    return area_mapping.get(category, 'Unbekannter Bereich')

def _generate_positive_checks(structured_issues: list, compliance_score: int) -> list:
    """Generiert positive Checks basierend auf fehlenden Issues"""
    all_categories = {
        'impressum': 'Impressum vorhanden und vollständig',
        'datenschutz': 'Datenschutzerklärung vollständig',
        'cookies': 'Cookie-Banner korrekt implementiert',
        'barrierefreiheit': 'Barrierefreiheit-Tools implementiert',
        'https': 'HTTPS-Verschlüsselung aktiv',
        'responsive': 'Mobile-optimierte Darstellung',
    }
    
    # Extrahiere vorhandene Issue-Kategorien
    # Sicherer Zugriff: dict oder Pydantic-Objekt
    issue_categories = {
        issue.get('category') if isinstance(issue, dict) else issue.category 
        for issue in structured_issues
    }
    
    # Generiere positive Checks für nicht-vorhandene Issues
    positive_checks = []
    for category, description in all_categories.items():
        if category not in issue_categories:
            positive_checks.append({
                'category': category,
                'title': description,
                'status': 'compliant',
                'icon': '✅'
            })
    
    # Füge weitere positive Checks basierend auf Score hinzu
    if compliance_score >= 50:
        positive_checks.append({
            'category': 'general',
            'title': 'Grundlegende Compliance-Anforderungen erfüllt',
            'status': 'compliant',
            'icon': '✅'
        })
    
    return positive_checks

async def _generate_ai_solution(issue_title: str, issue_description: str, category: str, url: str, retry_count: int = 0) -> Optional[str]:
    """
    Generiert individuelle KI-Lösung mit intelligentem Caching
    
    Flow:
    1. Prüfe Cache (Exact + Fuzzy Match)
    2. Bei Cache-Miss: OpenRouter API
    3. Speichere neue Lösung im Cache
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣ VERSUCHE CACHE-LOOKUP ZUERST
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if solution_cache:
        try:
            cached = await solution_cache.get_cached_solution(
                category=category,
                title=issue_title,
                description=issue_description,
                use_fuzzy=True
            )
            
            if cached:
                # ✅ Cache Hit - Spare API Call!
                match_type = cached.get('match_type', 'exact')
                usage = cached.get('usage_count', 0)
                success = cached.get('success_rate', 0.0)
                
                prefix = f"🎯 **Bewährte Lösung** ({usage}x erfolgreich umgesetzt, {success:.0%} Success Rate)\n\n"
                
                if match_type == 'fuzzy':
                    similarity = cached.get('similarity', 0.0)
                    prefix = f"🎯 **Ähnliche bewährte Lösung** ({similarity:.0%} Match, {usage}x verwendet)\n\n"
                
                return prefix + cached['solution']
        except Exception as e:
            logger.error(f"❌ Cache lookup failed: {e} - Falling back to API")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2️⃣ CACHE MISS - Nutze OpenRouter API
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not OPENROUTER_API_KEY:
        logger.warning("⚠️ No OPENROUTER_API_KEY - skipping AI solution")
        return None
    
    # Rate Limit Handling: Max 3 Retries mit exponential backoff
    MAX_RETRIES = 3
    BACKOFF_SECONDS = [2, 5, 10]  # 2s, 5s, 10s
    
    try:
        prompt = f"""Du bist ein Experte für Website-Compliance und Barrierefreiheit.

WEBSITE: {url}
PROBLEM: {issue_title}
DETAILS: {issue_description}
KATEGORIE: {category}

Erstelle eine **praxisnahe, individuell auf dieses Problem zugeschnittene Lösung**.

WICHTIG:
- Beziehe dich konkret auf die Website {url}
- Gib spezifische, umsetzbare Schritte
- Füge passende Code-Beispiele hinzu
- Erkläre anfängerfreundlich

Format:
1. Kurze Analyse des Problems (2-3 Sätze)
2. Konkrete Lösungsschritte (3-5 Punkte)
3. Code-Beispiel (falls relevant)
4. Hinweis zur Überprüfung

Antworte auf Deutsch, maximal 300 Wörter."""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://complyo.tech",
                    "X-Title": "Complyo Compliance Scanner"
                },
                json={
                    "model": "moonshotai/kimi-k2-thinking",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 800,
                    "temperature": 0.7
                },
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    ai_solution = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    logger.info(f"✅ KI-Lösung generiert für: {issue_title[:50]}...")
                    
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    # 3️⃣ SPEICHERE NEUE LÖSUNG IM CACHE
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    if solution_cache and ai_solution:
                        try:
                            await solution_cache.store_solution(
                                category=category,
                                title=issue_title,
                                description=issue_description,
                                solution=ai_solution,
                                model="moonshotai/kimi-k2-thinking"
                            )
                        except Exception as e:
                            logger.error(f"❌ Failed to cache solution: {e}")
                    
                    return ai_solution
                elif response.status == 429:
                    # Rate Limit - Retry mit Backoff
                    if retry_count < MAX_RETRIES:
                        wait_time = BACKOFF_SECONDS[retry_count]
                        logger.warning(f"⚠️ Rate Limit (429) - Retry {retry_count + 1}/{MAX_RETRIES} in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        return await _generate_ai_solution(issue_title, issue_description, category, url, retry_count + 1)
                    else:
                        logger.error(f"❌ Rate Limit (429) - Max Retries erreicht")
                        return "⚠️ KI-Analyse vorübergehend nicht verfügbar (Rate Limit). Bitte in wenigen Minuten erneut versuchen."
                else:
                    error_text = await response.text()
                    logger.error(f"❌ OpenRouter API Error: {response.status} - {error_text[:200]}")
                    return None
                    
    except asyncio.TimeoutError:
        logger.error(f"❌ KI-Lösung Timeout für: {issue_title[:50]}")
        return None
    except Exception as e:
        logger.error(f"❌ KI-Lösung Generation failed: {e}")
        return None

def _generate_solution_for_issue(category: str, title: str = '', description: str = '') -> IssueSolution:
    """Generiert issue-spezifische Lösungsvorschläge basierend auf Kategorie UND konkretem Titel"""
    
    title_lower = title.lower()
    desc_lower = description.lower()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECURITY-HEADERS (hsts, csp, x-frame, etc.)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if category == 'security' or 'security' in title_lower:
        # HSTS
        if 'hsts' in title_lower or 'strict-transport' in title_lower:
            return IssueSolution(
                code_snippet='''# Apache (.htaccess):
<IfModule mod_headers.c>
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
</IfModule>

# Nginx (server{} Block):
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# WordPress (wp-config.php):
// HSTS wird durch den Webserver gesetzt, nicht WordPress''',
                steps=[
                    '1. Öffnen Sie Ihre Webserver-Konfiguration (.htaccess für Apache oder nginx.conf)',
                    '2. Fügen Sie den HSTS-Header in den jeweiligen Abschnitt ein (siehe Code oben)',
                    '3. Bei Cloudflare/CDN: Aktivieren Sie HSTS unter SSL/TLS → Edge Certificates → HSTS',
                    '4. Testen Sie mit: https://securityheaders.com — "Strict-Transport-Security" muss grün sein',
                    '5. Wichtig: Stellen Sie sicher, dass Ihre Website vollständig via HTTPS erreichbar ist, bevor Sie HSTS aktivieren'
                ]
            )
        
        # CSP
        if 'csp' in title_lower or 'content-security-policy' in title_lower:
            return IssueSolution(
                code_snippet='''# Apache (.htaccess):
<IfModule mod_headers.c>
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://trusted-cdn.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https://fonts.googleapis.com; connect-src 'self'; frame-ancestors 'none'"
</IfModule>

# Nginx:
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; frame-ancestors 'none'" always;''',
                steps=[
                    '1. Analysieren Sie Ihre Website: Welche externen Ressourcen (Fonts, Scripts, CDN) werden geladen?',
                    '2. Beginnen Sie mit einem Report-Only Header: Content-Security-Policy-Report-Only um zu testen',
                    '3. Passen Sie den CSP-Header an Ihre Website an (erlaubte Domains eintragen)',
                    '4. Aktivieren Sie den Header in .htaccess (Apache) oder nginx.conf',
                    '5. Testen Sie mit https://csp-evaluator.withgoogle.com und Browser-DevTools → Console',
                    '6. Bei WordPress: Plugin "WP Content Security Policy" vereinfacht die Konfiguration'
                ]
            )
        
        # X-Frame-Options
        if 'x-frame' in title_lower or 'frame' in title_lower or 'clickjacking' in title_lower:
            return IssueSolution(
                code_snippet='''# Apache (.htaccess):
<IfModule mod_headers.c>
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Permissions-Policy "camera=(), microphone=(), geolocation=()"
</IfModule>

# Nginx:
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;''',
                steps=[
                    '1. Öffnen Sie die .htaccess Datei im Root-Verzeichnis Ihrer Website',
                    '2. Fügen Sie den Code-Block innerhalb des <IfModule mod_headers.c> Blocks ein',
                    '3. Speichern und testen Sie mit https://securityheaders.com',
                    '4. Überprüfen Sie, ob Ihre Website noch korrekt in iFrames dargestellt werden muss (selten)',
                    '5. Bei Nginx: Fügen Sie die add_header Zeilen in den server{} Block ein'
                ]
            )
        
        # Alle Security-Header auf einmal
        return IssueSolution(
            code_snippet='''# Vollständige Security-Headers (.htaccess):
<IfModule mod_headers.c>
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Permissions-Policy "camera=(), microphone=(), geolocation=()"
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com"
</IfModule>''',
            steps=[
                '1. Öffnen Sie die .htaccess im Root-Verzeichnis Ihrer Website (oder FTP/cPanel Dateimanager)',
                '2. Kopieren Sie den gesamten Code-Block und fügen Sie ihn am Ende der .htaccess ein',
                '3. Passen Sie den CSP an Ihre verwendeten Dienste an (Google Fonts, Analytics, etc.)',
                '4. Speichern und prüfen Sie mit https://securityheaders.com — alle Header müssen grün sein',
                '5. Bei Nginx: Übersetzen Sie die Header-Zeilen in add_header Direktiven im server{} Block'
            ]
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UWG (Bewertungen, Irreführung, Dark Patterns)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if category == 'uwg' or 'uwg' in title_lower:
        # Kundenbewertungen ohne Verifikation
        if 'bewertung' in title_lower or 'verifikation' in title_lower or 'disclosure' in title_lower or '35b' in title_lower:
            return IssueSolution(
                code_snippet='''<!-- Bewertungs-Disclosure nach §35b UWG -->
<div class="reviews-section">
  <div class="reviews-disclosure" style="background:#f8f9fa; border:1px solid #dee2e6; padding:12px 16px; border-radius:6px; margin-bottom:16px; font-size:0.875rem; color:#495057;">
    <strong>Bewertungshinweis:</strong> Alle Bewertungen stammen von verifizierten Käufern, 
    die das Produkt über unseren Shop erworben haben. 
    Wir prüfen Echtheit durch Bestellabgleich. 
    <a href="/bewertungsrichtlinie" style="color:#0066cc;">Mehr zu unserem Bewertungsverfahren</a>
  </div>
  <!-- Ihre bestehenden Bewertungen hier -->
</div>''',
                steps=[
                    '1. Fügen Sie direkt oberhalb Ihrer Bewertungssektion den Disclosure-Text ein',
                    '2. Erstellen Sie eine Seite /bewertungsrichtlinie mit Ihrem Prüfverfahren',
                    '3. Beschreiben Sie konkret: Wie werden Bewertungen verifiziert? (z.B. Bestellnummer-Abgleich)',
                    '4. Wenn Sie Trustpilot/Google verwenden: Linken Sie auf deren Verifizierungsseite',
                    '5. Entfernen Sie alle künstlichen Countdowns oder Lagerbestands-Anzeigen die nicht real sind',
                    '6. Rechtslage: §35b UWG seit Mai 2022 — Bußgeld bis 50.000€'
                ]
            )
        
        # Irreführende Werbung / Dringlichkeit
        if 'irreführ' in title_lower or 'dringlichkeit' in title_lower or 'countdown' in title_lower:
            return IssueSolution(
                code_snippet='''<!-- ENTFERNEN: Statische/gefälschte Countdown-Timer -->
<!-- <div class="countdown">Nur noch 2:34 Minuten!</div> -->

<!-- ERSETZEN durch echte serverseitige Logik (falls Angebot wirklich endet): -->
<div class="offer-end" data-end-time="{{ offer_end_timestamp }}">
  Angebot endet: <span class="real-end-date">{{ formatted_date }}</span>
</div>

<!-- Lagerbestand: Nur anzeigen wenn real und dynamisch -->
<div class="stock-info">
  <!-- Nur wenn tatsächlich < 10 Stück vorhanden: -->
  <span class="stock-warning">Nur noch {{ real_stock_count }} auf Lager</span>
</div>''',
                steps=[
                    '1. Entfernen Sie alle statischen Countdown-Timer, die sich nicht wirklich ändern',
                    '2. Lagerbestand-Anzeigen müssen dem echten Lagerbestand entsprechen — statische "Nur noch 3!" Angaben entfernen',
                    '3. Rabattpreise müssen dem günstigsten Preis der letzten 30 Tage entsprechen (§11 PAngV)',
                    '4. Kaufdruck-Elemente ("5 Personen schauen sich das gerade an") entfernen wenn nicht real',
                    '5. Siegel und Auszeichnungen nur anzeigen wenn aktuell und mit Prüfbericht verlinkbar'
                ]
            )
        
        return IssueSolution(
            code_snippet='''<!-- UWG-Compliance: Bewertungs-Disclosure -->
<p class="reviews-note" style="font-size:0.8rem; color:#666; margin-top:8px;">
  * Nur verifizierte Käufer können Bewertungen abgeben. 
  <a href="/bewertungsrichtlinie">Mehr Infos</a>
</p>''',
            steps=[
                '1. Prüfen Sie alle Bewertungen: Sind diese von verifizierten Käufern? (§35b UWG)',
                '2. Erstellen Sie eine Bewertungsrichtlinie-Seite und verlinken Sie diese bei Bewertungen',
                '3. Entfernen Sie gefälschte Dringlichkeitselemente (statische Countdowns, erfundene Lagerbestände)',
                '4. Bezahlte Inhalte/Kooperationen mit "Anzeige" oder "Gesponsert" kennzeichnen',
                '5. Günstigsten Preis der letzten 30 Tage bei Rabattaktionen anzeigen'
            ]
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PREISANGABEN (PAngV)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if category == 'preisangaben' or 'preis' in title_lower or 'pangv' in title_lower or 'mwst' in title_lower or 'versand' in title_lower:
        if 'grundpreis' in title_lower:
            return IssueSolution(
                code_snippet='''<!-- Grundpreisangabe nach §4 PAngV -->
<div class="product-price">
  <span class="price">3,49 €</span>
  <span class="base-price" style="font-size:0.85rem; color:#555;">
    (= 6,98 € / 100 g)
  </span>
  <span class="tax-shipping" style="font-size:0.8rem; color:#777;">
    inkl. MwSt. | zzgl. <a href="/versand">Versandkosten</a>
  </span>
</div>''',
                steps=[
                    '1. Berechnen Sie den Grundpreis: Produktpreis ÷ Menge × Bezugsgröße (100g, 100ml, 1l, etc.)',
                    '2. Zeigen Sie den Grundpreis direkt neben dem Verkaufspreis an',
                    '3. Schriftgröße: Grundpreis muss gut lesbar sein (mind. 75% der Produktpreis-Schriftgröße)',
                    '4. Gilt für alle Waren nach Gewicht, Volumen, Länge, Fläche',
                    '5. Bei WooCommerce: Plugin "WooCommerce Unit Measurements" oder "German Market" nutzen'
                ]
            )
        return IssueSolution(
            code_snippet='''<!-- Korrektes Preis-HTML nach PAngV -->
<div class="product-price">
  <strong class="price">29,99 €</strong>
  <small class="tax-info"> inkl. MwSt.</small>
  <small class="shipping">
    zzgl. <a href="/versandkosten">Versandkosten</a>
  </small>
</div>

<!-- Bei Rabatten: 30-Tage-Tiefstpreis anzeigen (§11 PAngV) -->
<div class="price-discount">
  <del class="was-price">39,99 €</del>
  <strong class="now-price">29,99 €</strong>
  <small class="reference-price">
    Bester Preis letzte 30 Tage: 34,99 €
  </small>
</div>''',
            steps=[
                '1. Fügen Sie bei jedem Preis "inkl. MwSt." hinzu (§3 PAngV Pflicht)',
                '2. Verlinken Sie "zzgl. Versandkosten" auf eine eigene Versandkostenseite',
                '3. Bei Mengenware (kg/l/m): Grundpreis direkt neben dem Preis anzeigen (§4 PAngV)',
                '4. Bei Rabattpreisen: Den günstigsten Preis der letzten 30 Tage als Referenz angeben (§11 PAngV)',
                '5. Prüfen Sie alle Produktseiten — auch im Warenkorb und der Bestellübersicht'
            ]
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AGB
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if category == 'agb' or 'agb' in title_lower or 'allgemeine geschäft' in title_lower:
        return IssueSolution(
            code_snippet='''<!-- AGB: Footer-Link -->
<footer>
  <nav>
    <a href="/agb">AGB</a>
    <a href="/widerrufsbelehrung">Widerruf</a>
    <a href="/impressum">Impressum</a>
    <a href="/datenschutz">Datenschutz</a>
  </nav>
</footer>

<!-- Checkout: AGB-Checkbox (Pflicht) -->
<form>
  <label>
    <input type="checkbox" name="agb_accepted" required>
    Ich akzeptiere die <a href="/agb" target="_blank">AGB</a>
    und die <a href="/widerrufsbelehrung" target="_blank">Widerrufsbelehrung</a>
  </label>
</form>''',
            steps=[
                '1. Erstellen Sie eine /agb Seite mit Ihren vollständigen AGB',
                '2. Verlinken Sie die AGB im Footer und im Bestellprozess',
                '3. Im Checkout: Pflicht-Checkbox "Ich akzeptiere die AGB" einbauen',
                '4. Senden Sie AGB per E-Mail mit jeder Bestellbestätigung mit',
                '5. Lassen Sie die AGB von einem Rechtsanwalt prüfen (juristische Prüfung empfohlen)'
            ]
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # WIDERRUFSBELEHRUNG
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if category == 'widerruf' or category == 'widerrufsbelehrung' or 'widerruf' in title_lower:
        return IssueSolution(
            code_snippet='''<!-- Widerrufsbelehrung: Footer-Link -->
<a href="/widerrufsbelehrung">Widerrufsrecht & Muster-Widerrufsformular</a>

<!-- Widerrufsbelehrung Seite /widerrufsbelehrung -->
<h1>Widerrufsbelehrung</h1>
<p><strong>Widerrufsrecht:</strong> Sie haben das Recht, binnen 14 Tagen 
ohne Angabe von Gründen diesen Vertrag zu widerrufen.</p>
<p>Widerruf per E-Mail an: <a href="mailto:widerruf@ihrshop.de">widerruf@ihrshop.de</a></p>
<h2>Muster-Widerrufsformular</h2>
<p>An [Firma, Adresse, E-Mail]:<br>
Ich widerrufe meinen Vertrag vom [Datum].<br>
Name / Datum / Unterschrift</p>''',
            steps=[
                '1. Erstellen Sie eine Seite /widerrufsbelehrung mit der gesetzlichen Muster-Belehrung',
                '2. Verlinken Sie die Seite im Footer und in Bestellbestätigungs-E-Mails',
                '3. Fügen Sie das Muster-Widerrufsformular als ausfüllbares Formular oder PDF ein',
                '4. Senden Sie die Widerrufsbelehrung automatisch mit jeder Bestellbestätigung',
                '5. Bei digitalen Produkten: Hinweis auf Erlöschen des Widerrufsrechts bei sofortigem Download'
            ]
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AVV (Auftragsverarbeitungsvertrag)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if category == 'avv' or 'avv' in title_lower or 'auftragsverarbeit' in title_lower or 'datenverarbeit' in title_lower:
        return IssueSolution(
            code_snippet='''<!-- Datenschutzerklärung: Auftragsverarbeiter nennen -->
<h2>Auftragsverarbeitung</h2>
<p>Für folgende Dienste haben wir einen Auftragsverarbeitungsvertrag (AVV) gemäß 
Art. 28 DSGVO abgeschlossen:</p>
<ul>
  <li><strong>Google Analytics 4:</strong> AVV abgeschlossen, 
      <a href="https://myaccount.google.com/data-and-privacy">Google Data Processing Terms</a></li>
  <li><strong>Mailchimp:</strong> AVV abgeschlossen,
      <a href="https://mailchimp.com/legal/data-processing-addendum/">Mailchimp DPA</a></li>
  <!-- Weitere Dienste hier ergänzen -->
</ul>''',
            steps=[
                '1. Google Analytics/GTM: AVV abschließen unter myaccount.google.com → Datenschutz → Datenverarbeitungsbedingungen',
                '2. Meta/Facebook Pixel: DPA unter facebook.com/legal/terms/dataprocessing abschließen',
                '3. E-Mail-Dienste (Mailchimp, Klaviyo etc.): DPA in den Account-Einstellungen aktivieren',
                '4. Hosting-Anbieter: AVV-Vorlage beim Anbieter anfordern (meist im Kundenportal)',
                '5. Dokumentieren Sie alle AVVs in Ihrer Datenschutzerklärung und im Verarbeitungsverzeichnis'
            ]
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BARRIEREFREIHEIT (BFSG/WCAG)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if category == 'barrierefreiheit':
        # H1-Überschrift fehlt
        if 'h1' in title_lower or 'überschrift' in title_lower or 'heading' in title_lower:
            return IssueSolution(
                code_snippet='''<!-- H1 in den <head> Bereich der Seite einfügen -->
<main>
  <h1>Ihr Seitenthema hier — z.B. "Herzlich Willkommen bei [Firmenname]"</h1>
  <!-- Weitere Inhalte -->
</main>

<!-- Hierarchie: Nur EINE H1 pro Seite, dann H2, H3... -->
<h1>Hauptüberschrift</h1>
  <h2>Unterabschnitt 1</h2>
    <h3>Detail</h3>
  <h2>Unterabschnitt 2</h2>''',
                steps=[
                    '1. Fügen Sie eine H1-Überschrift als erste Überschrift im <main> Element ein',
                    '2. Die H1 muss das Hauptthema der Seite präzise beschreiben',
                    '3. Verwenden Sie auf jeder Seite genau eine H1',
                    '4. Weitere Überschriften hierarchisch strukturieren (H2 → H3 → H4)',
                    '5. Bei CMS (WordPress/Shopware): Prüfen Sie den Seiteneditor — Titel = H1',
                    '6. Testen mit: Browser DevTools → Accessibility Tab → Headings'
                ]
            )
        
        # Semantische HTML-Elemente fehlen
        if 'semantisch' in title_lower or 'html5' in title_lower or 'landmark' in title_lower:
            return IssueSolution(
                code_snippet='''<!-- Semantische Struktur: Ersetzen Sie divs durch semantische Elemente -->
<header role="banner">
  <nav aria-label="Hauptnavigation">
    <ul>
      <li><a href="/">Startseite</a></li>
      <li><a href="/produkte">Produkte</a></li>
      <li><a href="/kontakt">Kontakt</a></li>
    </ul>
  </nav>
</header>

<main id="main-content">
  <a href="#main-content" class="skip-link">Zum Inhalt springen</a>
  <h1>Seitenüberschrift</h1>
  <article>
    <h2>Artikel-Überschrift</h2>
  </article>
</main>

<footer role="contentinfo">
  <nav aria-label="Footer-Navigation"><!-- Links --></nav>
</footer>''',
                steps=[
                    '1. Ersetzen Sie <div id="header"> durch <header role="banner">',
                    '2. Ersetzen Sie <div id="nav"> durch <nav aria-label="Hauptnavigation">',
                    '3. Ersetzen Sie <div id="content"> durch <main id="main-content">',
                    '4. Ersetzen Sie <div id="footer"> durch <footer role="contentinfo">',
                    '5. Fügen Sie einen Skip-Link als erstes Element in <main> ein',
                    '6. Testen mit NVDA (Windows) oder VoiceOver (Mac/iPhone)'
                ]
            )
        
        # Alt-Texte fehlen
        if 'alt' in title_lower or 'bild' in title_lower or 'img' in title_lower:
            return IssueSolution(
                code_snippet='''<!-- Bilder mit Alt-Text: Beschreibend und aussagekräftig -->
<img src="produkt-sneaker-blau.jpg" 
     alt="Blauer Nike Sneaker Air Max 270, Größe 42, Seitenansicht">

<!-- Dekorative Bilder: Leeres alt="" damit Screenreader ignoriert -->
<img src="trennlinie.png" alt="" role="presentation">

<!-- Verlinktes Bild: Alt-Text beschreibt das Ziel -->
<a href="/">
  <img src="logo.png" alt="Firmenname - Zurück zur Startseite">
</a>

<!-- Komplexe Grafiken: Zusätzliche Beschreibung -->
<figure>
  <img src="diagramm.png" alt="Umsatzentwicklung 2024">
  <figcaption>Umsatz stieg von 100k€ (Jan) auf 180k€ (Dez) — +80% Wachstum</figcaption>
</figure>''',
                steps=[
                    '1. Fügen Sie jedem <img> ein alt-Attribut hinzu — leer ("") für dekorative Bilder',
                    '2. Alt-Texte beschreiben: Was zeigt das Bild? Was ist der Zweck?',
                    '3. Für Produktbilder: Produktname + Farbe + relevante Details',
                    '4. Für Icons/Buttons: Das Ziel/die Funktion beschreiben (z.B. alt="Warenkorb öffnen")',
                    '5. Bei WordPress: Alle Bilder in der Mediathek → Alt-Text Feld ausfüllen',
                    '6. Bulk-Fix: Browser-Plugin "alt-text-tester" zeigt alle fehlenden Alt-Texte'
                ]
            )
        
        # Kontraste
        if 'kontrast' in title_lower or 'farb' in title_lower or 'color' in title_lower:
            return IssueSolution(
                code_snippet='''/* CSS: Ausreichende Farbkontraste (WCAG 2.1 Level AA) */

/* Normaler Text: Mindest-Kontrast 4.5:1 */
.body-text {
  color: #333333;        /* #333 auf Weiß = 12.6:1 ✓ */
  background: #ffffff;
}

/* Großer Text (>18pt): Mindest-Kontrast 3:1 */
.heading-large {
  color: #555555;        /* #555 auf Weiß = 7.5:1 ✓ */
  background: #ffffff;
}

/* FALSCH: Grauer Text auf weißem Hintergrund */
/* color: #999999;  →  nur 2.85:1 — NICHT WCAG-konform! */

/* RICHTIG: Mindestens #767676 für normalen Text auf Weiß */
.muted-text {
  color: #767676;        /* = 4.54:1 — gerade noch WCAG AA ✓ */
}''',
                steps=[
                    '1. Prüfen Sie alle Text-/Hintergrundfarben mit: https://webaim.org/resources/contrastchecker/',
                    '2. Normaler Text braucht min. 4.5:1 Kontrast, großer Text (>18pt/14pt fett) min. 3:1',
                    '3. Häufige Problemstelle: Hellgrauer Text (#999, #aaa) auf weiß — anpassen auf min. #767676',
                    '4. Buttons und Links: Auch Hover/Focus-Zustand prüfen',
                    '5. CSS-Farben anpassen und erneut mit Contrast-Checker verifizieren',
                    '6. Browser-Extension "WAVE" zeigt Kontrast-Fehler direkt auf Ihrer Website'
                ]
            )
        
        # Tastatur-Navigation
        if 'tastatur' in title_lower or 'keyboard' in title_lower or 'focus' in title_lower or 'tab' in title_lower:
            return IssueSolution(
                code_snippet='''/* CSS: Sichtbare Focus-Indikatoren (WCAG 2.1 §2.4.7) */
:focus-visible {
  outline: 3px solid #005fcc;
  outline-offset: 3px;
  border-radius: 3px;
}

/* Skip-Link für Tastatur-Nutzer */
.skip-link {
  position: absolute;
  top: -100%;
  left: 16px;
  background: #005fcc;
  color: white;
  padding: 8px 16px;
  border-radius: 0 0 4px 4px;
  font-weight: 600;
  z-index: 9999;
  transition: top 0.1s;
}
.skip-link:focus {
  top: 0;
}

/* HTML: Skip-Link als erstes Element im <body> */
/* <a href="#main-content" class="skip-link">Zum Hauptinhalt springen</a> */''',
                steps=[
                    '1. Fügen Sie den CSS-Code für :focus-visible in Ihre globale CSS-Datei ein',
                    '2. Entfernen Sie keinesfalls "outline: none" oder "outline: 0" aus Ihrem CSS',
                    '3. Fügen Sie den Skip-Link als erstes Element im <body> ein',
                    '4. Testen: Tab-Taste drücken — jedes fokussierte Element muss sichtbar hervorgehoben sein',
                    '5. Prüfen Sie: Können Sie alle Funktionen (Navigation, Formulare, Buttons) nur per Tastatur erreichen?'
                ]
            )
        
        # ARIA-Labels
        if 'aria' in title_lower or 'label' in title_lower or 'role' in title_lower:
            return IssueSolution(
                code_snippet='''<!-- ARIA-Labels für Screenreader-Zugänglichkeit -->

<!-- Buttons ohne sichtbaren Text: aria-label hinzufügen -->
<button aria-label="Produkt in den Warenkorb legen">
  <svg aria-hidden="true"><!-- Warenkorb-Icon --></svg>
</button>

<!-- Navigationen benennen -->
<nav aria-label="Hauptnavigation"><!-- ... --></nav>
<nav aria-label="Breadcrumb" aria-current="page"><!-- ... --></nav>

<!-- Formulare: Labels für alle Eingabefelder -->
<label for="email">E-Mail-Adresse *</label>
<input type="email" id="email" name="email" 
       aria-required="true" 
       aria-describedby="email-hint">
<p id="email-hint">Format: name@beispiel.de</p>

<!-- Modals/Dialoge -->
<div role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <h2 id="modal-title">Bestätigung</h2>
</div>''',
                steps=[
                    '1. Alle Buttons mit nur Icons/SVGs brauchen ein aria-label das die Funktion beschreibt',
                    '2. Navigationen mit aria-label benennen (Hauptnavigation, Breadcrumb, Footer-Navigation)',
                    '3. Jedes Formularfeld braucht ein zugehöriges <label> mit for-Attribut',
                    '4. Alle Icons in Buttons: aria-hidden="true" damit Screenreader sie ignoriert',
                    '5. Testen: Browser-Plugin WAVE oder Axe DevTools zeigt alle ARIA-Fehler an'
                ]
            )
        
        # Fehlender Sprachcode
        if 'sprach' in title_lower or 'lang' in title_lower or 'html lang' in title_lower:
            return IssueSolution(
                code_snippet='''<!-- HTML lang-Attribut im <html> Tag setzen -->
<!DOCTYPE html>
<html lang="de">  <!-- Deutsch -->
<!-- oder: lang="en" (Englisch), lang="fr" (Französisch) etc. -->
<head>
  <!-- ... -->
</head>

<!-- Bei mehrsprachigen Inhalten: lang lokal überschreiben -->
<p>Das ist auf Deutsch.</p>
<p lang="en">This is in English.</p>''',
                steps=[
                    '1. Öffnen Sie Ihre HTML-Vorlage / Template-Datei',
                    '2. Setzen Sie im <html> Tag das lang-Attribut: <html lang="de">',
                    '3. Bei WordPress: Theme-Einstellungen → Sprache, oder in der header.php',
                    '4. Bei anderssprachigen Textpassagen: lang-Attribut am betreffenden Element setzen',
                    '5. Testen: HTML-Validator auf https://validator.w3.org prüft das lang-Attribut'
                ]
            )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DATENSCHUTZ / DSGVO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if category == 'datenschutz' or 'datenschutz' in title_lower or 'dsgvo' in title_lower or 'gdpr' in title_lower:
        if 'google analytics' in title_lower or 'tracking' in title_lower or 'pixel' in title_lower:
            return IssueSolution(
                code_snippet='''<!-- Google Analytics 4: Nur nach Einwilligung laden -->
<!-- FALSCH: Direkt im <head> laden -->
<!-- <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXX"></script> -->

<!-- RICHTIG: Erst nach Cookie-Consent laden -->
<script>
  // Wird vom Cookie-Consent-Banner aufgerufen wenn Nutzer zustimmt
  function loadGoogleAnalytics() {
    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=G-IHRE-ID';
    document.head.appendChild(script);
    
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-IHRE-ID', {
      'anonymize_ip': true,  // IP-Anonymisierung aktivieren
      'storage': 'none'      // Kein Storage ohne Einwilligung
    });
  }
</script>''',
                steps=[
                    '1. Entfernen Sie den direkten Google Analytics / GTM Script-Tag aus dem <head>',
                    '2. Laden Sie GA/GTM nur nach expliziter Einwilligung im Cookie-Banner',
                    '3. In Google Analytics: IP-Anonymisierung aktivieren (Analytics → Admin → Datenstrom → Tagging-Einstellungen)',
                    '4. AVV mit Google abschließen: myaccount.google.com → Datenschutz → Datenverarbeitung',
                    '5. Datenschutzerklärung: Google Analytics mit Rechtsgrundlage (Einwilligung Art. 6 Abs. 1a DSGVO) dokumentieren'
                ]
            )
        
        return IssueSolution(
            code_snippet='''<!-- Datenschutzerklärung Footer-Link -->
<footer>
  <a href="/datenschutz" rel="privacy-policy">Datenschutzerklärung</a>
</footer>''',
            steps=[
                '1. Erstellen Sie eine Datenschutzerklärung-Seite unter /datenschutz',
                '2. Dokumentieren Sie alle Datenverarbeitungen: Hosting, Analytics, Kontaktformular, E-Mail',
                '3. Verlinken Sie die Datenschutzerklärung im Footer jeder Seite',
                '4. Nutzen Sie den Complyo Datenschutz-Generator für eine DSGVO-konforme Vorlage',
                '5. Aktualisieren Sie die Erklärung bei neuen Diensten (z.B. neues Plugin, Social-Media-Integration)'
            ]
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # IMPRESSUM
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if category == 'impressum' or 'impressum' in title_lower:
        return IssueSolution(
            code_snippet='''<!-- Impressum Footer-Link (Pflicht auf jeder Seite) -->
<footer>
  <nav aria-label="Rechtliche Links">
    <a href="/impressum" rel="legal">Impressum</a>
    <a href="/datenschutz" rel="privacy-policy">Datenschutz</a>
  </nav>
</footer>

<!-- Impressum-Seite /impressum (Pflichtangaben §5 TMG / §18 MStV) -->
<h1>Impressum</h1>
<h2>Angaben gemäß § 5 TMG</h2>
<address>
  Ihr Firmenname GmbH<br>
  Musterstraße 1<br>
  12345 Musterstadt<br>
  <br>
  E-Mail: <a href="mailto:kontakt@ihreshop.de">kontakt@ihreshop.de</a><br>
  Tel: +49 123 456789
</address>
<h2>Handelsregister</h2>
<p>HRB 12345, Amtsgericht Musterstadt</p>
<h2>Umsatzsteuer-ID</h2>
<p>DE123456789</p>''',
            steps=[
                '1. Erstellen Sie eine Seite unter /impressum',
                '2. Pflichtangaben: Name + Anschrift + E-Mail + Telefon (§5 TMG)',
                '3. Bei GmbH/AG: Handelsregisternummer + Amtsgericht + Geschäftsführer angeben',
                '4. Verlinken Sie das Impressum im Footer von jeder Seite (max. 2 Klicks)',
                '5. Nutzen Sie den Complyo Impressum-Generator für alle Pflichtangaben'
            ]
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # COOKIES / CONSENT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if category == 'cookies' or 'cookie' in title_lower or 'consent' in title_lower or 'ttdsg' in title_lower:
        if 'third-party' in title_lower or 'drittanbieter' in title_lower or 'social' in title_lower or 'embed' in title_lower:
            return IssueSolution(
                code_snippet='''<!-- Zwei-Klick-Lösung für YouTube-Embeds -->
<div class="embed-placeholder" data-src="https://www.youtube-nocookie.com/embed/VIDEO_ID">
  <div style="background:#000; color:#fff; padding:40px; text-align:center; border-radius:8px;">
    <p>YouTube-Video<br><small>Durch Klick werden Daten an YouTube übertragen</small></p>
    <button onclick="loadEmbed(this)" 
            style="background:#ff0000; color:white; border:none; padding:12px 24px; cursor:pointer; border-radius:4px;">
      Video laden (Datenschutzhinweis beachten)
    </button>
  </div>
</div>

<script>
function loadEmbed(btn) {
  const container = btn.closest('.embed-placeholder');
  const src = container.dataset.src;
  container.innerHTML = '<iframe src="' + src + '" allowfullscreen width="100%" height="400" loading="lazy"></iframe>';
}
</script>''',
                steps=[
                    '1. Ersetzen Sie direkte YouTube/Vimeo-Embeds durch Platzhalter mit Klick-Freigabe',
                    '2. Verwenden Sie youtube-nocookie.com statt youtube.com für datenschutzfreundlichere Embeds',
                    '3. Social-Media-Buttons: Shariff-Lösung verwenden statt direkte Facebook/Twitter Buttons',
                    '4. Bei WordPress: Plugin "DSGVO Video-Einbettung" oder "Borlabs Cookie" nutzen',
                    '5. Datenschutzerklärung: Eingebettete Inhalte und Drittzugriffe dokumentieren'
                ]
            )
        
        return IssueSolution(
            code_snippet='''<!-- Cookie-Banner Integration (Complyo) -->
<script>
  // Option A: Complyo Cookie-Banner nutzen (im AI-Plan enthalten)
  // Gehen Sie zu: App → Cookie-Compliance → Banner konfigurieren
  
  // Option B: Minimaler eigener Cookie-Banner
  if (!localStorage.getItem('cookie_consent')) {
    document.addEventListener('DOMContentLoaded', function() {
      const banner = document.createElement('div');
      banner.innerHTML = `
        <div style="position:fixed;bottom:0;left:0;right:0;background:#1a1a1a;color:#fff;padding:16px 24px;z-index:99999;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;">
          <p style="margin:0;font-size:14px;">
            Diese Website verwendet Cookies für Analytics und Funktionalität. 
            <a href="/datenschutz" style="color:#60a5fa;">Mehr erfahren</a>
          </p>
          <div style="display:flex;gap:8px;">
            <button onclick="setCookieConsent('rejected')" style="padding:8px 16px;border:1px solid #555;background:transparent;color:#fff;cursor:pointer;border-radius:4px;">Ablehnen</button>
            <button onclick="setCookieConsent('accepted')" style="padding:8px 16px;background:#2563eb;border:none;color:#fff;cursor:pointer;border-radius:4px;font-weight:600;">Akzeptieren</button>
          </div>
        </div>`;
      document.body.appendChild(banner);
    });
  }
  
  function setCookieConsent(value) {
    localStorage.setItem('cookie_consent', value);
    document.querySelector('[style*="position:fixed;bottom:0"]').remove();
    if (value === 'accepted') { /* Tracking laden */ }
  }
</script>''',
            steps=[
                '1. Empfehlung: Nutzen Sie die integrierte Complyo Cookie-Lösung (App → Cookie-Compliance)',
                '2. Der Banner muss VOR dem Laden von Tracking-Cookies erscheinen',
                '3. Tracking-Scripts (GA, Meta Pixel) dürfen NUR nach Einwilligung geladen werden',
                '4. Opt-out muss genauso einfach sein wie Opt-in (gleiche Anzahl Klicks)',
                '5. Jährlich re-consent einholen oder bei wesentlichen Änderungen',
                '6. Dokumentieren Sie alle gesetzten Cookies in der Datenschutzerklärung'
            ]
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SSL / HTTPS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if 'ssl' in title_lower or 'https' in title_lower or 'tls' in title_lower or 'verschlüssel' in title_lower:
        return IssueSolution(
            code_snippet='''# HTTP → HTTPS Redirect (.htaccess):
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]

# Nginx:
server {
    listen 80;
    server_name ihredomain.de www.ihredomain.de;
    return 301 https://$server_name$request_uri;
}

# www → non-www Redirect (optional):
RewriteCond %{HTTP_HOST} ^www\.(.*)$ [NC]
RewriteRule ^(.*)$ https://%1/$1 [R=301,L]''',
            steps=[
                '1. Stellen Sie sicher, dass ein SSL-Zertifikat installiert ist (kostenlos bei Let\'s Encrypt)',
                '2. Bei Hosting-Anbieter: SSL-Zertifikat im Control Panel aktivieren (meist 1-Klick)',
                '3. Fügen Sie den HTTP→HTTPS Redirect in die .htaccess (Apache) oder nginx.conf ein',
                '4. Aktualisieren Sie alle internen Links von http:// auf https:// oder relative Pfade',
                '5. Testen Sie mit: https://www.ssllabs.com/ssltest/ — Ziel ist Grade A'
            ]
        )
    
    # Fallback für andere Kategorien
    return _generate_solution(category)

def _generate_solution(category: str) -> IssueSolution:
    """Generiert Lösungsvorschläge basierend auf Kategorie"""
    solutions = {
        'impressum': IssueSolution(
            code_snippet='<footer>\n  <a href="/impressum" rel="legal">Impressum</a>\n  <a href="/datenschutz" rel="privacy-policy">Datenschutz</a>\n</footer>',
            steps=[
                '1. Erstelle eine Impressum-Seite unter /impressum mit allen Pflichtangaben (§5 TMG)',
                '2. Pflichtangaben: Firmenname, Adresse, E-Mail, Telefon — bei GmbH/AG auch Handelsregisternummer',
                '3. Verlinke das Impressum im Footer jeder Seite (max. 2 Klicks erreichbar)',
                '4. Nutze den Complyo Impressum-Generator für eine rechtssichere Vorlage'
            ]
        ),
        'datenschutz': IssueSolution(
            code_snippet='<footer>\n  <a href="/datenschutz" rel="privacy-policy">Datenschutzerklärung</a>\n</footer>',
            steps=[
                '1. Erstelle eine Datenschutzseite unter /datenschutz',
                '2. Dokumentiere alle Datenverarbeitungen: Hosting, Analytics, Cookies, Kontaktformular',
                '3. Verlinke die Datenschutzerklärung im Footer jeder Seite',
                '4. Nutze den Complyo Datenschutz-Generator für eine DSGVO-konforme Vorlage'
            ]
        ),
        'cookies': IssueSolution(
            code_snippet='<!-- Complyo Cookie-Banner: App → Cookie-Compliance → Banner konfigurieren -->\n<!-- Alternativ: Eigenen Banner vor Tracking-Scripts einbinden -->',
            steps=[
                '1. Nutze die integrierte Complyo Cookie-Lösung: App → Cookie-Compliance',
                '2. Cookie-Banner muss vor dem Laden von Tracking-Cookies erscheinen',
                '3. Tracking-Scripts (GA, Meta Pixel) erst nach Einwilligung laden',
                '4. Opt-out genauso einfach wie Opt-in gestalten'
            ]
        ),
        'barrierefreiheit': IssueSolution(
            code_snippet='<!-- WCAG 2.1 Basis -->\n<img src="bild.jpg" alt="Beschreibung des Bildinhalts">\n<button aria-label="Menü öffnen">Menu</button>\n<a href="#main" class="skip-link">Zum Inhalt springen</a>',
            steps=[
                '1. Alt-Texte: Füge jedem <img> ein aussagekräftiges alt-Attribut hinzu',
                '2. Kontraste: Mind. 4.5:1 für Text — prüfen auf webaim.org/resources/contrastchecker',
                '3. Tastatur: Alle interaktiven Elemente per Tab erreichbar, :focus-visible CSS hinzufügen',
                '4. Testen mit WAVE Browser Extension oder axe DevTools'
            ]
        ),
        'security': IssueSolution(
            code_snippet='# Apache .htaccess:\n<IfModule mod_headers.c>\n    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"\n    Header always set X-Content-Type-Options "nosniff"\n    Header always set X-Frame-Options "SAMEORIGIN"\n</IfModule>',
            steps=[
                '1. Füge Security-Header in die .htaccess (Apache) oder nginx.conf ein',
                '2. Aktiviere HTTPS mit kostenlosem Let\'s Encrypt SSL-Zertifikat',
                '3. Teste alle Header mit: https://securityheaders.com',
                '4. Bei Cloudflare: Security-Header unter Rules → Transform Rules konfigurieren'
            ]
        ),
        'uwg': IssueSolution(
            code_snippet='<!-- Bewertungs-Disclosure nach §35b UWG -->\n<p class="reviews-note">\n  * Alle Bewertungen stammen von verifizierten Käufern.\n  <a href="/bewertungsrichtlinie">Mehr erfahren</a>\n</p>',
            steps=[
                '1. Bewertungshinweis direkt bei Bewertungen einfügen (§35b UWG)',
                '2. Seite /bewertungsrichtlinie mit Prüfverfahren erstellen',
                '3. Statische Countdowns und erfundene Lagerbestands-Anzeigen entfernen',
                '4. Günstigsten Preis der letzten 30 Tage bei Rabatten anzeigen (§11 PAngV)'
            ]
        ),
        'preisangaben': IssueSolution(
            code_snippet='<!-- Preis nach PAngV -->\n<span class="price">29,99 €</span>\n<small> inkl. MwSt. | zzgl. <a href="/versand">Versandkosten</a></small>',
            steps=[
                '1. Bei jedem Preis "inkl. MwSt." ergänzen (§3 PAngV)',
                '2. Versandkosten als Link zu einer Versandkostenseite verlinken',
                '3. Bei Mengenware: Grundpreis direkt neben dem Preis anzeigen (§4 PAngV)',
                '4. Bei Rabatten: Günstigsten Preis der letzten 30 Tage als Referenz angeben (§11 PAngV)'
            ]
        ),
        'agb': IssueSolution(
            code_snippet='<footer>\n  <a href="/agb">AGB</a>\n  <a href="/widerrufsbelehrung">Widerruf</a>\n</footer>',
            steps=[
                '1. AGB-Seite unter /agb erstellen und im Footer verlinken',
                '2. Im Checkout: Pflicht-Checkbox "Ich akzeptiere die AGB" einbauen',
                '3. AGB per E-Mail mit jeder Bestellbestätigung mitsenden',
                '4. AGB von einem Rechtsanwalt prüfen lassen (juristische Prüfung empfohlen)'
            ]
        ),
        'widerruf': IssueSolution(
            code_snippet='<footer>\n  <a href="/widerrufsbelehrung">Widerrufsrecht</a>\n</footer>',
            steps=[
                '1. Widerrufsbelehrung-Seite unter /widerrufsbelehrung erstellen',
                '2. Muster-Widerrufsformular als Bestandteil einbinden (BGB Anlage 2)',
                '3. Widerrufsbelehrung mit jeder Bestellbestätigung per E-Mail senden',
                '4. 14-tägige Widerrufsfrist korrekt kommunizieren'
            ]
        ),
        'widerrufsbelehrung': IssueSolution(
            code_snippet='<footer>\n  <a href="/widerrufsbelehrung">Widerrufsrecht</a>\n</footer>',
            steps=[
                '1. Widerrufsbelehrung-Seite unter /widerrufsbelehrung erstellen',
                '2. Muster-Widerrufsformular als Bestandteil einbinden (BGB Anlage 2)',
                '3. Widerrufsbelehrung mit jeder Bestellbestätigung per E-Mail senden',
                '4. 14-tägige Widerrufsfrist korrekt kommunizieren'
            ]
        ),
    }
    
    return solutions.get(
        category,
        IssueSolution(
            code_snippet=f'<!-- Fix für: {category} -->\n<!-- Spezifische Lösung wird basierend auf Ihrer Website-Analyse generiert -->',
            steps=[
                f'1. Analysieren Sie die spezifischen Anforderungen für "{category}"',
                '2. Klicken Sie auf "KI-Fix generieren" für eine auf Ihre Website zugeschnittene Lösung',
                '3. Implementieren Sie die empfohlenen Änderungen',
                '4. Führen Sie einen erneuten Scan durch, um die Behebung zu bestätigen'
            ]
        )
    )

async def _generate_mock_analysis(url: str, risk_calculator) -> AnalysisResponse:
    """
    Generate a mock analysis when the real scanner is not available
    
    This provides a fallback for demo purposes or when the scanner fails.
    """
    
    # FIXED: Deterministischer Pseudo-Random Generator basierend auf URL
    def seeded_value(seed: str, min_val: int, max_val: int) -> int:
        """Generiere deterministische Werte basierend auf Seed (URL)"""
        hash_val = 0
        for char in seed:
            hash_val = ((hash_val << 5) - hash_val) + ord(char)
            hash_val = hash_val & 0xFFFFFFFF  # 32-bit integer
        normalized = abs(hash_val) / 0xFFFFFFFF
        return int(normalized * (max_val - min_val + 1)) + min_val
    
    # Define common compliance issues (die 4 Säulen)
    all_issues = [
        "Es wurde kein Link zum Impressum gefunden. Dies ist gesetzlich verpflichtend.",
        "Es wurde keine Datenschutzerklärung gefunden. Dies ist DSGVO-Pflicht.",
        "Es wurde kein Cookie-Consent-Banner gefunden",
        "Es wurde keine E-Mail-Adresse für Kontaktaufnahme gefunden",
        "Fehlende Alt-Texte für Barrierefreiheit",
        "Unzureichende Farbkontraste für Screenreader",
        "Fehlende Tastaturbedienung für interaktive Elemente",
        "Tracking ohne vorherige Einwilligung erkannt",
    ]
    
    # FIXED: Deterministisch Issues auswählen basierend auf URL
    num_issues = seeded_value(url + "num", 4, 6)
    # Deterministisch Issues auswählen
    selected_indices = []
    for i in range(num_issues):
        idx = seeded_value(url + f"idx_{i}", 0, len(all_issues) - 1)
        if idx not in selected_indices:
            selected_indices.append(idx)
    # Falls nicht genug eindeutige Indices, einfach die ersten num_issues nehmen
    while len(selected_indices) < num_issues:
        for i in range(len(all_issues)):
            if i not in selected_indices:
                selected_indices.append(i)
                if len(selected_indices) >= num_issues:
                    break
    
    selected_issues = [all_issues[i] for i in selected_indices[:num_issues]]
    
    # Calculate score based on issues (more issues = lower score)
    score = max(25, 100 - (num_issues * 12))
    
    # Convert to structured issues with risk calculation
    structured_issues = []
    for idx, issue_text in enumerate(selected_issues):
        risk_data = await risk_calculator.calculate_issue_risk(issue_text)
        
        structured_issue = ComplianceIssue(
            id=f"issue-{idx+1}",
            category=risk_data['category'],
            severity=risk_data['severity'],
            title=issue_text[:100],
            description=issue_text,
            risk_euro_min=risk_data['risk_min'],
            risk_euro_max=risk_data['risk_max'],
            risk_range=risk_data['risk_range'],
            legal_basis=risk_data['legal_basis'],
            location=IssueLocation(
                area=_determine_issue_area(risk_data['category']),
                hint=f"{_determine_issue_area(risk_data['category'])} fehlt oder ist fehlerhaft"
            ),
            solution=_generate_solution(risk_data['category']),
            auto_fixable=risk_data['category'] in ['impressum', 'datenschutz', 'cookies', 'agb']
        )
        structured_issues.append(structured_issue)
    
    # Calculate total risk
    total_risk_data = await risk_calculator.calculate_total_risk(selected_issues)
    
    # FIXED: Deterministischer scan_duration basierend auf URL
    scan_duration = seeded_value(url + "duration", 2000, 4000)
    
    return AnalysisResponse(
        success=True,
        url=url,
        compliance_score=score,
        estimated_risk_euro=total_risk_data['total_risk_range'],
        issues=structured_issues,
        has_accessibility_widget=scan_result.get('has_accessibility_widget', False),
        riskAmount=total_risk_data['total_risk_range'],
        score=score,
        scan_duration_ms=scan_duration,
        timestamp=datetime.now().isoformat()
    )

@public_router.post("/analyze-preview", response_model=Dict[str, Any])
async def analyze_website_preview(request: AnalyzeRequest, http_request: Request):
    """
    Preview-Analyse für Landing Page (ohne Details)
    
    Zeigt nur:
    - Compliance Score
    - Risiko-Kategorien (mit/ohne Probleme)
    - Gesamt-Risiko-Range
    
    Keine detaillierten Issue-Beschreibungen → Paywall
    """
    try:
        url = str(request.url)
        
        logger.info(f"Preview analysis request for: {url}")
        
        # ✅ FIX: Normalisiere URL (füge https:// hinzu falls fehlt)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            logger.info(f"✅ URL normalized to: {url}")
        
        # Get risk calculator
        from main_production import risk_calculator
        
        # Perform compliance scan
        try:
            async with ComplianceScanner() as scanner:
                scan_result = await scanner.scan_website(url)
            
            if scan_result.get("error"):
                # Fallback zu Mock
                return await _generate_preview_mock(url, risk_calculator)
            
            # Aggregiere Issues nach Kategorien
            risk_categories = await _aggregate_risk_categories(
                scan_result.get("issues", []),
                risk_calculator
            )
            
            # Berechne Gesamt-Risiko
            total_risk_min = sum(cat['risk_min'] for cat in risk_categories if cat['detected'])
            total_risk_max = sum(cat['risk_max'] for cat in risk_categories if cat['detected'])
            
            return {
                "success": True,
                "url": url,
                "score": scan_result.get("compliance_score", 50),
                "risk_categories": risk_categories,
                "total_risk_range": f"{int(total_risk_min):,}€ - {int(total_risk_max):,}€".replace(',', '.'),
                "issues_count": len(scan_result.get("issues", [])),
                "critical_count": sum(1 for cat in risk_categories if cat['severity'] == 'critical' and cat['detected']),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as scanner_error:
            logger.error(f"Preview scanner error: {scanner_error}", exc_info=True)
            return await _generate_preview_mock(url, risk_calculator)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in preview analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Fehler bei der Preview-Analyse"
        )

async def _aggregate_risk_categories(issues: list, risk_calculator) -> List[Dict[str, Any]]:
    """Aggregiert Issues nach den 4 Hauptsäulen + weitere Kategorien"""
    
    # Die 4 Hauptsäulen von Complyo
    main_pillars = {
        'barrierefreiheit': {
            'label': 'Barrierefreiheit',
            'icon': '♿',
            'categories': ['barrierefreiheit', 'kontraste', 'tastaturbedienung']
        },
        'cookies': {
            'label': 'Cookie Compliance',
            'icon': '🍪',
            'categories': ['cookies', 'tracking']
        },
        'rechtstexte': {
            'label': 'Rechtstexte',
            'icon': '📄',
            'categories': ['impressum', 'agb', 'contact', 'uwg']
        },
        'shop': {
            'label': 'Shop-Compliance',
            'icon': '🛒',
            'categories': ['shop', 'widerrufsbelehrung', 'preisangaben']
        },
        'dsgvo': {
            'label': 'DSGVO',
            'icon': '🔒',
            'categories': ['datenschutz', 'tracking', 'datenverarbeitung', 'avv']
        },
        'sicherheit': {
            'label': 'Sicherheit',
            'icon': '🔐',
            'categories': ['security']
        },
    }
    
    # Weitere Kategorien
    other_categories = {
        'wettbewerb': {
            'label': 'Wettbewerbsrecht',
            'icon': '⚖️',
            'categories': ['irrefuehrende_werbung', 'pruefsiegel', 'schleichwerbung']
        },
        'preise': {
            'label': 'Preisangaben',
            'icon': '💰',
            'categories': ['preisangaben', 'grundpreis']
        }
    }
    
    all_pillars = {**main_pillars, **other_categories}
    result = []
    
    # Zähle Issues pro Säule
    for pillar_id, pillar_data in all_pillars.items():
        detected_issues = []
        pillar_risk_min = 0
        pillar_risk_max = 0
        max_severity = 'info'
        
        for issue in issues:
            issue_text = issue if isinstance(issue, str) else issue.get("description", str(issue))
            risk_data = await risk_calculator.calculate_issue_risk(issue_text)
            
            if risk_data['category'] in pillar_data['categories']:
                detected_issues.append(issue_text)
                pillar_risk_min += risk_data['risk_min']
                pillar_risk_max += risk_data['risk_max']
                
                # Update max severity
                if risk_data['severity'] == 'critical':
                    max_severity = 'critical'
                elif risk_data['severity'] == 'warning' and max_severity != 'critical':
                    max_severity = 'warning'
        
        result.append({
            'id': pillar_id,
            'label': pillar_data['label'],
            'icon': pillar_data['icon'],
            'detected': len(detected_issues) > 0,
            'severity': max_severity if detected_issues else 'info',
            'risk_min': pillar_risk_min,
            'risk_max': pillar_risk_max,
            'risk_range': f"{int(pillar_risk_min):,}€ - {int(pillar_risk_max):,}€".replace(',', '.') if detected_issues else None,
            'issues_count': len(detected_issues)
        })
    
    return result

async def _generate_preview_mock(url: str, risk_calculator) -> Dict[str, Any]:
    """Mock Preview wenn Scanner fehlschlägt"""
    
    # FIXED: Deterministischer Pseudo-Random Generator basierend auf URL
    def seeded_value(seed: str, min_val: int, max_val: int) -> int:
        """Generiere deterministische Werte basierend auf Seed (URL)"""
        hash_val = 0
        for char in seed:
            hash_val = ((hash_val << 5) - hash_val) + ord(char)
            hash_val = hash_val & 0xFFFFFFFF  # 32-bit integer
        normalized = abs(hash_val) / 0xFFFFFFFF
        return int(normalized * (max_val - min_val + 1)) + min_val
    
    # Mock Issues
    mock_issues = [
        "Es wurde kein Link zum Impressum gefunden",
        "Cookie-Banner fehlt",
        "Datenschutzerklärung nicht gefunden",
        "Fehlende Alt-Texte für Barrierefreiheit"
    ]
    
    # FIXED: Deterministisch bestimmen, wie viele Issues angezeigt werden
    num_issues = seeded_value(url + "count", 2, 4)
    # Deterministisch Issues auswählen basierend auf URL
    selected_indices = []
    for i in range(num_issues):
        seed_idx = seeded_value(url + f"issue_{i}", 0, len(mock_issues) - 1)
        if seed_idx not in selected_indices:
            selected_indices.append(seed_idx)
    # Falls Duplikate, einfach die ersten num_issues nehmen
    if len(selected_indices) < num_issues:
        selected_indices = list(range(min(num_issues, len(mock_issues))))
    
    selected = [mock_issues[i] for i in selected_indices[:num_issues]]
    
    risk_categories = await _aggregate_risk_categories(selected, risk_calculator)
    
    total_risk_min = sum(cat['risk_min'] for cat in risk_categories if cat['detected'])
    total_risk_max = sum(cat['risk_max'] for cat in risk_categories if cat['detected'])
    
    # FIXED: Deterministischer Score basierend auf URL
    score = seeded_value(url + "score", 30, 60)
    
    return {
        "success": True,
        "url": url,
        "score": score,
        "risk_categories": risk_categories,
        "total_risk_range": f"{int(total_risk_min):,}€ - {int(total_risk_max):,}€".replace(',', '.'),
        "issues_count": len(selected),
        "critical_count": sum(1 for cat in risk_categories if cat['severity'] == 'critical' and cat['detected']),
        "timestamp": datetime.now().isoformat()
    }

@public_router.get("/health")
async def health_check_public():
    """
    Public health check endpoint
    """
    return {
        "status": "healthy",
        "service": "complyo-public-api",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# V1 API - Widget & Accessibility Fixes
# ============================================================================

@v1_router.get("/sites/{site_id}/accessibility-fixes")
async def get_accessibility_fixes(
    site_id: str,
    request: Request
):
    """
    Liefert site-spezifische Accessibility-Fixes für das Smart Widget
    
    Das Widget ruft diesen Endpoint beim Laden auf und erhält alle
    Auto-Fixes, die auf der Kunden-Website angewendet werden sollen.
    
    Args:
        site_id: Eindeutige Site-ID (generiert beim Scan)
        
    Returns:
        JSON mit Fix-Definitionen:
        - alt_text_fixes: Bilder ohne Alt-Text
        - aria_fixes: Fehlende ARIA-Labels
        - contrast_fixes: Kontrast-Probleme
        - focus_fixes: Focus-Indikatoren
        - keyboard_fixes: Keyboard-Navigation
    
    Cache: 1 Stunde (Fixes ändern sich nicht häufig)
    """
    try:
        logger.info(f"Loading accessibility fixes for site: {site_id}")
        
        # Hole Fixes aus Datenbank (wenn vorhanden)
        from main_production import db_pool
        
        fixes = {
            "alt_text_fixes": [],
            "aria_fixes": [],
            "contrast_fixes": [],
            "focus_fixes": [],
            "keyboard_fixes": []
        }
        
        if db_pool:
            try:
                async with db_pool.acquire() as conn:
                    # Hole letzten Scan für diese Site
                    scan = await conn.fetchrow("""
                        SELECT scan_data, url
                        FROM scan_history
                        WHERE site_id = $1
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, site_id)
                    
                    if scan and scan['scan_data']:
                        scan_data = json.loads(scan['scan_data']) if isinstance(scan['scan_data'], str) else scan['scan_data']
                        issues = scan_data.get('issues', [])
                        
                        # Konvertiere Issues zu Fixes
                        fixes = convert_issues_to_fixes(issues, scan.get('url'))
                        
                        logger.info(f"Generated {sum(len(v) for v in fixes.values())} fixes for {site_id}")
            
            except Exception as e:
                logger.error(f"Failed to load fixes from DB: {e}")
                # Continue mit leeren Fixes
        
        # Cache-Header setzen (1 Stunde)
        response = JSONResponse(
            content=fixes,
            headers={
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*"  # CORS für Widget
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error loading accessibility fixes: {e}")
        raise HTTPException(status_code=500, detail="Failed to load fixes")


def convert_issues_to_fixes(issues: List[Dict], base_url: str) -> Dict[str, List[Dict]]:
    """
    Konvertiert Scan-Issues in Widget-kompatible Fix-Definitionen
    
    Args:
        issues: Liste von Issues aus dem Scan
        base_url: Basis-URL der Webseite
        
    Returns:
        Dict mit kategorisierten Fixes
    """
    fixes = {
        "alt_text_fixes": [],
        "aria_fixes": [],
        "contrast_fixes": [],
        "focus_fixes": [],
        "keyboard_fixes": []
    }
    
    for issue in issues:
        if issue.get('category') != 'barrierefreiheit':
            continue
        
        # Alt-Text Fixes
        if 'alt-text' in issue.get('title', '').lower() or issue.get('suggested_alt'):
            image_src = issue.get('image_src', '')
            suggested_alt = issue.get('suggested_alt', 'Bild')
            
            if image_src:
                fixes['alt_text_fixes'].append({
                    "selector": f'img[src="{image_src}"]',
                    "alt": suggested_alt
                })
        
        # ARIA Fixes
        elif 'aria' in issue.get('title', '').lower():
            # Generiere generische ARIA-Fixes
            element_html = issue.get('element_html', '')
            if 'button' in element_html:
                fixes['aria_fixes'].append({
                    "selector": "button:not([aria-label])",
                    "aria-label": "Aktion ausführen"
                })
            if 'input' in element_html:
                fixes['aria_fixes'].append({
                    "selector": "input:not([aria-label]):not([aria-labelledby])",
                    "aria-label": "Eingabefeld"
                })
        
        # Kontrast Fixes
        elif 'kontrast' in issue.get('title', '').lower():
            # Generiere CSS-basierte Kontrast-Fixes
            fixes['contrast_fixes'].append({
                "selector": ".text-gray-400, .text-gray-500",
                "color": "#1f2937"
            })
    
    return fixes


@v1_router.post("/sites/{site_id}/widget-feedback")
async def widget_feedback(
    site_id: str,
    feedback: Dict[str, Any]
):
    """
    Empfängt Feedback vom Widget über angewendete Fixes
    
    Hilft bei Monitoring und Analytics:
    - Welche Fixes wurden angewendet?
    - Gab es Fehler?
    - Performance-Metriken
    """
    try:
        logger.info(f"Widget feedback from {site_id}: {feedback.get('event')}")

        from main_production import db_pool as main_db_pool
        if main_db_pool:
            async with main_db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO widget_events
                       (site_id, widget_type, event_name, event_data)
                       VALUES ($1, $2, $3, $4)""",
                    site_id,
                    "widget-feedback",
                    feedback.get("event", "feedback"),
                    json.dumps(feedback),
                )

        return {
            "success": True,
            "message": "Feedback received"
        }

    except Exception as e:
        logger.error(f"Failed to process widget feedback: {e}")
        return {
            "success": False,
            "message": "Failed to process feedback"
        }


@v1_router.get("/widget/version")
async def widget_version():
    """
    Gibt aktuelle Widget-Version zurück
    
    Für Auto-Update-Checks
    """
    return {
        "version": "2.0.0",
        "cdn_url": "https://cdn.complyo.tech/accessibility-v2.js",
        "changelog_url": "https://complyo.tech/widget/changelog",
        "deprecated_versions": ["1.0.0", "1.5.0"]
    }


@v1_router.get("/sites/{site_id}/code-package/{framework}")
async def download_code_package(
    site_id: str,
    framework: str,
    request: Request
):
    """
    Generiert und liefert ZIP-Paket mit Code-Fixes
    
    Args:
        site_id: Eindeutige Site-ID
        framework: 'react', 'vue', 'angular' oder 'html'
        
    Returns:
        ZIP-Datei zum Download
    """
    from fastapi.responses import StreamingResponse
    from compliance_engine.code_package_generator import CodePackageGenerator
    
    try:
        logger.info(f"Generating code package for {site_id}, framework: {framework}")
        
        # Validiere Framework
        valid_frameworks = ['react', 'vue', 'angular', 'html']
        if framework not in valid_frameworks:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid framework. Must be one of: {', '.join(valid_frameworks)}"
            )
        
        # Hole Scan-Daten aus DB
        from main_production import db_pool
        
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            scan = await conn.fetchrow("""
                SELECT scan_data, url
                FROM scan_history
                WHERE site_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, site_id)
            
            if not scan:
                raise HTTPException(status_code=404, detail="Scan not found")
            
            scan_data = json.loads(scan['scan_data']) if isinstance(scan['scan_data'], str) else scan['scan_data']
            site_url = scan['url']
        
        # Generiere ZIP-Paket
        generator = CodePackageGenerator()
        zip_bytes = generator.generate_package(scan_data, framework, site_url)
        
        # Erstelle Download-Response
        filename = f"complyo-accessibility-fixes-{framework}.zip"
        
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(zip_bytes))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate code package: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate package")


 

