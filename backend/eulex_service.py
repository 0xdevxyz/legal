"""
EU-Lex API Integration
Fetcht Gesetzesänderungen von EUR-Lex (EU-Recht)
Fokus auf: DSGVO, ePrivacy, AI Act, Digital Services Act
"""

import aiohttp
import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET
import logging
import re

logger = logging.getLogger(__name__)

EURLEX_SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
EURLEX_CELLAR_BASE = "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:"

RELEVANT_CELEX_PREFIXES = [
    "32016R0679",  # DSGVO
    "32002L0058",  # ePrivacy-Richtlinie
    "32024R1689",  # AI Act
    "32022R2065",  # Digital Services Act
    "32022R1925",  # Digital Markets Act
    "32019R0881",  # Cybersecurity Act
]

KEYWORD_FILTERS = [
    "Datenschutz", "personenbezogene Daten", "Verarbeitung",
    "Cookie", "elektronische Kommunikation", "Privatsphäre",
    "künstliche Intelligenz", "KI-System", "Algorithmus",
    "digitale Dienste", "Online-Plattform", "Barrierefreiheit"
]


class EULexService:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'ComplyoBot/1.0 (+https://complyo.tech)',
                    'Accept': 'application/sparql-results+xml, application/xml'
                }
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_recent_changes(self, days_back: int = 30) -> Dict[str, Any]:
        """Fetcht kürzliche Änderungen von EUR-Lex"""
        results = {
            "fetched": 0,
            "new_items": 0,
            "errors": []
        }
        
        try:
            changes = await self._query_eurlex_changes(days_back)
            results["fetched"] = len(changes)
            
            for change in changes:
                try:
                    saved = await self._save_legal_change(change)
                    if saved:
                        results["new_items"] += 1
                except Exception as e:
                    error_msg = f"Error saving change {change.get('celex')}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    
        except Exception as e:
            logger.error(f"Error fetching EUR-Lex changes: {e}")
            results["errors"].append(str(e))
            
        return results
    
    async def _query_eurlex_changes(self, days_back: int) -> List[Dict[str, Any]]:
        """SPARQL-Query für kürzliche EU-Rechtsänderungen"""
        date_filter = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        sparql_query = f"""
        PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        
        SELECT DISTINCT ?celex ?title ?date ?type WHERE {{
            ?work cdm:resource_legal_id_celex ?celex .
            ?work cdm:work_date_document ?date .
            ?work cdm:resource_legal_is_about_concept_eurovoc ?subject .
            
            OPTIONAL {{ ?work cdm:work_title ?title }}
            OPTIONAL {{ ?work cdm:resource_legal_type ?type }}
            
            FILTER (
                ?date >= "{date_filter}"^^xsd:date &&
                (
                    CONTAINS(LCASE(STR(?subject)), "datenschutz") ||
                    CONTAINS(LCASE(STR(?subject)), "data protection") ||
                    CONTAINS(LCASE(STR(?subject)), "elektronische kommunikation") ||
                    CONTAINS(LCASE(STR(?subject)), "künstliche intelligenz") ||
                    CONTAINS(LCASE(STR(?subject)), "artificial intelligence") ||
                    CONTAINS(LCASE(STR(?subject)), "digitale dienste") ||
                    CONTAINS(LCASE(STR(?subject)), "digital services")
                )
            )
        }}
        ORDER BY DESC(?date)
        LIMIT 100
        """
        
        try:
            session = await self._get_session()
            async with session.get(
                EURLEX_SPARQL_ENDPOINT,
                params={'query': sparql_query, 'format': 'application/sparql-results+xml'},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    logger.error(f"EUR-Lex API error: {response.status}")
                    return []
                
                xml_text = await response.text()
                return self._parse_sparql_results(xml_text)
                
        except Exception as e:
            logger.error(f"Error querying EUR-Lex: {e}")
            return []
    
    def _parse_sparql_results(self, xml_text: str) -> List[Dict[str, Any]]:
        """Parst SPARQL-XML-Ergebnisse"""
        results = []
        
        try:
            root = ET.fromstring(xml_text)
            ns = {'sparql': 'http://www.w3.org/2005/sparql-results#'}
            
            for result in root.findall('.//sparql:result', ns):
                item = {}
                
                for binding in result.findall('sparql:binding', ns):
                    name = binding.get('name')
                    value_elem = binding.find('sparql:literal', ns) or binding.find('sparql:uri', ns)
                    
                    if value_elem is not None:
                        item[name] = value_elem.text
                
                if item.get('celex'):
                    results.append({
                        'celex': item.get('celex', ''),
                        'title': item.get('title', 'EU-Rechtsakt'),
                        'date': item.get('date', ''),
                        'type': item.get('type', 'Unbekannt'),
                        'url': f"{EURLEX_CELLAR_BASE}{item.get('celex', '')}",
                        'source': 'EUR-Lex'
                    })
                    
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            
        return results
    
    async def _save_legal_change(self, change: Dict[str, Any]) -> bool:
        """Speichert EUR-Lex Änderung in legal_news Tabelle"""
        try:
            async with self.db_pool.acquire() as conn:
                exists = await conn.fetchval("""
                    SELECT id FROM legal_news 
                    WHERE url = $1 OR title = $2
                """, change['url'], change['title'])
                
                if exists:
                    return False
                
                severity = self._determine_severity(change)
                news_type = self._determine_news_type(change)
                keywords = self._extract_keywords(change)
                
                published_date = datetime.now()
                if change.get('date'):
                    try:
                        published_date = datetime.strptime(change['date'], '%Y-%m-%d')
                    except:
                        pass
                
                await conn.execute("""
                    INSERT INTO legal_news (
                        title, summary, content, url, source, source_feed,
                        published_date, news_type, severity, keywords
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                    change['title'],
                    f"EU-Rechtsakt: {change['title']}",
                    f"CELEX: {change['celex']} - {change.get('type', 'EU-Rechtsakt')}",
                    change['url'],
                    'EUR-Lex',
                    'EU-Gesetzgebung',
                    published_date,
                    news_type,
                    severity,
                    keywords
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error saving EUR-Lex change: {e}")
            return False
    
    def _determine_severity(self, change: Dict[str, Any]) -> str:
        """Bestimmt Severity basierend auf Änderungstyp"""
        title_lower = change.get('title', '').lower()
        type_lower = change.get('type', '').lower()
        
        if any(word in title_lower for word in ['verordnung', 'regulation']):
            return 'critical'
        if any(word in title_lower for word in ['richtlinie', 'directive']):
            return 'warning'
        if any(word in type_lower for word in ['durchführungsverordnung', 'delegierte']):
            return 'warning'
            
        return 'info'
    
    def _determine_news_type(self, change: Dict[str, Any]) -> str:
        """Bestimmt News-Typ"""
        type_lower = change.get('type', '').lower()
        
        if 'verordnung' in type_lower or 'regulation' in type_lower:
            return 'critical'
        if 'richtlinie' in type_lower or 'directive' in type_lower:
            return 'update'
        if 'beschluss' in type_lower or 'decision' in type_lower:
            return 'update'
            
        return 'info'
    
    def _extract_keywords(self, change: Dict[str, Any]) -> List[str]:
        """Extrahiert relevante Keywords"""
        text = f"{change.get('title', '')} {change.get('type', '')}".lower()
        
        keywords = []
        keyword_mapping = {
            'datenschutz': 'DSGVO',
            'data protection': 'DSGVO',
            'künstliche intelligenz': 'AI Act',
            'artificial intelligence': 'AI Act',
            'elektronische kommunikation': 'ePrivacy',
            'electronic communication': 'ePrivacy',
            'cookie': 'Cookie',
            'digitale dienste': 'DSA',
            'digital services': 'DSA',
            'barrierefreiheit': 'Barrierefreiheit',
            'accessibility': 'Barrierefreiheit'
        }
        
        for pattern, keyword in keyword_mapping.items():
            if pattern in text and keyword not in keywords:
                keywords.append(keyword)
        
        if 'verordnung' in text or 'regulation' in text:
            keywords.append('EU-Verordnung')
        if 'richtlinie' in text or 'directive' in text:
            keywords.append('EU-Richtlinie')
            
        return keywords if keywords else ['EU-Recht']


eulex_service: Optional[EULexService] = None

def init_eulex_service(db_pool: asyncpg.Pool) -> EULexService:
    """Initialisiert den EU-Lex Service"""
    global eulex_service
    eulex_service = EULexService(db_pool)
    return eulex_service
