"""Schrift und Ecken der Website fuer den Cookie-Banner.

Anlass (Daniel, 12.11.2026): Farben und Logo kommen schon aus dem Design der
Website, Schrift und Ecken waren im Widget fest eingestellt. Der Scan misst beides
im selben Browser-Durchlauf (compliance_engine/marken_stil.py) und legt es hier ab.

marken_schrift: Schriftfamilie des Fliesstextes, nur bereinigte Namen
                (compliance_engine/marken_stil.py, nie ungeprueft in ein <style>).
marken_radius:  Eckenradius des Hauptknopfs in Pixeln, 0 bis 24; 100 heisst Pille.

Beide NULL: der Banner bleibt bei seiner Standardschrift und seinen Standardecken.
Nicht Teil des grossen Konfigurations-SELECT und nicht Teil von POST /config: ein
Dashboard, das die Felder nicht kennt, kann sie nicht loeschen.

Revision ID: 0038_marken_stil
Revises: 0037_kanal_herkunft
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0038_marken_stil"
down_revision: Union[str, None] = "0037_kanal_herkunft"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE cookie_banner_configs ADD COLUMN IF NOT EXISTS marken_schrift TEXT")
    op.execute("ALTER TABLE cookie_banner_configs ADD COLUMN IF NOT EXISTS marken_radius SMALLINT")
    op.execute(
        """
        COMMENT ON COLUMN cookie_banner_configs.marken_schrift IS
        'Schriftfamilie des Fliesstextes der Website, vom Scan gemessen und bereinigt. NULL: Standardschrift des Banners.'
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN cookie_banner_configs.marken_radius IS
        'Eckenradius des Hauptknopfs der Website in px (0 bis 24), 100 = Pille. NULL: Standardecken des Banners.'
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE cookie_banner_configs DROP COLUMN IF EXISTS marken_radius")
    op.execute("ALTER TABLE cookie_banner_configs DROP COLUMN IF EXISTS marken_schrift")
