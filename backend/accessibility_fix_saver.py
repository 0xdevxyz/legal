"""
Complyo Accessibility Fix Saver
================================
Speichert AI-generierte Barrierefreiheits-Fixes in die Datenbank
"""

import asyncpg
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

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
        fixes: List[Dict[str, Any]]
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
                            'approved'  # Auto-approve für jetzt
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

