-- ============================================================================
-- User Limits & Fix Tracking System (UUID Version)
-- Erstellt user_limits und zugehörige Tabellen mit UUID statt INTEGER
-- ============================================================================

BEGIN;

-- User Limits Tabelle mit UUID
CREATE TABLE IF NOT EXISTS user_limits (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(20) NOT NULL DEFAULT 'free',
    
    -- Fix Limits
    fixes_limit INTEGER DEFAULT 1,
    fixes_used INTEGER DEFAULT 0,
    fix_started BOOLEAN DEFAULT FALSE,
    
    -- Website Limits
    websites_count INTEGER DEFAULT 0,
    websites_max INTEGER DEFAULT 1,
    
    -- Export Limits
    exports_this_month INTEGER DEFAULT 0,
    exports_max INTEGER DEFAULT 5,
    exports_used INTEGER DEFAULT 0,
    exports_reset_date DATE DEFAULT (CURRENT_DATE + INTERVAL '1 month'),
    
    -- Locked Domain (Free Plan)
    locked_domain VARCHAR(255),
    
    -- Refund & Subscription
    money_back_eligible BOOLEAN DEFAULT TRUE,
    subscription_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscription Tracking
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
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

-- Fix-Tracking
CREATE TABLE IF NOT EXISTS generated_fixes (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    issue_id VARCHAR(100) NOT NULL,
    issue_category VARCHAR(100) NOT NULL,
    fix_type VARCHAR(50) NOT NULL,
    plan_type VARCHAR(20) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exported BOOLEAN DEFAULT FALSE,
    exported_at TIMESTAMP,
    export_format VARCHAR(20),
    content_hash VARCHAR(64)
);

-- Website-Tracking
CREATE TABLE IF NOT EXISTS tracked_websites (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    last_score INTEGER DEFAULT 0,
    last_scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_count INTEGER DEFAULT 1,
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, url)
);

-- Export-Tracking
CREATE TABLE IF NOT EXISTS export_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fix_id INTEGER NOT NULL REFERENCES generated_fixes(id) ON DELETE CASCADE,
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    export_format VARCHAR(20) NOT NULL
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_user_limits_plan ON user_limits(plan_type);
CREATE INDEX IF NOT EXISTS idx_user_limits_fixes ON user_limits(user_id, fixes_used, fixes_limit);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_fixes_user ON generated_fixes(user_id);
CREATE INDEX IF NOT EXISTS idx_fixes_category ON generated_fixes(issue_category);
CREATE INDEX IF NOT EXISTS idx_tracked_websites_user ON tracked_websites(user_id);
CREATE INDEX IF NOT EXISTS idx_export_history_user ON export_history(user_id);
CREATE INDEX IF NOT EXISTS idx_export_history_month ON export_history(exported_at);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Funktion: Check Fix Limit
CREATE OR REPLACE FUNCTION check_fix_limit(p_user_id UUID)
RETURNS TABLE(allowed BOOLEAN, fixes_used INTEGER, fixes_limit INTEGER, plan_type VARCHAR) AS $$
DECLARE
    v_used INTEGER;
    v_limit INTEGER;
    v_plan VARCHAR(20);
BEGIN
    SELECT ul.fixes_used, ul.fixes_limit, ul.plan_type
    INTO v_used, v_limit, v_plan
    FROM user_limits ul
    WHERE ul.user_id = p_user_id;
    
    -- Wenn kein Eintrag existiert, erstelle einen (Free Plan)
    IF NOT FOUND THEN
        INSERT INTO user_limits (user_id, plan_type, fixes_limit, fixes_used, websites_max, exports_max)
        VALUES (p_user_id, 'free', 1, 0, 1, 5);
        v_used := 0;
        v_limit := 1;
        v_plan := 'free';
    END IF;
    
    -- NULL-Check
    IF v_used IS NULL THEN v_used := 0; END IF;
    IF v_limit IS NULL THEN v_limit := 1; END IF;
    
    RETURN QUERY SELECT (v_used < v_limit), v_used, v_limit, v_plan;
END;
$$ LANGUAGE plpgsql;

-- Funktion: Increment Fix Counter
CREATE OR REPLACE FUNCTION increment_fix_counter(p_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Erstelle Eintrag falls nicht vorhanden
    INSERT INTO user_limits (user_id, plan_type, fixes_used)
    VALUES (p_user_id, 'free', 1)
    ON CONFLICT (user_id) DO UPDATE
    SET fixes_used = COALESCE(user_limits.fixes_used, 0) + 1,
        fix_started = TRUE,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Funktion: Check Website Limit
CREATE OR REPLACE FUNCTION check_website_limit(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_count INTEGER;
    v_max INTEGER;
BEGIN
    SELECT websites_count, websites_max 
    INTO v_count, v_max
    FROM user_limits 
    WHERE user_id = p_user_id;
    
    IF NOT FOUND THEN RETURN TRUE; END IF;
    
    RETURN COALESCE(v_count, 0) < COALESCE(v_max, 1);
END;
$$ LANGUAGE plpgsql;

-- Funktion: Check Export Limit
CREATE OR REPLACE FUNCTION check_export_limit(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_exports INTEGER;
    v_max INTEGER;
BEGIN
    SELECT exports_this_month, exports_max 
    INTO v_exports, v_max
    FROM user_limits 
    WHERE user_id = p_user_id;
    
    IF NOT FOUND THEN RETURN TRUE; END IF;
    
    RETURN COALESCE(v_exports, 0) < COALESCE(v_max, 5);
END;
$$ LANGUAGE plpgsql;

-- Funktion: Reset Export Counter (monatlich)
CREATE OR REPLACE FUNCTION reset_export_counters()
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE user_limits
    SET 
        exports_this_month = 0,
        exports_reset_date = CURRENT_DATE + INTERVAL '1 month',
        updated_at = CURRENT_TIMESTAMP
    WHERE exports_reset_date <= CURRENT_DATE;
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update updated_at on user_limits
CREATE OR REPLACE FUNCTION update_user_limits_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_user_limits_updated_at ON user_limits;
CREATE TRIGGER trigger_user_limits_updated_at
    BEFORE UPDATE ON user_limits
    FOR EACH ROW
    EXECUTE FUNCTION update_user_limits_timestamp();

-- ============================================================================
-- Initialisiere user_limits für existierende User
-- ============================================================================

INSERT INTO user_limits (user_id, plan_type, fixes_limit, fixes_used, websites_max, exports_max)
SELECT 
    id, 
    'free', 
    1, 
    0, 
    1, 
    5
FROM users
WHERE id NOT IN (SELECT user_id FROM user_limits)
ON CONFLICT (user_id) DO NOTHING;

COMMIT;

-- Info
SELECT 
    'user_limits Migration completed' as status,
    COUNT(*) as users_with_limits 
FROM user_limits;

