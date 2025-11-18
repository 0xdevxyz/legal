-- ============================================================================
-- Complyo - eRecht24 Full Integration Migration
-- ============================================================================
-- 
-- Erstellt Tabellen für vollständige eRecht24-Integration:
-- - Projekt-Management
-- - Text-Caching
-- - Sync-History
--
-- Author: Complyo.tech
-- Date: 2025-01-11
-- ============================================================================

-- Table: erecht24_projects
-- Stores eRecht24 project associations for users/domains
CREATE TABLE IF NOT EXISTS erecht24_projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    erecht24_project_id VARCHAR(255),
    erecht24_api_key VARCHAR(255),
    erecht24_secret VARCHAR(512),
    status VARCHAR(50) DEFAULT 'active',
    auto_sync BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_user_domain UNIQUE(user_id, domain),
    CONSTRAINT unique_erecht24_project UNIQUE(erecht24_project_id)
);

-- Index for faster lookups
CREATE INDEX idx_erecht24_projects_user_id ON erecht24_projects(user_id);
CREATE INDEX idx_erecht24_projects_domain ON erecht24_projects(domain);
CREATE INDEX idx_erecht24_projects_status ON erecht24_projects(status);

-- Comment
COMMENT ON TABLE erecht24_projects IS 'eRecht24 project associations for Complyo users';
COMMENT ON COLUMN erecht24_projects.domain IS 'Website domain (e.g., example.com)';
COMMENT ON COLUMN erecht24_projects.erecht24_project_id IS 'Project ID from eRecht24 API';
COMMENT ON COLUMN erecht24_projects.status IS 'active, suspended, deleted';


-- Table: erecht24_texts_cache
-- Caches legal texts fetched from eRecht24 to reduce API calls
CREATE TABLE IF NOT EXISTS erecht24_texts_cache (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES erecht24_projects(id) ON DELETE CASCADE,
    text_type VARCHAR(50) NOT NULL,
    language VARCHAR(10) DEFAULT 'de',
    html_content TEXT NOT NULL,
    raw_content TEXT,
    version VARCHAR(50),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cache_expires_at TIMESTAMP,
    fetch_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_project_text_lang UNIQUE(project_id, text_type, language)
);

-- Indexes
CREATE INDEX idx_erecht24_cache_project_id ON erecht24_texts_cache(project_id);
CREATE INDEX idx_erecht24_cache_text_type ON erecht24_texts_cache(text_type);
CREATE INDEX idx_erecht24_cache_expires ON erecht24_texts_cache(cache_expires_at);

-- Comment
COMMENT ON TABLE erecht24_texts_cache IS 'Cached legal texts from eRecht24';
COMMENT ON COLUMN erecht24_texts_cache.text_type IS 'impressum, datenschutz, agb, widerruf, disclaimer';
COMMENT ON COLUMN erecht24_texts_cache.html_content IS 'HTML content with white-label processing applied';
COMMENT ON COLUMN erecht24_texts_cache.raw_content IS 'Original content from eRecht24 (optional)';
COMMENT ON COLUMN erecht24_texts_cache.cache_expires_at IS 'When cache should be refreshed';


-- Table: erecht24_sync_history
-- Tracks sync operations for monitoring and debugging
CREATE TABLE IF NOT EXISTS erecht24_sync_history (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES erecht24_projects(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    texts_updated INTEGER DEFAULT 0,
    error_message TEXT,
    api_response_code INTEGER,
    duration_ms INTEGER,
    triggered_by VARCHAR(50),
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (status IN ('success', 'partial', 'failed'))
);

-- Indexes
CREATE INDEX idx_erecht24_sync_project_id ON erecht24_sync_history(project_id);
CREATE INDEX idx_erecht24_sync_status ON erecht24_sync_history(status);
CREATE INDEX idx_erecht24_sync_date ON erecht24_sync_history(synced_at DESC);

-- Comment
COMMENT ON TABLE erecht24_sync_history IS 'History of eRecht24 sync operations';
COMMENT ON COLUMN erecht24_sync_history.sync_type IS 'manual, webhook, scheduled, auto';
COMMENT ON COLUMN erecht24_sync_history.triggered_by IS 'user_id, system, webhook, cron';


-- Table: erecht24_webhooks
-- Stores webhook configurations for automatic updates
CREATE TABLE IF NOT EXISTS erecht24_webhooks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES erecht24_projects(id) ON DELETE CASCADE,
    webhook_url VARCHAR(512) NOT NULL,
    webhook_secret VARCHAR(255),
    events JSON,
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_project_webhook UNIQUE(project_id)
);

-- Index
CREATE INDEX idx_erecht24_webhooks_active ON erecht24_webhooks(is_active);

-- Comment
COMMENT ON TABLE erecht24_webhooks IS 'Webhook configurations for automatic text updates';
COMMENT ON COLUMN erecht24_webhooks.events IS 'Array of event types to listen for';


-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_erecht24_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update updated_at
CREATE TRIGGER trigger_erecht24_projects_updated_at
BEFORE UPDATE ON erecht24_projects
FOR EACH ROW
EXECUTE FUNCTION update_erecht24_projects_updated_at();


