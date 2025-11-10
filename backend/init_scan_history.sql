-- ============================================================================
-- Complyo Scan History: Persistierung aller Website-Analysen
-- ============================================================================

-- Scan History Table
CREATE TABLE IF NOT EXISTS scan_history (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(100) UNIQUE NOT NULL,
    website_id INTEGER REFERENCES tracked_websites(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    
    -- Scan Results
    scan_data JSONB NOT NULL,
    compliance_score INTEGER NOT NULL,
    total_risk_euro INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    warning_issues INTEGER DEFAULT 0,
    total_issues INTEGER DEFAULT 0,
    
    -- Metadata
    scan_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    scan_duration_ms INTEGER,
    scanner_version VARCHAR(20) DEFAULT '2.0',
    
    -- Indexes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_scan_history_website ON scan_history(website_id);
CREATE INDEX IF NOT EXISTS idx_scan_history_user ON scan_history(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_history_timestamp ON scan_history(scan_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_scan_history_scan_id ON scan_history(scan_id);

-- Auto-update trigger for tracked_websites
CREATE OR REPLACE FUNCTION update_tracked_website_after_scan()
RETURNS TRIGGER AS $$
BEGIN
    -- Update tracked_websites with latest scan data
    UPDATE tracked_websites
    SET 
        last_score = NEW.compliance_score,
        last_scan_date = NEW.scan_timestamp,
        scan_count = scan_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.website_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Automatically update tracked_websites after scan insert
DROP TRIGGER IF EXISTS trigger_update_website_after_scan ON scan_history;
CREATE TRIGGER trigger_update_website_after_scan
    AFTER INSERT ON scan_history
    FOR EACH ROW
    EXECUTE FUNCTION update_tracked_website_after_scan();

-- View: Latest scans per website
CREATE OR REPLACE VIEW latest_scans_per_website AS
SELECT DISTINCT ON (website_id)
    website_id,
    scan_id,
    url,
    compliance_score,
    total_risk_euro,
    critical_issues,
    warning_issues,
    scan_timestamp
FROM scan_history
ORDER BY website_id, scan_timestamp DESC;

-- View: User scan statistics
CREATE OR REPLACE VIEW user_scan_statistics AS
SELECT 
    user_id,
    COUNT(*) as total_scans,
    COUNT(DISTINCT website_id) as unique_websites,
    AVG(compliance_score)::INTEGER as avg_score,
    SUM(critical_issues) as total_critical_issues,
    MAX(scan_timestamp) as last_scan_date
FROM scan_history
GROUP BY user_id;

COMMENT ON TABLE scan_history IS 'Vollständige Historie aller Compliance-Scans mit JSONB-Speicherung';
COMMENT ON COLUMN scan_history.scan_data IS 'Vollständiger Scan-Output als JSON (issues, recommendations, etc.)';
COMMENT ON VIEW latest_scans_per_website IS 'Neuester Scan pro Website für schnellen Dashboard-Zugriff';

