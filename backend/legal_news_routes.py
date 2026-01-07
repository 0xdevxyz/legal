"""
Legal News API Routes für Complyo
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal", tags=["legal-news"])

# Global variables - werden von main_production.py gesetzt
db_pool = None
news_service = None

# Response Models
class NewsItem(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    summary: str
    date: str
    source: str
    url: Optional[str] = None
    is_featured: bool = False

class NewsResponse(BaseModel):
    success: bool
    news: List[NewsItem]
    total: int

class NewsStatsResponse(BaseModel):
    success: bool
    stats: dict

@router.get("/news", response_model=NewsResponse)
async def get_legal_news(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = Query(None, regex="^(critical|warning|info)$")
):
    """
    Holt die neuesten rechtlichen Neuigkeiten
    
    - **limit**: Anzahl der News (1-50, default: 10)
    - **offset**: Offset für Pagination (default: 0)
    - **severity**: Filter nach Severity ('critical', 'warning', 'info')
    """
    try:
        from main_production import news_service
        
        if not news_service:
            raise HTTPException(status_code=503, detail="News service not available")
        
        news = await news_service.get_recent_news(
            limit=limit,
            offset=offset,
            severity=severity
        )
        
        return {
            "success": True,
            "news": news,
            "total": len(news)
        }
        
    except Exception as e:
        logger.error(f"Error in get_legal_news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/stats", response_model=NewsStatsResponse)
async def get_news_stats():
    """
    Gibt Statistiken über die rechtlichen Neuigkeiten zurück
    """
    try:
        if not news_service:
            logger.error("❌ news_service is not initialized!")
            raise HTTPException(status_code=503, detail="News service not available")
        
        stats = await news_service.get_news_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error in get_news_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/news/fetch")
async def fetch_feeds():
    """
    Triggert manuell das Fetchen aller RSS-Feeds
    (Normalerweise wird dies automatisch per Cronjob gemacht)
    """
    try:
        if not news_service:
            raise HTTPException(status_code=503, detail="News service not available")
        
        results = await news_service.fetch_all_feeds()
        
        return {
            "success": True,
            "message": "Feeds fetched successfully",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_feeds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Global reference (wird in main_production.py gesetzt)
db_pool = None

@router.get("/updates")
async def get_legal_updates(
    limit: int = Query(10, ge=1, le=50),
    severity: Optional[str] = Query(None)
):
    """
    Holt Gesetzesänderungen und rechtliche Updates aus der legal_updates Tabelle
    
    Args:
        limit: Anzahl der Updates
        severity: Filter nach Severity ('critical', 'warning', 'info')
        
    Returns:
        Liste von legal updates
    """
    try:
        if not db_pool:
            # Fallback auf Demo-Daten wenn DB nicht verfügbar
            return {
                "success": True,
                "updates": []
            }
        
        async with db_pool.acquire() as conn:
            query = """
                SELECT 
                    id,
                    update_type,
                    title,
                    description,
                    severity,
                    action_required,
                    source,
                    published_at,
                    effective_date,
                    url
                FROM legal_updates
            """
            params = []
            
            if severity:
                query += " WHERE severity = $1"
                params.append(severity)
            
            query += " ORDER BY published_at DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            
            updates = [
                {
                    "id": row["id"],
                    "update_type": row["update_type"],
                    "title": row["title"],
                    "description": row["description"],
                    "severity": row["severity"],
                    "action_required": row["action_required"],
                    "source": row["source"],
                    "published_at": row["published_at"].isoformat(),
                    "effective_date": row["effective_date"].isoformat() if row["effective_date"] else None,
                    "url": row["url"]
                }
                for row in rows
            ]
            
            return {
                "success": True,
                "updates": updates
            }
            
    except Exception as e:
        logger.error(f"Error fetching legal updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

