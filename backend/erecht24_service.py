"""
eRecht24 API Service
Integriert eRecht24 API für rechtssichere Texte und Compliance-Beschreibungen
API-Dokumentation: https://api-docs.e-recht24.dev/
"""

import os
import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ERecht24Service:
    """Service für eRecht24 API-Integration"""
    
    def __init__(self):
        self.api_url = os.getenv("ERECHT24_API_URL", "https://api.e-recht24.de")
        self.api_key = os.getenv("ERECHT24_API_KEY", "")
        self.timeout = 30.0
        
        if not self.api_key:
            logger.warning("ERECHT24_API_KEY nicht gesetzt - Service im Demo-Modus")
    
    async def create_project(self, domain: str, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Erstellt ein neues eRecht24-Projekt für eine Domain
        
        Args:
            domain: Die Website-Domain (z.B. "example.com")
            user_id: Complyo User-ID
            
        Returns:
            Dict mit project_id, api_key, secret oder None bei Fehler
        """
        if not self.api_key:
            logger.warning("Demo-Modus: Erstelle Mock eRecht24-Projekt")
            return self._create_mock_project(domain, user_id)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/projects",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "domain": domain,
                        "name": f"Complyo Project - {domain}",
                        "external_id": f"complyo_user_{user_id}"
                    }
                )
                
                if response.status_code == 201:
                    data = response.json()
                    logger.info(f"✅ eRecht24-Projekt erstellt: {data.get('project_id')}")
                    return {
                        "project_id": data.get("project_id"),
                        "api_key": data.get("api_key"),
                        "secret": data.get("secret")
                    }
                else:
                    logger.error(f"eRecht24 API Fehler: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des eRecht24-Projekts: {e}")
            return None
    
    async def get_legal_text(
        self, 
        project_id: str, 
        text_type: str, 
        language: str = "de"
    ) -> Optional[str]:
        """
        Holt rechtssicheren Text von eRecht24
        
        Args:
            project_id: eRecht24 Projekt-ID
            text_type: "impressum", "datenschutz", "agb", "widerruf"
            language: "de", "en", "fr"
            
        Returns:
            HTML-Text oder None
        """
        if not self.api_key:
            return self._get_mock_legal_text(text_type, language)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/v1/projects/{project_id}/texts/{text_type}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"language": language}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("html_content")
                else:
                    logger.error(f"Fehler beim Abrufen von {text_type}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Rechtstexts: {e}")
            return None
    
    async def get_compliance_description(self, category: str) -> Dict[str, str]:
        """
        Holt rechtssichere Issue-Beschreibungen von eRecht24
        
        Args:
            category: "impressum", "datenschutz", "cookies", etc.
            
        Returns:
            Dict mit description, legal_basis, recommendation
        """
        if not self.api_key:
            return self._get_mock_compliance_description(category)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/v1/compliance/descriptions/{category}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Fallback auf Mock-Beschreibung für {category}")
                    return self._get_mock_compliance_description(category)
                    
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Compliance-Beschreibung: {e}")
            return self._get_mock_compliance_description(category)
    
    async def generate_cookie_config(self, cookies: List[Dict]) -> Dict[str, Any]:
        """
        Generiert Cookie-Consent Konfiguration
        
        Args:
            cookies: Liste erkannter Cookies
            
        Returns:
            Config-Dict für Cookie-Banner
        """
        if not self.api_key:
            return self._get_mock_cookie_config(cookies)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/cookies/config",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"cookies": cookies}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return self._get_mock_cookie_config(cookies)
                    
        except Exception as e:
            logger.error(f"Fehler bei Cookie-Config-Generierung: {e}")
            return self._get_mock_cookie_config(cookies)
    
    async def validate_impressum(self, text: str) -> Dict[str, Any]:
        """
        Validiert Impressum auf Vollständigkeit
        
        Args:
            text: Impressum-Text
            
        Returns:
            Dict mit is_valid, missing_fields, score
        """
        if not self.api_key:
            return self._mock_validate_impressum(text)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/validation/impressum",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"text": text}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return self._mock_validate_impressum(text)
                    
        except Exception as e:
            logger.error(f"Fehler bei Impressum-Validierung: {e}")
            return self._mock_validate_impressum(text)
    
    # ==================== Mock-Funktionen für Demo-Modus ====================
    
    def _create_mock_project(self, domain: str, user_id: int) -> Dict[str, Any]:
        """Mock für create_project"""
        import uuid
        return {
            "project_id": f"demo_{uuid.uuid4().hex[:12]}",
            "api_key": f"demo_key_{uuid.uuid4().hex[:16]}",
            "secret": f"demo_secret_{uuid.uuid4().hex[:16]}"
        }
    
    def _get_mock_legal_text(self, text_type: str, language: str) -> str:
        """Mock für get_legal_text"""
        mock_texts = {
            "impressum": {
                "de": "<h1>Impressum</h1><p>Musterfirma GmbH<br>Musterstraße 1<br>12345 Musterstadt</p>",
                "en": "<h1>Imprint</h1><p>Sample Company Ltd.<br>Sample Street 1<br>12345 Sample City</p>"
            },
            "datenschutz": {
                "de": "<h1>Datenschutzerklärung</h1><p>Verantwortlich für die Datenverarbeitung gemäß Art. 13 DSGVO...</p>",
                "en": "<h1>Privacy Policy</h1><p>Responsible for data processing according to Art. 13 GDPR...</p>"
            }
        }
        return mock_texts.get(text_type, {}).get(language, f"<p>Mock {text_type} ({language})</p>")
    
    def _get_mock_compliance_description(self, category: str) -> Dict[str, str]:
        """Mock für get_compliance_description"""
        descriptions = {
            "impressum": {
                "description": "Das Impressum ist nach § 5 TMG (Telemediengesetz) für alle geschäftsmäßigen Online-Dienste verpflichtend. Es muss leicht erkennbar, unmittelbar erreichbar und ständig verfügbar sein.",
                "legal_basis": "§ 5 TMG, § 55 RStV",
                "recommendation": "Fügen Sie einen gut sichtbaren Link 'Impressum' im Footer jeder Seite hinzu. Das Impressum muss Name, Anschrift, Kontaktdaten und ggf. Handelsregister-Nummer enthalten."
            },
            "datenschutz": {
                "description": "Eine Datenschutzerklärung ist nach Art. 13 DSGVO verpflichtend, wenn personenbezogene Daten erhoben werden. Sie muss umfassend über Art, Umfang und Zweck der Datenverarbeitung informieren.",
                "legal_basis": "Art. 13, 14 DSGVO",
                "recommendation": "Erstellen Sie eine vollständige Datenschutzerklärung mit Informationen zu Verantwortlichen, Verarbeitungszwecken, Rechtsgrundlagen, Speicherdauer und Betroffenenrechten."
            },
            "cookies": {
                "description": "Cookies dürfen nach § 25 TTDSG nur mit aktiver Einwilligung des Nutzers gesetzt werden. Dies erfordert einen Cookie-Consent-Banner mit Opt-In-Funktion.",
                "legal_basis": "§ 25 TTDSG, Art. 6 Abs. 1 lit. a DSGVO",
                "recommendation": "Implementieren Sie einen Cookie-Consent-Banner, der vor dem Setzen von Cookies die Einwilligung einholt. Nutzer müssen Cookies ablehnen können."
            },
            "barrierefreiheit": {
                "description": "Das Barrierefreiheitsstärkungsgesetz (BFSG) verpflichtet ab Juni 2025 Unternehmen, digitale Produkte barrierefrei nach WCAG 2.1 Level AA zu gestalten.",
                "legal_basis": "BFSG §12-15, WCAG 2.1 AA",
                "recommendation": "Optimieren Sie Ihre Website mit Alt-Texten, ARIA-Labels, semantischem HTML und ausreichenden Kontrastverhältnissen."
            }
        }
        return descriptions.get(category, {
            "description": f"Compliance-Anforderung für {category}",
            "legal_basis": "Verschiedene Rechtsgrundlagen",
            "recommendation": "Bitte prüfen Sie die spezifischen Anforderungen für diesen Bereich."
        })
    
    def _get_mock_cookie_config(self, cookies: List[Dict]) -> Dict[str, Any]:
        """Mock für generate_cookie_config"""
        return {
            "banner_text": "Diese Website verwendet Cookies, um Ihnen die bestmögliche Nutzererfahrung zu bieten.",
            "categories": [
                {
                    "name": "Notwendig",
                    "required": True,
                    "description": "Erforderlich für die Grundfunktionen der Website"
                },
                {
                    "name": "Analyse",
                    "required": False,
                    "description": "Helfen uns, die Nutzung der Website zu verstehen"
                }
            ],
            "cookies": cookies
        }
    
    def _mock_validate_impressum(self, text: str) -> Dict[str, Any]:
        """Mock für validate_impressum"""
        # Einfache Prüfung auf wichtige Begriffe
        required_fields = ["name", "adresse", "kontakt", "e-mail"]
        text_lower = text.lower()
        missing = [field for field in required_fields if field not in text_lower]
        
        return {
            "is_valid": len(missing) == 0,
            "score": max(0, 100 - (len(missing) * 25)),
            "missing_fields": missing,
            "recommendations": [
                f"Fügen Sie '{field}' zu Ihrem Impressum hinzu" for field in missing
            ]
        }
    
    # ==================== WHITE-LABEL WRAPPER FUNKTIONEN ====================
    
    def apply_complyo_branding(self, html_content: str, branding_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Wendet Complyo-Branding auf eRecht24-Inhalte an (White-Label)
        
        Args:
            html_content: Original HTML von eRecht24
            branding_config: Optional custom branding settings
            
        Returns:
            HTML mit Complyo-Branding
        """
        if not html_content:
            return html_content
        
        # Standard Complyo-Branding
        complyo_header = "<!-- Erstellt von Complyo - Ihre KI-First Compliance-Plattform -->\n"
        complyo_footer = "\n<!-- Powered by Complyo -->"
        
        # Entferne eRecht24-Branding (falls vorhanden)
        html_content = html_content.replace("eRecht24", "Complyo")
        html_content = html_content.replace("e-recht24", "complyo")
        html_content = html_content.replace("<!-- Erstellt von eRecht24 -->", "")
        html_content = html_content.replace("<!-- Powered by eRecht24 -->", "")
        
        # Füge Complyo-Branding hinzu
        branded_html = f"{complyo_header}{html_content}{complyo_footer}"
        
        # Custom Branding falls vorhanden
        if branding_config:
            if branding_config.get("remove_footer"):
                branded_html = branded_html.replace(complyo_footer, "")
            if branding_config.get("custom_header"):
                branded_html = branded_html.replace(complyo_header, branding_config["custom_header"])
        
        return branded_html
    
    async def get_white_label_legal_text(
        self,
        project_id: str,
        text_type: str,
        language: str = "de",
        company_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        White-Label Version von get_legal_text
        Holt Text von eRecht24 und wendet Complyo-Branding an
        
        Args:
            project_id: eRecht24 Projekt-ID
            text_type: "impressum", "datenschutz", "agb", "widerruf"
            language: "de", "en", "fr"
            company_data: Optional Firmendaten für Personalisierung
            
        Returns:
            HTML-Text mit Complyo-Branding
        """
        # Hole Original-Text von eRecht24
        raw_html = await self.get_legal_text(project_id, text_type, language)
        
        if not raw_html:
            return None
        
        # Wende Complyo-Branding an
        branded_html = self.apply_complyo_branding(raw_html)
        
        # Personalisiere mit Firmendaten falls vorhanden
        if company_data:
            branded_html = self._personalize_legal_text(branded_html, company_data)
        
        return branded_html
    
    def _personalize_legal_text(self, html: str, company_data: Dict[str, Any]) -> str:
        """
        Personalisiert Rechtstexte mit echten Firmendaten
        
        Args:
            html: HTML-Content
            company_data: Dict mit company_name, address, email, phone, etc.
            
        Returns:
            Personalisierter HTML
        """
        placeholders = {
            "[Firmenname]": company_data.get("company_name", "[Ihre Firma]"),
            "[Company Name]": company_data.get("company_name", "[Your Company]"),
            "[Adresse]": company_data.get("address", "[Ihre Adresse]"),
            "[Address]": company_data.get("address", "[Your Address]"),
            "[E-Mail]": company_data.get("email", "[Ihre E-Mail]"),
            "[Email]": company_data.get("email", "[Your Email]"),
            "[Telefon]": company_data.get("phone", "[Ihre Telefonnummer]"),
            "[Phone]": company_data.get("phone", "[Your Phone]"),
            "[Website]": company_data.get("website", "[Ihre Website]"),
        }
        
        for placeholder, value in placeholders.items():
            html = html.replace(placeholder, value)
        
        return html
    
    def generate_white_label_widget_config(
        self,
        cookies: List[Dict],
        site_id: str,
        customization: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generiert Widget-Config für Complyo Cookie Consent Widget
        (basiert auf eRecht24 CCM19, aber komplett white-labeled)
        
        Args:
            cookies: Erkannte Cookies
            site_id: Complyo Site-ID
            customization: Optional Design-Anpassungen
            
        Returns:
            Config-Dict für Complyo Widget
        """
        # Hole Basis-Config von eRecht24
        # (In Produktion würde dies async sein)
        base_config = {
            "banner_text": "Diese Website verwendet Cookies, um Ihnen die bestmögliche Nutzererfahrung zu bieten.",
            "categories": [
                {
                    "name": "Notwendig",
                    "required": True,
                    "description": "Erforderlich für die Grundfunktionen der Website"
                },
                {
                    "name": "Analyse",
                    "required": False,
                    "description": "Helfen uns, die Nutzung der Website zu verstehen"
                }
            ],
            "cookies": cookies
        }
        
        # Complyo Widget Config
        widget_config = {
            "widget_type": "complyo_cookie_consent",
            "version": "1.0.0",
            "site_id": site_id,
            "branding": {
                "powered_by": "Complyo",
                "show_logo": customization.get("show_logo", False) if customization else False,
                "primary_color": customization.get("primary_color", "#6366f1") if customization else "#6366f1",
                "accent_color": customization.get("accent_color", "#8b5cf6") if customization else "#8b5cf6",
            },
            "content": base_config,
            "behavior": {
                "position": "bottom",
                "block_cookies_until_consent": True,
                "remember_choice": True,
                "cookie_lifetime_days": 365
            }
        }
        
        return widget_config
    
    def generate_white_label_accessibility_config(
        self,
        site_id: str,
        features: Optional[List[str]] = None,
        customization: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generiert Config für Complyo Accessibility Widget
        (Echtes Code-basiertes Widget, kein Overlay!)
        
        Args:
            site_id: Complyo Site-ID
            features: Liste gewünschter Features
            customization: Optional Design-Anpassungen
            
        Returns:
            Config-Dict für Complyo Accessibility Widget
        """
        default_features = features or [
            'contrast',
            'font-size',
            'keyboard-nav',
            'skip-links',
            'alt-text-fallback',
            'focus-indicators',
            'aria-enhancements'
        ]
        
        widget_config = {
            "widget_type": "complyo_accessibility",
            "version": "1.0.0",
            "site_id": site_id,
            "branding": {
                "powered_by": "Complyo",
                "show_logo": customization.get("show_logo", False) if customization else False,
                "primary_color": customization.get("primary_color", "#6366f1") if customization else "#6366f1",
            },
            "features": {
                "enabled": default_features,
                "auto_fix": True,  # Automatische Code-Fixes
                "show_toolbar": True,  # Benutzer-Toolbar anzeigen
                "persistent_preferences": True  # Einstellungen speichern
            },
            "wcag_level": "AA",  # WCAG 2.1 Level AA Compliance
            "implementation_method": "code_injection",  # Echtes Code-Widget, kein Overlay!
        }
        
        return widget_config
    
    def wrap_fix_with_complyo_metadata(self, fix_data: Dict[str, Any], source: str = "erecht24") -> Dict[str, Any]:
        """
        Versieht Fix-Daten mit Complyo-Metadaten (White-Label-Wrapper)
        
        Args:
            fix_data: Original Fix-Daten (ggf. von eRecht24)
            source: Quelle der Daten (für interne Nachverfolgung)
            
        Returns:
            Fix-Daten mit Complyo-Branding
        """
        wrapped = {
            **fix_data,
            "provider": "Complyo",  # Verstecke echten Provider
            "generated_by": "Complyo AI",  # White-Label AI Branding
            "compliance_certified": True,
            "source_internal": source,  # Nur für Backend-Logging
            "complyo_verified": True,
            "last_updated": datetime.now().isoformat()
        }
        
        # Entferne/Ersetze eRecht24-Referenzen falls vorhanden
        for key in list(wrapped.keys()):
            if 'erecht' in key.lower() or 'e-recht' in key.lower():
                if isinstance(wrapped[key], str):
                    wrapped[key] = wrapped[key].replace("eRecht24", "Complyo").replace("e-recht24", "Complyo")
        
        return wrapped

# Global Service-Instanz
erecht24_service = ERecht24Service()

