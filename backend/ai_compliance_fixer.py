"""
Complyo KI-Automation Engine
AI-powered compliance fixes using GPT-4 and Claude integration
"""

import os
import json
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from bs4 import BeautifulSoup
import re

@dataclass
class ComplianceFix:
    """Represents a single compliance fix"""
    issue_category: str
    fix_type: str  # "text_generation", "code_modification", "banner_integration"
    description: str
    generated_content: str
    implementation_instructions: str
    confidence_score: float
    estimated_time_minutes: int
    auto_applicable: bool

@dataclass
class AIFixResult:
    """Result of AI-powered compliance fixing"""
    scan_id: str
    total_issues_fixed: int
    fixes_applied: List[ComplianceFix]
    generated_files: Dict[str, str]  # filename -> content
    implementation_guide: List[str]
    estimated_total_time: int
    success_rate: float

class AIComplianceFixer:
    """AI-powered compliance automation engine"""
    
    def __init__(self):
        self.openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Legal text templates and patterns
        self.legal_templates = self._load_legal_templates()
        
    def _load_legal_templates(self) -> Dict[str, str]:
        """Load legal document templates"""
        return {
            "impressum": {
                "template": """# Impressum

## Angaben gemäß § 5 TMG

**Verantwortlich für den Inhalt:**
{company_name}
{address}
{postal_code} {city}

**Kontakt:**
Telefon: {phone}
E-Mail: {email}

{registration_info}

**Umsatzsteuer-Identifikationsnummer gemäß §27a Umsatzsteuergesetz:**
{vat_id}

**Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV:**
{responsible_person}
{address}
{postal_code} {city}
""",
                "required_fields": ["company_name", "address", "postal_code", "city", "phone", "email"]
            },
            "privacy_policy": {
                "template": """# Datenschutzerklärung

## 1. Datenschutz auf einen Blick

### Allgemeine Hinweise
Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen.

### Datenerfassung auf dieser Website
Die Datenverarbeitung auf dieser Website erfolgt durch den Websitebetreiber. Dessen Kontaktdaten können Sie dem Impressum dieser Website entnehmen.

## 2. Allgemeine Hinweise und Pflichtinformationen

### Datenschutz
Die Betreiber dieser Seiten nehmen den Schutz Ihrer persönlichen Daten sehr ernst. Wir behandeln Ihre personenbezogenen Daten vertraulich und entsprechend der gesetzlichen Datenschutzvorschriften sowie dieser Datenschutzerklärung.

### Hinweis zur verantwortlichen Stelle
Die verantwortliche Stelle für die Datenverarbeitung auf dieser Website ist:

{company_info}

Verantwortliche Stelle ist die natürliche oder juristische Person, die allein oder gemeinsam mit anderen über die Zwecke und Mittel der Verarbeitung von personenbezogenen Daten entscheidet.

## 3. Datenerfassung auf dieser Website

### Server-Log-Dateien
Der Provider der Seiten erhebt und speichert automatisch Informationen in so genannten Server-Log-Dateien, die Ihr Browser automatisch an uns übermittelt.

### Kontaktformular
Wenn Sie uns per Kontaktformular Anfragen zukommen lassen, werden Ihre Angaben aus dem Anfrageformular inklusive der von Ihnen dort angegebenen Kontaktdaten zwecks Bearbeitung der Anfrage und für den Fall von Anschlussfragen bei uns gespeichert.

## 4. Ihre Rechte

Sie haben jederzeit das Recht unentgeltlich Auskunft über Herkunft, Empfänger und Zweck Ihrer gespeicherten personenbezogenen Daten zu erhalten. Sie haben außerdem ein Recht, die Berichtigung, Sperrung oder Löschung dieser Daten zu verlangen.

Stand: {current_date}
""",
                "required_fields": ["company_info"]
            }
        }
    
    async def fix_compliance_issues(self, scan_id: str, violations: List[Dict[str, Any]], 
                                  company_info: Dict[str, str] = None) -> AIFixResult:
        """
        AI-powered fixing of compliance issues
        
        Args:
            scan_id: ID of the compliance scan
            violations: List of violations from compliance scanner  
            company_info: Company information for generating legal texts
        """
        fixes_applied = []
        generated_files = {}
        
        try:
            # Group violations by category for batch processing
            violations_by_category = self._group_violations_by_category(violations)
            
            # Process each category
            for category, category_violations in violations_by_category.items():
                if category.lower() in ['impressum', 'datenschutz']:
                    # Generate legal texts
                    fix = await self._generate_legal_text(category, category_violations, company_info)
                    if fix:
                        fixes_applied.append(fix)
                        generated_files[f"{category.lower()}.html"] = fix.generated_content
                        
                elif category.lower() in ['cookie-compliance', 'cookie compliance']:
                    # Generate cookie banner
                    fix = await self._generate_cookie_banner(category_violations)
                    if fix:
                        fixes_applied.append(fix)
                        generated_files["cookie-banner.html"] = fix.generated_content
                        generated_files["cookie-banner.js"] = self._generate_cookie_script()
                        
                elif category.lower() in ['barrierefreiheit', 'accessibility']:
                    # Generate accessibility fixes
                    fix = await self._generate_accessibility_fixes(category_violations)
                    if fix:
                        fixes_applied.append(fix)
                        
                else:
                    # Generic AI-powered fix
                    fix = await self._generate_generic_fix(category, category_violations)
                    if fix:
                        fixes_applied.append(fix)
            
            # Generate implementation guide
            implementation_guide = self._generate_implementation_guide(fixes_applied)
            
            # Calculate success metrics
            total_issues_fixed = len(fixes_applied)
            estimated_total_time = sum(fix.estimated_time_minutes for fix in fixes_applied)
            success_rate = total_issues_fixed / len(violations) if violations else 0
            
            return AIFixResult(
                scan_id=scan_id,
                total_issues_fixed=total_issues_fixed,
                fixes_applied=fixes_applied,
                generated_files=generated_files,
                implementation_guide=implementation_guide,
                estimated_total_time=estimated_total_time,
                success_rate=success_rate
            )
            
        except Exception as e:
            # Return partial results on error
            return AIFixResult(
                scan_id=scan_id,
                total_issues_fixed=len(fixes_applied),
                fixes_applied=fixes_applied,
                generated_files=generated_files,
                implementation_guide=[f"Fehler bei der Generierung: {str(e)}"],
                estimated_total_time=0,
                success_rate=0
            )
    
    def _group_violations_by_category(self, violations: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Group violations by category"""
        grouped = {}
        for violation in violations:
            category = violation.get('category', 'Other')
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(violation)
        return grouped
    
    async def _generate_legal_text(self, category: str, violations: List[Dict], 
                                 company_info: Dict[str, str] = None) -> Optional[ComplianceFix]:
        """Generate legal text (Impressum/Datenschutzerklärung)"""
        if not company_info:
            company_info = {
                "company_name": "[FIRMENNAME EINTRAGEN]",
                "address": "[ADRESSE EINTRAGEN]",
                "postal_code": "[PLZ]",
                "city": "[STADT]",
                "phone": "[TELEFON]",
                "email": "[EMAIL]",
                "vat_id": "[UST-ID]",
                "responsible_person": "[VERANTWORTLICHE PERSON]"
            }
        
        category_lower = category.lower()
        
        if category_lower == 'impressum':
            template = self.legal_templates["impressum"]["template"]
            
            # Add registration info based on company type
            registration_info = """**Handelsregister:**
Registergericht: [REGISTERGERICHT]
Registernummer: [HRB/HRA NUMMER]"""
            
            generated_content = template.format(
                company_name=company_info.get("company_name", "[FIRMENNAME]"),
                address=company_info.get("address", "[ADRESSE]"),
                postal_code=company_info.get("postal_code", "[PLZ]"),
                city=company_info.get("city", "[STADT]"),
                phone=company_info.get("phone", "[TELEFON]"),
                email=company_info.get("email", "[EMAIL]"),
                vat_id=company_info.get("vat_id", "[UST-ID]"),
                responsible_person=company_info.get("responsible_person", "[VERANTWORTLICHE PERSON]"),
                registration_info=registration_info
            )
            
            return ComplianceFix(
                issue_category="Impressum",
                fix_type="text_generation",
                description="Vollständiges Impressum nach TMG § 5 generiert",
                generated_content=generated_content,
                implementation_instructions="1. Datei 'impressum.html' auf Server hochladen\n2. Link zu /impressum im Footer hinzufügen\n3. Platzhalter durch echte Unternehmensdaten ersetzen",
                confidence_score=0.95,
                estimated_time_minutes=10,
                auto_applicable=True
            )
            
        elif category_lower == 'datenschutz':
            template = self.legal_templates["privacy_policy"]["template"]
            
            company_info_text = f"""**{company_info.get("company_name", "[FIRMENNAME]")}**
{company_info.get("address", "[ADRESSE]")}
{company_info.get("postal_code", "[PLZ]")} {company_info.get("city", "[STADT]")}

Telefon: {company_info.get("phone", "[TELEFON]")}
E-Mail: {company_info.get("email", "[EMAIL]")}"""
            
            generated_content = template.format(
                company_info=company_info_text,
                current_date=datetime.now().strftime("%d.%m.%Y")
            )
            
            # Enhance with AI for more detailed privacy policy
            enhanced_content = await self._enhance_privacy_policy_with_ai(generated_content, violations)
            
            return ComplianceFix(
                issue_category="Datenschutz",
                fix_type="text_generation", 
                description="DSGVO-konforme Datenschutzerklärung generiert",
                generated_content=enhanced_content or generated_content,
                implementation_instructions="1. Datei 'datenschutz.html' auf Server hochladen\n2. Link zu /datenschutz im Footer hinzufügen\n3. Spezifische Datenverarbeitungen ergänzen",
                confidence_score=0.90,
                estimated_time_minutes=15,
                auto_applicable=True
            )
        
        return None
    
    async def _enhance_privacy_policy_with_ai(self, base_content: str, violations: List[Dict]) -> Optional[str]:
        """Enhance privacy policy using AI based on specific violations"""
        if not self.openrouter_api_key:
            return None
            
        try:
            prompt = f"""
Du bist ein Experte für deutsche Datenschutzrecht (DSGVO). Erweitere die folgende Datenschutzerklärung basierend auf den gefundenen Compliance-Verstößen:

AKTUELLE DATENSCHUTZERKLÄRUNG:
{base_content}

GEFUNDENE VERSTÖSSE:
{json.dumps(violations, indent=2, ensure_ascii=False)}

Erweitere die Datenschutzerklärung um folgende Punkte:
1. Spezifische Abschnitte für die gefundenen Datenschutz-Verstöße
2. Konkrete Rechtsgrundlagen (DSGVO Artikel)
3. Detaillierte Informationen zu Cookies und Tracking
4. Betroffenenrechte vollständig ausformulieren
5. Kontaktdaten für Datenschutzanfragen

Schreibe auf Deutsch und folge der DSGVO strikt. Markiere Platzhalter mit [PLATZHALTER].
"""
            
            enhanced = await self._call_ai_api(prompt, model="gpt-4")
            return enhanced if enhanced else None
            
        except Exception as e:
            print(f"AI enhancement failed: {e}")
            return None
    
    async def _generate_cookie_banner(self, violations: List[Dict]) -> Optional[ComplianceFix]:
        """Generate GDPR-compliant cookie banner"""
        
        cookie_banner_html = """
<div id="cookie-banner" class="cookie-banner" style="display: none;">
    <div class="cookie-banner-content">
        <h3>🍪 Diese Website verwendet Cookies</h3>
        <p>
            Wir verwenden Cookies, um Ihnen ein optimales Website-Erlebnis zu bieten. 
            Dazu gehören notwendige Cookies für den Betrieb der Website sowie optionale 
            Cookies für Komfort und Analyse. Sie können selbst entscheiden, welche 
            Kategorien Sie zulassen möchten.
        </p>
        
        <div class="cookie-categories">
            <label class="cookie-category">
                <input type="checkbox" id="necessary-cookies" checked disabled>
                <span>Notwendige Cookies (immer aktiv)</span>
            </label>
            
            <label class="cookie-category">
                <input type="checkbox" id="analytics-cookies">
                <span>Analyse & Statistik Cookies</span>
            </label>
            
            <label class="cookie-category">
                <input type="checkbox" id="marketing-cookies">
                <span>Marketing & Personalisierung</span>
            </label>
        </div>
        
        <div class="cookie-banner-buttons">
            <button id="cookie-accept-all" class="cookie-btn cookie-btn-accept">
                Alle akzeptieren
            </button>
            <button id="cookie-accept-selected" class="cookie-btn cookie-btn-selected">
                Auswahl akzeptieren
            </button>
            <button id="cookie-reject-all" class="cookie-btn cookie-btn-reject">
                Nur notwendige
            </button>
        </div>
        
        <div class="cookie-banner-links">
            <a href="/datenschutz" target="_blank">Datenschutzerklärung</a> |
            <a href="/impressum" target="_blank">Impressum</a>
        </div>
    </div>
</div>

<style>
.cookie-banner {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #fff;
    border-top: 3px solid #007cba;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    z-index: 10000;
    padding: 20px;
    font-family: Arial, sans-serif;
}

.cookie-banner-content {
    max-width: 1200px;
    margin: 0 auto;
}

.cookie-categories {
    margin: 15px 0;
}

.cookie-category {
    display: block;
    margin: 8px 0;
    cursor: pointer;
}

.cookie-banner-buttons {
    margin: 15px 0;
}

.cookie-btn {
    margin: 5px 10px 5px 0;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
}

.cookie-btn-accept {
    background: #28a745;
    color: white;
}

.cookie-btn-selected {
    background: #007cba;
    color: white;
}

.cookie-btn-reject {
    background: #6c757d;
    color: white;
}

.cookie-banner-links {
    font-size: 12px;
    margin-top: 10px;
}

@media (max-width: 768px) {
    .cookie-banner {
        padding: 15px;
    }
    
    .cookie-btn {
        display: block;
        width: 100%;
        margin: 5px 0;
    }
}
</style>
"""
        
        return ComplianceFix(
            issue_category="Cookie-Compliance",
            fix_type="banner_integration",
            description="DSGVO-konformer Cookie-Banner mit Consent-Management",
            generated_content=cookie_banner_html,
            implementation_instructions="1. HTML-Code vor schließendem </body>-Tag einfügen\n2. JavaScript-Code einbinden\n3. Tracking-Skripte an Consent koppeln",
            confidence_score=0.92,
            estimated_time_minutes=20,
            auto_applicable=True
        )
    
    def _generate_cookie_script(self) -> str:
        """Generate cookie consent management JavaScript"""
        return """
// Complyo Cookie Consent Manager
class ComplyoCookieManager {
    constructor() {
        this.consentKey = 'complyo-cookie-consent';
        this.init();
    }
    
    init() {
        // Check if consent already given
        const consent = this.getConsent();
        if (!consent) {
            this.showBanner();
        } else {
            this.applyConsent(consent);
        }
        
        this.bindEvents();
    }
    
    showBanner() {
        const banner = document.getElementById('cookie-banner');
        if (banner) {
            banner.style.display = 'block';
        }
    }
    
    hideBanner() {
        const banner = document.getElementById('cookie-banner');
        if (banner) {
            banner.style.display = 'none';
        }
    }
    
    bindEvents() {
        // Accept all cookies
        document.getElementById('cookie-accept-all')?.addEventListener('click', () => {
            this.setConsent({
                necessary: true,
                analytics: true,
                marketing: true
            });
        });
        
        // Accept selected cookies
        document.getElementById('cookie-accept-selected')?.addEventListener('click', () => {
            this.setConsent({
                necessary: true,
                analytics: document.getElementById('analytics-cookies').checked,
                marketing: document.getElementById('marketing-cookies').checked
            });
        });
        
        // Reject all optional cookies
        document.getElementById('cookie-reject-all')?.addEventListener('click', () => {
            this.setConsent({
                necessary: true,
                analytics: false,
                marketing: false
            });
        });
    }
    
    setConsent(consent) {
        localStorage.setItem(this.consentKey, JSON.stringify(consent));
        this.applyConsent(consent);
        this.hideBanner();
    }
    
    getConsent() {
        const consent = localStorage.getItem(this.consentKey);
        return consent ? JSON.parse(consent) : null;
    }
    
    applyConsent(consent) {
        // Enable/disable Google Analytics
        if (consent.analytics) {
            this.enableGoogleAnalytics();
        }
        
        // Enable/disable marketing cookies
        if (consent.marketing) {
            this.enableMarketingCookies();
        }
        
        console.log('Cookie consent applied:', consent);
    }
    
    enableGoogleAnalytics() {
        // Example: Load Google Analytics if consented
        if (typeof gtag === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID';
            document.head.appendChild(script);
            
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'GA_MEASUREMENT_ID');
        }
    }
    
    enableMarketingCookies() {
        // Example: Enable marketing pixels/cookies
        console.log('Marketing cookies enabled');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ComplyoCookieManager();
});
"""
    
    async def _generate_accessibility_fixes(self, violations: List[Dict]) -> Optional[ComplianceFix]:
        """Generate accessibility fixes"""
        fix_content = """
