"""
Accessibility Alt-Text API Routes
Endpoints für KI-generierte Alt-Texte für Bilder
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/accessibility", tags=["accessibility-alt-text"])
security = HTTPBearer(auto_error=False)

db_pool = None
auth_service = None

class ImageToFix(BaseModel):
    url: str
    selector: Optional[str] = None
    context: Optional[str] = None
    original_alt: Optional[str] = None

class GenerateAltTextsRequest(BaseModel):
    site_id: str
    images: List[ImageToFix]
    language: str = "de"

class ApproveAltTextRequest(BaseModel):
    fix_id: str
    approved: bool
    custom_alt: Optional[str] = None

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """Optional auth - returns None if not authenticated"""
    if not credentials:
        return None
    try:
        token = credentials.credentials
        user_data = auth_service.verify_token(token)
        return user_data
    except:
        return None

async def get_required_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Required auth - raises 401 if not authenticated"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        token = credentials.credentials
        user_data = auth_service.verify_token(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid token")
        if "user_id" not in user_data and "id" in user_data:
            user_data["user_id"] = user_data["id"]
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.get("/alt-text-fixes")
async def get_alt_text_fixes(
    site_id: str = Query(..., description="Site ID for which to get fixes"),
    status: Optional[str] = Query(None, description="Filter by status: pending, applied, rejected"),
    approved_only: bool = Query(False, description="Return only approved fixes")
):
    """
    Public endpoint - Widget ruft diese Route auf um Alt-Texte zu laden
    Keine Auth erforderlich, da Widget auf Kundenwebsites läuft
    """
    try:
        async with db_pool.acquire() as conn:
            if approved_only:
                fixes = await conn.fetch("""
                    SELECT image_url, image_selector, generated_alt, confidence
                    FROM accessibility_alt_text_fixes
                    WHERE site_id = $1 AND is_approved = TRUE
                    ORDER BY created_at DESC
                """, UUID(site_id))
            elif status:
                fixes = await conn.fetch("""
                    SELECT id, image_url, image_selector, original_alt, generated_alt, 
                           confidence, source, status, is_approved, created_at
                    FROM accessibility_alt_text_fixes
                    WHERE site_id = $1 AND status = $2
                    ORDER BY created_at DESC
                """, UUID(site_id), status)
            else:
                fixes = await conn.fetch("""
                    SELECT id, image_url, image_selector, original_alt, generated_alt,
                           confidence, source, status, is_approved, created_at
                    FROM accessibility_alt_text_fixes
                    WHERE site_id = $1
                    ORDER BY created_at DESC
                """, UUID(site_id))
            
            return {
                "success": True,
                "fixes": [
                    {
                        "id": str(f.get("id", "")),
                        "image_url": f["image_url"],
                        "selector": f.get("image_selector"),
                        "alt_text": f["generated_alt"],
                        "original_alt": f.get("original_alt"),
                        "confidence": float(f.get("confidence", 0.9)),
                        "status": f.get("status", "pending"),
                        "is_approved": f.get("is_approved", False)
                    }
                    for f in fixes
                ],
                "count": len(fixes)
            }
    except Exception as e:
        logger.error(f"Error fetching alt-text fixes: {e}")
        return {"success": True, "fixes": [], "count": 0}


@router.post("/generate-alt-texts")
async def generate_alt_texts(
    request: GenerateAltTextsRequest,
    current_user: Dict[str, Any] = Depends(get_required_user)
):
    """
    Generiert KI-Alt-Texte für eine Liste von Bildern
    Requires authentication
    """
    from compliance_engine.ai_alt_text_generator import AIAltTextGenerator
    
    try:
        generator = AIAltTextGenerator()
        user_id = current_user.get("user_id") or current_user.get("id")
        site_uuid = UUID(request.site_id)
        
        results = []
        async with db_pool.acquire() as conn:
            for img in request.images:
                try:
                    existing = await conn.fetchrow("""
                        SELECT id, generated_alt, is_approved
                        FROM accessibility_alt_text_fixes
                        WHERE site_id = $1 AND image_url = $2
                    """, site_uuid, img.url)
                    
                    if existing:
                        results.append({
                            "image_url": img.url,
                            "alt_text": existing["generated_alt"],
                            "is_new": False,
                            "is_approved": existing["is_approved"]
                        })
                        continue
                    
                    ai_result = await generator.generate_alt_text(
                        image_url=img.url,
                        context=img.context,
                        language=request.language
                    )
                    
                    await conn.execute("""
                        INSERT INTO accessibility_alt_text_fixes 
                        (site_id, user_id, image_url, image_selector, original_alt, 
                         generated_alt, confidence, source, status)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')
                        ON CONFLICT (site_id, image_url) DO UPDATE SET
                            generated_alt = EXCLUDED.generated_alt,
                            confidence = EXCLUDED.confidence,
                            updated_at = NOW()
                    """, 
                        site_uuid,
                        user_id,
                        img.url,
                        img.selector,
                        img.original_alt,
                        ai_result["alt_text"],
                        ai_result.get("confidence", 0.9),
                        ai_result.get("source", "openai_vision")
                    )
                    
                    results.append({
                        "image_url": img.url,
                        "alt_text": ai_result["alt_text"],
                        "confidence": ai_result.get("confidence", 0.9),
                        "is_new": True,
                        "source": ai_result.get("source", "openai_vision")
                    })
                    
                except Exception as img_err:
                    logger.error(f"Error generating alt for {img.url}: {img_err}")
                    results.append({
                        "image_url": img.url,
                        "error": str(img_err)
                    })
        
        return {
            "success": True,
            "generated": len([r for r in results if not r.get("error")]),
            "errors": len([r for r in results if r.get("error")]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Alt-text generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/approve-alt-text")
async def approve_alt_text(
    request: ApproveAltTextRequest,
    current_user: Dict[str, Any] = Depends(get_required_user)
):
    """
    Genehmigt oder ändert einen generierten Alt-Text
    """
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        
        async with db_pool.acquire() as conn:
            fix = await conn.fetchrow("""
                SELECT id, user_id FROM accessibility_alt_text_fixes WHERE id = $1
            """, UUID(request.fix_id))
            
            if not fix:
                raise HTTPException(status_code=404, detail="Fix not found")
            
            if str(fix["user_id"]) != str(user_id):
                raise HTTPException(status_code=403, detail="Not authorized")
            
            if request.custom_alt:
                await conn.execute("""
                    UPDATE accessibility_alt_text_fixes
                    SET is_approved = $1, generated_alt = $2, 
                        status = CASE WHEN $1 THEN 'applied' ELSE 'rejected' END,
                        updated_at = NOW()
                    WHERE id = $3
                """, request.approved, request.custom_alt, UUID(request.fix_id))
            else:
                await conn.execute("""
                    UPDATE accessibility_alt_text_fixes
                    SET is_approved = $1, 
                        status = CASE WHEN $1 THEN 'applied' ELSE 'rejected' END,
                        updated_at = NOW()
                    WHERE id = $2
                """, request.approved, UUID(request.fix_id))
            
            return {
                "success": True,
                "fix_id": request.fix_id,
                "is_approved": request.approved
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving alt-text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan-images")
async def scan_images_for_alt_text(
    site_url: str = Query(..., description="URL to scan for images without alt"),
    site_id: str = Query(..., description="Site ID to associate fixes"),
    current_user: Dict[str, Any] = Depends(get_required_user)
):
    """
    Scannt eine Website nach Bildern ohne Alt-Attribut
    Generiert automatisch Alt-Texte für alle gefundenen Bilder
    """
    from compliance_engine.browser_renderer import smart_fetch_html
    from bs4 import BeautifulSoup
    from compliance_engine.ai_alt_text_generator import AIAltTextGenerator
    from urllib.parse import urljoin, urlparse
    
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        site_uuid = UUID(site_id)
        
        html, metadata = await smart_fetch_html(site_url)
        if not html:
            raise HTTPException(status_code=400, detail="Could not fetch page")
        
        soup = BeautifulSoup(html, 'html.parser')
        images_without_alt = []
        
        for img in soup.find_all('img'):
            alt = img.get('alt', '')
            src = img.get('src', '') or img.get('data-src', '')
            
            if not src:
                continue
            
            if not src.startswith(('http://', 'https://', 'data:')):
                src = urljoin(site_url, src)
            
            if not alt or alt.strip() == '':
                parent_text = ""
                figcaption = img.find_parent('figure')
                if figcaption:
                    cap = figcaption.find('figcaption')
                    if cap:
                        parent_text = cap.get_text(strip=True)[:200]
                
                if not parent_text:
                    parent = img.find_parent(['p', 'div', 'section', 'article'])
                    if parent:
                        parent_text = parent.get_text(strip=True)[:200]
                
                images_without_alt.append({
                    "url": src,
                    "selector": f"img[src='{img.get('src', '')}']",
                    "context": parent_text,
                    "original_alt": alt if alt else None
                })
        
        if not images_without_alt:
            return {
                "success": True,
                "message": "No images without alt text found",
                "images_found": 0,
                "generated": 0
            }
        
        generator = AIAltTextGenerator()
        generated_count = 0
        
        async with db_pool.acquire() as conn:
            for img_data in images_without_alt[:20]:
                try:
                    if img_data["url"].startswith('data:'):
                        continue
                    
                    ai_result = await generator.generate_alt_text(
                        image_url=img_data["url"],
                        context=img_data.get("context"),
                        language="de"
                    )
                    
                    await conn.execute("""
                        INSERT INTO accessibility_alt_text_fixes
                        (site_id, user_id, image_url, image_selector, original_alt,
                         generated_alt, confidence, source, status)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')
                        ON CONFLICT (site_id, image_url) DO UPDATE SET
                            generated_alt = EXCLUDED.generated_alt,
                            confidence = EXCLUDED.confidence,
                            updated_at = NOW()
                    """,
                        site_uuid,
                        user_id,
                        img_data["url"],
                        img_data.get("selector"),
                        img_data.get("original_alt"),
                        ai_result["alt_text"],
                        ai_result.get("confidence", 0.9),
                        ai_result.get("source", "openai_vision")
                    )
                    generated_count += 1
                    
                except Exception as e:
                    logger.warning(f"Could not generate alt for {img_data['url']}: {e}")
                    continue
        
        return {
            "success": True,
            "images_found": len(images_without_alt),
            "generated": generated_count,
            "message": f"Generated {generated_count} alt texts for images without alt attribute"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
