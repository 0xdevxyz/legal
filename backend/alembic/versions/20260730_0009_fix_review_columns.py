"""Fix-Review: die von der Admin-Queue erwarteten Spalten nachziehen.

Revision ID: 0009_fix_review_columns
Revises: 0008_leads_verification

Hintergrund: `admin_routes.py` (Fix-Review-Queue, approve/reject) liest
`website_id`, `issue_title`, `quality_gate_status`, `quality_gate_log`,
`reviewed_by` und `reviewed_at` aus `fix_application_audit` — keine dieser
Spalten existierte, der Endpunkt lief in 500. Das Quality-Gate-Ergebnis der
KI-Fix-Engine lag bisher nur in `fix_jobs.result` (JSONB) und war damit für
das Admin-Review unsichtbar.

Entscheidung des Betreibers (29.07.2026): Review-Kette fertigbauen.
`validated` wird sofort ausgeliefert, nur `pending_review` wartet auf
menschliche Freigabe.

`website_id` ist UUID — `tracked_websites.id` ist UUID, nicht Integer
(der Plan nahm zunächst Integer an; gegen die Live-DB verifiziert).
`ON DELETE SET NULL`, damit das Löschen einer Website den Audit-Trail
nicht mitreißt (Audit ist rechtssicheres Protokoll).

Rein additiv (`ADD COLUMN IF NOT EXISTS`).
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0009_fix_review_columns'
down_revision: Union[str, None] = '0008_leads_verification'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE fix_application_audit
            ADD COLUMN IF NOT EXISTS website_id          UUID
                REFERENCES tracked_websites(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS issue_title         TEXT,
            ADD COLUMN IF NOT EXISTS quality_gate_status VARCHAR(20)
                CHECK (quality_gate_status IN
                       ('validated', 'pending_review', 'approved', 'rejected')),
            ADD COLUMN IF NOT EXISTS quality_gate_log    JSONB,
            ADD COLUMN IF NOT EXISTS reviewed_by         VARCHAR(320),
            ADD COLUMN IF NOT EXISTS reviewed_at         TIMESTAMPTZ
    """)
    # Die Queue fragt ausschliesslich nach pending_review — partieller Index
    # haelt die Abfrage billig, egal wie gross der Audit-Trail wird.
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_faa_pending_review
            ON fix_application_audit (applied_at DESC)
            WHERE quality_gate_status = 'pending_review'
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_faa_pending_review")
    op.execute("""
        ALTER TABLE fix_application_audit
            DROP COLUMN IF EXISTS website_id,
            DROP COLUMN IF EXISTS issue_title,
            DROP COLUMN IF EXISTS quality_gate_status,
            DROP COLUMN IF EXISTS quality_gate_log,
            DROP COLUMN IF EXISTS reviewed_by,
            DROP COLUMN IF EXISTS reviewed_at
    """)
