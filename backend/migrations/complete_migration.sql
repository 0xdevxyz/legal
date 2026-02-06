-- =====================================================
-- COMPLETE MIGRATION - All missing tables
-- Run with: docker exec complyo-postgres psql -U complyo -d complyo_db -f /tmp/complete_migration.sql
-- =====================================================

-- 1. user_limits (BLOCKS REGISTRATION)
CREATE TABLE IF NOT EXISTS user_limits (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(50) DEFAULT 'free',
    max_websites INTEGER DEFAULT 1,
    max_scans_per_month INTEGER DEFAULT 5,
    max_fixes_per_month INTEGER DEFAULT 3,
    scans_used INTEGER DEFAULT 0,
    fixes_used INTEGER DEFAULT 0,
    current_period_start TIMESTAMP DEFAULT NOW(),
    current_period_end TIMESTAMP DEFAULT NOW() + INTERVAL '30 days',
    unlimited_fixes BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);
CREATE INDEX IF NOT EXISTS idx_user_limits_user_id ON user_limits(user_id);

-- 2. subscription_plans
CREATE TABLE IF NOT EXISTS subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    price_monthly DECIMAL(10,2),
    price_yearly DECIMAL(10,2),
    stripe_price_id_monthly VARCHAR(255),
    stripe_price_id_yearly VARCHAR(255),
    max_websites INTEGER DEFAULT 1,
    max_scans INTEGER DEFAULT 5,
    max_fixes INTEGER DEFAULT 3,
    features JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO subscription_plans (name, slug, price_monthly, price_yearly, max_websites, max_scans, max_fixes, features)
SELECT 'Free', 'free', 0, 0, 1, 5, 3, '{"basic_scan": true}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM subscription_plans WHERE slug = 'free');

INSERT INTO subscription_plans (name, slug, price_monthly, price_yearly, max_websites, max_scans, max_fixes, features)
SELECT 'AI', 'ai', 49.00, 468.00, 5, -1, -1, '{"basic_scan": true, "ai_fixes": true, "deep_scan": true}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM subscription_plans WHERE slug = 'ai');

INSERT INTO subscription_plans (name, slug, price_monthly, price_yearly, max_websites, max_scans, max_fixes, features)
SELECT 'Expert', 'expert', 149.00, 1428.00, -1, -1, -1, '{"basic_scan": true, "ai_fixes": true, "deep_scan": true, "priority_support": true, "expert_review": true}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM subscription_plans WHERE slug = 'expert');

-- 3. subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER REFERENCES subscription_plans(id),
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_id ON subscriptions(stripe_subscription_id);

