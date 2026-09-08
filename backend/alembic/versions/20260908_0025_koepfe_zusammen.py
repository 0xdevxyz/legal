"""Zwei Koepfe aus paralleler Arbeit zusammenfuehren

Am 07.09.2026 sind zwei Migrationen unabhaengig voneinander hinter
0023_ablehngrund_pruefregeln entstanden: 0024_gen_docs_version (fehlende
Spalten fuer generated_documents, aus der Baseline-Drift) und
0024_entscheidung_quelle (Herkunft der Freigaben bei Dokument-Fixes). Beide
liefen bereits gegen die Produktionsdatenbank, weil zwei getrennte
Arbeitsbaeume beide fuer sich genommen konsistent waren. Diese Revision fuegt
keine Schemaaenderung hinzu, sie erklaert Alembic nur, dass ab hier wieder ein
einziger Kopf gilt.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0025_koepfe_zusammen"
down_revision: Union[str, tuple, None] = (
    "0024_gen_docs_version",
    "0024_entscheidung_quelle",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
