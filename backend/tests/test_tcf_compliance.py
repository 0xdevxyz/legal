"""
Tests für TCF 2.2 Compliance Checker
"""

import pytest
import asyncio
from bs4 import BeautifulSoup
from compliance_engine.checks.tcf_check import check_tcf_compliance, detect_cmp_from_scripts, validate_tc_string_format
from compliance_engine.tcf_vendor_analyzer import tcf_vendor_analyzer


class TestTCFDetection:
    """Tests für TCF Detection"""
    
    @pytest.mark.asyncio
    async def test_detect_cookiebot_tcf(self):
        """Test: Cookiebot TCF wird erkannt"""
        html = """
        <html>
        <head>
            <script src="https://consent.cookiebot.com/uc.js" data-cbid="test123"></script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await check_tcf_compliance("https://example.com", soup, html)
        
        assert result["has_tcf"] == True
        assert result["cmp_name"] == "Cookiebot"
        assert result["cmp_id"] == 11
    
    @pytest.mark.asyncio
    async def test_detect_sourcepoint_tcf(self):
        """Test: Sourcepoint TCF wird erkannt"""
        html = """
        <html>
        <head>
            <script src="https://cdn.privacy-mgmt.com/unified/wrapperMessagingWithoutDetection.js"></script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await check_tcf_compliance("https://example.com", soup, html)
        
        assert result["has_tcf"] == True
        assert result["cmp_name"] == "Sourcepoint"
    
    @pytest.mark.asyncio
    async def test_detect_no_tcf(self):
        """Test: Kein TCF wird korrekt erkannt"""
        html = """
        <html>
        <head></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await check_tcf_compliance("https://example.com", soup, html)
        
        assert result["has_tcf"] == False
        assert result["tc_string_found"] == False
    
    @pytest.mark.asyncio
    async def test_detect_tcfapi_in_script(self):
        """Test: __tcfapi im Script wird erkannt"""
        html = """
        <html>
        <head>
            <script>
                window.__tcfapi = function(command, version, callback) {
                    // TCF API implementation
                };
            </script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await check_tcf_compliance("https://example.com", soup, html)
        
        assert result["has_tcf"] == True


class TestCMPDetection:
    """Tests für CMP Detection"""
    
    def test_detect_onetrust(self):
        """Test: OneTrust wird erkannt"""
        html = """
        <html>
        <head>
            <script src="https://cdn.cookielaw.org/scripttemplates/otSDKStub.js"></script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        cmp = detect_cmp_from_scripts(soup)
        
        assert cmp is not None
        assert cmp["name"] == "OneTrust"
        assert cmp["cmp_id"] == 28
    
    def test_detect_usercentrics(self):
        """Test: Usercentrics wird erkannt"""
        html = """
        <html>
        <head>
            <script src="https://app.usercentrics.eu/browser-ui/latest/loader.js"></script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        cmp = detect_cmp_from_scripts(soup)
        
        assert cmp is not None
        assert cmp["name"] == "Usercentrics"


class TestTCStringValidation:
    """Tests für TC String Validation"""
    
    def test_valid_tc_string_format(self):
        """Test: Valides TC String Format"""
        # Beispiel TC String (vereinfacht)
        tc_string = "CPt7PkAPt7PkADcABCENCsCgAP_AAH_AAAqIHJNf_X__bX9j-_59"
        
        result = validate_tc_string_format(tc_string)
        
        assert result["valid"] == True
        assert result["version"] == "2.2"
    
    def test_invalid_tc_string_empty(self):
        """Test: Leerer TC String"""
        result = validate_tc_string_format("")
        
        assert result["valid"] == False
        assert "leer" in result["errors"][0]
    
    def test_invalid_tc_string_short(self):
        """Test: Zu kurzer TC String"""
        result = validate_tc_string_format("ABC123")
        
        assert result["valid"] == False
        assert "zu kurz" in result["errors"][0].lower()


class TestVendorAnalyzer:
    """Tests für TCF Vendor Analyzer"""
    
    @pytest.mark.asyncio
    async def test_load_global_vendor_list(self):
        """Test: Global Vendor List laden"""
        result = await tcf_vendor_analyzer.load_global_vendor_list()
        
        assert result is not None
        assert "vendors" in result
        assert "purposes" in result
    
    @pytest.mark.asyncio
    async def test_analyze_vendors_google(self):
        """Test: Google Vendors werden erkannt"""
        html = """
        <html>
        <head>
            <script src="https://www.googletagmanager.com/gtag/js?id=GA123"></script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        vendors = await tcf_vendor_analyzer.analyze_vendors_on_page(soup, html)
        
        assert len(vendors) > 0
        # Google sollte erkannt werden (Vendor ID 755)
        google_vendors = [v for v in vendors if "Google" in v["vendor_name"]]
        assert len(google_vendors) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_vendors_facebook(self):
        """Test: Facebook Pixel wird erkannt"""
        html = """
        <html>
        <head>
            <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        vendors = await tcf_vendor_analyzer.analyze_vendors_on_page(soup, html)
        
        # Facebook sollte erkannt werden (Vendor ID 45)
        facebook_vendors = [v for v in vendors if "Facebook" in v["vendor_name"]]
        assert len(facebook_vendors) > 0


class TestTCFIssues:
    """Tests für TCF Issue Generation"""
    
    @pytest.mark.asyncio
    async def test_missing_tcf_generates_info_issue(self):
        """Test: Fehlendes TCF generiert Info-Issue wenn CMP vorhanden"""
        html = """
        <html>
        <head>
            <!-- OneTrust ohne TCF -->
            <script src="https://cdn.cookielaw.org/scripttemplates/otSDKStub.js"></script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await check_tcf_compliance("https://example.com", soup, html)
        
        assert result["has_tcf"] == False
        assert len(result["issues"]) > 0
        # Sollte Info-Issue sein (kein Error, da TCF optional)
        assert result["issues"][0]["severity"] == "info"
    
    @pytest.mark.asyncio
    async def test_tcf_without_tc_string_generates_warning(self):
        """Test: TCF ohne TC String generiert Warning"""
        html = """
        <html>
        <head>
            <script>
                window.__tcfapi = function(command, version, callback) {
                    // TCF API ohne TC String
                };
            </script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await check_tcf_compliance("https://example.com", soup, html)
        
        assert result["has_tcf"] == True
        assert result["tc_string_found"] == False
        # Sollte Warning generieren
        warnings = [i for i in result["issues"] if i["severity"] == "warning"]
        assert len(warnings) > 0


if __name__ == "__main__":
    # Für direktes Ausführen
    pytest.main([__file__, "-v"])

