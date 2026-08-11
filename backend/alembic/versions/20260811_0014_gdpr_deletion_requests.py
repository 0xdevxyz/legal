"""gdpr_deletion_requests: zweistufige Kontolöschung (Art. 17 DSGVO) für users

Bisher erfassten die Betroffenenrechte-Endpunkte nur die (leere) leads-Tabelle;
die 11 echten Konten in users waren unerreichbar. Löschanträge von Kunden
laufen jetzt zweistufig: Antrag (status='pending') → Bestätigungslauf
(status='confirmed' → Löschung → status='completed'). Vorbild ist das
Spaltenpaar leads.deletion_requested/deletion_requested_at.

BEWUSST OHNE Foreign Key auf users(id): Der Antrag ist der Nachweis der
Löschung (Rechenschaftspflicht, Art. 5 Abs. 2 DSGVO) und muss die Löschung
des Kontos überleben. email wird als Schnappschuss mitgeführt, damit der
Nachweis auch nach dem Wegfall der users-Zeile einem Vorgang zuordenbar bleibt.

Revision ID: 0014_gdpr_deletion_requests
Revises: 0013_wirkungsscan
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0014_gdpr_deletion_requests"
down_revision: Union[str, None] = "0013_wirkungsscan"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gdpr_deletion_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "requested_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("confirmed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        # Wer bestätigt hat (Admin-User-ID) — ebenfalls ohne FK, gleicher Grund.
        sa.Column("confirmed_by", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'completed', 'cancelled')",
            name="ck_gdpr_deletion_requests_status",
        ),
    )
    # Pro User höchstens EIN offener Antrag.
    op.create_index(
        "uq_gdpr_deletion_requests_offen",
        "gdpr_deletion_requests",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'confirmed')"),
    )
    op.create_index(
        "idx_gdpr_deletion_requests_status",
        "gdpr_deletion_requests",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("idx_gdpr_deletion_requests_status", table_name="gdpr_deletion_requests")
    op.drop_index("uq_gdpr_deletion_requests_offen", table_name="gdpr_deletion_requests")
    op.drop_table("gdpr_deletion_requests")
