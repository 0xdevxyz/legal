"""Ablehnungsgrund fuer Linktext-Fixes

Am 04.09.2026 bekam der Alt-Text-Weg eine Grunderfassung, weil der Generator
Ablehnungsgruende liest und nie welche bekam. Die Auswertung (Roadmap 2.1)
zeigte danach, dass fuenf von sechs Befundtypen ueberhaupt keinen Grund
erfassen koennen.

Beim Nachsehen zerfiel dieses "fuenf" in zwei sehr verschiedene Gruppen:

- **Linktexte** (`accessibility_link_fixes`) haben eine echte Entscheidung:
  die Oberflaeche zeigt "Freigeben" und "Ablehnen". Nur die Spalte fehlt.
  Diese Migration legt sie an.
- **kontrast-css** hat ebenfalls eine Entscheidung, aber sie steckt im
  JSONB-Payload (eine Zeile je Website, darin mehrere Farbpaare). Dort
  gehoert der Grund in den Eintrag, nicht in eine Tabellenspalte — deshalb
  keine Spalte dafuer.
- **skip-link, landmark-main, struktur, css-rule** werden beim Anlegen direkt
  als `approved` gespeichert. Es fragt nie jemand. Eine Grundspalte waere dort
  eine Spalte ohne Schreiber — der gleiche Fehler wie bei
  fix_acceptance_metrics, nur spiegelverkehrt. Sie bekommen keine.

Revision ID: 0021_ablehngrund_linktexte
Revises: 0020_drop_fix_acceptance_metrics
Create Date: 2026-09-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0021_ablehngrund_linktexte"
down_revision: Union[str, None] = "0020_drop_fix_acceptance_metrics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accessibility_link_fixes",
        sa.Column("rejected_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("accessibility_link_fixes", "rejected_reason")
