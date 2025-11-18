-- ============================================================================
-- Complyo - eRecht24 Full Integration Migration (FIXED)
-- ============================================================================
-- 
-- FIXED: Changed user_id from INTEGER to UUID to match existing users table
--
-- ============================================================================

-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: erecht24_projects
-- Stores eRecht24 project associations for users/domains
CREATE TABLE IF NOT EXISTS erecht24_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
CREATE INDEX IF NOT EXISTS idx_erecht24_projects_user_id ON erecht24_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_erecht24_projects_domain ON erecht24_projects(domain);
CREATE INDEX IF NOT EXISTS idx_erecht24_projects_status ON erecht24_projects(status);

-- Comment
COMMENT ON TABLE erecht24_projects IS 'eRecht24 project associations for Complyo users';
COMMENT ON COLUMN erecht24_projects.domain IS 'Website domain (e.g., example.com)';
COMMENT ON COLUMN erecht24_projects.erecht24_project_id IS 'Project ID from eRecht24 API';
COMMENT ON COLUMN erecht24_projects.status IS 'active, suspended, deleted';


-- Table: erecht24_texts_cache
-- Caches legal texts fetched from eRecht24 to reduce API calls
CREATE TABLE IF NOT EXISTS erecht24_texts_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES erecht24_projects(id) ON DELETE CASCADE,
    text_type VARCHAR(50) NOT NULL,
    language VARCHAR(10) DEFAULT 'de',
    content TEXT NOT NULL,
    html_content TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    version INTEGER DEFAULT 1,
    
    CONSTRAINT unique_project_text_lang UNIQUE(project_id, text_type, language)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_erecht24_cache_project ON erecht24_texts_cache(project_id);
CREATE INDEX IF NOT EXISTS idx_erecht24_cache_type ON erecht24_texts_cache(text_type);
CREATE INDEX IF NOT EXISTS idx_erecht24_cache_expires ON erecht24_texts_cache(expires_at);

-- Comment
COMMENT ON TABLE erecht24_texts_cache IS 'Cached legal texts from eRecht24 API';
COMMENT ON COLUMN erecht24_texts_cache.text_type IS 'impressum, datenschutz, agb, widerruf, etc.';
COMMENT ON COLUMN erecht24_texts_cache.expires_at IS 'When cache expires (typically +7 days)';


-- Table: erecht24_sync_history
-- Tracks sync operations for monitoring and debugging
CREATE TABLE IF NOT EXISTS erecht24_sync_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES erecht24_projects(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    texts_synced INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_erecht24_sync_project ON erecht24_sync_history(project_id);
CREATE INDEX IF NOT EXISTS idx_erecht24_sync_started ON erecht24_sync_history(started_at);
CREATE INDEX IF NOT EXISTS idx_erecht24_sync_status ON erecht24_sync_history(status);

-- Comment
COMMENT ON TABLE erecht24_sync_history IS 'History of all eRecht24 sync operations';
COMMENT ON COLUMN erecht24_sync_history.sync_type IS 'manual, auto, webhook, initial';
COMMENT ON COLUMN erecht24_sync_history.status IS 'success, failed, partial';


-- Table: erecht24_webhooks
-- Stores incoming webhooks from eRecht24 for legal text updates
CREATE TABLE IF NOT EXISTS erecht24_webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES erecht24_projects(id) ON DELETE SET NULL,
    webhook_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_erecht24_webhooks_project ON erecht24_webhooks(project_id);
CREATE INDEX IF NOT EXISTS idx_erecht24_webhooks_processed ON erecht24_webhooks(processed);
CREATE INDEX IF NOT EXISTS idx_erecht24_webhooks_received ON erecht24_webhooks(received_at);
CREATE INDEX IF NOT EXISTS idx_erecht24_webhooks_type ON erecht24_webhooks(webhook_type);

-- Comment
COMMENT ON TABLE erecht24_webhooks IS 'Incoming webhooks from eRecht24 API';
COMMENT ON COLUMN erecht24_webhooks.webhook_type IS 'text_updated, project_changed, etc.';


-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_erecht24_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM erecht24_texts_cache
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_erecht24_cache() IS 'Removes expired cache entries';


-- Function: Update project sync timestamp
CREATE OR REPLACE FUNCTION update_erecht24_project_sync_time()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE erecht24_projects
    SET last_sync_at = CURRENT_TIMESTAMP
    WHERE id = NEW.project_id AND NEW.status = 'success';
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_erecht24_project_sync_time() IS 'Automatically updates last_sync_at on successful sync';

-- Create trigger for auto-updating sync time
DROP TRIGGER IF EXISTS trigger_update_sync_time ON erecht24_sync_history;
CREATE TRIGGER trigger_update_sync_time
    AFTER INSERT ON erecht24_sync_history
    FOR EACH ROW
    EXECUTE FUNCTION update_erecht24_project_sync_time();


-- Function: Get project cache status
CREATE OR REPLACE FUNCTION get_erecht24_cache_status(p_project_id UUID)
RETURNS TABLE(
    text_type VARCHAR,
    cached_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_expired BOOLEAN,
    hours_until_expiry NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        tc.text_type,
        tc.cached_at,
        tc.expires_at,
        (tc.expires_at < NOW()) as is_expired,
        ROUND(EXTRACT(EPOCH FROM (tc.expires_at - NOW())) / 3600, 2) as hours_until_expiry
    FROM erecht24_texts_cache tc
    WHERE tc.project_id = p_project_id
    ORDER BY tc.text_type;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_erecht24_cache_status(UUID) IS 'Returns cache status for a project';


-- ============================================================================
-- Views
-- ============================================================================

-- View: Project status overview
CREATE OR REPLACE VIEW v_erecht24_projects_status AS
SELECT 
    p.id,
    p.user_id,
    p.domain,
    p.status,
    p.last_sync_at,
    p.created_at,
    COUNT(DISTINCT tc.text_type) as cached_texts_count,
    COUNT(DISTINCT CASE WHEN tc.expires_at < NOW() THEN tc.text_type END) as expired_texts_count,
    (SELECT sync_type FROM erecht24_sync_history sh 
     WHERE sh.project_id = p.id 
     ORDER BY started_at DESC LIMIT 1) as last_sync_type,
    (SELECT status FROM erecht24_sync_history sh 
     WHERE sh.project_id = p.id 
     ORDER BY started_at DESC LIMIT 1) as last_sync_status
FROM erecht24_projects p
LEFT JOIN erecht24_texts_cache tc ON p.id = tc.project_id
GROUP BY p.id, p.user_id, p.domain, p.status, p.last_sync_at, p.created_at;

COMMENT ON VIEW v_erecht24_projects_status IS 'Overview of all eRecht24 projects with cache status';


-- ============================================================================
-- Grant Permissions (adjust as needed)
-- ============================================================================

-- Grant access to complyo_user (adjust to your actual user)
GRANT SELECT, INSERT, UPDATE, DELETE ON erecht24_projects TO complyo_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON erecht24_texts_cache TO complyo_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON erecht24_sync_history TO complyo_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON erecht24_webhooks TO complyo_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO complyo_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO complyo_user;


-- ============================================================================
-- Final Message
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE '✅ eRecht24 Full Integration Migration completed successfully!';
    RAISE NOTICE '   - Created 4 tables: erecht24_projects, erecht24_texts_cache, erecht24_sync_history, erecht24_webhooks';
    RAISE NOTICE '   - Created helper functions and views';
    RAISE NOTICE '   - Created indexes and constraints';
    RAISE NOTICE '   - FIXED: Using UUID for user_id to match existing users table';
END $$;

