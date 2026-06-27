"""
Unit-Tests für den internen Rechtstexte-Generator (legal_text_generator.py).

Diese Tests sichern die Regressionen ab, die im Audit gefunden wurden:
- Template-Auflösung für ALLE Dokumenttypen × DE/EN (kein leeres Fallback mehr)
- user_data wird in den DB-Metadaten persistiert (Voraussetzung für Auto-Update)
- _build_prompt füllt Platzhalter inkl. generated_at

Sie laufen ohne DB/HTTP: _save wird gemockt, _call_ai nicht aufgerufen.
"""

import json
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from legal_text_generator import LegalTextGenerator, DocumentType  # noqa: E402


def _bare_generator() -> LegalTextGenerator:
    """Instanz ohne __init__ (kein DB-Pool nötig) für reine Logik-Tests."""
    return LegalTextGenerator.__new__(LegalTextGenerator)


class TestTemplateResolution:
    @pytest.mark.parametrize("doc_type", list(DocumentType))
    @pytest.mark.parametrize("language", ["de", "en"])
    def test_template_loads_non_empty(self, doc_type, language):
        """Jeder Dokumenttyp muss in DE und EN ein echtes Template laden —
        nicht das leere 'Erstelle ...'-Fallback (Regression: cookie-policy-Bug)."""
        gen = _bare_generator()
        tpl = gen._load_template(doc_type, language)
        assert tpl, f"Template leer für {doc_type.value}/{language}"
        assert not tpl.startswith("Erstelle "), (
            f"Fallback statt echtem Template für {doc_type.value}/{language}"
        )
        # Muss zumindest den company_name-Slot enthalten
        assert "{{company_name}}" in tpl

    def test_cookie_policy_uses_hyphen_filename(self):
        """Regression: COOKIE_POLICY-Wert ist 'cookie-policy' (Bindestrich)."""
        assert DocumentType.COOKIE_POLICY.value == "cookie-policy"
        gen = _bare_generator()
        tpl = gen._load_template(DocumentType.COOKIE_POLICY, "de")
        assert "Cookie" in tpl


class TestPromptBuilding:
    def test_placeholders_filled(self):
        gen = _bare_generator()
        template = "Firma: {{company_name}}, Mail: {{email}}, Stand: {{generated_at}}"
        prompt = gen._build_prompt(
            template,
            {"company_name": "ACME GmbH", "email": "a@b.de"},
            "laws",
            DocumentType.IMPRINT,
        )
        assert "ACME GmbH" in prompt
        assert "a@b.de" in prompt
        # generated_at wird automatisch ergänzt -> kein roher Platzhalter mehr
        assert "{{generated_at}}" not in prompt
        assert "{{company_name}}" not in prompt

    def test_doc_label_present(self):
        gen = _bare_generator()
        prompt = gen._build_prompt("{{company_name}}", {"company_name": "X"}, "", DocumentType.WITHDRAWAL)
        assert "Widerrufs" in prompt


class TestSavePersistsUserData:
    """Regression: Auto-Update wurde übersprungen, weil user_data nie in der DB
    landete. Wir prüfen, dass _save user_data in die Metadaten schreibt."""

    @pytest.mark.asyncio
    async def test_save_writes_user_data_into_metadata(self):
        captured = {}

        class FakeConn:
            async def execute(self, *args, **kwargs):
                return None

            async def fetchval(self, query, *params):
                # params-Reihenfolge: user_id, doc_type, language, html, content, metadata
                captured["metadata"] = params[5]
                return 123

        class _AcquireCtx:
            async def __aenter__(self):
                return FakeConn()

            async def __aexit__(self, *exc):
                return False

        class FakePool:
            def acquire(self):
                return _AcquireCtx()

        gen = _bare_generator()
        gen.db_pool = FakePool()

        user_data = {"company_name": "ACME GmbH", "email": "a@b.de"}
        doc_id = await gen._save(
            user_id=42,
            doc_type=DocumentType.IMPRINT,
            language="de",
            html_content="<h1>X</h1>",
            legal_update_id=None,
            regeneration_trigger="manual",
            user_data=user_data,
        )

        assert doc_id == 123
        meta = json.loads(captured["metadata"])
        assert meta["user_data"] == user_data
        assert meta["is_active"] is True
        assert meta["language"] == "de"
