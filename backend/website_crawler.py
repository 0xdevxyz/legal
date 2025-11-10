"""
Website Crawler für Complyo AI Fix Generation
Extrahiert Struktur und Kontext von Websites für personalisierte Fixes
Mit Caching-Support für bessere Performance und geringere API-Kosten
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import asyncpg
import json
import re
import logging

logger = logging.getLogger(__name__)

class WebsiteCrawler:
    def __init__(self, timeout: int = 30, db_pool: Optional[asyncpg.Pool] = None):
        self.timeout = timeout
        self.user_agent = 'Mozilla/5.0 (compatible; ComplyoBot/1.0; +https://complyo.tech/bot)'
        self.db_pool = db_pool
        self.cache_max_age_hours = 168  # 7 days
    
    async def crawl_website(self, url: str) -> Dict[str, Any]:
        """
        Hauptfunktion: Crawlt Website und extrahiert strukturierte Daten
        
        Args:
            url: URL der zu crawlenden Website
            
        Returns:
            Dict mit Website-Struktur, CMS-Info, Compliance-Status
        """
        try:
            logger.info(f"🕷️ Crawling website: {url}")
            
            # Normalisiere URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Fetch HTML
            html_content = await self._fetch_html(url)
            if not html_content:
                return self._get_fallback_structure(url)
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extrahiere alle Informationen
            structure = {
                'url': url,
                'domain': urlparse(url).netloc,
                'cms': self._detect_cms(soup, html_content),
                'structure': self._extract_structure(soup, url),
                'legal_pages': self._find_legal_pages(soup, url),
                'cookies': self._detect_cookies(soup),
                'accessibility': self._check_accessibility(soup),
                'meta_tags': self._extract_meta_tags(soup),
                'scripts': self._extract_scripts(soup),
                'footer': self._extract_footer(soup),
                'navigation': self._extract_navigation(soup),
                'technology_stack': self._detect_technology(soup, html_content)
            }
            
            logger.info(f"✅ Crawling completed for {url}")
            return structure
            
        except Exception as e:
            logger.error(f"❌ Crawling error for {url}: {e}")
            return self._get_fallback_structure(url)
    
    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetched HTML-Inhalt der Website"""
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8'
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, allow_redirects=True) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return None
    
    def _detect_cms(self, soup: BeautifulSoup, html: str) -> Dict[str, Any]:
        """Erkennt verwendetes CMS-System (erweitert)"""
        cms_info = {
            'detected': False,
            'type': 'custom',
            'version': None,
            'confidence': 0.0,
            'plugin_available': False,  # Ob Complyo-Plugin verfügbar ist
            'auto_fix_possible': False  # Ob Auto-Fixes möglich sind
        }
        
        # WordPress Detection (verbessert)
        wordpress_indicators = [
            'wp-content' in html,
            'wp-includes' in html,
            'wp-json' in html,
            bool(soup.find('link', rel='https://api.w.org/')),
            bool(soup.find('meta', attrs={'name': 'generator', 'content': re.compile('WordPress')}))
        ]
        
        if sum(wordpress_indicators) >= 2:
            cms_info.update({
                'detected': True,
                'type': 'wordpress',
                'confidence': 0.95,
                'plugin_available': True,
                'auto_fix_possible': True
            })
            
            # Version erkennen
            generator = soup.find('meta', attrs={'name': 'generator'})
            if generator and 'WordPress' in generator.get('content', ''):
                version_match = re.search(r'WordPress (\d+\.\d+(?:\.\d+)?)', generator.get('content', ''))
                if version_match:
                    cms_info['version'] = version_match.group(1)
        
        # Shopify Detection (verbessert)
        shopify_indicators = [
            'cdn.shopify.com' in html,
            'Shopify.theme' in html,
            'shopify-analytics' in html,
            bool(soup.find('meta', property='og:type', content='shopify.product'))
        ]
        
        if sum(shopify_indicators) >= 2:
            cms_info.update({
                'detected': True,
                'type': 'shopify',
                'confidence': 0.95,
                'plugin_available': True,  # Shopify App geplant
                'auto_fix_possible': True
            })
        
        # Wix Detection (verbessert)
        wix_indicators = [
            'wix.com' in html,
            '_wix' in html,
            'static.wixstatic.com' in html,
            bool(soup.find('meta', attrs={'name': 'generator', 'content': re.compile('Wix')}))
        ]
        
        if sum(wix_indicators) >= 2:
            cms_info.update({
                'detected': True,
                'type': 'wix',
                'confidence': 0.9,
                'plugin_available': False,  # Wix ist closed
                'auto_fix_possible': False  # Nur Widget möglich
            })
        
        # Joomla Detection
        joomla_indicators = [
            'Joomla' in html,
            '/components/com_' in html,
            '/templates/' in html and 'joomla' in html.lower(),
            bool(soup.find('meta', attrs={'name': 'generator', 'content': re.compile('Joomla')}))
        ]
        
        if sum(joomla_indicators) >= 2:
            cms_info.update({
                'detected': True,
                'type': 'joomla',
                'confidence': 0.85,
                'plugin_available': False,
                'auto_fix_possible': False
            })
            
        # Drupal Detection
        drupal_indicators = [
            '/sites/default/' in html,
            '/sites/all/' in html,
            'Drupal' in html,
            bool(soup.find('meta', attrs={'name': 'Generator', 'content': re.compile('Drupal')}))
        ]
        
        if sum(drupal_indicators) >= 2:
            cms_info.update({
                'detected': True,
                'type': 'drupal',
                'confidence': 0.85,
                'plugin_available': False,
                'auto_fix_possible': False
            })
        
        # TYPO3 Detection
        if 'typo3' in html.lower() or 'typo3conf' in html:
            cms_info.update({
                'detected': True,
                'type': 'typo3',
                'confidence': 0.8,
                'plugin_available': False,
                'auto_fix_possible': False
            })
        
        # Magento Detection
        magento_indicators = [
            'Mage.' in html,
            '/skin/frontend/' in html,
            '/media/catalog/' in html,
            'magento' in html.lower()
        ]
        
        if sum(magento_indicators) >= 2:
            cms_info.update({
                'detected': True,
                'type': 'magento',
                'confidence': 0.85,
                'plugin_available': False,
                'auto_fix_possible': False
            })
        
        # Squarespace Detection
        if 'squarespace' in html.lower() or 'sqsp.com' in html:
            cms_info.update({
                'detected': True,
                'type': 'squarespace',
                'confidence': 0.9,
                'plugin_available': False,
                'auto_fix_possible': False
            })
        
        # Webflow Detection
        if 'webflow' in html.lower() or 'wf-page' in html:
            cms_info.update({
                'detected': True,
                'type': 'webflow',
                'confidence': 0.9,
                'plugin_available': False,
                'auto_fix_possible': False
            })
        
        return cms_info
    
    def _extract_structure(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Extrahiert HTML-Struktur der Seite"""
        return {
            'has_header': bool(soup.find(['header', 'div'], class_=re.compile('header', re.I))),
            'has_footer': bool(soup.find(['footer', 'div'], class_=re.compile('footer', re.I))),
            'has_nav': bool(soup.find('nav')),
            'main_content_id': self._find_main_content_id(soup),
            'layout_type': self._detect_layout_type(soup),
            'total_links': len(soup.find_all('a')),
            'total_images': len(soup.find_all('img')),
            'has_forms': bool(soup.find('form'))
        }
    
    def _find_legal_pages(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Optional[str]]:
        """Findet Links zu rechtlichen Seiten (Impressum, Datenschutz, etc.)"""
        legal_pages = {
            'impressum': None,
            'datenschutz': None,
            'agb': None,
            'widerruf': None,
            'cookies': None
        }
        
        # Suche alle Links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text().lower().strip()
            
            # Impressum
            if any(keyword in href or keyword in text for keyword in ['impressum', 'imprint', 'legal-notice']):
                legal_pages['impressum'] = urljoin(base_url, link['href'])
            
            # Datenschutz
            elif any(keyword in href or keyword in text for keyword in ['datenschutz', 'privacy', 'dsgvo', 'gdpr']):
                legal_pages['datenschutz'] = urljoin(base_url, link['href'])
            
            # AGB
            elif any(keyword in href or keyword in text for keyword in ['agb', 'terms', 'conditions', 'nutzungsbedingungen']):
                legal_pages['agb'] = urljoin(base_url, link['href'])
            
            # Widerruf
            elif any(keyword in href or keyword in text for keyword in ['widerruf', 'cancellation', 'withdrawal']):
                legal_pages['widerruf'] = urljoin(base_url, link['href'])
            
            # Cookie-Richtlinie
            elif any(keyword in href or keyword in text for keyword in ['cookie', 'cookies']):
                legal_pages['cookies'] = urljoin(base_url, link['href'])
        
        return legal_pages
    
    def _detect_cookies(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detektiert Cookie-Banner und Cookie-Nutzung"""
        return {
            'has_cookie_banner': self._has_cookie_banner(soup),
            'cookie_scripts': self._find_cookie_scripts(soup),
            'tracking_detected': self._detect_tracking(soup)
        }
    
    def _has_cookie_banner(self, soup: BeautifulSoup) -> bool:
        """Prüft ob Cookie-Banner vorhanden"""
        cookie_indicators = [
            soup.find(id=re.compile('cookie', re.I)),
            soup.find(class_=re.compile('cookie', re.I)),
            soup.find(string=re.compile('cookie', re.I))
        ]
        return any(cookie_indicators)
    
    def _find_cookie_scripts(self, soup: BeautifulSoup) -> List[str]:
        """Findet Cookie-relevante Scripts"""
        cookie_scripts = []
        for script in soup.find_all('script', src=True):
            src = script['src'].lower()
            if any(keyword in src for keyword in ['cookie', 'consent', 'gdpr', 'cookiebot', 'onetrust']):
                cookie_scripts.append(script['src'])
        return cookie_scripts
    
    def _detect_tracking(self, soup: BeautifulSoup) -> Dict[str, bool]:
        """Erkennt verwendete Tracking-Dienste"""
        html_str = str(soup).lower()
        return {
            'google_analytics': 'google-analytics.com' in html_str or 'gtag' in html_str or 'ga(' in html_str,
            'google_tag_manager': 'googletagmanager.com' in html_str,
            'facebook_pixel': 'facebook.net' in html_str or 'fbq(' in html_str,
            'matomo': 'matomo' in html_str or 'piwik' in html_str,
            'hotjar': 'hotjar.com' in html_str
        }
    
    def _check_accessibility(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Prüft grundlegende Barrierefreiheits-Features"""
        images = soup.find_all('img')
        images_with_alt = sum(1 for img in images if img.get('alt'))
        
        return {
            'has_lang_attribute': bool(soup.html and soup.html.get('lang')),
            'images_with_alt': images_with_alt,
            'images_without_alt': len(images) - images_with_alt,
            'alt_text_coverage': (images_with_alt / len(images) * 100) if images else 100,
            'has_skip_links': bool(soup.find('a', href='#main') or soup.find('a', href='#content')),
            'has_aria_labels': bool(soup.find(attrs={'aria-label': True})),
            'heading_structure': self._check_heading_structure(soup)
        }
    
    def _check_heading_structure(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Prüft Überschriften-Hierarchie"""
        return {
            'h1_count': len(soup.find_all('h1')),
            'h2_count': len(soup.find_all('h2')),
            'h3_count': len(soup.find_all('h3')),
            'h4_count': len(soup.find_all('h4'))
        }
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Extrahiert wichtige Meta-Tags"""
        meta_tags = {
            'title': soup.title.string if soup.title else None,
            'description': None,
            'charset': None,
            'viewport': None,
            'robots': None
        }
        
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            property_attr = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if name == 'description' or property_attr == 'og:description':
                meta_tags['description'] = content
            elif meta.get('charset'):
                meta_tags['charset'] = meta.get('charset')
            elif name == 'viewport':
                meta_tags['viewport'] = content
            elif name == 'robots':
                meta_tags['robots'] = content
        
        return meta_tags
    
    def _extract_scripts(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extrahiert verwendete Scripts"""
        external_scripts = []
        inline_scripts_count = 0
        
        for script in soup.find_all('script'):
            if script.get('src'):
                external_scripts.append(script['src'])
            else:
                inline_scripts_count += 1
        
        return {
            'external': external_scripts[:20],  # Limit für Performance
            'inline_count': inline_scripts_count
        }
    
    def _extract_footer(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrahiert Footer-Informationen"""
        footer = soup.find(['footer', 'div'], class_=re.compile('footer', re.I))
        
        if footer:
            links = [a.get_text().strip() for a in footer.find_all('a') if a.get_text().strip()]
            return {
                'exists': True,
                'has_legal_links': any(keyword in ' '.join(links).lower() for keyword in ['impressum', 'datenschutz', 'agb']),
                'link_count': len(links),
                'links': links[:15]  # Erste 15 Links
            }
        
        return {'exists': False}
    
    def _extract_navigation(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrahiert Navigation-Struktur"""
        nav = soup.find('nav')
        
        if nav:
            links = [a.get_text().strip() for a in nav.find_all('a') if a.get_text().strip()]
            return {
                'exists': True,
                'type': 'nav_element',
                'link_count': len(links),
                'links': links
            }
        
        return {'exists': False}
    
    def _detect_technology(self, soup: BeautifulSoup, html: str) -> Dict[str, bool]:
        """Erkennt verwendete Technologien"""
        return {
            'jquery': 'jquery' in html.lower(),
            'react': '_react' in html.lower() or 'react' in html.lower(),
            'vue': 'vue.js' in html.lower() or '__vue__' in html.lower(),
            'bootstrap': 'bootstrap' in html.lower(),
            'tailwind': 'tailwind' in html.lower(),
            'nextjs': '__next' in html.lower() or '_next' in html.lower()
        }
    
    def _find_main_content_id(self, soup: BeautifulSoup) -> Optional[str]:
        """Findet ID des Haupt-Content-Bereichs"""
        main = soup.find(['main', 'div'], id=re.compile('main|content', re.I))
        if main and main.get('id'):
            return main.get('id')
        return None
    
    def _detect_layout_type(self, soup: BeautifulSoup) -> str:
        """Erkennt Layout-Typ der Seite"""
        # Vereinfachte Erkennung
        if soup.find('aside') or soup.find('div', class_=re.compile('sidebar', re.I)):
            return 'sidebar'
        return 'single-column'
    
    def _get_fallback_structure(self, url: str) -> Dict[str, Any]:
        """Fallback-Struktur wenn Crawling fehlschlägt"""
        return {
            'url': url,
            'domain': urlparse(url).netloc,
            'crawl_failed': True,
            'cms': {'detected': False, 'type': 'unknown'},
            'structure': {},
            'legal_pages': {},
            'cookies': {},
            'accessibility': {},
            'meta_tags': {},
            'scripts': {},
            'footer': {},
            'navigation': {},
            'technology_stack': {}
        }
    
    async def get_cached_structure(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Holt gecachte Website-Struktur aus DB (wenn frisch genug)
        
        Returns:
            Gecachte Struktur oder None
        """
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.acquire() as conn:
                cache = await conn.fetchrow(
                    """
                    SELECT structure_data, crawled_at
                    FROM website_structures
                    WHERE url = $1
                      AND is_stale = FALSE
                      AND crawled_at >= $2
                    ORDER BY crawled_at DESC
                    LIMIT 1
                    """,
                    url,
                    datetime.now() - timedelta(hours=self.cache_max_age_hours)
                )
                
                if cache:
                    age_hours = (datetime.now() - cache['crawled_at']).total_seconds() / 3600
                    logger.info(f"✅ Cache hit for {url} (age: {age_hours:.1f}h)")
                    return json.loads(cache['structure_data']) if isinstance(cache['structure_data'], str) else cache['structure_data']
                else:
                    logger.info(f"ℹ️ Cache miss for {url}")
                    return None
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    async def save_structure_to_cache(
        self, 
        url: str, 
        structure: Dict[str, Any],
        website_id: Optional[int] = None
    ) -> bool:
        """
        Speichert Website-Struktur in DB-Cache
        
        Args:
            url: Website URL
            structure: Crawler-Daten
            website_id: Optional tracked_websites ID
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self.db_pool:
            return False
        
        try:
            cms_info = structure.get('cms', {})
            legal_pages = structure.get('legal_pages', {})
            tracking = structure.get('cookies', {}).get('tracking_detected', {})
            accessibility = structure.get('accessibility', {})
            tech_stack = structure.get('technology_stack', {})
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO website_structures (
                        website_id, url, structure_data, cms_type, cms_version, cms_confidence,
                        has_legal_pages, tracking_services, accessibility_score, technology_stack,
                        crawled_at, is_stale
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (website_id)
                    DO UPDATE SET
                        structure_data = EXCLUDED.structure_data,
                        cms_type = EXCLUDED.cms_type,
                        cms_version = EXCLUDED.cms_version,
                        cms_confidence = EXCLUDED.cms_confidence,
                        has_legal_pages = EXCLUDED.has_legal_pages,
                        tracking_services = EXCLUDED.tracking_services,
                        accessibility_score = EXCLUDED.accessibility_score,
                        technology_stack = EXCLUDED.technology_stack,
                        crawled_at = EXCLUDED.crawled_at,
                        is_stale = FALSE,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    website_id,
                    url,
                    json.dumps(structure),
                    cms_info.get('type'),
                    cms_info.get('version'),
                    cms_info.get('confidence', 0.0),
                    json.dumps(legal_pages),
                    json.dumps(tracking),
                    int(accessibility.get('alt_text_coverage', 0)),
                    json.dumps(tech_stack),
                    datetime.now(),
                    False
                )
                logger.info(f"✅ Cached structure for {url}")
                return True
        except Exception as e:
            logger.error(f"Cache save error: {e}")
            return False

# Utility-Funktion für einfachen Zugriff
async def crawl_website(url: str, db_pool: Optional[asyncpg.Pool] = None, use_cache: bool = True) -> Dict[str, Any]:
    """
    Convenience-Funktion für schnellen Website-Crawl mit optionalem Caching
    
    Args:
        url: Website URL
        db_pool: Optional Database Pool für Caching
        use_cache: Nutze Cache wenn verfügbar (default: True)
    """
    crawler = WebsiteCrawler(db_pool=db_pool)
    
    # Versuche Cache wenn aktiviert
    if use_cache and db_pool:
        cached = await crawler.get_cached_structure(url)
        if cached:
            return cached
    
    # Crawl und cache
    structure = await crawler.crawl_website(url)
    if db_pool and not structure.get('crawl_failed'):
        await crawler.save_structure_to_cache(url, structure)
    
    return structure

