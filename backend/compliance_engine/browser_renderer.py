"""
Browser-Rendering Service für moderne JavaScript-Websites
Nutzt Playwright für präzises Rendering von Client-Side-Websites

Zweck:
- Erkennt Client-Side-gerenderte Websites (React, Vue, Angular, etc.)
- Rendert diese vollständig im Browser
- Gibt vollständig gerendertes HTML zurück für präzise Compliance-Checks

© 2025 Complyo.tech
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Tuple
from playwright.async_api import async_playwright, Browser, Page
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_browser_semaphore = asyncio.Semaphore(3)


class BrowserRenderer:
    """
    Service für Browser-basiertes Rendering
    
    Verwendet Playwright Chromium für vollständiges JavaScript-Rendering
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        
    async def __aenter__(self):
        """Context Manager Entry - initialisiert Browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',  # Docker-Kompatibilität
                '--disable-gpu'
            ]
        )
        logger.info("✅ Browser initialized")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit - schließt Browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("🔒 Browser closed")
    
    async def render_page(self, url: str, wait_for: str = 'networkidle', timeout: int = 30000) -> Dict[str, Any]:
        """
        Rendert Seite vollständig im Browser
        
        Args:
            url: URL der zu rendernden Seite
            wait_for: Warte-Strategie ('load', 'domcontentloaded', 'networkidle')
            timeout: Timeout in ms
            
        Returns:
            Dict mit:
                - html: Vollständig gerendertes HTML
                - success: Ob erfolgreich
                - rendering_type: 'client' oder 'server'
                - metadata: Zusätzliche Infos
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use async context manager.")

        async with _browser_semaphore:
            page = None
            try:
                logger.info(f"🌐 Rendering page: {url}")

                page = await self.browser.new_page()

                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Complyo-Scanner/2.0'
                })

                start_time = asyncio.get_event_loop().time()

                try:
                    response = await page.goto(url, wait_until=wait_for, timeout=timeout)

                    if not response:
                        return self._create_error_response(url, "No response from server")

                    await asyncio.sleep(2)

                    try:
                        await page.wait_for_selector('#root, #app, [data-reactroot], main, header', timeout=5000)
                    except:
                        pass

                except Exception as e:
                    logger.warning(f"Navigation timeout/error: {e}, trying to get content anyway")
                    await asyncio.sleep(3)

                html = await page.content()

                end_time = asyncio.get_event_loop().time()
                render_time = round((end_time - start_time) * 1000, 2)

                rendering_info = await self._analyze_rendering(page, html)

                metadata = {
                    'url': url,
                    'render_time_ms': render_time,
                    'status_code': response.status if response else None,
                    'final_url': page.url,
                    'title': await page.title(),
                    **rendering_info
                }

                logger.info(f"✅ Rendered successfully in {render_time}ms ({rendering_info['rendering_type']})")

                return {
                    'html': html,
                    'success': True,
                    'rendering_type': rendering_info['rendering_type'],
                    'metadata': metadata
                }

            except Exception as e:
                logger.error(f"❌ Browser rendering failed for {url}: {e}")
                return self._create_error_response(url, str(e))

            finally:
                if page:
                    await page.close()
    
    async def _analyze_rendering(self, page: Page, html: str) -> Dict[str, Any]:
        """
        Analysiert wie die Seite gerendert wurde
        
        Returns:
            Dict mit rendering_type, framework, indicators
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Framework-Detection
        framework = None
        indicators = []
        
        # React
        if soup.find(attrs={'data-reactroot': True}) or soup.find(id='root'):
            framework = 'React'
            indicators.append('React root detected')
        
        # Vue
        if soup.find(attrs={'data-v-': re.compile('.*')}) or soup.find(id='app'):
            framework = 'Vue'
            indicators.append('Vue app detected')
        
        # Angular
        if soup.find(attrs={'ng-version': True}):
            framework = 'Angular'
            indicators.append('Angular detected')
        
        # Next.js
        if soup.find(id='__next') or soup.find(id='__NEXT_DATA__'):
            framework = 'Next.js'
            indicators.append('Next.js detected')
        
        # Svelte
        if 'svelte-' in html:
            framework = 'Svelte'
            indicators.append('Svelte detected')
        
        # Prüfe ob Client-Side-Rendering
        # Indikatoren: Viel JS, wenig Content im initialen HTML
        scripts = soup.find_all('script')
        has_many_scripts = len(scripts) > 5
        
        # Prüfe auf "leeres" HTML (typisch für CSR)
        main_content = soup.find('main') or soup.find('body')
        content_text = main_content.get_text(strip=True) if main_content else ''
        content_length = len(content_text)
        
        # Bestimme Rendering-Typ
        if framework and (content_length > 500 or soup.find('header') or soup.find('nav')):
            # Framework mit Content = wahrscheinlich SSR oder Hybrid
            rendering_type = 'hybrid' if has_many_scripts else 'server'
        elif framework and content_length < 200:
            # Framework mit wenig Content = CSR
            rendering_type = 'client'
        elif has_many_scripts and content_length < 300:
            # Viel JS, wenig Content = CSR
            rendering_type = 'client'
        else:
            # Alles andere = Server-rendered
            rendering_type = 'server'
        
        return {
            'rendering_type': rendering_type,
            'framework': framework,
            'indicators': indicators,
            'content_length': content_length,
            'script_count': len(scripts)
        }
    
    def _create_error_response(self, url: str, error: str) -> Dict[str, Any]:
        """Erstellt Error-Response"""
        return {
            'html': None,
            'success': False,
            'rendering_type': 'unknown',
            'metadata': {
                'url': url,
                'error': error
            }
        }


def detect_client_rendering(html: str) -> Tuple[bool, str]:
    """
    Schnelle Detection ob Seite Client-Side-Rendering benötigt
    (ohne Browser-Start)
    
    Args:
        html: Initial HTML vom Server
        
    Returns:
        Tuple[needs_browser, reason]
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Check: Bailout-Patterns (Next.js CSR)
    if 'BAILOUT_TO_CLIENT_SIDE_RENDERING' in html:
        return (True, 'Next.js client-side rendering detected')
    
    # 2. NEU: Next.js immer mit Browser (wegen Hydration-Issues)
    # Next.js kann SSR haben aber trotzdem dynamische Inhalte per Hydration laden
    if soup.find(id='__next') or soup.find(id='__NEXT_DATA__') or '__next' in html:
        return (True, 'Next.js detected - using browser for full hydration')
    
    # 3. Check: Leerer Root
    root = soup.find(id='root') or soup.find(id='app')
    if root and len(root.get_text(strip=True)) < 50:
        return (True, 'Empty root element (likely React/Vue SPA)')
    
    # 4. Check: Framework-Indikatoren ohne Content
    body = soup.find('body')
    if body:
        body_text = body.get_text(strip=True)
        
        # React/Vue/Angular ohne Content
        if len(body_text) < 200:
            if soup.find(attrs={'data-reactroot': True}):
                return (True, 'React without server-rendered content')
            if soup.find(id='app') and not soup.find('main'):
                return (True, 'Vue SPA detected')
            if soup.find(attrs={'ng-version': True}):
                return (True, 'Angular SPA detected')
    
    # 5. Check: Kein semantisches HTML
    has_header = soup.find('header') is not None
    has_main = soup.find('main') is not None
    has_nav = soup.find('nav') is not None
    
    if not (has_header or has_main or has_nav):
        # Prüfe ob viele Scripts aber wenig Content
        scripts = soup.find_all('script')
        if len(scripts) > 8:
            return (True, 'Many scripts but no semantic HTML (likely CSR)')
    
    # 6. Check: Bekannte SPA-Builder
    if 'webpack' in html.lower() or 'vite' in html.lower():
        content_length = len(soup.get_text(strip=True))
        if content_length < 500:
            return (True, 'Webpack/Vite bundle with minimal content')
    
    # Wahrscheinlich Server-rendered
    return (False, 'Server-rendered content detected')


