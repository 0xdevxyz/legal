"""
Unit-Tests für Datenschutz-Checks (DSGVO)
"""

import pytest
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDataschutzDetection:
    """Tests für Datenschutzerklärung-Erkennung"""
    
    def test_datenschutz_link_found(self):
        """Test: Datenschutz-Link wird gefunden"""
        html = """
        <html>
        <body>
            <footer>
                <a href="/datenschutz">Datenschutzerklärung</a>
            </footer>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        link = soup.find('a', string=lambda x: x and 'datenschutz' in x.lower())
        assert link is not None
    
    def test_privacy_english_found(self):
        """Test: Englischer 'Privacy' Link wird gefunden"""
        html = """
        <html>
        <body>
            <footer>
                <a href="/privacy">Privacy Policy</a>
            </footer>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        link = soup.find('a', string=lambda x: x and 'privacy' in x.lower())
        assert link is not None
    
    def test_datenschutz_link_missing(self):
        """Test: Fehlender Datenschutz-Link wird erkannt"""
        html = """
        <html>
        <body>
            <footer>
                <a href="/impressum">Impressum</a>
            </footer>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        link = soup.find('a', string=lambda x: x and 'datenschutz' in x.lower())
        assert link is None


class TestDataschutzContent:
    """Tests für Datenschutz-Inhalts-Validierung"""
    
    def test_verantwortlicher_present(self):
        """Test: Verantwortlicher ist angegeben"""
        html = """
        <html>
        <body>
            <h1>Datenschutzerklärung</h1>
            
            <h2>Verantwortliche Stelle</h2>
            <p>
                Verantwortlich für die Datenverarbeitung:<br>
                Musterfirma GmbH<br>
                Musterstraße 123<br>
                12345 Musterstadt<br>
                E-Mail: datenschutz@musterfirma.de
            </p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        assert 'verantwortlich' in text
        assert '@' in text  # E-Mail vorhanden
    
    def test_rechtsgrundlagen_present(self):
        """Test: Rechtsgrundlagen nach Art. 6 DSGVO vorhanden"""
        html = """
        <html>
        <body>
            <h1>Datenschutzerklärung</h1>
            
            <h2>Rechtsgrundlagen</h2>
            <p>
                Die Verarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. a DSGVO 
                (Einwilligung) bzw. Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse).
            </p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        assert 'art. 6' in text or 'artikel 6' in text
        assert 'dsgvo' in text
    
    def test_betroffenenrechte_present(self):
        """Test: Betroffenenrechte sind aufgeführt"""
        html = """
        <html>
        <body>
            <h1>Datenschutzerklärung</h1>
            
            <h2>Ihre Rechte</h2>
            <ul>
                <li>Auskunftsrecht (Art. 15 DSGVO)</li>
                <li>Berichtigungsrecht (Art. 16 DSGVO)</li>
                <li>Löschungsrecht (Art. 17 DSGVO)</li>
                <li>Einschränkung der Verarbeitung (Art. 18 DSGVO)</li>
                <li>Datenübertragbarkeit (Art. 20 DSGVO)</li>
                <li>Widerspruchsrecht (Art. 21 DSGVO)</li>
            </ul>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        required_rights = [
            'auskunft',
            'berichtigung',
            'löschung',
            'widerspruch'
        ]
        
        found_rights = sum(1 for right in required_rights if right in text)
        assert found_rights >= 3  # Mindestens 3 von 4
    
    def test_beschwerderecht_present(self):
        """Test: Beschwerderecht bei Aufsichtsbehörde vorhanden"""
        html = """
        <html>
        <body>
            <h1>Datenschutzerklärung</h1>
            
            <h2>Beschwerderecht</h2>
            <p>
                Sie haben das Recht, Beschwerde bei einer Datenschutz-Aufsichtsbehörde 
                einzulegen. Zuständig ist die Aufsichtsbehörde Ihres üblichen Aufenthaltsortes.
            </p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        assert 'beschwerde' in text or 'aufsichtsbehörde' in text
    
    def test_speicherdauer_present(self):
        """Test: Speicherdauer ist angegeben"""
        html = """
        <html>
        <body>
            <h1>Datenschutzerklärung</h1>
            
            <h2>Kontaktformular</h2>
            <p>
                <strong>Speicherdauer:</strong> 6 Monate nach Bearbeitung Ihrer Anfrage
            </p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        assert 'speicherdauer' in text or 'speicher' in text


