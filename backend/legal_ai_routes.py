"""
Legal AI Routes - Gesetzesänderungen mit KI-Klassifizierung
"""

from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal-ai", tags=["legal-ai"])

# Global db_pool - wird von main_production.py gesetzt
db_pool = None


async def get_current_user(authorization: str = None):
    """Dependency für User-Auth (vereinfacht)"""
    # TODO: Echte Auth implementieren
    return {"user_id": "test-user"}


@router.get("/updates")
async def get_legal_updates(
    limit: int = Query(default=6, ge=1, le=50),
    include_info_only: bool = Query(default=False),
    current_user: Dict = Depends(get_current_user)
):
    """
    Liefert KI-klassifizierte Gesetzesänderungen
    
    Returns:
        List of legal updates with AI classification
    """
    try:
        if db_pool is None:
            logger.error("❌ db_pool is not initialized!")
            return []
        
        async with db_pool.acquire() as connection:
            # Filter nach action_required wenn include_info_only=False
            where_clause = "WHERE is_active = TRUE"
            if not include_info_only:
                where_clause += " AND (action_required IS NOT NULL AND action_required != '')"
            
            query = f"""
                SELECT 
                    id,
                    title,
                    description,
                    summary,
                    content,
                    url,
                    source,
                    update_type,
                    severity,
                    impact_level,
                    affected_areas,
                    published_date as published_at,
                    action_required
                FROM legal_updates
                {where_clause}
                ORDER BY published_date DESC NULLS LAST
                LIMIT $1
            """
            
            rows = await connection.fetch(query, limit)
            
            # Konvertiere zu Dict und füge KI-Klassifizierung hinzu
            updates = []
            for row in rows:
                update = dict(row)
                
                # KI-Klassifizierung (vereinfacht - später durch echte AI ersetzen)
                classification = await classify_legal_update(update)
                
                updates.append({
                    **update,
                    **classification
                })
            
            logger.info(f"✅ Loaded {len(updates)} legal updates")
            return updates
            
    except Exception as e:
        logger.error(f"❌ Error loading legal updates: {e}")
        return []


async def classify_legal_update(update: Dict[str, Any]) -> Dict[str, Any]:
    """
    KI-Klassifizierung für Gesetzesänderung (vereinfacht)
    
    TODO: Später durch echte AI/LLM ersetzen
    """
    severity = update.get('severity', 'info')
    update_type = update.get('update_type', 'law_change')
    
    # Bestimme Action-Type basierend auf update_type
    action_mapping = {
        'DSGVO': {
            'action_type': 'update_privacy_policy',
            'button_text': 'Datenschutz prüfen',
            'button_color': 'orange',
            'icon': 'Shield'
        },
        'Impressum': {
            'action_type': 'update_impressum',
            'button_text': 'Impressum aktualisieren',
            'button_color': 'blue',
            'icon': 'FileText'
        },
        'Cookies': {
            'action_type': 'update_cookie_banner',
            'button_text': 'Cookie-Banner prüfen',
            'button_color': 'orange',
            'icon': 'Eye'
        },
        'Barrierefreiheit': {
            'action_type': 'check_accessibility',
            'button_text': 'Barrierefreiheit prüfen',
            'button_color': 'blue',
            'icon': 'Zap'
        },
        'default': {
            'action_type': 'scan_website',
            'button_text': 'Website scannen',
            'button_color': 'red',
            'icon': 'Search'
        }
    }
    
    # Finde passende Action
    action = action_mapping.get(update_type, action_mapping['default'])
    
    # Impact-Score berechnen (vereinfacht)
    impact_score = 5.0
    if severity == 'critical':
        impact_score = 9.0
    elif severity == 'warning':
        impact_score = 7.0
    elif severity == 'info':
        impact_score = 4.0
    
    # Confidence basierend auf Vollständigkeit der Daten
    confidence = 'medium'
    if update.get('description') and update.get('action_required'):
        confidence = 'high'
    
    return {
        'action_required': bool(update.get('action_required')),
        'confidence': confidence,
        'impact_score': impact_score,
        'primary_action': action,
        'reasoning': update.get('description', 'Keine Details verfügbar'),
        'user_impact': update.get('action_required', 'Diese Änderung sollte geprüft werden'),
        'consequences_if_ignored': 'Bei Nicht-Umsetzung können rechtliche Risiken entstehen',
        'classification_id': update.get('id')
    }


@router.post("/feedback")
async def submit_feedback(
    feedback_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """
    Speichert User-Feedback für KI-Verbesserung
    """
    logger.info(f"📝 Feedback received: {feedback_data.get('feedback_type')}")
    
    # TODO: In Datenbank speichern für ML-Training
    
    return {"success": True, "message": "Feedback gespeichert"}


# Health Check
@router.get("/health")
async def health_check():
    """Health check für Legal AI Service"""
    return {
        "status": "ok",
        "service": "legal-ai",
        "timestamp": datetime.utcnow().isoformat()
    }

