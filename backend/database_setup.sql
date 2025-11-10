-- Complyo Database Complete Setup
-- This script creates all necessary tables and data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types
CREATE TYPE subscription_tier AS ENUM ('free', 'pro', 'enterprise');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'expired', 'trial');
CREATE TYPE scan_frequency AS ENUM ('daily', 'weekly', 'monthly', 'manual');
CREATE TYPE website_status AS ENUM ('active', 'paused', 'error');
CREATE TYPE scan_type AS ENUM ('manual', 'scheduled', 'api');
CREATE TYPE team_role AS ENUM ('owner', 'admin', 'member', 'viewer');

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    company_name VARCHAR(255),
    phone_number VARCHAR(50),
    
    subscription_tier subscription_tier DEFAULT 'free',
    subscription_status subscription_status DEFAULT 'trial',
    subscription_end_date TIMESTAMP WITH TIME ZONE,
    trial_end_date TIMESTAMP WITH TIME ZONE,
    
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    
    monthly_scans_limit INTEGER DEFAULT 10,
    monthly_scans_used INTEGER DEFAULT 0,
    total_scans INTEGER DEFAULT 0,
    api_key VARCHAR(255) UNIQUE,
    
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked_until TIMESTAMP WITH TIME ZONE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255)
);

-- User Sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    refresh_token VARCHAR(500) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    is_revoked BOOLEAN DEFAULT FALSE
);

-- Websites table
CREATE TABLE IF NOT EXISTS websites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    name VARCHAR(255),
    
    scan_frequency scan_frequency DEFAULT 'weekly',
    auto_fix_enabled BOOLEAN DEFAULT FALSE,
    notification_enabled BOOLEAN DEFAULT TRUE,
    
    last_scan_date TIMESTAMP WITH TIME ZONE,
    last_score FLOAT,
    status website_status DEFAULT 'active',
    
    favicon_url VARCHAR(500),
    screenshot_url VARCHAR(500),
    technology_stack JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tracked Websites (for compatibility)
CREATE TABLE IF NOT EXISTS tracked_websites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    url VARCHAR(500) NOT NULL UNIQUE,
    name VARCHAR(255),
    last_scan_date TIMESTAMP,
    last_score FLOAT,
    scan_frequency VARCHAR(50) DEFAULT 'weekly',
    auto_fix_enabled BOOLEAN DEFAULT FALSE,
    notification_enabled BOOLEAN DEFAULT TRUE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Scan History table (complete with all columns)
CREATE TABLE IF NOT EXISTS scan_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id VARCHAR(255),
    user_id UUID,
    website_id UUID NOT NULL,
    url VARCHAR(500),
    scan_date TIMESTAMP DEFAULT NOW(),
    
    overall_score FLOAT,
    compliance_score FLOAT,
    legal_score FLOAT,
    cookie_score FLOAT,
    accessibility_score FLOAT,
    privacy_score FLOAT,
    
    issues_count INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    
    results JSONB,
    scan_data JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scans table
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    website_id UUID NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    
    overall_score FLOAT,
    legal_score FLOAT,
    cookie_score FLOAT,
    accessibility_score FLOAT,
    privacy_score FLOAT,
    
    results JSONB,
    issues_count INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    
    scan_type scan_type DEFAULT 'manual',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fix Jobs table
CREATE TABLE IF NOT EXISTS fix_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    scan_id VARCHAR(255),
    issue_id VARCHAR(255),
    issue_category VARCHAR(100),
    issue_data JSONB,
    
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    
    progress_percent INTEGER DEFAULT 0,
    current_step TEXT,
    
    result TEXT,
    generated_content TEXT,
    implementation_guide TEXT,
    error_message TEXT,
    
    estimated_duration_seconds INTEGER DEFAULT 60,
    
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Legal News table
CREATE TABLE IF NOT EXISTS legal_news (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    summary TEXT,
    content TEXT,
    url VARCHAR(500),
    source VARCHAR(255),
    source_url VARCHAR(500),
    published_date TIMESTAMP,
    fetched_date TIMESTAMP DEFAULT NOW(),
    category VARCHAR(100),
    news_type VARCHAR(50) DEFAULT 'general',
    impact_level VARCHAR(50),
    affected_sectors TEXT[],
    tags TEXT[],
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- RSS Feed Sources table
CREATE TABLE IF NOT EXISTS rss_feed_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL UNIQUE,
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_fetch TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Compliance Risk Matrix table
CREATE TABLE IF NOT EXISTS compliance_risk_matrix (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    issue_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) DEFAULT 'medium',
    fine_min INTEGER DEFAULT 0,
    fine_max INTEGER DEFAULT 0,
    min_risk_euro INTEGER DEFAULT 0,
    max_risk_euro INTEGER DEFAULT 0,
    legal_basis TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Cookie Compliance Stats table
CREATE TABLE IF NOT EXISTS cookie_compliance_stats (
    id SERIAL PRIMARY KEY,
    website_id UUID,
    site_identifier VARCHAR(255) NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    consents_total INTEGER DEFAULT 0,
    consents_accepted INTEGER DEFAULT 0,
    consents_rejected INTEGER DEFAULT 0,
    consents_custom INTEGER DEFAULT 0,
    accepted_all INTEGER DEFAULT 0,
    rejected_all INTEGER DEFAULT 0,
    accepted_partial INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    total_impressions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Team Members table
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role team_role DEFAULT 'member',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, user_id)
);

