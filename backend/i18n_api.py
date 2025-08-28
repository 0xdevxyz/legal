"""
Internationalization API Endpoints
Provides language switching and translation endpoints for frontend
"""

from fastapi import APIRouter, Request, Query
from typing import Dict, Any, Optional
import logging
from i18n_service import i18n_service

logger = logging.getLogger(__name__)

i18n_router = APIRouter(prefix="/api/i18n", tags=["internationalization"])

@i18n_router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages
    """
    return {
        "supported_languages": i18n_service.supported_languages,
        "default_language": i18n_service.default_language,
        "languages": {
            "de": {
                "code": "de",
                "name": "Deutsch",
                "native_name": "Deutsch",
                "flag": "🇩🇪"
            },
            "en": {
                "code": "en", 
                "name": "English",
                "native_name": "English",
                "flag": "🇬🇧"
            }
        }
    }

@i18n_router.get("/translations")
async def get_translations(
    request: Request,
    language: Optional[str] = Query(None, description="Language code (de/en)")
):
    """
    Get all translations for a specific language
    """
    try:
        # Auto-detect language if not provided
        if language is None:
            language = i18n_service.get_language_from_request(dict(request.headers))
        
        # Validate language
        if language not in i18n_service.supported_languages:
            language = i18n_service.default_language
        
        # Get all translations for the language
        translations = i18n_service.translations.get(language, {})
        
        return {
            "language": language,
            "translations": translations,
            "meta": {
                "total_keys": len(translations),
                "language_name": "Deutsch" if language == "de" else "English"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting translations: {e}")
        return {
            "language": i18n_service.default_language,
            "translations": {},
            "error": "Failed to load translations"
        }

@i18n_router.get("/text/{key}")
async def get_text(
    key: str,
    request: Request,
    language: Optional[str] = Query(None, description="Language code (de/en)")
):
    """
    Get specific translation by key
    """
    try:
        # Auto-detect language if not provided
        if language is None:
            language = i18n_service.get_language_from_request(dict(request.headers))
        
        translated_text = i18n_service.get_text(key, language)
        
        return {
            "key": key,
            "text": translated_text,
            "language": language
        }
        
    except Exception as e:
        logger.error(f"Error getting text for key '{key}': {e}")
        return {
            "key": key,
            "text": key,  # Fallback to key
            "language": language or i18n_service.default_language,
            "error": "Translation not found"
        }

@i18n_router.get("/form-validation")
async def get_form_validation_messages(
    request: Request,
    language: Optional[str] = Query(None, description="Language code (de/en)")
):
    """
    Get form validation messages for frontend forms
    """
    try:
        # Auto-detect language if not provided
        if language is None:
            language = i18n_service.get_language_from_request(dict(request.headers))
        
        validation_messages = i18n_service.get_form_validation_messages(language)
        
        return {
            "language": language,
            "validation_messages": validation_messages
        }
        
    except Exception as e:
        logger.error(f"Error getting form validation messages: {e}")
        return {
            "language": i18n_service.default_language,
            "validation_messages": {},
            "error": "Failed to load validation messages"
        }

@i18n_router.get("/email-templates")
async def get_email_templates(
    request: Request,
    language: Optional[str] = Query(None, description="Language code (de/en)")
):
    """
    Get email template translations (for admin/testing purposes)
    """
    try:
        # Auto-detect language if not provided
        if language is None:
            language = i18n_service.get_language_from_request(dict(request.headers))
        
        templates = {
            "verification": i18n_service.get_email_template("verification", language),
            "report": i18n_service.get_email_template("report", language),
            "gdpr_deletion": i18n_service.get_email_template("gdpr_deletion", language),
            "gdpr_export": i18n_service.get_email_template("gdpr_export", language)
        }
        
        return {
            "language": language,
            "templates": templates
        }
        
    except Exception as e:
        logger.error(f"Error getting email templates: {e}")
        return {
            "language": i18n_service.default_language,
            "templates": {},
            "error": "Failed to load email templates"
        }

@i18n_router.post("/set-language")
async def set_default_language(
    language: str = Query(..., description="Language code to set as default")
):
    """
    Admin endpoint to change the default language
    """
    try:
        if language not in i18n_service.supported_languages:
            return {
                "success": False,
                "message": f"Unsupported language: {language}",
                "supported_languages": i18n_service.supported_languages
            }
        
        i18n_service.set_default_language(language)
        
        return {
            "success": True,
            "message": f"Default language set to {language}",
            "language": language
        }
        
    except Exception as e:
        logger.error(f"Error setting default language: {e}")
        return {
            "success": False,
            "message": "Failed to set default language",
            "error": str(e)
        }

@i18n_router.get("/detect-language")
async def detect_language(request: Request):
    """
    Detect user's preferred language from request headers
    """
    try:
        detected_language = i18n_service.get_language_from_request(dict(request.headers))
        
        return {
            "detected_language": detected_language,
            "supported_languages": i18n_service.supported_languages,
            "headers_checked": {
                "accept_language": request.headers.get("accept-language", ""),
                "user_agent": request.headers.get("user-agent", "")
            }
        }
        
    except Exception as e:
        logger.error(f"Error detecting language: {e}")
        return {
            "detected_language": i18n_service.default_language,
            "error": "Language detection failed"
        }