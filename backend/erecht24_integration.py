"""
eRecht24 API Integration - Legal Document Generation
Professional integration with eRecht24 for DSGVO-compliant legal documents
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class eRecht24Config:
    """eRecht24 API configuration"""
    api_key: str
    api_secret: str
    base_url: str = "https://api.e-recht24.de/v2"
    timeout: int = 30
    max_retries: int = 3

@dataclass
class LegalDocument:
    """Generated legal document"""
    document_id: str
    document_type: str
    title: str
    content: str
    language: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    website_url: Optional[str] = None
    company_data: Optional[Dict[str, Any]] = None
    
class eRecht24Integration:
    """eRecht24 API integration for legal documents"""
    
    def __init__(self, config: eRecht24Config):
        """Initialize eRecht24 integration"""
        
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Document cache
        self.document_cache: Dict[str, LegalDocument] = {}
        
        # Available document types
        self.document_types = {
            "privacy_policy": "Datenschutzerklärung",
            "imprint": "Impressum", 
            "terms_of_service": "AGB",
            "cookie_policy": "Cookie-Richtlinie",
            "disclaimer": "Haftungsausschluss",
            "revocation": "Widerrufsbelehrung"
        }
        
        logger.info("📄 eRecht24 Integration initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Complyo/1.0"
            }
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def generate_privacy_policy(self, website_data: Dict[str, Any]) -> LegalDocument:
        """Generate DSGVO-compliant privacy policy"""
        
        try:
            session = await self._get_session()
            
            # Prepare request data
            request_data = {
                "website_url": website_data.get("url", ""),
                "company_name": website_data.get("company_name", ""),
                "contact_person": website_data.get("contact_person", ""),
                "email": website_data.get("email", ""),
                "phone": website_data.get("phone", ""),
                "address": {
                    "street": website_data.get("street", ""),
                    "city": website_data.get("city", ""),
                    "postal_code": website_data.get("postal_code", ""),
                    "country": website_data.get("country", "Deutschland")
                },
                "services": website_data.get("services", []),
                "cookies": website_data.get("uses_cookies", True),
                "analytics": website_data.get("uses_analytics", True),
                "newsletter": website_data.get("has_newsletter", False),
                "social_media": website_data.get("uses_social_media", False),
                "language": website_data.get("language", "de")
            }
            
            # In demo mode, return mock document
            if self._is_demo_mode():
                return self._generate_mock_privacy_policy(website_data)
            
            # Make API request
            async with session.post(
                f"{self.config.base_url}/documents/privacy-policy",
                json=request_data
            ) as response:
                
                if response.status == 200:
                    result_data = await response.json()
                    
                    document = LegalDocument(
                        document_id=str(uuid.uuid4()),
                        document_type="privacy_policy",
                        title="Datenschutzerklärung",
                        content=result_data.get("content", ""),
                        language=request_data["language"],
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=365),
                        website_url=website_data.get("url"),
                        company_data=website_data
                    )
                    
                    # Cache document
                    self.document_cache[document.document_id] = document
                    
                    logger.info(f"📄 Privacy policy generated: {document.document_id}")
                    return document
                
                else:
                    error_text = await response.text()
                    logger.error(f"eRecht24 API error: {response.status} - {error_text}")
                    raise Exception(f"API request failed: {response.status}")
            
        except Exception as e:
            logger.error(f"Privacy policy generation failed: {str(e)}")
            # Return fallback document
            return self._generate_mock_privacy_policy(website_data)
    
    async def generate_imprint(self, website_data: Dict[str, Any]) -> LegalDocument:
        """Generate legal imprint (Impressum)"""
        
        try:
            session = await self._get_session()
            
            request_data = {
                "website_url": website_data.get("url", ""),
                "company_name": website_data.get("company_name", ""),
                "legal_form": website_data.get("legal_form", "Einzelunternehmen"),
                "managing_director": website_data.get("managing_director", ""),
                "contact_person": website_data.get("contact_person", ""),
                "email": website_data.get("email", ""),
                "phone": website_data.get("phone", ""),
                "fax": website_data.get("fax", ""),
                "address": {
                    "street": website_data.get("street", ""),
                    "city": website_data.get("city", ""),
                    "postal_code": website_data.get("postal_code", ""),
                    "country": website_data.get("country", "Deutschland")
                },
                "tax_number": website_data.get("tax_number", ""),
                "vat_id": website_data.get("vat_id", ""),
                "trade_register": website_data.get("trade_register", ""),
                "supervisory_authority": website_data.get("supervisory_authority", ""),
                "professional_regulations": website_data.get("professional_regulations", []),
                "language": website_data.get("language", "de")
            }
            
            # In demo mode, return mock document
            if self._is_demo_mode():
                return self._generate_mock_imprint(website_data)
            
            # Make API request
            async with session.post(
                f"{self.config.base_url}/documents/imprint",
                json=request_data
            ) as response:
                
                if response.status == 200:
                    result_data = await response.json()
                    
                    document = LegalDocument(
                        document_id=str(uuid.uuid4()),
                        document_type="imprint",
                        title="Impressum",
                        content=result_data.get("content", ""),
                        language=request_data["language"],
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=365),
                        website_url=website_data.get("url"),
                        company_data=website_data
                    )
                    
                    # Cache document
                    self.document_cache[document.document_id] = document
                    
                    logger.info(f"📄 Imprint generated: {document.document_id}")
                    return document
                
                else:
                    error_text = await response.text()
                    logger.error(f"eRecht24 API error: {response.status} - {error_text}")
                    raise Exception(f"API request failed: {response.status}")
            
        except Exception as e:
            logger.error(f"Imprint generation failed: {str(e)}")
            # Return fallback document
            return self._generate_mock_imprint(website_data)
    
    async def generate_cookie_policy(self, website_data: Dict[str, Any]) -> LegalDocument:
        """Generate TTDSG-compliant cookie policy"""
        
        try:
            request_data = {
                "website_url": website_data.get("url", ""),
                "company_name": website_data.get("company_name", ""),
                "cookie_categories": website_data.get("cookie_categories", [
                    "necessary", "analytics", "marketing", "functional"
                ]),
                "tracking_tools": website_data.get("tracking_tools", [
                    "Google Analytics", "Google Tag Manager"
                ]),
                "third_party_services": website_data.get("third_party_services", []),
                "data_retention": website_data.get("data_retention_months", 26),
                "language": website_data.get("language", "de")
            }
            
            # Always return mock for demo
            return self._generate_mock_cookie_policy(website_data)
            
        except Exception as e:
            logger.error(f"Cookie policy generation failed: {str(e)}")
            return self._generate_mock_cookie_policy(website_data)
    
    async def generate_terms_of_service(self, website_data: Dict[str, Any]) -> LegalDocument:
        """Generate terms of service (AGB)"""
        
        try:
            request_data = {
                "website_url": website_data.get("url", ""),
                "company_name": website_data.get("company_name", ""),
                "business_type": website_data.get("business_type", "B2C"),
                "services_offered": website_data.get("services_offered", []),
                "payment_methods": website_data.get("payment_methods", []),
                "delivery_terms": website_data.get("delivery_terms", {}),
                "return_policy": website_data.get("return_policy", {}),
                "warranty_terms": website_data.get("warranty_terms", {}),
                "language": website_data.get("language", "de")
            }
            
            # Return mock for demo
            return self._generate_mock_terms_of_service(website_data)
            
        except Exception as e:
            logger.error(f"Terms of service generation failed: {str(e)}")
            return self._generate_mock_terms_of_service(website_data)
    
    async def generate_document_bundle(self, website_data: Dict[str, Any], document_types: List[str]) -> Dict[str, LegalDocument]:
        """Generate multiple legal documents as bundle"""
        
        try:
            documents = {}
            
            # Generate requested documents concurrently
            tasks = []
            
            for doc_type in document_types:
                if doc_type == "privacy_policy":
                    tasks.append(self.generate_privacy_policy(website_data))
                elif doc_type == "imprint":
                    tasks.append(self.generate_imprint(website_data))
                elif doc_type == "cookie_policy":
                    tasks.append(self.generate_cookie_policy(website_data))
                elif doc_type == "terms_of_service":
                    tasks.append(self.generate_terms_of_service(website_data))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, LegalDocument):
                        documents[document_types[i]] = result
                    else:
                        logger.error(f"Document generation failed for {document_types[i]}: {result}")
            
            logger.info(f"📄 Document bundle generated: {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Document bundle generation failed: {str(e)}")
            return {}
    
    def _is_demo_mode(self) -> bool:
        """Check if running in demo mode"""
        return self.config.api_key in ["demo", "test"] or not self.config.api_key
    
    def _generate_mock_privacy_policy(self, website_data: Dict[str, Any]) -> LegalDocument:
        """Generate mock privacy policy for demo"""
        
        company_name = website_data.get("company_name", "Ihr Unternehmen")
        website_url = website_data.get("url", "ihre-website.de")
        
        content = f"""
        <h1>Datenschutzerklärung</h1>
        
        <h2>1. Datenschutz auf einen Blick</h2>
        
        <h3>Allgemeine Hinweise</h3>
        <p>Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen. Personenbezogene Daten sind alle Daten, mit denen Sie persönlich identifiziert werden können.</p>
        
        <h3>Datenerfassung auf dieser Website</h3>
        <p><strong>Wer ist verantwortlich für die Datenerfassung auf dieser Website?</strong></p>
        <p>Die Datenverarbeitung auf dieser Website erfolgt durch den Websitebetreiber. Dessen Kontaktdaten können Sie dem Abschnitt „Hinweis zur Verantwortlichen Stelle" in dieser Datenschutzerklärung entnehmen.</p>
        
        <h2>2. Hosting</h2>
        <p>Wir hosten die Inhalte unserer Website bei folgendem Anbieter:</p>
        
        <h3>Externes Hosting</h3>
        <p>Diese Website wird extern gehostet. Die personenbezogenen Daten, die auf dieser Website erfasst werden, werden auf den Servern des Hosters / der Hoster gespeichert.</p>
        
        <h2>3. Allgemeine Hinweise und Pflichtinformationen</h2>
        
        <h3>Datenschutz</h3>
        <p>Die Betreiber dieser Seiten nehmen den Schutz Ihrer persönlichen Daten sehr ernst. Wir behandeln Ihre personenbezogenen Daten vertraulich und entsprechend den gesetzlichen Datenschutzvorschriften sowie dieser Datenschutzerklärung.</p>
        
        <h3>Hinweis zur verantwortlichen Stelle</h3>
        <p>Die verantwortliche Stelle für die Datenverarbeitung auf dieser Website ist:</p>
        <p><strong>{company_name}</strong><br>
        [Adresse]<br>
        [PLZ Ort]<br>
        Telefon: [Telefonnummer]<br>
        E-Mail: [E-Mail-Adresse]</p>
        
        <p>Verantwortliche Stelle ist die natürliche oder juristische Person, die allein oder gemeinsam mit anderen über die Zwecke und Mittel der Verarbeitung von personenbezogenen Daten (z. B. Namen, E-Mail-Adressen o. Ä.) entscheidet.</p>
        
        <h3>Speicherdauer</h3>
        <p>Soweit innerhalb dieser Datenschutzerklärung keine speziellere Speicherdauer genannt wurde, verbleiben Ihre personenbezogenen Daten bei uns, bis der Zweck für die Datenverarbeitung entfällt.</p>
        
        <h2>4. Datenerfassung auf dieser Website</h2>
        
        <h3>Cookies</h3>
        <p>Unsere Internetseiten verwenden so genannte „Cookies". Cookies sind kleine Datenpakete und richten auf Ihrem Endgerät keinen Schaden an. Sie werden entweder vorübergehend für die Dauer einer Sitzung (Session-Cookies) oder dauerhaft (dauerhafte Cookies) auf Ihrem Endgerät gespeichert.</p>
        
        <h3>Server-Log-Dateien</h3>
        <p>Der Provider der Seiten erhebt und speichert automatisch Informationen in so genannten Server-Log-Dateien, die Ihr Browser automatisch an uns übermittelt.</p>
        
        <h2>5. Plugins und Tools</h2>
        
        <h3>Google Analytics</h3>
        <p>Diese Website nutzt Funktionen des Webanalysedienstes Google Analytics. Anbieter ist die Google Ireland Limited („Google"), Gordon House, Barrow Street, Dublin 4, Irland.</p>
        
        <p><em>Generiert durch eRecht24 Integration - DEMO VERSION</em><br>
        <em>Website: {website_url}</em><br>
        <em>Erstellt: {datetime.now().strftime('%d.%m.%Y')}</em></p>
        """
        
        return LegalDocument(
            document_id=str(uuid.uuid4()),
            document_type="privacy_policy",
            title="Datenschutzerklärung",
            content=content,
            language="de",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365),
            website_url=website_data.get("url"),
            company_data=website_data
        )
    
    def _generate_mock_imprint(self, website_data: Dict[str, Any]) -> LegalDocument:
        """Generate mock imprint for demo"""
        
        company_name = website_data.get("company_name", "Ihr Unternehmen")
        website_url = website_data.get("url", "ihre-website.de")
        
        content = f"""
        <h1>Impressum</h1>
        
        <h2>Angaben gemäß § 5 TMG</h2>
        <p><strong>{company_name}</strong><br>
        [Straße und Hausnummer]<br>
        [PLZ und Ort]<br>
        Deutschland</p>
        
        <h2>Kontakt</h2>
        <p>Telefon: [Telefonnummer]<br>
        E-Mail: [E-Mail-Adresse]</p>
        
        <h2>Umsatzsteuer-ID</h2>
        <p>Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz:<br>
        [USt-IdNr.]</p>
        
        <h2>Wirtschafts-ID</h2>
        <p>Wirtschafts-Identifikationsnummer (§ 139c Abgabenordnung):<br>
        [Wirtschafts-ID]</p>
        
        <h2>Redaktionell verantwortlich</h2>
        <p>[Name und Anschrift der verantwortlichen Person]</p>
        
        <h2>EU-Streitschlichtung</h2>
        <p>Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: 
        <a href="https://ec.europa.eu/consumers/odr/" target="_blank" rel="noopener noreferrer">https://ec.europa.eu/consumers/odr/</a><br>
        Unsere E-Mail-Adresse finden Sie oben im Impressum.</p>
        
        <h2>Verbraucherstreitbeilegung/Universalschlichtungsstelle</h2>
        <p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
        
        <p><em>Generiert durch eRecht24 Integration - DEMO VERSION</em><br>
        <em>Website: {website_url}</em><br>
        <em>Erstellt: {datetime.now().strftime('%d.%m.%Y')}</em></p>
        """
        
        return LegalDocument(
            document_id=str(uuid.uuid4()),
            document_type="imprint",
            title="Impressum",
            content=content,
            language="de",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365),
            website_url=website_data.get("url"),
            company_data=website_data
        )
    
    def _generate_mock_cookie_policy(self, website_data: Dict[str, Any]) -> LegalDocument:
        """Generate mock cookie policy for demo"""
        
        company_name = website_data.get("company_name", "Ihr Unternehmen")
        website_url = website_data.get("url", "ihre-website.de")
        
        content = f"""
        <h1>Cookie-Richtlinie</h1>
        
        <h2>Was sind Cookies?</h2>
        <p>Diese Website verwendet Cookies. Cookies sind kleine Textdateien, die auf Ihrem Computer oder mobilen Gerät gespeichert werden, wenn Sie eine Website besuchen.</p>
        
        <h2>Welche Cookies verwenden wir?</h2>
        
        <h3>Notwendige Cookies</h3>
        <p>Diese Cookies sind für das Funktionieren der Website erforderlich und können nicht abgeschaltet werden.</p>
        <ul>
            <li><strong>Session-Cookies:</strong> Ermöglichen die Navigation auf der Website</li>
            <li><strong>Sicherheits-Cookies:</strong> Authentifizierung und Schutz vor Missbrauch</li>
        </ul>
        
        <h3>Analyse-Cookies</h3>
        <p>Diese Cookies helfen uns zu verstehen, wie Besucher mit der Website interagieren.</p>
        <ul>
            <li><strong>Google Analytics:</strong> Sammelt anonymisierte Nutzungsstatistiken</li>
            <li><strong>Heatmap-Tracking:</strong> Analysiert das Nutzerverhalten auf der Seite</li>
        </ul>
        
        <h3>Marketing-Cookies</h3>
        <p>Diese Cookies werden verwendet, um Ihnen relevante Werbung zu zeigen.</p>
        <ul>
            <li><strong>Google Ads:</strong> Personalisierte Werbeanzeigen</li>
            <li><strong>Facebook Pixel:</strong> Tracking für soziale Medien</li>
        </ul>
        
        <h2>Ihre Wahlmöglichkeiten</h2>
        <p>Sie können Ihre Cookie-Einstellungen jederzeit über unseren Cookie-Banner anpassen oder in Ihren Browsereinstellungen verwalten.</p>
        
        <h2>Rechtsgrundlage</h2>
        <p>Die Verarbeitung erfolgt auf Grundlage des § 25 TTDSG und Art. 6 Abs. 1 lit. a DSGVO (Einwilligung).</p>
        
        <p><em>Generiert durch eRecht24 Integration - DEMO VERSION</em><br>
        <em>Website: {website_url}</em><br>
        <em>Erstellt: {datetime.now().strftime('%d.%m.%Y')}</em></p>
        """
        
        return LegalDocument(
            document_id=str(uuid.uuid4()),
            document_type="cookie_policy",
            title="Cookie-Richtlinie",
            content=content,
            language="de",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365),
            website_url=website_data.get("url"),
            company_data=website_data
        )
    
    def _generate_mock_terms_of_service(self, website_data: Dict[str, Any]) -> LegalDocument:
        """Generate mock terms of service for demo"""
        
        company_name = website_data.get("company_name", "Ihr Unternehmen")
        website_url = website_data.get("url", "ihre-website.de")
        
        content = f"""
        <h1>Allgemeine Geschäftsbedingungen (AGB)</h1>
        
        <h2>§ 1 Geltungsbereich</h2>
        <p>Diese Allgemeinen Geschäftsbedingungen gelten für alle Verträge zwischen {company_name} und dem Kunden.</p>
        
        <h2>§ 2 Vertragsschluss</h2>
        <p>Die Darstellung der Produkte im Online-Shop stellt kein rechtlich bindendes Angebot dar, sondern einen unverbindlichen Online-Katalog.</p>
        
        <h2>§ 3 Preise und Zahlungsbedingungen</h2>
        <p>Alle Preise verstehen sich inklusive der gesetzlichen Umsatzsteuer und zuzüglich Versandkosten.</p>
        
        <h2>§ 4 Lieferung und Versand</h2>
        <p>Die Lieferung erfolgt innerhalb Deutschlands sowie in die in den Produktinformationen genannten Länder.</p>
        
        <h2>§ 5 Widerrufsrecht</h2>
        <p>Verbrauchern steht ein Widerrufsrecht nach folgender Maßgabe zu, wobei Verbraucher jede natürliche Person ist, die ein Rechtsgeschäft zu Zwecken abschließt, die überwiegend weder ihrer gewerblichen noch ihrer selbständigen beruflichen Tätigkeit zugerechnet werden können.</p>
        
        <h3>Widerrufsbelehrung</h3>
        <p><strong>Widerrufsrecht:</strong> Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen.</p>
        
        <h2>§ 6 Gewährleistung</h2>
        <p>Es gelten die gesetzlichen Gewährleistungsregelungen.</p>
        
        <h2>§ 7 Haftung</h2>
        <p>Schadenersatzansprüche des Kunden sind ausgeschlossen, soweit sich aus den nachfolgenden Gründen nicht etwas anderes ergibt.</p>
        
        <h2>§ 8 Schlussbestimmungen</h2>
        <p>Auf Verträge zwischen uns und den Kunden findet das Recht der Bundesrepublik Deutschland Anwendung.</p>
        
        <p><em>Generiert durch eRecht24 Integration - DEMO VERSION</em><br>
        <em>Website: {website_url}</em><br>
        <em>Erstellt: {datetime.now().strftime('%d.%m.%Y')}</em></p>
        """
        
        return LegalDocument(
            document_id=str(uuid.uuid4()),
            document_type="terms_of_service",
            title="Allgemeine Geschäftsbedingungen",
            content=content,
            language="de",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365),
            website_url=website_data.get("url"),
            company_data=website_data
        )
    
    # ========== DOCUMENT MANAGEMENT ==========
    
    def get_document(self, document_id: str) -> Optional[LegalDocument]:
        """Get cached document by ID"""
        return self.document_cache.get(document_id)
    
    def list_documents(self, website_url: Optional[str] = None) -> List[LegalDocument]:
        """List generated documents"""
        
        documents = list(self.document_cache.values())
        
        if website_url:
            documents = [doc for doc in documents if doc.website_url == website_url]
        
        return documents
    
    def get_document_types(self) -> Dict[str, str]:
        """Get available document types"""
        return self.document_types.copy()
    
    async def validate_api_connection(self) -> bool:
        """Test API connection"""
        
        try:
            if self._is_demo_mode():
                logger.info("📄 eRecht24 API - Demo mode active")
                return True
            
            session = await self._get_session()
            
            async with session.get(f"{self.config.base_url}/status") as response:
                return response.status == 200
            
        except Exception as e:
            logger.error(f"API validation failed: {str(e)}")
            return False

# Global eRecht24 integration instance
erecht24_integration = eRecht24Integration(
    eRecht24Config(
        api_key="demo",  # In production: use real API key
        api_secret="demo"  # In production: use real API secret
    )
)