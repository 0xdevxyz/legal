"""Ablehnungsgrund fuer verworfene Pruefregeln

Von 159 automatisch erzeugten Checks sind 124 abgeschaltet — Annahmequote 0,22.
Der Grund wurde bisher als Freitext an `generation_notes` angehaengt, hinter
die Erzeugungsnotiz. Zwei Folgen:

1. **Nicht auswertbar.** Aus fuenfzig Formulierungen fuer dasselbe Problem wird
   kein Muster. Genau deshalb bekamen die Fix-Vorschlaege am 04.09. feste
   Gruende statt eines Freitextfelds.
2. **Meist gar nicht vorhanden.** Ein Grossteil der 124 wurde per Sammelaktion
   `audit-cleanup-2026-07` stillgelegt, ohne jede Begruendung.

Die neue Spalte nimmt den festen Grund auf. Der Freitext bleibt zusaetzlich in
`generation_notes` — er traegt Nuancen, die eine Auswahlliste nicht abbildet,
und die Notiz ist der Pruefpfad.

Revision ID: 0023_ablehngrund_pruefregeln
Revises: 0022_ablehngrund_dokumentfixes
Create Date: 2026-09-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0023_ablehngrund_pruefregeln"
down_revision: Union[str, None] = "0022_ablehngrund_dokumentfixes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "compliance_checks",
        sa.Column("dismissal_reason", sa.String(length=120), nullable=True),
    )
    # Die Auswertung fragt nach Gruenden verworfener Regeln.
    op.create_index(
        "ix_checks_dismissal_reason",
        "compliance_checks",
        ["dismissal_reason"],
        postgresql_where=sa.text("dismissal_reason IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_checks_dismissal_reason", table_name="compliance_checks")
    op.drop_column("compliance_checks", "dismissal_reason")
