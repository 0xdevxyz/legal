"""
Complyo Deep Scanner - Enhanced Website Analysis
Extends the base ComplianceScanner with additional context extraction:
- Company data (from Impressum/Footer)
- Shop system detection
- Technology stack analysis
- SEO data extraction
"""

import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import json

# Import base scanner
from compliance_engine.scanner import ComplianceScanner


class DeepScanner:
    """
    Enhanced scanner that extends base ComplianceScanner with context extraction
    """
    
    def __init__(self):
        self.base_scanner = ComplianceScanner()
        self.session = None
    
    async def __aenter__(self):
        await self.base_scanner.__aenter__()
        self.session = self.base_scanner.session
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.base_scanner.__aexit__(exc_type, exc_val, exc_tb)
    
    async def comprehensive_scan(self, url: str) -> Dict[str, Any]:
        """
        Performs comprehensive scan combining base compliance check + context extraction
        """
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # 1. Run base compliance scan
        base_result = await self.base_scanner.scan_website(url)
        
        # 2. Extract additional context in parallel
        try:
            context_data = await self._extract_website_context(url)
        except Exception as e:
            print(f"Warning: Context extraction failed: {e}")
            context_data = self._get_default_context()
        
        # 3. Merge results
        enhanced_result = {
            **base_result,
            "website_data": context_data["website_data"],
            "seo_data": context_data["seo_data"],
            "tech_stack": context_data["tech_stack"],
            "structure": context_data["structure"]
        }
        
        return enhanced_result
    
    async def _extract_website_context(self, url: str) -> Dict[str, Any]:
        """
        Extract comprehensive context about the website
        """
        # Fetch main page
        async with self.session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
        
        # Run extractions in parallel
        company_data = await self._extract_company_data(url, soup)
        seo_data = self._extract_seo_data(soup)
        tech_stack = self._detect_technologies(soup, html)
        structure = await self._analyze_structure(url, soup)
        
        return {
            "website_data": company_data,
            "seo_data": seo_data,
            "tech_stack": tech_stack,
            "structure": structure
        }
    
    async def _extract_company_data(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract company information from Impressum and footer
        """
        company_data = {
            "company_name": None,
            "address": None,
            "email": None,
            "phone": None,
            "shop_system": None,
            "has_impressum": False,
            "has_datenschutz": False
        }
        
        # Try to find Impressum page
        impressum_link = soup.find('a', href=re.compile(r'/impressum|/imprint', re.I))
        if impressum_link:
            company_data["has_impressum"] = True
            try:
                impressum_url = urljoin(url, impressum_link.get('href', ''))
                async with self.session.get(impressum_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    impressum_html = await response.text()
                    impressum_soup = BeautifulSoup(impressum_html, 'html.parser')
                    
                    # Extract company name (often in h1 or first paragraph)
                    h1 = impressum_soup.find('h1')
                    if h1:
                        company_data["company_name"] = h1.get_text(strip=True)
                    
                    # Extract email
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', impressum_soup.get_text())
                    if email_match:
                        company_data["email"] = email_match.group(0)
                    
                    # Extract phone
                    phone_match = re.search(r'(\+?\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}', impressum_soup.get_text())
                    if phone_match:
                        company_data["phone"] = phone_match.group(0)
                    
                    # Extract address (look for German address patterns)
                    address_pattern = r'(\d{5})\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)'
                    address_match = re.search(address_pattern, impressum_soup.get_text())
                    if address_match:
                        company_data["address"] = address_match.group(0)
            except Exception as e:
                print(f"Could not fetch Impressum: {e}")
        
        # Fallback: Try footer for company info
        if not company_data["company_name"]:
            footer = soup.find('footer') or soup.find(id=re.compile('footer', re.I))
            if footer:
                # Look for company patterns (GmbH, AG, etc.)
                company_pattern = r'([A-ZÄÖÜ][a-zäöüß\s&-]+(?:GmbH|AG|e\.K\.|UG|KG|OHG))'
                footer_text = footer.get_text()
                company_match = re.search(company_pattern, footer_text)
                if company_match:
                    company_data["company_name"] = company_match.group(1).strip()
        
        # Check for Datenschutz
        datenschutz_link = soup.find('a', href=re.compile(r'/datenschutz|/privacy', re.I))
        company_data["has_datenschutz"] = bool(datenschutz_link)
        
        # Detect shop system
        company_data["shop_system"] = self._detect_shop_system(soup)
        
        return company_data
    
    def _detect_shop_system(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Detect e-commerce platform
        """
        html_str = str(soup)
        
        # WooCommerce
        if 'woocommerce' in html_str.lower() or soup.find(class_=re.compile('woocommerce', re.I)):
            return "WooCommerce"
        
        # Shopify
        if 'shopify' in html_str.lower() or 'cdn.shopify.com' in html_str:
            return "Shopify"
        
        # Magento
        if 'magento' in html_str.lower() or soup.find(attrs={'data-mage-init': True}):
            return "Magento"
        
        # PrestaShop
        if 'prestashop' in html_str.lower():
            return "PrestaShop"
        
        # Shopware
        if 'shopware' in html_str.lower():
            return "Shopware"
        
        # Generic shop indicators
        cart_patterns = ['warenkorb', 'cart', 'basket', 'add-to-cart']
        for pattern in cart_patterns:
            if soup.find(class_=re.compile(pattern, re.I)) or soup.find(id=re.compile(pattern, re.I)):
                return "Generic E-Commerce"
        
        return None
    
    def _extract_seo_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract SEO-related meta data
        """
        seo_data = {
            "title": None,
            "description": None,
            "keywords": None,
            "og_title": None,
            "og_description": None,
            "og_image": None,
            "h1_count": 0,
            "h2_count": 0,
            "img_without_alt": 0
        }
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            seo_data["title"] = title_tag.get_text(strip=True)
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            seo_data["description"] = meta_desc.get('content', '')
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            seo_data["keywords"] = meta_keywords.get('content', '')
        
        # Open Graph
        og_title = soup.find('meta', property='og:title')
        if og_title:
            seo_data["og_title"] = og_title.get('content', '')
        
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            seo_data["og_description"] = og_desc.get('content', '')
        
        og_img = soup.find('meta', property='og:image')
        if og_img:
            seo_data["og_image"] = og_img.get('content', '')
        
        # Heading counts
        seo_data["h1_count"] = len(soup.find_all('h1'))
        seo_data["h2_count"] = len(soup.find_all('h2'))
        
        # Images without alt
        images = soup.find_all('img')
        seo_data["img_without_alt"] = sum(1 for img in images if not img.get('alt'))
        
        return seo_data
    
    def _detect_technologies(self, soup: BeautifulSoup, html: str) -> Dict[str, List[str]]:
        """
        Detect technologies used on the website
        """
        tech_stack = {
            "cms": [],
            "frameworks": [],
            "analytics": [],
            "hosting": [],
            "other": []
        }
        
        html_lower = html.lower()
        
        # CMS Detection
        if 'wp-content' in html_lower or 'wordpress' in html_lower:
            tech_stack["cms"].append("WordPress")
        if 'typo3' in html_lower:
            tech_stack["cms"].append("TYPO3")
        if 'joomla' in html_lower:
            tech_stack["cms"].append("Joomla")
        if 'drupal' in html_lower:
            tech_stack["cms"].append("Drupal")
        
        # Frameworks
        if 'react' in html_lower or soup.find(id='root') or soup.find(attrs={'data-reactroot': True}):
            tech_stack["frameworks"].append("React")
        if 'vue' in html_lower or soup.find(id='app') and 'v-' in html_lower:
            tech_stack["frameworks"].append("Vue.js")
        if 'angular' in html_lower or 'ng-app' in html_lower:
            tech_stack["frameworks"].append("Angular")
        if 'next' in html_lower or '__next' in html_lower:
            tech_stack["frameworks"].append("Next.js")
        
        # Analytics
        if 'google-analytics' in html_lower or 'gtag' in html_lower or 'ga(' in html_lower:
            tech_stack["analytics"].append("Google Analytics")
        if 'matomo' in html_lower or 'piwik' in html_lower:
            tech_stack["analytics"].append("Matomo")
        if 'facebook' in html_lower and 'pixel' in html_lower:
            tech_stack["analytics"].append("Facebook Pixel")
        if 'hotjar' in html_lower:
            tech_stack["analytics"].append("Hotjar")
        
        # External Resources (Hosting indicators)
        if 'cloudflare' in html_lower:
            tech_stack["hosting"].append("Cloudflare")
        if 'amazonaws' in html_lower:
            tech_stack["hosting"].append("AWS")
        if 'googleusercontent' in html_lower:
            tech_stack["hosting"].append("Google Cloud")
        
        return tech_stack
    
    async def _analyze_structure(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Analyze website structure
        """
        structure = {
            "has_navigation": False,
            "has_footer": False,
            "has_header": False,
            "link_count": 0,
            "internal_links": 0,
            "external_links": 0,
            "page_count_estimate": 0
        }
        
        # Navigation
        nav = soup.find('nav') or soup.find(role='navigation')
        structure["has_navigation"] = bool(nav)
        
        # Footer
        footer = soup.find('footer')
        structure["has_footer"] = bool(footer)
        
        # Header
        header = soup.find('header')
        structure["has_header"] = bool(header)
        
        # Links
        links = soup.find_all('a', href=True)
        structure["link_count"] = len(links)
        
        domain = urlparse(url).netloc
        for link in links:
            href = link.get('href', '')
            if href.startswith('/') or domain in href:
                structure["internal_links"] += 1
            else:
                structure["external_links"] += 1
        
        # Estimate page count (based on internal links)
        structure["page_count_estimate"] = min(structure["internal_links"], 100)
        
        return structure
    
    def _get_default_context(self) -> Dict[str, Any]:
        """
        Return default/empty context if extraction fails
        """
        return {
            "website_data": {
                "company_name": None,
                "address": None,
                "email": None,
                "phone": None,
                "shop_system": None,
                "has_impressum": False,
                "has_datenschutz": False
            },
            "seo_data": {
                "title": None,
                "description": None,
                "h1_count": 0,
                "h2_count": 0,
                "img_without_alt": 0
            },
            "tech_stack": {
                "cms": [],
                "frameworks": [],
                "analytics": [],
                "hosting": [],
                "other": []
            },
            "structure": {
                "has_navigation": False,
                "has_footer": False,
                "has_header": False,
                "link_count": 0,
                "internal_links": 0,
                "external_links": 0,
                "page_count_estimate": 0
            }
        }

