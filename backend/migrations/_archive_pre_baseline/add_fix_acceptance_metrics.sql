-- AP2: Fix-Akzeptanz und Erfolgs-KPIs
CREATE TABLE IF NOT EXISTS fix_acceptance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fix_job_id UUID,
    website_id UUID,
    fix_type TEXT NOT NULL,
    handler_used TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    presented_to_user_at TIMESTAMPTZ,
    user_decision TEXT CHECK (user_decision IN ('accepted','rejected','ignored','auto_deployed')),
    decision_at TIMESTAMPTZ,
    rescan_triggered_at TIMESTAMPTZ,
    rescan_passed BOOLEAN,
    rescan_score_before FLOAT,
    rescan_score_after FLOAT,
    time_to_decision_seconds INT,
    rejection_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_fam_fix_type ON fix_acceptance_metrics (fix_type);
CREATE INDEX IF NOT EXISTS idx_fam_decision ON fix_acceptance_metrics (user_decision);
CREATE INDEX IF NOT EXISTS idx_fam_rescan ON fix_acceptance_metrics (rescan_passed);

-- View: Acceptance-Rate per Fix-Type
CREATE OR REPLACE VIEW fix_acceptance_rate_by_type AS
SELECT
    fix_type,
    handler_used,
    COUNT(*) AS total_fixes,
    SUM(CASE WHEN user_decision = 'accepted' THEN 1 ELSE 0 END) AS accepted,
    SUM(CASE WHEN user_decision = 'rejected' THEN 1 ELSE 0 END) AS rejected,
    SUM(CASE WHEN rescan_passed = true THEN 1 ELSE 0 END) AS rescan_passed,
    ROUND(
        100.0 * SUM(CASE WHEN user_decision = 'accepted' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        2
    ) AS acceptance_rate_pct,
    ROUND(
        100.0 * SUM(CASE WHEN rescan_passed = true THEN 1 ELSE 0 END) /
        NULLIF(SUM(CASE WHEN rescan_triggered_at IS NOT NULL THEN 1 ELSE 0 END), 0),
        2
    ) AS rescan_pass_rate_pct
FROM fix_acceptance_metrics
GROUP BY fix_type, handler_used;
