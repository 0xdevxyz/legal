"""
Cookie Banner Handler - Widget-Integration

Behandelt Cookie-Consent-Management und TTDSG-Compliance
"""

from typing import Dict, Any, Optional, List
import json


class CookieBannerHandler:
    """Handler für Cookie-Banner und Consent-Management"""
    
    def __init__(self, widget_manager=None):
        """
        Args:
            widget_manager: Optional WidgetManager instance
        """
        self.widget_manager = widget_manager
    
    async def handle(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        ai_generated_fix: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generiert Cookie-Consent-Lösung
        
        Preferiert Widget-Integration über Code-Snippets
        """
        # Analyze cookies from context
        cookies = context.get("cookies", [])
        analytics = context.get("technology", {}).get("analytics", [])
        
        # Build widget configuration
        widget_config = self._build_widget_config(cookies, analytics, context)
        
        # Generate integration code
        if self.widget_manager:
            integration_code = await self.widget_manager.generate_cookie_widget_code(
                site_id=context.get("site_id", "demo"),
                config=widget_config
            )
        else:
            integration_code = self._generate_fallback_integration_code(
                context.get("site_id", "demo"),
                widget_config
            )
        
        # Build result
        return {
            "fix_id": issue.get("id", "cookie_banner_fix"),
            "title": "Cookie-Consent-Banner Integration",
            "description": "DSGVO/TTDSG-konformes Cookie-Consent-Management",
            "widget_type": "cookie-consent",
            "integration_code": integration_code,
            "configuration": widget_config,
            "preview_url": f"https://widgets.complyo.tech/preview/cookie-consent?site={context.get('site_id', 'demo')}",
            "features": [
                "Granulare Consent-Verwaltung (Notwendig, Statistik, Marketing)",
                "Automatisches Cookie-Blocking vor Consent",
                "Responsive Design & Mobile-optimiert",
                "WCAG 2.1 AA konform",
                "Mehrsprachig (DE/EN)",
                "Consent-Logging für Nachweis",
                "Anpassbares Design"
            ],
            "integration": {
                "instructions": self._get_integration_instructions(),
                "where": "Vor dem schließenden </body>-Tag",
                "test_checklist": [
                    "Banner erscheint beim ersten Besuch",
                    "Cookies werden erst nach Consent gesetzt",
                    "Consent-Entscheidung wird gespeichert",
                    "Widerruf-Button ist erreichbar",
                    "Banner ist barrierefrei navigierbar"
                ]
            },
            "estimated_time": "5 Minuten",
            "legal_compliance": {
                "dsgvo": True,
                "ttdsg": True,
                "references": ["Art. 7 DSGVO", "§ 25 TTDSG"]
            },
            "detected_cookies": self._categorize_cookies(cookies),
            "detected_tracking": analytics,
            "next_steps": [
                "Widget-Code einfügen",
                "Tracking-Scripts an Consent koppeln",
                "Datenschutzerklärung aktualisieren",
                "Banner testen (verschiedene Browser)"
            ]
        }
    
    def _build_widget_config(
        self,
        cookies: List[Dict[str, Any]],
        analytics: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Baut Widget-Konfiguration basierend auf erkannten Cookies
        """
        # Categorize cookies
        categorized = self._categorize_cookies(cookies)
        
        # Determine optimal layout
        layout = "box_modal"  # Default: Modal Box (DSGVO-konform)
        
        config = {
            "layout": layout,
            "position": "center",
            "primaryColor": "#7c3aed",
            "accentColor": "#9333ea",
            "bgColor": "#ffffff",
            "textColor": "#333333",
            
            # Behavior
            "autoBlockScripts": True,
            "respectDNT": True,
            "cookieLifetimeDays": 365,
            "showBranding": True,
            
            # Detected cookies
            "cookies": {
                "necessary": categorized.get("necessary", []),
                "functional": categorized.get("functional", []),
                "analytics": categorized.get("analytics", []),
                "marketing": categorized.get("marketing", [])
            },
            
            # Analytics tools
            "tracking_tools": analytics,
            
            # Language
            "language": "de",
            "multiLanguage": True,
            
            # Consent mode
            "consentMode": "opt-in",  # DSGVO-konform
            
            # Advanced
            "logConsent": True,
            "consentAPI": True
        }
        
        return config
    
    def _categorize_cookies(self, cookies: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Kategorisiert Cookies in DSGVO-Kategorien
        """
        categorized = {
            "necessary": [],
            "functional": [],
            "analytics": [],
            "marketing": []
        }
        
        # Known cookie patterns
        necessary_patterns = ["PHPSESSID", "session", "csrf", "xsrf", "consent", "complyo"]
        analytics_patterns = ["_ga", "_gid", "_gat", "matomo", "piwik", "_pk"]
        marketing_patterns = ["_fbp", "_gcl", "fr", "tr", "ads", "doubleclick"]
        
        for cookie in cookies:
            name = cookie.get("name", "").lower()
            
            # Check patterns
            if any(pattern.lower() in name for pattern in necessary_patterns):
                categorized["necessary"].append(cookie.get("name"))
            elif any(pattern.lower() in name for pattern in analytics_patterns):
                categorized["analytics"].append(cookie.get("name"))
            elif any(pattern.lower() in name for pattern in marketing_patterns):
                categorized["marketing"].append(cookie.get("name"))
            else:
                # Default: functional
                categorized["functional"].append(cookie.get("name"))
        
        return categorized
    
    def _generate_fallback_integration_code(
        self,
        site_id: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Generiert Fallback-Integration-Code wenn kein WidgetManager
        """
        config_json = json.dumps(config, ensure_ascii=False)
        
        return f'''<!-- Complyo Cookie Consent Banner -->
<script 
  src="https://widgets.complyo.tech/cookie-banner-v2.0.0.min.js" 
  data-site-id="{site_id}"
  data-config='{config_json}'
  async
></script>
<!-- End Complyo Cookie Banner -->'''
    
    def _get_integration_instructions(self) -> str:
        """Gibt detaillierte Integrations-Anweisungen"""
        return """**Integration des Cookie-Banners:**

1. **Code einfügen**
   - Kopieren Sie den Widget-Code
   - Fügen Sie ihn VOR dem schließenden </body>-Tag ein
   - Am besten in Ihrer Haupt-Template-Datei (z.B. footer.php, base.html)

2. **Tracking-Scripts anpassen**
   - Google Analytics, Facebook Pixel, etc. dürfen NICHT automatisch geladen werden
   - Scripts müssen an Consent gekoppelt werden
   
   Beispiel für Google Analytics:
   ```html
   <script>
   window.addEventListener('ComplyoConsent', function(e) {
     if (e.detail.analytics) {
       // GA-Code hier
       gtag('config', 'GA_MEASUREMENT_ID');
     }
   });
   </script>
   ```

3. **Datenschutzerklärung aktualisieren**
   - Erwähnen Sie die Cookie-Kategorien
   - Link zum Widerruf der Einwilligung
   - Liste aller verwendeten Cookies

4. **Testen**
   - Löschen Sie Browser-Cookies
   - Laden Sie die Seite neu
   - Banner sollte erscheinen
   - Prüfen Sie, dass Tracking-Scripts erst nach Consent laden

5. **Anpassung (optional)**
   - Farben können im Config-Object angepasst werden
   - Layout: 'box_modal', 'banner_bottom', 'banner_top'
   - Sprache: 'de', 'en'"""
    
    def get_tracking_integration_example(self, tool: str) -> str:
        """Gibt Beispiel-Code für Tracking-Tool-Integration"""
        examples = {
            "google-analytics": '''<!-- Google Analytics mit Consent -->
<script>
window.addEventListener('ComplyoConsent', function(e) {
  if (e.detail.analytics) {
    // Google Analytics laden
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'GA_MEASUREMENT_ID');
    
    var script = document.createElement('script');
    script.src = 'https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID';
    script.async = true;
    document.head.appendChild(script);
  }
});
</script>''',
            
            "facebook-pixel": '''<!-- Facebook Pixel mit Consent -->
<script>
window.addEventListener('ComplyoConsent', function(e) {
  if (e.detail.marketing) {
    !function(f,b,e,v,n,t,s)
    {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
    n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];
    s.parentNode.insertBefore(t,s)}(window, document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', 'YOUR_PIXEL_ID');
    fbq('track', 'PageView');
  }
});
</script>''',
            
            "matomo": '''<!-- Matomo mit Consent -->
<script>
window.addEventListener('ComplyoConsent', function(e) {
  if (e.detail.analytics) {
    var _paq = window._paq = window._paq || [];
    _paq.push(['trackPageView']);
    _paq.push(['enableLinkTracking']);
    (function() {
      var u="//YOUR_MATOMO_URL/";
      _paq.push(['setTrackerUrl', u+'matomo.php']);
      _paq.push(['setSiteId', 'YOUR_SITE_ID']);
      var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
      g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
    })();
  }
});
</script>'''
        }
        
        return examples.get(tool, "<!-- Bitte Script an Consent koppeln -->")


