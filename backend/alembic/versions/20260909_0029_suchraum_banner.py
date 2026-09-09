"""Gueltigkeitsdauer-Pruefung zurueckholen, diesmal mit Suchraum

0028 hatte `cookie-consent-gueltigkeitsdauer-info` abgeschaltet, weil sie
etwas ueber den Banner behauptete, aber die ganze Seite durchsuchte, und
deshalb in beide Richtungen irrte: sie verlangte woertlich "6 Monate"
(Fehlalarm bei einem Banner, das 12 Monate nennt) und traf nach dem Aufweichen
des Musters den Fliesstext "...16 Jahre alt sind und Ihre Einwilligung..."
(Fehl-Freispruch, ohne je im Banner gewesen zu sein).

Mit `detection.scope` gibt es den Suchraum jetzt. Die Pruefung kommt zurueck:
sie laeuft nur, wo ein Banner existiert (`requires`), und sieht nur dort nach
(`scope`).

Zwei Korrekturen am Gewicht, die dabei faellig sind:

* **severity `info` statt `warning`.** Art. 13 Abs. 2 lit. a DSGVO verlangt,
  ueber die Speicherdauer zu informieren — in den Datenschutzhinweisen. Dass
  die Gueltigkeitsdauer der Einwilligung im BANNER stehen muss, ist eine
  Empfehlung von DSK und CNIL, keine bussgeldbewehrte Pflicht. Als Verstoss
  ausgewiesen war das dieselbe Ueberzeichnung, die dieser ganze Durchgang
  beseitigt.
* **risk_euro 3.500 -> 0.** Ein Hinweis traegt kein Abmahnrisiko. Seit dem
  08.09. zaehlt die Anzeige `info` ohnehin getrennt und ohne Risikobeitrag;
  der alte Betrag stuende nur noch als tote Zahl in der Ablage.

Das laesst complyo.de bei 100/100 mit einem Hinweis mehr. Der Hinweis ist
zutreffend: der eigene Banner nennt die Gueltigkeitsdauer nicht.
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0029_suchraum_banner"
down_revision: Union[str, None] = "0028_gueltigkeitsdauer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DETECTION = {
    "type": "required_element",
    # Gesucht wird im Banner, nicht auf der Seite.
    "scope": "consent_banner",
    "url_paths": [],
    # Irgendeine genannte Dauer genuegt; die sechs Monate sind eine Empfehlung,
    # keine Vorgabe.
    "html_patterns": [
        r"\d{1,3}\s*(tage?n?|wochen?|monate?n?|jahre?n?)",
        r"\d{1,3}\s*(days?|weeks?|months?|years?)",
    ],
    "link_href_keywords": [],
    "link_text_keywords": [],
}

TITEL = "Banner nennt die Gültigkeitsdauer der Einwilligung nicht"

BESCHREIBUNG = (
    "Im Cookie-Banner ist keine Angabe zur Gültigkeitsdauer der Einwilligung "
    "erkennbar. DSK und CNIL empfehlen, sie dort zu nennen (Richtwert sechs "
    "Monate), damit Besucher wissen, wann erneut gefragt wird. Die "
    "Informationspflicht über Speicherdauern nach Art. 13 Abs. 2 lit. a DSGVO "
    "erfüllen Sie in den Datenschutzhinweisen; dies hier ist eine Empfehlung, "
    "kein Verstoß."
)

EMPFEHLUNG = (
    "Ergänzen Sie im Banner einen Satz wie „Ihre Einwilligung gilt 6 Monate, "
    "danach fragen wir erneut.“ und stellen Sie sicher, dass Ihr "
    "Consent-Speicher dieselbe Frist verwendet."
)


def upgrade() -> None:
    op.get_bind().execute(
        sa.text(
            "UPDATE compliance_checks SET "
            "  status = 'active', dismissal_reason = NULL, "
            "  severity = 'info', risk_euro = 0, "
            "  title = :titel, description = :beschreibung, recommendation = :empfehlung, "
            "  detection = CAST(:d AS jsonb), "
            "  applies_when = CAST(:g AS jsonb), "
            "  version = version + 1, updated_at = now() "
            "WHERE slug = 'cookie-consent-gueltigkeitsdauer-info'"
        ),
        {
            "titel": TITEL,
            "beschreibung": BESCHREIBUNG,
            "empfehlung": EMPFEHLUNG,
            "d": json.dumps(DETECTION),
            "g": json.dumps({"requires": ["consent_banner"]}),
        },
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text(
            "UPDATE compliance_checks SET status = 'disabled', updated_at = now() "
            "WHERE slug = 'cookie-consent-gueltigkeitsdauer-info'"
        )
    )
