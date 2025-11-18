"""
Complyo - eRecht24 Full Integration

Vollständige Integration mit:
- Auto-Setup für neue Domains
- Intelligentes Caching
- Fallback auf AI-generierte Texte
- Webhook-Support
- White-Label Processing

© 2025 Complyo.tech
"""

import os
import asyncpg
import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum

from .ai_fix_engine.white_label import WhiteLabelProcessor


logger = logging.getLogger(__name__)


class TextType(Enum):
    """eRecht24 Text-Typen"""
    IMPRESSUM = "impressum"
    DATENSCHUTZ = "datenschutz"
    AGB = "agb"
    WIDERRUF = "widerruf"
    DISCLAIMER = "disclaimer"


class ERecht24Integration:
    """
    Hauptklasse für eRecht24-Integration
    
    Features:
    - Automatisches Projekt-Setup
    - Caching mit konfigurierbarem Expiry
    - Fallback auf AI-Generierung
    - White-Label Processing
    - Sync-History
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Args:
            db_pool: PostgreSQL connection pool
        """
        self.db_pool = db_pool
        self.api_url = os.getenv("ERECHT24_API_URL", "https://api.e-recht24.de")
        self.api_key = os.getenv("ERECHT24_API_KEY", "")
        self.timeout = 30.0
        self.white_label_processor = WhiteLabelProcessor()
        
        # Cache settings
        self.cache_duration_days = int(os.getenv("ERECHT24_CACHE_DAYS", "7"))
        
        if not self.api_key:
            logger.warning("⚠️ ERECHT24_API_KEY nicht gesetzt - läuft im Fallback-Modus")
    
    async def auto_create_project(
        self,
        user_id: int,
        domain: str,
        company_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Automatisches Projekt-Setup für neue Domain
        
        Args:
            user_id: Complyo User-ID
            domain: Domain (z.B. "example.com")
            company_info: Optional company data for project setup
        
        Returns:
            Project data or None on failure
        """
        logger.info(f"🔧 Auto-setup eRecht24 project for user {user_id}, domain: {domain}")
        
        # Check if project already exists
        async with self.db_pool.acquire() as conn:
            existing = await conn.fetchrow(
                """
                SELECT id, erecht24_project_id, status 
                FROM erecht24_projects 
                WHERE user_id = $1 AND domain = $2
                """,
                user_id, domain
            )
            
            if existing:
                logger.info(f"✅ Project already exists: {existing['id']}")
                return {
                    "id": existing["id"],
                    "erecht24_project_id": existing["erecht24_project_id"],
                    "status": existing["status"],
                    "existing": True
                }
        
        # Create new project
        if not self.api_key:
            logger.warning("⚠️ No API key - creating placeholder project")
            return await self._create_placeholder_project(user_id, domain)
        
        try:
            # Call eRecht24 API to create project
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/projects",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "domain": domain,
                        "name": f"Complyo Project - {domain}",
                        "external_id": f"complyo_user_{user_id}",
                        "company_info": company_info or {}
                    }
                )
                
                if response.status_code == 201:
                    data = response.json()
                    
                    # Store in database
                    async with self.db_pool.acquire() as conn:
                        project = await conn.fetchrow(
                            """
                            INSERT INTO erecht24_projects 
                            (user_id, domain, erecht24_project_id, erecht24_api_key, erecht24_secret, status)
                            VALUES ($1, $2, $3, $4, $5, 'active')
                            RETURNING id, erecht24_project_id, status
                            """,
                            user_id,
                            domain,
                            data.get("project_id"),
                            data.get("api_key"),
                            data.get("secret")
                        )
                    
                    logger.info(f"✅ eRecht24 project created: {project['id']}")
                    return dict(project)
                
                else:
                    logger.error(f"❌ eRecht24 API error: {response.status_code} - {response.text}")
                    # Fallback to placeholder
                    return await self._create_placeholder_project(user_id, domain)
        
        except Exception as e:
            logger.error(f"❌ Error creating eRecht24 project: {e}")
            return await self._create_placeholder_project(user_id, domain)
    
    async def _create_placeholder_project(
        self,
        user_id: int,
        domain: str
    ) -> Optional[Dict[str, Any]]:
        """
        Creates placeholder project (when no eRecht24 API key)
        """
        async with self.db_pool.acquire() as conn:
            try:
                project = await conn.fetchrow(
                    """
                    INSERT INTO erecht24_projects 
                    (user_id, domain, erecht24_project_id, status)
                    VALUES ($1, $2, $3, 'fallback')
                    RETURNING id, status
                    ON CONFLICT (user_id, domain) DO UPDATE
                    SET status = 'fallback'
                    RETURNING id, status
                    """,
                    user_id,
                    domain,
                    f"fallback_{user_id}_{domain}"
                )
                
                logger.info(f"✅ Placeholder project created: {project['id']}")
                return dict(project)
            
            except Exception as e:
                logger.error(f"❌ Error creating placeholder project: {e}")
                return None
    
    async def get_legal_text_with_fallback(
        self,
        user_id: int,
        domain: str,
        text_type: str,
        language: str = "de",
        force_refresh: bool = False
    ) -> Optional[str]:
        """
        Holt rechtssicheren Text mit intelligentem Fallback
        
        Priorität:
        1. Cache (wenn nicht expired und force_refresh=False)
        2. eRecht24 API
        3. AI-Generierung (Fallback)
        
        Args:
            user_id: User-ID
            domain: Domain
            text_type: impressum, datenschutz, agb, widerruf
            language: de, en, fr
            force_refresh: Cache ignorieren
        
        Returns:
            HTML-Text oder None
        """
        logger.info(f"📄 Fetching {text_type} for {domain} (user: {user_id})")
        
        # Step 1: Check cache (unless force_refresh)
        if not force_refresh:
            cached = await self._get_from_cache(user_id, domain, text_type, language)
            if cached:
                logger.info(f"✅ Found in cache (age: {cached['age_hours']}h)")
                return cached["content"]
        
        # Step 2: Get project
        project = await self._get_or_create_project(user_id, domain)
        if not project:
            logger.error(f"❌ No project for {domain}")
            return None
        
        # Step 3: Fetch from eRecht24 API
        if project.get("erecht24_project_id") and not project.get("erecht24_project_id").startswith("fallback_"):
            api_text = await self._fetch_from_erecht24_api(
                project["erecht24_project_id"],
                text_type,
                language
            )
            
            if api_text:
                # Process with white-label
                processed = await self.white_label_processor.process(api_text)
                
                # Cache it
                await self._save_to_cache(
                    project["id"],
                    text_type,
                    language,
                    processed
                )
                
                # Log sync
                await self._log_sync(
                    project["id"],
                    "api_fetch",
                    "success",
                    texts_updated=1
                )
                
                logger.info(f"✅ Fetched from eRecht24 API and cached")
                return processed
        
        # Step 4: Fallback to AI-generated (will be handled by caller)
        logger.warning(f"⚠️ No eRecht24 data available - fallback required")
        
        # Log failed sync
        await self._log_sync(
            project["id"],
            "fallback_required",
            "failed",
            error_message="No eRecht24 data available"
        )
        
        return None
    
    async def _get_from_cache(
        self,
        user_id: int,
        domain: str,
        text_type: str,
        language: str
    ) -> Optional[Dict[str, Any]]:
        """
        Holt Text aus Cache wenn nicht expired
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT 
                    c.html_content,
                    c.last_updated,
                    c.cache_expires_at,
                    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - c.last_updated)) / 3600 as age_hours
                FROM erecht24_texts_cache c
                JOIN erecht24_projects p ON c.project_id = p.id
                WHERE p.user_id = $1
                  AND p.domain = $2
                  AND p.status IN ('active', 'fallback')
                  AND c.text_type = $3
                  AND c.language = $4
                  AND (c.cache_expires_at IS NULL OR c.cache_expires_at > CURRENT_TIMESTAMP)
                """,
                user_id, domain, text_type, language
            )
            
            if result:
                return {
                    "content": result["html_content"],
                    "age_hours": round(result["age_hours"], 1),
                    "expires_at": result["cache_expires_at"]
                }
            
            return None
    
    async def _get_or_create_project(
        self,
        user_id: int,
        domain: str
    ) -> Optional[Dict[str, Any]]:
        """
        Holt Projekt oder erstellt es automatisch
        """
        async with self.db_pool.acquire() as conn:
            project = await conn.fetchrow(
                """
                SELECT id, erecht24_project_id, status
                FROM erecht24_projects
                WHERE user_id = $1 AND domain = $2
                """,
                user_id, domain
            )
            
            if project:
                return dict(project)
        
        # Auto-create
        return await self.auto_create_project(user_id, domain)
    
    async def _fetch_from_erecht24_api(
        self,
        project_id: str,
        text_type: str,
        language: str
    ) -> Optional[str]:
        """
        Holt Text von eRecht24 API
        """
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/v1/projects/{project_id}/texts/{text_type}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "application/json"
                    },
                    params={"language": language}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("html", data.get("content"))
                
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Text {text_type} nicht in eRecht24 gefunden")
                    return None
                
                else:
                    logger.error(f"❌ eRecht24 API error: {response.status_code}")
                    return None
        
        except Exception as e:
            logger.error(f"❌ Error fetching from eRecht24: {e}")
            return None
    
    async def _save_to_cache(
        self,
        project_id: int,
        text_type: str,
        language: str,
        html_content: str,
        version: Optional[str] = None
    ) -> None:
        """
        Speichert Text im Cache
        """
        cache_expires = datetime.now() + timedelta(days=self.cache_duration_days)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO erecht24_texts_cache 
                (project_id, text_type, language, html_content, version, cache_expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (project_id, text_type, language)
                DO UPDATE SET
                    html_content = EXCLUDED.html_content,
                    version = EXCLUDED.version,
                    last_updated = CURRENT_TIMESTAMP,
                    cache_expires_at = EXCLUDED.cache_expires_at,
                    fetch_count = erecht24_texts_cache.fetch_count + 1
                """,
                project_id, text_type, language, html_content, version, cache_expires
            )
        
        logger.info(f"💾 Cached {text_type} (expires: {cache_expires.strftime('%Y-%m-%d')})")
    
    async def sync_all_texts(
        self,
        project_id: int,
        triggered_by: str = "manual"
    ) -> Dict[str, Any]:
        """
        Synchronisiert alle Texte für ein Projekt
        
        Args:
            project_id: Database project ID
            triggered_by: manual, webhook, scheduled, auto
        
        Returns:
            Sync result with statistics
        """
        logger.info(f"🔄 Starting full sync for project {project_id}")
        start_time = datetime.now()
        
        # Get project
        async with self.db_pool.acquire() as conn:
            project = await conn.fetchrow(
                "SELECT * FROM erecht24_projects WHERE id = $1",
                project_id
            )
        
        if not project or project["status"] != "active":
            logger.error(f"❌ Project {project_id} not active")
            return {"status": "failed", "error": "Project not active"}
        
        # Fetch all text types
        text_types = ["impressum", "datenschutz", "agb", "widerruf"]
        texts_updated = 0
        errors = []
        
        for text_type in text_types:
            try:
                text = await self._fetch_from_erecht24_api(
                    project["erecht24_project_id"],
                    text_type,
                    "de"
                )
                
                if text:
                    # Process with white-label
                    processed = await self.white_label_processor.process(text)
                    
                    # Save to cache
                    await self._save_to_cache(
                        project_id,
                        text_type,
                        "de",
                        processed
                    )
                    
                    texts_updated += 1
                    logger.info(f"✅ Synced {text_type}")
                else:
                    logger.warning(f"⚠️ No content for {text_type}")
            
            except Exception as e:
                logger.error(f"❌ Error syncing {text_type}: {e}")
                errors.append(f"{text_type}: {str(e)}")
        
        # Calculate duration
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Log sync
        status = "success" if texts_updated > 0 and not errors else "failed"
        if texts_updated > 0 and errors:
            status = "partial"
        
        await self._log_sync(
            project_id,
            "full_sync",
            status,
            texts_updated=texts_updated,
            error_message="; ".join(errors) if errors else None,
            duration_ms=duration_ms,
            triggered_by=triggered_by
        )
        
        # Update last_sync_at
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE erecht24_projects SET last_sync_at = CURRENT_TIMESTAMP WHERE id = $1",
                project_id
            )
        
        result = {
            "status": status,
            "texts_updated": texts_updated,
            "errors": errors,
            "duration_ms": duration_ms
        }
        
        logger.info(f"🏁 Sync complete: {result}")
        return result
    
    async def _log_sync(
        self,
        project_id: int,
        sync_type: str,
        status: str,
        texts_updated: int = 0,
        error_message: Optional[str] = None,
        api_response_code: Optional[int] = None,
        duration_ms: Optional[int] = None,
        triggered_by: str = "system"
    ) -> None:
        """
        Loggt Sync-Operation
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO erecht24_sync_history
                (project_id, sync_type, status, texts_updated, error_message, 
                 api_response_code, duration_ms, triggered_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                project_id, sync_type, status, texts_updated, error_message,
                api_response_code, duration_ms, triggered_by
            )
    
    async def handle_webhook(
        self,
        project_id: str,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Behandelt Webhook von eRecht24
        
        Args:
            project_id: eRecht24 project ID
            webhook_data: Webhook payload
        
        Returns:
            Processing result
        """
        logger.info(f"🔔 Webhook received for project {project_id}")
        
        # Find project in database
        async with self.db_pool.acquire() as conn:
            project = await conn.fetchrow(
                """
                SELECT id FROM erecht24_projects
                WHERE erecht24_project_id = $1 AND status = 'active'
                """,
                project_id
            )
        
        if not project:
            logger.error(f"❌ Project {project_id} not found")
            return {"status": "error", "message": "Project not found"}
        
        # Trigger sync
        result = await self.sync_all_texts(
            project["id"],
            triggered_by="webhook"
        )
        
        # Update webhook trigger count
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE erecht24_webhooks
                SET last_triggered_at = CURRENT_TIMESTAMP,
                    trigger_count = trigger_count + 1
                WHERE project_id = $1
                """,
                project["id"]
            )
        
        return result
    
    async def get_project_status(
        self,
        user_id: int,
        domain: str
    ) -> Optional[Dict[str, Any]]:
        """
        Holt Status eines Projekts mit Cache-Info
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT * FROM v_erecht24_projects_status
                WHERE user_id = $1 AND domain = $2
                """,
                user_id, domain
            )
            
            if result:
                return dict(result)
            
            return None
    
    async def clean_expired_cache(self) -> int:
        """
        Löscht abgelaufene Cache-Einträge
        
        Returns:
            Anzahl gelöschter Einträge
        """
        async with self.db_pool.acquire() as conn:
            deleted_count = await conn.fetchval(
                "SELECT clean_erecht24_expired_cache()"
            )
        
        logger.info(f"🧹 Cleaned {deleted_count} expired cache entries")
        return deleted_count


