-- Migration: create_generated_documents.sql
-- AUDIT-28: Tabelle für AI-generierte Rechtsdokumente (Datenschutzerklärung, Impressum, AGB)
-- Applied: 2026-05-01

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
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_reviewed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gen_docs_user ON generated_documents (user_id, document_type);
