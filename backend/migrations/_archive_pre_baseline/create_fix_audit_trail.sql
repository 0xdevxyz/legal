-- ============================================================================
-- FIX APPLICATION AUDIT TRAIL
-- Rechtssichere Nachverfolgung aller Fix-Anwendungen
-- ============================================================================

-- Tabelle für Audit-Trail
CREATE TABLE IF NOT EXISTS fix_application_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fix_id VARCHAR(255) NOT NULL,
    fix_category VARCHAR(100),
    fix_type VARCHAR(50), -- 'code', 'text', 'guide', 'widget'
    
    -- Was wurde gemacht?
    action_type VARCHAR(50) NOT NULL, -- 'generated', 'downloaded', 'applied', 'previewed', 'rolled_back'
    deployment_method VARCHAR(50), -- 'ftp', 'sftp', 'github_pr', 'zip_download', 'manual'
    
    -- Wann und wo?
    applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Ergebnis
    deployment_result JSONB, -- Success/Errors, deployed_files, etc.
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Backup & Rollback
    backup_id VARCHAR(255),
    backup_location TEXT,
    rollback_available BOOLEAN DEFAULT FALSE,
    
    -- Bestätigung
    user_confirmed BOOLEAN DEFAULT FALSE,
    confirmation_timestamp TIMESTAMP,
    
    -- Metadaten
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON fix_application_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_fix_id ON fix_application_audit(fix_id);
CREATE INDEX IF NOT EXISTS idx_audit_action_type ON fix_application_audit(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_applied_at ON fix_application_audit(applied_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_success ON fix_application_audit(success);

-- Trigger für updated_at
CREATE OR REPLACE FUNCTION update_fix_audit_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_fix_audit_timestamp
BEFORE UPDATE ON fix_application_audit
FOR EACH ROW
EXECUTE FUNCTION update_fix_audit_timestamp();

-- ============================================================================
-- FIX BACKUPS
-- Speichert Informationen über erstellte Backups
-- ============================================================================

CREATE TABLE IF NOT EXISTS fix_backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backup_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    audit_id UUID REFERENCES fix_application_audit(id) ON DELETE CASCADE,
    
    -- Backup-Informationen
    backup_location TEXT NOT NULL, -- Pfad zum Backup (File oder S3)
    backup_size_bytes BIGINT,
    backup_type VARCHAR(50), -- 'full', 'files', 'database'
    
    -- Was wurde gesichert?
    backed_up_files JSONB, -- Array von Dateipfaden
    deployment_method VARCHAR(50),
    site_url TEXT,
    
    -- Metadaten
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP, -- Backups werden nach 30 Tagen gelöscht
    is_restored BOOLEAN DEFAULT FALSE,
    restored_at TIMESTAMP,
    
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_backups_user_id ON fix_backups(user_id);
CREATE INDEX IF NOT EXISTS idx_backups_backup_id ON fix_backups(backup_id);
CREATE INDEX IF NOT EXISTS idx_backups_expires_at ON fix_backups(expires_at);
CREATE INDEX IF NOT EXISTS idx_backups_audit_id ON fix_backups(audit_id);

-- ============================================================================
-- STAGING DEPLOYMENTS (für Premium-Feature)
-- ============================================================================

CREATE TABLE IF NOT EXISTS staging_deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fix_id VARCHAR(255) NOT NULL,
    audit_id UUID REFERENCES fix_application_audit(id) ON DELETE CASCADE,
    
    -- Staging-Environment
    staging_url TEXT NOT NULL, -- z.B. preview-abc123.complyo.tech
    staging_subdomain VARCHAR(100),
    
    -- Screenshots
    screenshot_before TEXT, -- URL/Pfad zum Screenshot vor Fix
    screenshot_after TEXT, -- URL/Pfad zum Screenshot mit Fix
    screenshot_diff TEXT, -- URL/Pfad zum Diff-Image
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'deployed', 'approved', 'rejected', 'live'
    deployed_at TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by INTEGER REFERENCES users(id),
    
    -- Live-Deployment
    live_deployed_at TIMESTAMP,
    live_deployment_result JSONB,
    
    -- Cleanup
    expires_at TIMESTAMP, -- Staging-Umgebung wird nach 24h gelöscht
    cleaned_up BOOLEAN DEFAULT FALSE,
    cleaned_up_at TIMESTAMP,
    
    -- Metadaten
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_staging_user_id ON staging_deployments(user_id);
CREATE INDEX IF NOT EXISTS idx_staging_fix_id ON staging_deployments(fix_id);
CREATE INDEX IF NOT EXISTS idx_staging_status ON staging_deployments(status);
CREATE INDEX IF NOT EXISTS idx_staging_expires_at ON staging_deployments(expires_at);

-- ============================================================================
-- VIEWS für Dashboard
-- ============================================================================

-- View: User Audit Summary
CREATE OR REPLACE VIEW user_audit_summary AS
SELECT 
    u.id as user_id,
    u.email,
    COUNT(DISTINCT faa.id) as total_actions,
    COUNT(DISTINCT CASE WHEN faa.action_type = 'applied' THEN faa.id END) as fixes_applied,
    COUNT(DISTINCT CASE WHEN faa.action_type = 'downloaded' THEN faa.id END) as fixes_downloaded,
    COUNT(DISTINCT CASE WHEN faa.action_type = 'rolled_back' THEN faa.id END) as rollbacks,
    COUNT(DISTINCT CASE WHEN faa.success = true THEN faa.id END) as successful_actions,
    COUNT(DISTINCT CASE WHEN faa.success = false THEN faa.id END) as failed_actions,
    MAX(faa.applied_at) as last_action_at,
    COUNT(DISTINCT fb.id) as total_backups
FROM users u
LEFT JOIN fix_application_audit faa ON u.id = faa.user_id
LEFT JOIN fix_backups fb ON u.id = fb.user_id
GROUP BY u.id, u.email;

-- View: Recent Audit Log (für Dashboard)
CREATE OR REPLACE VIEW recent_audit_log AS
SELECT 
    faa.id,
    faa.user_id,
    u.email,
    faa.fix_id,
    faa.fix_category,
    faa.action_type,
    faa.deployment_method,
    faa.applied_at,
    faa.success,
    faa.backup_id,
    faa.rollback_available,
    fb.backup_location,
    fb.backup_size_bytes
FROM fix_application_audit faa
JOIN users u ON faa.user_id = u.id
LEFT JOIN fix_backups fb ON faa.backup_id = fb.backup_id
ORDER BY faa.applied_at DESC
LIMIT 1000;

-- ============================================================================
-- CLEANUP FUNCTIONS
-- ============================================================================

-- Funktion: Alte Backups löschen (>30 Tage)
CREATE OR REPLACE FUNCTION cleanup_expired_backups()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM fix_backups
    WHERE expires_at < NOW()
    AND is_restored = false;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Funktion: Alte Staging-Deployments löschen (>24h)
CREATE OR REPLACE FUNCTION cleanup_staging_environments()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    UPDATE staging_deployments
    SET cleaned_up = true,
        cleaned_up_at = NOW()
    WHERE expires_at < NOW()
    AND cleaned_up = false;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- KOMMENTARE für Dokumentation
-- ============================================================================

COMMENT ON TABLE fix_application_audit IS 'Rechtssicherer Audit-Trail aller Fix-Anwendungen für Haftungssicherheit';
COMMENT ON TABLE fix_backups IS 'Backup-Informationen für Rollback-Funktionalität';
COMMENT ON TABLE staging_deployments IS 'Premium-Feature: Staging-Deployments mit Screenshot-Diff';

COMMENT ON COLUMN fix_application_audit.user_confirmed IS 'Hat der User explizit bestätigt (für rechtliche Nachweisbarkeit)';
COMMENT ON COLUMN fix_application_audit.rollback_available IS 'Kann die Änderung rückgängig gemacht werden?';
COMMENT ON COLUMN fix_backups.expires_at IS 'Backups werden nach 30 Tagen automatisch gelöscht';
COMMENT ON COLUMN staging_deployments.screenshot_diff IS 'Pixelmatch-Diff zwischen Before/After für visuelle Kontrolle';

-- ============================================================================
-- GRANTS (für Production)
-- ============================================================================

-- Complyo Backend hat vollen Zugriff
GRANT ALL PRIVILEGES ON TABLE fix_application_audit TO complyo_user;
GRANT ALL PRIVILEGES ON TABLE fix_backups TO complyo_user;
GRANT ALL PRIVILEGES ON TABLE staging_deployments TO complyo_user;

-- Read-only für Analytics
GRANT SELECT ON user_audit_summary TO complyo_analytics;
GRANT SELECT ON recent_audit_log TO complyo_analytics;

-- ============================================================================
-- DONE
-- ============================================================================

-- Erfolgs-Meldung
DO $$
BEGIN
    RAISE NOTICE '✅ Fix Audit Trail erfolgreich erstellt!';
    RAISE NOTICE '   - fix_application_audit: Haupttabelle für Audit-Logging';
    RAISE NOTICE '   - fix_backups: Backup-Verwaltung';
    RAISE NOTICE '   - staging_deployments: Premium Staging-Feature';
    RAISE NOTICE '   - Views: user_audit_summary, recent_audit_log';
    RAISE NOTICE '   - Cleanup-Funktionen: cleanup_expired_backups(), cleanup_staging_environments()';
END $$;

