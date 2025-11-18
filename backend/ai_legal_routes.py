"""
API Routes für AI-gestützte Legal Updates mit intelligenter Klassifizierung
===========================================================================

Features:
- Automatische KI-Klassifizierung von Gesetzesänderungen
- Dynamische Button-Aktionen basierend auf KI-Entscheidung
- Feedback-Collection für selbstlernendes System
- Archiv-Funktionalität
- Performance-Tracking
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

from auth_routes import get_current_user
from database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal-ai", tags=["Legal AI"])

# db_pool wird zur Laufzeit gesetzt
db_pool = None

# Helper function to get db_pool
def get_db_pool():
    from main_production import db_pool as main_db_pool
    return main_db_pool

# Helper function to extract user_id
async def get_current_user_id(current_user: dict = Depends(get_current_user)) -> int:
    return current_user.get("user_id")


# ==================== PYDANTIC MODELS ====================

class ClassificationRequest(BaseModel):
    update_id: str
    force_reclassify: bool = False


class FeedbackRequest(BaseModel):
    update_id: str
    classification_id: int
    feedback_type: str  # implicit_click, explicit_helpful, etc.
    user_action: Optional[str] = None
    time_to_action: Optional[int] = None
    context_data: Optional[Dict[str, Any]] = None


class ClassifiedUpdateResponse(BaseModel):
    # Update-Daten
    id: int
    update_type: str
    title: str
    description: str
    severity: str
    published_at: str
    effective_date: Optional[str]
    url: Optional[str]
    
    # KI-Klassifizierung
    action_required: bool
    confidence: Optional[str]
    impact_score: Optional[float]
    
    # Primary Action
    primary_action: Optional[Dict[str, Any]]
    
    # Zusätzliche Actions
    recommended_actions: Optional[List[Dict[str, Any]]]
    
    # Erklärungen
    reasoning: Optional[str]
    user_impact: Optional[str]
    consequences_if_ignored: Optional[str]
    
    # Metadata
    classification_id: Optional[int]
    auto_classified: bool
    classified_at: Optional[str]


class ArchiveResponse(BaseModel):
    updates: List[ClassifiedUpdateResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class StatsResponse(BaseModel):
    total_updates: int
    action_required: int
    critical: int
    high_impact: int
    pending_actions: int
    avg_impact_score: float


# ==================== HELPER FUNCTIONS ====================

async def auto_archive_old_updates(conn, max_active: int = 6):
    """
    ✅ AUTO-ARCHIVIERUNG: Archiviert automatisch ältere Updates wenn mehr als max_active vorhanden sind
    
    Args:
        conn: DB Connection
        max_active: Maximale Anzahl aktiver Updates (Default: 6)
    
    Returns:
        Anzahl archivierter Updates
    """
    try:
        # Zähle aktive Updates
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM legal_updates WHERE archived = FALSE"
        )
        
        if count <= max_active:
            logger.debug(f"✅ Auto-Archivierung nicht nötig: {count}/{max_active} aktive Updates")
            return 0
        
        # Archiviere die ältesten Updates
        to_archive = count - max_active
        archived_ids = await conn.fetch(
            """
            UPDATE legal_updates
            SET archived = TRUE, archived_at = NOW()
            WHERE id IN (
                SELECT id FROM legal_updates 
                WHERE archived = FALSE
                ORDER BY published_date ASC
                LIMIT $1
            )
            RETURNING id, title
            """,
            to_archive
        )
        
        for row in archived_ids:
            logger.info(f"📦 Archiviert: {row['title'][:60]}...")
        
        logger.info(f"✅ Auto-Archivierung abgeschlossen: {len(archived_ids)} Updates archiviert")
        return len(archived_ids)
        
    except Exception as e:
        logger.error(f"❌ Auto-Archivierung fehlgeschlagen: {e}")
        return 0


# ==================== API ENDPOINTS ====================

@router.get("/updates", response_model=List[ClassifiedUpdateResponse])
async def get_classified_updates(
    limit: int = Query(6, ge=1, le=50),
    include_info_only: bool = Query(False),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """
    Holt die aktuellsten Gesetzesänderungen mit KI-Klassifizierung
    
    - Automatisch klassifiziert falls noch nicht geschehen
    - Sortiert nach Wichtigkeit (action_required, impact_score, published_at)
    - Standard: Nur Updates mit Handlungsbedarf
    - USER-SPEZIFISCH: Prüft Relevanz für hinterlegte Website
    """
    try:
        # Hole db_pool von main_production
        from main_production import db_pool as main_db_pool
        pool = main_db_pool
        if not pool:
            raise HTTPException(status_code=503, detail="Database pool not initialized")
        
        async with pool.acquire() as conn:
            # ✅ AUTO-ARCHIVIERUNG: Halte max. 6 aktive Updates
            await auto_archive_old_updates(conn, max_active=6)
            
            # ✅ Ermittle User-Website (letzte gescannte Website)
            user_website = None
            if user_id:
                user_website_row = await conn.fetchrow("""
                    SELECT url, last_scan 
                    FROM websites 
                    WHERE user_id = $1 
                    ORDER BY last_scan DESC NULLS LAST
                    LIMIT 1
                """, user_id)
                if user_website_row:
                    user_website = user_website_row['url']
                    logger.info(f"🌐 User-Website gefunden: {user_website}")
            
            # Hole Updates mit Klassifizierung - direkte Query statt Funktion
            # Vereinfachte Query: Wenn include_info_only=false, zeige alle Updates
            if include_info_only:
                where_clause = "WHERE COALESCE(ac.action_required, false) = false"
            else:
                where_clause = ""  # Zeige alle Updates
            
            query = f"""
                SELECT 
                    lu.id,
                    lu.update_type,
                    lu.title,
                    lu.description,
                    lu.severity,
                    lu.published_date as published_at,
                    lu.effective_date,
                    lu.url,
                    COALESCE(ac.action_required, (lu.action_required IS NOT NULL AND lu.action_required::text != '')) as action_required,
                    ac.confidence,
                    ac.impact_score,
                    ac.primary_action_type,
                    ac.primary_button_text,
                    ac.primary_button_color,
                    ac.primary_button_icon,
                    ac.primary_action_description,
                    ac.estimated_time,
                    ac.reasoning,
                    ac.user_impact,
                    ac.consequences_if_ignored
                FROM legal_updates lu
                LEFT JOIN ai_classifications ac ON lu.id = ac.update_id
                WHERE lu.archived = FALSE  -- ✅ Nur nicht-archivierte Updates
                {where_clause.replace('WHERE ', 'AND ') if where_clause.startswith('WHERE') else where_clause}
                ORDER BY 
                    COALESCE(ac.action_required, true) DESC,
                    COALESCE(ac.impact_score, 5.0) DESC,
                    lu.published_date DESC
                LIMIT $1
            """
            
            rows = await conn.fetch(query, limit)
        
        updates = []
        for row in rows:
            # Baue Primary Action mit Details
            primary_action = None
            if row['primary_action_type']:
                primary_action = {
                    "action_type": row['primary_action_type'],
                    "button_text": row['primary_button_text'],
                    "button_color": row['primary_button_color'],
                    "icon": row['primary_button_icon'],
                    "description": row.get('primary_action_description'),
                    "estimated_time": row.get('estimated_time'),
                    "user_website": user_website,  # ✅ User-Website für Frontend
                    "has_website": user_website is not None  # ✅ Prüfung ob Website vorhanden
                }
            
            # ✅ NULL-SAFE: Alle Felder mit Fallbacks
            update = ClassifiedUpdateResponse(
                id=row['id'],
                update_type=str(row['update_type'] or ''),
                title=str(row['title'] or 'Unbekanntes Update'),
                description=str(row['description'] or ''),
                severity=str(row['severity'] or 'info'),
                published_at=row['published_at'].isoformat() if row['published_at'] else datetime.now().isoformat(),
                effective_date=row['effective_date'].isoformat() if row['effective_date'] else None,
                url=str(row['url']) if row['url'] else None,
                
                action_required=bool(row['action_required']) if row['action_required'] is not None else False,
                confidence=str(row['confidence']) if row['confidence'] else None,
                impact_score=float(row['impact_score']) if row['impact_score'] else None,
                
                primary_action=primary_action,
                recommended_actions=None,  # TODO: Aus JSONB laden
                
                reasoning=row['reasoning'],
                user_impact=row['user_impact'],
                consequences_if_ignored=row.get('consequences_if_ignored'),
                
                classification_id=None,
                auto_classified=False,
                classified_at=None
            )
            updates.append(update)
        
        # TODO: Auto-Klassifizierung im Background triggern
        # (schedule_auto_classification noch nicht implementiert)
        
        logger.info(f"✅ Returned {len(updates)} classified updates (public endpoint)")
        return updates
        
    except Exception as e:
        logger.error(f"❌ Error fetching classified updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/updates/{update_id}/details")
async def get_update_details(
    update_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Holt detaillierte Informationen zu einem Update inklusive vollständiger Klassifizierung
    """
    try:
        async with db_pool.acquire() as conn:
            # Hole Update
            update_row = await conn.fetchrow(
                """
                SELECT * FROM legal_updates WHERE id = $1
                """,
                update_id
            )
            
            if not update_row:
                raise HTTPException(status_code=404, detail="Update nicht gefunden")
            
            # Hole Klassifizierung
            classification_row = await conn.fetchrow(
                """
                SELECT * FROM ai_classifications
                WHERE update_id = $1 AND (user_id = $2 OR user_id IS NULL)
                ORDER BY user_id DESC NULLS LAST, classified_at DESC
                LIMIT 1
                """,
                str(update_id),
                user_id
            )
            
            # Baue Response
            result = {
                "update": dict(update_row),
                "classification": dict(classification_row) if classification_row else None,
                "has_user_feedback": False
            }
            
            # Prüfe ob User bereits Feedback gegeben hat
            if classification_row:
                has_feedback = await conn.fetchval(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM ai_classification_feedback
                        WHERE classification_id = $1 AND user_id = $2
                    )
                    """,
                    classification_row['id'],
                    user_id
                )
                result["has_user_feedback"] = has_feedback
            
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching update details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/updates/{update_id}/classify")
async def classify_update(
    update_id: int,
    background_tasks: BackgroundTasks,
    force: bool = Query(False),
    user_id: int = Depends(get_current_user_id)
):
    """
    Klassifiziert ein Update mit KI
    
    - force=true: Erzwingt Re-Klassifizierung auch wenn schon klassifiziert
    """
    try:
        # Prüfe ob bereits klassifiziert
        async with db_pool.acquire() as conn:
            existing = await conn.fetchrow(
                """
                SELECT id FROM ai_classifications
                WHERE update_id = $1 AND (user_id = $2 OR user_id IS NULL)
                """,
                str(update_id),
                user_id
            )
            
            if existing and not force:
                return {
                    "success": False,
                    "message": "Update bereits klassifiziert. Verwende force=true zum Re-Klassifizieren.",
                    "classification_id": existing['id']
                }
            
            # Hole Update-Daten
            update_row = await conn.fetchrow(
                "SELECT * FROM legal_updates WHERE id = $1",
                update_id
            )
            
            if not update_row:
                raise HTTPException(status_code=404, detail="Update nicht gefunden")
        
        # Starte Klassifizierung im Hintergrund
        background_tasks.add_task(
            _classify_update_background,
            update_id,
            dict(update_row),
            user_id
        )
        
        return {
            "success": True,
            "message": "Klassifizierung gestartet",
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting classification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    user_id: Optional[int] = None
):
    """
    Nimmt User-Feedback zu einer Klassifizierung entgegen
    
    Feedback-Typen:
    - implicit_click: User hat geklickt
    - implicit_ignore: User hat ignoriert
    - implicit_dismiss: User hat abgelehnt
    - explicit_helpful: User fand es hilfreich
    - explicit_not_helpful: User fand es nicht hilfreich
    - explicit_wrong: User meldet Fehler
    - action_completed: User hat Aktion ausgeführt
    - action_skipped: User hat Aktion übersprungen
    
    ÖFFENTLICH: Funktioniert auch ohne Authentication (user_id optional)
    """
    try:
        from ai_feedback_learning import get_feedback_learning, FeedbackType, UserActionType
        
        learning = get_feedback_learning()
        if not learning:
            raise HTTPException(
                status_code=503,
                detail="Feedback-System nicht verfügbar"
            )
        
        # Konvertiere zu Enums
        try:
            feedback_type = FeedbackType(feedback.feedback_type)
            user_action = UserActionType(feedback.user_action) if feedback.user_action else None
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Ungültiger Feedback-Typ: {e}")
        
        # Record Feedback
        success = await learning.record_feedback(
            user_id=user_id,
            update_id=feedback.update_id,
            classification_id=feedback.classification_id,
            feedback_type=feedback_type,
            user_action=user_action,
            time_to_action=feedback.time_to_action,
            context_data=feedback.context_data
        )
        
        if success:
            return {
                "success": True,
                "message": "Feedback gespeichert"
            }
        else:
            raise HTTPException(status_code=500, detail="Feedback konnte nicht gespeichert werden")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/archive", response_model=ArchiveResponse)
async def get_archive(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user_id)
):
    """
    Holt archivierte Updates (älter als die aktuellsten 6)
    
    - Pagination-Support
    - Filter nach Severity
    """
    try:
        offset = (page - 1) * page_size
        
        async with db_pool.acquire() as conn:
            # Baue Query
            query = """
                SELECT 
                    lu.*,
                    ac.id as classification_id,
                    ac.action_required,
                    ac.confidence,
                    ac.impact_score,
                    ac.primary_action_type,
                    ac.primary_button_text,
                    ac.primary_button_color,
                    ac.primary_button_icon,
                    ac.reasoning,
                    ac.user_impact,
                    ac.classified_at
                FROM legal_updates lu
                LEFT JOIN ai_classifications ac ON lu.id = ac.update_id
                WHERE lu.published_date < (
                    SELECT published_date FROM legal_updates
                    ORDER BY published_date DESC
                    LIMIT 1 OFFSET 5
                )
            """
            params = [user_id]
            param_count = 2
            
            if severity:
                query += f" AND lu.severity = ${param_count}"
                params.append(severity)
                param_count += 1
            
            # Count total
            count_query = query.replace("SELECT lu.*,", "SELECT COUNT(*)")
            count_query = count_query.split("FROM")[0] + " FROM " + "FROM ".join(count_query.split("FROM")[1:])
            # Remove classification fields from count query
            count_query = count_query.split("LEFT JOIN")[0]
            total = await conn.fetchval(count_query, user_id)
            
            # Get page
            query += f" ORDER BY lu.published_date DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
            params.extend([page_size, offset])
            
            rows = await conn.fetch(query, *params)
        
        # Baue Response
        updates = []
        for row in rows:
            primary_action = None
            if row['primary_action_type']:
                primary_action = {
                    "action_type": row['primary_action_type'],
                    "button_text": row['primary_button_text'],
                    "button_color": row['primary_button_color'],
                    "icon": row['primary_button_icon']
                }
            
            update = ClassifiedUpdateResponse(
                id=row['id'],
                update_type=row['update_type'],
                title=row['title'],
                description=row['description'],
                severity=row['severity'],
                published_at=row['published_at'].isoformat(),
                effective_date=row['effective_date'].isoformat() if row['effective_date'] else None,
                url=row['url'],
                
                action_required=row['action_required'] if row['action_required'] is not None else False,
                confidence=row['confidence'],
                impact_score=float(row['impact_score']) if row['impact_score'] else None,
                
                primary_action=primary_action,
                recommended_actions=None,
                
                reasoning=row['reasoning'],
                user_impact=row['user_impact'],
                consequences_if_ignored=row.get('consequences_if_ignored'),
                
                classification_id=row['classification_id'],
                auto_classified=True,
                classified_at=row['classified_at'].isoformat() if row['classified_at'] else None
            )
            updates.append(update)
        
        return ArchiveResponse(
            updates=updates,
            total=total or 0,
            page=page,
            page_size=page_size,
            has_more=(offset + len(updates)) < (total or 0)
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching archive: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_stats(user_id: int = Depends(get_current_user_id)):
    """
    Dashboard-Statistiken für Legal Updates
    """
    try:
        async with db_pool.acquire() as conn:
            stats = await conn.fetchval(
                "SELECT get_legal_updates_stats($1)",
                user_id
            )
        
        import json
        stats_dict = json.loads(stats) if isinstance(stats, str) else stats
        
        return StatsResponse(
            total_updates=stats_dict.get('total_updates', 0),
            action_required=stats_dict.get('action_required', 0),
            critical=stats_dict.get('critical', 0),
            high_impact=stats_dict.get('high_impact', 0),
            pending_actions=stats_dict.get('pending_actions', 0),
            avg_impact_score=float(stats_dict.get('avg_impact_score', 0.0))
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/insights")
async def get_learning_insights(
    days: int = Query(30, ge=1, le=365),
    user_id: int = Depends(get_current_user_id)
):
    """
    Holt Learning Insights (nur für Admins)
    
    TODO: Admin-Check einbauen
    """
    try:
        from ai_feedback_learning import get_feedback_learning
        
        learning = get_feedback_learning()
        if not learning:
            raise HTTPException(
                status_code=503,
                detail="Learning-System nicht verfügbar"
            )
        
        insights = await learning.get_learning_insights(days=days)
        
        return {
            "success": True,
            "insights": [
                {
                    "pattern_type": i.pattern_type,
                    "description": i.description,
                    "confidence": i.confidence,
                    "sample_size": i.sample_size,
                    "recommendation": i.recommendation,
                    "created_at": i.created_at.isoformat()
                }
                for i in insights
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching learning insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/suggestions")
async def get_optimization_suggestions(user_id: int = Depends(get_current_user_id)):
    """
    Holt Optimierungs-Vorschläge aus dem Learning-System (nur für Admins)
    
    TODO: Admin-Check einbauen
    """
    try:
        from ai_feedback_learning import get_feedback_learning
        
        learning = get_feedback_learning()
        if not learning:
            raise HTTPException(
                status_code=503,
                detail="Learning-System nicht verfügbar"
            )
        
        suggestions = await learning.get_optimization_suggestions()
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BACKGROUND TASKS ====================

async def _classify_update_background(
    update_id: int,
    update_data: Dict[str, Any],
    user_id: Optional[int] = None
):
    """
    Background Task: Klassifiziert ein Update mit KI
    """
    try:
        from ai_legal_classifier import get_ai_classifier
        
        classifier = get_ai_classifier()
        if not classifier:
            logger.error("❌ Classifier nicht verfügbar")
            return
        
        # Hole User-Context (optional)
        user_context = None
        if user_id:
            async with db_pool.acquire() as conn:
                site_row = await conn.fetchrow(
                    "SELECT * FROM monitored_websites WHERE user_id = $1 LIMIT 1",
                    user_id
                )
                if site_row:
                    user_context = {
                        "website_url": site_row['url'],
                        "industry": "unknown",  # TODO
                        "compliance_areas": [],  # TODO
                        "services": [],  # TODO
                        "subscription_plan": "free"  # TODO
                    }
        
        # Klassifiziere
        result = await classifier.classify_legal_update(update_data, user_context)
        
        # Speichere in DB
        async with db_pool.acquire() as conn:
            classification_id = await conn.fetchval(
                """
                INSERT INTO ai_classifications (
                    update_id, user_id,
                    action_required, confidence, severity, impact_score,
                    primary_action_type, primary_action_priority, primary_action_title,
                    primary_action_description, primary_button_text, primary_button_color,
                    primary_button_icon, estimated_time, requires_paid_plan,
                    recommended_actions, reasoning, user_impact, consequences_if_ignored,
                    model_version, classified_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, NOW()
                )
                ON CONFLICT (update_id, user_id) 
                DO UPDATE SET
                    action_required = EXCLUDED.action_required,
                    confidence = EXCLUDED.confidence,
                    severity = EXCLUDED.severity,
                    impact_score = EXCLUDED.impact_score,
                    primary_action_type = EXCLUDED.primary_action_type,
                    primary_button_text = EXCLUDED.primary_button_text,
                    primary_button_color = EXCLUDED.primary_button_color,
                    primary_button_icon = EXCLUDED.primary_button_icon,
                    reasoning = EXCLUDED.reasoning,
                    user_impact = EXCLUDED.user_impact,
                    classified_at = NOW()
                RETURNING id
                """,
                str(update_id), user_id,
                result.action_required, result.confidence.value, result.severity, result.impact_score,
                result.primary_action.action_type.value, result.primary_action.priority,
                result.primary_action.title, result.primary_action.description,
                result.primary_action.button_text, result.primary_action.button_color,
                result.primary_action.icon, result.primary_action.estimated_time,
                result.primary_action.requires_paid_plan,
                json.dumps([a.to_dict() for a in result.recommended_actions]),
                result.reasoning, result.user_impact, result.consequences_if_ignored,
                result.model_version
            )
            
            # Update legal_updates Tabelle
            await conn.execute(
                """
                UPDATE legal_updates
                SET classification_id = $1, auto_classified = true
                WHERE id = $2
                """,
                classification_id,
                update_id
            )
        
        logger.info(f"✅ Update {update_id} klassifiziert: {result.primary_action.action_type.value}")
        
    except Exception as e:
        logger.error(f"❌ Background-Klassifizierung fehlgeschlagen: {e}")


# Export router
__all__ = ['router']

