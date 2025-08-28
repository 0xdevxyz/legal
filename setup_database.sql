-- Complyo Production Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    url VARCHAR(500) NOT NULL,
    domain VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    compliance_score INTEGER DEFAULT 0,
    last_scan TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    findings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scans table (für Verlauf)
CREATE TABLE IF NOT EXISTS scans (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    compliance_score INTEGER DEFAULT 0,
    findings JSONB DEFAULT '{}',
    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_type VARCHAR(50) DEFAULT 'full',
    ai_model VARCHAR(100)
);

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_name VARCHAR(255),
    api_key VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    plan VARCHAR(50) NOT NULL,
    stripe_subscription_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initial admin user
INSERT INTO users (email, password_hash, name, plan) 
VALUES (
    'admin@complyo.tech', 
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', -- Hash von "Admin123!"
    'Demo Admin', 
    'expert'
) ON CONFLICT (email) DO NOTHING;

-- Demo projects für Admin
INSERT INTO projects (user_id, url, domain, status, compliance_score, findings) 
VALUES 
(1, 'https://example.com', 'example.com', 'completed', 92, '{"impressum": {"status": "success", "score": 95}, "datenschutz": {"status": "success", "score": 90}}'),
(1, 'https://shop.beispiel.de', 'shop.beispiel.de', 'in_progress', 67, '{"impressum": {"status": "success", "score": 85}, "cookies": {"status": "error", "score": 30}}'),
(1, 'https://webapp.test.de', 'webapp.test.de', 'new', 45, '{"impressum": {"status": "warning", "score": 60}, "datenschutz": {"status": "error", "score": 20}}')
ON CONFLICT DO NOTHING;

-- Indexes für Performance
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_project_id ON scans(project_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO complyo_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO complyo_user;
