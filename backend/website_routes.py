"""
Website Management Routes - Complyo
Handles tracked websites with persistence and limits
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from uuid import UUID
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
    id: Union[str, int, UUID]
    url: str
    last_score: int
    last_scan_date: Optional[str] = None
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

# ✅ Helper function to extract user_id from token (with DB lookup)
async def get_user_id_from_token(user: Dict[str, Any]) -> Any:
    """Extract user_id from token and verify in database"""
    user_id_from_token = user.get("id") or user.get("user_id")
    
    if not user_id_from_token:
        logger.error(f"No user_id in token: {user}")
        raise HTTPException(status_code=403, detail="User ID not found in token")
    
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not available")
    
    # ✅ Hole echte user_id aus DB (kann UUID sein)
    async with db_pool.acquire() as conn:
        db_user = await conn.fetchrow(
            "SELECT id FROM users WHERE id::text = $1 OR email = $2 LIMIT 1",
            str(user_id_from_token),
            user.get("email", "")
        )
        
        if not db_user:
            logger.error(f"User not found in database for token: {user_id_from_token}")
            raise HTTPException(status_code=403, detail="User not found in database")
        
        return db_user["id"]

@router.get("", response_model=WebsitesResponse)
async def get_websites(user=Depends(get_current_user)):
    """Get all tracked websites for the current user"""
    try:
        # ✅ FIX: Verwende Helper-Funktion für user_id
        user_id = await get_user_id_from_token(user)
        
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
                    "id": str(row["id"]),
                    "url": row["url"],
                    "last_score": int(row["last_score"]) if row["last_score"] is not None else 0,
                    "last_scan_date": row["last_scan_date"].isoformat() if row["last_scan_date"] else None,
                    "scan_count": int(row.get("scan_count", 0)) if row.get("scan_count") is not None else 0,
                    "is_primary": bool(row.get("is_primary", False))
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
        # ✅ FIX: Verwende Helper-Funktion für user_id
        user_id = await get_user_id_from_token(user)
        
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
                
                # ✅ NEU: Erstelle automatisch eine Cookie-Banner-Konfiguration
                try:
                    from urllib.parse import urlparse
                    import json
                    
                    # Generate site_id from URL
                    parsed_url = urlparse(data.url if data.url.startswith('http') else f'https://{data.url}')
                    hostname = parsed_url.netloc or parsed_url.path
                    hostname = hostname.replace('www.', '')
                    site_id = hostname.replace('.', '-').lower()
                    
                    # Prüfe ob bereits eine Config existiert
                    existing_config = await conn.fetchrow(
                        "SELECT id FROM cookie_banner_configs WHERE site_id = $1",
                        site_id
                    )
                    
                    if not existing_config:
                        # Erstelle Default-Cookie-Banner-Konfiguration
                        default_texts = {
                            "de": {
                                "title": "Datenschutz-Präferenz",
                                "description": "Wir benötigen Ihre Einwilligung, bevor Sie unsere Website weiter besuchen können.\n\nWenn Sie unter 16 Jahre alt sind und Ihre Einwilligung zu optionalen Services geben möchten, müssen Sie Ihre Erziehungsberechtigten um Erlaubnis bitten.\n\nWir verwenden Cookies und andere Technologien auf unserer Website. Einige von ihnen sind essenziell, während andere uns helfen, diese Website und Ihre Erfahrung zu verbessern.",
                                "accept_all": "Alle akzeptieren",
                                "reject_all": "Nur essenzielle Cookies akzeptieren",
                                "accept_selected": "Speichern",
                                "settings": "Individuelle Datenschutzeinstellungen",
                                "necessary": "Essenziell",
                                "necessaryDesc": "Essenzielle Services ermöglichen grundlegende Funktionen.",
                                "functional": "Funktional",
                                "functionalDesc": "Funktionale Cookies speichern Ihre Präferenzen.",
                                "analytics": "Statistiken",
                                "analyticsDesc": "Statistik-Cookies helfen uns zu verstehen, wie Besucher interagieren.",
                                "marketing": "Externe Medien",
                                "marketingDesc": "Inhalte von Videoplattformen und Social-Media werden standardmäßig blockiert.",
                                "privacy_link": "Datenschutzerklärung",
                                "imprint_link": "Impressum"
                            }
                        }
                        
                        await conn.execute("""
                            INSERT INTO cookie_banner_configs (
                                site_id, user_id, layout, primary_color, accent_color,
                                text_color, bg_color, button_style, position, width_mode,
                                texts, services, show_on_pages, geo_restriction,
                                auto_block_scripts, respect_dnt, cookie_lifetime_days,
                                show_branding, is_active, last_scan_url
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                        """,
                            site_id,
                            user_id,
                            'box_modal',  # Default Layout
                            '#7c3aed',    # Primary Color (Violet)
                            '#8b5cf6',    # Accent Color
                            '#333333',    # Text Color
                            '#ffffff',    # Background Color
                            'rounded',    # Button Style
                            'center',     # Position
                            'boxed',      # Width Mode
                            json.dumps(default_texts),
                            json.dumps([]),  # Services - leer, wird durch Scan gefüllt
                            json.dumps({"all": True, "exclude": []}),
                            json.dumps({"enabled": False, "countries": []}),
                            True,         # Auto-block scripts
                            True,         # Respect DNT
                            365,          # Cookie lifetime
                            True,         # Show branding
                            True,         # Is active
                            data.url      # Last scan URL
                        )
                        logger.info(f"✅ Cookie-Banner-Config erstellt für site_id: {site_id}")
                except Exception as e:
                    logger.warning(f"Cookie-Banner-Config konnte nicht erstellt werden: {e}")
                    # Nicht kritisch - kann später manuell erstellt werden
                
                # Create eRecht24 project for new website
                try:
                    from erecht24_service import erecht24_service
                    
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
                    "id": str(website["id"]),
                    "url": website["url"],
                    "last_score": int(website["last_score"]) if website["last_score"] is not None else 0,
                    "last_scan_date": website["last_scan_date"].isoformat() if website["last_scan_date"] else None,
                    "scan_count": int(website.get("scan_count", 0)) if website.get("scan_count") is not None else 0,
                    "is_primary": bool(website.get("is_primary", False))
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error saving website: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to save website: {str(e)}")

@router.delete("/{website_id}")
async def delete_website(website_id: str, user=Depends(get_current_user)):
    """Delete a tracked website"""
    try:
        # ✅ FIX: Verwende Helper-Funktion für user_id
        user_id = await get_user_id_from_token(user)
        
        # Convert website_id to UUID
        try:
            from uuid import UUID as UUIDType
            website_uuid = UUIDType(website_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid website ID format")
        
        async with db_pool.acquire() as conn:
            # Check if website exists and belongs to user
            website = await conn.fetchrow("""
                SELECT id, is_primary
                FROM tracked_websites
                WHERE id = $1 AND user_id = $2
            """, website_uuid, user_id)
            
            if not website:
                raise HTTPException(status_code=404, detail="Website not found")
            
            if website["is_primary"]:
                raise HTTPException(
                    status_code=403,
                    detail="Die primäre Website kann nicht gelöscht werden. Diese Verknüpfung ist dauerhaft. Bitte kontaktieren Sie den Support unter support@complyo.tech für Änderungen."
                )
            
            # Delete website
            await conn.execute("""
                DELETE FROM tracked_websites
                WHERE id = $1
            """, website_uuid)
            
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
    website_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get last scan for a website"""
    try:
        # ✅ FIX: Verwende Helper-Funktion für user_id
        user_id = await get_user_id_from_token(user)
        
        # Convert website_id to UUID
        try:
            from uuid import UUID as UUIDType
            website_uuid = UUIDType(website_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid website ID format")
        
        async with db_pool.acquire() as conn:
            # Verify website belongs to user
            website = await conn.fetchrow("""
                SELECT id FROM tracked_websites
                WHERE id = $1 AND user_id = $2
            """, website_uuid, user_id)
            
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
            """, website_uuid)
            
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
    website_id: str,
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
        user_id = await get_user_id_from_token(user)
        
        try:
            from uuid import UUID as UUIDType
            website_uuid = UUIDType(website_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid website ID format")
        
        async with db_pool.acquire() as conn:
            website = await conn.fetchrow("""
                SELECT id, url FROM tracked_websites
                WHERE id = $1 AND user_id = $2
            """, website_uuid, user_id)
            
            if not website:
                raise HTTPException(status_code=404, detail="Website not found")
            
            history = await conn.fetch("""
                SELECT 
                    scan_date as date,
                    overall_score as score,
                    pillar_scores,
                    id
                FROM score_history
                WHERE website_id = $1 AND user_id = $2
                  AND scan_date >= NOW() - ($3 || ' days')::INTERVAL
                ORDER BY scan_date ASC
            """, website_uuid, user_id, days)
            
            if not history:
                history = await conn.fetch("""
                    SELECT 
                        COALESCE(scan_date, scan_timestamp, created_at) as date,
                        COALESCE(overall_score, compliance_score)::int as score,
                        critical_issues as critical_count,
                        scan_data
                    FROM scan_history
                    WHERE (website_id = $1 OR url = $2) AND user_id = $3
                      AND COALESCE(scan_date, scan_timestamp, created_at) >= NOW() - ($4 || ' days')::INTERVAL
                    ORDER BY COALESCE(scan_date, scan_timestamp, created_at) ASC
                """, website_uuid, website["url"], user_id, days)
                
                return [
                    {
                        "date": entry["date"].isoformat() if entry["date"] else None,
                        "score": int(entry["score"]) if entry["score"] else 0,
                        "critical_count": entry["critical_count"] or 0,
                        "scan_type": "scan"
                    }
                    for entry in history
                ]
            
            result = []
            for entry in history:
                pillar_scores = entry["pillar_scores"] or {}
                critical_count = pillar_scores.get("critical_issues", 0) if isinstance(pillar_scores, dict) else 0
                result.append({
                    "date": entry["date"].isoformat() if entry["date"] else None,
                    "score": entry["score"] or 0,
                    "critical_count": critical_count,
                    "scan_type": "scored"
                })
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting score history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get score history: {str(e)}")