/* Accessibility Fixes - Add to your CSS */

/* Improve focus visibility */
*:focus {
    outline: 2px solid #005fcc !important;
    outline-offset: 2px;
}

/* Skip navigation link */
.skip-nav {
    position: absolute;
    top: -40px;
    left: 6px;
    background: #000;
    color: #fff;
    padding: 8px;
    text-decoration: none;
    z-index: 10000;
}

.skip-nav:focus {
    top: 6px;
}

/* Ensure minimum color contrast */
body {
    color: #212529; /* Ensure good contrast */
}

/* Screen reader only text */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
}

/* Form improvements */
input:invalid {
    border-color: #dc3545;
}

input:valid {
    border-color: #28a745;
}

/* Button improvements */
button, .btn {
    min-height: 44px; /* Touch target size */
    min-width: 44px;
}

/* Image alt text reminder */
img:not([alt]) {
    border: 3px dashed red !important;
}
"""
        
        javascript_fixes = """
// Accessibility JavaScript fixes
document.addEventListener('DOMContentLoaded', function() {
    // Add alt text placeholders for missing images
    const imagesWithoutAlt = document.querySelectorAll('img:not([alt])');
    imagesWithoutAlt.forEach(img => {
        img.setAttribute('alt', 'Bild: Beschreibung fehlt');
        console.warn('Missing alt text for image:', img.src);
    });
    
    // Add labels for unlabeled inputs
    const unlabeledInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]');
    unlabeledInputs.forEach(input => {
        if (!input.getAttribute('aria-label') && !document.querySelector(`label[for="${input.id}"]`)) {
            input.setAttribute('aria-label', 'Eingabefeld');
        }
    });
    
    // Add skip navigation if not exists
    if (!document.querySelector('.skip-nav')) {
        const skipNav = document.createElement('a');
        skipNav.href = '#main';
        skipNav.className = 'skip-nav';
        skipNav.textContent = 'Zum Hauptinhalt springen';
        document.body.insertBefore(skipNav, document.body.firstChild);
    }
});
"""
        
        return ComplianceFix(
            issue_category="Barrierefreiheit",
            fix_type="code_modification",
            description="Automatische Verbesserungen der Barrierefreiheit (WCAG 2.1)",
            generated_content=f"/* CSS Fixes */\n{fix_content}\n\n/* JavaScript Fixes */\n<script>\n{javascript_fixes}\n</script>",
            implementation_instructions="1. CSS-Code in Stylesheet einbinden\n2. JavaScript vor schließendem </body> einfügen\n3. Fehlende Alt-Texte manuell ergänzen",
            confidence_score=0.85,
            estimated_time_minutes=25,
            auto_applicable=True
        )
    
    async def _generate_generic_fix(self, category: str, violations: List[Dict]) -> Optional[ComplianceFix]:
        """Generate generic fix using AI"""
        if not self.openrouter_api_key:
            return None
            
        try:
            prompt = f"""
