"""
TTDSG-Compliant Cookie Banner and Consent Management Platform (CMP)
Implementation according to German TTDSG § 25 and GDPR Article 7
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
import json

class CookieCategory(BaseModel):
    id: str
    name: str
    description: str
    required: bool
    enabled: bool = False

class ConsentRecord(BaseModel):
    consent_id: str
    user_identifier: str  # IP hash or user ID
    website_domain: str
    categories_consented: List[str]
    consent_timestamp: datetime
    expiry_date: datetime
    consent_string: str  # TCF-like consent string
    user_agent: str
    ip_hash: str
    withdrawal_date: Optional[datetime] = None
    is_valid: bool = True

class CookieBannerConfig(BaseModel):
    website_domain: str
    company_name: str
    privacy_policy_url: str
    imprint_url: str
    banner_position: str = "bottom"  # top, bottom, center
    banner_style: str = "compact"  # compact, detailed, overlay
    language: str = "de"
    categories: List[CookieCategory]
    legal_text: Optional[str] = None
    contact_email: str

class TTDSGCookieManager:
    """
    TTDSG-compliant Cookie Consent Management System
    """
    
    def __init__(self):
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.banner_configs: Dict[str, CookieBannerConfig] = {}
        self.predefined_categories = {
            "necessary": CookieCategory(
                id="necessary",
                name="Notwendige Cookies",
                description="Diese Cookies sind für das Funktionieren der Website erforderlich und können nicht deaktiviert werden.",
                required=True,
                enabled=True
            ),
            "analytics": CookieCategory(
                id="analytics",
                name="Analyse & Statistik",
                description="Diese Cookies helfen uns zu verstehen, wie Besucher mit der Website interagieren, indem Informationen anonym gesammelt werden.",
                required=False,
                enabled=False
            ),
            "marketing": CookieCategory(
                id="marketing", 
                name="Marketing & Werbung",
                description="Diese Cookies werden verwendet, um Ihnen relevante Werbung zu zeigen und die Effektivität von Werbekampagnen zu messen.",
                required=False,
                enabled=False
            ),
            "social_media": CookieCategory(
                id="social_media",
                name="Social Media",
                description="Diese Cookies ermöglichen es Ihnen, Inhalte in sozialen Netzwerken zu teilen und sich mit diesen zu verbinden.",
                required=False,
                enabled=False
            ),
            "personalization": CookieCategory(
                id="personalization",
                name="Personalisierung",
                description="Diese Cookies ermöglichen es der Website, sich an Ihre Präferenzen zu erinnern und Ihnen ein personalisiertes Erlebnis zu bieten.",
                required=False,
                enabled=False
            )
        }
    
    def create_banner_config(self, config_data: Dict[str, Any]) -> CookieBannerConfig:
        """Create a new cookie banner configuration"""
        
        # Use predefined categories if not specified
        if "categories" not in config_data:
            categories = list(self.predefined_categories.values())
        else:
            categories = [
                CookieCategory(**cat) if isinstance(cat, dict) else cat 
                for cat in config_data["categories"]
            ]
        
        config = CookieBannerConfig(
            website_domain=config_data["website_domain"],
            company_name=config_data["company_name"],
            privacy_policy_url=config_data.get("privacy_policy_url", "/datenschutz"),
            imprint_url=config_data.get("imprint_url", "/impressum"),
            banner_position=config_data.get("banner_position", "bottom"),
            banner_style=config_data.get("banner_style", "compact"),
            language=config_data.get("language", "de"),
            categories=categories,
            contact_email=config_data.get("contact_email", "datenschutz@example.com")
        )
        
        self.banner_configs[config.website_domain] = config
        return config
    
    def generate_banner_html(self, domain: str) -> str:
        """Generate TTDSG-compliant cookie banner HTML"""
        
        config = self.banner_configs.get(domain)
        if not config:
            raise ValueError(f"No banner configuration found for domain: {domain}")
        
        # Generate category checkboxes
        category_html = ""
        for category in config.categories:
            if category.required:
                category_html += f"""
                <div class="cookie-category">
                    <label class="cookie-category-label required">
                        <input type="checkbox" checked disabled class="cookie-checkbox">
                        <span class="cookie-category-name">{category.name}</span>
                        <span class="required-badge">Erforderlich</span>
                    </label>
                    <p class="cookie-category-description">{category.description}</p>
                </div>
                """
            else:
                category_html += f"""
                <div class="cookie-category">
                    <label class="cookie-category-label">
                        <input type="checkbox" name="cookie-category" value="{category.id}" class="cookie-checkbox">
                        <span class="cookie-category-name">{category.name}</span>
                    </label>
                    <p class="cookie-category-description">{category.description}</p>
                </div>
                """
        
        banner_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        /* TTDSG Cookie Banner Styles */
        #complyo-cookie-banner {{
            position: fixed;
            {config.banner_position}: 0;
            left: 0;
            right: 0;
            background: rgba(255, 255, 255, 0.98);
            border-top: 3px solid #2563eb;
            padding: 20px;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
            z-index: 999999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            color: #374151;
            backdrop-filter: blur(10px);
        }}
        
        .cookie-banner-content {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .cookie-banner-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .cookie-icon {{
            width: 24px;
            height: 24px;
            margin-right: 10px;
        }}
        
        .cookie-banner-title {{
            font-size: 18px;
            font-weight: 600;
            color: #1f2937;
        }}
        
        .cookie-banner-text {{
            margin-bottom: 20px;
            color: #4b5563;
        }}
        
        .cookie-categories {{
            display: none;
            margin-bottom: 20px;
            padding: 15px;
            background: #f9fafb;
            border-radius: 8px;
        }}
        
        .cookie-categories.open {{
            display: block;
        }}
        
        .cookie-category {{
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .cookie-category:last-child {{
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
        }}
        
        .cookie-category-label {{
            display: flex;
            align-items: center;
            font-weight: 500;
            cursor: pointer;
        }}
        
        .cookie-category-label.required {{
            cursor: default;
        }}
        
        .cookie-checkbox {{
            margin-right: 10px;
            accent-color: #2563eb;
        }}
        
        .required-badge {{
            background: #dc2626;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
            margin-left: 8px;
        }}
        
        .cookie-category-description {{
            margin: 8px 0 0 24px;
            font-size: 12px;
            color: #6b7280;
        }}
        
        .cookie-banner-actions {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }}
        
        .cookie-btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .cookie-btn-accept-all {{
            background: #2563eb;
            color: white;
        }}
        
        .cookie-btn-accept-all:hover {{
            background: #1d4ed8;
        }}
        
        .cookie-btn-accept-selected {{
            background: #10b981;
            color: white;
        }}
        
        .cookie-btn-accept-selected:hover {{
            background: #059669;
        }}
        
        .cookie-btn-reject {{
            background: #f3f4f6;
            color: #374151;
            border: 1px solid #d1d5db;
        }}
        
        .cookie-btn-reject:hover {{
            background: #e5e7eb;
        }}
        
        .cookie-btn-settings {{
            background: transparent;
            color: #2563eb;
            text-decoration: underline;
            padding: 0;
        }}
        
        .cookie-btn-settings:hover {{
            color: #1d4ed8;
        }}
        
        .cookie-legal-links {{
            margin-left: auto;
            font-size: 12px;
        }}
        
        .cookie-legal-links a {{
            color: #2563eb;
            text-decoration: none;
            margin-left: 15px;
        }}
        
        .cookie-legal-links a:hover {{
            text-decoration: underline;
        }}
        
        /* Dark theme support */
        @media (prefers-color-scheme: dark) {{
            #complyo-cookie-banner {{
                background: rgba(17, 24, 39, 0.98);
                color: #f3f4f6;
            }}
            
            .cookie-banner-title {{
                color: #f9fafb;
            }}
            
            .cookie-banner-text {{
                color: #d1d5db;
            }}
            
            .cookie-categories {{
                background: #1f2937;
            }}
            
            .cookie-category {{
                border-bottom-color: #374151;
            }}
            
            .cookie-category-description {{
                color: #9ca3af;
            }}
        }}
        
        /* Mobile responsive */
        @media (max-width: 768px) {{
            #complyo-cookie-banner {{
                padding: 15px;
            }}
            
            .cookie-banner-actions {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .cookie-btn {{
                width: 100%;
                text-align: center;
            }}
            
            .cookie-legal-links {{
                margin: 10px 0 0 0;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div id="complyo-cookie-banner">
        <div class="cookie-banner-content">
            <div class="cookie-banner-header">
                <svg class="cookie-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <h3 class="cookie-banner-title">Cookie-Einstellungen</h3>
            </div>
            
            <div class="cookie-banner-text">
                Wir verwenden Cookies, um Ihnen die bestmögliche Nutzung unserer Website zu ermöglichen. 
                Notwendige Cookies sind für das Funktionieren der Website erforderlich. Mit Ihrer Zustimmung verwenden wir auch Cookies für Analyse und Marketing.
                Weitere Informationen finden Sie in unserer 
                <a href="{config.privacy_policy_url}" target="_blank">Datenschutzerklärung</a>.
            </div>
            
            <div id="cookie-categories" class="cookie-categories">
                {category_html}
            </div>
            
            <div class="cookie-banner-actions">
                <button class="cookie-btn cookie-btn-accept-all" onclick="acceptAllCookies()">
                    Alle akzeptieren
                </button>
                <button class="cookie-btn cookie-btn-accept-selected" onclick="acceptSelectedCookies()">
                    Auswahl akzeptieren
                </button>
                <button class="cookie-btn cookie-btn-reject" onclick="rejectOptionalCookies()">
                    Nur notwendige
                </button>
                <button class="cookie-btn cookie-btn-settings" onclick="toggleCookieSettings()">
                    Einstellungen
                </button>
                
                <div class="cookie-legal-links">
                    <a href="{config.privacy_policy_url}" target="_blank">Datenschutz</a>
                    <a href="{config.imprint_url}" target="_blank">Impressum</a>
                </div>
            </div>
        </div>
    </div>

    <script>
        // TTDSG Cookie Consent Management
        const COMPLYO_CMP = {{
            version: '1.0.0',
            domain: '{domain}',
            categories: {json.dumps([cat.dict() for cat in config.categories])},
            
            // Initialize the banner
            init: function() {{
                const existingConsent = this.getStoredConsent();
                if (!existingConsent || this.isConsentExpired(existingConsent)) {{
                    this.showBanner();
                }} else {{
                    this.applyStoredConsent(existingConsent);
                }}
            }},
            
            // Show the cookie banner
            showBanner: function() {{
                document.getElementById('complyo-cookie-banner').style.display = 'block';
            }},
            
            // Hide the cookie banner  
            hideBanner: function() {{
                document.getElementById('complyo-cookie-banner').style.display = 'none';
            }},
            
            // Get stored consent from localStorage
            getStoredConsent: function() {{
                try {{
                    const stored = localStorage.getItem('complyo_consent_' + this.domain);
                    return stored ? JSON.parse(stored) : null;
                }} catch (e) {{
                    return null;
                }}
            }},
            
            // Check if consent is expired (1 year)
            isConsentExpired: function(consent) {{
                const expiry = new Date(consent.expiry_date);
                return new Date() > expiry;
            }},
            
            // Store consent in localStorage
            storeConsent: function(categories, consentType) {{
                const consent = {{
                    consent_id: this.generateUUID(),
                    categories: categories,
                    consent_type: consentType,
                    timestamp: new Date().toISOString(),
                    expiry_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // 1 year
                    user_agent: navigator.userAgent,
                    domain: this.domain
                }};
                
                localStorage.setItem('complyo_consent_' + this.domain, JSON.stringify(consent));
                return consent;
            }},
            
            // Apply stored consent settings
            applyStoredConsent: function(consent) {{
                // Enable/disable cookies based on consent
                consent.categories.forEach(categoryId => {{
                    this.enableCookieCategory(categoryId);
                }});
                
                // Trigger consent events
                this.fireConsentEvent('consent_applied', consent);
            }},
            
            // Enable specific cookie category
            enableCookieCategory: function(categoryId) {{
                // This would typically enable/load scripts for the category
                console.log('Enabling cookie category:', categoryId);
                
                // Example: Load analytics if consented
                if (categoryId === 'analytics') {{
                    this.loadAnalytics();
                }}
                
                // Example: Load marketing cookies if consented
                if (categoryId === 'marketing') {{
                    this.loadMarketing();
                }}
            }},
            
            // Load analytics scripts
            loadAnalytics: function() {{
                // Example: Google Analytics
                // gtag('config', 'GA_MEASUREMENT_ID');
                console.log('Analytics cookies enabled');
            }},
            
            // Load marketing scripts
            loadMarketing: function() {{
                // Example: Facebook Pixel, Google Ads
                console.log('Marketing cookies enabled');
            }},
            
            // Fire consent events
            fireConsentEvent: function(eventType, data) {{
                const event = new CustomEvent('complyo_consent', {{
                    detail: {{ type: eventType, data: data }}
                }});
                document.dispatchEvent(event);
            }},
            
            // Generate UUID for consent ID
            generateUUID: function() {{
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {{
                    const r = Math.random() * 16 | 0;
                    const v = c == 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                }});
            }},
            
            // Send consent to server
            sendConsentToServer: function(consent) {{
                fetch('/api/cookie-consent', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify(consent)
                }}).catch(err => console.log('Consent logging failed:', err));
            }}
        }};
        
        // Global functions for banner buttons
        function acceptAllCookies() {{
            const allCategories = COMPLYO_CMP.categories.map(cat => cat.id);
            const consent = COMPLYO_CMP.storeConsent(allCategories, 'accept_all');
            COMPLYO_CMP.applyStoredConsent(consent);
            COMPLYO_CMP.sendConsentToServer(consent);
            COMPLYO_CMP.hideBanner();
            COMPLYO_CMP.fireConsentEvent('consent_given', consent);
        }}
        
        function acceptSelectedCookies() {{
            const selectedCategories = ['necessary']; // Always include necessary
            const checkboxes = document.querySelectorAll('input[name="cookie-category"]:checked');
            checkboxes.forEach(cb => selectedCategories.push(cb.value));
            
            const consent = COMPLYO_CMP.storeConsent(selectedCategories, 'accept_selected');
            COMPLYO_CMP.applyStoredConsent(consent);
            COMPLYO_CMP.sendConsentToServer(consent);
            COMPLYO_CMP.hideBanner();
            COMPLYO_CMP.fireConsentEvent('consent_given', consent);
        }}
        
        function rejectOptionalCookies() {{
            const consent = COMPLYO_CMP.storeConsent(['necessary'], 'reject_optional');
            COMPLYO_CMP.applyStoredConsent(consent);
            COMPLYO_CMP.sendConsentToServer(consent);
            COMPLYO_CMP.hideBanner();
            COMPLYO_CMP.fireConsentEvent('consent_given', consent);
        }}
        
        function toggleCookieSettings() {{
            const categories = document.getElementById('cookie-categories');
            categories.classList.toggle('open');
        }}
        
        // Initialize the CMP when DOM is ready
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', function() {{
                COMPLYO_CMP.init();
            }});
        }} else {{
            COMPLYO_CMP.init();
        }}
        
        // Expose CMP globally for external access
        window.COMPLYO_CMP = COMPLYO_CMP;
    </script>
</body>
</html>
        """
        
        return banner_html.strip()
    
    def record_consent(self, consent_data: Dict[str, Any]) -> ConsentRecord:
        """Record user consent in compliance with TTDSG"""
        
        consent_id = str(uuid.uuid4())
        consent_record = ConsentRecord(
            consent_id=consent_id,
            user_identifier=consent_data.get("user_identifier", "anonymous"),
            website_domain=consent_data["website_domain"],
            categories_consented=consent_data["categories_consented"],
            consent_timestamp=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=365),  # 1 year expiry
            consent_string=self._generate_consent_string(consent_data["categories_consented"]),
            user_agent=consent_data.get("user_agent", ""),
            ip_hash=consent_data.get("ip_hash", "")
        )
        
        self.consent_records[consent_id] = consent_record
        return consent_record
    
    def withdraw_consent(self, consent_id: str) -> bool:
        """Withdraw previously given consent"""
        
        if consent_id in self.consent_records:
            self.consent_records[consent_id].withdrawal_date = datetime.now()
            self.consent_records[consent_id].is_valid = False
            return True
        return False
    
    def get_consent_status(self, user_identifier: str, domain: str) -> Optional[ConsentRecord]:
        """Get current consent status for a user"""
        
        # Find most recent valid consent for user/domain
        user_consents = [
            record for record in self.consent_records.values()
            if record.user_identifier == user_identifier 
            and record.website_domain == domain 
            and record.is_valid
            and record.expiry_date > datetime.now()
        ]
        
        if user_consents:
            return max(user_consents, key=lambda x: x.consent_timestamp)
        
        return None
    
    def generate_consent_report(self, domain: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate consent compliance report for a domain"""
        
        domain_consents = [
            record for record in self.consent_records.values()
            if record.website_domain == domain
            and start_date <= record.consent_timestamp <= end_date
        ]
        
        total_consents = len(domain_consents)
        valid_consents = len([r for r in domain_consents if r.is_valid])
        withdrawn_consents = len([r for r in domain_consents if r.withdrawal_date])
        
        # Category statistics
        category_stats = {}
        for record in domain_consents:
            for category in record.categories_consented:
                category_stats[category] = category_stats.get(category, 0) + 1
        
        return {
            "domain": domain,
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_consents": total_consents,
            "valid_consents": valid_consents,
            "withdrawn_consents": withdrawn_consents,
            "consent_rate": (valid_consents / total_consents * 100) if total_consents > 0 else 0,
            "category_statistics": category_stats,
            "compliance_status": "TTDSG compliant" if total_consents > 0 else "No consents recorded"
        }
    
    def _generate_consent_string(self, categories: List[str]) -> str:
        """Generate TCF-like consent string"""
        
        # Simplified consent string - in production, use IAB TCF format
        consent_bits = ""
        for cat_id in ["necessary", "analytics", "marketing", "social_media", "personalization"]:
            consent_bits += "1" if cat_id in categories else "0"
        
        return f"v1.{consent_bits}.{int(datetime.now().timestamp())}"
    
    def get_javascript_integration(self, domain: str) -> str:
        """Get JavaScript code for easy website integration"""
        
        return f"""
<!-- Complyo Cookie Consent Integration -->
<script>
(function() {{
    const script = document.createElement('script');
    script.src = '/api/cookie-banner/{domain}';
    script.async = true;
    document.head.appendChild(script);
}})();
</script>

<!-- Optional: Listen to consent events -->
<script>
document.addEventListener('complyo_consent', function(event) {{
    const {{ type, data }} = event.detail;
    console.log('Cookie consent event:', type, data);
    
    // Your custom logic here
    if (type === 'consent_given') {{
        // Enable tracking, analytics, etc.
    }}
}});
</script>
        """.strip()

# Global cookie manager instance
ttdsg_cookie_manager = TTDSGCookieManager()