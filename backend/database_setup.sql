-- Create Complyo Database Schema
-- Run this in PostgreSQL as superuser

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS complyo_db;

-- Connect to database
\c complyo_db;

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
    
    -- Subscription
    subscription_tier subscription_tier DEFAULT 'free',
    subscription_status subscription_status DEFAULT 'trial',
    subscription_end_date TIMESTAMP WITH TIME ZONE,
    trial_end_date TIMESTAMP WITH TIME ZONE,
    
    -- Account Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Limits & Usage
    monthly_scans_limit INTEGER DEFAULT 10,
    monthly_scans_used INTEGER DEFAULT 0,
    total_scans INTEGER DEFAULT 0,
    api_key VARCHAR(255) UNIQUE,
    
    -- Security
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked_until TIMESTAMP WITH TIME ZONE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255)
);

-- Websites table
CREATE TABLE IF NOT EXISTS websites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    name VARCHAR(255),
    
    -- Monitoring Settings
    scan_frequency scan_frequency DEFAULT 'weekly',
    auto_fix_enabled BOOLEAN DEFAULT FALSE,
    notification_enabled BOOLEAN DEFAULT TRUE,
    
    -- Current Status
    last_scan_date TIMESTAMP WITH TIME ZONE,
    last_score FLOAT,
    status website_status DEFAULT 'active',
    
    -- Metadata
    favicon_url VARCHAR(500),
    screenshot_url VARCHAR(500),
    technology_stack JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scans table
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    website_id UUID NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    
    -- Scan Results
    overall_score FLOAT,
    legal_score FLOAT,
    cookie_score FLOAT,
    accessibility_score FLOAT,
    privacy_score FLOAT,
    
    -- Detailed Results
    results JSONB,
    issues_count INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    
    -- Metadata
    scan_duration_ms INTEGER,
    scan_type scan_type DEFAULT 'manual',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Team Members table
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role team_role DEFAULT 'member',
    permissions JSONB,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, user_id)
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_api_key ON users(api_key);
CREATE INDEX idx_websites_user_id ON websites(user_id);
CREATE INDEX idx_websites_url ON websites(url);
CREATE INDEX idx_scans_user_id ON scans(user_id);
CREATE INDEX idx_scans_website_id ON scans(website_id);
CREATE INDEX idx_scans_created_at ON scans(created_at DESC);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
CREATE INDEX idx_team_members_team_id ON team_members(team_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_websites_updated_at BEFORE UPDATE ON websites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO complyo_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO complyo_user;

-- Create first admin user (change password immediately!)
INSERT INTO users (
    email, 
    hashed_password, 
    full_name, 
    is_superuser, 
    is_verified,
    api_key
) VALUES (
    'admin@complyo.tech',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY3L2oFrlE7JTIu', -- Password: Admin123!
    'Admin User',
    TRUE,
    TRUE,
    'admin_' || gen_random_uuid()
);