-- 4. stripe_customers
CREATE TABLE IF NOT EXISTS stripe_customers (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 5. payment_history
CREATE TABLE IF NOT EXISTS payment_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_payment_id VARCHAR(255),
    amount DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'eur',
    status VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. plan_setup_fees
CREATE TABLE IF NOT EXISTS plan_setup_fees (
    id SERIAL PRIMARY KEY,
    plan_slug VARCHAR(50) NOT NULL,
    fee_amount DECIMAL(10,2) DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 7. domain_locks
CREATE TABLE IF NOT EXISTS domain_locks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    website_id UUID,
    domain VARCHAR(500) NOT NULL,
    lock_type VARCHAR(50) DEFAULT 'standard',
    is_active BOOLEAN DEFAULT TRUE,
    locked_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_domain_locks_user ON domain_locks(user_id);
CREATE INDEX IF NOT EXISTS idx_domain_locks_domain ON domain_locks(domain);

-- 8. oauth_providers
CREATE TABLE IF NOT EXISTS oauth_providers (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);

-- 9. oauth_states
CREATE TABLE IF NOT EXISTS oauth_states (
    id SERIAL PRIMARY KEY,
    state VARCHAR(255) UNIQUE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    redirect_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '10 minutes'
);

-- 10. email_verifications
CREATE TABLE IF NOT EXISTS email_verifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours'
);

-- 11. generated_documents
CREATE TABLE IF NOT EXISTS generated_documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    website_id UUID,
    doc_type VARCHAR(100) NOT NULL,
    title VARCHAR(500),
    content TEXT,
    language VARCHAR(10) DEFAULT 'de',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 12. score_history
CREATE TABLE IF NOT EXISTS score_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    website_id UUID,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    overall_score INTEGER,
    pillar_scores JSONB DEFAULT '{}',
    scan_date TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_score_history_website ON score_history(website_id);

-- 13. generated_fixes
CREATE TABLE IF NOT EXISTS generated_fixes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    website_id UUID,
    scan_id UUID,
    issue_id VARCHAR(255),
    fix_type VARCHAR(100),
    fix_content TEXT,
    fix_code TEXT,
    status VARCHAR(50) DEFAULT 'generated',
    applied_at TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 14. fix_application_audit
CREATE TABLE IF NOT EXISTS fix_application_audit (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    fix_id UUID,
    website_id UUID,
    action VARCHAR(50),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 15. fix_backups
CREATE TABLE IF NOT EXISTS fix_backups (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    fix_id UUID,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    original_content TEXT,
    backup_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 16. fix_generation_stats
CREATE TABLE IF NOT EXISTS fix_generation_stats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    fix_type VARCHAR(100),
    generation_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 17. fix_user_feedback
CREATE TABLE IF NOT EXISTS fix_user_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    fix_id UUID,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 18. cookie_consent_logs
CREATE TABLE IF NOT EXISTS cookie_consent_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    site_id VARCHAR(255),
    visitor_id VARCHAR(255),
    consent_type VARCHAR(50),
    categories JSONB DEFAULT '{}',
    ip_hash VARCHAR(64),
    user_agent TEXT,
    country_code VARCHAR(5),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cookie_consent_logs_site ON cookie_consent_logs(site_id);

-- 19. cookie_ab_tests
CREATE TABLE IF NOT EXISTS cookie_ab_tests (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    variant_a_config JSONB DEFAULT '{}',
    variant_b_config JSONB DEFAULT '{}',
    traffic_split INTEGER DEFAULT 50,
    winner VARCHAR(10),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    min_sample_size INTEGER DEFAULT 100,
    confidence_level DECIMAL(3,2) DEFAULT 0.95,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_running_test_per_site UNIQUE (site_id, status)
);

-- 20. cookie_ab_results
CREATE TABLE IF NOT EXISTS cookie_ab_results (
    id SERIAL PRIMARY KEY,
    test_id INTEGER REFERENCES cookie_ab_tests(id) ON DELETE CASCADE,
    variant VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    impressions INTEGER DEFAULT 0,
    accepts INTEGER DEFAULT 0,
    rejects INTEGER DEFAULT 0,
    customizes INTEGER DEFAULT 0,
    interaction_time_avg DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(test_id, variant, date)
);

-- 21. cookie_ab_assignments
CREATE TABLE IF NOT EXISTS cookie_ab_assignments (
    id SERIAL PRIMARY KEY,
    test_id INTEGER REFERENCES cookie_ab_tests(id) ON DELETE CASCADE,
    visitor_id VARCHAR(255) NOT NULL,
    variant VARCHAR(10) NOT NULL,
    assigned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(test_id, visitor_id)
);

-- 22. widget_analytics
CREATE TABLE IF NOT EXISTS widget_analytics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    site_id VARCHAR(255),
    event_type VARCHAR(100),
    event_data JSONB DEFAULT '{}',
    visitor_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_widget_analytics_site ON widget_analytics(site_id);

-- 23. widget_events (alias/secondary)
CREATE TABLE IF NOT EXISTS widget_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    site_id VARCHAR(255),
    widget_type VARCHAR(100),
    event_name VARCHAR(100),
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 24. widget_usage_stats
CREATE TABLE IF NOT EXISTS widget_usage_stats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    site_id VARCHAR(255),
    widget_type VARCHAR(100),
    date DATE DEFAULT CURRENT_DATE,
    impressions INTEGER DEFAULT 0,
    interactions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(site_id, widget_type, date)
);

-- 25. erecht24_projects
CREATE TABLE IF NOT EXISTS erecht24_projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id VARCHAR(255),
    project_name VARCHAR(500),
    domain VARCHAR(500),
    api_key TEXT,
    status VARCHAR(50) DEFAULT 'active',
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 26. erecht24_texts_cache / erecht24_cached_texts
CREATE TABLE IF NOT EXISTS erecht24_texts_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id VARCHAR(255),
    text_type VARCHAR(100),
    content TEXT,
    language VARCHAR(10) DEFAULT 'de',
    hash VARCHAR(64),
    fetched_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours'
);

CREATE TABLE IF NOT EXISTS erecht24_cached_texts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id VARCHAR(255),
    text_type VARCHAR(100),
    content TEXT,
    language VARCHAR(10) DEFAULT 'de',
    hash VARCHAR(64),
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- 27. erecht24_sync_history
CREATE TABLE IF NOT EXISTS erecht24_sync_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id VARCHAR(255),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    sync_type VARCHAR(100),
    status VARCHAR(50),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 28. erecht24_webhooks
CREATE TABLE IF NOT EXISTS erecht24_webhooks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id VARCHAR(255),
    event_type VARCHAR(100),
    payload JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 29. git_credentials
CREATE TABLE IF NOT EXISTS git_credentials (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) DEFAULT 'github',
    access_token TEXT,
    refresh_token TEXT,
    username VARCHAR(255),
    email VARCHAR(255),
    avatar_url TEXT,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

-- 30. git_connected_repos
CREATE TABLE IF NOT EXISTS git_connected_repos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    website_id UUID,
    provider VARCHAR(50) DEFAULT 'github',
    repo_full_name VARCHAR(500) NOT NULL,
    repo_url TEXT,
    default_branch VARCHAR(100) DEFAULT 'main',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 31. git_pull_requests
CREATE TABLE IF NOT EXISTS git_pull_requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    repo_id UUID REFERENCES git_connected_repos(id) ON DELETE CASCADE,
    pr_number INTEGER,
    pr_url TEXT,
    title VARCHAR(500),
    status VARCHAR(50) DEFAULT 'open',
    fix_ids JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 32. legal_changes
CREATE TABLE IF NOT EXISTS legal_changes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title VARCHAR(500),
    description TEXT,
    source VARCHAR(255),
    source_url TEXT,
    change_type VARCHAR(100),
    severity VARCHAR(50) DEFAULT 'medium',
    affected_areas JSONB DEFAULT '[]',
    effective_date DATE,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 33. legal_change_impacts
CREATE TABLE IF NOT EXISTS legal_change_impacts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    change_id UUID REFERENCES legal_changes(id) ON DELETE CASCADE,
    website_id UUID,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    impact_level VARCHAR(50),
    recommendations JSONB DEFAULT '[]',
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 34. legal_monitoring_logs
CREATE TABLE IF NOT EXISTS legal_monitoring_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source VARCHAR(255),
    check_timestamp TIMESTAMP DEFAULT NOW(),
    items_found INTEGER DEFAULT 0,
    new_items INTEGER DEFAULT 0,
    status VARCHAR(50),
    details JSONB DEFAULT '{}'
);

