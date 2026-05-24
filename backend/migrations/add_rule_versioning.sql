-- Rule Versioning Migration
-- Fügt Versionierung und Changelog für compliance_risk_matrix hinzu
-- Task 1 — Quality Process Implementation

ALTER TABLE compliance_risk_matrix
  ADD COLUMN IF NOT EXISTS rule_version INTEGER DEFAULT 1,
  ADD COLUMN IF NOT EXISTS valid_from DATE DEFAULT CURRENT_DATE,
  ADD COLUMN IF NOT EXISTS valid_until DATE,
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

CREATE INDEX IF NOT EXISTS idx_compliance_risk_matrix_active
  ON compliance_risk_matrix(is_active, effective_date);

CREATE TABLE IF NOT EXISTS rule_changelog (
  id SERIAL PRIMARY KEY,
  rule_id INTEGER REFERENCES compliance_risk_matrix(id) ON DELETE CASCADE,
  rule_version INTEGER NOT NULL,
  change_type VARCHAR(50) NOT NULL CHECK (change_type IN ('created', 'updated', 'deprecated')),
  change_description TEXT,
  legal_basis_ref VARCHAR(255),
  triggered_by_legal_update_id INTEGER REFERENCES legal_updates(id) ON DELETE SET NULL,
  changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  changed_by VARCHAR(100) NOT NULL DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_rule_changelog_rule_id ON rule_changelog(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_changelog_changed_at ON rule_changelog(changed_at DESC);

ALTER TABLE tracked_websites
  ADD COLUMN IF NOT EXISTS rescan_required BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS rescan_reason TEXT,
  ADD COLUMN IF NOT EXISTS rescan_triggered_by INTEGER REFERENCES legal_updates(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS last_scan_ruleset_version INTEGER;

CREATE INDEX IF NOT EXISTS idx_tracked_websites_rescan
  ON tracked_websites(rescan_required) WHERE rescan_required = TRUE;

ALTER TABLE scan_history
  ADD COLUMN IF NOT EXISTS ruleset_snapshot JSONB,
  ADD COLUMN IF NOT EXISTS ruleset_version INTEGER;

ALTER TABLE fix_application_audit
  ADD COLUMN IF NOT EXISTS quality_gate_status VARCHAR(50),
  ADD COLUMN IF NOT EXISTS quality_gate_log JSONB,
  ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100),
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_fix_audit_quality_gate
  ON fix_application_audit(quality_gate_status)
  WHERE quality_gate_status IS NOT NULL;
