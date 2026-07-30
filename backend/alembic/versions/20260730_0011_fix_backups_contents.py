"""Direct-Deploy-Backups in die Datenbank statt ins Container-Dateisystem.

Revision ID: 0011_fix_backups_contents
Revises: 0010_git_integration

Hintergrund: Der alte Deploy-Motor legte Backups unter self.backup_dir im
Container ab — nach jedem Rebuild weg — und das Backup selbst war ein Stub
(FTP/SFTP: `pass`), meldete aber backup_created=True. Zusätzlich las der
Rollback-Pfad Spalten, die es nie gab (backup_type, backed_up_files).

Neu (secure_deployment.py): vor jedem Upload wird der Bestand jeder Zieldatei
heruntergeladen und hier als JSONB abgelegt:
  file_contents = { "<remote_path>": {"existed": bool, "content_b64": str|null} }
Restore lädt daraus hoch bzw. entfernt Dateien, die es vorher nicht gab.

Rein additiv.
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0011_fix_backups_contents'
down_revision: Union[str, None] = '0010_git_integration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE fix_backups
            ADD COLUMN IF NOT EXISTS file_contents JSONB
    """)
    # log_fix_application() INSERTete seit jeher zwei Spalten, die es nie gab —
    # jeder Aufruf schlug fehl. Nachziehen statt den Audit-Umfang zu kuerzen:
    # deployment_result (vollstaendiges Deploy-Ergebnis) und
    # confirmation_timestamp (wann der Kunde bestaetigt hat) gehoeren in ein
    # rechtssicheres Protokoll.
    op.execute("""
        ALTER TABLE fix_application_audit
            ADD COLUMN IF NOT EXISTS deployment_result JSONB,
            ADD COLUMN IF NOT EXISTS confirmation_timestamp TIMESTAMPTZ
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE fix_backups DROP COLUMN IF EXISTS file_contents")
    op.execute("""
        ALTER TABLE fix_application_audit
            DROP COLUMN IF EXISTS deployment_result,
            DROP COLUMN IF EXISTS confirmation_timestamp
    """)
