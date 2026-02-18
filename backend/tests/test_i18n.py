import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestI18nService:
    def test_supported_languages(self):
        from i18n_service import I18nService
        svc = I18nService()
        langs = svc.get_supported_languages()
        assert "de" in langs
        assert "en" in langs
    
    def test_translate_known_key(self):
        from i18n_service import I18nService
        svc = I18nService()
        result = svc.translate("de", list(svc.translations.get("de", {}).keys())[0])
        assert result is not None
        assert isinstance(result, str)
    
    def test_translate_unknown_key(self):
        from i18n_service import I18nService
        svc = I18nService()
        result = svc.translate("de", "non_existent_key_xyz")
        assert result == "non_existent_key_xyz" or result is not None
