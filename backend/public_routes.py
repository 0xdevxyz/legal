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
from datetime import datetime
from compliance_engine.scanner import ComplianceScanner
from compliance_engine.priority_engine import priority_engine
from compliance_engine.solution_generator import solution_generator
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
    url: str  # Akzeptiert URLs mit oder ohne Protokoll

class ChatMessage(BaseModel):
    role: str  # "user" oder "assistant"
    content: str

class IssueChatRequest(BaseModel):
    website_url: str
    issue_title: str
    issue_description: str
    ai_solution: Optional[str] = None
    user_question: str
    chat_history: List[ChatMessage] = []

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
        # ✅ FIX: Key ist "id", nicht "user_id" (siehe auth_service.get_user_by_id)
        user_id = current_user.get("id") or current_user.get("user_id")
        
        # ✅ FIX: Normalisiere URL (füge https:// hinzu falls fehlt)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            logger.info(f"✅ URL normalized to: {url}")
        
        logger.info(f"Analysis request for: {url} (User: {user_id})")
        
        # Get risk calculator from app state
        from main_production import db_pool, risk_calculator
        
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
            
            # ✅ NEU: Generiere individuelle KI-Lösungen (ERHÖHTER TIMEOUT für Reasoning Model)
            if OPENROUTER_API_KEY and len(structured_issues) > 0:
                logger.info(f"🤖 Generiere KI-Lösungen für erste 5 Critical Issues...")
                
                # Priorisiere Critical Issues
                critical_issues = [i for i in structured_issues if i.severity == 'critical'][:5]
                if not critical_issues:
                    critical_issues = structured_issues[:5]
                
                ai_tasks = []
                for issue in critical_issues:
                    ai_tasks.append(_generate_ai_solution(
                        issue_title=issue.title,
                        issue_description=issue.description,
                        category=issue.category,
                        url=url
                    ))
                
                # Parallel KI-Lösungen generieren mit LÄNGEREM Timeout (für kimi-k2-thinking)
                try:
                    ai_solutions = await asyncio.wait_for(
                        asyncio.gather(*ai_tasks, return_exceptions=True),
                        timeout=20.0  # 20 Sekunden für Reasoning Model
                    )
                    
                    # Füge KI-Lösungen zu Issues hinzu
                    for idx, issue in enumerate(critical_issues):
                        if idx < len(ai_solutions) and ai_solutions[idx] and not isinstance(ai_solutions[idx], Exception):
                            issue.ai_solution = ai_solutions[idx]
                    
                    successful = sum(1 for s in ai_solutions if s and not isinstance(s, Exception))
                    logger.info(f"✅ {successful}/{len(critical_issues)} KI-Lösungen generiert")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ KI-Generierung Timeout - Scan wird trotzdem zurückgegeben")
            else:
                logger.info("ℹ️ KI-Lösungen übersprungen (kein API Key)")
            
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
                            warning_issues, total_issues, scan_duration_ms
                        ) VALUES ($1, $2, $3, $4, $5, NOW(), $6, $7, $8, $9, $10, $11, $12)
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
                            'issue_groups': scan_result.get('issue_groups', []),  # ✅ NEU: Gruppierte Issues
                            'grouping_stats': scan_result.get('grouping_stats', {})  # ✅ NEU: Gruppierungs-Statistiken
                        }),
                        overall_compliance_score,
                        total_risk_data.get('total_risk_max', 0),
                        critical_issues_count,
                        warning_issues_count,
                        len(structured_issues),
                        scan_result.get("scan_duration_ms")
                    )
                    logger.info(f"✅ Saved scan history for website ID {website_id}")
                    
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
        'gdpr': ['datenschutz', 'tracking', 'datenverarbeitung'],
        'legal': ['impressum', 'agb', 'widerrufsbelehrung', 'contact'],
        'cookies': ['cookies']
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
    """Generiert issue-spezifische Lösungsvorschläge"""
    
    # ✅ Spezielle Lösungen für Barrierefreiheit basierend auf Issue-Titel
    if category == 'barrierefreiheit':
        title_lower = title.lower()
        
        # H1-Überschrift fehlt
        if 'h1' in title_lower or 'überschrift' in title_lower:
            return IssueSolution(
                code_snippet='<h1>Hauptüberschrift der Seite</h1>',
                steps=[
                    '1. Fügen Sie eine aussagekräftige H1-Überschrift am Seitenanfang ein',
                    '2. Die H1 sollte das Hauptthema der Seite beschreiben',
                    '3. Verwenden Sie nur eine H1 pro Seite',
                    '4. Weitere Überschriften hierarchisch strukturieren (H2, H3, etc.)'
                ]
            )
        
        # Semantische HTML-Elemente fehlen
        if 'semantisch' in title_lower or 'html5' in title_lower or 'html-elemente' in title_lower:
            return IssueSolution(
                code_snippet='''<!-- Beispiel-Struktur mit semantischen HTML5-Elementen -->
<header>
    <nav><!-- Navigation --></nav>
</header>
<main>
    <article><!-- Hauptinhalt --></article>
</main>
<footer><!-- Footer-Bereich --></footer>''',
                steps=[
                    '1. Ersetzen Sie <div>-Container durch semantische Elemente: <header>, <nav>, <main>, <footer>',
                    '2. Nutzen Sie <article> für eigenständige Inhalte und <section> für thematische Gruppierungen',
                    '3. Verwenden Sie <aside> für ergänzende Inhalte (Sidebars)',
                    '4. Testen Sie die Struktur mit einem Screenreader (z.B. NVDA oder VoiceOver)'
                ]
            )
        
        # Alt-Texte fehlen
        if 'alt' in title_lower or 'bild' in title_lower:
            return IssueSolution(
                code_snippet='<img src="logo.png" alt="Firmenname Logo - Zurück zur Startseite">',
                steps=[
                    '1. Fügen Sie jedem <img>-Tag ein alt-Attribut hinzu',
                    '2. Beschreiben Sie den Inhalt und Zweck des Bildes präzise',
                    '3. Dekorative Bilder: Leeres alt-Attribut verwenden (alt="")',
                    '4. Prüfen Sie alle Bilder auf der gesamten Website'
                ]
            )
        
        # Kontraste
        if 'kontrast' in title_lower or 'farb' in title_lower:
            return IssueSolution(
                code_snippet='''/* Beispiel mit ausreichendem Kontrast */
.text {
    color: #1a1a1a;        /* Dunkler Text */
    background: #ffffff;    /* Heller Hintergrund */
    /* Kontrast-Verhältnis: 15:1 ✓ */
}''',
                steps=[
                    '1. Prüfen Sie Farbkontraste mit einem Tool (z.B. WebAIM Contrast Checker)',
                    '2. Mindestanforderung: 4.5:1 für normalen Text, 3:1 für großen Text (>18pt)',
                    '3. Passen Sie Farben an, um ausreichenden Kontrast zu erreichen',
                    '4. Testen Sie auch Hover- und Focus-Zustände'
                ]
            )
        
        # Tastatur-Navigation
        if 'tastatur' in title_lower or 'keyboard' in title_lower or 'focus' in title_lower:
            return IssueSolution(
                code_snippet='''<button tabindex="0" aria-label="Menü öffnen">
    Menu
</button>

<style>
button:focus {
    outline: 3px solid #4a90e2;
    outline-offset: 2px;
}
</style>''',
                steps=[
                    '1. Stellen Sie sicher, dass alle interaktiven Elemente per Tab-Taste erreichbar sind',
                    '2. Fügen Sie sichtbare Focus-Indikatoren hinzu (outline, border, etc.)',
                    '3. Verwenden Sie tabindex="0" für fokussierbare custom Elemente',
                    '4. Testen Sie die Navigation komplett per Tastatur (ohne Maus)'
                ]
            )
        
        # ARIA-Labels
        if 'aria' in title_lower or 'label' in title_lower:
            return IssueSolution(
                code_snippet='''<button aria-label="Schließen">
    <svg><!-- X Icon --></svg>
</button>

<nav aria-label="Hauptnavigation">
    <!-- Navigation Items -->
</nav>''',
                steps=[
                    '1. Fügen Sie aria-label zu Buttons ohne Text-Inhalt hinzu',
                    '2. Verwenden Sie aria-labelledby bei komplexeren Elementen',
                    '3. Nutzen Sie role-Attribute für custom Komponenten',
                    '4. Validieren Sie mit dem WAVE Browser Extension'
                ]
            )
    
    # Fallback für andere Kategorien
    return _generate_solution(category)

