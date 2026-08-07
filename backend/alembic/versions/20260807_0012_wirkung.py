"""Wirksamkeitsueberwachung: was auf echten Seitenaufrufen ankommt.

Das Widget meldet je Seite, wie viele Reparaturen ein Ziel gefunden haben und
wie viele ins Leere liefen. Der zweite Wert ist der eigentliche: ein
ausgelieferter Fix ohne Ziel ist das Bild eines Theme-Updates, das eine Klasse
umbenannt hat — ohne diese Meldung faellt so etwas erst beim naechsten Scan
auf, womoeglich Wochen spaeter.

Bewusst OHNE jede Besucherspalte: keine IP, keine Kennung, kein Verweis, kein
User-Agent. Die Zeile sagt etwas ueber die SEITE aus, nicht ueber den Menschen
davor — deshalb sind es keine personenbezogenen Daten. Was nicht gespeichert
werden kann, kann auch nicht auslaufen.

Der Primaerschluessel ist (site_id, pfad): je Seite eine Zeile, die bei jedem
Aufruf aktualisiert wird. Kein Verlauf, kein Wachstum ohne Grenze.

Revision ID: 0012_wirkung
Revises: 0011_fix_backups_contents
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0012_wirkung"
down_revision: Union[str, None] = "0011_fix_backups_contents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS accessibility_wirkung (
            id           BIGSERIAL PRIMARY KEY,
            site_id      VARCHAR(100) NOT NULL,
            pfad         VARCHAR(200) NOT NULL,
            angewendet   INTEGER      NOT NULL DEFAULT 0,
            verfehlt     INTEGER      NOT NULL DEFAULT 0,
            erwartet     INTEGER      NOT NULL DEFAULT 0,
            je_art       JSONB        NOT NULL DEFAULT '{}'::jsonb,
            aufrufe      INTEGER      NOT NULL DEFAULT 1,
            zuerst       TIMESTAMP    NOT NULL DEFAULT NOW(),
            zuletzt      TIMESTAMP    NOT NULL DEFAULT NOW(),
            UNIQUE (site_id, pfad)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_wirkung_site "
        "ON accessibility_wirkung (site_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS accessibility_wirkung")
