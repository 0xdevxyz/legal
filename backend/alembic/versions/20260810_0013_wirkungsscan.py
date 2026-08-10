"""Wirkungsscan: dieselbe Seite ohne und mit complyo-Widget gemessen.

Der normale Scan blockiert complyos eigenes Widget — sonst misst er die
bereits reparierte Seite und ueberschreibt den Messwert mit einer Null. Der
Preis dieser richtigen Entscheidung: den AUSGELIEFERTEN Zustand hat nie jemand
gemessen. Der Pruefnachweis sagt "vorher 22, nachher 2", aber das "nachher"
stammt aus dem Scan-Browser, nicht vom echten Besucher.

Diese Tabelle haelt beide Messungen fest, damit aus einem Foto eine Reihe
wird: eine einzelne Messung sagt, wie es heute steht — erst der Verlauf sagt,
ob es haelt.

`lage` ist das Urteil in einem Wort: laeuft / wirksam / vollstaendig /
wirkungslos / verschlechterung / kein_widget. Der Fall "verschlechterung"
existiert wirklich: beim ersten Lauf trug complyos eigener Cookie-Banner-Knopf
weisse Schrift auf der Markenfarbe #1597a3 (3,5:1 statt 4,5:1) — MIT complyo
war ein Kontrastbefund MEHR da als ohne.

Wie die Wirkungstabelle ohne jede Besucherspalte: gespeichert werden Adresse,
Zaehler und das Messergebnis. Was nicht gespeichert werden kann, kann auch
nicht auslaufen.

Revision ID: 0013_wirkungsscan
Revises: 0012_wirkung
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0013_wirkungsscan"
down_revision: Union[str, None] = "0012_wirkung"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS accessibility_wirkungsscan (
            id           BIGSERIAL PRIMARY KEY,
            site_id      VARCHAR(100) NOT NULL,
            url          TEXT         NOT NULL,
            -- Fundstellen der beiden Messungen. Bewusst getrennt gespeichert
            -- und nicht als Differenz: eine Differenz laesst sich nicht mehr
            -- pruefen, zwei Zahlen schon.
            ohne_widget  INTEGER      NOT NULL,
            mit_widget   INTEGER      NOT NULL,
            lage         VARCHAR(32)  NOT NULL,
            ergebnis     JSONB        NOT NULL,
            gemessen_am  TIMESTAMP    NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_wirkungsscan_site
            ON accessibility_wirkungsscan (site_id, gemessen_am DESC);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_wirkungsscan_site;")
    op.execute("DROP TABLE IF EXISTS accessibility_wirkungsscan;")
