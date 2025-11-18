"""
Complyo Widget Manager

Verwaltet Widget-Deployment und Auto-Konfiguration für:
- Cookie-Consent-Banner
- Accessibility-Tools
- Combined-Compliance-Widget

© 2025 Complyo.tech
"""

import json
import hashlib
from typing import Dict, Any, List, Optional
from enum import Enum


class WidgetType(Enum):
    """Verfügbare Widget-Typen"""
    COOKIE_CONSENT = "cookie-consent"
    ACCESSIBILITY = "accessibility"
    COMBINED = "combined"


class WidgetVersion(Enum):
    """Widget-Versionen"""
    COOKIE_V2 = "cookie-banner-v2.0.0"
    ACCESSIBILITY_V2 = "accessibility-v2.0.0"
    COMBINED_V1 = "combined-compliance-v1.0.0"


class WidgetManager:
    """
    Hauptklasse für Widget-Verwaltung
    """
    
    def __init__(self):
        """Initialize widget manager"""
        self.base_url = "https://widgets.complyo.tech"
        self.cdn_url = "https://cdn.complyo.tech/widgets"
        
        # Widget-Version-Mapping
        self.versions = {
            WidgetType.COOKIE_CONSENT: WidgetVersion.COOKIE_V2.value,
            WidgetType.ACCESSIBILITY: WidgetVersion.ACCESSIBILITY_V2.value,
            WidgetType.COMBINED: WidgetVersion.COMBINED_V1.value
        }
    
    async def generate_cookie_widget_code(
        self,
        site_id: str,
        config: Dict[str, Any],
        use_cdn: bool = True
    ) -> str:
        """
        Generiert Cookie-Widget-Integration-Code
        
        Args:
            site_id: Eindeutige Site-ID
            config: Widget-Konfiguration
            use_cdn: CDN verwenden (schneller) oder direkt von widgets.complyo.tech
        
        Returns:
            HTML-Code zum Einbinden
        """
        widget_version = self.versions[WidgetType.COOKIE_CONSENT]
        widget_url = f"{self.cdn_url if use_cdn else self.base_url}/{widget_version}.min.js"
        
        # Optimize config für Performance
        optimized_config = self._optimize_config(config)
        config_json = json.dumps(optimized_config, ensure_ascii=False, separators=(',', ':'))
        
        # Generate integrity hash for security
        integrity = self._generate_integrity_hash(widget_version)
        
        code = f'''<!-- Complyo Cookie Consent Widget v2.0 -->
<script 
  src="{widget_url}"
  data-site-id="{site_id}"
  data-config='{config_json}'
  integrity="{integrity}"
  crossorigin="anonymous"
  async
></script>
<!-- End Complyo Cookie Consent -->'''
        
        return code
    
    async def generate_accessibility_widget_code(
        self,
        site_id: str,
        config: Dict[str, Any],
        use_cdn: bool = True
    ) -> str:
        """
        Generiert Accessibility-Widget-Integration-Code
        """
        widget_version = self.versions[WidgetType.ACCESSIBILITY]
        widget_url = f"{self.cdn_url if use_cdn else self.base_url}/{widget_version}.min.js"
        
        optimized_config = self._optimize_config(config)
        config_json = json.dumps(optimized_config, ensure_ascii=False, separators=(',', ':'))
        
        integrity = self._generate_integrity_hash(widget_version)
        
        code = f'''<!-- Complyo Accessibility Widget v2.0 -->
<script 
  src="{widget_url}"
  data-site-id="{site_id}"
  data-config='{config_json}'
  integrity="{integrity}"
  crossorigin="anonymous"
  async
></script>
<!-- End Complyo Accessibility -->'''
        
        return code
    
    async def generate_combined_widget_code(
        self,
        site_id: str,
        cookie_config: Dict[str, Any],
        accessibility_config: Dict[str, Any],
        use_cdn: bool = True
    ) -> str:
        """
        Generiert Combined-Widget-Code (Cookie + Accessibility in einem)
        """
        widget_version = self.versions[WidgetType.COMBINED]
        widget_url = f"{self.cdn_url if use_cdn else self.base_url}/{widget_version}.min.js"
        
        combined_config = {
            "cookie": self._optimize_config(cookie_config),
            "accessibility": self._optimize_config(accessibility_config)
        }
        
        config_json = json.dumps(combined_config, ensure_ascii=False, separators=(',', ':'))
        integrity = self._generate_integrity_hash(widget_version)
        
        code = f'''<!-- Complyo Combined Compliance Widget v1.0 -->
<script 
  src="{widget_url}"
  data-site-id="{site_id}"
  data-config='{config_json}'
  integrity="{integrity}"
  crossorigin="anonymous"
  async
></script>
<!-- End Complyo Combined Widget -->'''
        
        return code
    
    def configure_cookie_widget(
        self,
        detected_cookies: List[Dict[str, Any]],
        analytics_tools: List[str],
        tech_stack: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Auto-Konfiguration basierend auf Website-Scan
        
        Args:
            detected_cookies: Liste erkannter Cookies
            analytics_tools: Liste erkannter Analytics-Tools
            tech_stack: Optional Tech-Stack-Info
        
        Returns:
            Optimale Widget-Konfiguration
        """
        # Categorize cookies
        categorized = self._categorize_cookies(detected_cookies)
        
        # Determine layout based on cookie count
        layout = "box_modal" if len(detected_cookies) > 5 else "banner_bottom"
        
        # Build config
        config = {
            # Design
            "layout": layout,
            "position": "center" if layout == "box_modal" else "bottom",
            "primaryColor": "#7c3aed",
            "accentColor": "#9333ea",
            "bgColor": "#ffffff",
            "textColor": "#333333",
            "buttonStyle": "rounded",
            
            # Behavior
            "autoBlockScripts": True,
            "respectDNT": True,
            "cookieLifetimeDays": 365,
            "showBranding": True,
            "consentMode": "opt-in",  # DSGVO-konform
            
            # Cookies
            "cookies": categorized,
            
            # Analytics
            "tracking_tools": analytics_tools,
            
            # Language
            "language": "de",
            "multiLanguage": True,
            "availableLanguages": ["de", "en"],
            
            # Advanced
            "logConsent": True,
            "consentAPI": True,
            "showStatistics": len(detected_cookies) > 0,
            
            # CMS-specific
            "cms": tech_stack.get("cms", [None])[0] if tech_stack else None
        }
        
        return config
    
    def configure_accessibility_widget(
        self,
        accessibility_issues: List[Dict[str, Any]],
        tech_stack: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Auto-Konfiguration für Accessibility-Widget
        
        Args:
            accessibility_issues: Gefundene A11y-Issues
            tech_stack: Optional Tech-Stack-Info
        
        Returns:
            Optimale Widget-Konfiguration
        """
        # Determine which features to enable based on issues
        features = ["contrast", "fontsize"]  # Always enabled
        
        issue_titles = [issue.get("title", "").lower() for issue in accessibility_issues]
        
        if any("alt" in title for title in issue_titles):
            features.append("alt-text-fix")
        
        if any("aria" in title for title in issue_titles):
            features.append("aria-fix")
        
        if any("fokus" in title or "focus" in title for title in issue_titles):
            features.append("focus-enhancement")
        
        if any("tastatur" in title or "keyboard" in title for title in issue_titles):
            features.append("keyboard-nav")
        
        # Always add some standard features
        features.extend([
            "line-height",
            "letter-spacing",
            "highlight-links",
            "screen-reader-friendly"
        ])
        
        config = {
            "siteId": "",  # Will be set by caller
            "autoFix": True,
            "showToolbar": True,
            "features": list(set(features)),  # Remove duplicates
            "position": "bottom-right",
            "primaryColor": "#7c3aed",
            "theme": "light",
            
            # Performance
            "lazyLoad": True,
            "cacheSettings": True,
            
            # Analytics
            "trackUsage": True,
            
            # CMS
            "cms": tech_stack.get("cms", [None])[0] if tech_stack else None
        }
        
        return config
    
    def _categorize_cookies(
        self,
        cookies: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Kategorisiert Cookies in DSGVO-Kategorien
        """
        categorized = {
            "necessary": [],
            "functional": [],
            "analytics": [],
            "marketing": []
        }
        
        # Known patterns
        necessary_patterns = [
            "phpsessid", "session", "csrf", "xsrf", "_token",
            "cookie-consent", "complyo", "security"
        ]
        
        analytics_patterns = [
            "_ga", "_gid", "_gat", "matomo", "piwik", "_pk",
            "analytics", "tracking", "_utm"
        ]
        
        marketing_patterns = [
            "_fbp", "_gcl", "fr", "tr", "ads", "doubleclick",
            "facebook", "google-ads", "linkedin", "pixel"
        ]
        
        for cookie in cookies:
            name = cookie.get("name", "").lower()
            
            # Categorize
            if any(pattern in name for pattern in necessary_patterns):
                categorized["necessary"].append(cookie.get("name"))
            elif any(pattern in name for pattern in analytics_patterns):
                categorized["analytics"].append(cookie.get("name"))
            elif any(pattern in name for pattern in marketing_patterns):
                categorized["marketing"].append(cookie.get("name"))
            else:
                categorized["functional"].append(cookie.get("name"))
        
        return categorized
    
    def _optimize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimiert Config für Größe und Performance
        """
        optimized = {}
        
        for key, value in config.items():
            # Skip None values
            if value is None:
                continue
            
            # Skip empty lists/dicts
            if isinstance(value, (list, dict)) and not value:
                continue
            
            # Skip default values (saves bandwidth)
            defaults = {
                "showBranding": True,
                "respectDNT": True,
                "lazyLoad": True,
                "trackUsage": True
            }
            
            if key in defaults and value == defaults[key]:
                continue
            
            optimized[key] = value
        
        return optimized
    
    def _generate_integrity_hash(self, widget_version: str) -> str:
        """
        Generiert Integrity-Hash für SRI (Subresource Integrity)
        
        In Production würde dies echte Hashes der Widget-Dateien zurückgeben
        """
        # Placeholder - in production würde hier der echte SHA-384 Hash stehen
        hash_base = f"complyo-{widget_version}"
        sha = hashlib.sha384(hash_base.encode()).hexdigest()
        return f"sha384-{sha}"
    
    def get_widget_preview_url(
        self,
        widget_type: WidgetType,
        site_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generiert Preview-URL für Widget
        """
        base = f"{self.base_url}/preview/{widget_type.value}"
        params = [f"site={site_id}"]
        
        if config:
            # Encode config as URL param (shortened)
            config_str = json.dumps(config, separators=(',', ':'))
            params.append(f"config={config_str[:500]}")  # Limit length
        
        return f"{base}?{'&'.join(params)}"
    
    def get_widget_documentation_url(
        self,
        widget_type: WidgetType,
        language: str = "de"
    ) -> str:
        """
        Gibt Dokumentations-URL für Widget
        """
        docs_base = "https://docs.complyo.tech"
        
        docs_paths = {
            WidgetType.COOKIE_CONSENT: f"{docs_base}/{language}/widgets/cookie-consent",
            WidgetType.ACCESSIBILITY: f"{docs_base}/{language}/widgets/accessibility",
            WidgetType.COMBINED: f"{docs_base}/{language}/widgets/combined"
        }
        
        return docs_paths.get(widget_type, f"{docs_base}/{language}/widgets")
    
    def generate_installation_guide(
        self,
        widget_type: WidgetType,
        integration_code: str,
        cms: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generiert Installations-Anleitung
        """
        guide = {
            "widget_type": widget_type.value,
            "integration_code": integration_code,
            "steps": [],
            "cms_specific": None,
            "testing": [],
            "troubleshooting": []
        }
        
        # Generic steps
        guide["steps"] = [
            {
                "step": 1,
                "title": "Code kopieren",
                "description": "Kopieren Sie den Widget-Code aus dem Textfeld"
            },
            {
                "step": 2,
                "title": "Einfügen",
                "description": "Fügen Sie den Code in Ihre Website ein (siehe CMS-spezifische Anleitung)"
            },
            {
                "step": 3,
                "title": "Testen",
                "description": "Laden Sie die Website neu und prüfen Sie, ob das Widget funktioniert"
            }
        ]
        
        # CMS-specific instructions
        if cms:
            guide["cms_specific"] = self._get_cms_instructions(cms, widget_type)
        
        # Testing checklist
        if widget_type == WidgetType.COOKIE_CONSENT:
            guide["testing"] = [
                "Banner erscheint beim ersten Besuch",
                "Consent-Entscheidung wird gespeichert",
                "Tracking-Scripts laden erst nach Consent",
                "Widerruf-Button ist erreichbar"
            ]
        elif widget_type == WidgetType.ACCESSIBILITY:
            guide["testing"] = [
                "Toolbar erscheint (unten rechts)",
                "Schriftgröße lässt sich ändern",
                "Kontrast lässt sich anpassen",
                "Einstellungen werden gespeichert"
            ]
        
        # Troubleshooting
        guide["troubleshooting"] = [
            {
                "problem": "Widget wird nicht angezeigt",
                "solutions": [
                    "Browser-Cache leeren",
                    "JavaScript-Fehler in Console prüfen",
                    "Prüfen ob Code korrekt eingefügt wurde"
                ]
            },
            {
                "problem": "Konflikte mit anderen Scripts",
                "solutions": [
                    "Widget als letztes Script laden",
                    "async-Attribut verwenden",
                    "Support kontaktieren"
                ]
            }
        ]
        
        return guide
    
    def _get_cms_instructions(
        self,
        cms: str,
        widget_type: WidgetType
    ) -> Dict[str, Any]:
        """
        CMS-spezifische Installations-Anweisungen
        """
        cms_lower = cms.lower()
        
        instructions = {
            "wordpress": {
                "method": "Plugin oder Theme",
                "steps": [
                    "Option 1: Nutzen Sie das 'Insert Headers and Footers' Plugin",
                    "Option 2: Fügen Sie den Code in functions.php ein (Child-Theme!)",
                    "Option 3: Nutzen Sie einen Custom-Code-Block in Ihrem Theme"
                ],
                "code_location": "wp_footer Hook oder vor </body>"
            },
            "shopify": {
                "method": "Theme-Editor",
                "steps": [
                    "Gehen Sie zu Online Store > Themes > Aktives Theme > Actions > Edit Code",
                    "Öffnen Sie theme.liquid",
                    "Fügen Sie den Code vor dem schließenden </body>-Tag ein",
                    "Speichern Sie die Änderungen"
                ],
                "code_location": "theme.liquid vor </body>"
            },
            "wix": {
                "method": "Tracking & Analytics",
                "steps": [
                    "Gehen Sie zu Einstellungen > Tracking & Analytics",
                    "Klicken Sie auf '+ Neues Tool' > 'Benutzerdefiniert'",
                    "Fügen Sie den Code ein",
                    "Wählen Sie 'Body - Ende'"
                ],
                "code_location": "Custom Code Section (Body - Ende)"
            }
        }
        
        return instructions.get(cms_lower, {
            "method": "Manuell in Template",
            "steps": [
                "Öffnen Sie Ihre Haupt-Template-Datei",
                "Fügen Sie den Code vor dem </body>-Tag ein",
                "Speichern und Website neu laden"
            ],
            "code_location": "Vor </body> im Haupt-Template"
        })