Du bist ein Experte für deutsche Website-Compliance. Erstelle konkrete Lösungen für folgende Compliance-Verstöße:

KATEGORIE: {category}
VERSTÖSSE:
{json.dumps(violations, indent=2, ensure_ascii=False)}

Erstelle:
1. Konkrete Implementierungsschritte
2. Code-Beispiele (HTML/CSS/JavaScript) falls nötig
3. Rechtliche Hinweise
4. Zeitschätzung in Minuten

Antwort auf Deutsch, praxistauglich und rechtssicher.
"""
            
            ai_response = await self._call_ai_api(prompt, model="gpt-4")
            
            if ai_response:
                return ComplianceFix(
                    issue_category=category,
                    fix_type="ai_generated",
                    description=f"KI-generierte Lösung für {category}",
                    generated_content=ai_response,
                    implementation_instructions="Siehe generierte Lösung für Details",
                    confidence_score=0.80,
                    estimated_time_minutes=30,
                    auto_applicable=False
                )
                
        except Exception as e:
            print(f"Generic AI fix failed: {e}")
            
        return None
    
    async def _call_ai_api(self, prompt: str, model: str = "gpt-4") -> Optional[str]:
        """Call OpenRouter AI API"""
        if not self.openrouter_api_key:
            return None
            
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Du bist ein Experte für deutsche Website-Compliance und Rechtssicherheit."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/chat/completions", 
                                      headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        print(f"AI API error: {response.status}")
                        return None
        except Exception as e:
            print(f"AI API call failed: {e}")
            return None
    
    def _generate_implementation_guide(self, fixes: List[ComplianceFix]) -> List[str]:
        """Generate step-by-step implementation guide"""
        guide = [
            "# Complyo Compliance Implementation Guide",
            "## Automatisch generierte Lösungen",
            ""
        ]
        
        for i, fix in enumerate(fixes, 1):
            guide.extend([
                f"### {i}. {fix.issue_category}",
                f"**Beschreibung:** {fix.description}",
                f"**Geschätzte Zeit:** {fix.estimated_time_minutes} Minuten",
                f"**Automatisch anwendbar:** {'Ja' if fix.auto_applicable else 'Nein'}",
                "",
                "**Implementierung:**",
                fix.implementation_instructions,
                "",
                "---",
                ""
            ])
        
        guide.extend([
            "## Prioritäten-Reihenfolge:",
            "1. Impressum und Datenschutzerklärung (rechtlich verpflichtend)",
            "2. Cookie-Banner (bei Verwendung von Cookies/Tracking)",  
            "3. Barrierefreiheit (schrittweise Verbesserung)",
            "4. Weitere Optimierungen",
            "",
            "## Support:",
            "Bei Fragen zur Implementierung wenden Sie sich an support@complyo.tech"
        ])
        
        return guide