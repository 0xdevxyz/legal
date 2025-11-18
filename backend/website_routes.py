"""
Website Management Routes - Complyo
Handles tracked websites with persistence and limits
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import traceback
import logging

logger = logging.getLogger(__name__)

# Global references (set in main_production.py)
db_pool = None
auth_service = None

router = APIRouter(prefix="/api/v2/websites", tags=["websites"])
security = HTTPBearer()

# Pydantic Models
class WebsiteCreate(BaseModel):
    url: str
    score: int

class TrackedWebsite(BaseModel):
    id: int
    url: str
    last_score: int
    last_scan_date: str
    scan_count: int
    is_primary: bool

class WebsitesResponse(BaseModel):
    success: bool
    websites: List[TrackedWebsite]

class WebsiteResponse(BaseModel):
    success: bool
    website: TrackedWebsite

# Dependency for auth
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return user data"""
    try:
        token = credentials.credentials
        user_data = auth_service.verify_token(token)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        logger.info(f"User authenticated: {user_data.get('user_id')}")
        return user_data
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Not authenticated")

@router.get("", response_model=WebsitesResponse)
async def get_websites(user=Depends(get_current_user)):
    """Get all tracked websites for the current user"""
    try:
        user_id = user.get("id") or user.get("user_id")
        
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database not available")
        
        if not user_id:
            logger.error(f"No user_id in token: {user}")
            raise HTTPException(status_code=403, detail="User ID not found in token")
        
        async with db_pool.acquire() as conn:
            # Get tracked websites
            rows = await conn.fetch("""
                SELECT 
                    id,
                    url,
                    last_score,
                    last_scan_date,
                    scan_count,
                    is_primary,
                    created_at
                FROM tracked_websites
                WHERE user_id = $1
                ORDER BY is_primary DESC, last_scan_date DESC
            """, user_id)
            
            websites = [
                {
                    "id": row["id"],
                    "url": row["url"],
                    "last_score": row["last_score"],
                    "last_scan_date": row["last_scan_date"].isoformat() if row["last_scan_date"] else None,
                    "scan_count": row["scan_count"],
                    "is_primary": row["is_primary"]
                }
                for row in rows
            ]
            
            return {
                "success": True,
                "websites": websites
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching websites: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch websites: {str(e)}")

@router.post("", response_model=WebsiteResponse)
async def save_website(data: WebsiteCreate, user=Depends(get_current_user)):
    """Save or update a tracked website"""
    try:
        user_id = user.get("user_id")
        
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            # Check if website already exists
            existing = await conn.fetchrow("""
                SELECT id, scan_count, is_primary
                FROM tracked_websites
                WHERE user_id = $1 AND url = $2
            """, user_id, data.url)
            
            if existing:
                # Update existing website
                website = await conn.fetchrow("""
                    UPDATE tracked_websites
                    SET 
                        last_score = $1,
                        last_scan_date = $2,
                        scan_count = scan_count + 1
                    WHERE id = $3
                    RETURNING 
                        id, url, last_score, last_scan_date, 
                        scan_count, is_primary
                """, data.score, datetime.utcnow(), existing["id"])
            else:
                # Check user limits
                user_limits = await conn.fetchrow("""
                    SELECT websites_max, websites_count
                    FROM user_limits
                    WHERE user_id = $1
                """, user_id)
                
                if user_limits and user_limits["websites_count"] >= user_limits["websites_max"]:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Website limit reached ({user_limits['websites_max']} websites)"
                    )
                
                # Check if this is the first website (make it primary)
                website_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM tracked_websites WHERE user_id = $1
                """, user_id)
                
                is_primary = (website_count == 0)
                
                # Create new website
                website = await conn.fetchrow("""
                    INSERT INTO tracked_websites (
                        user_id, url, last_score, last_scan_date, 
                        scan_count, is_primary
                    )
                    VALUES ($1, $2, $3, $4, 1, $5)
                    RETURNING 
                        id, url, last_score, last_scan_date, 
                        scan_count, is_primary
                """, user_id, data.url, data.score, datetime.utcnow(), is_primary)
                
                # Update user_limits.websites_count
                await conn.execute("""
                    UPDATE user_limits
                    SET websites_count = websites_count + 1
                    WHERE user_id = $1
                """, user_id)
                
                # Create eRecht24 project for new website
                try:
                    from erecht24_service import erecht24_service
                    from urllib.parse import urlparse
                    
                    # Extract domain from URL
                    parsed_url = urlparse(data.url)
                    domain = parsed_url.netloc or parsed_url.path
                    
                    erecht24_project = await erecht24_service.create_project(domain, user_id)
                    
                    if erecht24_project:
                        # Save eRecht24 credentials
                        await conn.execute("""
                            INSERT INTO erecht24_projects (
                                website_id,
                                erecht24_project_id,
                                erecht24_api_key,
                                erecht24_secret
                            ) VALUES ($1, $2, $3, $4)
                        """,
                            website["id"],
                            erecht24_project["project_id"],
                            erecht24_project.get("api_key"),
                            erecht24_project.get("secret")
                        )
                        logger.info(f"✅ eRecht24-Projekt erstellt für Website #{website['id']}")
                except Exception as e:
                    # Nicht kritisch - Website wurde trotzdem gespeichert
                    logger.warning(f"eRecht24-Projekt konnte nicht erstellt werden: {e}")
            
            return {
                "success": True,
                "website": {
                    "id": website["id"],
                    "url": website["url"],
                    "last_score": website["last_score"],
                    "last_scan_date": website["last_scan_date"].isoformat() if website["last_scan_date"] else None,
                    "scan_count": website["scan_count"],
                    "is_primary": website["is_primary"]
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error saving website: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to save website: {str(e)}")

@router.delete("/{website_id}")
async def delete_website(website_id: int, user=Depends(get_current_user)):
    """Delete a tracked website"""
    try:
        user_id = user.get("user_id")
        
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            # Check if website exists and belongs to user
            website = await conn.fetchrow("""
                SELECT id, is_primary
                FROM tracked_websites
                WHERE id = $1 AND user_id = $2
            """, website_id, user_id)
            
            if not website:
                raise HTTPException(status_code=404, detail="Website not found")
            
            if website["is_primary"]:
                raise HTTPException(
                    status_code=403,
                    detail="Cannot delete primary website"
                )
            
            # Delete website
            await conn.execute("""
                DELETE FROM tracked_websites
                WHERE id = $1
            """, website_id)
            
            # Update user_limits.websites_count
            await conn.execute("""
                UPDATE user_limits
                SET websites_count = websites_count - 1
                WHERE user_id = $1
            """, user_id)
            
            return {"success": True, "message": "Website deleted"}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting website: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to delete website: {str(e)}")

@router.get("/{website_id}/last-scan")
async def get_last_scan(
    website_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the last scan result for a specific website
    """
    try:
        user_id = user.get('user_id')
        
        async with db_pool.acquire() as conn:
            # Verify website belongs to user
            website = await conn.fetchrow("""
                SELECT id FROM tracked_websites
                WHERE id = $1 AND user_id = $2
            """, website_id, user_id)
            
            if not website:
                raise HTTPException(status_code=404, detail="Website not found")
            
            # Get last scan
            scan = await conn.fetchrow("""
                SELECT scan_id, scan_data, compliance_score, 
                       critical_issues, warning_issues, total_risk_euro, scan_timestamp
                FROM scan_history
                WHERE website_id = $1
                ORDER BY scan_timestamp DESC
                LIMIT 1
            """, website_id)
            
            if not scan:
                raise HTTPException(status_code=404, detail="No scan history found")
            
            return {
                "success": True,
                "scan": {
                    "scan_id": scan['scan_id'],
                    "data": scan['scan_data'],
                    "compliance_score": scan['compliance_score'],
                    "critical_issues": scan['critical_issues'],
                    "warning_issues": scan['warning_issues'],
                    "total_risk_euro": scan['total_risk_euro'],
                    "scan_timestamp": scan['scan_timestamp'].isoformat()
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting last scan: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get last scan: {str(e)}")

@router.get("/{website_id}/score-history")
async def get_score_history(
    website_id: int,
    days: int = 30,
    user=Depends(get_current_user)
):
    """
    Get score history for a website
    
    Args:
        website_id: Website ID
        days: Number of days to look back (default: 30)
    
    Returns:
        List of score history entries
    """
    try:
        user_id = user.get("user_id")
        
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            # Verify website belongs to user
            website = await conn.fetchrow("""
                SELECT id FROM tracked_websites
                WHERE id = $1 AND user_id = $2
            """, website_id, user_id)
            
            if not website:
                raise HTTPException(status_code=404, detail="Website not found")
            
            # Get score history
            history = await conn.fetch("""
                SELECT 
                    created_at as date,
                    compliance_score as score,
                    critical_issues_count,
                    scan_type
                FROM score_history
                WHERE website_id = $1
                  AND created_at >= NOW() - ($2 || ' days')::INTERVAL
                ORDER BY created_at ASC
            """, website_id, days)
            
            return [
                {
                    "date": entry["date"].isoformat(),
                    "score": entry["score"],
                    "critical_count": entry["critical_issues_count"],
                    "scan_type": entry["scan_type"]
                }
                for entry in history
            ]
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting score history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get score history: {str(e)}")

