"""fix_acceptance_metrics entfernen — eine Messung, die nie gemessen hat

Die Tabelle wurde im Juli 2026 angelegt, um Annahme- und Ablehnungsquoten
erzeugter Fixes festzuhalten: fix_type, handler_used, user_decision,
rejection_reason, time_to_decision_seconds. Die Spalten waren gut gewaehlt.

Beschrieben hat sie nie jemand. Der einzige Schreibweg war
POST /api/v2/fixes/{fix_id}/outcome — registriert, erreichbar, funktionsfaehig
und ohne einen einzigen Aufrufer: kein Frontend, kein Backend, kein Cronjob.
Stand 04.09.2026: 0 Zeilen, seit ueber sechs Wochen.

**Nicht angetastet wird generated_fixes.** Der Weg /generate, /export,
/history, /limits ist verdrahtet und wird vom Dashboard benutzt; die Tabelle
ist leer, weil noch niemand einen Fix erzeugt hat, nicht weil sie tot waere.
Ein DROP dort wuerde die Fix-Erzeugung zerstoeren.

Warum das nicht einfach stehenbleiben kann: eine leere Messtabelle sieht in
jeder Uebersicht aus wie eine Messung, die nichts gefunden hat. Genau diese
Verwechslung hat am 04.09. Stunden gekostet — die eigentliche Bruchstelle im
Lernkreislauf lag woanders (fehlender Ablehnungsgrund bei den Alt-Texten,
Commit 1f7eb6c), und die verwaiste Tabelle hat davon abgelenkt.

Falls der Fix-Ablauf spaeter eine Freigabe bekommt, gehoert die Messung
dorthin, wo die Entscheidung faellt — serverseitig in den Freigabeweg, so wie
fuer die Alt-Texte gebaut. Ein Endpunkt, den der Client von sich aus rufen
muss, wird vergessen. Genau so ist dieser hier entstanden.

Der downgrade legt die Tabelle wieder an, damit die Kette umkehrbar bleibt.
Zeilen gehen dabei nicht verloren, es gab nie welche.

Revision ID: 0020_drop_fix_acceptance_metrics
Revises: 0019_rule_review_queue
Create Date: 2026-09-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0020_drop_fix_acceptance_metrics"
down_revision: Union[str, None] = "0019_rule_review_queue"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schutz gegen den Fall, dass doch jemand angefangen hat zu schreiben:
    # eine nicht leere Tabelle wird NICHT geloescht, die Migration bricht ab.
    verbindung = op.get_bind()
    vorhanden = verbindung.execute(sa.text("""
        SELECT count(*) FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'fix_acceptance_metrics'
    """)).scalar()
    if not vorhanden:
        return

    zeilen = verbindung.execute(
        sa.text("SELECT count(*) FROM fix_acceptance_metrics")
    ).scalar()
    if zeilen:
        raise RuntimeError(
            f"fix_acceptance_metrics enthaelt {zeilen} Zeilen — nicht mehr tot. "
            "Diese Migration loescht nur eine leere Tabelle; bitte erst pruefen, "
            "wer inzwischen schreibt."
        )

    op.execute("DROP INDEX IF EXISTS idx_fix_acceptance_job")
    op.drop_table("fix_acceptance_metrics")


def downgrade() -> None:
    op.create_table(
        "fix_acceptance_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fix_job_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fix_type", sa.String(length=100), nullable=True),
        sa.Column("handler_used", sa.String(length=100), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("presented_to_user_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_decision", sa.String(length=50), nullable=True),
        sa.Column("decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_to_decision_seconds", sa.Integer(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_fix_acceptance_job", "fix_acceptance_metrics", ["fix_job_id"]
    )
