"""
Internationalization Service for Complyo
Provides German, English, French, Italian and Polish translations
"""

import json
import logging
from typing import Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

class SupportedLanguages(Enum):
    GERMAN = "de"
    ENGLISH = "en"
    FR = "fr"
    IT = "it"
    PL = "pl"

class I18nService:
    def __init__(self):
        self.supported_languages = ["de", "en", "fr", "it", "pl"]
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
                "company_placeholder": "Mustermann GmbH",
                "scan_complete": "Scan abgeschlossen.",
                "issues_found": "Compliance-Probleme gefunden.",
                "action_required": "Handlung erforderlich.",
                "risk_high": "Hohes Risiko",
                "risk_medium": "Mittleres Risiko",
                "risk_low": "Niedriges Risiko",
                "cookie_consent_missing": "Cookie-Einwilligung fehlt.",
                "impressum_missing": "Impressum fehlt.",
                "accessibility_issue": "Barrierefreiheitsproblem erkannt."
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
                "company_placeholder": "Acme Corp",
                "scan_complete": "Scan complete.",
                "issues_found": "Compliance issues found.",
                "action_required": "Action required.",
                "risk_high": "High risk",
                "risk_medium": "Medium risk",
                "risk_low": "Low risk",
                "cookie_consent_missing": "Cookie consent is missing.",
                "impressum_missing": "Legal notice is missing.",
                "accessibility_issue": "Accessibility issue detected."
            },
            "fr": {
                "scan_complete": "Analyse terminée.",
                "issues_found": "Problèmes de conformité détectés.",
                "action_required": "Action requise.",
                "risk_high": "Risque élevé",
                "risk_medium": "Risque moyen",
                "risk_low": "Risque faible",
                "cookie_consent_missing": "Le consentement aux cookies est manquant.",
                "impressum_missing": "Les mentions légales sont manquantes.",
                "accessibility_issue": "Problème d'accessibilité détecté."
            },
            "it": {
                "scan_complete": "Scansione completata.",
                "issues_found": "Problemi di conformità rilevati.",
                "action_required": "Azione richiesta.",
                "risk_high": "Rischio elevato",
                "risk_medium": "Rischio medio",
                "risk_low": "Rischio basso",
                "cookie_consent_missing": "Manca il consenso ai cookie.",
                "impressum_missing": "Note legali mancanti.",
                "accessibility_issue": "Problema di accessibilità rilevato."
            },
            "pl": {
                "scan_complete": "Skanowanie zakończone.",
                "issues_found": "Wykryto problemy ze zgodnością.",
                "action_required": "Wymagane działanie.",
                "risk_high": "Wysokie ryzyko",
                "risk_medium": "Średnie ryzyko",
                "risk_low": "Niskie ryzyko",
                "cookie_consent_missing": "Brakuje zgody na pliki cookie.",
                "impressum_missing": "Brakuje informacji prawnych.",
                "accessibility_issue": "Wykryto problem z dostępnością."
            }
        }
        
    def load_translations_from_file(self, file_path: str):
        """Load translations from a JSON file and merge them into existing translations."""
        try:
            with open(file_path, "r", encoding="utf-8") as translation_file:
                loaded_translations = json.load(translation_file)

            if not isinstance(loaded_translations, dict):
                logger.warning(f"Translation file has invalid format: {file_path}")
                return

            for language, translations in loaded_translations.items():
                if not isinstance(translations, dict):
                    logger.warning(f"Translations for '{language}' have invalid format")
                    continue
                if language not in self.translations:
                    self.translations[language] = {}
                self.translations[language].update(translations)
                if language not in self.supported_languages:
                    self.supported_languages.append(language)
        except Exception as e:
            logger.warning(f"Could not load translations from '{file_path}': {e}")

    def get_translation(self, key: str, language: str = "de", **kwargs) -> str:
        """Get translation for a key in specified language"""
        try:
            if language not in self.supported_languages:
                language = "de"
            
            translation = self.translations[language].get(key, key)
            
            if kwargs:
                translation = translation.format(**kwargs)
            
            return translation
            
        except Exception as e:
            logger.warning(f"Translation error for '{key}': {e}")
            return key
    
    def translate(self, language: str, key: str, **kwargs) -> str:
        """Alias for get_translation with (language, key) argument order"""
        return self.get_translation(key, language, **kwargs)

    def detect_language_from_url(self, url: str) -> str:
        """Detect language from URL"""
        if url and ".de" in url:
            return "de"
        return "en"
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return self.supported_languages

# Global i18n service instance
i18n_service = I18nService()
