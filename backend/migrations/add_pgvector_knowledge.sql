-- AP1: pgvector für semantischen Embedding-Index
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    embedding vector(1536),
    law_refs TEXT[] DEFAULT '{}',
    language TEXT DEFAULT 'de',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_vector
    ON knowledge_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_law_refs
    ON knowledge_embeddings USING gin (law_refs);

CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_language
    ON knowledge_embeddings (language);

-- Benchmark-Tabelle für wissenschaftliche Validierung
CREATE TABLE IF NOT EXISTS classification_benchmark_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_date TIMESTAMPTZ DEFAULT NOW(),
    model_version TEXT NOT NULL,
    test_set_version TEXT NOT NULL,
    precision_score FLOAT,
    recall_score FLOAT,
    f1_score FLOAT,
    brier_score FLOAT,
    ece_score FLOAT,
    notes TEXT
);

-- Multi-Label-Erweiterung für ai_compliance_logs
ALTER TABLE ai_compliance_logs
    ADD COLUMN IF NOT EXISTS applicable_laws TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS law_confidence JSONB DEFAULT '{}';
