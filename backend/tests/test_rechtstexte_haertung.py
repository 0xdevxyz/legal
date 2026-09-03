"""
Wächtertests für die Rechtstexte-Härtung (2026-08-11)
=====================================================

Abgedeckte Befunde:

1. Fence-Strip: _call_ai lieferte Markdown-Fences (```html ... ```) ungefiltert
   aus — der "Rechtstext" begann dann mit ``` statt mit <h1>.
2. Platzhalter-Blockade: Dokumente voller "[Firmenname]" wurden gespeichert und
   als fertig ausgeliefert. Jetzt bricht _save VOR dem Persistieren mit
   UnvollstaendigeAngabenError ab, die Route übersetzt in HTTP 422 mit
   Klartext. Ausnahme: der bewusste UNFERTIG-Fallback bei KI-Ausfall.
3. persisted-Feld: DB-Fehler beim Speichern wurden still geschluckt — jetzt
   meldet die Response persisted=false und das Log enthält ein Alarmwort.
4. Preview-Auth: GET /api/legal-texts/{type}/preview war öffentlich und damit
   ein LLM-Kosten-Vektor — jetzt Auth-Pflicht (401 ohne Token).
"""

import os
import re

import pytest
from unittest.mock import AsyncMock, MagicMock

from legal_text_generator import (
    DocumentType,
    GeneratedDocument,
    LegalTextGenerator,
    UnvollstaendigeAngabenError,
    find_placeholders,
)

_ROUTES_FILE = os.path.join(os.path.dirname(__file__), "..", "legal_text_routes.py")


# ============================================================================
# 1) Markdown-Fences werden aus der KI-Antwort entfernt
# ============================================================================

class TestFenceStrip:
    def test_html_fence_wird_entfernt(self):
        raw = "```html\n<h1>Impressum</h1>\n<p>Musterfirma GmbH</p>\n```"
        assert LegalTextGenerator._strip_markdown_fences(raw) == (
            "<h1>Impressum</h1>\n<p>Musterfirma GmbH</p>"
        )

    def test_fence_ohne_sprachangabe_wird_entfernt(self):
        raw = "```\n<h1>AGB</h1>\n```"
        assert LegalTextGenerator._strip_markdown_fences(raw) == "<h1>AGB</h1>"

    def test_sauberes_html_bleibt_unveraendert(self):
        raw = "<h1>Datenschutzerklärung</h1><p>Text</p>"
        assert LegalTextGenerator._strip_markdown_fences(raw) == raw

    def test_leere_antwort_faellt_nicht_um(self):
        assert LegalTextGenerator._strip_markdown_fences("") == ""
        assert LegalTextGenerator._strip_markdown_fences(None) == ""


# ============================================================================
# 2) Platzhalter-Erkennung + Blockade in _save
# ============================================================================

class TestPlatzhalterErkennung:
    def test_platzhalter_werden_gefunden(self):
        html = "<p>[Firmenname]<br>[Straße und Hausnummer]</p><p>E-Mail: [E-Mail-Adresse]</p>"
        gefunden = find_placeholders(html)
        assert "[Firmenname]" in gefunden
        assert "[Straße und Hausnummer]" in gefunden
        assert "[E-Mail-Adresse]" in gefunden

    def test_kurze_klammern_sind_keine_platzhalter(self):
        # Fußnoten/Zähler wie "[1]" oder "[12]" dürfen nicht blockieren
        assert find_placeholders("<p>Siehe [1] und [12].</p>") == []

    def test_unfertig_fallback_ist_ausgenommen(self):
        """Der bewusste UNFERTIG-Fallback bei KI-Ausfall darf NICHT als
        Platzhalter-Dokument blockiert werden — er ist bereits unmissverständlich
        als unfertig markiert."""
        gen = LegalTextGenerator(db_pool=None)
        fallback_html = gen._fallback_template("egal")
        assert 'data-document-status="incomplete"' in fallback_html
        assert find_placeholders(fallback_html) == []

    def test_fehlermeldung_nennt_die_platzhalter(self):
        err = UnvollstaendigeAngabenError(["[Firmenname]", "[PLZ]"])
        assert "[Firmenname]" in str(err)
        assert "[PLZ]" in str(err)


class _PoolDarfNichtAngefasstWerden:
    """DB-Attrappe, die laut wird, sobald jemand speichern will."""

    def acquire(self):
        raise AssertionError("DB darf bei Platzhalter-Dokumenten nicht angefasst werden")


class TestSaveBlockiertPlatzhalter:
    @pytest.mark.asyncio
    async def test_save_wirft_vor_dem_persistieren(self):
        gen = LegalTextGenerator(db_pool=_PoolDarfNichtAngefasstWerden())
        with pytest.raises(UnvollstaendigeAngabenError) as exc:
            await gen._save(
                user_id=1,
                doc_type=DocumentType.IMPRINT,
                language="de",
                html_content="<h1>Impressum</h1><p>[Firmenname], [Straße und Hausnummer]</p>",
                legal_update_id=None,
                regeneration_trigger="manual",
            )
        assert "[Firmenname]" in str(exc.value)


# ============================================================================
# 3) persisted-Feld: DB-Fehler werden gemeldet statt geschluckt
# ============================================================================

_HTML_OHNE_PLATZHALTER = (
    "<h1>Impressum</h1>"
    "<p>Angaben gemäß §5 DDG: Musterfirma GmbH, vertreten durch Max Mustermann</p>"
    "<p>Musterstraße 1, 12345 berlin</p>"
    "<p>Telefon: 030 123456, E-Mail: mail@musterfirma.de</p>"
    "<p>USt-ID: DE123456789, Handelsregister: HRB 12345, Amtsgericht Berlin</p>"
)


