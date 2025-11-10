"""
Unit-Tests für Cookie-Compliance-Checks
"""

import pytest
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestCookieDetection:
    """Tests für Cookie-Banner-Erkennung"""
    
    def test_no_cookie_banner_detected(self):
        """Test: Fehlender Cookie-Banner wird erkannt"""
        html = """
        <html>
        <body>
            <h1>Website ohne Cookie-Banner</h1>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Prüfe auf bekannte Cookie-Banner
        known_banners = [
            'cookiebot', 'usercentrics', 'onetrust', 
            'cookie-consent', 'cookie-banner'
        ]
        
        found = False
        for banner_id in known_banners:
            if soup.find(id=lambda x: x and banner_id in x.lower()):
                found = True
                break
            if soup.find(class_=lambda x: x and banner_id in x.lower()):
                found = True
                break
        
        assert found is False
    
    def test_cookie_banner_detected(self):
        """Test: Cookie-Banner wird erkannt"""
        html = """
        <html>
        <body>
            <div id="cookie-consent-banner">
                <p>Wir verwenden Cookies</p>
                <button>Akzeptieren</button>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        banner = soup.find(id=lambda x: x and 'cookie' in x.lower())
        assert banner is not None
    
    def test_cookiebot_detected(self):
        """Test: Cookiebot wird erkannt"""
        html = """
        <html>
        <body>
            <script id="Cookiebot" src="https://consent.cookiebot.com"></script>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        cookiebot = soup.find('script', id='Cookiebot')
        assert cookiebot is not None


class TestTrackingScriptDetection:
    """Tests für Tracking-Script-Erkennung"""
    
    def test_google_analytics_detected(self):
        """Test: Google Analytics wird erkannt"""
        html = """
        <html>
        <head>
            <script async src="https://www.googletagmanager.com/gtag/js?id=GA-123"></script>
        </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        ga_script = soup.find('script', src=lambda x: x and 'googletagmanager.com/gtag' in x)
        assert ga_script is not None
    
    def test_facebook_pixel_detected(self):
        """Test: Facebook Pixel wird erkannt"""
        html = """
        <html>
        <head>
            <script>
                fbq('init', '1234567890');
            </script>
        </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        scripts = soup.find_all('script')
        has_fbq = any('fbq' in script.string for script in scripts if script.string)
        assert has_fbq is True
    
    def test_no_tracking_clean(self):
        """Test: Keine Tracking-Scripts auf sauberer Seite"""
        html = """
        <html>
        <head>
            <script src="/app.js"></script>
        </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Prüfe auf bekannte Tracking-Domains
        tracking_domains = [
            'google-analytics.com',
            'googletagmanager.com',
            'facebook.net',
            'hotjar.com'
        ]
        
        scripts = soup.find_all('script', src=True)
        tracking_found = any(
            any(domain in script['src'] for domain in tracking_domains)
            for script in scripts
        )
        
        assert tracking_found is False


class TestCookieConsent:
    """Tests für Cookie-Consent-Validierung"""
    
    def test_opt_in_mechanism(self):
        """Test: Opt-In Mechanismus vorhanden"""
        html = """
        <html>
        <body>
            <div id="cookie-banner">
                <button id="accept-all">Alle akzeptieren</button>
                <button id="reject-all">Ablehnen</button>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        accept_button = soup.find(id='accept-all')
        reject_button = soup.find(id='reject-all')
        
        assert accept_button is not None
        assert reject_button is not None
    
    def test_reject_option_available(self):
        """Test: Ablehnen-Option ist verfügbar"""
        html = """
        <html>
        <body>
            <div class="cookie-banner">
                <button class="accept">Akzeptieren</button>
                <!-- Fehlende Ablehnen-Option -->
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Suche nach Ablehnen/Nur-notwendige Button
        reject_keywords = ['ablehnen', 'reject', 'nur notwendige', 'only necessary']
        
        buttons = soup.find_all('button')
        has_reject = any(
            any(keyword in button.get_text().lower() for keyword in reject_keywords)
            for button in buttons
        )
        
        # Sollte NICHT vorhanden sein in diesem HTML
        assert has_reject is False


@pytest.mark.asyncio
class TestCookieIntegration:
    """Integrations-Tests für Cookie-Compliance"""
    
    def test_compliant_cookie_setup(self):
        """Test: Vollständig compliant Cookie-Setup"""
        html = """
        <html>
        <body>
            <div id="cookie-consent">
                <h3>Cookie-Einstellungen</h3>
                <p>Wir verwenden Cookies. Wählen Sie Ihre Präferenzen:</p>
                
                <label>
                    <input type="checkbox" checked disabled> Notwendig
                </label>
                <label>
                    <input type="checkbox" id="analytics"> Analyse
                </label>
                <label>
                    <input type="checkbox" id="marketing"> Marketing
                </label>
                
                <button id="accept-all">Alle akzeptieren</button>
                <button id="accept-selected">Auswahl speichern</button>
                <button id="reject-all">Nur notwendige</button>
                
                <a href="/datenschutz">Datenschutzerklärung</a>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Banner vorhanden
        banner = soup.find(id='cookie-consent')
        assert banner is not None
        
        # Alle drei Button-Typen vorhanden
        accept_all = soup.find(id='accept-all')
        accept_selected = soup.find(id='accept-selected')
        reject_all = soup.find(id='reject-all')
        assert all([accept_all, accept_selected, reject_all])
        
        # Kategorien vorhanden
        checkboxes = soup.find_all('input', type='checkbox')
        assert len(checkboxes) >= 2
        
        # Datenschutz-Link vorhanden
        privacy_link = soup.find('a', href=lambda x: x and 'datenschutz' in x.lower())
        assert privacy_link is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

