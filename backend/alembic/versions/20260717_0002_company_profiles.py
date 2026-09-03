"""Firmenprofil für den Pflichten-Report (Phase 7.2 Pflichtenradar).

Revision ID: 0002_company_profiles
Revises: baseline_2026_07
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0002_company_profiles'
down_revision: Union[str, None] = 'baseline_2026_07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS company_profiles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            answers JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS company_profiles")
