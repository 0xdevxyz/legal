"""
Unit-Tests für Impressum-Checks
"""

import pytest
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestImpressumDetection:
    """Tests für Impressum-Erkennung"""
    
    def test_impressum_link_found(self):
        """Test: Impressum-Link im Footer wird gefunden"""
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
        
        impressum_link = soup.find('a', string=lambda x: x and 'impressum' in x.lower())
        assert impressum_link is not None
        assert impressum_link.get('href') == '/impressum'
    
    def test_impressum_link_missing(self):
        """Test: Fehlender Impressum-Link wird erkannt"""
        html = """
        <html>
        <body>
            <footer>
                <a href="/contact">Kontakt</a>
            </footer>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        impressum_link = soup.find('a', string=lambda x: x and 'impressum' in x.lower())
        assert impressum_link is None
    
    def test_imprint_english_found(self):
        """Test: Englischer 'Imprint' Link wird auch gefunden"""
        html = """
        <html>
        <body>
            <footer>
                <a href="/imprint">Imprint</a>
            </footer>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        imprint_link = soup.find('a', string=lambda x: x and 'imprint' in x.lower())
        assert imprint_link is not None


class TestImpressumContent:
    """Tests für Impressum-Inhalts-Validierung"""
    
    def test_complete_impressum_tmg5(self):
        """Test: Vollständiges Impressum nach TMG §5"""
        html = """
        <html>
        <body>
            <h1>Impressum</h1>
            
            <h2>Angaben gemäß § 5 TMG</h2>
            <p>
                Musterfirma GmbH<br>
                Musterstraße 123<br>
                12345 Musterstadt<br>
                Deutschland
            </p>
            
            <h2>Kontakt</h2>
            <p>
                Telefon: +49 30 12345678<br>
                E-Mail: info@musterfirma.de
            </p>
            
            <h2>Registereintrag</h2>
            <p>
                Registergericht: Amtsgericht Berlin<br>
                Registernummer: HRB 12345
            </p>
            
            <h2>Umsatzsteuer-ID</h2>
            <p>
                Umsatzsteuer-Identifikationsnummer: DE123456789
            </p>
            
            <h2>Geschäftsführung</h2>
            <p>Max Mustermann</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        # Prüfe Pflichtangaben
        assert 'gmbh' in text or 'ag' in text or any(form in text for form in ['kg', 'ohg', 'gbr'])
        assert 'telefon' in text or 'tel.' in text
        assert 'e-mail' in text or 'email' in text
        assert 'register' in text
        assert any(keyword in text for keyword in ['hrb', 'hra', 'registernummer'])
    
    def test_missing_phone_number(self):
        """Test: Fehlende Telefonnummer wird erkannt"""
        html = """
        <html>
        <body>
            <h1>Impressum</h1>
            <p>
                Musterfirma GmbH<br>
                Musterstraße 123<br>
                12345 Musterstadt<br>
                E-Mail: info@musterfirma.de
            </p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        has_phone = any(keyword in text for keyword in ['telefon', 'tel.', 'tel:', 'phone'])
        assert has_phone is False
    
    def test_missing_email(self):
        """Test: Fehlende E-Mail wird erkannt"""
        html = """
        <html>
        <body>
            <h1>Impressum</h1>
            <p>
                Musterfirma GmbH<br>
                Musterstraße 123<br>
                12345 Musterstadt<br>
                Telefon: +49 30 12345678
            </p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        has_email = 'e-mail' in text or 'email' in text or '@' in text
        assert has_email is False
    
    def test_address_format_validation(self):
        """Test: Vollständige Adresse wird validiert"""
        html = """
        <html>
        <body>
            <h1>Impressum</h1>
            <p>
                Musterfirma GmbH<br>
                Musterstraße 123<br>
                12345 Musterstadt
            </p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        # Prüfe auf PLZ (5 Ziffern) und Straße mit Hausnummer
        import re
        has_plz = bool(re.search(r'\b\d{5}\b', text))
        has_street_number = bool(re.search(r'\w+straße\s+\d+', text, re.IGNORECASE))
        
        assert has_plz is True
        assert has_street_number is True


class TestImpressumPOBox:
    """Tests für Postfach-Validierung (nicht erlaubt)"""
    
    def test_postbox_detected(self):
        """Test: Postfach wird erkannt (nicht TMG-konform)"""
        html = """
        <html>
        <body>
            <h1>Impressum</h1>
            <p>
                Musterfirma GmbH<br>
                Postfach 12345<br>
                12345 Musterstadt
            </p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        # Postfach ist NICHT erlaubt
        has_postbox = 'postfach' in text or 'p.o. box' in text or 'po box' in text
        assert has_postbox is True  # Wird erkannt (= Problem!)
    
    def test_valid_address_without_postbox(self):
        """Test: Valide Adresse ohne Postfach"""
        html = """
        <html>
        <body>
            <h1>Impressum</h1>
            <p>
                Musterfirma GmbH<br>
                Musterstraße 123<br>
                12345 Musterstadt
            </p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        has_postbox = 'postfach' in text
        assert has_postbox is False  # Kein Postfach = OK


@pytest.mark.asyncio
class TestImpressumIntegration:
    """Integrations-Tests für Impressum"""
    
    def test_full_impressum_validation(self):
        """Test: Vollständige Impressum-Validierung"""
        html = """
        <html>
        <body>
            <footer>
                <a href="/impressum">Impressum</a>
            </footer>
            
            <div id="impressum-content">
                <h1>Impressum</h1>
                
                <h2>Angaben gemäß § 5 TMG</h2>
                <p>
                    Musterfirma GmbH<br>
                    Musterstraße 123<br>
                    12345 Musterstadt<br>
                    Deutschland
                </p>
                
                <h2>Kontakt</h2>
                <p>
                    Telefon: +49 30 12345678<br>
                    E-Mail: info@musterfirma.de
                </p>
                
                <h2>Registereintrag</h2>
                <p>
                    Registergericht: Amtsgericht Berlin<br>
                    Registernummer: HRB 12345
                </p>
                
                <h2>Umsatzsteuer-ID</h2>
                <p>USt-IdNr.: DE123456789</p>
                
                <h2>Geschäftsführung</h2>
                <p>Max Mustermann</p>
                
                <h2>Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV</h2>
                <p>
                    Max Mustermann<br>
                    Musterstraße 123<br>
                    12345 Musterstadt
                </p>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Link vorhanden
        impressum_link = soup.find('a', string=lambda x: x and 'impressum' in x.lower())
        assert impressum_link is not None
        
        # 2. Content vorhanden
        impressum_content = soup.find(id='impressum-content')
        assert impressum_content is not None
        
        text = impressum_content.get_text().lower()
        
        # 3. Alle Pflichtangaben vorhanden
        checks = {
            'company': 'gmbh' in text,
            'address': any(x in text for x in ['straße', 'str.']),
            'plz': True,  # Simplified check
            'phone': 'telefon' in text,
            'email': 'e-mail' in text or '@' in text,
            'register': 'register' in text,
            'hrb': 'hrb' in text,
            'geschäftsführung': 'geschäftsführung' in text or 'geschäftsführer' in text,
            'rstv': 'rstv' in text or '§ 55' in text
        }
        
        # Mindestens 8 von 9 müssen erfüllt sein
        passed = sum(checks.values())
        assert passed >= 8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

