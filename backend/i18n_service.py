"""
Internationalization Service for Complyo
Provides German and English translations
"""

import logging
from typing import Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

class SupportedLanguages(Enum):
    GERMAN = "de"
    ENGLISH = "en"

class I18nService:
    def __init__(self):
        self.translations = {
            "de": {
                "email_verification_subject": "Bestätigen Sie Ihre E-Mail-Adresse - Complyo",
                "email_report_subject": "Ihr Website-Compliance-Report - Complyo", 
                "email_deletion_subject": "Bestätigung der Datenlöschung - Complyo",
                "email_export_subject": "Ihr Datenexport - Complyo DSGVO",
                "greeting": "Hallo {name}",
                "verify_email_title": "E-Mail-Adresse bestätigen",
                "verify_button": "E-Mail bestätigen",
                "gdpr_notice": "🇩🇪 DSGVO-HINWEIS",
                "lead_collected": "Lead erfolgreich erfasst. Bestätigungs-E-Mail wurde versendet.",
                "email_verified": "E-Mail-Adresse erfolgreich bestätigt.",
                "data_deleted": "Ihre Daten wurden erfolgreich gelöscht.",
                "analysis_started": "Analyse läuft...",
                "analyze_button": "Kostenlose Analyse starten",
                "name_placeholder": "Max Mustermann",
                "email_placeholder": "max@beispiel.de",
                "company_placeholder": "Mustermann GmbH"
            },
            "en": {
                "email_verification_subject": "Confirm your email address - Complyo",
                "email_report_subject": "Your Website Compliance Report - Complyo",
                "email_deletion_subject": "Data Deletion Confirmation - Complyo", 
                "email_export_subject": "Your Data Export - Complyo GDPR",
                "greeting": "Hello {name}",
                "verify_email_title": "Confirm your email address",
                "verify_button": "Confirm Email",
                "gdpr_notice": "🇬🇧 GDPR NOTICE",
                "lead_collected": "Lead successfully captured. Confirmation email sent.",
                "email_verified": "Email address successfully verified.",
                "data_deleted": "Your data has been successfully deleted.",
                "analysis_started": "Analysis running...",
                "analyze_button": "Start Free Analysis",
                "name_placeholder": "John Doe",
                "email_placeholder": "john@example.com",
                "company_placeholder": "Acme Corp"
            }
        }
        
    def get_translation(self, key: str, language: str = "de", **kwargs) -> str:
        """Get translation for a key in specified language"""
        try:
            if language not in ["de", "en"]:
                language = "de"
            
            translation = self.translations[language].get(key, key)
            
            if kwargs:
                translation = translation.format(**kwargs)
            
            return translation
            
        except Exception as e:
            logger.warning(f"Translation error for '{key}': {e}")
            return key
    
    def detect_language_from_url(self, url: str) -> str:
        """Detect language from URL"""
        if url and ".de" in url:
            return "de"
        return "en"

# Global i18n service instance
i18n_service = I18nService()
