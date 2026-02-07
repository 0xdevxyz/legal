#!/usr/bin/env python3
"""
Cronjob Script für Legal News Processing
- Fetcht RSS-Feeds
- Verarbeitet neue Gesetzesänderungen
- Versendet Benachrichtigungen

Empfohlene Cron-Schedule:
  - RSS-Fetch: */4 * * * * (alle 4 Stunden für kritische Quellen)
  - Notifications: 0 9 * * * (täglich um 09:00 für Digest)
"""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_service import NewsService
from legal_notification_service import LegalNewsNotificationService

async def fetch_feeds(db_pool: asyncpg.Pool) -> dict:
    """Fetcht alle RSS-Feeds"""
    news_service = NewsService(db_pool)
    return await news_service.fetch_all_feeds()

async def process_notifications(db_pool: asyncpg.Pool) -> dict:
    """Verarbeitet neue Änderungen und sendet Benachrichtigungen"""
    notification_service = LegalNewsNotificationService(db_pool)
    return await notification_service.process_new_legal_changes()

async def send_daily_digest(db_pool: asyncpg.Pool) -> dict:
    """Versendet tägliche Digest-E-Mails"""
    notification_service = LegalNewsNotificationService(db_pool)
    return await notification_service.send_daily_digest()

async def main():
    parser = argparse.ArgumentParser(description='Legal News Cronjob')
    parser.add_argument('--mode', choices=['fetch', 'notify', 'digest', 'all'], 
                       default='all', help='Ausführungsmodus')
    args = parser.parse_args()
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        print(f"[{datetime.now().isoformat()}] Starting legal news cronjob (mode: {args.mode})")
        
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        
        if args.mode in ('fetch', 'all'):
            print("\n--- RSS Feed Fetch ---")
            results = await fetch_feeds(db_pool)
            print(f"  Total feeds: {results['total_feeds']}")
            print(f"  Processed: {results['processed']}")
            print(f"  New items: {results['new_items']}")
            if results['errors']:
                for error in results['errors']:
                    print(f"  ERROR: {error}")
        
        if args.mode in ('notify', 'all'):
            print("\n--- Notification Processing ---")
            results = await process_notifications(db_pool)
            print(f"  Processed: {results['processed']}")
            print(f"  Notifications created: {results['notifications_created']}")
            print(f"  Emails sent: {results['emails_sent']}")
            if results['errors']:
                for error in results['errors']:
                    print(f"  ERROR: {error}")
        
        if args.mode == 'digest':
            print("\n--- Daily Digest ---")
            results = await send_daily_digest(db_pool)
            print(f"  Users processed: {results['users_processed']}")
            print(f"  Emails sent: {results['emails_sent']}")
            if results['errors']:
                for error in results['errors']:
                    print(f"  ERROR: {error}")
        
        await db_pool.close()
        
        print(f"\n[{datetime.now().isoformat()}] Cronjob completed successfully")
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
