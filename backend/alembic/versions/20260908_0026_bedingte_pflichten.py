"""Bedingte Pflichten an belegte Tatsachen binden statt an jede Seite

Der Selbstscan von complyo.de am 08.09.2026 ergab 13 Befunde, davon 9 aus
deklarativen Pruefungen: ein fehlender Ablehnen-Knopf in einem Cookie-Banner,
den die Seite nicht hat, ein fehlender USA-Hinweis fuer Transfers, die nicht
stattfinden, ein DSA-Transparenzbericht fuer eine Plattform, die es nicht gibt.

Ursache war die Gate-Form. Acht Pruefungen standen auf `{"always": true}` und
liefen damit auf JEDER Kundenseite; weitere gruendeten auf Stichwoertern, die
den Werbetext treffen ("cookie" trifft jede Seite, die ueber Cookies schreibt,
"anzeigen" das Verb). Beide Formen behaupten die Pflicht, statt sie zu pruefen.

Diese Revision traegt die tatsaechliche Bedingung nach: `applies_when.requires`
nennt die Tatsache, auf der die Pflicht beruht, und der Runner prueft sie gegen
den Scan-Kontext (compliance_engine/scan_kontext.py). Ist die Tatsache nicht
belegt, laeuft die Pruefung nicht.

Drei Nebenentscheidungen:

* `cookie-banner-ablehnen-button-erste-ebene` wird abgeschaltet. Sie prueft
  dasselbe wie `cookie-banner-reject-button-equal-prominence` (Existenz eines
  Ablehnen-Knopfes im Markup) und hat auf complyo.de denselben Befund ein
  zweites Mal erzeugt. Die Ebene, auf der der Knopf sitzt, unterscheidet keine
  der beiden Detektionen.
* Die beiden Google-Pruefungen bekommen ihr Gate ersetzt. Ihre Stichwoerter
  ("googletagmanager", "gtag", "ga4") wurden gegen den SICHTBAREN Seitentext
  geprueft und konnten dort nie stehen — die Pruefungen liefen seit ihrer
  Anlage auf keiner einzigen Seite. Ueber `consent_tracking` greifen sie jetzt
  dort, wo Google-Tracking tatsaechlich laeuft.
* `wcag-22-konsistente-hilfe` wird abgeschaltet. WCAG 2.2 SC 3.2.6 verlangt,
  dass ein VORHANDENER Hilfe-Mechanismus auf allen Seiten an derselben Stelle
  steht — nicht, dass es ihn gibt. Die Pruefung verlangte seine blosse
  Existenz und pruefte damit etwas anderes als ihr Titel sagt.
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0026_bedingte_pflichten"
down_revision: Union[str, None] = "0025_koepfe_zusammen"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# slug -> neues applies_when. Bewusst als VOLLSTAENDIGES Gate geschrieben und
# nicht als Teil-Update: wo die Stichwoerter nichts eingrenzen, sollen sie weg,
# nicht zusaetzlich zur Tatsache stehen.
GATES = {
    # --- Cookie-Banner: setzt einen Banner voraus --------------------------
    "cookie-banner-reject-button-equal-prominence": {"requires": ["consent_banner"]},
    "cookie-consent-gueltigkeitsdauer-info":        {"requires": ["consent_banner"]},
    "cookie-banner-usa-transfer-hinweis":           {"requires": ["consent_banner", "drittland_usa"]},
    "cookie-wall-alternative-option":               {"requires": ["consent_banner"]},
    "cookie-wall-alternative-information":          {"requires": ["consent_banner"]},
    # --- Tracking: setzt einwilligungspflichtiges Tracking voraus ----------
    "ttdsg-tracking-informationspflicht":           {"requires": ["consent_tracking"]},
    "dsk-web-analytics-widerspruchsrecht":          {"requires": ["consent_tracking"]},
    "google-analytics-einwilligung-cookie-banner":  {"requires": ["consent_tracking"]},
    "google-consent-mode-v2-implementation":        {"requires": ["consent_tracking"]},
    # --- Drittlandtransfer: setzt den Transfer voraus ----------------------
    "drittlandtransfer-usa-dokumentation":          {"requires": ["drittland_usa"]},
    "uk-drittlandtransfer-hinweis-datenschutz":     {"requires": ["drittland_uk"]},
    # --- Newsletter: setzt ein Anmeldeformular voraus ----------------------
    "newsletter-abmeldung-pflicht":                 {"requires": ["newsletter_formular"]},
    "newsletter-double-opt-in-formular":            {"requires": ["newsletter_formular"]},
    # --- DSA: Pflichten von Online-Plattformen ----------------------------
    # `plattform_ugc` / `plattform_werbung` erhebt heute noch niemand. Die
    # Pruefungen warten damit sichtbar auf ihren Detektor, statt auf Verdacht
    # jeder Seite mit dem Wort "Plattform" einen Transparenzbericht abzuverlangen.
    "dsa-transparenzbericht-online-plattform":      {"requires": ["plattform_ugc"]},
    "dsa-meldemechanismus-rechtswidrige-inhalte":   {"requires": ["plattform_ugc"]},
    "dsa-empfehlungssystem-transparenz":            {"requires": ["plattform_ugc"]},
    "dsa-werbeanzeigen-kennzeichnung":              {"requires": ["plattform_werbung"]},
}

ABSCHALTEN = {
    "cookie-banner-ablehnen-button-erste-ebene":
        "Doppelung zu cookie-banner-reject-button-equal-prominence",
    "wcag-22-konsistente-hilfe":
        "prueft Existenz statt Konsistenz (WCAG 2.2 SC 3.2.6)",
}


def upgrade() -> None:
    conn = op.get_bind()

    setze_gate = sa.text(
        "UPDATE compliance_checks SET applies_when = CAST(:gate AS jsonb), "
        "version = version + 1, updated_at = now() WHERE slug = :slug"
    )
    for slug, gate in GATES.items():
        conn.execute(setze_gate, {"gate": json.dumps(gate), "slug": slug})

    schalte_ab = sa.text(
        "UPDATE compliance_checks SET status = 'disabled', "
        "dismissal_reason = :grund, updated_at = now() "
        "WHERE slug = :slug AND status = 'active'"
    )
    for slug, grund in ABSCHALTEN.items():
        conn.execute(schalte_ab, {"grund": grund[:120], "slug": slug})


def downgrade() -> None:
    # Bewusst ohne Rueckweg: die alten Gates erzeugten auf jeder Kundenseite
    # Befunde ohne Rechtsgrundlage. Sie wiederherzustellen waere kein
    # Rollback, sondern ein Rueckfall.
    pass