-- 35. user_legal_notifications
CREATE TABLE IF NOT EXISTS user_legal_notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    change_id UUID,
    notification_type VARCHAR(50),
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 36. user_company_data
CREATE TABLE IF NOT EXISTS user_company_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    company_name VARCHAR(500),
    company_address TEXT,
    company_email VARCHAR(255),
    company_phone VARCHAR(100),
    company_website VARCHAR(500),
    tax_id VARCHAR(100),
    trade_register VARCHAR(255),
    industry VARCHAR(255),
    employee_count VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 37. user_journeys
CREATE TABLE IF NOT EXISTS user_journeys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    current_step INTEGER DEFAULT 0,
    completed_steps JSONB DEFAULT '[]',
    journey_data JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 38. leads
CREATE TABLE IF NOT EXISTS leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    company VARCHAR(500),
    phone VARCHAR(100),
    source VARCHAR(100),
    scan_data JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'new',
    score INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);

-- 39. lead_consents
CREATE TABLE IF NOT EXISTS lead_consents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    consent_type VARCHAR(100) NOT NULL,
    granted BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    granted_at TIMESTAMP DEFAULT NOW()
);

-- 40. communication_log
CREATE TABLE IF NOT EXISTS communication_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    lead_id UUID,
    user_id UUID,
    channel VARCHAR(50),
    direction VARCHAR(20),
    subject VARCHAR(500),
    content TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 41. expert_service_requests
