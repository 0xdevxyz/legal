"""fix_freigaben: Beleg, dass der Kunde den Hinweis gesehen und den Fix freigegeben hat

fix_jobs haelt fest, WAS repariert wurde und fuer wen. Es haelt nicht fest,
DASS der Kunde vorher den rechtlichen Hinweis gesehen und aktiv bestaetigt hat.
Genau darauf kommt es an: Ziffer 8 der AGB legt dem Kunden die Pruefung vor der
Veroeffentlichung auf, und ein Mitverschulden nach Paragraf 254 BGB laesst sich
nur einwenden, wenn die Bestaetigung belegbar ist. Der Dialog zeigte den Hinweis
bisher nur an und vergass ihn sofort wieder.

hinweis_version haelt fest, WELCHE Fassung des Hinweises gezeigt wurde. Ohne das
belegt der Nachweis nur, dass irgendetwas bestaetigt wurde. Dieselbe Luecke gab
es beim Stand-Datum der AGB, das ein rollendes new Date() war.

BEWUSST OHNE Foreign Key auf fix_jobs oder users, wie bei
gdpr_deletion_requests und vertragsannahmen: der Nachweis muss den geloeschten
Job und das geloeschte Konto ueberleben.

Typen nachgesehen, nicht angenommen: fix_jobs.job_id ist uuid, users.id ist
integer. Ein Typkonflikt an dieser Stelle hat schon einmal sechs Wochen lang
jeden Insert still verschluckt.

Revision ID: 0017_fix_freigaben
Revises: 0016_vertragsannahmen
Create Date: 2026-09-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0017_fix_freigaben"
down_revision: Union[str, None] = "0016_vertragsannahmen"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fix_freigaben",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("issue_id", sa.String(length=255), nullable=True),
        sa.Column("fix_typ", sa.String(length=64), nullable=True),
        sa.Column("hinweis_version", sa.String(length=32), nullable=True),
        sa.Column("ip_adresse", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("bestaetigt_am", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_fix_freigaben_user_id", "fix_freigaben", ["user_id"])
    op.create_index("ix_fix_freigaben_job_id", "fix_freigaben", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_fix_freigaben_job_id", table_name="fix_freigaben")
    op.drop_index("ix_fix_freigaben_user_id", table_name="fix_freigaben")
    op.drop_table("fix_freigaben")
