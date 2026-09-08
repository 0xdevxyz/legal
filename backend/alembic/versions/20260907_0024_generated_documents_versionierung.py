"""generated_documents_versionierung: fehlende Spalten aus der archivierten
Migration nachziehen

Die Migration migrations/_archive_pre_baseline/add_legal_update_ref_to_generated_documents.sql
(datiert 23.05.2026, "Phase 1 eRecht24-Removal") wurde beim Zusammenfassen zur
Baseline archiviert, ihre Spalten aber nie in baseline_schema.sql uebernommen.
legal_text_generator.py liest/schreibt seither template_version,
legal_update_id und regeneration_trigger auf generated_documents, ohne dass
die Spalten existieren.

Live-Symptom (Backend-Log, 04.09.2026 05:00 UTC):
    asyncpg.exceptions.UndefinedColumnError: column "template_version" does not exist
    bei legal_change_monitor -> LegalTextGenerator.regenerate_affected_users
    -> get_active_document

Das bedeutet konkret: seit dieser Drift wird KEIN Impressum/keine
Datenschutzerklaerung mehr automatisch neu generiert, wenn eine erkannte
Gesetzesaenderung sie betrifft — der Aufruf crasht, bevor er etwas tut. Diese
Revision ist REIN ADDITIV (ADD COLUMN IF NOT EXISTS), Spalten/Typen/Defaults
1:1 aus der archivierten Migration uebernommen.

Revision ID: 0024_gen_docs_version
Revises: 0023_ablehngrund_pruefregeln
Create Date: 2026-09-07
"""
from typing import Sequence, Union

from alembic import op

# Kurz gehalten: alembic_version.version_num ist VARCHAR(32), der volle Name
# ("0024_generated_documents_versionierung", 39 Zeichen) passt nicht hinein.
revision: str = "0024_gen_docs_version"
down_revision: Union[str, None] = "0023_ablehngrund_pruefregeln"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE generated_documents
            -- legal_text_generator.py:551/574 (SELECT), regenerate_affected_users
            -- setzt sie beim Re-Generieren -> TEXT, NULL solange kein
            -- Gesetzes-Update das Dokument ausgeloest hat.
            ADD COLUMN IF NOT EXISTS legal_update_id TEXT DEFAULT NULL,

            -- legal_text_generator.py:551/574/814 (SELECT + geschrieben als
            -- self.TEMPLATE_VERSION bei jeder Generierung) -> TEXT, Default '1.0'
            -- fuer Bestandszeilen ohne Versionsangabe.
            ADD COLUMN IF NOT EXISTS template_version TEXT DEFAULT '1.0',

            -- legal_text_generator.py:551/574 (SELECT), regenerate_affected_users
            -- setzt 'legal_update' beim Aufruf -> TEXT, Default 'manual' (jede
            -- Bestandszeile wurde vor dieser Spalte manuell/initial erzeugt).
            ADD COLUMN IF NOT EXISTS regeneration_trigger TEXT DEFAULT 'manual',

            -- get_active_document filtert bereits auf
            -- (metadata->>'is_active')::boolean IS NOT FALSE (liest also aus
            -- metadata, nicht aus einer Spalte) — die echte Spalte fehlte
            -- trotzdem nie test-relevant, wird hier nachgezogen fuer den Index
            -- unten und kuenftige Abfragen, die nicht ueber metadata gehen.
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
        """
    )

    op.execute(
        """
        UPDATE generated_documents
            SET is_active = (status = 'active')
            WHERE is_active IS NULL
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_gen_docs_user_type_active
            ON generated_documents (user_id, document_type, is_active)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_gen_docs_legal_update
            ON generated_documents (legal_update_id)
            WHERE legal_update_id IS NOT NULL
        """
    )

    op.execute(
        """
        COMMENT ON COLUMN generated_documents.legal_update_id IS
            'Referenz auf legal_updates.id — gesetzt, wenn Dokument durch Gesetzesänderung re-generiert wurde'
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN generated_documents.template_version IS
            'Version des Vorlagen-Templates zum Zeitpunkt der Generierung'
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN generated_documents.regeneration_trigger IS
            'Auslöser der Generierung: manual | legal_update | migration | auto'
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN generated_documents.is_active IS
            'Nur das aktive Dokument wird ausgeliefert; ältere Versionen bleiben als Archiv'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_gen_docs_legal_update")
    op.execute("DROP INDEX IF EXISTS idx_gen_docs_user_type_active")
    op.execute(
        """
        ALTER TABLE generated_documents
            DROP COLUMN IF EXISTS is_active,
            DROP COLUMN IF EXISTS regeneration_trigger,
            DROP COLUMN IF EXISTS template_version,
            DROP COLUMN IF EXISTS legal_update_id
        """
    )