def _generate_solution(category: str) -> IssueSolution:
    """Generiert Lösungsvorschläge basierend auf Kategorie"""
    solutions = {
        'impressum': IssueSolution(
            code_snippet='<a href="/impressum" rel="legal">Impressum</a>',
            steps=[
                '1. Erstelle eine Impressum-Seite unter /impressum',
                '2. Füge alle Pflichtangaben hinzu (§5 TMG)',
                '3. Verlinke das Impressum im Footer',
                '4. Stelle sicher, dass es von jeder Seite aus erreichbar ist'
            ]
        ),
        'datenschutz': IssueSolution(
            code_snippet='<a href="/datenschutz" rel="privacy-policy">Datenschutzerklärung</a>',
            steps=[
                '1. Erstelle eine Datenschutzseite unter /datenschutz',
                '2. Dokumentiere alle Datenverarbeitungen (DSGVO Art. 13-14)',
                '3. Verlinke die Datenschutzerklärung im Footer',
                '4. Aktualisiere sie bei Änderungen'
            ]
        ),
        'cookies': IssueSolution(
            code_snippet='<!-- Cookie-Consent-Banner Integration -->\n<script src="cookie-consent.js"></script>',
            steps=[
                '1. Implementiere einen Cookie-Consent-Banner',
                '2. Blockiere Tracking-Cookies bis zur Einwilligung',
                '3. Biete Opt-out-Möglichkeit an',
                '4. Dokumentiere in der Datenschutzerklärung'
            ]
        ),
        'barrierefreiheit': IssueSolution(
            code_snippet='<button aria-label="Menü öffnen" role="button" tabindex="0">Menu</button>',
            steps=[
                '1. Füge Alt-Texte zu allen Bildern hinzu',
                '2. Stelle ausreichende Farbkontraste sicher (WCAG 2.1)',
                '3. Aktiviere Tastaturbedienung für alle interaktiven Elemente',
                '4. Teste mit Screenreader'
            ]
        ),
    }
    
    return solutions.get(
        category,
        IssueSolution(
            code_snippet='<!-- Siehe Dokumentation für Details -->',
            steps=[
                '1. Prüfe die rechtliche Grundlage',
                '2. Implementiere die erforderlichen Änderungen',
                '3. Dokumentiere die Umsetzung',
                '4. Teste die Implementierung'
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
            'categories': ['impressum', 'agb', 'widerrufsbelehrung', 'contact']
        },
        'dsgvo': {
            'label': 'DSGVO',
            'icon': '🔒',
            'categories': ['datenschutz', 'tracking', 'datenverarbeitung']
        }
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
        
        # Speichere in Analytics-Tabelle (TODO)
        # await store_widget_analytics(site_id, feedback)
        
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


@public_router.post("/chat/issue-solution")
async def chat_with_ai_about_issue(
    request: IssueChatRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat-Endpoint für Rückfragen zu KI-generierten Lösungen
    
    Ermöglicht es Nutzern, spezifische Fragen zur Implementierung
    der vorgeschlagenen Lösung zu stellen.
    """
    try:
        if not OPENROUTER_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="KI-Chat ist momentan nicht verfügbar. Bitte kontaktieren Sie den Support."
            )
        
        logger.info(f"💬 Chat-Anfrage: {request.user_question[:50]}... für Issue: {request.issue_title[:50]}")
        
        # Baue Kontext für KI auf
        context_prompt = f"""Du bist ein Experte für Website-Compliance und unterstützt bei der Implementierung von Lösungen.

**KONTEXT:**
Website: {request.website_url}
Problem: {request.issue_title}
Details: {request.issue_description}
"""
        
        if request.ai_solution:
            context_prompt += f"\n**Bereits vorgeschlagene Lösung:**\n{request.ai_solution}\n"
        
        context_prompt += f"""
**AUFGABE:**
Beantworte die folgende Frage des Nutzers präzise und praxisnah.
Gib konkrete Code-Beispiele, wenn relevant.
Bleibe im Kontext der Website {request.website_url} und des Problems "{request.issue_title}".

**NUTZER-FRAGE:**
{request.user_question}

Antworte auf Deutsch, maximal 250 Wörter."""

        # Erstelle Nachrichten-Array mit Chat-History
        messages = []
        
        # Füge Chat-History hinzu (falls vorhanden)
        for msg in request.chat_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Füge aktuelle Frage hinzu
        messages.append({
            "role": "user",
            "content": context_prompt
        })
        
        # Rufe OpenRouter API auf
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://complyo.tech",
                    "X-Title": "Complyo Compliance Scanner - Chat Support"
                },
                json={
                    "model": "moonshotai/kimi-k2-thinking",
                    "messages": messages,
                    "max_tokens": 700,
                    "temperature": 0.7
                },
                timeout=aiohttp.ClientTimeout(total=20)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    ai_response = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    
                    if not ai_response:
                        raise HTTPException(
                            status_code=500,
                            detail="KI konnte keine Antwort generieren"
                        )
                    
                    logger.info(f"✅ Chat-Antwort generiert ({len(ai_response)} Zeichen)")
                    
                    return {
                        "success": True,
                        "response": ai_response,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ OpenRouter API Error: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=503,
                        detail="KI-Service vorübergehend nicht verfügbar"
                    )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Chat-Fehler: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ein Fehler ist beim Chat aufgetreten"
        )

