"""AVV-Fassung im Nachweis der Vertragsannahme festhalten

Bis zum 10.09.2026 gab es keinen Auftragsverarbeitungsvertrag. Sobald complyo
auf einer Kundenwebsite laeuft, verarbeitet es aber Daten der Besucher DIESER
Website: Einwilligungsprotokolle, die Verbindungsdaten beim Laden der Widgets
und die Inhalte der geprueften Seiten. Das ist Auftragsverarbeitung nach
Art. 28 DSGVO. Fehlt der Vertrag, verstoesst der KUNDE gegen Art. 28 Abs. 3 —
und complyo haftet als Auftragsverarbeiter daneben (Art. 83 Abs. 4 lit. a).

Der Vertrag wird jetzt mit der Registrierung in Textform geschlossen
(Art. 28 Abs. 9 DSGVO). Damit der Abschluss nachweisbar ist, haelt der
bestehende Nachweis auch die angenommene Fassung fest. Nullable, weil die
bereits registrierten Konten keine Fassung angenommen haben — deren Zustimmung
ist gesondert einzuholen, und eine erfundene Eintragung waere ein wertloser
Nachweis.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0030_avv_fassung"
down_revision: Union[str, None] = "0029_suchraum_banner"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE vertragsannahmen "
        "ADD COLUMN IF NOT EXISTS avv_version VARCHAR(32)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE vertragsannahmen DROP COLUMN IF EXISTS avv_version")
