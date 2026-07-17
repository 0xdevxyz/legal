-- Database Performance Optimization for Complyo Production
-- PostgreSQL 15 optimizations, indexing, and maintenance
-- Version: 2.0
-- Date: 2025-08-27

-- ===========================================
-- PERFORMANCE INDEXES
-- ===========================================

-- Users table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created ON users(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login ON users(last_login_at);

-- Analysis results indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_url ON analysis_results(url);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_user ON analysis_results(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_created ON analysis_results(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_score ON analysis_results(compliance_score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_status ON analysis_results(status);

-- Composite index for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_user_created ON analysis_results(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_url_created ON analysis_results(url, created_at DESC);

-- Payments and subscriptions indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_user ON payments(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_created ON payments(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

-- Audit logs indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_created ON audit_logs(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_ip ON audit_logs(ip_address);

-- Session management indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);

-- ===========================================
-- PERFORMANCE VIEWS
-- ===========================================

-- User activity summary view
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT 
    u.id,
    u.email,
    u.company_name,
    COUNT(ar.id) as total_analyses,
    AVG(ar.compliance_score) as avg_compliance_score,
    MAX(ar.created_at) as last_analysis,
    COUNT(CASE WHEN ar.created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as analyses_last_30_days
FROM users u
LEFT JOIN analysis_results ar ON u.id = ar.user_id
WHERE u.is_active = true
GROUP BY u.id, u.email, u.company_name;

-- System performance metrics view
CREATE OR REPLACE VIEW system_metrics AS
SELECT 
    'total_users' as metric,
    COUNT(*)::text as value,
    NOW() as updated_at
FROM users WHERE is_active = true
UNION ALL
SELECT 
    'total_analyses' as metric,
    COUNT(*)::text as value,
    NOW() as updated_at
FROM analysis_results
UNION ALL
SELECT 
    'avg_compliance_score' as metric,
    ROUND(AVG(compliance_score), 2)::text as value,
    NOW() as updated_at
FROM analysis_results WHERE created_at >= NOW() - INTERVAL '30 days'
UNION ALL
SELECT 
    'analyses_today' as metric,
    COUNT(*)::text as value,
    NOW() as updated_at
FROM analysis_results WHERE created_at >= CURRENT_DATE;

-- ===========================================
-- STORED PROCEDURES FOR PERFORMANCE
-- ===========================================

-- Cleanup old sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    INSERT INTO audit_logs (action, details, created_at)
    VALUES ('session_cleanup', jsonb_build_object('deleted_sessions', deleted_count), NOW());
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Archive old analysis results
CREATE OR REPLACE FUNCTION archive_old_analyses(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Move old analyses to archive table
    WITH archived AS (
        DELETE FROM analysis_results 
        WHERE created_at < NOW() - (retention_days || ' days')::INTERVAL
        RETURNING *
    )
    INSERT INTO analysis_results_archive SELECT * FROM archived;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    INSERT INTO audit_logs (action, details, created_at)
    VALUES ('analysis_archive', jsonb_build_object('archived_count', archived_count, 'retention_days', retention_days), NOW());
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Update table statistics
CREATE OR REPLACE FUNCTION update_table_statistics()
RETURNS VOID AS $$
BEGIN
    ANALYZE users;
    ANALYZE analysis_results;
    ANALYZE payments;
    ANALYZE subscriptions;
    ANALYZE audit_logs;
    ANALYZE user_sessions;
    
    INSERT INTO audit_logs (action, details, created_at)
    VALUES ('statistics_update', jsonb_build_object('status', 'completed'), NOW());
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- ARCHIVE TABLES
-- ===========================================

-- Create archive table for old analysis results
CREATE TABLE IF NOT EXISTS analysis_results_archive (
    LIKE analysis_results INCLUDING ALL
);

-- Add partition key if not exists
ALTER TABLE analysis_results_archive 
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- ===========================================
-- PERFORMANCE CONFIGURATION
-- ===========================================

-- Connection pooling settings (applied via Docker command)
-- max_connections = 100
-- shared_buffers = 256MB
-- effective_cache_size = 1GB
-- work_mem = 4MB
-- maintenance_work_mem = 64MB

-- WAL settings for performance
-- wal_buffers = 16MB
-- checkpoint_completion_target = 0.9
-- min_wal_size = 1GB
-- max_wal_size = 4GB

-- ===========================================
-- AUTOMATED MAINTENANCE JOBS
-- ===========================================

-- Create maintenance schedule table
CREATE TABLE IF NOT EXISTS maintenance_schedule (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL UNIQUE,
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    interval_hours INTEGER NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert maintenance jobs
INSERT INTO maintenance_schedule (job_name, interval_hours, next_run) VALUES
('cleanup_expired_sessions', 24, NOW() + INTERVAL '1 hour'),
('update_table_statistics', 168, NOW() + INTERVAL '2 hours'), -- Weekly
('vacuum_analyze_tables', 24, NOW() + INTERVAL '3 hours'),
('archive_old_analyses', 720, NOW() + INTERVAL '4 hours') -- Monthly
ON CONFLICT (job_name) DO NOTHING;

-- Function to run scheduled maintenance
CREATE OR REPLACE FUNCTION run_maintenance_job(job_name_param VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    job_record RECORD;
    result BOOLEAN := false;
BEGIN
    -- Get job details
    SELECT * INTO job_record FROM maintenance_schedule 
    WHERE job_name = job_name_param AND enabled = true AND next_run <= NOW();
    
    IF NOT FOUND THEN
        RETURN false;
    END IF;
    
    -- Execute the appropriate maintenance job
    CASE job_record.job_name
        WHEN 'cleanup_expired_sessions' THEN
            PERFORM cleanup_expired_sessions();
            result := true;
        WHEN 'update_table_statistics' THEN
            PERFORM update_table_statistics();
            result := true;
        WHEN 'vacuum_analyze_tables' THEN
            VACUUM ANALYZE;
            result := true;
        WHEN 'archive_old_analyses' THEN
            PERFORM archive_old_analyses();
            result := true;
    END CASE;
    
    -- Update job schedule
    IF result THEN
        UPDATE maintenance_schedule 
        SET last_run = NOW(), 
            next_run = NOW() + (interval_hours || ' hours')::INTERVAL
        WHERE job_name = job_name_param;
    END IF;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- GDPR COMPLIANCE FUNCTIONS
-- ===========================================

-- Right to be forgotten implementation
CREATE OR REPLACE FUNCTION gdpr_delete_user_data(user_email VARCHAR)
RETURNS JSONB AS $$
DECLARE
    user_id_val INTEGER;
    deletion_summary JSONB := '{}'::JSONB;
    deleted_count INTEGER;
BEGIN
    -- Get user ID
    SELECT id INTO user_id_val FROM users WHERE email = user_email;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object('error', 'User not found');
    END IF;
    
    -- Delete analysis results
    DELETE FROM analysis_results WHERE user_id = user_id_val;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    deletion_summary := deletion_summary || jsonb_build_object('analysis_results', deleted_count);
    
    -- Delete payments
    DELETE FROM payments WHERE user_id = user_id_val;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    deletion_summary := deletion_summary || jsonb_build_object('payments', deleted_count);
    
    -- Delete subscriptions
    DELETE FROM subscriptions WHERE user_id = user_id_val;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    deletion_summary := deletion_summary || jsonb_build_object('subscriptions', deleted_count);
    
    -- Delete audit logs (anonymize IP addresses)
    UPDATE audit_logs SET details = details || jsonb_build_object('anonymized', true), 
                         ip_address = '0.0.0.0'
    WHERE user_id = user_id_val;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    deletion_summary := deletion_summary || jsonb_build_object('audit_logs_anonymized', deleted_count);
    
    -- Delete user sessions
    DELETE FROM user_sessions WHERE user_id = user_id_val;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    deletion_summary := deletion_summary || jsonb_build_object('user_sessions', deleted_count);
    
    -- Finally delete user
    DELETE FROM users WHERE id = user_id_val;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    deletion_summary := deletion_summary || jsonb_build_object('user_deleted', deleted_count > 0);
    
    -- Log the deletion
    INSERT INTO audit_logs (action, details, created_at)
    VALUES ('gdpr_deletion', deletion_summary || jsonb_build_object('user_email', user_email), NOW());
    
    RETURN deletion_summary;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- FINAL OPTIMIZATION
-- ===========================================

-- Refresh materialized views if any exist
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_stats;

-- Update all table statistics
SELECT update_table_statistics();

-- Log optimization completion
INSERT INTO audit_logs (action, details, created_at)
VALUES ('database_optimization', jsonb_build_object('status', 'completed', 'version', '2.0'), NOW());