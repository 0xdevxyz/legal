-- Migration: Create Cookie Compliance Tables
-- Date: 2025-11-11

-- Cookie Services (Template Library)
CREATE TABLE IF NOT EXISTS cookie_services (
    id SERIAL PRIMARY KEY,
    service_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('necessary', 'functional', 'analytics', 'marketing')),
    provider VARCHAR(255),
    description TEXT,
    cookies JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    plan_required VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cookie_services_category ON cookie_services(category);
CREATE INDEX IF NOT EXISTS idx_cookie_services_active ON cookie_services(is_active);

-- Cookie Banner Configurations
CREATE TABLE IF NOT EXISTS cookie_banner_configs (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID,
    layout VARCHAR(50) DEFAULT 'banner_bottom',
    primary_color VARCHAR(7) DEFAULT '#6366f1',
    accent_color VARCHAR(7) DEFAULT '#8b5cf6',
    text_color VARCHAR(7) DEFAULT '#333333',
    bg_color VARCHAR(7) DEFAULT '#ffffff',
    button_style VARCHAR(50) DEFAULT 'rounded',
    position VARCHAR(50) DEFAULT 'bottom',
    width_mode VARCHAR(50) DEFAULT 'full',
    texts JSONB DEFAULT '{}',
    services JSONB DEFAULT '[]',
    show_on_pages JSONB DEFAULT '{"all": true, "exclude": []}',
    geo_restriction JSONB DEFAULT '{"enabled": false, "countries": []}',
    auto_block_scripts BOOLEAN DEFAULT true,
    respect_dnt BOOLEAN DEFAULT true,
    cookie_lifetime_days INTEGER DEFAULT 365,
    show_branding BOOLEAN DEFAULT true,
    custom_logo_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cookie_banner_configs_site ON cookie_banner_configs(site_id);
CREATE INDEX IF NOT EXISTS idx_cookie_banner_configs_user ON cookie_banner_configs(user_id);

-- Consent Logs
CREATE TABLE IF NOT EXISTS cookie_consent_logs (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR(255) NOT NULL,
    visitor_id VARCHAR(255) NOT NULL,
    consent_categories JSONB NOT NULL,
    services_accepted JSONB DEFAULT '[]',
    language VARCHAR(10) DEFAULT 'de',
    banner_shown BOOLEAN DEFAULT true,
    user_agent TEXT,
    ip_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_consent_logs_site ON cookie_consent_logs(site_id);
CREATE INDEX IF NOT EXISTS idx_consent_logs_visitor ON cookie_consent_logs(visitor_id);
CREATE INDEX IF NOT EXISTS idx_consent_logs_created ON cookie_consent_logs(created_at);

-- Consent Statistics (Aggregated Daily)
CREATE TABLE IF NOT EXISTS cookie_compliance_stats (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    total_impressions INTEGER DEFAULT 0,
    accepted_all INTEGER DEFAULT 0,
    accepted_partial INTEGER DEFAULT 0,
    rejected_all INTEGER DEFAULT 0,
    accepted_necessary INTEGER DEFAULT 0,
    accepted_functional INTEGER DEFAULT 0,
    accepted_analytics INTEGER DEFAULT 0,
    accepted_marketing INTEGER DEFAULT 0,
    service_stats JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site_id, date)
);

CREATE INDEX IF NOT EXISTS idx_stats_site_date ON cookie_compliance_stats(site_id, date);

-- Log
DO $$
BEGIN
    RAISE NOTICE 'Cookie Compliance tables created successfully';
END $$;

