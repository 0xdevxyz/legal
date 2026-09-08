"""Wer hat die Freigabe erteilt: ein Mensch oder die Automatik?

Am 05.09.2026 kam die Umstellung: dokumentweite Fixes werden als `pending`
angelegt und muessen freigegeben werden. Damit ist die Zukunft geklaert, die
Vergangenheit aber nicht.

**Achtzehn Zeilen stehen auf `approved`, ohne dass je jemand gefragt wurde.**
skip-link 6, landmark-main 6, struktur 4, css-rule 2 — alle vor dem 05.09.
angelegt, als der Vorgabestatus noch `approved` war. Im Lernstand erscheinen
sie als achtzehn Zustimmungen und null Ablehnungen, also 100 % Annahmequote.

Das ist keine Kleinigkeit, sondern genau die Sorte Zahl, vor der der Lernstand
warnen soll. Ab 30 Belegen je Befundtyp darf ein Skill `aktiv` werden. Wuerden
diese achtzehn mitzaehlen, traegt spaeter ein Verfahren das Praedikat
"bewaehrt", dessen Bewaehrung nie stattgefunden hat.

Die Spalte trennt beides:

    'mensch'     jemand hat geklickt (set_dokument_status)
    'automatik'  ohne Rueckfrage gesetzt, in der Zeit vor dem 05.09.
    NULL         unbekannt oder noch nicht entschieden

Nachgetragen wird nur, was eindeutig ist: Zeilen, die vor der Freischaltung
der Freigaberoute zuletzt angefasst wurden, koennen nur von der Automatik
stammen — die Route gab es noch nicht. Alles danach bleibt NULL. Lieber eine
Luecke als eine erfundene Herkunft.

**Ausserdem: der Spaltenvorgabewert stand noch auf 'approved'.** Die Anwendung
uebergibt seit dem 05.09. immer 'pending', aber ein Einfuegen ohne
Statusangabe — ein Skript, eine spaetere Route, ein Handgriff in psql — waere
still wieder auf Auto-Freigabe gelaufen. Ein Vorgabewert, der der
Produktentscheidung widerspricht, ist eine Falle, die irgendwann zuschnappt.

**Diese Revision ist ein zweiter Zweig hinter 0023, kein Nachfolger von
0024_gen_docs_version.** Am 07.09. wurde parallel eine zweite Revision mit der
Nummer 0024 angelegt und auf die Produktionsdatenbank angewandt — sie liegt
dort aber bis heute als unversionierte Datei, in keinem Commit. Eine
Abhaengigkeit auf eine Revision zu setzen, die es in der Versionsverwaltung
nicht gibt, wuerde jede frische Auscheckung unbrauchbar machen: die Kette
braeche an einer Stelle, die niemand nachvollziehen kann.

Als Zweig geht beides: `alembic upgrade heads` wendet beide an, und sobald die
Schwesterrevision eingecheckt ist, fuehrt eine Merge-Revision die Koepfe
zusammen. Bis dahin schlaegt `alembic upgrade head` (Einzahl) fehl und
verlangt ein Ziel — unschoen, aber ehrlich: es gibt gerade wirklich zwei
Koepfe.

Revision ID: 0024_entscheidung_quelle
Revises: 0023_ablehngrund_pruefregeln
Create Date: 2026-09-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0024_entscheidung_quelle"
down_revision: Union[str, None] = "0023_ablehngrund_pruefregeln"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Deploy-Zeitpunkt von 0dd3425 ("dokumentweite Fixes kommen zur Freigabe").
# Vorher gab es POST /api/accessibility/approve-dokument nicht, eine Freigabe
# konnte also gar nicht von einem Menschen stammen.
FREIGABEWEG_SEIT = "2026-09-05 03:55:00"


def upgrade() -> None:
    op.add_column(
        "accessibility_document_fixes",
        sa.Column("entscheidung_quelle", sa.String(length=16), nullable=True),
    )

    # Nachtrag nur fuer den eindeutigen Fall. kontrast-css bleibt aussen vor:
    # dort steht die Entscheidung je Farbpaar im Payload, der Zeilenstatus ist
    # abgeleitet und wuerde hier eine Herkunft behaupten, die er nicht hat.
    op.execute(
        f"""
        UPDATE accessibility_document_fixes
           SET entscheidung_quelle = 'automatik'
         WHERE status = 'approved'
           AND fix_type <> 'kontrast-css'
           AND entscheidung_quelle IS NULL
           AND COALESCE(updated_at, created_at) < TIMESTAMP '{FREIGABEWEG_SEIT}'
        """
    )

    # Die Auswertung fragt: "wie viele davon hat wirklich jemand entschieden?"
    op.create_index(
        "ix_doc_fixes_entscheidung_quelle",
        "accessibility_document_fixes",
        ["entscheidung_quelle"],
    )

    # Der Vorgabewert widersprach seit dem 05.09. der Produktentscheidung.
    op.execute(
        "ALTER TABLE accessibility_document_fixes "
        "ALTER COLUMN status SET DEFAULT 'pending'"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE accessibility_document_fixes "
        "ALTER COLUMN status SET DEFAULT 'approved'"
    )
    op.drop_index(
        "ix_doc_fixes_entscheidung_quelle",
        table_name="accessibility_document_fixes",
    )
    op.drop_column("accessibility_document_fixes", "entscheidung_quelle")
