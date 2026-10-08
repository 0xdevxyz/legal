"""legal_change_notifications bekommt die Spalten, die der Dienst benutzt.

Anlass (08.10.2026): GET /api/legal-notifications/confirm/<token> schrieb ins
Log

    Error confirming notification: column "confirmation_token" does not exist

Gemessen per information_schema: die Live-Tabelle hat id, user_id,
legal_change_id, notification_type, sent_at, read_at, clicked_at, status,
created_at. Das ist der Spaltensatz aus migration_legal_changes.sql vom
10.11.2025 (Planung fuer den Legal-Change-Monitor).
legal_notification_service.py schreibt und liest aber das Schema aus
add_legal_news_sources.sql vom 07.02.2026: legal_news_id, severity,
confirmation_token, action_required, action_deadline, confirmed_at. Beide
Dateien legen die Tabelle mit CREATE TABLE IF NOT EXISTS an; als die zweite
lief, stand die Tabelle schon, ihr CREATE tat nichts. Die Baseline vom 17.07.
hat diesen Stand eingefroren.

Folge: Es ist nie eine Benachrichtigung entstanden (0 Zeilen), Bestaetigen und
Verwerfen aus der Mail antworten immer "ungueltig", und die Zahl im
Dashboard-Menue (/stats) ist immer 0.

Warum ergaenzen und nicht den Dienst umbauen: die vorhandenen Spalten haben
keinen Schreiber. Kein Code fuegt eine Zeile mit legal_change_id ein, und
legal_changes, worauf der Fremdschluessel zeigt, ist live leer (0 Zeilen).
Der Monitor schreibt seit Juli nach legal_updates und
user_legal_notifications. Den Dienst auf ein Schema ohne Token umzustellen
hiesse, den Bestaetigungsweg neu zu bauen. Ergaenzen laesst die bestehenden
Spalten, ihren Fremdschluessel und ihre Vorbelegungen unberuehrt.

Alle Spalten sind NULL-faehig oder haben eine Vorbelegung, damit die Migration
auch auf einer Tabelle mit Zeilen laeuft. severity war im alten Schema
NOT NULL; der Dienst setzt sie immer, die Datenbank muss das nicht erzwingen.

Revision ID: 0037b_rechtsaenderung_quittung
Revises: 0036_ki_erlaubnis
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0037b_rechtsaenderung_quittung"
down_revision: Union[str, None] = "0036_ki_erlaubnis"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE legal_change_notifications
            ADD COLUMN IF NOT EXISTS legal_news_id INTEGER
                REFERENCES legal_news(id) ON DELETE CASCADE,
            ADD COLUMN IF NOT EXISTS severity VARCHAR(50),
            ADD COLUMN IF NOT EXISTS confirmation_token VARCHAR(255),
            ADD COLUMN IF NOT EXISTS action_required BOOLEAN NOT NULL DEFAULT false,
            ADD COLUMN IF NOT EXISTS action_deadline TIMESTAMP,
            ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP
        """
    )
    # Der Token ist der Schluessel der Links in der Mail. Doppelt vergeben
    # wuerde ein Klick eine fremde Benachrichtigung quittieren.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_legal_change_notifications_token
            ON legal_change_notifications (confirmation_token)
        """
    )
    # process_new_legal_changes sucht per LEFT JOIN, welche Meldung noch
    # keine Benachrichtigung hat.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_legal_change_notifications_news
            ON legal_change_notifications (legal_news_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_legal_change_notifications_user_status
            ON legal_change_notifications (user_id, status)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_legal_change_notifications_user_status")
    op.execute("DROP INDEX IF EXISTS idx_legal_change_notifications_news")
    op.execute("DROP INDEX IF EXISTS uq_legal_change_notifications_token")
    op.execute(
        """
        ALTER TABLE legal_change_notifications
            DROP COLUMN IF EXISTS confirmed_at,
            DROP COLUMN IF EXISTS action_deadline,
            DROP COLUMN IF EXISTS action_required,
            DROP COLUMN IF EXISTS confirmation_token,
            DROP COLUMN IF EXISTS severity,
            DROP COLUMN IF EXISTS legal_news_id
        """
    )
