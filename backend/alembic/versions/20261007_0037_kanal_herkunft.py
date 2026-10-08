"""kanal_herkunft: aus welchem Kanal kam eine Registrierung, aus welchem ein Kauf

Anlass ist die Entscheidungsregel nach Woche 45 des Launchplans: "Kaeufe je
Kanal". Die Warteliste speichert utm_source und utm_content seit dem 02.09.
(Migration 0018). Registrierung und Kauf taten das bisher nicht:

* Die Registrierung kannte die Herkunft nur in der Adresszeile und im
  sessionStorage des Browsers. In die Datenbank gelangte sie nie, ein
  kostenloses Konto war also keinem Kanal zuzuordnen.
* Der Kauf trug sie (seit PR #10) in die Stripe-Metadaten, aber der Webhook
  schrieb sie nicht in die Datenbank. Wer "Kaeufe je Kanal" zaehlen wollte,
  haette das Live-Konto von Stripe abfragen muessen, also mit einem
  Stripe-Schluessel an der Auswertung haengen.

Beide Tabellen sind Zusatz, nichts im Kaufweg haengt von ihnen ab: die
Schreibstellen sind best effort (`backend/herkunft.py`), eine fehlende Tabelle
blockiert weder Registrierung noch Freischaltung.

users.id ist integer (nachgesehen, nicht angenommen). Beide Tabellen
kaskadieren auf users(id): die Kampagnenherkunft eines Kontos ist kein
Nachweis, den ein Loeschantrag ueberleben muss (anders als vertragsannahmen),
und `gdpr_retention_service._LOESCH_STATEMENTS` verlaesst sich fuer solche
Tabellen auf das ON DELETE CASCADE.

`kauf_herkunft.stripe_subscription_id` ist der Primaerschluessel, damit
Webhook-Wiederholungen und der verify-checkout-Fallback denselben Kauf nicht
doppelt eintragen. `plan` ist der Tarif aus den Checkout-Metadaten, weil
`subscriptions.plan_type` bei `customer.subscription.created` fest auf 'pro'
gesetzt wird.

Revision ID: 0037_kanal_herkunft
Revises: 0036_ki_erlaubnis
Create Date: 2026-10-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0037_kanal_herkunft"
down_revision: Union[str, None] = "0037_banner_erzwingen"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_UTM = ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")


def _utm_spalten():
    # Laengen wie waitlist_leads (Migration 0018); beschnitten wird vor dem
    # Schreiben, ein ueberlanger Wert sprengt keinen Insert.
    return [sa.Column(name, sa.String(length=120), nullable=True) for name in _UTM]


def upgrade() -> None:
    op.create_table(
        "registrierung_herkunft",
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        *_utm_spalten(),
        sa.Column("erfasst_am", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_table(
        "kauf_herkunft",
        sa.Column("stripe_subscription_id", sa.String(length=255), primary_key=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan", sa.String(length=20), nullable=True),
        *_utm_spalten(),
        sa.Column("erfasst_am", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_kauf_herkunft_user_id", "kauf_herkunft", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_kauf_herkunft_user_id", table_name="kauf_herkunft")
    op.drop_table("kauf_herkunft")
    op.drop_table("registrierung_herkunft")
