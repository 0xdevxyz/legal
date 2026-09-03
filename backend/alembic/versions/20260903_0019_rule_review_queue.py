"""knowledge_rule_review_queue: der letzte Schritt des Lernkreislaufs bekommt eine Ablage

Der Wissens-Cron endet mit "Schritt 5/5: Rule-Review fuer High-Impact Updates".
Findet er eine Rechtsaenderung, die einen bestehenden Check beruehrt, schreibt
er das in `knowledge_rule_review_queue` - eine Tabelle, die nie eine Migration
angelegt hat. Der Insert steht in einem try/except, das den Fehler als
"non-critical" protokolliert. Im Log steht seit Wochen dieselbe Zeile:

    2026-09-02 07:00:41 [WARNING] knowledge_updater:
    Rule-Review trigger fehlgeschlagen (non-critical):
    relation "knowledge_rule_review_queue" does not exist

Jede angestossene Regelpruefung ging damit verloren. Genau der Teil, der
complyo von einer Checkliste unterscheiden soll - dass eine neue Entscheidung
einen alten Check als ueberholt markiert - lief ins Leere.

Die Tabelle allein reicht nicht: geschrieben wurde an zwei Stellen, gelesen an
keiner. Eine Warteschlange ohne Leser ist nur eine leisere Art zu verlieren.
Deshalb kommt mit dieser Aenderung ein Ausleseweg dazu (siehe
legal_change_routes.py, /api/legal-changes/rule-reviews).

`status` unterscheidet, was noch zu tun ist, von dem, was erledigt oder bewusst
verworfen wurde. Ohne diese Spalte waechst die Ablage monoton und sagt nach
drei Monaten nichts mehr aus.

Dieselbe Revision legt `classification_drift_log` an. Der Grund ist derselbe
Befund an anderer Stelle: `ai_feedback_learning._trigger_learning_if_needed`
fragt die Tabelle ab, um zu entscheiden, ob genug neues Negativ-Feedback fuer
eine Prompt-Anpassung zusammengekommen ist. Die Abfrage steht in einem
try/except, das den Fehler nur protokolliert - die Anpassung waere beim ersten
abgegebenen Feedback still ausgeblieben. Aufgefallen ist es bisher nicht, weil
es noch keine echten Kunden gibt, die Feedback geben.

Die Tabelle bleibt zunaechst leer: geschrieben wird sie von
`cronjobs/drift_detector.py`, und der steht in keinem Crontab. Das schadet
hier nicht - die Abfrage faengt den leeren Fall mit COALESCE ab und faellt auf
ein 30-Tage-Fenster zurueck. Ob der Drift-Job scharf geschaltet wird, ist eine
Produktentscheidung und steht aus.

Das ON CONFLICT der beiden Schreiber nennt (check_name, knowledge_file), also
braucht es genau darauf einen eindeutigen Index - sonst laeuft der Insert in
einen Fehler statt in DO NOTHING.

Revision ID: 0019_rule_review_queue
Revises: 0018_waitlist_kampagne
Create Date: 2026-09-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0019_rule_review_queue"
down_revision: Union[str, None] = "0018_waitlist_kampagne"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_rule_review_queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        # rule_versioning_service schreibt hier mehrere Checks komma-getrennt
        # in ein Feld, knowledge_updater genau einen. Deshalb grosszuegig.
        sa.Column("check_name", sa.String(length=500), nullable=False),
        sa.Column("knowledge_file", sa.String(length=300), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        # law_areas kommt als Liste aus dem Wissensspeicher.
        sa.Column("law_areas", sa.ARRAY(sa.Text()), nullable=True),
        sa.Column("impact", sa.String(length=32), nullable=True),
        sa.Column(
            "status",
            sa.String(length=24),
            nullable=False,
            server_default="offen",
        ),
        sa.Column("bearbeitet_von", sa.String(length=200), nullable=True),
        sa.Column("bearbeitet_am", sa.DateTime(), nullable=True),
        sa.Column("notiz", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )

    # Muss zum ON CONFLICT (check_name, knowledge_file) der Schreiber passen.
    op.create_unique_constraint(
        "uq_rule_review_check_datei",
        "knowledge_rule_review_queue",
        ["check_name", "knowledge_file"],
    )

    # Die Admin-Ansicht fragt nach offenen Eintraegen, neueste zuerst.
    op.create_index(
        "ix_rule_review_status_datum",
        "knowledge_rule_review_queue",
        ["status", "created_at"],
    )

    # Verteilungsverschiebung der Klassifikation (KL-Divergenz gegen Baseline).
    # Spalten aus cronjobs/drift_detector.py und ai_feedback_learning.py.
    op.create_table(
        "classification_drift_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("check_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("kl_divergence", sa.Float(), nullable=True),
        sa.Column("baseline_verteilung", sa.JSON(), nullable=True),
        sa.Column("aktuelle_verteilung", sa.JSON(), nullable=True),
        sa.Column("alert_ausgeloest", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "ix_drift_log_datum",
        "classification_drift_log",
        ["check_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_drift_log_datum", table_name="classification_drift_log")
    op.drop_table("classification_drift_log")
    op.drop_index("ix_rule_review_status_datum", table_name="knowledge_rule_review_queue")
    op.drop_constraint(
        "uq_rule_review_check_datei",
        "knowledge_rule_review_queue",
        type_="unique",
    )
    op.drop_table("knowledge_rule_review_queue")
