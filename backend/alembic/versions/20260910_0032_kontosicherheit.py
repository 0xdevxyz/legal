"""Kontosicherheit: Passwort zuruecksetzen, E-Mail bestaetigen, zweiter Faktor, Loeschprotokoll

Prüfung vom 10.09.2026. Fünf Lücken, die alle dieselbe Form hatten: die Spalte
oder der Vorgang war gedacht, aber nirgends gebaut.

- `users.is_verified` stand seit dem ersten Schema in der Tabelle und wurde von
  keiner Route je gesetzt. Es gab keinen Bestätigungsweg für Konten, nur einen
  für Leads (`email_verifications`, Fremdschlüssel auf `leads`).
- Ein vergessenes Passwort war ein verlorenes Konto.
- Kein zweiter Faktor, obwohl ein complyo-Konto auf fremden Websites Code
  ausliefern und in verbundene Git-Depots schreiben kann.
- Kein Nachweis darüber, was wann nach welcher Frist gelöscht wurde
  (Art. 5 Abs. 2 DSGVO).

Revision ID: 0032_kontosicherheit
Revises: 0031_banner_fassung_im_protokoll
Create Date: 2026-09-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0032_kontosicherheit"
down_revision: Union[str, None] = "0031_banner_fassung_im_protokoll"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _einmal_token(name: str) -> None:
    """
    Passwort-Zurücksetzen und E-Mail-Bestätigung haben dieselbe Form: ein
    Token, der einem Konto gehört, einmal gilt und abläuft. Zwei Tabellen statt
    einer mit Typspalte, weil die Fristen und die Aufräumregeln verschieden
    sind und eine gemeinsame Tabelle nur eine Bedingung mehr in jeder Abfrage
    wäre.
    """
    op.create_table(
        name,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        # Nur der Hash. Der Token selbst existiert ausschliesslich in der Mail;
        # wer die Datenbank liest, bekommt keine gültigen Zurücksetzungen.
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("gueltig_bis", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("eingeloest_am", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ip_adresse", sa.String(length=45), nullable=True),
        sa.Column("erstellt_am", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    # Eindeutig, damit derselbe Hash nicht zweimal existieren kann, und weil
    # das Einlösen genau über diese Spalte sucht.
    op.create_index(f"ux_{name}_token", name, ["token_hash"], unique=True)
    op.create_index(f"ix_{name}_user", name, ["user_id"])


def upgrade() -> None:
    _einmal_token("passwort_reset")
    _einmal_token("email_bestaetigung")

    # -----------------------------------------------------------------------
    # Zweiter Faktor
    # -----------------------------------------------------------------------
    op.create_table(
        "user_totp",
        # Ein Konto, ein Geheimnis. Der Primärschlüssel ist die user_id selbst;
        # ein zweites TOTP-Geheimnis pro Konto hätte keine Bedeutung.
        sa.Column("user_id", sa.Integer(), primary_key=True),
        # Fernet-Chiffre, Schlüssel COMPLYO_2FA_ENC_KEY. Im Klartext wäre der
        # zweite Faktor nur eine zweite Kopie des ersten in derselben Datenbank.
        sa.Column("geheimnis_chiffre", sa.Text(), nullable=False),
        sa.Column("erstellt_am", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        # Erst gesetzt, wenn der Nutzer einen gültigen Code eingetippt hat.
        # Ohne das liesse sich ein Konto durch einen abgebrochenen
        # Einrichtungsversuch aussperren.
        sa.Column("bestaetigt_am", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "user_wiederherstellungscodes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        # bcrypt wie beim Passwort: ein Wiederherstellungscode ist ein Passwort
        # mit einer einzigen Verwendung.
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("benutzt_am", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("erstellt_am", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_wiederherstellungscodes_user", "user_wiederherstellungscodes",
                    ["user_id"])

    # -----------------------------------------------------------------------
    # Löschfristen
    # -----------------------------------------------------------------------
    op.add_column(
        "users",
        sa.Column("loeschung_angekuendigt_am", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "loeschprotokoll",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        # Kennung des Laufs, damit die Zeilen eines Durchgangs zusammengehören.
        sa.Column("lauf", sa.String(length=32), nullable=False),
        sa.Column("regel", sa.String(length=128), nullable=False),
        sa.Column("tabelle", sa.String(length=128), nullable=False),
        sa.Column("anzahl", sa.Integer(), nullable=False),
        # False heisst: die Regel hat gegriffen, gelöscht wurde aber nicht —
        # Trockenlauf oder fehlender Schalter. Auch das ist Teil des Nachweises.
        sa.Column("ausgefuehrt", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("grundlage", sa.Text(), nullable=True),
        sa.Column("zeitpunkt", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_loeschprotokoll_zeitpunkt", "loeschprotokoll", ["zeitpunkt"])


def downgrade() -> None:
    op.drop_index("ix_loeschprotokoll_zeitpunkt", table_name="loeschprotokoll")
    op.drop_table("loeschprotokoll")
    op.drop_column("users", "loeschung_angekuendigt_am")
    op.drop_index("ix_wiederherstellungscodes_user", table_name="user_wiederherstellungscodes")
    op.drop_table("user_wiederherstellungscodes")
    op.drop_table("user_totp")
    for name in ("email_bestaetigung", "passwort_reset"):
        op.drop_index(f"ix_{name}_user", table_name=name)
        op.drop_index(f"ux_{name}_token", table_name=name)
        op.drop_table(name)
