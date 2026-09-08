"""cookie-consent-gueltigkeitsdauer-info abschalten: nicht messbar wie beschrieben

0027 hatte den Wortlaut-Zwang "6 Monate" durch Muster ersetzt, die jede genannte
Dauer akzeptieren. Der erste Lauf danach zeigte, warum das nicht reicht: auf
complyo.de traf das Muster den Satz "...16 Jahre alt sind und Ihre
Einwilligung..." — die Altersangabe aus dem Einwilligungshinweis. Aus einem
Fehlalarm war ein Fehl-Freispruch geworden, beides aus derselben Ursache.

Die Ursache ist nicht das Muster, sondern der Zuschnitt der Pruefung. Sie
behauptet etwas ueber den BANNER ("Das Cookie-Consent-Banner informiert nicht
ueber die Gueltigkeitsdauer der Einwilligung"), durchsucht dafuer aber den
gesamten Seitenquelltext. Selbst ein perfektes Muster wuerde dort faelschlich
fuendig: jede Datenschutzerklaerung nennt Speicherdauern. Der deklarative
Runner kann seine Suche nicht auf den Bannerbereich beschraenken; er kennt nur
die ganze Seite.

Dazu kommt das Gewicht: die maximale Gueltigkeitsdauer im Banner zu nennen, ist
eine Empfehlung von DSK und CNIL, keine gesetzliche Pflicht mit Bussgeldfolge.
Eine Pruefung, die eine Empfehlung als 3.500-EUR-Befund ausweist und dabei in
beide Richtungen irren kann, gehoert nicht auf eine Kundenseite.

Bleibt als offener Punkt festgehalten: die Pflicht ist damit nicht geprueft.
Sobald der Runner einen Bannerbereich als Suchraum kennt, kann die Pruefung
zurueckkommen.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0028_gueltigkeitsdauer"
down_revision: Union[str, None] = "0027_cookie_pruefungen"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.get_bind().execute(
        sa.text(
            "UPDATE compliance_checks SET status = 'disabled', "
            "dismissal_reason = :grund, updated_at = now() "
            "WHERE slug = 'cookie-consent-gueltigkeitsdauer-info' AND status = 'active'"
        ),
        {"grund": "durchsucht die ganze Seite, behauptet aber etwas ueber den "
                  "Banner — irrt in beide Richtungen"},
    )


def downgrade() -> None:
    pass
