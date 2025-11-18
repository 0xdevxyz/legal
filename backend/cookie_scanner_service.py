"""
Cookie Scanner Service
Scannt Websites und erkennt automatisch verwendete Cookie-Services
"""

import asyncio
import re
from typing import List, Dict, Any, Set
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class CookieScanner:
    """Scannt Websites nach Cookie-Services"""
    
    # Service Detection Patterns
    DETECTION_PATTERNS = {
        # === Analytics & Tracking ===
        'google_analytics_ga4': {
            'patterns': [
                r'googletagmanager\.com/gtag/js',
                r'google-analytics\.com/analytics\.js',
                r'GA_MEASUREMENT_ID',
                r'gtag\(.*?config.*?G-',
                r'_ga',
                r'_gid',
                r'_gat',
            ],
            'confidence_boost': ['gtag', 'GA_MEASUREMENT_ID']
        },
        'google_tag_manager': {
            'patterns': [
                r'googletagmanager\.com/gtm\.js',
                r'GTM-[A-Z0-9]+',
            ],
            'confidence_boost': ['GTM-']
        },
        'matomo': {
            'patterns': [
                r'matomo\.js',
                r'piwik\.js',
                r'_pk_id',
                r'_pk_ses',
            ],
            'confidence_boost': ['matomo.js', 'piwik.js']
        },
        'hotjar': {
            'patterns': [
                r'static\.hotjar\.com',
                r'hotjar\.com/c/hotjar',
                r'_hjid',
                r'_hjSession',
            ],
            'confidence_boost': ['static.hotjar.com']
        },
        'plausible': {
            'patterns': [
                r'plausible\.io/js',
            ],
            'confidence_boost': ['plausible.io/js']
        },
        
        # === Marketing & Advertising ===
        'facebook_pixel': {
            'patterns': [
                r'connect\.facebook\.net',
                r'fbq\(',
                r'facebook\.com/tr',
                r'_fbp',
                r'_fbc',
            ],
            'confidence_boost': ['fbq(', 'facebook.com/tr']
        },
        'google_ads': {
            'patterns': [
                r'googleadservices\.com',
                r'doubleclick\.net',
                r'_gcl_au',
                r'_gcl_aw',
                r'_gac_',
            ],
            'confidence_boost': ['googleadservices.com', 'doubleclick.net']
        },
        'linkedin_insight': {
            'patterns': [
                r'snap\.licdn\.com',
                r'linkedin\.com/px',
                r'li_fat_id',
                r'lidc',
            ],
            'confidence_boost': ['snap.licdn.com']
        },
        'tiktok_pixel': {
            'patterns': [
                r'analytics\.tiktok\.com',
                r'ttq\.load',
                r'_ttp',
            ],
            'confidence_boost': ['analytics.tiktok.com']
        },
        'twitter_x': {
            'patterns': [
                r'platform\.twitter\.com',
                r'platform\.x\.com',
                r'twitter\.com/widgets',
                r'twq\(',
            ],
            'confidence_boost': ['platform.twitter.com', 'twitter.com/widgets']
        },
        
        # === Content & Media ===
        'youtube': {
            'patterns': [
                r'youtube\.com/embed',
                r'youtube-nocookie\.com',
                r'youtu\.be',
                r'youtube\.com/iframe_api',
            ],
            'confidence_boost': ['youtube.com/embed']
        },
        'vimeo': {
            'patterns': [
                r'player\.vimeo\.com',
                r'vimeo\.com/video',
                r'vimeo_player',
            ],
            'confidence_boost': ['player.vimeo.com']
        },
        'instagram': {
            'patterns': [
                r'instagram\.com/embed',
                r'cdninstagram\.com',
            ],
            'confidence_boost': ['instagram.com/embed']
        },
        'google_maps': {
            'patterns': [
                r'maps\.googleapis\.com',
                r'maps\.google\.com',
                r'google\.com/maps/embed',
            ],
            'confidence_boost': ['maps.googleapis.com', 'maps.google.com/maps/embed']
        },
        'openstreetmap': {
            'patterns': [
                r'openstreetmap\.org',
                r'tile\.openstreetmap\.org',
            ],
            'confidence_boost': ['openstreetmap.org/export/embed']
        },
        
        # === WordPress & CMS ===
        'wordpress': {
            'patterns': [
                r'wp-content/',
                r'wp-includes/',
                r'/wp-json/',
                r'wordpress_logged_in',
                r'wordpress_test_cookie',
                r'wp-settings-',
                r'wp_woocommerce_session',
                r'woocommerce_cart_hash',
                r'wp-admin',
                r'/wp-',
            ],
            'confidence_boost': ['wp-content/', 'wp-includes/', 'wordpress_']
        },
        'woocommerce': {
            'patterns': [
                r'woocommerce',
                r'woocommerce_cart_hash',
                r'woocommerce_items_in_cart',
                r'wp_woocommerce_session',
                r'wc_cart_hash',
                r'wc_fragments',
            ],
            'confidence_boost': ['woocommerce', 'wc_cart_hash']
        },
        'elementor': {
            'patterns': [
                r'elementor',
                r'wp-content/plugins/elementor',
                r'elementor-kit-',
            ],
            'confidence_boost': ['elementor']
        },
        'yoast_seo': {
            'patterns': [
                r'yoast',
                r'wp-content/plugins/wordpress-seo',
            ],
            'confidence_boost': ['yoast']
        },
        
        # === E-Commerce ===
        'shopify': {
            'patterns': [
                r'cdn\.shopify\.com',
                r'myshopify\.com',
                r'_shopify_',
                r'cart_currency',
                r'secure_customer_sig',
            ],
            'confidence_boost': ['cdn.shopify.com', '_shopify_']
        },
        'stripe': {
            'patterns': [
                r'js\.stripe\.com',
                r'checkout\.stripe\.com',
            ],
            'confidence_boost': ['js.stripe.com']
        },
        'paypal': {
            'patterns': [
                r'paypal\.com/sdk',
                r'paypalobjects\.com',
                r'PYPF',
            ],
            'confidence_boost': ['paypal.com/sdk']
        },
        
        # === Support & Chat ===
        'intercom': {
            'patterns': [
                r'widget\.intercom\.io',
                r'intercom\.io',
                r'intercom-',
            ],
            'confidence_boost': ['widget.intercom.io']
        },
        'zendesk': {
            'patterns': [
                r'static\.zdassets\.com',
                r'zendesk\.com',
                r'__zlcmid',
            ],
            'confidence_boost': ['static.zdassets.com']
        },
        'tawk': {
            'patterns': [
                r'embed\.tawk\.to',
                r'tawk\.to',
            ],
            'confidence_boost': ['embed.tawk.to']
        },
        'crisp': {
            'patterns': [
                r'client\.crisp\.chat',
                r'crisp\.chat',
            ],
            'confidence_boost': ['client.crisp.chat']
        },
        
        # === Fonts & Resources ===
        'google_fonts': {
            'patterns': [
                r'fonts\.googleapis\.com',
                r'fonts\.gstatic\.com',
            ],
            'confidence_boost': ['fonts.googleapis.com']
        },
        
        # === Other CMS/Platforms ===
        'joomla': {
            'patterns': [
                r'/media/jui/',
                r'/media/system/',
                r'Joomla!',
                r'joomla_',
            ],
            'confidence_boost': ['Joomla!', '/media/jui/']
        },
        'drupal': {
            'patterns': [
                r'Drupal',
                r'/sites/all/',
                r'/sites/default/',
                r'drupal\.js',
            ],
            'confidence_boost': ['Drupal', '/sites/all/']
        },
        'magento': {
            'patterns': [
                r'Magento',
                r'/mage/',
                r'frontend_cid',
                r'mage-cache',
            ],
            'confidence_boost': ['Magento', '/mage/']
        },
        'prestashop': {
            'patterns': [
                r'PrestaShop',
                r'/modules/',
                r'prestashop',
            ],
            'confidence_boost': ['PrestaShop']
        },
        
        # === CDN & Performance ===
        'cloudflare': {
            'patterns': [
                r'cloudflare',
                r'__cfduid',
                r'cf_clearance',
                r'cdn\.cloudflare\.com',
            ],
            'confidence_boost': ['cloudflare', '__cfduid']
        },
        
        # === Session & Authentication ===
        'php_session': {
            'patterns': [
                r'PHPSESSID',
            ],
            'confidence_boost': ['PHPSESSID']
        },
    }
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def scan_website(self, url: str) -> Dict[str, Any]:
        """
        Scannt eine Website und erkennt verwendete Services
        
        Returns:
            {
                'url': 'https://example.com',
                'detected_services': ['google_analytics_ga4', 'youtube'],
                'confidence': {'google_analytics_ga4': 0.95, 'youtube': 0.8},
                'scripts': [...],
                'iframes': [...],
                'cookies_mentioned': [...]
            }
        """
        try:
            html_content = await self._fetch_html(url)
            if not html_content:
                return {
                    'url': url,
                    'error': 'Failed to fetch website',
                    'detected_services': [],
                    'confidence': {}
                }
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract all relevant content
            scripts = self._extract_scripts(soup)
            iframes = self._extract_iframes(soup)
            links = self._extract_links(soup)
            meta_tags = self._extract_meta_tags(soup)
            text_content = soup.get_text()
            
            # Combine all content for analysis
            all_content = html_content + '\n' + text_content + '\n' + '\n'.join(meta_tags)
            
            # Detect services
            detected = self._detect_services(all_content, scripts, iframes, links, meta_tags)
            
            return {
                'url': url,
                'detected_services': list(detected['services']),
                'confidence': detected['confidence'],
                'scripts': scripts[:20],  # Limit for response size
                'iframes': iframes[:20],
                'scan_timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error scanning website {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'detected_services': [],
                'confidence': {}
            }
    
    async def _fetch_html(self, url: str) -> str:
        """Fetches HTML content from URL"""
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return ''
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ''
    
    def _extract_scripts(self, soup: BeautifulSoup) -> List[str]:
        """Extracts all script sources"""
        scripts = []
        for script in soup.find_all('script'):
            if script.get('src'):
                scripts.append(script['src'])
            elif script.string:
                # Inline scripts - get first 500 chars
                scripts.append(script.string[:500])
        return scripts
    
    def _extract_iframes(self, soup: BeautifulSoup) -> List[str]:
        """Extracts all iframe sources"""
        iframes = []
        for iframe in soup.find_all('iframe'):
            if iframe.get('src'):
                iframes.append(iframe['src'])
        return iframes
    
    def _extract_links(self, soup: BeautifulSoup) -> List[str]:
        """Extracts all link hrefs (for fonts, stylesheets, etc.)"""
        links = []
        for link in soup.find_all('link'):
            if link.get('href'):
                links.append(link['href'])
        return links
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extracts all meta tag content"""
        meta_content = []
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                meta_content.append(f"{meta.get('name')}: {meta.get('content', '')}")
            if meta.get('property'):
                meta_content.append(f"{meta.get('property')}: {meta.get('content', '')}")
            if meta.get('content'):
                meta_content.append(meta.get('content'))
        return meta_content
    
    def _detect_services(
        self, 
        content: str, 
        scripts: List[str], 
        iframes: List[str],
        links: List[str],
        meta_tags: List[str]
    ) -> Dict[str, Any]:
        """Detects services based on patterns"""
        
        detected_services: Set[str] = set()
        confidence: Dict[str, float] = {}
        
        # Combine all sources for comprehensive scanning
        all_sources = '\n'.join([
            content,
            '\n'.join(scripts),
            '\n'.join(iframes),
            '\n'.join(links),
            '\n'.join(meta_tags)
        ])
        
        for service_key, detection in self.DETECTION_PATTERNS.items():
            score = 0
            matches = 0
            matched_patterns = []
            
            # Check patterns
            for pattern in detection['patterns']:
                if re.search(pattern, all_sources, re.IGNORECASE):
                    matches += 1
                    score += 1
                    matched_patterns.append(pattern)
                    
                    # Boost confidence for high-value patterns
                    if any(boost in pattern for boost in detection.get('confidence_boost', [])):
                        score += 2
            
            # Calculate confidence
            if matches > 0:
                # Base confidence on number of matches
                conf = min(0.5 + (matches * 0.15), 1.0)
                
                # Boost confidence for multiple matches
                if matches >= 4:
                    conf = 0.98
                elif matches >= 3:
                    conf = 0.90
                elif matches == 2:
                    conf = 0.75
                elif matches == 1:
                    conf = 0.60
                
                detected_services.add(service_key)
                confidence[service_key] = conf
                
                logger.info(f"Detected {service_key} with {matches} matches (confidence: {conf:.2f})")
        
        return {
            'services': detected_services,
            'confidence': confidence
        }
    
    def _get_timestamp(self) -> str:
        """Returns current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Singleton instance
cookie_scanner = CookieScanner()

