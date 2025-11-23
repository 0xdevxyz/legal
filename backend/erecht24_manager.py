"""
Complyo - Unified eRecht24 Manager
Single Source of Truth für alle eRecht24-Integrationen

Features:
- Konsolidierte API-Zugriffe (Project API + Rechtstexte-API)
- Priorisierte Fallback-Kette (Live-API → Redis → DB → AI)
- Health-Monitoring
- Automatisches Projekt-Setup
- Webhook-Handler

© 2025 Complyo.tech
"""

import os
import asyncpg
import httpx
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
from redis import asyncio as aioredis

from ai_fix_engine.white_label import WhiteLabelProcessor

logger = logging.getLogger(__name__)


class TextType(Enum):
    """Unterstützte Text-Typen"""
    IMPRESSUM = "impressum"
    DATENSCHUTZ = "datenschutz"
    PRIVACY_POLICY = "privacy_policy"
    AGB = "agb"
    WIDERRUF = "widerruf"
    DISCLAIMER = "disclaimer"
    PRIVACY_POLICY_SOCIAL_MEDIA = "privacy_policy_social_media"


class ERecht24Manager:
    """
    Unified eRecht24 Manager - Single Source of Truth
    
    Konsolidiert alle eRecht24-Services in eine konsistente Schnittstelle
    mit robuster Fallback-Hierarchie und Health-Monitoring.
    """
    
    def __init__(self, db_pool: asyncpg.Pool, redis_client: Optional[aioredis.Redis] = None):
        """
        Args:
            db_pool: PostgreSQL connection pool
            redis_client: Optional Redis client für schnelles Caching
        """
        self.db_pool = db_pool
        self.redis_client = redis_client
        
        # API Configuration
        self.api_url = os.getenv("ERECHT24_API_URL", "https://api.e-recht24.de")
        self.api_key = os.getenv("ERECHT24_API_KEY", "")
        self.plugin_key = os.getenv("ERECHT24_PLUGIN_KEY", "complyo-ai-compliance")
        self.timeout = 30.0
        
        # Cache Configuration
        self.redis_ttl_days = int(os.getenv("ERECHT24_REDIS_CACHE_DAYS", "7"))
        self.db_cache_days = int(os.getenv("ERECHT24_DB_CACHE_DAYS", "30"))
        
        # White-Label Processing
        self.white_label_processor = WhiteLabelProcessor()
        
        # Health Status
        self._api_healthy = True
        self._last_api_check = None
        
        if not self.api_key:
            logger.warning("⚠️ ERECHT24_API_KEY nicht gesetzt - Fallback-Modus aktiv")
        else:
            logger.info("✅ eRecht24 Manager initialisiert (API verfügbar)")
    
    # ========================================================================
    # MAIN API: Legal Text Retrieval with Fallback Chain
    # ========================================================================
    
    async def get_legal_text(
        self,
        user_id: int,
        domain: str,
        text_type: str,
        language: str = "de",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Haupt-Methode: Holt rechtssicheren Text mit Fallback-Hierarchie
        
        Fallback-Kette:
        1. Live eRecht24 API (wenn verfügbar)
        2. Redis Cache (< 7 Tage alt)
        3. DB Cache (< 30 Tage alt)
        4. AI-Generator (letzter Fallback)
        
        Args:
            user_id: Complyo User-ID
            domain: Domain (z.B. "example.com")
            text_type: "impressum", "datenschutz", "agb", etc.
            language: "de", "en", "fr"
            force_refresh: Bypass Cache und hole frische Daten
        
        Returns:
            Dict mit: {
                "content": HTML-String,
                "source": "api" | "redis" | "db" | "ai",
                "last_updated": ISO timestamp,
                "cached": bool
            }
        """
        logger.info(f"📄 Request: {text_type} für {domain} (user: {user_id})")
        
        # Normalisiere text_type
        text_type = self._normalize_text_type(text_type)
        
        # Force Refresh → Skip Cache
        if not force_refresh:
            # 1. TRY: Redis Cache (schnellster)
            cached = await self._get_from_redis(domain, text_type, language)
            if cached:
                logger.info(f"✅ Redis Cache Hit für {text_type}")
                return {
                    "content": cached["content"],
                    "source": "redis",
                    "last_updated": cached.get("timestamp"),
                    "cached": True
                }
            
            # 2. TRY: DB Cache
            cached = await self._get_from_db_cache(user_id, domain, text_type, language)
            if cached:
                logger.info(f"✅ DB Cache Hit für {text_type}")
                # Schreibe in Redis für zukünftige Requests
                await self._save_to_redis(domain, text_type, language, cached["content"])
                return {
                    "content": cached["content"],
                    "source": "db",
                    "last_updated": cached.get("timestamp"),
                    "cached": True
                }
        
        # 3. TRY: Live eRecht24 API
        if self.api_key and self._api_healthy:
            try:
                project = await self._get_or_create_project(user_id, domain)
                if project:
                    content = await self._fetch_from_api(
                        project.get("erecht24_project_id"),
                        text_type,
                        language
                    )
                    
                    if content:
                        logger.info(f"✅ eRecht24 API Success für {text_type}")
                        
                        # Cache in Redis + DB
                        await self._save_to_redis(domain, text_type, language, content)
                        await self._save_to_db(
                            project["id"],
                            text_type,
                            language,
                            content
                        )
                        
                        return {
                            "content": content,
                            "source": "api",
                            "last_updated": datetime.utcnow().isoformat(),
                            "cached": False
                        }
            except Exception as e:
                logger.warning(f"⚠️ eRecht24 API Error: {e}")
                self._api_healthy = False  # Mark as unhealthy
        
        # 4. FALLBACK: AI Generator
        logger.warning(f"⚠️ Fallback zu AI-Generator für {text_type}")
        content = await self._generate_with_ai(domain, text_type, language)
        
        if content:
            # Cache AI-generated content
            await self._save_to_redis(domain, text_type, language, content)
            
            return {
                "content": content,
                "source": "ai",
                "last_updated": datetime.utcnow().isoformat(),
                "cached": False,
                "warning": "Generiert mit KI - sollte durch Rechtsanwalt geprüft werden"
            }
        
        # Complete Failure
        logger.error(f"❌ Konnte {text_type} nicht generieren für {domain}")
        return {
            "content": None,
            "source": "none",
            "error": "Alle Quellen fehlgeschlagen"
        }
    
    # ========================================================================
    # PROJECT MANAGEMENT
    # ========================================================================
    
    async def _get_or_create_project(
        self,
        user_id: int,
        domain: str
    ) -> Optional[Dict[str, Any]]:
        """Holt existierendes Projekt oder erstellt neues"""
        
        # Check DB
        async with self.db_pool.acquire() as conn:
            project = await conn.fetchrow(
                """
                SELECT id, erecht24_project_id, status, api_key, secret
                FROM erecht24_projects
                WHERE user_id = $1 AND domain = $2
                ORDER BY created_at DESC
                LIMIT 1
                """,
                user_id, domain
            )
            
            if project and project["status"] == "active":
                return dict(project)
        
        # Create new project
        return await self._create_project(user_id, domain)
    
    async def _create_project(
        self,
        user_id: int,
        domain: str,
        company_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Erstellt neues eRecht24-Projekt"""
        
        if not self.api_key:
            # Demo-Modus: Erstelle nur DB-Eintrag
            logger.info(f"🔧 Demo-Modus: Erstelle lokales Projekt für {domain}")
            async with self.db_pool.acquire() as conn:
                project_id = await conn.fetchval(
                    """
                    INSERT INTO erecht24_projects 
                    (user_id, domain, status, erecht24_project_id)
                    VALUES ($1, $2, 'demo', $3)
                    RETURNING id
                    """,
                    user_id, domain, f"demo_{domain}_{user_id}"
                )
                
                return {
                    "id": project_id,
                    "erecht24_project_id": f"demo_{domain}_{user_id}",
                    "status": "demo"
                }
        
        # API-Modus: Erstelle bei eRecht24
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/projects",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "domain": domain,
                        "name": f"Complyo - {domain}",
                        "external_id": f"complyo_user_{user_id}",
                        "company_info": company_info or {}
                    }
                )
                
                if response.status_code == 201:
                    data = response.json()
                    erecht_project_id = data.get("project_id")
                    
                    # Speichere in DB
                    async with self.db_pool.acquire() as conn:
                        project_id = await conn.fetchval(
                            """
                            INSERT INTO erecht24_projects 
                            (user_id, domain, erecht24_project_id, status, api_key, secret)
                            VALUES ($1, $2, $3, 'active', $4, $5)
                            RETURNING id
                            """,
                            user_id, domain, erecht_project_id,
                            data.get("api_key"), data.get("secret")
                        )
                        
                        logger.info(f"✅ eRecht24 Projekt erstellt: {erecht_project_id}")
                        
                        return {
                            "id": project_id,
                            "erecht24_project_id": erecht_project_id,
                            "status": "active",
                            "api_key": data.get("api_key"),
                            "secret": data.get("secret")
                        }
                else:
                    logger.error(f"❌ API Error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Projekt-Erstellung fehlgeschlagen: {e}")
            return None
    
    # ========================================================================
    # API CALLS
    # ========================================================================
    
    async def _fetch_from_api(
        self,
        project_id: str,
        text_type: str,
        language: str
    ) -> Optional[str]:
        """Holt Text direkt von eRecht24 API"""
        
        if not self.api_key or not project_id:
            return None
        
        # Map text_type to API endpoint
        endpoint_map = {
            "impressum": "imprint",
            "datenschutz": "privacy-policy",
            "privacy_policy": "privacy-policy",
            "agb": "terms",
            "widerruf": "revocation"
        }
        
        endpoint = endpoint_map.get(text_type, text_type)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Try Project API first
                response = await client.get(
                    f"{self.api_url}/v1/projects/{project_id}/texts/{endpoint}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "application/json"
                    },
                    params={"language": language}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("html") or data.get("content")
                    
                    # White-Label Processing
                    if content:
                        content = self.white_label_processor.process(content)
                    
                    return content
                
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Text {text_type} nicht gefunden in Projekt {project_id}")
                    return None
                
                else:
                    logger.error(f"❌ API Error {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ API Request fehlgeschlagen: {e}")
            return None
    
    # ========================================================================
    # CACHING: Redis
    # ========================================================================
    
    async def _get_from_redis(
        self,
        domain: str,
        text_type: str,
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Holt cached Text aus Redis"""
        
        if not self.redis_client:
            return None
        
        try:
            key = f"erecht24:{domain}:{text_type}:{language}"
            data = await self.redis_client.get(key)
            
            if data:
                cached = json.loads(data)
                
                # Check age
                timestamp = datetime.fromisoformat(cached.get("timestamp", "2000-01-01"))
                age_days = (datetime.utcnow() - timestamp).days
                
                if age_days < self.redis_ttl_days:
                    return cached
                else:
                    logger.info(f"🔄 Redis Cache expired ({age_days} days)")
                    await self.redis_client.delete(key)
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Redis Read Error: {e}")
            return None
    
    async def _save_to_redis(
        self,
        domain: str,
        text_type: str,
        language: str,
        content: str
    ) -> None:
        """Speichert Text in Redis Cache"""
        
        if not self.redis_client:
            return
        
        try:
            key = f"erecht24:{domain}:{text_type}:{language}"
            data = {
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # TTL in Sekunden
            ttl_seconds = self.redis_ttl_days * 24 * 60 * 60
            
            await self.redis_client.setex(
                key,
                ttl_seconds,
                json.dumps(data)
            )
            
            logger.info(f"✅ Redis Cache gespeichert: {key}")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis Write Error: {e}")
    
    # ========================================================================
    # CACHING: Database
    # ========================================================================
    
    async def _get_from_db_cache(
        self,
        user_id: int,
        domain: str,
        text_type: str,
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Holt cached Text aus DB"""
        
        try:
            async with self.db_pool.acquire() as conn:
                # Hole Projekt
                project = await conn.fetchrow(
                    """
                    SELECT id FROM erecht24_projects
                    WHERE user_id = $1 AND domain = $2
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    user_id, domain
                )
                
                if not project:
                    return None
                
                # Hole gecachten Text
                cached = await conn.fetchrow(
                    """
                    SELECT html_content, last_synced, version
                    FROM erecht24_cached_texts
                    WHERE project_id = $1 
                    AND text_type = $2 
                    AND language = $3
                    ORDER BY last_synced DESC
                    LIMIT 1
                    """,
                    project["id"], text_type, language
                )
                
                if not cached:
                    return None
                
                # Check age
                last_synced = cached["last_synced"]
                if not last_synced:
                    return None
                
                age_days = (datetime.utcnow() - last_synced).days
                
                if age_days < self.db_cache_days:
                    logger.info(f"✅ DB Cache Hit ({age_days} days old)")
                    return {
                        "content": cached["html_content"],
                        "timestamp": last_synced.isoformat(),
                        "version": cached["version"]
                    }
                else:
                    logger.info(f"🔄 DB Cache expired ({age_days} days)")
                    return None
                    
        except Exception as e:
            logger.warning(f"⚠️ DB Cache Read Error: {e}")
            return None
    
    async def _save_to_db(
        self,
        project_id: int,
        text_type: str,
        language: str,
        content: str,
        version: Optional[str] = None
    ) -> None:
        """Speichert Text in DB Cache"""
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO erecht24_cached_texts 
                    (project_id, text_type, language, html_content, last_synced, version)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (project_id, text_type, language) 
                    DO UPDATE SET 
                        html_content = EXCLUDED.html_content,
                        last_synced = EXCLUDED.last_synced,
                        version = EXCLUDED.version
                    """,
                    project_id, text_type, language, content, 
                    datetime.utcnow(), version or "1.0"
                )
                
                logger.info(f"✅ DB Cache gespeichert: {text_type}")
                
        except Exception as e:
            logger.warning(f"⚠️ DB Cache Write Error: {e}")
    
    # ========================================================================
    # AI FALLBACK
    # ========================================================================
    
    async def _generate_with_ai(
        self,
        domain: str,
        text_type: str,
        language: str
    ) -> Optional[str]:
        """Generiert Text mit AI als Fallback"""
        
        try:
            # Import AI Generator
            from .ai_fix_engine.legal_text_generator import LegalTextGenerator
            
            generator = LegalTextGenerator()
            
            # Generate based on type
            if text_type in ["impressum", "imprint"]:
                content = await generator.generate_impressum(domain)
            elif text_type in ["datenschutz", "privacy_policy"]:
                content = await generator.generate_privacy_policy(domain)
            elif text_type == "agb":
                content = await generator.generate_terms(domain)
            else:
                logger.warning(f"⚠️ AI-Generator für {text_type} nicht verfügbar")
                return None
            
            logger.info(f"✅ AI-generiert: {text_type}")
            return content
            
        except Exception as e:
            logger.error(f"❌ AI Generation fehlgeschlagen: {e}")
            return None
    
    # ========================================================================
    # HEALTH CHECK
    # ========================================================================
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Health-Check für Dashboard"""
        
        # Check API
        api_status = "healthy" if self._api_healthy and self.api_key else "unavailable"
        
        # Check Redis
        redis_status = "healthy" if self.redis_client else "unavailable"
        
        # Check DB
        try:
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "healthy"
        except:
            db_status = "unhealthy"
        
        return {
            "api": {
                "status": api_status,
                "last_check": self._last_api_check.isoformat() if self._last_api_check else None
            },
            "redis": {
                "status": redis_status,
                "ttl_days": self.redis_ttl_days
            },
            "database": {
                "status": db_status,
                "cache_days": self.db_cache_days
            },
            "overall": "healthy" if all([
                api_status != "unhealthy",
                db_status == "healthy"
            ]) else "degraded"
        }
    
    # ========================================================================
    # WEBHOOK HANDLER
    # ========================================================================
    
    async def handle_webhook(
        self,
        project_id: str,
        text_type: str,
        content: str,
        version: Optional[str] = None
    ) -> bool:
        """
        Webhook-Handler für eRecht24 Push-Notifications
        Wird aufgerufen wenn eRecht24 eine Aktualisierung pushed
        """
        
        try:
            # Finde Projekt in DB
            async with self.db_pool.acquire() as conn:
                project = await conn.fetchrow(
                    """
                    SELECT id, domain FROM erecht24_projects
                    WHERE erecht24_project_id = $1
                    """,
                    project_id
                )
                
                if not project:
                    logger.warning(f"⚠️ Webhook für unbekanntes Projekt: {project_id}")
                    return False
                
                # Update Cache
                await self._save_to_db(
                    project["id"],
                    text_type,
                    "de",  # Default language
                    content,
                    version
                )
                
                # Update Redis
                await self._save_to_redis(
                    project["domain"],
                    text_type,
                    "de",
                    content
                )
                
                logger.info(f"✅ Webhook verarbeitet: {text_type} für {project['domain']}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Webhook-Verarbeitung fehlgeschlagen: {e}")
            return False
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def _normalize_text_type(self, text_type: str) -> str:
        """Normalisiert Text-Type Namen"""
        
        mapping = {
            "imprint": "impressum",
            "privacy": "datenschutz",
            "privacy_policy": "datenschutz",
            "terms": "agb",
            "tos": "agb",
            "revocation": "widerruf"
        }
        
        return mapping.get(text_type.lower(), text_type.lower())

