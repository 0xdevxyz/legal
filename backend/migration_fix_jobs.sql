-- Migration: Fix Jobs System für persistente KI-Fixes
-- Datum: 2025-11-04
-- Beschreibung: Ermöglicht das Tracking von KI-Fix Jobs über Page-Refreshs hinweg

-- 1. Fix Jobs Tabelle
CREATE TABLE IF NOT EXISTS fix_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE NOT NULL DEFAULT ('fix_' || gen_random_uuid()::TEXT),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scan_id VARCHAR(100) NOT NULL REFERENCES scan_history(scan_id) ON DELETE CASCADE,
    issue_id TEXT NOT NULL,
    issue_data JSONB NOT NULL, -- Vollständige Issue-Daten für die Bearbeitung
    
    -- Job Status
    status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    progress_percent INTEGER DEFAULT 0,
    current_step TEXT,
    
    -- Ergebnisse
    result JSONB, -- Generated fix code/instructions
    error_message TEXT,
    
    -- Zeitstempel
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Metadaten
    estimated_duration_seconds INTEGER DEFAULT 300, -- 5 Min Standard
    
    CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CHECK (progress_percent >= 0 AND progress_percent <= 100)
);

-- 2. Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_fix_jobs_user_id ON fix_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_scan_id ON fix_jobs(scan_id);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_status ON fix_jobs(status);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_created_at ON fix_jobs(created_at DESC);

-- 3. Funktion: Aktive Jobs für einen User abrufen
CREATE OR REPLACE FUNCTION get_active_fix_jobs(p_user_id INTEGER)
RETURNS TABLE (
    job_id VARCHAR(100),
    scan_id VARCHAR(100),
    issue_id TEXT,
    status TEXT,
    progress_percent INTEGER,
    current_step TEXT,
    created_at TIMESTAMP,
    estimated_completion TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fj.job_id,
        fj.scan_id,
        fj.issue_id,
        fj.status,
        fj.progress_percent,
        fj.current_step,
        fj.created_at,
        fj.created_at + (fj.estimated_duration_seconds || ' seconds')::INTERVAL
    FROM fix_jobs fj
    WHERE fj.user_id = p_user_id
      AND fj.status IN ('pending', 'processing')
    ORDER BY fj.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- 4. Funktion: Job starten
CREATE OR REPLACE FUNCTION start_fix_job(p_job_id VARCHAR(100))
RETURNS VOID AS $$
BEGIN
    UPDATE fix_jobs
    SET 
        status = 'processing',
        started_at = NOW(),
        progress_percent = 10
    WHERE job_id = p_job_id AND status = 'pending';
END;
$$ LANGUAGE plpgsql;

-- 5. Funktion: Job Progress aktualisieren
CREATE OR REPLACE FUNCTION update_fix_job_progress(
    p_job_id VARCHAR(100),
    p_progress INTEGER,
    p_step TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE fix_jobs
    SET 
        progress_percent = p_progress,
        current_step = p_step
    WHERE job_id = p_job_id;
END;
$$ LANGUAGE plpgsql;

-- 6. Funktion: Job abschließen
CREATE OR REPLACE FUNCTION complete_fix_job(
    p_job_id VARCHAR(100),
    p_result JSONB
)
RETURNS VOID AS $$
BEGIN
    UPDATE fix_jobs
    SET 
        status = 'completed',
        progress_percent = 100,
        result = p_result,
        completed_at = NOW()
    WHERE job_id = p_job_id;
END;
$$ LANGUAGE plpgsql;

-- 7. Funktion: Job als fehlgeschlagen markieren
CREATE OR REPLACE FUNCTION fail_fix_job(
    p_job_id VARCHAR(100),
    p_error_message TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE fix_jobs
    SET 
        status = 'failed',
        error_message = p_error_message,
        completed_at = NOW()
    WHERE job_id = p_job_id;
END;
$$ LANGUAGE plpgsql;

-- 8. Automatische Cleanup-Funktion (Jobs älter als 7 Tage löschen)
CREATE OR REPLACE FUNCTION cleanup_old_fix_jobs()
RETURNS VOID AS $$
BEGIN
    DELETE FROM fix_jobs
    WHERE completed_at < NOW() - INTERVAL '7 days'
      AND status IN ('completed', 'failed');
END;
$$ LANGUAGE plpgsql;

-- 9. View für Job-Übersicht
CREATE OR REPLACE VIEW fix_jobs_overview AS
SELECT 
    fj.id,
    fj.user_id,
    u.email,
    fj.scan_id,
    fj.issue_id,
    fj.status,
    fj.progress_percent,
    fj.current_step,
    fj.created_at,
    fj.started_at,
    fj.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(fj.completed_at, NOW()) - fj.created_at)) as duration_seconds,
    fj.issue_data->>'title' as issue_title,
    fj.issue_data->>'severity' as issue_severity
FROM fix_jobs fj
JOIN users u ON fj.user_id = u.id
ORDER BY fj.created_at DESC;

COMMENT ON TABLE fix_jobs IS 'Tracking von KI-Fix Jobs für persistente Bearbeitung über Refreshs hinweg';
COMMENT ON COLUMN fix_jobs.status IS 'pending=wartend, processing=läuft, completed=fertig, failed=fehler';
COMMENT ON COLUMN fix_jobs.progress_percent IS 'Fortschritt 0-100%';
COMMENT ON COLUMN fix_jobs.issue_data IS 'Vollständige Issue-Daten als JSONB für die Bearbeitung';

