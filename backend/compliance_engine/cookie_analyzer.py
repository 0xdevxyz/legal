"""
Cookie Analyzer - Analysiert und dokumentiert Cookies auf einer Website
Generiert Cookie-Consent Konfigurationen
"""

import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class CookieAnalyzer:
    """Analysiert Cookies und generiert Consent-Konfigurationen"""
    
    def __init__(self):
        self.known_cookies = self._load_known_cookies()
    
    def analyze_cookies(self, url: str, html: str = None, session=None) -> List[Dict[str, Any]]:
        """
        Analysiert welche Cookies eine Website setzt
        
        Args:
            url: Website-URL
            html: Optional - HTML-Content
            session: Optional - httpx Session mit Cookies
            
        Returns:
            Liste von Cookie-Informationen
        """
        cookies = []
        
        # Analyse basierend auf bekannten Tracking-Scripts
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            script_cookies = self._analyze_tracking_scripts(soup)
            cookies.extend(script_cookies)
        
        # Analyse von session.cookies (falls vorhanden)
        if session and hasattr(session, 'cookies'):
            session_cookies = self._analyze_session_cookies(session.cookies)
            cookies.extend(session_cookies)
        
        # Dedupliziere basierend auf Cookie-Namen
        unique_cookies = {}
        for cookie in cookies:
            name = cookie.get('name')
            if name not in unique_cookies:
                unique_cookies[name] = cookie
        
        return list(unique_cookies.values())
    
    def generate_cookie_banner_config(self, cookies: List[Dict]) -> Dict[str, Any]:
        """
        Generiert eine Cookie-Consent-Banner Konfiguration
        
        Args:
            cookies: Liste erkannter Cookies
            
        Returns:
            Config-Dict für Cookie-Banner
        """
        # Kategorisiere Cookies
        categories = {
            'necessary': [],
            'analytics': [],
            'marketing': [],
            'preferences': []
        }
        
        for cookie in cookies:
            category = cookie.get('category', 'necessary')
            categories[category].append(cookie)
        
        config = {
            'banner_text': self._generate_banner_text(len(cookies)),
            'categories': self._generate_category_config(categories),
            'cookies': cookies,
            'privacy_policy_url': '/datenschutz',
            'version': '1.0'
        }
        
        return config
    
    def get_cookie_descriptions(self, cookie_name: str) -> Dict[str, str]:
        """
        Holt rechtssichere Beschreibungen für einen Cookie
        
        Args:
            cookie_name: Name des Cookies
            
        Returns:
            Dict mit description, purpose, duration, legal_basis
        """
        return self.known_cookies.get(cookie_name, {
            'description': f'Cookie: {cookie_name}',
            'purpose': 'Keine Informationen verfügbar',
            'duration': 'Unbekannt',
            'legal_basis': 'Art. 6 Abs. 1 lit. a DSGVO'
        })
    
    # ==================== Private Methoden ====================
    
    def _analyze_tracking_scripts(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Erkennt Tracking-Scripts und deren Cookies"""
        cookies = []
        
        # Google Analytics
        if self._has_google_analytics(soup):
            cookies.append({
                'name': '_ga',
                'category': 'analytics',
                'provider': 'Google Analytics',
                'description': 'Google Analytics Cookie zur Unterscheidung von Benutzern',
                'duration': '2 Jahre',
                'required': False
            })
            cookies.append({
                'name': '_gid',
                'category': 'analytics',
                'provider': 'Google Analytics',
                'description': 'Google Analytics Cookie zur Unterscheidung von Benutzern',
                'duration': '24 Stunden',
                'required': False
            })
        
        # Google Tag Manager
        if self._has_google_tag_manager(soup):
            cookies.append({
                'name': '_gat',
                'category': 'analytics',
                'provider': 'Google Tag Manager',
                'description': 'Wird von Google Analytics verwendet, um die Anforderungsrate zu drosseln',
                'duration': '1 Minute',
                'required': False
            })
        
        # Facebook Pixel
        if self._has_facebook_pixel(soup):
            cookies.append({
                'name': '_fbp',
                'category': 'marketing',
                'provider': 'Facebook',
                'description': 'Facebook Pixel Cookie für Conversion-Tracking',
                'duration': '3 Monate',
                'required': False
            })
        
        # Meta Pixel (Instagram)
        if self._has_meta_pixel(soup):
            cookies.append({
                'name': '_fbc',
                'category': 'marketing',
                'provider': 'Meta',
                'description': 'Meta Cookie für Werbe-Tracking',
                'duration': '2 Jahre',
                'required': False
            })
        
        return cookies
    
    def _analyze_session_cookies(self, cookies) -> List[Dict[str, Any]]:
        """Analysiert Cookies aus einer Session"""
        analyzed = []
        
        for cookie in cookies:
            name = cookie.name if hasattr(cookie, 'name') else str(cookie)
            
            # Bestimme Kategorie basierend auf Cookie-Namen
            category = self._determine_cookie_category(name)
            
            analyzed.append({
                'name': name,
                'category': category,
                'provider': 'Website',
                'description': self.known_cookies.get(name, {}).get('description', f'Cookie: {name}'),
                'duration': 'Session',
                'required': category == 'necessary'
            })
        
        return analyzed
    
    def _determine_cookie_category(self, cookie_name: str) -> str:
        """Bestimmt die Kategorie eines Cookies basierend auf dem Namen"""
        name_lower = cookie_name.lower()
        
        # Analytics
        if any(x in name_lower for x in ['_ga', '_gid', '_gat', 'analytics']):
            return 'analytics'
        
        # Marketing
        if any(x in name_lower for x in ['_fb', 'pixel', 'ads', 'marketing']):
            return 'marketing'
        
        # Session/Notwendig
        if any(x in name_lower for x in ['session', 'csrf', 'xsrf', 'auth']):
            return 'necessary'
        
        # Preferences
        if any(x in name_lower for x in ['lang', 'theme', 'pref']):
            return 'preferences'
        
        return 'necessary'  # Default
    
    def _has_google_analytics(self, soup: BeautifulSoup) -> bool:
        """Prüft ob Google Analytics eingebunden ist"""
        scripts = soup.find_all('script', src=True)
        return any('google-analytics.com' in script.get('src', '') for script in scripts)
    
    def _has_google_tag_manager(self, soup: BeautifulSoup) -> bool:
        """Prüft ob Google Tag Manager eingebunden ist"""
        scripts = soup.find_all('script', src=True)
        return any('googletagmanager.com' in script.get('src', '') for script in scripts)
    
    def _has_facebook_pixel(self, soup: BeautifulSoup) -> bool:
        """Prüft ob Facebook Pixel eingebunden ist"""
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'fbq(' in script.string:
                return True
        return False
    
    def _has_meta_pixel(self, soup: BeautifulSoup) -> bool:
        """Prüft ob Meta Pixel eingebunden ist"""
        scripts = soup.find_all('script', src=True)
        return any('connect.facebook.net' in script.get('src', '') for script in scripts)
    
    def _generate_banner_text(self, cookie_count: int) -> str:
        """Generiert Banner-Text basierend auf Cookie-Anzahl"""
        if cookie_count == 0:
            return "Diese Website verwendet keine Tracking-Cookies."
        elif cookie_count <= 3:
            return f"Diese Website verwendet {cookie_count} Cookies, um Ihnen die bestmögliche Nutzererfahrung zu bieten."
        else:
            return f"Diese Website verwendet {cookie_count} verschiedene Cookies. Einige davon sind notwendig, andere helfen uns, die Nutzung zu verstehen."
    
    def _generate_category_config(self, categories: Dict[str, List]) -> List[Dict[str, Any]]:
        """Generiert Kategorie-Konfiguration für Banner"""
        config = []
        
        category_info = {
            'necessary': {
                'name': 'Notwendig',
                'description': 'Erforderlich für die Grundfunktionen der Website',
                'required': True
            },
            'analytics': {
                'name': 'Analyse',
                'description': 'Helfen uns, die Nutzung der Website zu verstehen',
                'required': False
            },
            'marketing': {
                'name': 'Marketing',
                'description': 'Werden für Werbezwecke verwendet',
                'required': False
            },
            'preferences': {
                'name': 'Präferenzen',
                'description': 'Speichern Ihre persönlichen Einstellungen',
                'required': False
            }
        }
        
        for cat_key, cookies in categories.items():
            if cookies:  # Nur Kategorien mit Cookies hinzufügen
                info = category_info.get(cat_key, {})
                config.append({
                    'key': cat_key,
                    'name': info.get('name', cat_key.title()),
                    'description': info.get('description', ''),
                    'required': info.get('required', False),
                    'cookie_count': len(cookies)
                })
        
        return config
    
    def _load_known_cookies(self) -> Dict[str, Dict]:
        """Lädt bekannte Cookie-Definitionen"""
        return {
            '_ga': {
                'description': 'Google Analytics Cookie zur Unterscheidung von Benutzern',
                'purpose': 'Nutzeridentifikation für Statistiken',
                'duration': '2 Jahre',
                'legal_basis': 'Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)'
            },
            '_gid': {
                'description': 'Google Analytics Cookie zur Unterscheidung von Benutzern',
                'purpose': 'Nutzeridentifikation für Statistiken',
                'duration': '24 Stunden',
                'legal_basis': 'Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)'
            },
            '_gat': {
                'description': 'Google Analytics Cookie zur Drosselung der Anforderungsrate',
                'purpose': 'Rate-Limiting',
                'duration': '1 Minute',
                'legal_basis': 'Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)'
            },
            '_fbp': {
                'description': 'Facebook Pixel Cookie',
                'purpose': 'Conversion-Tracking für Facebook-Werbung',
                'duration': '3 Monate',
                'legal_basis': 'Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)'
            },
            'PHPSESSID': {
                'description': 'PHP Session Cookie',
                'purpose': 'Erhält die Benutzersitzung aufrecht',
                'duration': 'Session',
                'legal_basis': 'Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse)'
            },
            'cookieconsent_status': {
                'description': 'Cookie-Consent Status',
                'purpose': 'Speichert die Cookie-Einwilligung',
                'duration': '1 Jahr',
                'legal_basis': 'Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse)'
            }
        }

# Global Instance
cookie_analyzer = CookieAnalyzer()

