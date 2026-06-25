-- User Journeys Table
-- Speichert den Workflow-/Journey-Fortschritt pro Benutzer (Compliance-Reise).
-- Wird von compliance_engine/workflow_integration.py gelesen/geschrieben.

CREATE TABLE IF NOT EXISTS user_journeys (
    user_id      TEXT PRIMARY KEY,           -- entspricht str(current_user["id"])
    journey_data TEXT NOT NULL,              -- JSON (json.dumps/json.loads im Code)
    created_at   TIMESTAMP DEFAULT NOW(),
    updated_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_journeys_updated ON user_journeys(updated_at DESC);

COMMENT ON TABLE user_journeys IS 'Workflow-/Journey-Fortschritt pro Benutzer (workflow_engine)';
COMMENT ON COLUMN user_journeys.journey_data IS 'JSON-serialisierte UserJourney (json.dumps)';
