"""
API Routes für Legal News Benachrichtigungen
Nutzer-Bestätigungsflow und Notification-Management
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from auth_routes import get_current_user
from database_service import DatabaseService
from legal_notification_service import legal_notification_service, init_legal_notification_service

router = APIRouter(prefix="/api/legal-notifications", tags=["Legal Notifications"])
db_service = DatabaseService()


class NotificationSettingsUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    min_severity: Optional[str] = None
    notify_areas: Optional[List[str]] = None
    instant_for_critical: Optional[bool] = None
    digest_frequency: Optional[str] = None


class NotificationResponse(BaseModel):
    id: int
    severity: str
    status: str
    action_required: bool
    action_deadline: Optional[str]
    sent_at: Optional[str]
    title: str
    summary: Optional[str]
    source: str
    url: Optional[str]
    published_date: str


@router.get("/pending", response_model=List[NotificationResponse])
async def get_pending_notifications(
    current_user: dict = Depends(get_current_user)
):
    """Holt alle ausstehenden Benachrichtigungen für den aktuellen User"""
    user_id = current_user.get("user_id")
    
    if not legal_notification_service:
        raise HTTPException(status_code=503, detail="Notification Service nicht verfügbar")
    
    notifications = await legal_notification_service.get_pending_notifications(user_id)
    
    return [
        NotificationResponse(
            id=n['id'],
            severity=n['severity'],
            status=n['status'],
            action_required=n['action_required'],
            action_deadline=n['action_deadline'].isoformat() if n['action_deadline'] else None,
            sent_at=n['sent_at'].isoformat() if n['sent_at'] else None,
            title=n['title'],
            summary=n['summary'],
            source=n['source'],
            url=n['url'],
            published_date=n['published_date'].isoformat()
        )
        for n in notifications
    ]


@router.get("/confirm/{token}")
async def confirm_notification(token: str):
    """Bestätigt eine Benachrichtigung (Nutzer hat zur Kenntnis genommen)"""
    if not legal_notification_service:
        raise HTTPException(status_code=503, detail="Notification Service nicht verfügbar")
    
    result = await legal_notification_service.confirm_notification(token)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Fehler bei Bestätigung"))
    
    return result


@router.get("/dismiss/{token}")
async def dismiss_notification(token: str):
    """Markiert eine Benachrichtigung als nicht relevant"""
    if not legal_notification_service:
        raise HTTPException(status_code=503, detail="Notification Service nicht verfügbar")
    
    result = await legal_notification_service.dismiss_notification(token)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Fehler beim Verwerfen"))
    
    return result


@router.get("/settings")
async def get_notification_settings(
    current_user: dict = Depends(get_current_user)
):
    """Holt die Benachrichtigungseinstellungen des Users"""
    user_id = current_user.get("user_id")
    
    async with db_service.pool.acquire() as conn:
        settings = await conn.fetchrow("""
            SELECT * FROM user_legal_notification_settings
            WHERE user_id = $1
        """, user_id)
        
        if not settings:
            return {
                "email_enabled": True,
                "in_app_enabled": True,
                "push_enabled": False,
                "min_severity": "medium",
                "notify_areas": ["dsgvo", "ttdsg", "cookie", "impressum", "barrierefreiheit", "ai_act"],
                "instant_for_critical": True,
                "digest_frequency": "daily"
            }
        
        return dict(settings)


@router.put("/settings")
async def update_notification_settings(
    settings: NotificationSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Aktualisiert die Benachrichtigungseinstellungen"""
    user_id = current_user.get("user_id")
    
    async with db_service.pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM user_legal_notification_settings WHERE user_id = $1",
            user_id
        )
        
        if existing:
            update_fields = []
            params = [user_id]
            param_count = 2
            
            if settings.email_enabled is not None:
                update_fields.append(f"email_enabled = ${param_count}")
                params.append(settings.email_enabled)
                param_count += 1
            
            if settings.in_app_enabled is not None:
                update_fields.append(f"in_app_enabled = ${param_count}")
                params.append(settings.in_app_enabled)
                param_count += 1
            
            if settings.push_enabled is not None:
                update_fields.append(f"push_enabled = ${param_count}")
                params.append(settings.push_enabled)
                param_count += 1
            
            if settings.min_severity is not None:
                update_fields.append(f"min_severity = ${param_count}")
                params.append(settings.min_severity)
                param_count += 1
            
            if settings.notify_areas is not None:
                update_fields.append(f"notify_areas = ${param_count}")
                params.append(settings.notify_areas)
                param_count += 1
            
            if settings.instant_for_critical is not None:
                update_fields.append(f"instant_for_critical = ${param_count}")
                params.append(settings.instant_for_critical)
                param_count += 1
            
            if settings.digest_frequency is not None:
                update_fields.append(f"digest_frequency = ${param_count}")
                params.append(settings.digest_frequency)
                param_count += 1
            
            if update_fields:
                query = f"""
                    UPDATE user_legal_notification_settings
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $1
                """
                await conn.execute(query, *params)
        else:
            await conn.execute("""
                INSERT INTO user_legal_notification_settings (
                    user_id, email_enabled, in_app_enabled, push_enabled,
                    min_severity, notify_areas, instant_for_critical, digest_frequency
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                user_id,
                settings.email_enabled if settings.email_enabled is not None else True,
                settings.in_app_enabled if settings.in_app_enabled is not None else True,
                settings.push_enabled if settings.push_enabled is not None else False,
                settings.min_severity or "medium",
                settings.notify_areas or ["dsgvo", "ttdsg", "cookie", "impressum", "barrierefreiheit", "ai_act"],
                settings.instant_for_critical if settings.instant_for_critical is not None else True,
                settings.digest_frequency or "daily"
            )
    
    return {"success": True, "message": "Einstellungen aktualisiert"}


@router.get("/stats")
async def get_notification_stats(
    current_user: dict = Depends(get_current_user)
):
    """Holt Statistiken über Benachrichtigungen"""
    user_id = current_user.get("user_id")
    
    async with db_service.pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'sent') as sent,
                COUNT(*) FILTER (WHERE status = 'confirmed') as confirmed,
                COUNT(*) FILTER (WHERE status = 'dismissed') as dismissed,
                COUNT(*) FILTER (WHERE severity = 'critical' AND status IN ('pending', 'sent')) as critical_pending,
                COUNT(*) FILTER (WHERE action_required = TRUE AND status IN ('pending', 'sent')) as action_required
            FROM legal_change_notifications
            WHERE user_id = $1
        """, user_id)
        
        return dict(stats) if stats else {
            "pending": 0, "sent": 0, "confirmed": 0, "dismissed": 0,
            "critical_pending": 0, "action_required": 0
        }


@router.post("/process-new")
async def trigger_process_new_changes(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Manueller Trigger zum Verarbeiten neuer Gesetzesänderungen (Admin only)"""
    if not legal_notification_service:
        raise HTTPException(status_code=503, detail="Notification Service nicht verfügbar")
    
    background_tasks.add_task(legal_notification_service.process_new_legal_changes)
    
    return {"success": True, "message": "Verarbeitung gestartet"}
