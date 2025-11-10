"""
Screenshot-Service für Barrierefreiheits-Prüfung
Crawlt Bilder mit Playwright und erstellt visuelle Screenshots
"""

import asyncio
import base64
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import logging
from playwright.async_api import async_playwright, Browser, Page
import re

logger = logging.getLogger(__name__)


class ScreenshotService:
    """Service zum Crawlen und Screenshot von Bildern für Accessibility-Checks"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.max_images = 50  # Limit für Performance
        
    async def __aenter__(self):
        """Context Manager Entry - initialisiert Browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit - schließt Browser"""
        if self.browser:
            await self.browser.close()
    
    async def capture_images(self, url: str) -> List[Dict[str, Any]]:
        """
        Crawlt Seite mit Playwright und erstellt Screenshots
        aller Bilder mit Accessibility-Problemen
        
        Args:
            url: URL der zu scannenden Seite
            
        Returns:
            Liste mit Bild-Daten inkl. Screenshots und AI-Vorschlägen
        """
        try:
            logger.info(f"🖼️  Capturing images from {url}")
            
            if not self.browser:
                raise RuntimeError("Browser not initialized. Use async context manager.")
            
            page = await self.browser.new_page()
            
            # Setze viewport für konsistente Screenshots
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Navigate zur Seite
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
            except Exception as e:
                logger.warning(f"Navigation timeout/error: {e}, continuing anyway")
                await asyncio.sleep(2)  # Warte kurz
            
            # Finde alle Bilder
            images = await page.query_selector_all('img')
            logger.info(f"Found {len(images)} images on page")
            
            image_data = []
            
            # Limitiere Anzahl für Performance
            images_to_process = images[:self.max_images]
            
            for idx, img in enumerate(images_to_process):
                try:
                    img_info = await self._process_image(img, idx, url, page)
                    if img_info:
                        image_data.append(img_info)
                except Exception as e:
                    logger.warning(f"Failed to process image {idx}: {e}")
                    continue
            
            await page.close()
            
            logger.info(f"✅ Captured {len(image_data)} images successfully")
            return image_data
            
        except Exception as e:
            logger.error(f"❌ Screenshot capture failed: {e}")
            return []
    
    async def _process_image(
        self, 
        img, 
        idx: int, 
        base_url: str, 
        page: Page
    ) -> Optional[Dict[str, Any]]:
        """
        Verarbeitet ein einzelnes Bild
        
        Returns:
            Dict mit Bild-Informationen oder None bei Fehler
        """
        try:
            # Hole Attribute
            alt = await img.get_attribute('alt')
            src = await img.get_attribute('src')
            title = await img.get_attribute('title')
            aria_label = await img.get_attribute('aria-label')
            
            if not src:
                return None
            
            # Relative URLs zu absoluten konvertieren
            absolute_src = urljoin(base_url, src)
            
            # Prüfe ob Bild sichtbar ist
            is_visible = await img.is_visible()
            
            # Hole Dimensionen
            bounding_box = await img.bounding_box()
            if not bounding_box:
                # Bild nicht im Viewport oder zu klein
                return None
            
            width = bounding_box.get('width', 0)
            height = bounding_box.get('height', 0)
            
            # Ignoriere zu kleine Bilder (Icons, Spacer)
            if width < 20 or height < 20:
                return None
            
            # Screenshot des Bildes (nur wenn sichtbar und groß genug)
            screenshot_b64 = None
            if is_visible and width >= 50 and height >= 50:
                try:
                    screenshot_bytes = await img.screenshot(timeout=5000)
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                except Exception as e:
                    logger.debug(f"Could not screenshot image {idx}: {e}")
            
            # Hole umgebenden Text für Kontext
            parent_text = await self._get_surrounding_text(img, page)
            
            # Generiere Vorschlag für Alt-Text
            suggested_alt = self._generate_alt_suggestion(
                src=absolute_src,
                context=parent_text,
                title=title,
                aria_label=aria_label
            )
            
            return {
                'id': f'img_{idx}',
                'src': absolute_src,
                'alt': alt or '',
                'title': title or '',
                'aria_label': aria_label or '',
                'has_alt': bool(alt),
                'has_title': bool(title),
                'has_aria_label': bool(aria_label),
                'screenshot': screenshot_b64,  # base64
                'screenshot_data_url': f'data:image/png;base64,{screenshot_b64}' if screenshot_b64 else None,
                'context': parent_text,
                'suggested_alt': suggested_alt,
                'width': int(width),
                'height': int(height),
                'is_visible': is_visible,
                'is_decorative': self._is_likely_decorative(src, width, height)
            }
            
        except Exception as e:
            logger.debug(f"Error processing image: {e}")
            return None
    
    async def _get_surrounding_text(self, img, page: Page) -> str:
        """
        Extrahiert umgebenden Text für Kontext-Analyse
        
        Args:
            img: Playwright Element Locator
            page: Page-Objekt
            
        Returns:
            Umgebender Text (max 200 Zeichen)
        """
        try:
            # Versuche verschiedene Strategien für Kontext
            
            # 1. Text im Parent-Element
            parent = await img.evaluate_handle('el => el.parentElement')
            parent_text = await parent.evaluate('el => el.textContent || ""')
            
            if parent_text and len(parent_text.strip()) > 10:
                return parent_text.strip()[:200]
            
            # 2. Figure/Caption
            figure = await img.evaluate_handle(
                'el => el.closest("figure")'
            )
            if figure:
                caption = await figure.evaluate(
                    'el => el.querySelector("figcaption")?.textContent || ""'
                )
                if caption:
                    return caption.strip()[:200]
            
            # 3. Benachbarte Überschriften
            heading = await page.evaluate('''
                (img) => {
                    let el = img;
                    while (el && el.parentElement) {
                        el = el.parentElement;
                        const heading = el.querySelector('h1, h2, h3, h4, h5, h6');
                        if (heading) return heading.textContent;
                    }
                    return '';
                }
            ''', img)
            
            if heading:
                return heading.strip()[:200]
            
            return ""
            
        except Exception as e:
            logger.debug(f"Could not extract surrounding text: {e}")
            return ""
    
    def _generate_alt_suggestion(
        self, 
        src: str, 
        context: str, 
        title: Optional[str] = None,
        aria_label: Optional[str] = None
    ) -> str:
        """
        Generiert Alt-Text-Vorschlag basierend auf verfügbaren Informationen
        
        Args:
            src: Bild-URL
            context: Umgebender Text
            title: Title-Attribut
            aria_label: ARIA-Label
            
        Returns:
            Vorgeschlagener Alt-Text
        """
        # Priorisierung: aria-label > title > context > filename
        
        if aria_label:
            return aria_label
        
        if title and len(title) > 3:
            return title
        
        if context and len(context) > 10:
            # Nutze ersten Satz aus Kontext
            first_sentence = context.split('.')[0].strip()
            if len(first_sentence) > 10 and len(first_sentence) < 150:
                return first_sentence
        
        # Fallback: Extrahiere aus Dateiname
        filename = self._extract_filename(src)
        cleaned = self._clean_filename(filename)
        
        if cleaned:
            return cleaned
        
        return "Bild"  # Letzter Fallback
    
    def _extract_filename(self, src: str) -> str:
        """Extrahiert Dateinamen aus URL"""
        try:
            # Entferne Query-Parameter
            src_clean = src.split('?')[0]
            # Hole letzten Teil des Pfades
            filename = src_clean.split('/')[-1]
            # Entferne Dateiendung
            name_without_ext = filename.rsplit('.', 1)[0]
            return name_without_ext
        except:
            return ""
    
    def _clean_filename(self, filename: str) -> str:
        """
        Bereinigt Dateinamen für menschenlesbaren Alt-Text
        
        Beispiel: "team-meeting-2024" -> "Team Meeting"
        """
        if not filename:
            return ""
        
        # Entferne Zahlen am Ende
        filename = re.sub(r'-?\d+$', '', filename)
        
        # Ersetze Trennzeichen durch Leerzeichen
        filename = re.sub(r'[-_]', ' ', filename)
        
        # Capitalize words
        words = filename.split()
        cleaned_words = [w.capitalize() for w in words if len(w) > 1]
        
        result = ' '.join(cleaned_words)
        
        # Validierung: Mindestens 2 Zeichen
        if len(result) < 2:
            return ""
        
        return result
    
    def _is_likely_decorative(self, src: str, width: int, height: int) -> bool:
        """
        Prüft ob Bild wahrscheinlich dekorativ ist (sollte alt="" haben)
        
        Args:
            src: Bild-URL
            width: Breite in px
            height: Höhe in px
            
        Returns:
            True wenn wahrscheinlich dekorativ
        """
        # Kleine Bilder sind oft dekorativ
        if width < 50 or height < 50:
            return True
        
        # Icons, Spacer, etc.
        decorative_patterns = [
            r'icon',
            r'spacer',
            r'divider',
            r'separator',
            r'bullet',
            r'arrow',
            r'decoration',
            r'bg[-_]',
            r'background',
        ]
        
        src_lower = src.lower()
        for pattern in decorative_patterns:
            if re.search(pattern, src_lower):
                return True
        
        return False


# Convenience-Funktion für einfache Nutzung
async def capture_page_images(url: str) -> List[Dict[str, Any]]:
    """
    Convenience-Funktion zum Screenshot-Capture
    
    Usage:
        images = await capture_page_images('https://example.com')
    """
    async with ScreenshotService() as service:
        return await service.capture_images(url)

