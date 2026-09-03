-- Migration: add_legal_update_ref_to_generated_documents.sql
-- Phase 1 eRecht24-Removal: generated_documents-Tabelle für interne Versionierung erweitern
-- Datum: 2026-05-23

BEGIN;

ALTER TABLE generated_documents
  ADD COLUMN IF NOT EXISTS legal_update_id TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS template_version TEXT DEFAULT '1.0',
  ADD COLUMN IF NOT EXISTS regeneration_trigger TEXT DEFAULT 'manual',
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

UPDATE generated_documents
  SET is_active = (status = 'active')
  WHERE is_active IS NULL;

CREATE INDEX IF NOT EXISTS idx_gen_docs_user_type_active
  ON generated_documents (user_id, document_type, is_active);

CREATE INDEX IF NOT EXISTS idx_gen_docs_legal_update
  ON generated_documents (legal_update_id)
  WHERE legal_update_id IS NOT NULL;

COMMENT ON COLUMN generated_documents.legal_update_id IS
  'Referenz auf legal_updates.id — gesetzt, wenn Dokument durch Gesetzesänderung re-generiert wurde';
COMMENT ON COLUMN generated_documents.template_version IS
  'Version des Vorlagen-Templates zum Zeitpunkt der Generierung';
COMMENT ON COLUMN generated_documents.regeneration_trigger IS
  'Auslöser der Generierung: manual | legal_update | migration | auto';
COMMENT ON COLUMN generated_documents.is_active IS
  'Nur das aktive Dokument wird ausgeliefert; ältere Versionen bleiben als Archiv';

COMMIT;
