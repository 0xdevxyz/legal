"""Kennzeichen: Bannerfarben folgen der Website.

Anlass (Daniel, 20.11.2026): Die Farben des Banners sollen automatisch aus der
Website kommen, auch fuer bestehende Konfigurationen. Bisher schrieb der Scan sie
nur beim Anlegen; bestehende behielten ihre Farben, weil ein Kunde sie bewusst
gewaehlt haben kann.

farben_automatisch: TRUE = der Scan (und der Wochenlauf) zieht die Farben der
                    Website nach (compliance_engine/farben_nachziehen.py).
                    FALSE = von Hand gewaehlt, wird nie ueberschrieben.

Voreinstellung FALSE, denn ohne Kennzeichen laesst sich nicht erkennen, ob ein
Mensch die Farben gewaehlt hat (revision zaehlt auch Scans mit). Nachgetragen wird nur,
was sicher nie gewaehlt wurde: Konfigurationen mit der Plattform-Standardfarbe als
Hauptfarbe (#7c3aed Widget-Vorgabe, #6366f1 Datenbank-Vorgabe).

Nicht Teil des grossen Konfigurations-SELECT und nicht Teil des UPDATE in
POST /config: ein Backend vor der Migration darf nicht mit 500 antworten, ein
Dashboard, das das Feld nicht kennt, darf es nicht loeschen.

Revision ID: 0039_farben_automatisch
Revises: 0038_marken_stil
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0039_farben_automatisch"
down_revision: Union[str, None] = "0038_marken_stil"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE cookie_banner_configs "
        "ADD COLUMN IF NOT EXISTS farben_automatisch BOOLEAN NOT NULL DEFAULT FALSE"
    )
    op.execute(
        """
        COMMENT ON COLUMN cookie_banner_configs.farben_automatisch IS
        'TRUE: Scan und Wochenlauf ziehen die Bannerfarben der Website nach. FALSE: von Hand gewaehlt, nie ueberschreiben.'
        """
    )
    op.execute(
        "UPDATE cookie_banner_configs SET farben_automatisch = TRUE "
        "WHERE lower(primary_color) IN ('#7c3aed', '#6366f1')"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE cookie_banner_configs DROP COLUMN IF EXISTS farben_automatisch")
