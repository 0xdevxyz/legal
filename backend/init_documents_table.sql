-- ============================================================================
-- Generated Documents Table für Expert Plan
-- Speichert vollständige KI-generierte Dokumente mit Audit-Trail
-- ============================================================================

CREATE TABLE IF NOT EXISTS generated_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    doc_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    audit_trail JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES user_limits(user_id)
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_documents_user ON generated_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON generated_documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_created ON generated_documents(created_at DESC);

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

-- View für aktuelle Dokumente pro User
CREATE OR REPLACE VIEW user_current_documents AS
SELECT DISTINCT ON (user_id, doc_type)
    id,
    user_id,
    doc_type,
    created_at,
    version,
    audit_trail->'legal_basis' as legal_basis,
    audit_trail->'ai_model' as ai_model
FROM generated_documents
WHERE is_active = TRUE
ORDER BY user_id, doc_type, created_at DESC;

