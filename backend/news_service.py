"""
RSS Feed News Service für Complyo
Parst RSS-Feeds von Rechts- und Datenschutz-Quellen
"""

import feedparser
import asyncio
import asyncpg
import requests
from datetime import datetime
from typing import List, Dict, Any, NamedTuple, Optional
import re
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HTTP-Antworten, die keine Fehler sind
# ---------------------------------------------------------------------------
#
# Gefunden am 14.09.2026: Die Quelle "EU Parlament Digitales" antwortet mit
# HTTP 202 ("Accepted", angenommen, der Inhalt wird noch erzeugt) und einem
# leeren Rumpf. Der Abruf buchte das als `❌ HTTP 202` und brach ab. Die Quelle
# hat deshalb seit ihrer Anlage keinen einzigen Eintrag geliefert, ohne dass
# je etwas rot geworden waere: im Log stand eine ERROR-Zeile zwischen
# Hunderten, im Ergebnis stand "11 Feeds verarbeitet". Fuer ein Produkt,
# dessen verkauftes Merkmal die Rechtsaenderungs-Ueberwachung ist, heisst eine
# still ausgefallene Quelle: eine Rechtsaenderung wird nicht bemerkt.
#
# 202 ist keine Absage, sondern die Aufforderung, gleich noch einmal zu
# fragen. Wartezeiten zwischen den Wiederholungen, Summe = Obergrenze je
# Quelle. Bewusst kurz: der Abruf laeuft sequenziell ueber alle Feeds.
WARTEPLAN_202 = (4, 8, 12)        # drei Wiederholungen, hoechstens 24 s Warten
UMLEITUNGEN_MAX = 5               # 3xx sind Wegbeschreibungen, keine Fehler


