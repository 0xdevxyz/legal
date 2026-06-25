"""
Complyo Background Worker
Processes fix-jobs asynchronously using the UnifiedFixEngine with real AI
"""

import asyncio
import asyncpg
import json
from typing import Optional, Dict, Any
import logging

from ai_fix_engine.unified_fix_engine import UnifiedFixEngine
from ai_fix_engine.prompts_v2 import ContextBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackgroundWorker:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.is_running = False
        self.engine = UnifiedFixEngine()
        self.context_builder = ContextBuilder()

    async def start(self):
        self.is_running = True
        logger.info("🚀 Background Worker started")
        while self.is_running:
            try:
                await self.process_pending_jobs()
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ Worker error: {e}")
                await asyncio.sleep(10)

    async def stop(self):
        self.is_running = False
        logger.info("🛑 Background Worker stopped")

    async def process_pending_jobs(self):
        async with self.db_pool.acquire() as conn:
            pending_jobs = await conn.fetch("""
                SELECT job_id, user_id, scan_id, issue_id, issue_data, created_at
                FROM fix_jobs
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 5
            """)
            for job in pending_jobs:
                try:
                    await self.process_job(conn, job)
                except Exception as e:
                    logger.error(f"❌ Error processing job {job['job_id']}: {e}")
                    await self.fail_job(conn, job['job_id'], str(e))

    async def process_job(self, conn: asyncpg.Connection, job: Dict[str, Any]):
        job_id = job['job_id']
        scan_id = job.get('scan_id')

        logger.info(f"⚙️ Processing job {job_id}")

        await conn.execute("""
            UPDATE fix_jobs
            SET status = 'processing', started_at = NOW(),
                progress_percent = 10, current_step = 'Kontext wird geladen...'
            WHERE job_id = $1
        """, job_id)

        issue_data = job['issue_data']
        if isinstance(issue_data, str):
            issue_data = json.loads(issue_data)

        # Load scan context from DB
        context = await self._load_context(conn, scan_id, issue_data)

        await conn.execute("""
            UPDATE fix_jobs SET progress_percent = 30,
                current_step = 'KI analysiert das Problem...'
            WHERE job_id = $1
        """, job_id)

        await asyncio.sleep(1)

        await conn.execute("""
            UPDATE fix_jobs SET progress_percent = 55,
                current_step = 'Individuelle Lösung wird generiert...'
            WHERE job_id = $1
        """, job_id)

        fix_result = await self.engine.generate_fix(
            issue=issue_data,
            context=context,
            user_skill=context.get("user_skill", "intermediate")
        )

        await conn.execute("""
            UPDATE fix_jobs SET progress_percent = 85,
                current_step = 'Anleitung wird aufbereitet...'
            WHERE job_id = $1
        """, job_id)

        await asyncio.sleep(0.5)

        result_dict = self.engine.to_dict(fix_result)

        await conn.execute("""
            UPDATE fix_jobs
            SET status = 'completed', completed_at = NOW(),
                progress_percent = 100, current_step = 'Abgeschlossen!',
                result = $1
            WHERE job_id = $2
        """, json.dumps(result_dict, default=str), job_id)

        logger.info(f"✅ Job {job_id} completed — model: {fix_result.ai_model_used}, "
                    f"time: {fix_result.generation_time_ms}ms, "
                    f"fallback: {fix_result.fallback_used}")

    async def _load_context(
        self, conn: asyncpg.Connection, scan_id: Optional[str], issue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Load full scan context from DB to pass into the AI prompt."""
        if not scan_id:
            return self._minimal_context(issue_data)

        row = await conn.fetchrow(
            "SELECT scan_data, url FROM scan_history WHERE scan_id = $1",
            scan_id
        )
        if not row:
            return self._minimal_context(issue_data)

        scan_data = row["scan_data"]
        if isinstance(scan_data, str):
            scan_data = json.loads(scan_data)

        # Build rich context from scan_data
        context = ContextBuilder.build_full_context(scan_data)

        # Enrich with URL if missing
        if not context.get("url") and row.get("url"):
            context["url"] = row["url"]

        # Inject detected issues list for the AI to understand the full picture
        issues = scan_data.get("issues", [])
        context["all_issues"] = [
            {"title": i.get("title"), "category": i.get("category"), "severity": i.get("severity")}
            for i in issues
        ]

        # Tracking / cookie data
        context["tracking_services"] = scan_data.get("tracking_services", [])
        context["detected_cookies"] = scan_data.get("detected_cookies", [])

        # Tech stack fields used in prompts
        tech = scan_data.get("tech_stack", {})
        context.setdefault("technology", {})
        if tech:
            context["technology"].update({
                "cms": tech.get("cms", []),
                "frameworks": tech.get("frameworks", []),
                "analytics": tech.get("analytics", []),
            })

        return context

    def _minimal_context(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "url": issue_data.get("url", ""),
            "site_id": "unknown",
            "company": {},
            "technology": {"cms": [], "frameworks": [], "analytics": []},
            "cookies": [],
            "tracking_services": [],
            "all_issues": [],
            "user_skill": "intermediate",
        }

    async def fail_job(self, conn: asyncpg.Connection, job_id: str, error_message: str):
        await conn.execute("""
            UPDATE fix_jobs
            SET status = 'failed', completed_at = NOW(),
                error_message = $1, current_step = 'Fehler aufgetreten'
            WHERE job_id = $2
        """, error_message, job_id)
        logger.error(f"❌ Job {job_id} failed: {error_message}")


_worker_instance: Optional[BackgroundWorker] = None
_worker_task: Optional[asyncio.Task] = None


async def start_background_worker(db_pool: asyncpg.Pool):
    global _worker_instance, _worker_task
    if _worker_instance is None:
        _worker_instance = BackgroundWorker(db_pool)
        _worker_task = asyncio.create_task(_worker_instance.start())
        logger.info("✅ Background worker started successfully")
    else:
        logger.warning("⚠️ Background worker already running")


async def stop_background_worker():
    global _worker_instance, _worker_task
    if _worker_instance:
        await _worker_instance.stop()
        if _worker_task:
            _worker_task.cancel()
            try:
                await _worker_task
            except asyncio.CancelledError:
                pass
        _worker_instance = None
        _worker_task = None
        logger.info("✅ Background worker stopped successfully")
