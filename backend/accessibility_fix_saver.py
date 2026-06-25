"""
Complyo Accessibility Fix Saver
================================
Speichert AI-generierte Barrierefreiheits-Fixes in die Datenbank
"""

import asyncpg
import hashlib
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AccessibilityFixSaver:
    """
    Speichert AI-generierte Alt-Texte und andere Accessibility-Fixes
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def save_alt_text_fixes(
        self,
        site_id: str,
        scan_id: str,
        user_id: str,  # UUID als String
        fixes: List[Dict[str, Any]],
        status: str = 'pending'  # Human-in-the-loop: NICHT mehr Auto-Approve
    ) -> int:
        """
        Speichert AI-generierte Alt-Texte in die Datenbank
        
        Args:
            site_id: Site-Identifier (z.B. "scan-91778ad450e1")
            scan_id: Scan-ID aus scan_history
            user_id: User UUID
            fixes: Liste von Alt-Text-Fixes
                   Format: [{
                       "page_url": "https://...",
                       "image_src": "/images/logo.png",
                       "image_filename": "logo.png",
                       "suggested_alt": "Firmenlogo...",
                       "confidence": 0.95,
                       "page_title": "Startseite",
                       "surrounding_text": "Text um das Bild",
                       "element_html": "<img src=...>"
                   }]
        
        Returns:
            Anzahl gespeicherter Fixes
        """
        if not fixes:
            logger.warning(f"No alt-text fixes to save for site_id={site_id}")
            return 0
        
        saved_count = 0
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for fix in fixes:
                    try:
                        # Generiere Hash für eindeutiges Image-Matching
                        image_hash = hashlib.sha256(
                            f"{site_id}:{fix['image_src']}".encode()
                        ).hexdigest()
                        
                        # Insert or Update (UPSERT)
                        await conn.execute(
                            """
                            INSERT INTO accessibility_alt_text_fixes (
                                site_id,
                                scan_id,
                                user_id,
                                page_url,
                                image_src,
                                image_filename,
                                image_url_hash,
                                suggested_alt,
                                confidence,
                                page_title,
                                surrounding_text,
                                element_html,
                                status,
                                created_at,
                                updated_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW(), NOW())
                            ON CONFLICT (site_id, image_src) 
                            DO UPDATE SET
                                suggested_alt = EXCLUDED.suggested_alt,
                                confidence = EXCLUDED.confidence,
                                scan_id = EXCLUDED.scan_id,
                                page_title = EXCLUDED.page_title,
                                surrounding_text = EXCLUDED.surrounding_text,
                                element_html = EXCLUDED.element_html,
                                updated_at = NOW()
                            """,
                            site_id,
                            scan_id,
                            user_id,
                            fix.get('page_url', ''),
                            fix['image_src'],
                            fix.get('image_filename', ''),
                            image_hash,
                            fix['suggested_alt'],
                            fix.get('confidence', 0.0),
                            fix.get('page_title', ''),
                            fix.get('surrounding_text', ''),
                            fix.get('element_html', ''),
                            status  # Standard: 'pending' → erst nach Review live
                        )
                        
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error saving alt-text fix for {fix.get('image_src')}: {e}")
                        # Continue mit nächstem Fix
                        continue
        
        logger.info(f"✅ Saved {saved_count}/{len(fixes)} alt-text fixes for site_id={site_id}")
        return saved_count
    
    async def get_fixes_for_site(
        self,
        site_id: str,
        status: Optional[str] = 'approved'
    ) -> List[Dict[str, Any]]:
        """
        Lädt Alt-Text-Fixes für eine Site (für Widget)
        
        Args:
            site_id: Site-Identifier
            status: Filter nach Status (approved, pending, etc.)
        
        Returns:
            Liste von Alt-Text-Fixes
        """
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT 
                    image_src,
                    image_filename,
                    suggested_alt,
                    page_url,
                    confidence,
                    page_title,
                    status,
                    created_at
                FROM accessibility_alt_text_fixes
                WHERE site_id = $1
            """
            
            params = [site_id]
            
            if status:
                query += " AND status = $2"
                params.append(status)
            
            query += " ORDER BY confidence DESC, created_at DESC"
            
            rows = await conn.fetch(query, *params)
            
            fixes = [
                {
                    "image_src": row['image_src'],
                    "image_filename": row['image_filename'],
                    "suggested_alt": row['suggested_alt'],
                    "page_url": row['page_url'],
                    "confidence": float(row['confidence']) if row['confidence'] else 0.0,
                    "page_title": row['page_title'],
                    "status": row['status']
                }
                for row in rows
            ]
            
            logger.info(f"📦 Loaded {len(fixes)} alt-text fixes for site_id={site_id}")
            return fixes
    
    async def set_status(
        self,
        fix_id: int,
        status: str,
        custom_alt: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Setzt den Status eines Fixes (approve/reject/deploy). Optionaler user_id-Check.
        status ∈ ('pending','approved','rejected','deployed').
        Gibt True zurück, wenn eine Zeile aktualisiert wurde.
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, user_id FROM accessibility_alt_text_fixes WHERE id = $1",
                fix_id
            )
            if not row:
                return False
            if user_id is not None and row['user_id'] is not None and str(row['user_id']) != str(user_id):
                raise PermissionError("not authorized for this fix")

            approved_at = "NOW()" if status == 'approved' else "approved_at"
            if custom_alt is not None:
                await conn.execute(
                    f"""
                    UPDATE accessibility_alt_text_fixes
                    SET status = $1, suggested_alt = $2, approved_at = {approved_at}, updated_at = NOW()
                    WHERE id = $3
                    """,
                    status, custom_alt, fix_id
                )
            else:
                await conn.execute(
                    f"""
                    UPDATE accessibility_alt_text_fixes
                    SET status = $1, approved_at = {approved_at}, updated_at = NOW()
                    WHERE id = $2
                    """,
                    status, fix_id
                )
            return True

    async def get_review_queue(
        self,
        site_id: str,
        status: str = 'pending'
    ) -> List[Dict[str, Any]]:
        """Alt-Text-Fixes für die Review-Ansicht (Dashboard)."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, page_url, image_src, image_filename, suggested_alt,
                       confidence, surrounding_text, status, created_at
                FROM accessibility_alt_text_fixes
                WHERE site_id = $1 AND status = $2
                ORDER BY confidence DESC, created_at DESC
                """,
                site_id, status
            )
            return [
                {
                    "id": r['id'],
                    "page_url": r['page_url'],
                    "image_src": r['image_src'],
                    "image_filename": r['image_filename'],
                    "suggested_alt": r['suggested_alt'],
                    "confidence": float(r['confidence']) if r['confidence'] else 0.0,
                    "surrounding_text": r['surrounding_text'],
                    "status": r['status'],
                }
                for r in rows
            ]

    async def get_stats_for_site(
        self,
        site_id: str
    ) -> Dict[str, Any]:
        """
        Statistiken für Dashboard
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_fixes,
                    COUNT(*) FILTER (WHERE status = 'approved') as approved_fixes,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending_fixes,
                    AVG(confidence) as avg_confidence,
                    COUNT(DISTINCT page_url) as pages_with_fixes
                FROM accessibility_alt_text_fixes
                WHERE site_id = $1
                """,
                site_id
            )
            
            if not row:
                return {
                    "total_fixes": 0,
                    "approved_fixes": 0,
                    "pending_fixes": 0,
                    "avg_confidence": 0.0,
                    "pages_with_fixes": 0
                }
            
            return {
                "total_fixes": row['total_fixes'],
                "approved_fixes": row['approved_fixes'],
                "pending_fixes": row['pending_fixes'],
                "avg_confidence": float(row['avg_confidence']) if row['avg_confidence'] else 0.0,
                "pages_with_fixes": row['pages_with_fixes']
            }

