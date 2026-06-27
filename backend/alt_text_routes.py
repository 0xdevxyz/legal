"""
Accessibility Alt-Text API Routes
Endpoints für KI-generierte Alt-Texte für Bilder.

KANONISCHER PFAD: schreibt/liest die Tabelle accessibility_alt_text_fixes über
AccessibilityFixSaver (Schema: image_src / suggested_alt / status / SERIAL id,
site_id als String). Der frühere UUID-Pfad (image_url/generated_alt/is_approved)
ist abgelöst.

Hinweis: Das öffentliche GET /api/accessibility/alt-text-fixes (Widget-Runtime)
wird von widget_routes.py bedient (kanonisch). Hier nur Generierung + Review.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import logging

from accessibility_fix_saver import AccessibilityFixSaver

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
    fix_id: int          # SERIAL id aus accessibility_alt_text_fixes
    approved: bool
    custom_alt: Optional[str] = None


class ApproveLinkRequest(BaseModel):
    fix_id: int          # SERIAL id aus accessibility_link_fixes
    approved: bool
    custom_label: Optional[str] = None


class RescanRequest(BaseModel):
    site_url: str
    criteria: Optional[List[str]] = None   # z.B. ["2.4.4","3.1.1"]; None = nur Ist-Zustand


def _filename_from_url(url: str) -> str:
    try:
        path = urlparse(url).path
        return path.rsplit('/', 1)[-1] if path else ''
    except Exception:
        return ''


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
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.get("/alt-text-review-queue")
async def alt_text_review_queue(
    site_id: str = Query(..., description="Site ID"),
    status: str = Query("pending", description="pending | approved | rejected | deployed"),
    current_user: Dict[str, Any] = Depends(get_required_user)
):
    """Liste der Alt-Text-Fixes zum Review (Dashboard)."""
    try:
        saver = AccessibilityFixSaver(db_pool)
        items = await saver.get_review_queue(site_id, status=status)
        return {"success": True, "items": items, "count": len(items)}
    except Exception as e:
        logger.error(f"Error loading alt-text review queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-alt-texts")
async def generate_alt_texts(
    request: GenerateAltTextsRequest,
    current_user: Dict[str, Any] = Depends(get_required_user)
):
    """
    Generiert KI-Alt-Texte (Claude Vision) für eine Liste von Bildern und legt sie
    als 'pending' im kanonischen Schema ab (Review erforderlich, bevor sie live gehen).
    """
    from compliance_engine.ai_alt_text_generator import AIAltTextGenerator

    try:
        generator = AIAltTextGenerator()
        user_id = current_user.get("user_id") or current_user.get("id")

        fixes: List[Dict[str, Any]] = []
        results: List[Dict[str, Any]] = []
        for img in request.images:
            try:
                ai_result = await generator.generate_alt_text(
                    image_url=img.url,
                    context=img.context,
                    language=request.language
                )
                fixes.append({
                    "page_url": "",
                    "image_src": img.url,
                    "image_filename": _filename_from_url(img.url),
                    "suggested_alt": ai_result["alt_text"],
                    "confidence": ai_result.get("confidence", 0.9),
                    "surrounding_text": img.context or "",
                })
                results.append({
                    "image_url": img.url,
                    "alt_text": ai_result["alt_text"],
                    "confidence": ai_result.get("confidence", 0.9),
                    "source": ai_result.get("source", "claude_vision"),
                })
            except Exception as img_err:
                logger.error(f"Error generating alt for {img.url}: {img_err}")
                results.append({"image_url": img.url, "error": str(img_err)})

        saved = 0
        if fixes:
            saver = AccessibilityFixSaver(db_pool)
            saved = await saver.save_alt_text_fixes(
                site_id=request.site_id, scan_id=None, user_id=user_id,
                fixes=fixes, status='pending'
            )

        return {
            "success": True,
            "generated": len([r for r in results if not r.get("error")]),
            "saved": saved,
            "errors": len([r for r in results if r.get("error")]),
            "results": results,
            "note": "Fixes liegen als 'pending' vor und gehen erst nach Freigabe live.",
        }
    except Exception as e:
        logger.error(f"Alt-text generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/approve-alt-text")
async def approve_alt_text(
    request: ApproveAltTextRequest,
    current_user: Dict[str, Any] = Depends(get_required_user)
):
    """Genehmigt (approved) oder lehnt ab (rejected) einen Alt-Text; optional Text überschreiben."""
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        saver = AccessibilityFixSaver(db_pool)
        new_status = 'approved' if request.approved else 'rejected'
        try:
            ok = await saver.set_status(
                fix_id=request.fix_id, status=new_status,
                custom_alt=request.custom_alt, user_id=user_id
            )
        except PermissionError:
            raise HTTPException(status_code=403, detail="Not authorized")
        if not ok:
            raise HTTPException(status_code=404, detail="Fix not found")
        return {"success": True, "fix_id": request.fix_id, "status": new_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving alt-text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/link-review-queue")
async def link_review_queue(
    site_id: str = Query(..., description="Site ID"),
    status: str = Query("pending", description="pending | approved | rejected | deployed"),
    current_user: Dict[str, Any] = Depends(get_required_user)
):
    """Liste der Link-Zweck-Fixes (WCAG 2.4.4) zum Review (Dashboard)."""
    try:
        saver = AccessibilityFixSaver(db_pool)
        items = await saver.get_link_fixes_for_site(site_id, status=status)
        return {"success": True, "items": items, "count": len(items)}
    except Exception as e:
        logger.error(f"Error loading link review queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve-link")
async def approve_link(
    request: ApproveLinkRequest,
    current_user: Dict[str, Any] = Depends(get_required_user)
):
    """Genehmigt/lehnt einen Link-aria-Vorschlag ab; optional Label überschreiben."""
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        saver = AccessibilityFixSaver(db_pool)
        new_status = 'approved' if request.approved else 'rejected'
        try:
            ok = await saver.set_link_status(
                fix_id=request.fix_id, status=new_status,
                custom_label=request.custom_label, user_id=user_id
            )
        except PermissionError:
            raise HTTPException(status_code=403, detail="Not authorized")
        if not ok:
            raise HTTPException(status_code=404, detail="Fix not found")
        return {"success": True, "fix_id": request.fix_id, "status": new_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving link fix: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/worklist")
async def accessibility_worklist(
    site_id: str = Query(..., description="Site ID"),
    current_user: Dict[str, Any] = Depends(get_required_user)
):
    """
    Vereinheitlichte A11y-Worklist für das Dashboard: Review-Items + Zähler über
    Alt-Texte (HITL), Link-Zweck (HITL) und dokumentweite Fixes (auto, read-only).
    Ein Aufruf bedient die ganze Worklist-Seite.
    """
    try:
        saver = AccessibilityFixSaver(db_pool)

        alt_pending = await saver.get_review_queue(site_id, status='pending')
        alt_approved = await saver.get_fixes_for_site(site_id, status='approved')
        link_pending = await saver.get_link_fixes_for_site(site_id, status='pending')
        link_approved = await saver.get_link_fixes_for_site(site_id, status='approved')
        doc_fixes = await saver.get_document_fixes_for_site(site_id, status='approved')

        return {
            "success": True,
            "site_id": site_id,
            "alt_texts": {
                "pending": alt_pending,
                "approved_count": len(alt_approved),
                "pending_count": len(alt_pending),
            },
            "link_fixes": {
                "pending": link_pending,
                "approved_count": len(link_approved),
                "pending_count": len(link_pending),
            },
            "document_fixes": {
                "items": doc_fixes,          # auto-approved, read-only
                "count": len(doc_fixes),
            },
            "totals": {
                "needs_review": len(alt_pending) + len(link_pending),
                "live": len(alt_approved) + len(link_approved) + len(doc_fixes),
            },
        }
    except Exception as e:
        logger.error(f"Error loading accessibility worklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rescan")
async def rescan_accessibility(
    request: RescanRequest,
    current_user: Dict[str, Any] = Depends(get_required_user)
):
    """
    Echter Re-Scan (axe + Heuristik auf gerendertem DOM) zur WCAG-kriteriengenauen
    Verifikation nach Fix-Anwendung: belegt, welche adressierten Kriterien jetzt
    gelöst sind ('issue weg') und welche noch offen sind — statt grober Heuristik.
    """
    from compliance_engine.live_validator import LiveValidator
    try:
        validator = LiveValidator()
        result = await validator.rescan_accessibility(
            website_url=request.site_url,
            target_criteria=request.criteria,
        )
        return result
    except Exception as e:
        logger.error(f"Accessibility rescan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Re-Scan fehlgeschlagen: {str(e)}")


@router.post("/scan-images")
async def scan_images_for_alt_text(
    site_url: str = Query(..., description="URL to scan for images without alt"),
    site_id: str = Query(..., description="Site ID to associate fixes"),
    current_user: Dict[str, Any] = Depends(get_required_user)
):
    """
    Rendert eine Seite, findet Bilder ohne Alt-Attribut und generiert dafür
    KI-Alt-Texte (Claude Vision) → als 'pending' im kanonischen Schema.
    """
    from compliance_engine.browser_renderer import smart_fetch_html
    from bs4 import BeautifulSoup
    from compliance_engine.ai_alt_text_generator import AIAltTextGenerator
    from urllib.parse import urljoin

    try:
        user_id = current_user.get("user_id") or current_user.get("id")

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
                fig = img.find_parent('figure')
                if fig:
                    cap = fig.find('figcaption')
                    if cap:
                        parent_text = cap.get_text(strip=True)[:200]
                if not parent_text:
                    parent = img.find_parent(['p', 'div', 'section', 'article'])
                    if parent:
                        parent_text = parent.get_text(strip=True)[:200]
                images_without_alt.append({
                    "url": src,
                    "context": parent_text,
                    "original_alt": alt if alt else None
                })

        if not images_without_alt:
            return {"success": True, "message": "No images without alt text found",
                    "images_found": 0, "generated": 0}

        generator = AIAltTextGenerator()
        fixes: List[Dict[str, Any]] = []
        for img_data in images_without_alt[:20]:
            if img_data["url"].startswith('data:'):
                continue
            try:
                ai_result = await generator.generate_alt_text(
                    image_url=img_data["url"], context=img_data.get("context"), language="de"
                )
                fixes.append({
                    "page_url": site_url,
                    "image_src": img_data["url"],
                    "image_filename": _filename_from_url(img_data["url"]),
                    "suggested_alt": ai_result["alt_text"],
                    "confidence": ai_result.get("confidence", 0.9),
                    "surrounding_text": img_data.get("context") or "",
                })
            except Exception as e:
                logger.warning(f"Could not generate alt for {img_data['url']}: {e}")
                continue

        saved = 0
        if fixes:
            saver = AccessibilityFixSaver(db_pool)
            saved = await saver.save_alt_text_fixes(
                site_id=site_id, scan_id=None, user_id=user_id, fixes=fixes, status='pending'
            )

        return {
            "success": True,
            "images_found": len(images_without_alt),
            "generated": saved,
            "message": f"{saved} Alt-Texte generiert (Status: pending, Review erforderlich)",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
