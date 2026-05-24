-- AP5: Strukturierte XAI-Felder für Compliance-Klassifizierungen
ALTER TABLE ai_compliance_logs
    ADD COLUMN IF NOT EXISTS cited_norms JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS triggering_factors JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS confidence_breakdown JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS counterfactuals JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS xai_version TEXT DEFAULT 'v1';

COMMENT ON COLUMN ai_compliance_logs.cited_norms IS 
    'Liste: [{law, article, paragraph, url, relevance_score}]';
COMMENT ON COLUMN ai_compliance_logs.triggering_factors IS 
    'Liste: [{factor, weight, description}]';
COMMENT ON COLUMN ai_compliance_logs.confidence_breakdown IS 
    'Dict: {law_match_score, severity_keywords, historical_precedent, context_clarity}';
COMMENT ON COLUMN ai_compliance_logs.counterfactuals IS 
    'Liste: ["Wenn X dann würde Klassifizierung Y lauten"]';

CREATE INDEX IF NOT EXISTS idx_acl_cited_norms ON ai_compliance_logs USING gin (cited_norms);
CREATE INDEX IF NOT EXISTS idx_acl_xai_version ON ai_compliance_logs (xai_version);
