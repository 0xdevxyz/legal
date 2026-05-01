-- Deep Cookie Scanner Tables (adapted for Complyo schema: user_id is INTEGER)

CREATE TABLE IF NOT EXISTS deep_cookie_scans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    website_id VARCHAR(255),
    url TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    cookies JSONB DEFAULT '[]',
    requests JSONB DEFAULT '[]',
    storage JSONB DEFAULT '{}',
    categorized JSONB DEFAULT '{}',
    total_cookies INTEGER DEFAULT 0,
    unique_services INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    services_detected JSONB DEFAULT '[]',
    scan_duration_seconds INTEGER,
    error_message TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deep_scans_user ON deep_cookie_scans(user_id);
CREATE INDEX IF NOT EXISTS idx_deep_scans_website ON deep_cookie_scans(website_id);
CREATE INDEX IF NOT EXISTS idx_deep_scans_status ON deep_cookie_scans(status);
CREATE INDEX IF NOT EXISTS idx_deep_scans_created ON deep_cookie_scans(created_at);

CREATE TABLE IF NOT EXISTS deep_scan_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    current_month VARCHAR(7) NOT NULL,
    scans_used INTEGER DEFAULT 0,
    scans_limit INTEGER DEFAULT 5,
    last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usage_user_month ON deep_scan_usage(user_id, current_month);

CREATE TABLE IF NOT EXISTS deep_scan_history (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER NOT NULL REFERENCES deep_cookie_scans(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_history_scan ON deep_scan_history(scan_id);
