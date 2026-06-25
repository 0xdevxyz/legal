-- ============================================================================
-- Generated Documents Table — KI-generierte Rechtsdokumente
-- (Impressum, Datenschutz, AGB, Cookie-Richtlinie, Widerrufsbelehrung)
--
-- KANONISCHES SCHEMA. Identisch zu migrations/create_generated_documents.sql
-- (+ add_legal_update_ref_to_generated_documents.sql), passt zu
-- legal_text_generator._save (document_type / html_content / metadata JSONB).
-- Das frühere Schema (doc_type / audit_trail / version) war OBSOLET und
-- inkompatibel mit dem Generator — hier ersetzt.
-- Alle Statements sind IF NOT EXISTS / idempotent: in bereits migrierten
-- Produktions-DBs No-ops.
-- ============================================================================

CREATE TABLE IF NOT EXISTS generated_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    title VARCHAR(500),
    content TEXT NOT NULL,
    html_content TEXT,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'draft')),
    language VARCHAR(10) DEFAULT 'de',
    legal_update_id TEXT DEFAULT NULL,
    template_version TEXT DEFAULT '1.0',
    regeneration_trigger TEXT DEFAULT 'manual',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_reviewed_at TIMESTAMP
);

-- Falls eine ältere Instanz das frühere Schema hatte: fehlende Spalten ergänzen
ALTER TABLE generated_documents
    ADD COLUMN IF NOT EXISTS document_type VARCHAR(50),
    ADD COLUMN IF NOT EXISTS html_content TEXT,
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'de',
    ADD COLUMN IF NOT EXISTS legal_update_id TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS template_version TEXT DEFAULT '1.0',
    ADD COLUMN IF NOT EXISTS regeneration_trigger TEXT DEFAULT 'manual',
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Indizes
CREATE INDEX IF NOT EXISTS idx_gen_docs_user ON generated_documents (user_id, document_type);
CREATE INDEX IF NOT EXISTS idx_documents_created ON generated_documents (created_at DESC);

-- Trigger für updated_at
CREATE OR REPLACE FUNCTION update_documents_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_documents_updated_at ON generated_documents;
CREATE TRIGGER trigger_documents_updated_at
    BEFORE UPDATE ON generated_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_documents_timestamp();

-- View für aktuelle Dokumente pro User (an kanonisches Schema angepasst)
-- DROP zuerst, da eine alte View ggf. andere Spalten (doc_type/audit_trail) hat
DROP VIEW IF EXISTS user_current_documents;
CREATE VIEW user_current_documents AS
SELECT DISTINCT ON (user_id, document_type)
    id,
    user_id,
    document_type,
    language,
    created_at,
    template_version,
    metadata
FROM generated_documents
WHERE (metadata->>'is_active')::boolean IS NOT FALSE
ORDER BY user_id, document_type, created_at DESC;
