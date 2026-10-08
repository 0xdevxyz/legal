"""Der Kunde kann den Banner erzwingen, auch wenn die Seite nichts zu fragen hat.

Anlass (07.10.2026): steinhau.de zeigte den Banner mit dem Satz "Wir benoetigen
Ihre Einwilligung, bevor Sie unsere Website weiter besuchen koennen" und einem
Absatz zur Datenuebermittlung in die USA. Gemessen: keine Cookies, kein
Browser-Speicher, kein fremder Host, in der Konfiguration keine Dienste.

Der Banner erkennt das ab jetzt selbst und bleibt weg, wenn nichts zu
entscheiden ist (cookie_banner_v2.js, pruefeAnlass). Wer ihn trotzdem will, etwa
weil die Website bald einen Dienst bekommt oder der Kunde ihn schlicht
bevorzugt, setzt dieses Flag.

Vorbelegung false: die Selbstabschaltung gilt fuer alle, die nichts anderes
sagen. Das ist eine bewusste Entscheidung (Daniel, 08.10.2026), und das Flag
ist der Ausweg dazu. Die Abschaltung ist zusaetzlich an eine abgeschlossene
Pruefung im Browser des Besuchers gebunden; im Zweifel bleibt der Banner.

Revision ID: 0037_banner_erzwingen
Revises: 0036_ki_erlaubnis
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0037_banner_erzwingen"
down_revision: Union[str, None] = "0037b_rechtsaenderung_quittung"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE cookie_banner_configs
        ADD COLUMN IF NOT EXISTS banner_erzwingen BOOLEAN NOT NULL DEFAULT false
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN cookie_banner_configs.banner_erzwingen IS
        'true: der Banner erscheint immer, auch wenn die Pruefung im Browser keinen Anlass findet. false: der Banner bleibt weg, wenn Scan ohne Treffer und Laufzeitpruefung sauber sind.'
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE cookie_banner_configs DROP COLUMN IF EXISTS banner_erzwingen")
