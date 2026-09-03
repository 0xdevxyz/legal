"""vertragsannahmen: Nachweis, wer wann welche AGB-Fassung als Unternehmer angenommen hat

Die AGB beschraenken den Vertragsschluss auf Unternehmer nach Paragraf 14 BGB
und schliessen Verbrauchervertraege aus. Erhoben wurde diese Bestaetigung
bisher nirgends: die Registrierung zeigte nur den Satz "Mit der Registrierung
stimmen Sie unseren AGB zu". Eine Beschraenkung, die man nicht belegen kann,
haelt im Streitfall nicht, und damit greift die Verbraucher-Klauselkontrolle
nach Paragraf 309 BGB doch.

Zusaetzlich wird die AGB-Fassung mitgeschrieben. Das "Stand"-Datum der
AGB-Seite war ein rollendes new Date(), zeigte also immer den heutigen Tag und
konnte nie belegen, welche Fassung jemand gesehen hat.

BEWUSST OHNE Foreign Key auf users(id), wie schon bei gdpr_deletion_requests:
der Nachweis muss die Loeschung des Kontos ueberleben. email dient als
Schnappschuss zur Zuordnung.

users.id ist integer, NICHT uuid. Nachgesehen, nicht angenommen: ein
Typkonflikt an genau dieser Stelle hat schon einmal sechs Wochen lang jeden
Insert still verschluckt.

Revision ID: 0016_vertragsannahmen
Revises: 0015_audit_schema_drift
Create Date: 2026-09-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0016_vertragsannahmen"
down_revision: Union[str, None] = "0015_audit_schema_drift"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vertragsannahmen",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("agb_version", sa.String(length=32), nullable=True),
        sa.Column("unternehmer_bestaetigt", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("ip_adresse", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("angenommen_am", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_vertragsannahmen_user_id", "vertragsannahmen", ["user_id"])
    op.create_index("ix_vertragsannahmen_email", "vertragsannahmen", ["email"])


def downgrade() -> None:
    op.drop_index("ix_vertragsannahmen_email", table_name="vertragsannahmen")
    op.drop_index("ix_vertragsannahmen_user_id", table_name="vertragsannahmen")
    op.drop_table("vertragsannahmen")