CREATE TABLE IF NOT EXISTS expert_service_requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    website_id UUID,
    service_type VARCHAR(100),
    priority VARCHAR(50) DEFAULT 'normal',
    status VARCHAR(50) DEFAULT 'pending',
    description TEXT,
    requirements JSONB DEFAULT '{}',
    response TEXT,
    assigned_to VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 42. export_history
CREATE TABLE IF NOT EXISTS export_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    export_type VARCHAR(100),
    file_path TEXT,
    file_size BIGINT,
    status VARCHAR(50) DEFAULT 'completed',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 43. website_structures
CREATE TABLE IF NOT EXISTS website_structures (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    website_id UUID,
    url VARCHAR(2000),
    structure_data JSONB DEFAULT '{}',
    page_count INTEGER DEFAULT 0,
    crawled_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 44. monitored_websites
CREATE TABLE IF NOT EXISTS monitored_websites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(2000) NOT NULL,
    check_frequency VARCHAR(50) DEFAULT 'daily',
    last_check TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 45. analysis_results
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scan_id UUID,
    website_id UUID,
    category VARCHAR(100),
    results JSONB DEFAULT '{}',
    score INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 46. scan_results
CREATE TABLE IF NOT EXISTS scan_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scan_id UUID,
    website_id UUID,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(2000),
    results JSONB DEFAULT '{}',
    overall_score INTEGER,
    pillar_scores JSONB DEFAULT '{}',
    issues JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 47. projects
CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 48. accessibility_alt_text_fixes
CREATE TABLE IF NOT EXISTS accessibility_alt_text_fixes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    website_id UUID,
    image_url TEXT,
    original_alt TEXT,
    generated_alt TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    confidence DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 49. accessibility_fix_packages
CREATE TABLE IF NOT EXISTS accessibility_fix_packages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    website_id UUID,
    scan_id UUID,
    package_data JSONB DEFAULT '{}',
    fix_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'generated',
    applied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 50. AI monitoring/feedback tables
CREATE TABLE IF NOT EXISTS ai_cache_stats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cache_key VARCHAR(255),
    hit_count INTEGER DEFAULT 0,
    last_hit TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_call_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    model VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost_estimate DECIMAL(10,6),
    duration_ms INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_classification_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    classification_id UUID,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    is_correct BOOLEAN,
    correct_category VARCHAR(100),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_fix_monitoring (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    fix_id UUID,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    fix_type VARCHAR(100),
    generation_time_ms INTEGER,
    validation_passed BOOLEAN,
    error_details TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_learning_cycles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cycle_type VARCHAR(100),
    data_points INTEGER DEFAULT 0,
    improvements JSONB DEFAULT '{}',
    status VARCHAR(50),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 51. compliance_fixes
CREATE TABLE IF NOT EXISTS compliance_fixes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scan_id UUID,
    issue_id VARCHAR(255),
    fix_type VARCHAR(100),
    original_code TEXT,
    fixed_code TEXT,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 52. complyo_main_pillars (config/reference table)
CREATE TABLE IF NOT EXISTS complyo_main_pillars (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    weight DECIMAL(3,2) DEFAULT 0.25,
    icon VARCHAR(100),
    color VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO complyo_main_pillars (name, slug, description, weight)
SELECT 'Datenschutz (DSGVO)', 'datenschutz', 'DSGVO & TTDSG Compliance', 0.35
WHERE NOT EXISTS (SELECT 1 FROM complyo_main_pillars WHERE slug = 'datenschutz');

INSERT INTO complyo_main_pillars (name, slug, description, weight)
SELECT 'Barrierefreiheit', 'barrierefreiheit', 'BFSG & WCAG 2.1 AA', 0.30
WHERE NOT EXISTS (SELECT 1 FROM complyo_main_pillars WHERE slug = 'barrierefreiheit');

INSERT INTO complyo_main_pillars (name, slug, description, weight)
SELECT 'Cookie Compliance', 'cookies', 'Cookie-Banner & Consent', 0.20
WHERE NOT EXISTS (SELECT 1 FROM complyo_main_pillars WHERE slug = 'cookies');

INSERT INTO complyo_main_pillars (name, slug, description, weight)
SELECT 'Impressum & Rechtstexte', 'impressum', 'TMG & Rechtstexte', 0.15
WHERE NOT EXISTS (SELECT 1 FROM complyo_main_pillars WHERE slug = 'impressum');

-- Done!