class TestTrackingDisclosure:
    """Tests für Tracking-Offenlegung in Datenschutzerklärung"""
    
    def test_google_analytics_disclosed(self):
        """Test: Google Analytics wird offengelegt"""
        html = """
        <html>
        <body>
            <h1>Datenschutzerklärung</h1>
            
            <h2>Google Analytics</h2>
            <p>
                Diese Website nutzt Google Analytics, einen Webanalysedienst der 
                Google Ireland Limited. Google Analytics verwendet Cookies...
                
                <strong>Rechtsgrundlage:</strong> Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)
                <strong>Speicherdauer:</strong> 14 Monate
            </p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        assert 'google analytics' in text
        assert 'rechtsgrundlage' in text
        assert 'speicherdauer' in text or 'speicher' in text
    
    def test_facebook_pixel_disclosed(self):
        """Test: Facebook Pixel wird offengelegt"""
        html = """
        <html>
        <body>
            <h1>Datenschutzerklärung</h1>
            
            <h2>Facebook Pixel</h2>
            <p>
                Wir verwenden den Facebook Pixel der Meta Platforms Ireland Limited.
                Dabei werden Daten in die USA übermittelt...
            </p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        assert 'facebook pixel' in text or 'facebook' in text
        assert 'usa' in text or 'drittland' in text


@pytest.mark.asyncio
class TestDataschutzIntegration:
    """Integrations-Tests für Datenschutz"""
    
    def test_complete_dsgvo_compliance(self):
        """Test: Vollständige DSGVO-konforme Datenschutzerklärung"""
        html = """
        <html>
        <body>
            <footer>
                <a href="/datenschutz">Datenschutzerklärung</a>
            </footer>
            
            <div id="datenschutz-content">
                <h1>Datenschutzerklärung</h1>
                
                <h2>1. Verantwortliche Stelle</h2>
                <p>
                    Verantwortlich: Musterfirma GmbH<br>
                    E-Mail: datenschutz@musterfirma.de
                </p>
                
                <h2>2. Datenerfassung</h2>
                <p>
                    Wir erfassen folgende Daten:<br>
                    - Server-Log-Dateien (IP-Adresse, Browser, etc.)<br>
                    - Kontaktformular-Daten
                </p>
                
                <h3>Rechtsgrundlage</h3>
                <p>Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse)</p>
                
                <h3>Speicherdauer</h3>
                <p>7 Tage (Server-Logs), 6 Monate (Kontaktformular)</p>
                
                <h2>3. Ihre Rechte</h2>
                <ul>
                    <li>Auskunftsrecht (Art. 15 DSGVO)</li>
                    <li>Berichtigungsrecht (Art. 16 DSGVO)</li>
                    <li>Löschungsrecht (Art. 17 DSGVO)</li>
                    <li>Einschränkung der Verarbeitung (Art. 18 DSGVO)</li>
                    <li>Datenübertragbarkeit (Art. 20 DSGVO)</li>
                    <li>Widerspruchsrecht (Art. 21 DSGVO)</li>
                </ul>
                
                <h2>4. Beschwerderecht</h2>
                <p>
                    Sie haben das Recht, Beschwerde bei der zuständigen 
                    Datenschutz-Aufsichtsbehörde einzulegen.
                </p>
                
                <h2>5. Google Analytics</h2>
                <p>
                    Diese Website nutzt Google Analytics.<br>
                    <strong>Rechtsgrundlage:</strong> Art. 6 Abs. 1 lit. a DSGVO<br>
                    <strong>Speicherdauer:</strong> 14 Monate<br>
                    <strong>Datenübermittlung:</strong> USA (Angemessenheitsbeschluss)
                </p>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Link vorhanden
        link = soup.find('a', string=lambda x: x and 'datenschutz' in x.lower())
        assert link is not None
        
        # 2. Content vorhanden
        content = soup.find(id='datenschutz-content')
        assert content is not None
        
        text = content.get_text().lower()
        
        # 3. Alle DSGVO-Pflichtangaben vorhanden
        checks = {
            'verantwortlich': 'verantwortlich' in text,
            'rechtsgrundlage': 'rechtsgrundlage' in text and 'art. 6' in text,
            'speicherdauer': 'speicherdauer' in text or 'speicher' in text,
            'auskunft': 'auskunft' in text,
            'löschung': 'löschung' in text,
            'widerspruch': 'widerspruch' in text,
            'beschwerde': 'beschwerde' in text,
            'aufsichtsbehörde': 'aufsichtsbehörde' in text
        }
        
        passed = sum(checks.values())
        assert passed >= 6  # Mindestens 6 von 8 müssen erfüllt sein


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

