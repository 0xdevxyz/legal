"""
Complyo Background Worker
Processes fix-jobs asynchronously in the background
"""

import asyncio
import asyncpg
import os
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from ai_fix_engine.smart_fix_generator import SmartFixGenerator
from erecht24_service import erecht24_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundWorker:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.is_running = False
        self.smart_fix_generator = SmartFixGenerator()
        self.smart_fix_generator.set_erecht24_service(erecht24_service)
        
    async def start(self):
        """Start the background worker"""
        self.is_running = True
        logger.info("🚀 Background Worker started")
        
        while self.is_running:
            try:
                await self.process_pending_jobs()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"❌ Worker error: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def stop(self):
        """Stop the background worker"""
        self.is_running = False
        logger.info("🛑 Background Worker stopped")
    
    async def process_pending_jobs(self):
        """Process all pending fix jobs"""
        async with self.db_pool.acquire() as conn:
            # Get all pending jobs
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
        """Process a single fix job"""
        job_id = job['job_id']
        issue_data = job['issue_data']
        scan_id = job.get('scan_id')  # ✅ FIX: scan_id aus job-Dict holen
        
        logger.info(f"⚙️ Processing job {job_id}")
        
        # Mark as processing
        await conn.execute("""
            UPDATE fix_jobs
            SET status = 'processing',
                started_at = NOW(),
                progress_percent = 20,
                current_step = 'KI analysiert Problem...'
            WHERE job_id = $1
        """, job_id)
        
        # Simulate progress steps
        steps = [
            (40, 'Lösung wird generiert...'),
            (60, 'Code wird optimiert...'),
            (80, 'Integration wird vorbereitet...')
        ]
        
        for progress, step_text in steps:
            await asyncio.sleep(2)  # Simulate work
            await conn.execute("""
                UPDATE fix_jobs
                SET progress_percent = $1,
                    current_step = $2
                WHERE job_id = $3
            """, progress, step_text, job_id)
        
        # Get scan_id as site_id for widget
        site_id = scan_id if scan_id else None
        
        # Generate the actual fix
        try:
            fix_result = await self.generate_fix(issue_data, site_id=site_id)
            
            # Mark as completed
            await conn.execute("""
                UPDATE fix_jobs
                SET status = 'completed',
                    completed_at = NOW(),
                    progress_percent = 100,
                    current_step = 'Abgeschlossen!',
                    result = $1
                WHERE job_id = $2
            """, fix_result, job_id)
            
            logger.info(f"✅ Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Fix generation failed for job {job_id}: {e}")
            raise
    
    async def generate_fix(self, issue_data: Any, site_id: str = None) -> str:
        """Generate a fix for the issue"""
        # Parse issue_data if it's a string
        if isinstance(issue_data, str):
            import json
            issue_data = json.loads(issue_data)
        
        # Extract relevant info
        category = issue_data.get('category', 'unknown')
        title = issue_data.get('title', 'Unknown Issue')
        
        # Use site_id or generate a placeholder
        if not site_id:
            site_id = "YOUR_SITE_ID"
        
        # Generate fix based on category
        if 'impressum' in category.lower() or 'impressum' in title.lower():
            return self._generate_impressum_fix()
        elif 'datenschutz' in category.lower() or 'datenschutz' in title.lower():
            return self._generate_datenschutz_fix()
        elif 'cookie' in category.lower() or 'cookie' in title.lower():
            return self._generate_cookie_fix(site_id)
        elif 'barriere' in category.lower() or 'accessibility' in title.lower():
            return self._generate_accessibility_fix(site_id)
        else:
            return self._generate_generic_fix(issue_data)
    
    def _generate_impressum_fix(self) -> str:
        """Generate fix for Impressum issues"""
        import json
        return json.dumps({
            "type": "text",
            "title": "Impressum erstellen",
            "description": "Erstellen Sie ein rechtssicheres Impressum mit allen erforderlichen Angaben.",
            "content": """<h1>Impressum</h1>
<p><strong>Angaben gemäß § 5 TMG:</strong></p>
<p>[Ihr Firmenname]<br>
[Ihre Adresse]<br>
[PLZ Ort]</p>

<p><strong>Vertreten durch:</strong><br>
[Ihr Name]</p>

<p><strong>Kontakt:</strong><br>
Telefon: [Ihre Telefonnummer]<br>
E-Mail: [Ihre E-Mail]</p>

<p><strong>Umsatzsteuer-ID:</strong><br>
Umsatzsteuer-Identifikationsnummer gemäß §27 a Umsatzsteuergesetz:<br>
[Ihre USt-IdNr.]</p>""",
            "integration_instructions": "Kopieren Sie diesen Text und fügen Sie ihn auf einer neuen Seite unter /impressum ein. Ersetzen Sie die Platzhalter mit Ihren echten Daten.",
            "target_url": "/impressum"
        })
    
    def _generate_datenschutz_fix(self) -> str:
        """Generate fix for Datenschutz issues"""
        import json
        return json.dumps({
            "type": "text",
            "title": "Datenschutzerklärung erstellen",
            "description": "DSGVO-konforme Datenschutzerklärung mit allen erforderlichen Informationen.",
            "content": """<h1>Datenschutzerklärung</h1>
<p><strong>1. Datenschutz auf einen Blick</strong></p>
<p>Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen.</p>

<p><strong>2. Verantwortlicher</strong></p>
<p>Verantwortlicher für die Datenverarbeitung auf dieser Website ist:<br>
[Ihr Firmenname]<br>
[Ihre Adresse]<br>
E-Mail: [Ihre E-Mail]</p>

<p><strong>3. Datenerfassung auf dieser Website</strong></p>
<p>Die Datenverarbeitung auf dieser Website erfolgt durch den Websitebetreiber.</p>""",
            "integration_instructions": "Kopieren Sie diesen Text auf eine neue Seite unter /datenschutz oder /privacy. Passen Sie die Platzhalter an Ihre Daten an.",
            "target_url": "/datenschutz"
        })
    
    def _generate_cookie_fix(self, site_id: str) -> str:
        """Generate fix for Cookie issues"""
        import json
        return json.dumps({
            "type": "widget",
            "title": "Cookie-Banner integrieren",
            "description": "DSGVO-konformes Cookie-Consent-Widget von Complyo.",
            "content": f'<script src="https://widget.complyo.tech/cookie-consent.js" data-site-id="{site_id}"></script>',
            "integration_instructions": f"Fügen Sie dieses Skript im <head>-Bereich Ihrer Website ein. Ihre Site-ID: {site_id}",
            "widget_script_url": "https://widget.complyo.tech/cookie-consent.js",
            "site_id": site_id
        })
    
    def _generate_accessibility_fix(self, site_id: str) -> str:
        """Generate fix for Accessibility issues"""
        import json
        return json.dumps({
            "type": "widget",
            "title": "Barrierefreiheits-Widget integrieren",
            "description": "Complyo Accessibility Widget für WCAG 2.1 Level AA Konformität.",
            "content": f'<script src="https://widget.complyo.tech/accessibility.js" data-site-id="{site_id}" data-auto-fix="true" data-show-toolbar="true"></script>',
            "integration_instructions": f"Fügen Sie dieses Skript am Ende des <body>-Tags Ihrer Website ein. Das Widget verbessert automatisch die Barrierefreiheit. Ihre Site-ID: {site_id}",
            "widget_script_url": "https://widget.complyo.tech/accessibility.js",
            "site_id": site_id,
            "auto_fixable_issues": [
                "Alt-Texte für Bilder (AI-generiert)",
                "ARIA-Labels für Buttons",
                "Kontrast-Verbesserungen",
                "Focus-Indikatoren",
                "Keyboard-Navigation",
                "Skip-Links"
            ]
        })
    
    def _generate_generic_fix(self, issue_data: Dict[str, Any]) -> str:
        """Generate generic fix guide"""
        import json
        return json.dumps({
            "type": "guide",
            "title": f"Anleitung: {issue_data.get('title', 'Problem beheben')}",
            "description": issue_data.get('description', 'Befolgen Sie diese Schritte zur Behebung.'),
            "content": issue_data.get('recommendation', 'Bitte prüfen Sie die Anforderungen und beheben Sie das Problem manuell.'),
            "integration_instructions": "Folgen Sie der Empfehlung und prüfen Sie die Umsetzung.",
            "guide_steps": [
                "Analysieren Sie das Problem",
                "Implementieren Sie die empfohlene Lösung",
                "Testen Sie die Änderungen",
                "Führen Sie einen erneuten Scan durch"
            ]
        })
    
    async def fail_job(self, conn: asyncpg.Connection, job_id: str, error_message: str):
        """Mark a job as failed"""
        await conn.execute("""
            UPDATE fix_jobs
            SET status = 'failed',
                completed_at = NOW(),
                error_message = $1,
                current_step = 'Fehler aufgetreten'
            WHERE job_id = $2
        """, error_message, job_id)
        logger.error(f"❌ Job {job_id} marked as failed: {error_message}")


# Global worker instance
_worker_instance: Optional[BackgroundWorker] = None
_worker_task: Optional[asyncio.Task] = None

async def start_background_worker(db_pool: asyncpg.Pool):
    """Start the global background worker"""
    global _worker_instance, _worker_task
    
    if _worker_instance is None:
        _worker_instance = BackgroundWorker(db_pool)
        _worker_task = asyncio.create_task(_worker_instance.start())
        logger.info("✅ Background worker started successfully")
    else:
        logger.warning("⚠️ Background worker already running")

async def stop_background_worker():
    """Stop the global background worker"""
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

