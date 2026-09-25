"""wirkung: unplausible Meldungen kennzeichnen und die Fassung des Melders festhalten

Anlass (25.09.2026): Der oeffentliche Pruefnachweis von complyo.de zeigte
"33 Ziele nicht gefunden". Nachgerechnet stand in der Tabelle fuer eine
loqal.io-Unterseite `verfehlt=35` bei `erwartet=4`.

Das ist arithmetisch unmoeglich: man kann nicht mehr Ziele verfehlen, als es
ueberhaupt zu treffen gab. Insgesamt verletzten zwoelf Zeilen diese Invariante.
Ein echter Seitenaufruf mit dem heutigen Widget lieferte fuer dieselbe Seite
`verfehlt=5` bei `erwartet=5`, also stimmig.

Am 10.09.2026 wurde genau dieser Fehler schon einmal behoben (17d0a8f, "der
Pruefnachweis meldete einen Fehlalarm an den Kunden"). Er kam zurueck, weil
niemand ihn faengt: weder das Widget noch der Server pruefen die Invariante,
und keine Zeile weiss, welche Fassung sie geschrieben hat.

Zwei Spalten, zwei Zwecke:

`unplausibel`  Die Zeile bleibt erhalten, wird aber nicht veroeffentlicht.
               Loeschen waere bequemer und falsch: die Zeile ist der Beleg
               dafuer, dass etwas schieflief, und genau den braucht man beim
               naechsten Mal.

`melder`       Welche Fassung des Widgets die Zeile geschrieben hat. Ohne sie
               laesst sich nach dem naechsten Umbau nicht unterscheiden, ob
               eine Zahl alt oder falsch ist. Bestehende Zeilen bekommen NULL,
               das heisst "unbekannt", nicht "alt".

Revision ID: 0034_wirkung_plausibel
Revises: 0033_herkunft_ueberlebt_scan
Create Date: 2026-09-25
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0034_wirkung_plausibel"
down_revision: Union[str, None] = "0033_herkunft_ueberlebt_scan"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accessibility_wirkung",
        sa.Column("unplausibel", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "accessibility_wirkung",
        sa.Column("melder", sa.String(length=32), nullable=True),
    )

    # Den Bestand einmalig nachziehen. Nicht loeschen: die Zeilen sind der
    # Beleg. Sie verschwinden nur aus dem, was veroeffentlicht wird.
    op.execute(
        "UPDATE accessibility_wirkung SET unplausibel = TRUE "
        "WHERE verfehlt > erwartet"
    )

    # Nur ueber die unplausiblen: der Normalfall ist die grosse Mehrheit, und
    # ein Index darauf waere fast so gross wie die Tabelle.
    op.create_index(
        "ix_wirkung_unplausibel",
        "accessibility_wirkung",
        ["site_id"],
        postgresql_where=sa.text("unplausibel"),
    )


def downgrade() -> None:
    op.drop_index("ix_wirkung_unplausibel", table_name="accessibility_wirkung")
    op.drop_column("accessibility_wirkung", "melder")
    op.drop_column("accessibility_wirkung", "unplausibel")
