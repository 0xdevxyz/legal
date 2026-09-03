-- AP3: Prompt-Versioning für adaptives Lernsystem
CREATE TABLE IF NOT EXISTS prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_key TEXT NOT NULL,
    version_tag TEXT NOT NULL,
    template TEXT NOT NULL,
    performance_score FLOAT DEFAULT 0.0,
    sample_count INT DEFAULT 0,
    positive_rate FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT FALSE,
    is_baseline BOOLEAN DEFAULT FALSE,
    ab_test_id UUID,
    activated_at TIMESTAMPTZ,
    deactivated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    UNIQUE (prompt_key, version_tag)
);

CREATE INDEX IF NOT EXISTS idx_pv_key_active ON prompt_versions (prompt_key, is_active);

-- Fix-Outcome-Tracking
CREATE TABLE IF NOT EXISTS fix_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fix_job_id UUID NOT NULL,
    website_id UUID,
    fix_template_id TEXT,
    fix_type TEXT,
    deployed_at TIMESTAMPTZ DEFAULT NOW(),
    rescan_at TIMESTAMPTZ,
    passed_rescan BOOLEAN,
    score_before FLOAT,
    score_after FLOAT,
    score_delta FLOAT GENERATED ALWAYS AS (score_after - score_before) STORED,
    user_accepted BOOLEAN,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_fo_fix_type ON fix_outcomes (fix_type);
CREATE INDEX IF NOT EXISTS idx_fo_template ON fix_outcomes (fix_template_id);

-- Drift-Detection-Log
CREATE TABLE IF NOT EXISTS classification_drift_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_date DATE DEFAULT CURRENT_DATE,
    window_days INT DEFAULT 7,
    kl_divergence FLOAT,
    distribution_current JSONB,
    distribution_baseline JSONB,
    drift_detected BOOLEAN DEFAULT FALSE,
    alert_sent BOOLEAN DEFAULT FALSE
);

-- View: Modell-Performance über Zeit
CREATE OR REPLACE VIEW model_performance_timeline AS
SELECT
    DATE_TRUNC('week', fo.deployed_at) AS week,
    fo.fix_type,
    COUNT(*) AS total_fixes,
    AVG(CASE WHEN fo.passed_rescan THEN 1.0 ELSE 0.0 END) AS rescan_pass_rate,
    AVG(fo.score_delta) AS avg_score_improvement,
    COUNT(DISTINCT pv.version_tag) AS prompt_versions_used
FROM fix_outcomes fo
LEFT JOIN prompt_versions pv ON pv.is_active = TRUE AND pv.prompt_key = fo.fix_type
GROUP BY DATE_TRUNC('week', fo.deployed_at), fo.fix_type
ORDER BY week DESC;