class Abrufergebnis(NamedTuple):
    """Was ein Feed-Abruf ergeben hat.

    Die Trennung von `eintraege` und `neue_items` ist der Kern. Vorher gab
    `_fetch_and_parse_feed` nur eine Zahl zurueck, und zwei voellig
    verschiedene Zustaende sahen identisch aus:

      eintraege=20, neue_items=0  -> Quelle lebt, hat nur nichts Neues
      eintraege=0,  neue_items=0  -> Quelle liefert nichts Lesbares mehr

    Der zweite Fall wurde als "✅ 0 neue Items gespeichert" protokolliert.
    Genau so verschwanden EDPB News und Datenschutz.org: ihre Feed-Adresse
    leitet auf eine HTML-Seite um, Statuscode 200, Inhalt keiner.
    """
    neue_items: int = 0
    eintraege: int = 0
    status: int = 0
    fehler: str = ""

    @property
    def ok(self) -> bool:
        return not self.fehler


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
                    "errors": [],
                    # Quellen, die geantwortet haben, aber nichts Lesbares
                    # lieferten. Frueher nicht unterscheidbar von "nichts Neues".
                    "leere_quellen": [],
                    "failed": 0,
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
                        ergebnis = await self._fetch_and_parse_feed(
                            feed['id'],
                            feed['name'],
                            feed['url'],
                            feed['category'],
                            feed['keywords']
                        )

                        results['new_items'] += ergebnis.neue_items
                        if ergebnis.ok:
                            results['processed'] += 1
                        else:
                            # Ein gescheiterter Abruf ist kein verarbeiteter
                            # Feed. Dass er frueher mitgezaehlt wurde, ist der
                            # Grund, warum "11 Feeds verarbeitet" im Log stand,
                            # waehrend drei Quellen seit Monaten nichts lasen.
                            results['failed'] += 1
                            results['errors'].append(f"{feed['name']}: {ergebnis.fehler}")
                            results['leere_quellen'].append(feed['name'])
                        
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
    
    async def _abrufen(self, feed_url: str, source_name: str) -> tuple:
        """Holt den Feed und behandelt die Antworten, die kein Fehler sind.

        Rueckgabe: (response, fehlertext). Ist `response` None, steht in
        `fehlertext`, warum der Abruf endgueltig gescheitert ist.

          202 Accepted     angenommen, Inhalt folgt -> erneut abrufen
                           (Wartezeiten WARTEPLAN_202, danach Abbruch)
          3xx + Location   Wegbeschreibung -> folgen, hoechstens
                           UMLEITUNGEN_MAX mal (requests folgt normalerweise
                           selbst; das hier greift, wenn es das ausnahmsweise
                           nicht tut, etwa beim Schemawechsel)

        204 und 304 kommen hier durch und werden beim Auswerten unterschieden:
        sie sind gueltige Antworten ohne Inhalt, nicht Fehler.
        """
        schleife = asyncio.get_event_loop()
        kopf = {
            'User-Agent': 'Mozilla/5.0 (compatible; ComplyoBot/1.0; +https://complyo.de)'
        }
        url = feed_url
        versuche_202 = 0
        umleitungen = 0

        while True:
            response = await schleife.run_in_executor(
                None,
                lambda ziel=url: requests.get(ziel, headers=kopf, timeout=30)
            )
            code = response.status_code

            if code == 202:
                # Nicht jedes 202 meint "Inhalt folgt". Eine Bot-Abwehr vor
                # der Quelle antwortet ebenfalls mit 202 und leerem Rumpf,
                # sagt es aber im Kopf (AWS WAF: x-amzn-waf-action:
                # challenge; so verhaelt sich europarl.europa.eu, Stand
                # 14.09.2026). Dagegen hilft kein Wiederholen — wer das nicht
                # unterscheidet, laesst jemanden ewig auf einen Inhalt warten,
                # der nie kommen wird.
                abwehr = (response.headers.get('x-amzn-waf-action')
                          or response.headers.get('cf-mitigated'))
                if abwehr:
                    return None, (
                        f"HTTP 202, aber vom Bot-Schutz der Quelle "
                        f"(\"{abwehr}\"), nicht \"Inhalt folgt\". Wiederholen "
                        f"hilft nicht; die Quelle ist von diesem Server aus "
                        f"nicht lesbar und braucht eine Entscheidung: ersetzen "
                        f"oder abschalten."
                    )
                if versuche_202 >= len(WARTEPLAN_202):
                    return None, (
                        f"HTTP 202 auch nach {len(WARTEPLAN_202) + 1} Abrufen "
                        f"ueber {sum(WARTEPLAN_202)}s. Inhalt folgte nie."
                    )
                warten = WARTEPLAN_202[versuche_202]
                versuche_202 += 1
                logger.info(
                    f"⏳ HTTP 202 (angenommen, Inhalt folgt) fuer {source_name}: "
                    f"erneuter Abruf in {warten}s "
                    f"({versuche_202}/{len(WARTEPLAN_202)})"
                )
                await asyncio.sleep(warten)
                continue

            if 300 <= code < 400 and response.headers.get('Location'):
                if umleitungen >= UMLEITUNGEN_MAX:
                    return None, f"HTTP {code}: mehr als {UMLEITUNGEN_MAX} Umleitungen"
                url = requests.compat.urljoin(url, response.headers['Location'])
                umleitungen += 1
                logger.info(f"↪️ HTTP {code} fuer {source_name}: folge nach {url}")
                continue

            return response, ""

    async def _fetch_and_parse_feed(
        self,
        feed_id: int,
        source_name: str,
        feed_url: str,
        category: str,
        keywords: List[str]
    ) -> Abrufergebnis:
        """Parst einen einzelnen RSS-Feed und speichert relevante Items"""
        try:
            response, abruf_fehler = await self._abrufen(feed_url, source_name)
            if response is None:
                logger.error(f"❌ {source_name}: {abruf_fehler}")
                return Abrufergebnis(fehler=abruf_fehler)

            code = response.status_code

            # 204 und 304 sind gueltige Antworten ohne Inhalt. Sie als Fehler
            # zu buchen waere dieselbe Verwechslung wie bei 202: die Quelle
            # hat geantwortet, sie hat nur nichts zu sagen.
            if code == 204:
                logger.info(f"ℹ️ HTTP 204 (kein Inhalt) fuer {source_name}")
                return Abrufergebnis(status=code)
            if code == 304:
                logger.info(f"ℹ️ HTTP 304 (unveraendert) fuer {source_name}")
                return Abrufergebnis(status=code)
            if code >= 400:
                logger.error(f"❌ HTTP {code} fuer {source_name}")
                return Abrufergebnis(status=code, fehler=f"HTTP {code}")
            if code != 200:
                logger.warning(f"⚠️ HTTP {code} fuer {source_name}, wird trotzdem gelesen")

            # Parse RSS-Feed
            feed = await asyncio.get_event_loop().run_in_executor(
                None, feedparser.parse, response.text
            )

            if feed.bozo:
                logger.warning(f"⚠️ Feed parsing warning for {source_name}: {feed.bozo_exception}")

            if not feed.entries:
                # HTTP 200, aber nichts Lesbares. Genau so sehen die Quellen
                # aus, deren Feed-Adresse auf eine HTML-Seite umgezogen ist
                # (EDPB News, Datenschutz.org, Stand 14.09.2026). Das frueher
                # hier folgende "✅ 0 neue Items gespeichert" war die Unwahrheit,
                # die beide monatelang verdeckt hat.
                grund = f"bozo: {feed.bozo_exception}" if feed.bozo else "Feed ohne Eintraege"
                logger.error(
                    f"❌ {source_name}: HTTP {code}, aber kein lesbarer Feed ({grund}) "
                    f"Adresse pruefen: {response.url}"
                )
                return Abrufergebnis(status=code, fehler=f"kein lesbarer Feed ({grund})")

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
            
            logger.info(
                f"✅ {source_name}: {new_items} neue Items gespeichert "
                f"({len(feed.entries)} Eintraege gelesen)"
            )
            return Abrufergebnis(
                neue_items=new_items,
                eintraege=len(feed.entries),
                status=code,
            )

        except Exception as e:
            logger.error(f"Error fetching feed {source_name}: {e}")
            return Abrufergebnis(fehler=f"{type(e).__name__}: {e}")
    
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

