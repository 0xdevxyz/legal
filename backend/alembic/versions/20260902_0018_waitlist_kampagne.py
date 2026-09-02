"""waitlist_kampagne: Herkunft und zugesagtes Angebot je Wartelisten-Eintrag

Anlass ist eine bezahlte Anzeigenkampagne. Bisher kannte waitlist_leads nur
`source` mit drei erlaubten Werten ("early-access", "complyo.de", "landing"),
und alles andere fiel still auf "early-access" zurueck. Damit landet jeder
Eintrag im selben Topf: man sieht, DASS jemand kam, aber nicht, aus welcher
Anzeige. Genau diese Frage soll die Kampagne beantworten, also muss die
Herkunft mitgeschrieben werden, bevor der erste Euro ausgegeben wird.

`angebot` haelt fest, WAS der Person zugesagt wurde. Die Kampagnenseite
verspricht den ersten 100 Anmeldungen 35 EUR pro Monat im ersten Jahr, waehrend
der regulaere Pro-Tarif bei 49 EUR liegt. Wer sich eintraegt, erwartet diesen
Preis. Ohne Beleg, welche Fassung des Angebots zum Zeitpunkt der Anmeldung
galt, laesst sich spaeter weder die Zusage einloesen noch eine geaenderte
Fassung begruenden. Dieselbe Ueberlegung steht hinter hinweis_version in
fix_freigaben.

`platz_nr` macht die Verknappung nachpruefbar. "Nur 100 Plaetze" ist eine
Werbeaussage; ist sie nicht gedeckt, ist sie nach Paragraf 5 UWG irrefuehrend.
Die Nummer kommt aus einer Sequence (race-frei bei gleichzeitigen Anmeldungen)
und wird erst bei der Double-Opt-In-Bestaetigung vergeben: ein unbestaetigter
Eintrag darf keinen Platz blockieren, sonst zeigt der oeffentliche Zaehler
Plaetze als vergeben an, die niemand hat.

Alle Spalten sind nullable. Bestandszeilen gibt es zwar noch keine, aber der
Endpunkt nimmt weiterhin Anmeldungen ohne UTM-Parameter an - jemand, der die
Seite direkt aufruft, ist ein gueltiger Lead und kein Fehlerfall.

Revision ID: 0018_waitlist_kampagne
Revises: 0017_fix_freigaben
Create Date: 2026-09-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0018_waitlist_kampagne"
down_revision: Union[str, None] = "0017_fix_freigaben"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Herkunft der Anmeldung. Laengen orientieren sich an dem, was Google Ads
    # und Meta tatsaechlich in die URL schreiben; abgeschnitten wird schon im
    # Endpunkt, damit ein ueberlanger Parameter keinen Insert sprengt.
    op.add_column("waitlist_leads", sa.Column("campaign", sa.String(length=64), nullable=True))
    op.add_column("waitlist_leads", sa.Column("utm_source", sa.String(length=120), nullable=True))
    op.add_column("waitlist_leads", sa.Column("utm_medium", sa.String(length=120), nullable=True))
    op.add_column("waitlist_leads", sa.Column("utm_campaign", sa.String(length=120), nullable=True))
    op.add_column("waitlist_leads", sa.Column("utm_content", sa.String(length=120), nullable=True))
    op.add_column("waitlist_leads", sa.Column("utm_term", sa.String(length=120), nullable=True))
    op.add_column("waitlist_leads", sa.Column("landing_path", sa.String(length=200), nullable=True))

    # Zugesagtes Angebot und belegter Platz.
    op.add_column("waitlist_leads", sa.Column("angebot", sa.String(length=64), nullable=True))
    op.add_column("waitlist_leads", sa.Column("platz_nr", sa.Integer(), nullable=True))

    # Sequence statt MAX(platz_nr)+1: zwei gleichzeitige Bestaetigungen wuerden
    # sonst dieselbe Nummer ziehen und der Unique-Index schluege fehl.
    op.execute("CREATE SEQUENCE IF NOT EXISTS waitlist_platz_seq START WITH 1")

    op.create_index("ix_waitlist_leads_campaign", "waitlist_leads", ["campaign"])
    op.create_index("ix_waitlist_leads_utm_campaign", "waitlist_leads", ["utm_campaign"])
    # Teil-Index: die Nummer ist nur dort vergeben, wo bestaetigt wurde.
    op.execute(
        "CREATE UNIQUE INDEX ix_waitlist_leads_platz_nr ON waitlist_leads (platz_nr) "
        "WHERE platz_nr IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_waitlist_leads_platz_nr")
    op.drop_index("ix_waitlist_leads_utm_campaign", table_name="waitlist_leads")
    op.drop_index("ix_waitlist_leads_campaign", table_name="waitlist_leads")
    op.execute("DROP SEQUENCE IF EXISTS waitlist_platz_seq")
    for spalte in (
        "platz_nr", "angebot", "landing_path", "utm_term", "utm_content",
        "utm_campaign", "utm_medium", "utm_source", "campaign",
    ):
        op.drop_column("waitlist_leads", spalte)
