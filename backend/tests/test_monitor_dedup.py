"""
Wächtertests: Legal-Monitor enthalluziniert (2026-08-11)

Abgedeckte Szenarien:
- Dedup OHNE Datumsfenster (lower(trim(title)); das alte published_at::date-
  Fenster hat 83× identische Einträge über Wochen erzeugt)
- Grounding: Promptbau enthält das RSS-News-Material und verbietet eigenes
  Wissen; bei 0 neuen News gibt es KEINEN LLM-Call
- Notifications nur bei Nicht-Duplikat (Monitor-Ebene UND Integration-Guard)
- Re-Generation nur bei severity high/critical

LLM und DB sind durchgehend gemockt.
"""

from datetime import datetime

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from legal_change_monitor import ChangeSeverity, LegalArea, LegalChange, LegalChangeMonitor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_db_pool(fetch=None, fetchval=None, execute=None, fetchrow=None):
    """Erstellt einen Mock asyncpg-Pool (Stil wie test_legal_update_pipeline)."""
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=fetch or [])
    conn.fetchval = AsyncMock(return_value=fetchval)
    conn.execute = AsyncMock(return_value=execute or "UPDATE 0")
    conn.fetchrow = AsyncMock(return_value=fetchrow)

    pool = MagicMock()
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    return pool, conn


def make_change(severity=ChangeSeverity.MEDIUM, title="DSGVO Anpassung 2025"):
    return LegalChange(
        id="chg-1",
        title=title,
        description="Teständerung",
        affected_areas=[LegalArea.DATENSCHUTZ],
        severity=severity,
        effective_date=datetime(2026, 9, 1),
        source="Testquelle",
        source_url="https://example.org/quelle",
        requirements=["Anforderung 1"],
    )


NEWS_ITEMS = [
    {
        "id": 11,
        "title": "BFSG-Übergangsfrist endet",
        "summary": "Ab sofort gelten die Anforderungen ohne Ausnahme.",
        "url": "https://example.org/bfsg",
        "source": "BfDI",
        "published_date": datetime(2026, 8, 10),
        "news_type": "regulation_change",
        "severity": "high",
        "keywords": ["bfsg"],
    },
]


# ---------------------------------------------------------------------------
# 1. Dedup ohne Datumsfenster
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dedup_vergleicht_titel_ohne_datumsfenster():
    """Die Duplikat-SELECT vergleicht lower(trim(title)) und hat KEIN Datumsfenster."""
    pool, conn = make_db_pool(fetchval=7)  # existierende Zeile gefunden
    monitor = LegalChangeMonitor("test-key", db_pool=pool)

    result = await monitor._save_change_to_db(make_change())

    assert result is None  # Duplikat -> nicht erneut gespeichert
    dedup_sql = conn.fetchval.call_args_list[0][0][0].lower()
    assert "lower(trim(title))" in dedup_sql
    assert "published_at::date" not in dedup_sql
    # Nur der Titel wird als Parameter übergeben — kein Datum
    assert conn.fetchval.call_args_list[0][0][1:] == ("DSGVO Anpassung 2025",)


@pytest.mark.asyncio
async def test_dedup_neue_aenderung_wird_gespeichert():
    """Ohne existierenden Titel wird gespeichert und die neue ID zurückgegeben."""
    pool, conn = make_db_pool()
    conn.fetchval = AsyncMock(side_effect=[None, 123])  # kein Duplikat, dann INSERT-ID
    monitor = LegalChangeMonitor("test-key", db_pool=pool)

    result = await monitor._save_change_to_db(make_change())

    assert result == 123
    insert_sql = conn.fetchval.call_args_list[1][0][0].lower()
    assert "insert into legal_updates" in insert_sql


# ---------------------------------------------------------------------------
# 2. Grounding: Promptbau + kein LLM-Call bei 0 News
# ---------------------------------------------------------------------------