-- AI Compliance Scans table
CREATE TABLE IF NOT EXISTS ai_compliance_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scan_data JSONB,
    risk_level VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI Systems table
CREATE TABLE IF NOT EXISTS ai_systems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    risk_category VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI Documentation table
CREATE TABLE IF NOT EXISTS ai_documentation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ai_system_id UUID NOT NULL REFERENCES ai_systems(id) ON DELETE CASCADE,
    document_type VARCHAR(100),
    content JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Addons table
CREATE TABLE IF NOT EXISTS user_addons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    addon_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, addon_name)
);

-- Create Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(refresh_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_websites_user_id ON websites(user_id);
CREATE INDEX IF NOT EXISTS idx_websites_url ON websites(url);
CREATE INDEX IF NOT EXISTS idx_tracked_websites_user_id ON tracked_websites(user_id);
CREATE INDEX IF NOT EXISTS idx_tracked_websites_url ON tracked_websites(url);
CREATE INDEX IF NOT EXISTS idx_scan_history_user_id ON scan_history(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_history_website_id ON scan_history(website_id);
CREATE INDEX IF NOT EXISTS idx_scan_history_scan_date ON scan_history(scan_date);
CREATE INDEX IF NOT EXISTS idx_scan_history_scan_id ON scan_history(scan_id);
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_website_id ON scans(website_id);
CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_user_id ON fix_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_status ON fix_jobs(status);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_created_at ON fix_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_priority ON fix_jobs(priority DESC);
CREATE INDEX IF NOT EXISTS idx_legal_news_published_date ON legal_news(published_date);
CREATE INDEX IF NOT EXISTS idx_legal_news_category ON legal_news(category);
CREATE INDEX IF NOT EXISTS idx_cookie_stats_site ON cookie_compliance_stats(site_identifier, date);
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_ai_systems_user_id ON ai_systems(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_systems_risk_category ON ai_systems(risk_category);
CREATE INDEX IF NOT EXISTS idx_ai_systems_status ON ai_systems(status);

-- Insert initial data

-- Master Admin User (password: master123)
INSERT INTO users (email, hashed_password, full_name, company_name, subscription_tier, subscription_status, is_active, is_verified, is_superuser, monthly_scans_limit)
VALUES (
    'master@complyo.tech',
    '$2b$12$Dh2GX7LtvRqMV0k/t/Fbz.uHDH7DtpbA42MHwWFz071khUI9zw9oG',
    'Master Admin',
    'Complyo',
    'enterprise',
    'active',
    true,
    true,
    true,
    999999
) ON CONFLICT (email) DO NOTHING;

-- Compliance Risk Matrix data
INSERT INTO compliance_risk_matrix (category, issue_type, severity, fine_min, fine_max, min_risk_euro, max_risk_euro, legal_basis, description) VALUES
('barrierefreiheit', 'missing_alt_text', 'medium', 0, 10000, 0, 10000, 'BGG §12a', 'Fehlende Alt-Texte für Bilder'),
('barrierefreiheit', 'low_contrast', 'low', 0, 5000, 0, 5000, 'WCAG 2.1 AA', 'Unzureichender Kontrast'),
('impressum', 'missing', 'critical', 5000, 50000, 5000, 50000, 'TMG §5', 'Fehlendes Impressum'),
('impressum', 'incomplete', 'high', 1000, 20000, 1000, 20000, 'TMG §5', 'Unvollständiges Impressum'),
('datenschutz', 'missing', 'critical', 10000, 300000, 10000, 300000, 'DSGVO Art. 13', 'Fehlende Datenschutzerklärung'),
('cookies', 'no_consent', 'high', 5000, 100000, 5000, 100000, 'TTDSG §25', 'Fehlende Cookie-Einwilligung'),
('datenverarbeitung', 'unlawful', 'critical', 10000, 20000000, 10000, 20000000, 'DSGVO Art. 6', 'Rechtswidrige Datenverarbeitung')
ON CONFLICT DO NOTHING;

-- RSS Feed Sources
INSERT INTO rss_feed_sources (name, url, category, is_active) VALUES
('Datenschutz-Ticker', 'https://www.datenschutz-ticker.de/feed/', 'dsgvo', true),
('IT-Recht Kanzlei', 'https://www.it-recht-kanzlei.de/rss.xml', 'legal', true)
ON CONFLICT (url) DO NOTHING;

-- Create update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_websites_updated_at ON websites;
CREATE TRIGGER update_websites_updated_at BEFORE UPDATE ON websites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
