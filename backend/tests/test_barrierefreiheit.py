"""
Unit-Tests für Barrierefreiheits-Checks
"""

import pytest
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks.aria_checker import ARIAChecker
from compliance_engine.contrast_analyzer import ContrastAnalyzer


class TestARIAChecker:
    """Tests für ARIA-Compliance-Checks"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.checker = ARIAChecker()
    
    def test_button_without_label(self):
        """Test: Button ohne Label wird erkannt"""
        html = """
        <html>
        <body>
            <button></button>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        issues = self.checker.check_aria_compliance(soup, 'https://test.com')
        
        # Sollte Issue für Button ohne Label finden
        button_issues = [i for i in issues if 'BUTTON' in i['title']]
        assert len(button_issues) > 0
        assert button_issues[0]['severity'] == 'warning'
    
    def test_button_with_text_passes(self):
        """Test: Button mit Text ist OK"""
        html = """
        <html>
        <body>
            <button>Absenden</button>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        issues = self.checker.check_aria_compliance(soup, 'https://test.com')
        
        # Sollte kein Issue für Button mit Text finden
        button_issues = [i for i in issues if 'BUTTON' in i['title']]
        assert len(button_issues) == 0
    
    def test_button_with_aria_label_passes(self):
        """Test: Button mit aria-label ist OK"""
        html = """
        <html>
        <body>
            <button aria-label="Menü öffnen">
                <svg>...</svg>
            </button>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        issues = self.checker.check_aria_compliance(soup, 'https://test.com')
        
        # Sollte kein Issue finden
        button_issues = [i for i in issues if 'BUTTON' in i['title']]
        assert len(button_issues) == 0
    
    def test_missing_landmarks(self):
        """Test: Fehlende Landmark-Regions werden erkannt"""
        html = """
        <html>
        <body>
            <div>Content without landmarks</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        issues = self.checker.check_aria_compliance(soup, 'https://test.com')
        
        # Sollte Issue für fehlende Landmarks finden
        landmark_issues = [i for i in issues if 'Landmark' in i['title']]
        assert len(landmark_issues) > 0
    
    def test_complete_landmarks_pass(self):
        """Test: Vollständige Landmarks sind OK"""
        html = """
        <html>
        <body>
            <header>Header</header>
            <nav>Navigation</nav>
            <main>Content</main>
            <footer>Footer</footer>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        issues = self.checker.check_aria_compliance(soup, 'https://test.com')
        
        # Sollte keine Landmark-Issues finden
        landmark_issues = [i for i in issues if 'Landmark' in i['title']]
        assert len(landmark_issues) == 0
    
    def test_invalid_aria_role(self):
        """Test: Invalide ARIA-Rolle wird erkannt"""
        html = """
        <html>
        <body>
            <div role="invalid-role">Content</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        issues = self.checker.check_aria_compliance(soup, 'https://test.com')
        
        # Sollte Issue für invalide Rolle finden
        role_issues = [i for i in issues if 'invalide ARIA-Rollen' in i['title']]
        assert len(role_issues) > 0
    
    def test_valid_aria_role_passes(self):
        """Test: Valide ARIA-Rolle ist OK"""
        html = """
        <html>
        <body>
            <div role="navigation">Nav content</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        issues = self.checker.check_aria_compliance(soup, 'https://test.com')
        
        # Sollte kein Issue für valide Rolle finden
        role_issues = [i for i in issues if 'invalide' in i['title'].lower()]
        assert len(role_issues) == 0
    
    def test_input_without_label(self):
        """Test: Input ohne Label wird erkannt"""
        html = """
        <html>
        <body>
            <input type="text" id="email">
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        issues = self.checker.check_aria_compliance(soup, 'https://test.com')
        
        # Sollte Issue für Input ohne Label finden
        form_issues = [i for i in issues if 'Formularfelder' in i['title']]
        assert len(form_issues) > 0
        assert form_issues[0]['severity'] == 'critical'
    
    def test_input_with_label_passes(self):
        """Test: Input mit Label ist OK"""
        html = """
        <html>
        <body>
            <label for="email">E-Mail</label>
            <input type="text" id="email">
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        issues = self.checker.check_aria_compliance(soup, 'https://test.com')
        
        # Sollte kein Issue finden
        form_issues = [i for i in issues if 'Formularfelder' in i['title']]
        assert len(form_issues) == 0


