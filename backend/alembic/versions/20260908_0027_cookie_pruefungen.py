"""Cookie-Pruefungen: Doppelung raus, Wortlaut-Zwang raus

Nachlese zum Selbstscan vom 08.09.2026, nachdem 0026 die bedingungslosen Gates
beseitigt hatte. Zwei Cookie-Pruefungen feuerten weiterhin auf complyo.de —
diesmal mit korrekt belegter Voraussetzung (es GIBT dort einen Consent-Banner),
aber trotzdem zu Unrecht:

**cookie-banner-reject-button-equal-prominence** verlangte einen Knopf, dessen
Beschriftung in einer Stichwortliste steht ("ablehnen", "reject", "alle
ablehnen"). Der Ablehnen-Knopf von complyo heisst "Nur essenzielle Cookies
akzeptieren" — rechtlich genau der gleichwertige Ablehnen-Knopf, den die DSK
verlangt, aber in keiner Stichwortliste. Eine Liste deutscher Formulierungen
wird nie vollstaendig ("Ohne Einwilligung fortfahren", "Nur technisch
notwendige", "Ablehnen und schliessen").

Die harte Pruefung leistet ohnehin der fest verdrahtete Cookie-Check: er
klassifiziert die tatsaechlichen Knoepfe im gerenderten Banner
(_classify_consent_buttons) und vergleicht danach ihre Prominenz nach Flaeche,
Fuellung und Schriftgroesse (_assess_dark_pattern). Er meldet beides — den
fehlenden und den ungleichwertigen Ablehnen-Knopf. Die deklarative Pruefung war
eine schlechtere Zweitfassung derselben Pflicht.

**cookie-consent-gueltigkeitsdauer-info** verlangte woertlich "6 Monate". Ein
Banner, der "Ihre Einwilligung gilt 12 Monate" schreibt, erfuellt die
Informationspflicht und bekam trotzdem den Befund. Die Pflicht ist, die Dauer
zu NENNEN, nicht eine bestimmte Dauer zu waehlen — die sechs Monate sind eine
Empfehlung von CNIL und DSK, keine Vorgabe. Die Muster akzeptieren jetzt jede
genannte Dauer.
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0027_cookie_pruefungen"
down_revision: Union[str, None] = "0026_bedingte_pflichten"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DAUER_DETECTION = {
    "type": "required_element",
    "url_paths": [],
    # Irgendeine genannte Dauer im Zusammenhang mit der Einwilligung genuegt.
    "html_patterns": [
        r"einwilligung[^.]{0,80}?\d{1,3}\s*(tage?n?|wochen?|monate?n?|jahre?n?)",
        r"\d{1,3}\s*(tage?n?|wochen?|monate?n?|jahre?n?)[^.]{0,80}?einwilligung",
        r"(g(ü|ue)ltig(keit)?|dauer|laufzeit)[^.]{0,60}?\d{1,3}\s*(tage?n?|wochen?|monate?n?|jahre?n?)",
        r"consent[^.]{0,80}?\d{1,3}\s*(days?|weeks?|months?|years?)",
        r"\d{1,3}\s*(days?|weeks?|months?|years?)[^.]{0,80}?consent",
    ],
    "link_href_keywords": [],
    "link_text_keywords": [],
}


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text(
            "UPDATE compliance_checks SET status = 'disabled', "
            "dismissal_reason = :grund, updated_at = now() "
            "WHERE slug = 'cookie-banner-reject-button-equal-prominence' "
            "AND status = 'active'"
        ),
        {"grund": "Doppelung: der Cookie-Check prueft Ablehnen-Knopf und "
                  "Prominenz funktional statt per Stichwortliste"},
    )

    conn.execute(
        sa.text(
            "UPDATE compliance_checks SET detection = CAST(:d AS jsonb), "
            "version = version + 1, updated_at = now() "
            "WHERE slug = 'cookie-consent-gueltigkeitsdauer-info'"
        ),
        {"d": json.dumps(DAUER_DETECTION)},
    )


def downgrade() -> None:
    # Kein Rueckweg: die alten Fassungen erzeugten Befunde gegen Seiten, die
    # ihre Pflicht erfuellen.
    pass
