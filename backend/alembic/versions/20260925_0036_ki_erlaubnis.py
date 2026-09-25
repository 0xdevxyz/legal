"""Das Konto traegt, ob KI-Aufrufe erlaubt sind.

Anlass (25.09.2026): Die veroeffentlichte Datenschutzerklaerung sagt zu:

    "Wer das vermeiden moechte, kann die KI-gestuetzten Funktionen ungenutzt
     lassen; die technische Pruefung und die Reparaturen ohne Sprachmodell
     laufen vollstaendig auf unseren Servern in Deutschland."

Gemessen: der Satz stimmte nicht. Es gab keinen Schalter, und ungenutzt
lassen liess sich die KI auch nicht, weil sie am Scan haengt.
public_routes.py startet nach jedem Scan den
AccessibilityPostScanProcessor; findet der Scan Bilder ohne Alternativtext,
geht deren Adresse an Claude Vision ueber OpenRouter, also in die USA.
Gefragt wurde vorher nur das Tagesbudget und der Tarif, nicht der Kunde.

Vorbelegung 'true', und das ist eine bewusste Entscheidung, keine
Bequemlichkeit: die Datenschutzerklaerung beschreibt die KI-Nutzung als
Regelfall, und ein stillschweigendes Abschalten haette die Leistung
veraendert, die bestehende Kunden gekauft haben. Was der Wert NICHT ist: eine
Einwilligung. Die Rechtsgrundlage bleibt Art. 6 Abs. 1 lit. b DSGVO, und eine
Vorbelegung koennte eine Einwilligung ohnehin nicht tragen (Art. 4 Nr. 11).

Revision ID: 0036_ki_erlaubnis
Revises: 0035_scan_saeulen_rechtsraum
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0036_ki_erlaubnis"
down_revision: Union[str, None] = "0035_scan_saeulen_rechtsraum"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS ki_erlaubt BOOLEAN NOT NULL DEFAULT true
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN users.ki_erlaubt IS
        'false schaltet alle KI-Aufrufe im Kundenweg dieses Kontos ab (Alt-Texte, Fix-Vorschlaege, Erlaeuterungen). Umsetzung der Zusage in der Datenschutzerklaerung, die KI-gestuetzten Funktionen ungenutzt lassen zu koennen. Keine Einwilligung im Sinne von Art. 4 Nr. 11 DSGVO: die Rechtsgrundlage der Verarbeitung ist Art. 6 Abs. 1 lit. b.'
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS ki_erlaubnis_geaendert_am TIMESTAMPTZ
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN users.ki_erlaubnis_geaendert_am IS
        'Zeitpunkt der letzten Aenderung von ki_erlaubt. NULL heisst: nie geaendert, es gilt die Vorbelegung. Nachweisbar machen, wann ein Kunde widersprochen hat, gehoert zum Widerspruch selbst.'
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS ki_erlaubnis_geaendert_am")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS ki_erlaubt")