async def smart_fetch_html(url: str, simple_html: str = None) -> Tuple[str, Dict[str, Any]]:
    """
    Smart HTML-Fetching mit automatischer Browser-Nutzung
    
    Args:
        url: URL zum Fetchen
        simple_html: Optional bereits gefetchtes HTML (für Re-Check)
        
    Returns:
        Tuple[html, metadata]
    """
    # 1. Wenn kein simple_html gegeben, hole es erst
    if not simple_html:
        import aiohttp
        import ssl
        import certifi
        
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    simple_html = await response.text()
            except Exception as e:
                logger.warning(f"Simple fetch failed: {e}, trying browser")
                simple_html = ""
    
    # 2. Prüfe ob Browser nötig
    needs_browser, reason = detect_client_rendering(simple_html)
    
    metadata = {
        'detection_reason': reason,
        'used_browser': needs_browser
    }
    
    # 3. Wenn Browser nötig, nutze ihn
    if needs_browser:
        logger.info(f"🌐 Browser needed: {reason}")
        try:
            async with BrowserRenderer() as renderer:
                result = await renderer.render_page(url)
                
                if result['success']:
                    metadata.update(result['metadata'])
                    return result['html'], metadata
                else:
                    logger.warning(f"Browser rendering failed, using simple HTML")
                    metadata['browser_error'] = 'render_failed'
                    return simple_html, metadata
        except Exception as e:
            logger.warning(f"⚠️ Browser not available: {e}, using simple HTML fallback")
            metadata['browser_error'] = str(e)
            metadata['used_browser'] = False
            return simple_html, metadata
    
    # 4. Server-rendered, nutze simple HTML
    logger.info(f"⚡ Server-rendered, using simple fetch")
    metadata['fetch_method'] = 'simple'
    return simple_html, metadata

