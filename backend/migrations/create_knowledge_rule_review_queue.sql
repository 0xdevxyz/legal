-- Knowledge Rule Review Queue
-- Wird befüllt wenn ein High-Impact Knowledge Update erkannt wird
-- und manuelle Prüfung der betroffenen Compliance-Regeln erforderlich ist

CREATE TABLE IF NOT EXISTS knowledge_rule_review_queue (
    id SERIAL PRIMARY KEY,
    check_name TEXT NOT NULL,
    knowledge_file TEXT NOT NULL,
    title TEXT,
    law_areas TEXT[],
    impact TEXT DEFAULT 'high',
    status TEXT DEFAULT 'pending',  -- pending | reviewed | dismissed
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT knowledge_rule_review_queue_unique UNIQUE (check_name, knowledge_file)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_rule_review_status ON knowledge_rule_review_queue(status);
CREATE INDEX IF NOT EXISTS idx_knowledge_rule_review_created ON knowledge_rule_review_queue(created_at DESC);

COMMENT ON TABLE knowledge_rule_review_queue IS
    'Queue für manuelle Rule-Reviews ausgelöst durch High-Impact Knowledge Updates';
