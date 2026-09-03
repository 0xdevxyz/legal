"""Baseline 2026-07 — eingefrorenes Produktionsschema.

Revision ID: baseline_2026_07
Revises: (Root — ersetzt die nie angewendeten Revisionen 0001/0002,
archiviert unter alembic/archived_versions/)

Quelle: pg_dump --schema-only der Produktions-DB vom 2026-07-17
(alembic/baseline_schema.sql). Auf der Produktions-DB wurde diese Revision
nur gestempelt (alembic stamp head), nie ausgeführt.

Ab dieser Revision gilt: JEDE Schema-Änderung ausschließlich als
Alembic-Revision. Keine losen SQL-Dateien mehr (siehe CONTRIBUTING.md).
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op

revision: str = 'baseline_2026_07'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_BASELINE_SQL = Path(__file__).resolve().parent.parent / "baseline_schema.sql"


def upgrade() -> None:
    sql = _BASELINE_SQL.read_text()
    # op.execute() scheitert mit asyncpg an Multi-Statement-SQL (Prepared
    # Statements). Die rohe asyncpg-Verbindung nutzt das Simple-Query-Protokoll
    # und führt den kompletten Dump in einem Rutsch aus.
    from sqlalchemy.util import await_only
    driver_conn = op.get_bind().connection.driver_connection
    await_only(driver_conn.execute(sql))
    # pg_dump leert den search_path — zurücksetzen, sonst findet Alembic
    # seine alembic_version-Tabelle nicht mehr.
    await_only(driver_conn.execute("SET search_path = public"))


def downgrade() -> None:
    raise NotImplementedError(
        "Baseline kann nicht heruntermigriert werden — DB neu aufsetzen."
    )
