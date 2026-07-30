"""Double-Opt-in: die fehlenden Verifikationsspalten in `leads` nachziehen.

Revision ID: 0008_leads_verification
Revises: 0007_geo_ip_cache

Hintergrund: `database_service.verify_lead_email()` — der Bestätigungsschritt des
Double-Opt-in — liest `email_verified` und schreibt anschließend `email_verified`,
`verified_at` und `updated_at`. Keine dieser drei Spalten existierte. Beide
Queries liefen in eine `UndefinedColumnError`, die der umschließende
Exception-Handler zu `return False` verschluckt hat.

Folge: **kein Lead konnte seine E-Mail jemals bestätigen.** Der Bestätigungslink
aus der Opt-in-Mail meldete stillschweigend „ungültig", der Lead blieb auf
`status = 'pending_confirmation'` stehen, und die Admin-Statistik zählte
dauerhaft 0 verifizierte Leads.

Die Spalten fehlten seit Revision 0003, die die `leads`-Tabelle nach dem
Baseline-Cut aus den realen INSERT/SELECT-Aufrufen rekonstruiert hat — der
Verifikationspfad war dabei nicht abgedeckt.

`email_verified` ist bewusst redundant zu `status = 'verified'`: der Code liest
an acht Stellen das Flag, nicht den Status. Die Migration folgt dem Code, statt
acht Aufrufstellen umzuschreiben. Bestandszeilen werden aus `status` abgeleitet,
damit beide Sichten von Anfang an übereinstimmen.

Rein additiv (`ADD COLUMN IF NOT EXISTS`).
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0008_leads_verification'
down_revision: Union[str, None] = '0007_geo_ip_cache'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE leads
            ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS verified_at    TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS updated_at     TIMESTAMP WITH TIME ZONE
                                                    NOT NULL DEFAULT CURRENT_TIMESTAMP
    """)

    # Bestand angleichen: wer laut status schon bestaetigt ist, bekommt das Flag.
    op.execute("""
        UPDATE leads
           SET email_verified = TRUE
         WHERE status IN ('verified', 'converted')
           AND email_verified = FALSE
    """)

    # verify_lead_email() sucht ueber den Token; die Suche laeuft bei jedem
    # Klick auf einen Bestaetigungslink.
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_verification_token
            ON leads (verification_token) WHERE verification_token IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_leads_verification_token")
    op.execute("""
        ALTER TABLE leads
            DROP COLUMN IF EXISTS email_verified,
            DROP COLUMN IF EXISTS verified_at,
            DROP COLUMN IF EXISTS updated_at
    """)
