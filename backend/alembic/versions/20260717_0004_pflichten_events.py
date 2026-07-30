"""Pflichten-Events: Gesetzesänderungen → Katalog-Regeln (Phase 7.3).

Revision ID: 0004_pflichten_events
Revises: 0003_missing_tables
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0004_pflichten_events'
down_revision: Union[str, None] = '0003_missing_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS pflichten_events (
            id SERIAL PRIMARY KEY,
            legal_update_id INTEGER NOT NULL REFERENCES legal_updates(id) ON DELETE CASCADE,
            rule_id VARCHAR(100) NOT NULL,
            title VARCHAR(500) NOT NULL,
            summary TEXT,
            severity VARCHAR(50) DEFAULT 'info',
            source_url TEXT,
            published_at TIMESTAMP,
            effective_date DATE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (legal_update_id, rule_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_pflichten_events_rule ON pflichten_events(rule_id, published_at DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS pflichten_events")
