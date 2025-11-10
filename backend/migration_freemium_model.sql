-- ============================================================================
-- Migration: Freemium Model mit Stripe Paywall
-- Fügt fixes_used und fixes_limit zur user_limits Tabelle hinzu
-- ============================================================================

-- Füge neue Spalten für Fix-Tracking und Domain-Lock hinzu
ALTER TABLE user_limits 
ADD COLUMN IF NOT EXISTS fixes_used INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS fixes_limit INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS locked_domain VARCHAR(500) DEFAULT NULL;

-- Update plan_type defaults für Freemium
-- free: 1 Fix, pro: unbegrenzt
UPDATE user_limits 
SET fixes_limit = CASE 
    WHEN plan_type = 'free' THEN 1
    WHEN plan_type = 'pro' THEN 999999
    WHEN plan_type = 'ai' THEN 999999
    WHEN plan_type = 'expert' THEN 999999
    ELSE 1
END
WHERE fixes_limit = 0 OR fixes_limit IS NULL;

-- Füge Stripe Customer ID zur subscriptions Tabelle hinzu (falls nicht vorhanden)
ALTER TABLE subscriptions 
ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_user_limits_fixes ON user_limits(fixes_used, fixes_limit);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer ON subscriptions(stripe_customer_id);

-- Funktion: Check Fix Limit
CREATE OR REPLACE FUNCTION check_fix_limit(p_user_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    v_used INTEGER;
    v_limit INTEGER;
BEGIN
    SELECT fixes_used, fixes_limit 
    INTO v_used, v_limit
    FROM user_limits 
    WHERE user_id = p_user_id;
    
    -- NULL-Check
    IF v_used IS NULL THEN v_used := 0; END IF;
    IF v_limit IS NULL THEN v_limit := 1; END IF;
    
    RETURN v_used < v_limit;
END;
$$ LANGUAGE plpgsql;

-- Funktion: Check Domain Lock (ob User bereits eine andere Domain hat)
CREATE OR REPLACE FUNCTION check_domain_lock(p_user_id INTEGER, p_url VARCHAR)
RETURNS TABLE(is_locked BOOLEAN, locked_url VARCHAR, needs_new_subscription BOOLEAN) AS $$
DECLARE
    v_locked_domain VARCHAR;
    v_plan_type VARCHAR;
BEGIN
    SELECT locked_domain, plan_type 
    INTO v_locked_domain, v_plan_type
    FROM user_limits 
    WHERE user_id = p_user_id;
    
    -- Keine Domain gelockt → OK
    IF v_locked_domain IS NULL THEN
        RETURN QUERY SELECT FALSE, NULL::VARCHAR, FALSE;
        RETURN;
    END IF;
    
    -- Gleiche Domain → OK
    IF v_locked_domain = p_url THEN
        RETURN QUERY SELECT TRUE, v_locked_domain, FALSE;
        RETURN;
    END IF;
    
    -- Andere Domain → Neue Subscription erforderlich (nur bei free/pro)
    IF v_plan_type IN ('free', 'pro') THEN
        RETURN QUERY SELECT TRUE, v_locked_domain, TRUE;
        RETURN;
    END IF;
    
    -- Expert Plan → Mehrere Domains erlaubt
    RETURN QUERY SELECT FALSE, NULL::VARCHAR, FALSE;
END;
$$ LANGUAGE plpgsql;

-- Funktion: Increment Fix Counter
CREATE OR REPLACE FUNCTION increment_fix_counter(p_user_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE user_limits
    SET fixes_used = COALESCE(fixes_used, 0) + 1,
        fix_started = TRUE
    WHERE user_id = p_user_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Funktion: Reset Fix Counter (bei Upgrade)
CREATE OR REPLACE FUNCTION reset_fix_counter(p_user_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE user_limits
    SET fixes_used = 0,
        fixes_limit = 999999
    WHERE user_id = p_user_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Update existierende Demo-Daten
UPDATE user_limits
SET fixes_used = 0, fixes_limit = 1
WHERE user_id = 1 AND plan_type NOT IN ('pro', 'expert');

COMMIT;