-- Function: Clean expired cache entries
CREATE OR REPLACE FUNCTION clean_erecht24_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM erecht24_texts_cache
    WHERE cache_expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Comment
COMMENT ON FUNCTION clean_erecht24_expired_cache() IS 'Removes expired cache entries, returns count of deleted rows';


-- Function: Get legal text with fallback
CREATE OR REPLACE FUNCTION get_erecht24_text_or_fallback(
    p_user_id INTEGER,
    p_domain VARCHAR,
    p_text_type VARCHAR,
    p_language VARCHAR DEFAULT 'de'
)
RETURNS TABLE (
    source VARCHAR,
    content TEXT,
    cached BOOLEAN,
    updated_at TIMESTAMP
) AS $$
BEGIN
    -- Try to get from cache
    RETURN QUERY
    SELECT 
        'erecht24'::VARCHAR as source,
        c.html_content as content,
        true as cached,
        c.last_updated as updated_at
    FROM erecht24_texts_cache c
    JOIN erecht24_projects p ON c.project_id = p.id
    WHERE p.user_id = p_user_id
      AND p.domain = p_domain
      AND p.status = 'active'
      AND c.text_type = p_text_type
      AND c.language = p_language
      AND (c.cache_expires_at IS NULL OR c.cache_expires_at > CURRENT_TIMESTAMP)
    LIMIT 1;
    
    -- If not found, return indication to fetch from API
    IF NOT FOUND THEN
        RETURN QUERY
        SELECT 
            'api_fetch_required'::VARCHAR,
            NULL::TEXT,
            false,
            NULL::TIMESTAMP;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Comment
COMMENT ON FUNCTION get_erecht24_text_or_fallback IS 'Gets legal text from cache or indicates API fetch needed';


-- View: Active projects with cache status
CREATE OR REPLACE VIEW v_erecht24_projects_status AS
SELECT 
    p.id,
    p.user_id,
    p.domain,
    p.erecht24_project_id,
    p.status,
    p.auto_sync,
    p.last_sync_at,
    COUNT(c.id) as cached_texts_count,
    MAX(c.last_updated) as last_text_update,
    COUNT(CASE WHEN c.cache_expires_at < CURRENT_TIMESTAMP THEN 1 END) as expired_cache_count,
    (
        SELECT COUNT(*) 
        FROM erecht24_sync_history h 
        WHERE h.project_id = p.id 
          AND h.status = 'failed' 
          AND h.synced_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
    ) as failed_syncs_24h
FROM erecht24_projects p
LEFT JOIN erecht24_texts_cache c ON p.id = c.project_id
GROUP BY p.id, p.user_id, p.domain, p.erecht24_project_id, p.status, p.auto_sync, p.last_sync_at;

-- Comment
COMMENT ON VIEW v_erecht24_projects_status IS 'Overview of eRecht24 projects with cache and sync status';


-- ============================================================================
-- Sample Data (Optional - for development/testing)
-- ============================================================================

-- Uncomment for development environment:
/*
INSERT INTO erecht24_projects (user_id, domain, erecht24_project_id, status) 
VALUES 
    (1, 'example.com', 'er24_demo_001', 'active'),
    (1, 'test.com', 'er24_demo_002', 'active')
ON CONFLICT (user_id, domain) DO NOTHING;

INSERT INTO erecht24_texts_cache (project_id, text_type, language, html_content, cache_expires_at)
SELECT 
    1,
    'impressum',
    'de',
    '<h1>Impressum (Demo)</h1><p>Demo-Content aus Cache</p>',
    CURRENT_TIMESTAMP + INTERVAL '7 days'
WHERE EXISTS (SELECT 1 FROM erecht24_projects WHERE id = 1);
*/


-- ============================================================================
-- Grants (adjust based on your setup)
-- ============================================================================

-- Grant permissions to application user (adjust username)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON erecht24_projects TO complyo_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON erecht24_texts_cache TO complyo_app;
-- GRANT SELECT, INSERT ON erecht24_sync_history TO complyo_app;
-- GRANT SELECT, INSERT, UPDATE ON erecht24_webhooks TO complyo_app;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO complyo_app;


-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check tables created:
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_name LIKE 'erecht24_%' AND table_schema = 'public';

-- Check constraints:
-- SELECT conname, contype FROM pg_constraint 
-- WHERE conrelid::regclass::text LIKE 'erecht24_%';

-- Check indexes:
-- SELECT indexname FROM pg_indexes 
-- WHERE tablename LIKE 'erecht24_%' AND schemaname = 'public';


-- ============================================================================
-- Migration Complete
-- ============================================================================

-- Log success (if logging table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'migration_log') THEN
        INSERT INTO migration_log (migration_name, status, executed_at)
        VALUES ('migration_erecht24_full', 'success', CURRENT_TIMESTAMP);
    END IF;
END $$;

-- Output success message
DO $$
BEGIN
    RAISE NOTICE '✅ eRecht24 Full Integration Migration completed successfully!';
    RAISE NOTICE '   - Created 4 tables: erecht24_projects, erecht24_texts_cache, erecht24_sync_history, erecht24_webhooks';
    RAISE NOTICE '   - Created helper functions and views';
    RAISE NOTICE '   - Created indexes and constraints';
END $$;


