"""Add jurisdiction columns (Internationalisierung Stufe 1: de + eu)

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-03

user_limits.jurisdiction  : Account-Default ('de')
tracked_websites/websites.jurisdiction : Pro-Site-Override (NULL = erben)

Guards: Die Alembic-Baseline (0001) enthält 'websites', aber nicht
'user_limits'/'tracked_websites' (diese entstehen über die SQL-Init-Skripte).
Alle ALTERs sind daher tabellen-existenz-geprüft, damit upgrade()/downgrade()
sowohl gegen die reine Baseline als auch gegen Produktions-DBs sauber laufen.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES_ADD = {
    'user_limits': "ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR(10) NOT NULL DEFAULT 'de'",
    'tracked_websites': "ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR(10) DEFAULT NULL",
    'websites': "ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR(10) DEFAULT NULL",
}


def upgrade() -> None:
    for table, alter in _TABLES_ADD.items():
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables
                           WHERE table_name = '{table}') THEN
                    EXECUTE 'ALTER TABLE {table} {alter}';
                END IF;
            END $$;
        """)


def downgrade() -> None:
    for table in _TABLES_ADD:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables
                           WHERE table_name = '{table}') THEN
                    EXECUTE 'ALTER TABLE {table} DROP COLUMN IF EXISTS jurisdiction';
                END IF;
            END $$;
        """)
