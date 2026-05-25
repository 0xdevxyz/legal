#!/usr/bin/env python3
"""
Cronjob Script zum Fetchen von RSS-Feed News
und Ausführen der Legal Intelligence Pipeline.
Läuft täglich um 06:00 Uhr
"""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_service import NewsService


async def run_legal_intelligence_pipeline(db_pool: asyncpg.Pool) -> None:
    """
    Tägliche Legal Intelligence Pipeline:
    1. LegalChangeMonitor erkennt neue Gesetzesänderungen via KI
    2. Neue Einträge werden in legal_updates gespeichert
    3. Betroffene Compliance-Regeln werden versioniert
    4. Betroffene Websites werden als rescan_required markiert
    5. User-Notifications werden erstellt
    """
    from legal_change_monitor import LegalChangeMonitor

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("⚠️  OPENROUTER_API_KEY nicht gesetzt — Legal-Pipeline wird übersprungen")
        return

    print(f"⚖️  Starting legal intelligence pipeline at {datetime.now().isoformat()}")
    monitor = LegalChangeMonitor(openrouter_api_key=api_key, db_pool=db_pool)

    try:
        summary = await monitor.monitor_and_persist()
        print(f"✅ Legal pipeline completed:")
        print(f"   - Changes detected : {summary['detected']}")
        print(f"   - New saved to DB  : {summary['new_saved']}")
        for pr in summary.get("pipeline_results", []):
            print(
                f"   - [{pr.get('legal_update_id')}] {pr.get('title', '')[:60]} "
                f"→ rules={pr.get('rules_updated', 0)}, "
                f"sites={pr.get('websites_flagged', 0)}, "
                f"notifications={pr.get('notifications_queued', 0)}"
            )
    except Exception as e:
        print(f"❌ Legal pipeline error: {e}")


async def main():
    """Fetcht alle RSS-Feeds und führt die Legal Intelligence Pipeline aus"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        sys.exit(1)
    
    try:
        print(f"🕐 Starting RSS feed fetch at {datetime.now().isoformat()}")
        
        # Connect to database
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        
        # Initialize news service
        news_service = NewsService(db_pool)
        
        # Fetch all feeds
        results = await news_service.fetch_all_feeds()
        
        print(f"✅ Feed fetch completed:")
        print(f"   - Total feeds: {results['total_feeds']}")
        print(f"   - Processed: {results['processed']}")
        print(f"   - New items: {results['new_items']}")
        
        if results['errors']:
            print(f"⚠️  Errors encountered:")
            for error in results['errors']:
                print(f"   - {error}")

        # Run legal intelligence pipeline after feeds are loaded
        await run_legal_intelligence_pipeline(db_pool)
        
        # Close database connection
        await db_pool.close()
        
        print(f"🎉 RSS feed fetch finished at {datetime.now().isoformat()}")
        
    except Exception as e:
        print(f"❌ Error in cronjob: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