class _KaputterPool:
    """Simuliert einen DB-Ausfall beim Speichern."""

    def acquire(self):
        raise RuntimeError("DB nicht erreichbar")


def _pool_mit_doc_id(doc_id: int):
    conn = MagicMock()
    conn.execute = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=doc_id)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=conn)
    ctx.__aexit__ = AsyncMock(return_value=False)
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=ctx)
    return pool


class TestPersistedFeld:
    @pytest.mark.asyncio
    async def test_db_fehler_ergibt_persisted_false_und_alarm_log(self, caplog):
        gen = LegalTextGenerator(db_pool=_KaputterPool())
        gen._call_ai = AsyncMock(return_value=_HTML_OHNE_PLATZHALTER)

        with caplog.at_level("ERROR", logger="legal_text_generator"):
            result = await gen.generate_imprint(1, {"company_name": "Musterfirma GmbH"})

        assert result.persisted is False
        assert result.document_id is None
        # Alarmwort im Log, damit die Persistenz-Lücke im Monitoring auffällt
        assert any("ALARM" in rec.message for rec in caplog.records), (
            "DB-Fehler beim Speichern muss ein ERROR-Log mit Alarmwort erzeugen"
        )

    @pytest.mark.asyncio
    async def test_erfolgreiches_speichern_ergibt_persisted_true(self):
        gen = LegalTextGenerator(db_pool=_pool_mit_doc_id(42))
        gen._call_ai = AsyncMock(return_value=_HTML_OHNE_PLATZHALTER)

        result = await gen.generate_imprint(1, {"company_name": "Musterfirma GmbH"})

        assert result.persisted is True
        assert result.document_id == 42

    def test_response_modell_kennt_persisted(self):
        """Die Route muss das Feld durchreichen — das Response-Modell trägt es."""
        from legal_text_routes import LegalTextResponse

        assert "persisted" in LegalTextResponse.model_fields


# ============================================================================
# Route-Ebene: 422 bei Platzhaltern, persisted-Durchreichung, Preview-Auth
# ============================================================================

def _make_app(monkeypatch, generator):
    from fastapi import FastAPI
    import dependencies
    import legal_text_routes

    monkeypatch.setattr(dependencies, "get_db_pool", AsyncMock(return_value=MagicMock()))
    monkeypatch.setattr(legal_text_routes, "get_legal_text_generator", lambda pool: generator)

    app = FastAPI()
    app.include_router(legal_text_routes.router)
    return app, dependencies


def _client(app):
    from fastapi.testclient import TestClient

    return TestClient(app, raise_server_exceptions=False)


class TestRouteVerhalten:
    def test_platzhalter_ergeben_422_mit_klartext(self, monkeypatch):
        gen = MagicMock()
        gen.generate_imprint = AsyncMock(
            side_effect=UnvollstaendigeAngabenError(["[Firmenname]", "[Straße und Hausnummer]"])
        )
        app, dependencies = _make_app(monkeypatch, gen)
        app.dependency_overrides[dependencies.get_current_user] = lambda: {"user_id": 1, "id": 1}

        resp = _client(app).post(
            "/api/legal-texts/imprint/generate",
            json={"user_data": {"company_name": "X"}, "language": "de"},
            headers={"Authorization": "Bearer x"},
        )

        assert resp.status_code == 422, resp.text
        detail = resp.json()["detail"]
        assert "[Firmenname]" in detail
        assert "[Straße und Hausnummer]" in detail

    def test_generate_reicht_persisted_false_durch(self, monkeypatch):
        doc = GeneratedDocument(
            document_id=None,
            user_id=1,
            document_type=DocumentType.IMPRINT,
            language="de",
            html_content=_HTML_OHNE_PLATZHALTER,
            plain_text="Impressum",
            template_version="1.0",
            legal_update_id=None,
            regeneration_trigger="manual",
            is_active=True,
            generated_at="2026-08-11T00:00:00",
            disclaimer="Hinweis",
            metadata={},
            persisted=False,
        )
        gen = MagicMock()
        gen.generate_imprint = AsyncMock(return_value=doc)
        app, dependencies = _make_app(monkeypatch, gen)
        app.dependency_overrides[dependencies.get_current_user] = lambda: {"user_id": 1, "id": 1}

        resp = _client(app).post(
            "/api/legal-texts/imprint/generate",
            json={"user_data": {"company_name": "X"}, "language": "de"},
            headers={"Authorization": "Bearer x"},
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["persisted"] is False

    def test_preview_ohne_token_ergibt_401(self, monkeypatch):
        gen = MagicMock()
        app, _dependencies = _make_app(monkeypatch, gen)

        resp = _client(app).get(
            "/api/legal-texts/imprint/preview",
            params={"company_name": "Musterfirma GmbH"},
        )

        assert resp.status_code == 401, (
            f"Preview ohne Token muss 401 liefern (öffentlicher LLM-Kosten-Vektor), "
            f"war {resp.status_code}: {resp.text}"
        )


class TestPreviewAuthImQuelltext:
    """Statischer Wächter: schlägt an, sobald jemand die Auth-Pflicht der
    Preview-Route wieder entfernt — unabhängig von Test-Umgebung/DB."""

    def test_preview_signatur_verlangt_authentifizierten_user(self):
        with open(_ROUTES_FILE, encoding="utf-8") as fh:
            src = fh.read()
        m = re.search(
            r"async def preview_legal_text\((.*?)\n\):", src, re.S
        )
        assert m, "preview_legal_text nicht gefunden — Test anpassen"
        assert "get_current_user_id" in m.group(1), (
            "preview_legal_text hat keine Auth-Dependency mehr — die Route wäre "
            "wieder ein öffentlicher LLM-Kosten-Vektor"
        )
