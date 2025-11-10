"""
RSS Feed News Service für Complyo
Parst RSS-Feeds von Rechts- und Datenschutz-Quellen
"""

import feedparser
import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        
    async def fetch_all_feeds(self) -> Dict[str, Any]:
        """Fetcht alle aktiven RSS-Feeds"""
        try:
            async with self.db_pool.acquire() as conn:
                # Hole aktive Feed-Quellen
                feeds = await conn.fetch(
                    """
                    SELECT id, name, url, category, keywords, last_fetch, fetch_frequency_hours
                    FROM rss_feed_sources
                    WHERE is_active = TRUE
                    """
                )
                
                results = {
                    "total_feeds": len(feeds),
                    "processed": 0,
                    "new_items": 0,
                    "errors": []
                }
                
                for feed in feeds:
                    try:
                        # Prüfen ob Update nötig (basierend auf fetch_frequency)
                        if feed['last_fetch']:
                            time_since_fetch = datetime.now() - feed['last_fetch']
                            if time_since_fetch.total_seconds() < feed['fetch_frequency_hours'] * 3600:
                                logger.info(f"⏭️ Skipping {feed['name']} - fetched {time_since_fetch.total_seconds()/3600:.1f}h ago")
                                continue
                        
                        logger.info(f"📡 Fetching feed: {feed['name']}")
                        new_items = await self._fetch_and_parse_feed(
                            feed['id'],
                            feed['name'], 
                            feed['url'],
                            feed['category'],
                            feed['keywords']
                        )
                        
                        results['processed'] += 1
                        results['new_items'] += new_items
                        
                        # Update last_fetch timestamp
                        await conn.execute(
                            "UPDATE rss_feed_sources SET last_fetch = $1 WHERE id = $2",
                            datetime.now(), feed['id']
                        )
                        
                    except Exception as e:
                        error_msg = f"Error fetching {feed['name']}: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                
                return results
                
        except Exception as e:
            logger.error(f"Error in fetch_all_feeds: {e}")
            raise
    
    async def _fetch_and_parse_feed(
        self, 
        feed_id: int,
        source_name: str, 
        feed_url: str, 
        category: str,
        keywords: List[str]
    ) -> int:
        """Parst einen einzelnen RSS-Feed und speichert relevante Items"""
        try:
            # Fetch RSS-Feed mit User-Agent (viele Seiten blockieren feedparser ohne UA)
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; ComplyoBot/1.0; +https://complyo.tech)'
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: requests.get(feed_url, headers=headers, timeout=30)
            )
            
            if response.status_code != 200:
                logger.error(f"❌ HTTP {response.status_code} for {source_name}")
                return 0
            
            # Parse RSS-Feed
            feed = await asyncio.get_event_loop().run_in_executor(
                None, feedparser.parse, response.text
            )
            
            if feed.bozo:
                logger.warning(f"⚠️ Feed parsing warning for {source_name}: {feed.bozo_exception}")
            
            new_items = 0
            
            for entry in feed.entries[:20]:  # Nur die neuesten 20 Items
                try:
                    # Extrahiere Daten
                    title = entry.get('title', 'Kein Titel')
                    link = entry.get('link', '')
                    
                    # Summary/Content extrahieren und HTML entfernen
                    summary = self._extract_text(
                        entry.get('summary', entry.get('description', ''))
                    )
                    content = self._extract_text(
                        entry.get('content', [{}])[0].get('value', '') if 'content' in entry else summary
                    )
                    
                    # Published Date parsen
                    published_date = self._parse_date(entry)
                    
                    # Relevanz prüfen (Keyword-Filter)
                    if not self._is_relevant(title, summary, keywords):
                        continue
                    
                    # News-Typ und Severity bestimmen
                    news_type, severity = self._classify_news(title, summary, keywords)
                    
                    # In Datenbank speichern (nur wenn noch nicht vorhanden)
                    saved = await self._save_news_item(
                        title=title,
                        summary=summary[:1000],  # Limit summary length
                        content=content,
                        url=link,
                        source=source_name,
                        source_feed=category,
                        published_date=published_date,
                        news_type=news_type,
                        severity=severity,
                        keywords=keywords
                    )
                    
                    if saved:
                        new_items += 1
                        
                except Exception as e:
                    logger.error(f"Error processing entry from {source_name}: {e}")
                    continue
            
            logger.info(f"✅ {source_name}: {new_items} neue Items gespeichert")
            return new_items
            
        except Exception as e:
            logger.error(f"Error fetching feed {source_name}: {e}")
            return 0
    
    def _extract_text(self, html_content: str) -> str:
        """Extrahiert Text aus HTML"""
        if not html_content:
            return ""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            # Entferne mehrfache Leerzeichen
            text = re.sub(r'\s+', ' ', text)
            return text[:2000]  # Limit length
        except:
            return html_content[:2000]
    
    def _parse_date(self, entry: Dict) -> datetime:
        """Parst Datum aus Feed-Entry"""
        try:
            if 'published_parsed' in entry and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            elif 'updated_parsed' in entry and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
            else:
                return datetime.now()
        except:
            return datetime.now()
    
    def _is_relevant(self, title: str, summary: str, keywords: List[str]) -> bool:
        """Prüft ob News relevant ist basierend auf Keywords"""
        if not keywords:
            return True
        
        text = f"{title} {summary}".lower()
        
        # Mindestens ein Keyword muss vorkommen
        for keyword in keywords:
            if keyword.lower() in text:
                return True
        
        return False
    
    def _classify_news(self, title: str, summary: str, keywords: List[str]) -> tuple:
        """Klassifiziert News-Typ und Severity"""
        text = f"{title} {summary}".lower()
        
        # Critical indicators
        critical_words = ['bußgeld', 'strafe', 'verstoß', 'abmahnung', 'klage', 'urteil']
        if any(word in text for word in critical_words):
            return ('critical', 'critical')
        
        # Update indicators
        update_words = ['änderung', 'update', 'neu', 'anpassung', 'reform']
        if any(word in text for word in update_words):
            return ('update', 'info')
        
        # Tip indicators
        tip_words = ['tipp', 'empfehlung', 'praxis', 'hinweis', 'beachten']
        if any(word in text for word in tip_words):
            return ('tip', 'info')
        
        return ('info', 'info')
    
    async def _save_news_item(
        self,
        title: str,
        summary: str,
        content: str,
        url: str,
        source: str,
        source_feed: str,
        published_date: datetime,
        news_type: str,
        severity: str,
        keywords: List[str]
    ) -> bool:
        """Speichert News-Item in Datenbank (nur wenn noch nicht vorhanden)"""
        try:
            async with self.db_pool.acquire() as conn:
                # Prüfe ob bereits vorhanden (gleiche URL oder gleicher Titel + Source)
                exists = await conn.fetchval(
                    """
                    SELECT id FROM legal_news 
                    WHERE url = $1 OR (title = $2 AND source = $3)
                    """,
                    url, title, source
                )
                
                if exists:
                    return False
                
                # Speichere neues Item
                await conn.execute(
                    """
                    INSERT INTO legal_news (
                        title, summary, content, url, source, source_feed,
                        published_date, news_type, severity, keywords
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    title, summary, content, url, source, source_feed,
                    published_date, news_type, severity, keywords
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error saving news item: {e}")
            return False
    
    async def get_recent_news(
        self, 
        limit: int = 10,
        offset: int = 0,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Holt die neuesten News aus der Datenbank"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT 
                        id, title, summary, url, source, published_date,
                        news_type, severity, keywords, is_featured
                    FROM legal_news
                    WHERE is_active = TRUE
                """
                
                params = []
                param_count = 1
                
                if severity:
                    query += f" AND severity = ${param_count}"
                    params.append(severity)
                    param_count += 1
                
                query += " ORDER BY is_featured DESC, published_date DESC"
                query += f" LIMIT ${param_count} OFFSET ${param_count + 1}"
                params.extend([limit, offset])
                
                rows = await conn.fetch(query, *params)
                
                return [
                    {
                        "id": str(row['id']),
                        "type": row['news_type'],
                        "severity": row['severity'],
                        "title": row['title'],
                        "summary": row['summary'],
                        "date": row['published_date'].isoformat(),
                        "source": row['source'],
                        "url": row['url'],
                        "is_featured": row['is_featured']
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Error getting recent news: {e}")
            return []
    
    async def get_news_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über die News zurück"""
        try:
            async with self.db_pool.acquire() as conn:
                stats = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE severity = 'critical') as critical,
                        COUNT(*) FILTER (WHERE published_date >= CURRENT_TIMESTAMP - INTERVAL '7 days') as last_week,
                        COUNT(*) FILTER (WHERE published_date >= CURRENT_TIMESTAMP - INTERVAL '24 hours') as last_24h
                    FROM legal_news
                    WHERE is_active = TRUE
                    """
                )
                
                return dict(stats)
                
        except Exception as e:
            logger.error(f"Error getting news stats: {e}")
            return {}

