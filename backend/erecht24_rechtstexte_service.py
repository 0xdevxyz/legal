"""
eRecht24 Rechtstexte-API Service
Integriert eRecht24 Rechtstexte-API für automatische Generierung von:
- Impressum
- Datenschutzerklärung
- Datenschutzerklärung Social Media

API Dokumentation: https://github.com/erecht24/rechtstexte-sdk
"""

import os
import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class LegalTextType(str, Enum):
    """Typen von Rechtstexten"""
    IMPRINT = "imprint"
    PRIVACY_POLICY = "privacy_policy"
    PRIVACY_POLICY_SOCIAL_MEDIA = "privacy_policy_social_media"


class PushType(str, Enum):
    """Push-Notification Typen"""
    IMPRINT = "imprint"
    PRIVACY_POLICY = "privacyPolicy"
    PRIVACY_POLICY_SOCIAL_MEDIA = "privacyPolicySocialMedia"


class ERecht24RechtstexteService:
    """Service für eRecht24 Rechtstexte-API Integration"""
    
    # API Base URL (aus SDK Dokumentation)
    API_BASE_URL = "https://api.e-recht24.de"
    
    def __init__(self, api_key: Optional[str] = None, plugin_key: Optional[str] = None):
        """
        Initialisiert den eRecht24 Rechtstexte Service
        
        Args:
            api_key: eRecht24 API Key (project key)
            plugin_key: eRecht24 Developer/Plugin Key
        """
        self.api_key = api_key or os.getenv(
            "ERECHT24_API_KEY", 
            "e81cbf18a5239377aa4972773d34cc2b81ebc672879581bce29a0a4c414bf117"  # Development Key
        )
        self.plugin_key = plugin_key or os.getenv(
            "ERECHT24_PLUGIN_KEY",
            "complyo-ai-compliance"  # Muss bei eRecht24 registriert werden
        )
        self.timeout = 30.0
        
        if self.api_key == "e81cbf18a5239377aa4972773d34cc2b81ebc672879581bce29a0a4c414bf117":
            logger.info("🔑 Verwende eRecht24 Development API Key")
        
        logger.info(f"✅ eRecht24 Rechtstexte Service initialisiert")
    
    def _get_headers(self) -> Dict[str, str]:
        """Erstellt die HTTP Headers für API Requests"""
        return {
            "eRecht24-api-key": self.api_key,
            "eRecht24-plugin-key": self.plugin_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def create_client(
        self,
        push_uri: str,
        cms: str = "Custom",
        cms_version: str = "1.0",
        plugin_name: str = "complyo-ai-compliance",
        author_mail: str = "api@complyo.tech",
        push_method: str = "POST"
    ) -> Optional[Dict[str, Any]]:
        """
        Registriert einen neuen Client für Push-Notifications
        
        Args:
            push_uri: Webhook URL für Push-Notifications
            cms: CMS Name (z.B. "WordPress", "Custom")
            cms_version: CMS Version
            plugin_name: Plugin Name
            author_mail: Kontakt E-Mail
            push_method: HTTP Methode für Push (POST oder PUT)
            
        Returns:
            Dict mit client_id und Details oder None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.API_BASE_URL}/v1/client",
                    headers=self._get_headers(),
                    json={
                        "pushUri": push_uri,
                        "pushMethod": push_method,
                        "cms": cms,
                        "cmsVersion": cms_version,
                        "pluginName": plugin_name,
                        "authorMail": author_mail
                    }
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.info(f"✅ eRecht24 Client registriert: {data.get('client_id')}")
                    return data
                else:
                    logger.error(f"❌ eRecht24 Client-Registrierung fehlgeschlagen: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Fehler bei Client-Registrierung: {e}")
            return None
    
    async def get_imprint(self, language: str = "de") -> Optional[str]:
        """
        Holt das Impressum vom eRecht24 API
        
        Args:
            language: Sprache (de, en, fr, etc.)
            
        Returns:
            HTML-Text des Impressums oder None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.API_BASE_URL}/v1/imprint",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # HTML Text nach Sprache extrahieren
                    html_key = f"html_{language.upper()}" if language != "de" else "html_de"
                    html_text = data.get(html_key) or data.get("html_de")
                    
                    if html_text:
                        logger.info(f"✅ Impressum abgerufen ({language}): {len(html_text)} Zeichen")
                        return html_text
                    else:
                        logger.warning(f"⚠️  Kein Impressum-Text für Sprache '{language}' gefunden")
                        return None
                else:
                    logger.error(f"❌ Impressum-Abruf fehlgeschlagen: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Impressum-Abruf: {e}")
            return None
    
    async def get_privacy_policy(self, language: str = "de") -> Optional[str]:
        """
        Holt die Datenschutzerklärung vom eRecht24 API
        
        Args:
            language: Sprache (de, en, fr, etc.)
            
        Returns:
            HTML-Text der Datenschutzerklärung oder None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.API_BASE_URL}/v1/privacyPolicy",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # HTML Text nach Sprache extrahieren
                    html_key = f"html_{language.upper()}" if language != "de" else "html_de"
                    html_text = data.get(html_key) or data.get("html_de")
                    
                    if html_text:
                        logger.info(f"✅ Datenschutzerklärung abgerufen ({language}): {len(html_text)} Zeichen")
                        return html_text
                    else:
                        logger.warning(f"⚠️  Keine Datenschutzerklärung für Sprache '{language}' gefunden")
                        return None
                else:
                    logger.error(f"❌ Datenschutz-Abruf fehlgeschlagen: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Datenschutz-Abruf: {e}")
            return None
    
    async def get_privacy_policy_social_media(self, language: str = "de") -> Optional[str]:
        """
        Holt die Datenschutzerklärung für Social Media vom eRecht24 API
        
        Args:
            language: Sprache (de, en, fr, etc.)
            
        Returns:
            HTML-Text der Social Media Datenschutzerklärung oder None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.API_BASE_URL}/v1/privacyPolicySocialMedia",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # HTML Text nach Sprache extrahieren
                    html_key = f"html_{language.upper()}" if language != "de" else "html_de"
                    html_text = data.get(html_key) or data.get("html_de")
                    
                    if html_text:
                        logger.info(f"✅ Social Media Datenschutz abgerufen ({language}): {len(html_text)} Zeichen")
                        return html_text
                    else:
                        logger.warning(f"⚠️  Kein Social Media Datenschutz für Sprache '{language}' gefunden")
                        return None
                else:
                    logger.error(f"❌ Social Media Datenschutz-Abruf fehlgeschlagen: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Social Media Datenschutz-Abruf: {e}")
            return None
    
    async def get_legal_text(
        self, 
        text_type: LegalTextType, 
        language: str = "de"
    ) -> Optional[str]:
        """
        Universelle Methode zum Abrufen von Rechtstexten
        
        Args:
            text_type: Typ des Rechtstextes
            language: Sprache
            
        Returns:
            HTML-Text oder None
        """
        if text_type == LegalTextType.IMPRINT:
            return await self.get_imprint(language)
        elif text_type == LegalTextType.PRIVACY_POLICY:
            return await self.get_privacy_policy(language)
        elif text_type == LegalTextType.PRIVACY_POLICY_SOCIAL_MEDIA:
            return await self.get_privacy_policy_social_media(language)
        else:
            logger.error(f"❌ Unbekannter Text-Typ: {text_type}")
            return None
    
    async def get_client_list(self) -> Optional[List[Dict[str, Any]]]:
        """
        Holt die Liste aller registrierten Clients
        
        Returns:
            Liste von Client-Dicts oder None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.API_BASE_URL}/v1/client",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    clients = data.get("clients", [])
                    logger.info(f"✅ {len(clients)} Clients abgerufen")
                    return clients
                else:
                    logger.error(f"❌ Client-Liste-Abruf fehlgeschlagen: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Client-Listen-Abruf: {e}")
            return None
    
    async def fire_test_push(self, client_id: int, push_type: str = "ping") -> bool:
        """
        Triggert einen Test-Push an einen Client
        
        Args:
            client_id: Die Client-ID
            push_type: Typ des Pushes (ping, imprint, privacyPolicy, etc.)
            
        Returns:
            True bei Erfolg, False sonst
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.API_BASE_URL}/v1/testPush",
                    headers=self._get_headers(),
                    json={
                        "clientId": client_id,
                        "type": push_type
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Test-Push an Client {client_id} gesendet")
                    return True
                else:
                    logger.error(f"❌ Test-Push fehlgeschlagen: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Test-Push: {e}")
            return False


# Singleton Instance
erecht24_rechtstexte_service = ERecht24RechtstexteService()

