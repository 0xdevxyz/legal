-- Score History Table
-- Speichert den Verlauf der Compliance-Scores für jede Website

CREATE TABLE IF NOT EXISTS score_history (
    id SERIAL PRIMARY KEY,
    website_id INTEGER REFERENCES tracked_websites(id) ON DELETE CASCADE,
    compliance_score INTEGER NOT NULL CHECK (compliance_score >= 0 AND compliance_score <= 100),
    critical_issues_count INTEGER DEFAULT 0,
    warning_issues_count INTEGER DEFAULT 0,
    info_issues_count INTEGER DEFAULT 0,
    scan_type VARCHAR(50) DEFAULT 'initial',  -- 'initial', 'after_fix', 'rescan', 'scheduled'
    scan_trigger VARCHAR(100),  -- 'manual', 'ki_fix', 'scheduled', 'legal_update'
    notes TEXT,  -- Optionale Notizen
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_score_history_website ON score_history(website_id);
CREATE INDEX IF NOT EXISTS idx_score_history_created ON score_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_score_history_scan_type ON score_history(scan_type);

-- Composite Index für Website + Zeitraum Abfragen
CREATE INDEX IF NOT EXISTS idx_score_history_website_date ON score_history(website_id, created_at DESC);

-- Kommentare
COMMENT ON TABLE score_history IS 'Verlauf der Compliance-Scores für Tracking und Charts';
COMMENT ON COLUMN score_history.scan_type IS 'Art des Scans: initial (erster), after_fix (nach KI-Fix), rescan (manuell), scheduled (automatisch)';
COMMENT ON COLUMN score_history.scan_trigger IS 'Was hat den Scan ausgelöst?';


-- View für schnellen Zugriff auf neueste Scores pro Website
CREATE OR REPLACE VIEW latest_scores AS
SELECT DISTINCT ON (website_id)
    website_id,
    compliance_score,
    critical_issues_count,
    warning_issues_count,
    scan_type,
    created_at
FROM score_history
ORDER BY website_id, created_at DESC;

COMMENT ON VIEW latest_scores IS 'Zeigt den aktuellsten Score für jede Website';


-- Funktion um Score-Verlauf für eine Website abzurufen
CREATE OR REPLACE FUNCTION get_score_history(
    p_website_id INTEGER,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    date TIMESTAMP,
    score INTEGER,
    critical_count INTEGER,
    scan_type VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        created_at as date,
        compliance_score as score,
        critical_issues_count as critical_count,
        score_history.scan_type
    FROM score_history
    WHERE website_id = p_website_id
      AND created_at >= NOW() - (p_days || ' days')::INTERVAL
    ORDER BY created_at ASC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_score_history IS 'Gibt Score-Verlauf für eine Website über die letzten X Tage zurück';

