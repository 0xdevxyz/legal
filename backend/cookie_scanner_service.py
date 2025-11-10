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
        'google_analytics_ga4': {
            'patterns': [
                r'googletagmanager\.com/gtag/js',
                r'google-analytics\.com/analytics\.js',
                r'GA_MEASUREMENT_ID',
                r'gtag\(.*?config.*?G-',
                r'_ga',
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
        'facebook_pixel': {
            'patterns': [
                r'connect\.facebook\.net',
                r'fbq\(',
                r'facebook\.com/tr',
                r'_fbp',
            ],
            'confidence_boost': ['fbq(', 'facebook.com/tr']
        },
        'youtube': {
            'patterns': [
                r'youtube\.com/embed',
                r'youtube-nocookie\.com',
                r'youtu\.be',
            ],
            'confidence_boost': ['youtube.com/embed']
        },
        'google_maps': {
            'patterns': [
                r'maps\.googleapis\.com',
                r'maps\.google\.com',
                r'google\.com/maps/embed',
            ],
            'confidence_boost': ['maps.googleapis.com', 'maps.google.com/maps/embed']
        },
        'vimeo': {
            'patterns': [
                r'player\.vimeo\.com',
                r'vimeo\.com/video',
            ],
            'confidence_boost': ['player.vimeo.com']
        },
        'linkedin_insight': {
            'patterns': [
                r'snap\.licdn\.com',
                r'linkedin\.com/px',
            ],
            'confidence_boost': ['snap.licdn.com']
        },
        'tiktok_pixel': {
            'patterns': [
                r'analytics\.tiktok\.com',
                r'ttq\.load',
            ],
            'confidence_boost': ['analytics.tiktok.com']
        },
        'google_ads': {
            'patterns': [
                r'googleadservices\.com',
                r'doubleclick\.net',
                r'_gcl_au',
            ],
            'confidence_boost': ['googleadservices.com']
        },
        'matomo': {
            'patterns': [
                r'matomo\.js',
                r'piwik\.js',
                r'_pk_id',
            ],
            'confidence_boost': ['matomo.js', 'piwik.js']
        },
        'hotjar': {
            'patterns': [
                r'static\.hotjar\.com',
                r'hotjar\.com/c/hotjar',
            ],
            'confidence_boost': ['static.hotjar.com']
        },
        'intercom': {
            'patterns': [
                r'widget\.intercom\.io',
                r'intercom\.io',
            ],
            'confidence_boost': ['widget.intercom.io']
        },
        'zendesk': {
            'patterns': [
                r'static\.zdassets\.com',
                r'zendesk\.com',
            ],
            'confidence_boost': ['static.zdassets.com']
        },
        'instagram': {
            'patterns': [
                r'instagram\.com/embed',
                r'cdninstagram\.com',
            ],
            'confidence_boost': ['instagram.com/embed']
        },
        'twitter_x': {
            'patterns': [
                r'platform\.twitter\.com',
                r'platform\.x\.com',
                r'twitter\.com/widgets',
            ],
            'confidence_boost': ['platform.twitter.com', 'twitter.com/widgets']
        },
        'google_fonts': {
            'patterns': [
                r'fonts\.googleapis\.com',
                r'fonts\.gstatic\.com',
            ],
            'confidence_boost': ['fonts.googleapis.com']
        },
        'stripe': {
            'patterns': [
                r'js\.stripe\.com',
                r'checkout\.stripe\.com',
            ],
            'confidence_boost': ['js.stripe.com']
        },
        'openstreetmap': {
            'patterns': [
                r'openstreetmap\.org',
                r'tile\.openstreetmap\.org',
            ],
            'confidence_boost': ['openstreetmap.org/export/embed']
        },
        'plausible': {
            'patterns': [
                r'plausible\.io/js',
            ],
            'confidence_boost': ['plausible.io/js']
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
            text_content = soup.get_text()
            
            # Combine all content for analysis
            all_content = html_content + '\n' + text_content
            
            # Detect services
            detected = self._detect_services(all_content, scripts, iframes, links)
            
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
    
    def _detect_services(
        self, 
        content: str, 
        scripts: List[str], 
        iframes: List[str],
        links: List[str]
    ) -> Dict[str, Any]:
        """Detects services based on patterns"""
        
        detected_services: Set[str] = set()
        confidence: Dict[str, float] = {}
        
        for service_key, detection in self.DETECTION_PATTERNS.items():
            score = 0
            matches = 0
            
            # Check patterns
            for pattern in detection['patterns']:
                if re.search(pattern, content, re.IGNORECASE):
                    matches += 1
                    score += 1
                    
                    # Boost confidence for high-value patterns
                    if any(boost in pattern for boost in detection.get('confidence_boost', [])):
                        score += 2
            
            # Calculate confidence
            if matches > 0:
                # Base confidence on number of matches
                conf = min(0.5 + (matches * 0.2), 1.0)
                
                # Boost confidence for multiple matches
                if matches >= 3:
                    conf = 0.95
                elif matches == 2:
                    conf = 0.8
                elif matches == 1:
                    conf = 0.6
                
                detected_services.add(service_key)
                confidence[service_key] = conf
        
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

