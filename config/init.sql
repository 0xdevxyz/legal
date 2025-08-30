-- Complyo Enterprise Database Initialization
-- =============================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    role VARCHAR(100) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    subscription_status VARCHAR(50) DEFAULT 'free',
    stripe_customer_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create compliance_projects table
CREATE TABLE IF NOT EXISTS compliance_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    website_url VARCHAR(500) NOT NULL,
    compliance_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    compliance_score DECIMAL(5,2),
    results JSONB,
    recommendations TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create compliance_scans table
CREATE TABLE IF NOT EXISTS compliance_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES compliance_projects(id) ON DELETE CASCADE,
    scan_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    results JSONB,
    score DECIMAL(5,2),
    issues_found INTEGER DEFAULT 0,
    scan_duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON compliance_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON compliance_projects(status);
CREATE INDEX IF NOT EXISTS idx_scans_project_id ON compliance_scans(project_id);
CREATE INDEX IF NOT EXISTS idx_scans_created_at ON compliance_scans(created_at);

-- Insert demo admin user (password: admin123)
INSERT INTO users (email, hashed_password, full_name, role, is_admin) 
VALUES (
    'admin@complyo.enterprise', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiKJVyy6k5s6',
    'Complyo Administrator',
    'admin',
    true
) ON CONFLICT (email) DO NOTHING;

-- Insert demo compliance project
INSERT INTO compliance_projects (
    user_id, 
    name, 
    website_url, 
    compliance_type, 
    status, 
    compliance_score,
    results,
    recommendations
) VALUES (
    (SELECT id FROM users WHERE email = 'admin@complyo.enterprise' LIMIT 1),
    'Demo Website Analysis',
    'https://example.com',
    'gdpr',
    'completed',
    94.2,
    '{"gdpr": {"score": 94.2, "status": "compliant", "issues": []}}',
    'Website shows excellent GDPR compliance. Minor improvements suggested for cookie consent granularity.'
) ON CONFLICT DO NOTHING;