def test_grounding_prompt_enthaelt_news_material():
    """Der Prompt enthält das News-Material und verbietet eigenes Wissen."""
    monitor = LegalChangeMonitor("test-key")

    prompt = monitor._build_monitoring_prompt(NEWS_ITEMS)

    assert "BFSG-Übergangsfrist endet" in prompt
    assert "https://example.org/bfsg" in prompt
    # Anti-Halluzination: nur Quellmaterial, kein eigenes Wissen
    assert "AUSSCHLIESSLICH" in prompt
    assert "eigenem Wissen" in prompt
    # Ausgabeformat bleibt der Vertrag, den _parse_legal_changes erwartet
    assert '"changes"' in prompt


@pytest.mark.asyncio
async def test_kein_llm_call_bei_null_news():
    """0 neue News seit letztem Lauf -> kein LLM-Call, Lauf endet mit 0 Änderungen."""
    monitor = LegalChangeMonitor("test-key", db_pool=MagicMock())
    monitor._fetch_news_since_last_run = AsyncMock(return_value=[])
    monitor._call_ai_api = AsyncMock()

    changes = await monitor.monitor_legal_changes()

    assert changes == []
    monitor._call_ai_api.assert_not_called()


@pytest.mark.asyncio
async def test_llm_call_bekommt_news_material():
    """Mit neuen News wird das LLM genau einmal mit dem Material aufgerufen."""
    monitor = LegalChangeMonitor("test-key", db_pool=MagicMock())
    monitor._fetch_news_since_last_run = AsyncMock(return_value=NEWS_ITEMS)
    monitor._call_ai_api = AsyncMock(return_value='{"changes": []}')

    changes = await monitor.monitor_legal_changes()

    assert changes == []
    monitor._call_ai_api.assert_called_once()
    prompt = monitor._call_ai_api.call_args[0][0]
    assert "BFSG-Übergangsfrist endet" in prompt


@pytest.mark.asyncio
async def test_ohne_db_pool_keine_freie_recherche():
    """Ohne db_pool gibt es keine Quellen — und damit auch keinen LLM-Call."""
    monitor = LegalChangeMonitor("test-key", db_pool=None)
    monitor._call_ai_api = AsyncMock()

    changes = await monitor.monitor_legal_changes()

    assert changes == []
    monitor._call_ai_api.assert_not_called()


# ---------------------------------------------------------------------------
# 3. Notifications nur bei Nicht-Duplikat
# ---------------------------------------------------------------------------

def _wire_monitor_for_persist(monitor, saved_id):
    """Verdrahtet monitor_and_persist-Abhängigkeiten mit Mocks."""
    monitor.monitor_legal_changes = AsyncMock(return_value=[make_change()])
    monitor._save_change_to_db = AsyncMock(return_value=saved_id)
    monitor.on_legal_change = AsyncMock(return_value={"regenerated": 0})
    monitor._generate_declarative_check = AsyncMock(return_value={"created": False})


@pytest.mark.asyncio
async def test_duplikat_loest_keine_pipeline_und_keine_notifications_aus():
    """Duplikat (_save_change_to_db -> None): keine Pipeline, keine Notifications, keine Re-Gen."""
    monitor = LegalChangeMonitor("test-key", db_pool=MagicMock())
    _wire_monitor_for_persist(monitor, saved_id=None)

    integration_cls = MagicMock()
    integration_cls.return_value.process_new_legal_update = AsyncMock(
        return_value={"rules_updated": 0, "websites_flagged": 0, "notifications_queued": 0}
    )

    with patch(
        "compliance_engine.legal_update_integration.LegalUpdateIntegration",
        integration_cls,
    ):
        summary = await monitor.monitor_and_persist()

    assert summary["new_saved"] == 0
    assert summary["duplicates"] == 1
    integration_cls.return_value.process_new_legal_update.assert_not_called()
    monitor.on_legal_change.assert_not_called()
    monitor._generate_declarative_check.assert_not_called()


