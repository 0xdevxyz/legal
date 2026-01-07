"""
Headless Cookie Scanner Service
Scannt Websites mit Playwright fuer vollstaendige Cookie/Storage-Erkennung

Features:
- Echtes Browser-Rendering (Chromium)
- JavaScript-Ausfuehrung
- Cookie-Erkennung
- Local Storage Scanning
- Session Storage Scanning
- Third-Party Request Tracking
- Network Request Interception

(c) 2025 Complyo
"""

import asyncio
import re
import json
import hashlib
from typing import List, Dict, Any, Set, Optional
from datetime import datetime
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Check if playwright is available
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Headless scanning disabled.")


class HeadlessCookieScanner:
    """
    Headless Browser Scanner fuer umfassende Cookie/Tracker-Erkennung
    
    Nutzt Playwright (Chromium) fuer:
    - Vollstaendiges JS-Rendering
    - Cookie-Auslesen
    - Local/Session Storage Scanning
    - Third-Party Request Tracking
    """
    
    # Known tracking domains by category
    TRACKING_DOMAINS = {
        'analytics': [
            'google-analytics.com',
            'googletagmanager.com',
            'analytics.google.com',
            'matomo',
            'piwik',
            'hotjar.com',
            'plausible.io',
            'segment.com',
            'mixpanel.com',
            'amplitude.com',
            'heap.io',
            'fullstory.com',
            'mouseflow.com',
            'clarity.ms',
        ],
        'marketing': [
            'facebook.com',
            'facebook.net',
            'fbcdn.net',
            'doubleclick.net',
            'googlesyndication.com',
            'googleadservices.com',
            'linkedin.com',
            'snap.licdn.com',
            'tiktok.com',
            'twitter.com',
            'ads.twitter.com',
            'pinterest.com',
            'criteo.com',
            'outbrain.com',
            'taboola.com',
            'bing.com/bat',
            'ads.yahoo.com',
        ],
        'functional': [
            'intercom.io',
            'zendesk.com',
            'zdassets.com',
            'crisp.chat',
            'tawk.to',
            'livechat.com',
            'drift.com',
            'hubspot.com',
            'freshdesk.com',
        ],
        'media': [
            'youtube.com',
            'youtube-nocookie.com',
            'vimeo.com',
            'dailymotion.com',
            'wistia.com',
            'soundcloud.com',
            'spotify.com',
        ],
        'maps': [
            'maps.googleapis.com',
            'maps.google.com',
            'openstreetmap.org',
            'mapbox.com',
            'here.com',
        ],
        'fonts': [
            'fonts.googleapis.com',
            'fonts.gstatic.com',
            'use.typekit.net',
            'fast.fonts.net',
        ],
        'cdn': [
            'cloudflare.com',
            'jsdelivr.net',
            'unpkg.com',
            'cdnjs.cloudflare.com',
            'bootstrapcdn.com',
        ]
    }
    
    # Known cookie patterns
    COOKIE_PATTERNS = {
        'google_analytics': ['_ga', '_gid', '_gat', '_gac_'],
        'google_ads': ['_gcl_au', '_gcl_aw', '_gcl_dc'],
        'facebook': ['_fbp', '_fbc', 'fr'],
        'linkedin': ['li_fat_id', 'lidc', 'bcookie', 'UserMatchHistory'],
        'tiktok': ['_ttp', '_tt_enable_cookie'],
        'hotjar': ['_hjid', '_hjSessionUser', '_hjSession', '_hjAbsoluteSessionInProgress'],
        'intercom': ['intercom-id', 'intercom-session'],
        'hubspot': ['__hs', 'hubspotutk', '__hssrc', '__hstc'],
        'stripe': ['__stripe_mid', '__stripe_sid'],
        'cloudflare': ['__cfduid', 'cf_clearance', '__cf_bm'],
        'wordpress': ['wordpress_logged_in', 'wp-settings', 'wordpress_test_cookie'],
        'shopify': ['_shopify_s', '_shopify_y', 'cart_currency'],
        'matomo': ['_pk_id', '_pk_ses', '_pk_ref'],
    }
    
    # Known localStorage keys
    LOCAL_STORAGE_PATTERNS = {
        'google_analytics': ['_ga', 'ga_client_id'],
        'facebook': ['fb_local_storage'],
        'intercom': ['intercom.intercom-state'],
        'hotjar': ['hjViewportId', '_hjRecordingEnabled'],
        'segment': ['ajs_user_id', 'ajs_anonymous_id'],
        'amplitude': ['amplitude_id'],
    }
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialisiert den Headless Scanner
        
        Args:
            headless: Browser ohne GUI starten
            timeout: Timeout fuer Page-Load in ms
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
    
    async def start(self):
        """Startet den Browser"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright ist nicht installiert. Bitte 'pip install playwright' und 'playwright install chromium' ausfuehren.")
        
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        logger.info("Headless Browser gestartet")
    
    async def stop(self):
        """Stoppt den Browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if hasattr(self, '_playwright'):
            await self._playwright.stop()
        logger.info("Headless Browser gestoppt")
    
    async def scan_website(self, url: str, wait_time: int = 3000) -> Dict[str, Any]:
        """
        Scannt eine Website vollstaendig
        
        Args:
            url: URL der zu scannenden Website
            wait_time: Wartezeit nach Page-Load fuer dynamische Inhalte (ms)
            
        Returns:
            Umfassendes Scan-Ergebnis mit Cookies, Storage, Requests etc.
        """
        if not self.browser:
            await self.start()
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed_url = urlparse(url)
        base_domain = parsed_url.netloc
        
        # Tracking data
        third_party_requests: List[Dict[str, Any]] = []
        blocked_resources: List[str] = []
        
        try:
            # Create new context with tracking
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='de-DE',
            )
            
            page = await context.new_page()
            
            # Track network requests
            async def handle_request(request):
                request_url = request.url
                request_domain = urlparse(request_url).netloc
                
                # Check if third-party
                if request_domain and request_domain != base_domain:
                    category = self._categorize_domain(request_domain)
                    third_party_requests.append({
                        'url': request_url[:500],  # Truncate long URLs
                        'domain': request_domain,
                        'category': category,
                        'resource_type': request.resource_type,
                        'method': request.method,
                    })
            
            page.on('request', handle_request)
            
            # Navigate to page
            try:
                response = await page.goto(url, wait_until='networkidle', timeout=self.timeout)
                status_code = response.status if response else 0
            except Exception as e:
                logger.warning(f"Navigation error: {e}")
                status_code = 0
            
            # Wait for dynamic content
            await asyncio.sleep(wait_time / 1000)
            
            # Collect all data
            cookies = await self._get_cookies(context)
            local_storage = await self._get_local_storage(page)
            session_storage = await self._get_session_storage(page)
            scripts = await self._get_scripts(page)
            iframes = await self._get_iframes(page)
            
            # Analyze and categorize
            detected_services = self._detect_services(
                cookies, 
                local_storage, 
                session_storage, 
                third_party_requests,
                scripts,
                iframes
            )
            
            # Build result
            result = {
                'url': url,
                'status_code': status_code,
                'scan_timestamp': datetime.now().isoformat(),
                'scan_method': 'headless_browser',
                
                # Detected services
                'detected_services': list(detected_services['services']),
                'confidence': detected_services['confidence'],
                'service_details': detected_services['details'],
                
                # Cookies
                'cookies': {
                    'total': len(cookies),
                    'first_party': len([c for c in cookies if self._is_first_party(c, base_domain)]),
                    'third_party': len([c for c in cookies if not self._is_first_party(c, base_domain)]),
                    'items': cookies[:50],  # Limit
                },
                
                # Local Storage
                'local_storage': {
                    'total': len(local_storage),
                    'items': local_storage[:30],  # Limit
                    'detected_trackers': self._detect_storage_trackers(local_storage, 'local'),
                },
                
                # Session Storage
                'session_storage': {
                    'total': len(session_storage),
                    'items': session_storage[:30],  # Limit
                    'detected_trackers': self._detect_storage_trackers(session_storage, 'session'),
                },
                
                # Third-Party Requests
                'third_party_requests': {
                    'total': len(third_party_requests),
                    'by_category': self._group_requests_by_category(third_party_requests),
                    'unique_domains': list(set(r['domain'] for r in third_party_requests))[:50],
                },
                
                # Scripts & Iframes
                'scripts': scripts[:30],
                'iframes': iframes[:20],
                
                # Summary
                'summary': {
                    'has_analytics': 'analytics' in detected_services['categories'],
                    'has_marketing': 'marketing' in detected_services['categories'],
                    'has_functional': 'functional' in detected_services['categories'],
                    'requires_consent': len(detected_services['services']) > 0,
                    'risk_level': self._calculate_risk_level(detected_services),
                }
            }
            
            await context.close()
            return result
            
        except Exception as e:
            logger.error(f"Scan error for {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'scan_timestamp': datetime.now().isoformat(),
                'scan_method': 'headless_browser',
                'detected_services': [],
                'confidence': {},
            }
    
    async def _get_cookies(self, context: BrowserContext) -> List[Dict[str, Any]]:
        """Extrahiert alle Cookies"""
        try:
            cookies = await context.cookies()
            return [
                {
                    'name': c['name'],
                    'domain': c['domain'],
                    'path': c['path'],
                    'expires': c.get('expires', -1),
                    'httpOnly': c.get('httpOnly', False),
                    'secure': c.get('secure', False),
                    'sameSite': c.get('sameSite', 'None'),
                    'value_length': len(c.get('value', '')),
                    'category': self._categorize_cookie(c['name']),
                }
                for c in cookies
            ]
        except Exception as e:
            logger.error(f"Error getting cookies: {e}")
            return []
    
    async def _get_local_storage(self, page: Page) -> List[Dict[str, Any]]:
        """Extrahiert Local Storage"""
        try:
            storage = await page.evaluate("""
                () => {
                    const items = [];
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        const value = localStorage.getItem(key);
                        items.push({
                            key: key,
                            value_preview: value ? value.substring(0, 200) : null,
                            value_length: value ? value.length : 0
                        });
                    }
                    return items;
                }
            """)
            
            # Add category detection
            for item in storage:
                item['category'] = self._categorize_storage_key(item['key'])
            
            return storage
        except Exception as e:
            logger.error(f"Error getting localStorage: {e}")
            return []
    
    async def _get_session_storage(self, page: Page) -> List[Dict[str, Any]]:
        """Extrahiert Session Storage"""
        try:
            storage = await page.evaluate("""
                () => {
                    const items = [];
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        const value = sessionStorage.getItem(key);
                        items.push({
                            key: key,
                            value_preview: value ? value.substring(0, 200) : null,
                            value_length: value ? value.length : 0
                        });
                    }
                    return items;
                }
            """)
            
            # Add category detection
            for item in storage:
                item['category'] = self._categorize_storage_key(item['key'])
            
            return storage
        except Exception as e:
            logger.error(f"Error getting sessionStorage: {e}")
            return []
    
    async def _get_scripts(self, page: Page) -> List[Dict[str, Any]]:
        """Extrahiert Script-Informationen"""
        try:
            scripts = await page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('script[src]')).map(s => ({
                        src: s.src,
                        async: s.async,
                        defer: s.defer,
                        type: s.type || 'text/javascript'
                    }));
                }
            """)
            
            # Categorize scripts
            for script in scripts:
                script['category'] = self._categorize_domain(urlparse(script['src']).netloc)
            
            return scripts
        except Exception as e:
            logger.error(f"Error getting scripts: {e}")
            return []
    
    async def _get_iframes(self, page: Page) -> List[Dict[str, Any]]:
        """Extrahiert Iframe-Informationen"""
        try:
            iframes = await page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('iframe[src]')).map(f => ({
                        src: f.src,
                        width: f.width,
                        height: f.height,
                        sandbox: f.sandbox ? f.sandbox.value : null
                    }));
                }
            """)
            
            # Categorize iframes
            for iframe in iframes:
                domain = urlparse(iframe['src']).netloc
                iframe['domain'] = domain
                iframe['category'] = self._categorize_domain(domain)
                iframe['service'] = self._detect_iframe_service(iframe['src'])
            
            return iframes
        except Exception as e:
            logger.error(f"Error getting iframes: {e}")
            return []
    
    def _categorize_domain(self, domain: str) -> str:
        """Kategorisiert eine Domain"""
        if not domain:
            return 'unknown'
        
        domain_lower = domain.lower()
        
        for category, domains in self.TRACKING_DOMAINS.items():
            for pattern in domains:
                if pattern in domain_lower:
                    return category
        
        return 'other'
    
    def _categorize_cookie(self, cookie_name: str) -> str:
        """Kategorisiert einen Cookie nach Namen"""
        cookie_lower = cookie_name.lower()
        
        for service, patterns in self.COOKIE_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in cookie_lower:
                    # Map service to category
                    if service in ['google_analytics', 'hotjar', 'matomo']:
                        return 'analytics'
                    elif service in ['google_ads', 'facebook', 'linkedin', 'tiktok']:
                        return 'marketing'
                    elif service in ['intercom', 'hubspot']:
                        return 'functional'
                    elif service in ['stripe', 'shopify', 'wordpress']:
                        return 'necessary'
                    else:
                        return 'functional'
        
        # Check common patterns
        if any(p in cookie_lower for p in ['session', 'csrf', 'token', 'auth']):
            return 'necessary'
        elif any(p in cookie_lower for p in ['_ga', 'analytics', 'stat']):
            return 'analytics'
        elif any(p in cookie_lower for p in ['_fb', 'ad', 'marketing', 'track']):
            return 'marketing'
        elif any(p in cookie_lower for p in ['pref', 'lang', 'theme']):
            return 'functional'
        
        return 'unknown'
    
    def _categorize_storage_key(self, key: str) -> str:
        """Kategorisiert einen Storage-Key"""
        key_lower = key.lower()
        
        for service, patterns in self.LOCAL_STORAGE_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in key_lower:
                    if service in ['google_analytics', 'hotjar', 'amplitude', 'segment']:
                        return 'analytics'
                    elif service in ['facebook']:
                        return 'marketing'
                    else:
                        return 'functional'
        
        if any(p in key_lower for p in ['ga', 'analytics', 'track', 'stat']):
            return 'analytics'
        elif any(p in key_lower for p in ['fb', 'ad', 'marketing']):
            return 'marketing'
        elif any(p in key_lower for p in ['user', 'auth', 'token', 'session']):
            return 'necessary'
        elif any(p in key_lower for p in ['pref', 'setting', 'theme', 'lang']):
            return 'functional'
        
        return 'unknown'
    
    def _is_first_party(self, cookie: Dict, base_domain: str) -> bool:
        """Prueft ob Cookie First-Party ist"""
        cookie_domain = cookie.get('domain', '').lstrip('.')
        return base_domain.endswith(cookie_domain) or cookie_domain.endswith(base_domain)
    
    def _detect_services(
        self, 
        cookies: List[Dict],
        local_storage: List[Dict],
        session_storage: List[Dict],
        requests: List[Dict],
        scripts: List[Dict],
        iframes: List[Dict]
    ) -> Dict[str, Any]:
        """Erkennt Services aus allen gesammelten Daten"""
        
        detected_services: Set[str] = set()
        confidence: Dict[str, float] = {}
        details: Dict[str, Dict] = {}
        categories: Set[str] = set()
        
        # Check cookies
        for cookie in cookies:
            for service, patterns in self.COOKIE_PATTERNS.items():
                for pattern in patterns:
                    if pattern.lower() in cookie['name'].lower():
                        detected_services.add(service)
                        confidence[service] = max(confidence.get(service, 0), 0.9)
                        if service not in details:
                            details[service] = {'evidence': [], 'category': self._get_service_category(service)}
                        details[service]['evidence'].append(f"Cookie: {cookie['name']}")
                        categories.add(self._get_service_category(service))
        
        # Check requests
        request_domains = set(r['domain'] for r in requests)
        domain_to_service = {
            'google-analytics.com': 'google_analytics',
            'googletagmanager.com': 'google_tag_manager',
            'facebook.net': 'facebook_pixel',
            'connect.facebook.net': 'facebook_pixel',
            'snap.licdn.com': 'linkedin_insight',
            'analytics.tiktok.com': 'tiktok_pixel',
            'static.hotjar.com': 'hotjar',
            'widget.intercom.io': 'intercom',
            'youtube.com': 'youtube',
            'player.vimeo.com': 'vimeo',
            'maps.googleapis.com': 'google_maps',
        }
        
        for domain in request_domains:
            for pattern, service in domain_to_service.items():
                if pattern in domain:
                    detected_services.add(service)
                    confidence[service] = max(confidence.get(service, 0), 0.95)
                    if service not in details:
                        details[service] = {'evidence': [], 'category': self._get_service_category(service)}
                    details[service]['evidence'].append(f"Request: {domain}")
                    categories.add(self._get_service_category(service))
        
        # Check iframes
        for iframe in iframes:
            if iframe.get('service'):
                detected_services.add(iframe['service'])
                confidence[iframe['service']] = max(confidence.get(iframe['service'], 0), 0.95)
                if iframe['service'] not in details:
                    details[iframe['service']] = {'evidence': [], 'category': self._get_service_category(iframe['service'])}
                details[iframe['service']]['evidence'].append(f"Iframe: {iframe.get('domain', 'unknown')}")
                categories.add(self._get_service_category(iframe['service']))
        
        return {
            'services': detected_services,
            'confidence': confidence,
            'details': details,
            'categories': categories,
        }
    
    def _get_service_category(self, service: str) -> str:
        """Gibt die Kategorie eines Services zurueck"""
        analytics = ['google_analytics', 'google_tag_manager', 'matomo', 'hotjar', 'plausible', 'amplitude', 'segment', 'mixpanel']
        marketing = ['facebook_pixel', 'google_ads', 'linkedin_insight', 'tiktok_pixel', 'twitter_x', 'pinterest', 'criteo']
        functional = ['intercom', 'zendesk', 'crisp', 'tawk', 'hubspot']
        media = ['youtube', 'vimeo', 'instagram', 'spotify']
        
        if service in analytics:
            return 'analytics'
        elif service in marketing:
            return 'marketing'
        elif service in functional:
            return 'functional'
        elif service in media:
            return 'marketing'  # Media meist mit Tracking
        
        return 'functional'
    
    def _detect_iframe_service(self, src: str) -> Optional[str]:
        """Erkennt Service aus Iframe-URL"""
        src_lower = src.lower()
        
        patterns = {
            'youtube': ['youtube.com/embed', 'youtube-nocookie.com/embed'],
            'vimeo': ['player.vimeo.com/video'],
            'google_maps': ['google.com/maps/embed', 'maps.google.com'],
            'spotify': ['open.spotify.com/embed'],
            'soundcloud': ['soundcloud.com/player'],
            'instagram': ['instagram.com/p/'],
            'twitter_x': ['twitter.com/intent', 'platform.twitter.com'],
            'facebook_plugin': ['facebook.com/plugins'],
        }
        
        for service, patterns_list in patterns.items():
            for pattern in patterns_list:
                if pattern in src_lower:
                    return service
        
        return None
    
    def _detect_storage_trackers(self, storage: List[Dict], storage_type: str) -> List[Dict]:
        """Erkennt Tracker in Storage"""
        trackers = []
        
        for item in storage:
            if item.get('category') in ['analytics', 'marketing']:
                trackers.append({
                    'key': item['key'],
                    'category': item['category'],
                    'storage_type': storage_type,
                })
        
        return trackers
    
    def _group_requests_by_category(self, requests: List[Dict]) -> Dict[str, int]:
        """Gruppiert Requests nach Kategorie"""
        grouped = {}
        for req in requests:
            cat = req.get('category', 'other')
            grouped[cat] = grouped.get(cat, 0) + 1
        return grouped
    
    def _calculate_risk_level(self, detected: Dict) -> str:
        """Berechnet Risiko-Level basierend auf erkannten Services"""
        marketing_count = len([s for s in detected['services'] if self._get_service_category(s) == 'marketing'])
        analytics_count = len([s for s in detected['services'] if self._get_service_category(s) == 'analytics'])
        
        if marketing_count >= 3:
            return 'high'
        elif marketing_count >= 1 or analytics_count >= 2:
            return 'medium'
        elif analytics_count >= 1:
            return 'low'
        
        return 'minimal'


# Singleton instance for reuse
headless_scanner: Optional[HeadlessCookieScanner] = None

async def get_headless_scanner() -> HeadlessCookieScanner:
    """Gibt eine Singleton-Instanz des Scanners zurueck"""
    global headless_scanner
    if headless_scanner is None:
        headless_scanner = HeadlessCookieScanner()
        await headless_scanner.start()
    return headless_scanner


async def scan_website_headless(url: str) -> Dict[str, Any]:
    """
    Convenience-Funktion fuer einzelne Scans
    
    Nutzt den Singleton-Scanner fuer bessere Performance
    """
    scanner = await get_headless_scanner()
    return await scanner.scan_website(url)

