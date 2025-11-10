#!/usr/bin/env python3
"""
Cronjob Script zum Fetchen von RSS-Feed News
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

async def main():
    """Fetcht alle RSS-Feeds und speichert neue News"""
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
        
        # Close database connection
        await db_pool.close()
        
        print(f"🎉 RSS feed fetch finished at {datetime.now().isoformat()}")
        
    except Exception as e:
        print(f"❌ Error in cronjob: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

