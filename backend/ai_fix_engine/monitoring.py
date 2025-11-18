"""
Complyo AI Fix Engine - Monitoring & Logging

Trackt AI-Calls, Kosten, Success-Rates und User-Feedback

© 2025 Complyo.tech
"""

import asyncpg
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum


logger = logging.getLogger(__name__)


class EventType(Enum):
    """Monitoring Event-Typen"""
    AI_CALL = "ai_call"
    FIX_GENERATED = "fix_generated"
    FIX_APPLIED = "fix_applied"
    USER_FEEDBACK = "user_feedback"
    ERROR = "error"


@dataclass
class AICallMetrics:
    """Metriken für einen AI-Call"""
    model: str
    tokens_used: int
    cost_usd: float
    response_time_ms: int
    success: bool
    error: Optional[str]


@dataclass
class FixMetrics:
    """Metriken für einen generierten Fix"""
    fix_id: str
    fix_type: str
    issue_category: str
    validation_passed: bool
    generation_time_ms: int
    fallback_used: bool
    user_skill_level: str


class FixEngineMonitor:
    """
    Hauptklasse für Monitoring der AI Fix Engine
    """
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        """
        Args:
            db_pool: Optional PostgreSQL connection pool
        """
        self.db_pool = db_pool
        self._ensure_tables_created = False
    
    async def _ensure_tables(self) -> None:
        """
        Stellt sicher, dass Monitoring-Tabellen existieren
        """
        if self._ensure_tables_created or not self.db_pool:
            return
        
        async with self.db_pool.acquire() as conn:
            # Monitoring Events Table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_fix_monitoring (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    user_id INTEGER,
                    fix_id VARCHAR(255),
                    data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # AI Call Logs Table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_call_logs (
                    id SERIAL PRIMARY KEY,
                    model VARCHAR(100) NOT NULL,
                    tokens_used INTEGER,
                    cost_usd DECIMAL(10, 6),
                    response_time_ms INTEGER,
                    success BOOLEAN DEFAULT false,
                    error_message TEXT,
                    prompt_length INTEGER,
                    response_length INTEGER,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Fix Generation Stats Table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fix_generation_stats (
                    id SERIAL PRIMARY KEY,
                    fix_id VARCHAR(255) NOT NULL,
                    fix_type VARCHAR(50) NOT NULL,
                    issue_category VARCHAR(100),
                    user_id INTEGER,
                    validation_passed BOOLEAN,
                    generation_time_ms INTEGER,
                    fallback_used BOOLEAN DEFAULT false,
                    user_skill_level VARCHAR(50),
                    ai_model_used VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User Feedback Table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fix_user_feedback (
                    id SERIAL PRIMARY KEY,
                    fix_id VARCHAR(255) NOT NULL,
                    user_id INTEGER NOT NULL,
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    feedback_text TEXT,
                    was_helpful BOOLEAN,
                    was_applied BOOLEAN,
                    tags TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ai_call_logs_created 
                ON ai_call_logs(created_at DESC)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fix_stats_fix_type 
                ON fix_generation_stats(fix_type)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_rating 
                ON fix_user_feedback(rating)
            """)
        
        self._ensure_tables_created = True
        logger.info("✅ Monitoring tables ensured")
    
    async def log_ai_call(
        self,
        metrics: AICallMetrics,
        user_id: Optional[int] = None,
        prompt_length: Optional[int] = None,
        response_length: Optional[int] = None
    ) -> None:
        """
        Loggt einen AI-API-Call
        """
        if not self.db_pool:
            logger.debug(f"AI Call: {metrics.model}, tokens: {metrics.tokens_used}, cost: ${metrics.cost_usd:.4f}")
            return
        
        await self._ensure_tables()
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ai_call_logs 
                (model, tokens_used, cost_usd, response_time_ms, success, 
                 error_message, prompt_length, response_length, user_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                metrics.model,
                metrics.tokens_used,
                metrics.cost_usd,
                metrics.response_time_ms,
                metrics.success,
                metrics.error,
                prompt_length,
                response_length,
                user_id
            )
        
        logger.info(f"📊 AI Call logged: {metrics.model}, ${metrics.cost_usd:.4f}, {metrics.response_time_ms}ms")
    
    async def log_fix_generation(
        self,
        metrics: FixMetrics,
        user_id: Optional[int] = None,
        ai_model_used: Optional[str] = None
    ) -> None:
        """
        Loggt eine Fix-Generierung
        """
        if not self.db_pool:
            logger.debug(f"Fix Generated: {metrics.fix_type}, validation: {metrics.validation_passed}")
            return
        
        await self._ensure_tables()
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO fix_generation_stats
                (fix_id, fix_type, issue_category, user_id, validation_passed,
                 generation_time_ms, fallback_used, user_skill_level, ai_model_used)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                metrics.fix_id,
                metrics.fix_type,
                metrics.issue_category,
                user_id,
                metrics.validation_passed,
                metrics.generation_time_ms,
                metrics.fallback_used,
                metrics.user_skill_level,
                ai_model_used
            )
        
        logger.info(f"📊 Fix generation logged: {metrics.fix_type}, {metrics.generation_time_ms}ms")
    
    async def log_user_feedback(
        self,
        fix_id: str,
        user_id: int,
        rating: int,
        feedback_text: Optional[str] = None,
        was_helpful: Optional[bool] = None,
        was_applied: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """
        Loggt User-Feedback für einen Fix
        """
        if not self.db_pool:
            logger.debug(f"User Feedback: fix_id={fix_id}, rating={rating}")
            return
        
        await self._ensure_tables()
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO fix_user_feedback
                (fix_id, user_id, rating, feedback_text, was_helpful, was_applied, tags)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                fix_id,
                user_id,
                rating,
                feedback_text,
                was_helpful,
                was_applied,
                tags
            )
        
        logger.info(f"📊 User feedback logged: fix_id={fix_id}, rating={rating}/5")
    
    async def log_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        user_id: Optional[int] = None,
        fix_id: Optional[str] = None
    ) -> None:
        """
        Loggt ein generisches Monitoring-Event
        """
        if not self.db_pool:
            logger.debug(f"Event: {event_type.value}, data: {json.dumps(data)[:100]}")
            return
        
        await self._ensure_tables()
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ai_fix_monitoring
                (event_type, user_id, fix_id, data)
                VALUES ($1, $2, $3, $4)
                """,
                event_type.value,
                user_id,
                fix_id,
                json.dumps(data)
            )
    
    async def get_ai_call_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Holt AI-Call-Statistiken
        """
        if not self.db_pool:
            return {}
        
        await self._ensure_tables()
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        async with self.db_pool.acquire() as conn:
            # Total calls and costs
            totals = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_calls,
                    COUNT(CASE WHEN success THEN 1 END) as successful_calls,
                    SUM(tokens_used) as total_tokens,
                    SUM(cost_usd) as total_cost,
                    AVG(response_time_ms) as avg_response_time
                FROM ai_call_logs
                WHERE created_at BETWEEN $1 AND $2
                """,
                start_date, end_date
            )
            
            # By model
            by_model = await conn.fetch(
                """
                SELECT 
                    model,
                    COUNT(*) as calls,
                    SUM(tokens_used) as tokens,
                    SUM(cost_usd) as cost,
                    AVG(response_time_ms) as avg_time
                FROM ai_call_logs
                WHERE created_at BETWEEN $1 AND $2
                GROUP BY model
                ORDER BY calls DESC
                """,
                start_date, end_date
            )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "totals": dict(totals) if totals else {},
            "by_model": [dict(row) for row in by_model]
        }
    
    async def get_fix_generation_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Holt Fix-Generierungs-Statistiken
        """
        if not self.db_pool:
            return {}
        
        await self._ensure_tables()
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        async with self.db_pool.acquire() as conn:
            # Overall stats
            overall = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_fixes,
                    COUNT(CASE WHEN validation_passed THEN 1 END) as validated_fixes,
                    COUNT(CASE WHEN fallback_used THEN 1 END) as fallback_used,
                    AVG(generation_time_ms) as avg_generation_time,
                    (COUNT(CASE WHEN validation_passed THEN 1 END)::float / 
                     NULLIF(COUNT(*), 0) * 100) as success_rate
                FROM fix_generation_stats
                WHERE created_at BETWEEN $1 AND $2
                """,
                start_date, end_date
            )
            
            # By fix type
            by_type = await conn.fetch(
                """
                SELECT 
                    fix_type,
                    COUNT(*) as count,
                    AVG(generation_time_ms) as avg_time,
                    (COUNT(CASE WHEN validation_passed THEN 1 END)::float / 
                     NULLIF(COUNT(*), 0) * 100) as success_rate
                FROM fix_generation_stats
                WHERE created_at BETWEEN $1 AND $2
                GROUP BY fix_type
                ORDER BY count DESC
                """,
                start_date, end_date
            )
            
            # By category
            by_category = await conn.fetch(
                """
                SELECT 
                    issue_category,
                    COUNT(*) as count,
                    AVG(generation_time_ms) as avg_time
                FROM fix_generation_stats
                WHERE created_at BETWEEN $1 AND $2
                  AND issue_category IS NOT NULL
                GROUP BY issue_category
                ORDER BY count DESC
                LIMIT 10
                """,
                start_date, end_date
            )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "overall": dict(overall) if overall else {},
            "by_type": [dict(row) for row in by_type],
            "by_category": [dict(row) for row in by_category]
        }
    
    async def get_user_feedback_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Holt User-Feedback-Statistiken
        """
        if not self.db_pool:
            return {}
        
        await self._ensure_tables()
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        async with self.db_pool.acquire() as conn:
            # Overall feedback
            overall = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_feedback,
                    AVG(rating) as avg_rating,
                    COUNT(CASE WHEN was_helpful THEN 1 END) as helpful_count,
                    COUNT(CASE WHEN was_applied THEN 1 END) as applied_count
                FROM fix_user_feedback
                WHERE created_at BETWEEN $1 AND $2
                """,
                start_date, end_date
            )
            
            # Rating distribution
            rating_dist = await conn.fetch(
                """
                SELECT 
                    rating,
                    COUNT(*) as count
                FROM fix_user_feedback
                WHERE created_at BETWEEN $1 AND $2
                GROUP BY rating
                ORDER BY rating DESC
                """,
                start_date, end_date
            )
            
            # Common tags
            common_tags = await conn.fetch(
                """
                SELECT 
                    tag,
                    COUNT(*) as count
                FROM fix_user_feedback,
                     UNNEST(tags) as tag
                WHERE created_at BETWEEN $1 AND $2
                GROUP BY tag
                ORDER BY count DESC
                LIMIT 10
                """,
                start_date, end_date
            )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "overall": dict(overall) if overall else {},
            "rating_distribution": [dict(row) for row in rating_dist],
            "common_tags": [dict(row) for row in common_tags]
        }
    
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Holt Metriken für Monitoring-Dashboard
        """
        # Last 24 hours
        last_24h = datetime.now() - timedelta(hours=24)
        # Last 7 days
        last_7d = datetime.now() - timedelta(days=7)
        
        ai_stats_24h = await self.get_ai_call_stats(start_date=last_24h)
        ai_stats_7d = await self.get_ai_call_stats(start_date=last_7d)
        
        fix_stats_24h = await self.get_fix_generation_stats(start_date=last_24h)
        fix_stats_7d = await self.get_fix_generation_stats(start_date=last_7d)
        
        feedback_stats_7d = await self.get_user_feedback_stats(start_date=last_7d)
        
        return {
            "last_24_hours": {
                "ai_calls": ai_stats_24h.get("totals", {}),
                "fixes_generated": fix_stats_24h.get("overall", {})
            },
            "last_7_days": {
                "ai_calls": ai_stats_7d.get("totals", {}),
                "fixes_generated": fix_stats_7d.get("overall", {}),
                "user_feedback": feedback_stats_7d.get("overall", {})
            },
            "top_fix_types": fix_stats_7d.get("by_type", [])[:5],
            "top_categories": fix_stats_7d.get("by_category", [])[:5]
        }


# Globale Monitor-Instanz (singleton)
_monitor_instance: Optional[FixEngineMonitor] = None


def get_monitor(db_pool: Optional[asyncpg.Pool] = None) -> FixEngineMonitor:
    """
    Holt oder erstellt Monitor-Instanz (Singleton)
    """
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = FixEngineMonitor(db_pool)
    elif db_pool and not _monitor_instance.db_pool:
        _monitor_instance.db_pool = db_pool
    
    return _monitor_instance


