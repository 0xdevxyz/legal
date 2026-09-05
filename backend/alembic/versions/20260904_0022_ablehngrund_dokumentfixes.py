"""Ablehnungsgrund fuer dokumentweite Fixes

Bis heute wurden skip-link, landmark-main, struktur und css-rule beim Anlegen
direkt auf `approved` gesetzt und gingen ohne Rueckfrage live. Der Lernstand
wies sie deshalb als "nicht entscheidbar" aus: eine Ablehnungsquote von 0 %
bedeutete dort nicht "niemand lehnt ab", sondern "niemand wird gefragt".

Damit erfuhr complyo nie, dass eine Strukturreparatur danebenlag. Genau das
soll sich aendern — die Fixes kommen kuenftig zur Freigabe, und dafuer braucht
es einen Ort fuer den Ablehnungsgrund.

**Bestehende Freigaben bleiben unberuehrt.** Das ON CONFLICT in
save_document_fixes haelt einen einmal erteilten `approved`-Status fest
(`WHEN status = 'approved' THEN 'approved'`). Die 18 heute live stehenden
Reparaturen verschwinden also nicht von den Kundenseiten — nur neue warten auf
eine Entscheidung.

Revision ID: 0022_ablehngrund_dokumentfixes
Revises: 0021_ablehngrund_linktexte
Create Date: 2026-09-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0022_ablehngrund_dokumentfixes"
down_revision: Union[str, None] = "0021_ablehngrund_linktexte"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accessibility_document_fixes",
        sa.Column("rejected_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("accessibility_document_fixes", "rejected_reason")
