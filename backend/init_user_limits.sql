-- ============================================================================
-- User Limits & Fix Tracking System
-- Verwaltet Plan-Limitierungen und Geld-zurück-Garantie
-- ============================================================================

-- User Limits Tabelle
CREATE TABLE IF NOT EXISTS user_limits (
    user_id INTEGER PRIMARY KEY,
    plan_type VARCHAR(20) NOT NULL DEFAULT 'ai',
    websites_count INTEGER DEFAULT 0,
    websites_max INTEGER DEFAULT 1, -- AI: 1, Expert: unlimited
    exports_this_month INTEGER DEFAULT 0,
    exports_max INTEGER DEFAULT 10,
    exports_reset_date DATE,
    fix_started BOOLEAN DEFAULT FALSE,
    money_back_eligible BOOLEAN DEFAULT TRUE,
    subscription_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscription Tracking mit Refund-Logik
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    plan_type VARCHAR(20) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fix_first_used_at TIMESTAMP,
    refund_eligible BOOLEAN DEFAULT TRUE,
    refund_deadline TIMESTAMP,
    refund_requested_at TIMESTAMP,
    refund_processed_at TIMESTAMP,
    refund_stripe_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fix-Tracking: Welche Fixes wurden generiert
CREATE TABLE IF NOT EXISTS generated_fixes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    issue_id VARCHAR(100) NOT NULL,
    issue_category VARCHAR(100) NOT NULL,
    fix_type VARCHAR(50) NOT NULL, -- 'code_snippet', 'full_document'
    plan_type VARCHAR(20) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exported BOOLEAN DEFAULT FALSE,
    exported_at TIMESTAMP,
    export_format VARCHAR(20), -- 'html', 'pdf', 'txt'
    content_hash VARCHAR(64),
    FOREIGN KEY (user_id) REFERENCES user_limits(user_id)
);

-- Website-Tracking: Welche Websites wurden analysiert
CREATE TABLE IF NOT EXISTS tracked_websites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    url VARCHAR(500) NOT NULL,
    last_score INTEGER DEFAULT 0,
    last_scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_count INTEGER DEFAULT 1,
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, url),
    FOREIGN KEY (user_id) REFERENCES user_limits(user_id)
);

-- Export-Tracking für monatliches Limit
CREATE TABLE IF NOT EXISTS export_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    fix_id INTEGER NOT NULL,
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    export_format VARCHAR(20) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user_limits(user_id),
    FOREIGN KEY (fix_id) REFERENCES generated_fixes(id)
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_user_limits_plan ON user_limits(plan_type);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_fixes_user ON generated_fixes(user_id);
CREATE INDEX IF NOT EXISTS idx_fixes_category ON generated_fixes(issue_category);
CREATE INDEX IF NOT EXISTS idx_tracked_websites_user ON tracked_websites(user_id);
CREATE INDEX IF NOT EXISTS idx_export_history_user ON export_history(user_id);
CREATE INDEX IF NOT EXISTS idx_export_history_month ON export_history(exported_at);

-- Trigger: Setze refund_deadline bei neuer Subscription
CREATE OR REPLACE FUNCTION set_refund_deadline()
RETURNS TRIGGER AS $$
BEGIN
    NEW.refund_deadline = NEW.started_at + INTERVAL '14 days';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_set_refund_deadline ON subscriptions;
CREATE TRIGGER trigger_set_refund_deadline
    BEFORE INSERT ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION set_refund_deadline();

-- Trigger: Update updated_at
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_user_limits_timestamp ON user_limits;
CREATE TRIGGER trigger_user_limits_timestamp
    BEFORE UPDATE ON user_limits
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trigger_subscriptions_timestamp ON subscriptions;
CREATE TRIGGER trigger_subscriptions_timestamp
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Funktion: Check Website Limit
CREATE OR REPLACE FUNCTION check_website_limit(p_user_id INTEGER, p_new_url VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    v_count INTEGER;
    v_max INTEGER;
    v_exists BOOLEAN;
BEGIN
    -- Check ob Website bereits existiert
    SELECT EXISTS(
        SELECT 1 FROM tracked_websites 
        WHERE user_id = p_user_id AND url = p_new_url
    ) INTO v_exists;
    
    IF v_exists THEN
        RETURN TRUE; -- Website bereits tracked, kein Limit-Problem
    END IF;
    
    -- Check Limit
    SELECT websites_count, websites_max 
    INTO v_count, v_max
    FROM user_limits 
    WHERE user_id = p_user_id;
    
    RETURN v_count < v_max;
END;
$$ LANGUAGE plpgsql;

-- Funktion: Check Export Limit
CREATE OR REPLACE FUNCTION check_export_limit(p_user_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    v_exports INTEGER;
    v_max INTEGER;
BEGIN
    SELECT exports_this_month, exports_max 
    INTO v_exports, v_max
    FROM user_limits 
    WHERE user_id = p_user_id;
    
    RETURN v_exports < v_max;
END;
$$ LANGUAGE plpgsql;

-- Funktion: Reset monatliche Export-Counts (für Cronjob)
CREATE OR REPLACE FUNCTION reset_monthly_exports()
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE user_limits
    SET 
        exports_this_month = 0,
        exports_reset_date = CURRENT_DATE + INTERVAL '1 month'
    WHERE exports_reset_date <= CURRENT_DATE;
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Demo-Daten für Testing (User ID 1)
INSERT INTO user_limits (user_id, plan_type, websites_max, exports_max, exports_reset_date)
VALUES (1, 'ai', 1, 10, CURRENT_DATE + INTERVAL '1 month')
ON CONFLICT (user_id) DO UPDATE SET
    plan_type = EXCLUDED.plan_type,
    websites_max = EXCLUDED.websites_max,
    exports_max = EXCLUDED.exports_max;

-- Demo-Subscription für User 1
INSERT INTO subscriptions (user_id, plan_type, stripe_subscription_id)
VALUES (1, 'ai', 'sub_demo_12345')
ON CONFLICT DO NOTHING;