class TestContrastAnalyzer:
    """Tests für Kontrast-Analysen"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.analyzer = ContrastAnalyzer(target_level='AA')
    
    def test_insufficient_contrast_detected(self):
        """Test: Unzureichender Kontrast wird erkannt"""
        result = self.analyzer.analyze_color_pair(
            foreground='#999999',
            background='#FFFFFF',
            text_size='normal'
        )
        
        assert result['valid'] is True
        assert result['passes'] is False
        assert result['contrast_ratio'] < 4.5
    
    def test_sufficient_contrast_passes(self):
        """Test: Ausreichender Kontrast ist OK"""
        result = self.analyzer.analyze_color_pair(
            foreground='#000000',
            background='#FFFFFF',
            text_size='normal'
        )
        
        assert result['valid'] is True
        assert result['passes'] is True
        assert result['contrast_ratio'] >= 4.5
    
    def test_large_text_lower_requirement(self):
        """Test: Großer Text hat niedrigere Anforderung (3:1)"""
        result = self.analyzer.analyze_color_pair(
            foreground='#767676',  # 3.1:1 auf Weiß
            background='#FFFFFF',
            text_size='large'
        )
        
        assert result['required_ratio'] == 3.0
        assert result['passes'] is True
    
    def test_normal_text_higher_requirement(self):
        """Test: Normaler Text hat höhere Anforderung (4.5:1)"""
        result = self.analyzer.analyze_color_pair(
            foreground='#767676',
            background='#FFFFFF',
            text_size='normal'
        )
        
        assert result['required_ratio'] == 4.5
        assert result['passes'] is False
    
    def test_black_on_white_high_contrast(self):
        """Test: Schwarz auf Weiß hat sehr hohen Kontrast"""
        result = self.analyzer.analyze_color_pair(
            foreground='#000000',
            background='#FFFFFF'
        )
        
        assert result['contrast_ratio'] == 21.0  # Maximum
    
    def test_white_on_black_high_contrast(self):
        """Test: Weiß auf Schwarz hat auch hohen Kontrast"""
        result = self.analyzer.analyze_color_pair(
            foreground='#FFFFFF',
            background='#000000'
        )
        
        assert result['contrast_ratio'] == 21.0


@pytest.mark.asyncio
class TestAccessibilityIntegration:
    """Integrations-Tests für Barrierefreiheit"""
    
    def test_full_accessibility_scan(self):
        """Test: Vollständiger Accessibility-Scan"""
        html = """
        <html lang="de">
        <head>
            <title>Test</title>
        </head>
        <body>
            <header>
                <nav>
                    <a href="/">Home</a>
                </nav>
            </header>
            <main>
                <h1>Willkommen</h1>
                <img src="test.jpg" alt="Testbild">
                <form>
                    <label for="name">Name</label>
                    <input type="text" id="name">
                    <button type="submit">Absenden</button>
                </form>
            </main>
            <footer>
                <p>&copy; 2025</p>
            </footer>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        checker = ARIAChecker()
        issues = checker.check_aria_compliance(soup, 'https://test.com')
        
        # Diese Seite sollte KEINE Issues haben
        assert len(issues) == 0
    
    def test_problematic_page(self):
        """Test: Seite mit vielen Problemen"""
        html = """
        <html>
        <body>
            <div class="header">
                <div class="nav">
                    <a href="#">Link</a>
                </div>
            </div>
            <div class="content">
                <button></button>
                <img src="test.jpg">
                <input type="text">
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        checker = ARIAChecker()
        issues = checker.check_aria_compliance(soup, 'https://test.com')
        
        # Diese Seite sollte MEHRERE Issues haben
        assert len(issues) > 3
        
        # Mindestens: Landmarks, Button, Input ohne Label
        categories = [i['title'] for i in issues]
        assert any('Landmark' in c for c in categories)
        assert any('BUTTON' in c for c in categories)
        assert any('Formular' in c for c in categories)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

