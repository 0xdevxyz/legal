"""
Complyo AI Fix Engine - Handlers

Spezifische Handler für verschiedene Fix-Typen
"""

from .legal_text_handler import LegalTextHandler
from .cookie_handler import CookieBannerHandler
from .accessibility_handler import AccessibilityHandler
from .code_handler import CodeFixHandler
from .guide_handler import GuideHandler

__all__ = [
    "LegalTextHandler",
    "CookieBannerHandler",
    "AccessibilityHandler",
    "CodeFixHandler",
    "GuideHandler"
]


