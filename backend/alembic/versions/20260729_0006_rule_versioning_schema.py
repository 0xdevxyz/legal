"""Regel-Versionierung: die fehlenden Spalten und `rule_changelog` nachziehen.

Revision ID: 0006_rule_versioning_schema
Revises: 0005_cookie_ab_testing

Hintergrund: `compliance_engine/rule_versioning_service.py` ist gegen ein Schema
geschrieben, das es in der DB nie gab. `compliance_risk_matrix` hat nur
(id, category, issue_type, severity, fine_*, *_risk_euro, legal_basis,
description, created_at, updated_at) — der Service erwartet zusätzlich
`rule_version`, `valid_from`, `valid_until`, `is_active`, `market`,
`effective_date` sowie die Tabelle `rule_changelog`.

Folge: jeder Aufruf lief in eine `UndefinedColumnError`, die der jeweilige
Exception-Handler still zu `[]` / `False` verschluckt hat. Sichtbar wurde das im
Legal-Monitoring-Cron — `find_rules_affected_by_legal_update failed: column
"issue_category" does not exist` bei jedem einzelnen Update, danach
`0 rules` im Pipeline-Log. Damit war die Kette
"Gesetzesänderung erkannt → betroffene Regel versionieren → Änderung
protokollieren" faktisch tot, und `get_active_ruleset_snapshot()` lieferte für
die Scan-Protokollierung dauerhaft `ruleset_version: 0`.

Der Spaltenname `issue_category` wird NICHT nachgezogen — die Tabelle heißt
fachlich korrekt `category`; die drei Queries im Service aliasen jetzt darauf.

Rein additiv (`ADD COLUMN IF NOT EXISTS` / `CREATE TABLE IF NOT EXISTS`) —
keine Bestandsdaten werden verändert, `effective_date` wird für die 8
vorhandenen Regeln auf `created_at::date` gesetzt, damit sie im Snapshot
(`WHERE effective_date <= CURRENT_DATE`) nicht wegfallen.
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0006_rule_versioning_schema'
down_revision: Union[str, None] = '0005_cookie_ab_testing'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE compliance_risk_matrix
            ADD COLUMN IF NOT EXISTS rule_version   INTEGER NOT NULL DEFAULT 1,
            ADD COLUMN IF NOT EXISTS valid_from     DATE,
            ADD COLUMN IF NOT EXISTS valid_until    DATE,
            ADD COLUMN IF NOT EXISTS is_active      BOOLEAN NOT NULL DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS market         VARCHAR(8) NOT NULL DEFAULT 'DE',
            ADD COLUMN IF NOT EXISTS effective_date DATE
        """
    )

    # Bestandsregeln sollen im Snapshot auftauchen (effective_date <= today).
    op.execute(
        """
        UPDATE compliance_risk_matrix
        SET effective_date = COALESCE(effective_date, created_at::date, CURRENT_DATE),
            valid_from     = COALESCE(valid_from, created_at::date, CURRENT_DATE)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rule_changelog (
            id                           SERIAL PRIMARY KEY,
            rule_id                      INTEGER NOT NULL
                                         REFERENCES compliance_risk_matrix(id) ON DELETE CASCADE,
            rule_version                 INTEGER NOT NULL,
            change_type                  VARCHAR(32) NOT NULL,
            change_description           TEXT,
            legal_basis_ref              TEXT,
            triggered_by_legal_update_id INTEGER
                                         REFERENCES legal_updates(id) ON DELETE SET NULL,
            changed_by                   VARCHAR(64) NOT NULL DEFAULT 'system',
            changed_at                   TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_rule_changelog_rule "
        "ON rule_changelog (rule_id, changed_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_rule_changelog_legal_update "
        "ON rule_changelog (triggered_by_legal_update_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS rule_changelog")
    op.execute(
        """
        ALTER TABLE compliance_risk_matrix
            DROP COLUMN IF EXISTS rule_version,
            DROP COLUMN IF EXISTS valid_from,
            DROP COLUMN IF EXISTS valid_until,
            DROP COLUMN IF EXISTS is_active,
            DROP COLUMN IF EXISTS market,
            DROP COLUMN IF EXISTS effective_date
        """
    )
