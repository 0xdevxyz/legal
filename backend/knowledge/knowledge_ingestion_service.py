import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import feedparser

from knowledge import RawContentItem

logger = logging.getLogger(__name__)

WEB_SOURCES = [
    {
        "name": "BfDI Pressemitteilungen",
        "url": "https://www.bfdi.bund.de/SharedDocs/RSS/DE/Pressemitteilungen.xml",
        "source_type": "bfdi",
    },
    {
        "name": "DSK Beschlüsse",
        "url": "https://www.datenschutzkonferenz-online.de/rss.xml",
        "source_type": "bfdi",
    },
    {
        "name": "LTO Legal Tribune Online",
        "url": "https://www.lto.de/rss/feed/",
        "source_type": "legal_news",
    },
    {
        "name": "Heise Datenschutz",
        "url": "https://www.heise.de/thema/Datenschutz.rss",
        "source_type": "web",
    },
    {
        "name": "EUR-Lex Neuigkeiten",
        "url": "https://eur-lex.europa.eu/oj/direct-access.html?ojId=OJ_L&page=1&format=rss",
        "source_type": "eulex",
    },
    {
        "name": "it-recht-kanzlei",
        "url": "https://www.it-recht-kanzlei.de/rss/news.xml",
        "source_type": "web",
    },
]

COMPLIANCE_KEYWORDS = [
    "datenschutz", "dsgvo", "gdpr", "cookie", "einwilligung", "consent",
    "barrierefreiheit", "wcag", "bfsg", "accessibility", "impressum",
    "nis2", "cybersicherheit", "ki-verordnung", "ai act", "ttdsg",
    "uwg", "wettbewerb", "agb", "widerrufsrecht", "pangv", "eugh",
    "bgh", "olg", "datenschutzbehörde", "abmahnung", "bußgeld",
    "transparenz", "verarbeitung", "personenbezogene daten",
]


class KnowledgeIngestionService:
    def __init__(self, db_pool=None):
        self.db_pool = db_pool
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": "ComplyoKnowledgeBot/1.0 (+https://complyo.tech)"},
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _compute_hash(self, url: str, date: str) -> str:
        return hashlib.sha256(f"{url}|{date}".encode()).hexdigest()

    def _is_relevant(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in COMPLIANCE_KEYWORDS)

    def _parse_feed_entry(self, entry: Any, source_type: str) -> Optional[RawContentItem]:
        title = getattr(entry, "title", "") or ""
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
        link = getattr(entry, "link", "") or ""
        published = getattr(entry, "published_parsed", None)

        if not title or not link:
            return None

        combined = f"{title} {summary}"
        if not self._is_relevant(combined):
            return None

        pub_date = datetime(*published[:6]) if published else datetime.now()
        content_hash = self._compute_hash(link, pub_date.strftime("%Y-%m-%d"))

        content = re.sub(r"<[^>]+>", "", summary).strip()

        return RawContentItem(
            title=title.strip(),
            content=content[:2000],
            source_url=link,
            source_type=source_type,
            published_at=pub_date,
            content_hash=content_hash,
        )

    async def fetch_from_web_sources(self) -> List[RawContentItem]:
        items: List[RawContentItem] = []
        session = await self._get_session()

        for source in WEB_SOURCES:
            try:
                async with session.get(source["url"]) as resp:
                    if resp.status != 200:
                        logger.warning(f"Feed {source['name']} returned {resp.status}")
                        continue
                    text = await resp.text()

                feed = feedparser.parse(text)
                count = 0
                for entry in feed.entries:
                    item = self._parse_feed_entry(entry, source["source_type"])
                    if item:
                        items.append(item)
                        count += 1

                logger.info(f"Fetched {count} relevant items from {source['name']}")

            except Exception as e:
                logger.error(f"Error fetching {source['name']}: {e}")

        return items

    async def fetch_from_eulex(self) -> List[RawContentItem]:
        if not self.db_pool:
            return await self.fetch_from_web_sources()
        try:
            from eulex_service import EULexService
            service = EULexService(self.db_pool)
            result = await service.fetch_recent_changes(days_back=7)
            await service.close()
            logger.info(f"eulex_service returned {result.get('new_items', 0)} new items")
        except Exception as e:
            logger.warning(f"eulex_service unavailable, falling back to RSS: {e}")
        return []

    async def fetch_from_legal_news_db(self) -> List[RawContentItem]:
        if not self.db_pool:
            return []
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT title, content, source_url, source_type, published_at
                    FROM legal_news
                    WHERE published_at >= NOW() - INTERVAL '3 days'
                      AND processed_for_knowledge IS NOT TRUE
                    ORDER BY published_at DESC
                    LIMIT 50
                    """
                )
            items = []
            for row in rows:
                combined = f"{row['title']} {row.get('content', '')}"
                if not self._is_relevant(combined):
                    continue
                h = self._compute_hash(row["source_url"] or "", str(row["published_at"])[:10])
                items.append(
                    RawContentItem(
                        title=row["title"],
                        content=(row.get("content") or "")[:2000],
                        source_url=row.get("source_url", ""),
                        source_type=row.get("source_type", "web"),
                        published_at=row["published_at"],
                        content_hash=h,
                    )
                )
            return items
        except Exception as e:
            logger.error(f"Error fetching from legal_news DB: {e}")
            return []

    def deduplicate(self, items: List[RawContentItem]) -> List[RawContentItem]:
        seen: set = set()
        unique: List[RawContentItem] = []
        for item in items:
            if item.content_hash not in seen:
                seen.add(item.content_hash)
                unique.append(item)
        return unique

    async def ingest_all(self) -> List[RawContentItem]:
        results = await asyncio.gather(
            self.fetch_from_web_sources(),
            self.fetch_from_legal_news_db(),
            return_exceptions=True,
        )

        all_items: List[RawContentItem] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Ingestion source error: {result}")
            else:
                all_items.extend(result)

        unique = self.deduplicate(all_items)
        logger.info(f"Ingestion complete: {len(all_items)} total → {len(unique)} unique")
        return unique