@pytest.mark.asyncio
async def test_integration_guard_blockt_notifications_bei_duplikat():
    """LegalUpdateIntegration: Duplikat-Update erzeugt KEINE Notifications."""
    from compliance_engine.legal_update_integration import LegalUpdateIntegration

    pool, conn = make_db_pool()
    with patch(
        "compliance_engine.rule_versioning_service.RuleVersioningService.find_rules_affected_by_legal_update",
        new=AsyncMock(return_value=[]),
    ):
        integration = LegalUpdateIntegration(pool)
        integration._is_duplicate_update = AsyncMock(return_value=True)
        integration.create_scan_notification_for_users = AsyncMock()

        result = await integration.process_new_legal_update(
            {"id": 42, "title": "DSGVO Anpassung 2025", "update_type": "regulation_change"}
        )

    integration.create_scan_notification_for_users.assert_not_called()
    assert result["notifications_queued"] == 0


@pytest.mark.asyncio
async def test_integration_notifications_bei_nicht_duplikat():
    """LegalUpdateIntegration: Nicht-Duplikat erzeugt Notifications wie bisher."""
    from compliance_engine.legal_update_integration import LegalUpdateIntegration

    pool, conn = make_db_pool(execute="UPDATE 5")
    with patch(
        "compliance_engine.rule_versioning_service.RuleVersioningService.find_rules_affected_by_legal_update",
        new=AsyncMock(return_value=[]),
    ):
        integration = LegalUpdateIntegration(pool)
        integration._is_duplicate_update = AsyncMock(return_value=False)
        integration.create_scan_notification_for_users = AsyncMock()

        await integration.process_new_legal_update(
            {"id": 42, "title": "DSGVO Anpassung 2025", "update_type": "regulation_change"}
        )

    integration.create_scan_notification_for_users.assert_called_once()


# ---------------------------------------------------------------------------
# 4. Re-Generation nur bei severity high/critical
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "severity,erwartet_regen",
    [
        (ChangeSeverity.CRITICAL, True),
        (ChangeSeverity.HIGH, True),
        (ChangeSeverity.MEDIUM, False),
        (ChangeSeverity.LOW, False),
        (ChangeSeverity.INFO, False),
    ],
)
@pytest.mark.asyncio
async def test_regeneration_nur_bei_high_oder_critical(severity, erwartet_regen):
    """on_legal_change läuft nur bei high/critical; sonst skipped-Ergebnis."""
    monitor = LegalChangeMonitor("test-key", db_pool=MagicMock())
    _wire_monitor_for_persist(monitor, saved_id=55)
    monitor.monitor_legal_changes = AsyncMock(return_value=[make_change(severity=severity)])

    integration_cls = MagicMock()
    integration_cls.return_value.process_new_legal_update = AsyncMock(
        return_value={"rules_updated": 0, "websites_flagged": 0, "notifications_queued": 0}
    )

    with patch(
        "compliance_engine.legal_update_integration.LegalUpdateIntegration",
        integration_cls,
    ):
        summary = await monitor.monitor_and_persist()

    assert summary["new_saved"] == 1
    if erwartet_regen:
        monitor.on_legal_change.assert_called_once()
    else:
        monitor.on_legal_change.assert_not_called()
        assert summary["regeneration_results"][0].get("skipped") is True


# ---------------------------------------------------------------------------
# 5. Metrics-Wiring (Muster wie test_ki_lernkreislauf)
# ---------------------------------------------------------------------------

def test_monitor_zaehlt_openrouter_requests():
    """legal_change_monitor muss openrouter_requests_total inkrementieren."""
    import inspect
    import legal_change_monitor as mod

    src = inspect.getsource(mod)
    assert "openrouter_requests_total" in src
    assert '_openrouter_counter.labels(status="success")' in src
    assert '_openrouter_counter.labels(status="error")' in src
