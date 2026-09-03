"""Statische Kontrakt-Tests fuer die Drift-Migration 0015 (ohne DB).

Die Migration selbst laeuft nur beim Orchestrator (alembic upgrade head);
hier wird abgesichert, dass die Datei importierbar bleibt, korrekt an 0014
haengt und alle im Audit festgestellten Spalten additiv (IF NOT EXISTS)
anlegt — inkl. der beiden Sonderfaelle website_id-Typwechsel und
expires_at-Default.
"""
import importlib.util
import re
from pathlib import Path
from unittest import mock

MIGRATION = (
    Path(__file__).resolve().parent.parent
    / "alembic" / "versions" / "20260811_0015_audit_schema_drift.py"
)


def _lade_modul():
    spec = importlib.util.spec_from_file_location("mig_0015", MIGRATION)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _gesammeltes_sql(funktion):
    """Fuehrt upgrade()/downgrade() gegen ein gemocktes op aus und sammelt SQL."""
    saetze = []
    modul = _lade_modul()
    with mock.patch.object(modul, "op") as op_mock:
        op_mock.execute.side_effect = lambda sql, *a, **k: saetze.append(str(sql))
        getattr(modul, funktion)()
    return "\n".join(saetze)


def test_revisionskette_haengt_an_0014():
    modul = _lade_modul()
    assert modul.revision == "0015_audit_schema_drift"
    assert modul.down_revision == "0014_gdpr_deletion_requests"


def test_upgrade_ist_rein_additiv_und_vollstaendig():
    sql = _gesammeltes_sql("upgrade")

    erwartete_spalten = [
        # cookie_banner_configs
        "language", "requires_reconsent", "config_hash", "bannerless_mode",
        "tcf_enabled", "tcf_vendors", "age_verification_enabled",
        "age_verification_min_age", "geo_restriction_enabled", "geo_countries",
        "forwarding_enabled", "forwarding_target_sites",
        # cookie_custom_services
        "is_active", "updated_at",
        # leads
        "deletion_requested", "deletion_requested_at",
        # legal_updates
        "archived", "archived_at",
        # scan_history
        "legal_update_id",
    ]
    for spalte in erwartete_spalten:
        assert re.search(
            rf"ADD COLUMN IF NOT EXISTS {spalte}\b", sql
        ), f"Spalte {spalte} fehlt oder ist nicht mit IF NOT EXISTS angelegt"

    # Kein blankes ADD COLUMN ohne IF NOT EXISTS (Additivitaets-Kontrakt).
    assert not re.search(r"ADD COLUMN (?!IF NOT EXISTS)", sql)

    # Sonderfall 1: website_id-Typwechsel nur mit NULL-Guard.
    assert "USING NULL::uuid" in sql
    assert "RAISE EXCEPTION" in sql

    # Sonderfall 2: Retention-Default 24 Monate.
    assert "interval '24 months'" in sql


def test_downgrade_ist_invers_aber_schont_config_hash():
    sql = _gesammeltes_sql("downgrade")
    # config_hash existierte in Prod schon vor 0015 (Drift) und darf im
    # Downgrade nicht mit abgeraeumt werden.
    assert "config_hash" not in sql
    assert "interval '3 years'" in sql
    assert "USING NULL::integer" in sql
    for spalte in ["language", "tcf_vendors", "geo_countries", "legal_update_id",
                   "deletion_requested", "archived", "is_active"]:
        assert re.search(rf"DROP COLUMN IF EXISTS {spalte}\b", sql), spalte
