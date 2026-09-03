-- ============================================================================
-- Migration V2: Domain-Locks System für Per-Domain-Subscriptions
-- Erstellt domain_locks Tabelle und aktualisierte Funktionen
-- ============================================================================

-- Erstelle domain_locks Tabelle
CREATE TABLE IF NOT EXISTS domain_locks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain_name VARCHAR(500) NOT NULL,
    fixes_used INTEGER DEFAULT 0,
    fixes_limit INTEGER DEFAULT 1,
    is_unlocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unlocked_at TIMESTAMP,
    UNIQUE(user_id, domain_name)
);

-- Indices für Performance
CREATE INDEX IF NOT EXISTS idx_domain_locks_user_id ON domain_locks(user_id);
CREATE INDEX IF NOT EXISTS idx_domain_locks_domain_name ON domain_locks(domain_name);
CREATE INDEX IF NOT EXISTS idx_domain_locks_user_domain ON domain_locks(user_id, domain_name);

-- Aktualisiere user_limits Tabelle
ALTER TABLE user_limits 
ADD COLUMN IF NOT EXISTS fixes_used INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS fixes_limit INTEGER DEFAULT 1;

-- Index für user_limits
CREATE INDEX IF NOT EXISTS idx_user_limits_fixes ON user_limits(user_id, fixes_used, fixes_limit);

-- Update existierende user_limits für Free/Pro Plans
UPDATE user_limits 
SET 
    fixes_limit = CASE 
        WHEN plan_type = 'free' THEN 1
        WHEN plan_type = 'pro' THEN 999999
        WHEN plan_type = 'ai' THEN 999999
        WHEN plan_type = 'expert' THEN 999999
        ELSE 1
    END,
    fixes_used = 0
WHERE fixes_limit IS NULL OR fixes_limit = 0;

-- ============================================================================
-- Funktion: Check Domain Lock
-- Prüft, ob eine Domain bereits gelockt ist
-- ============================================================================
CREATE OR REPLACE FUNCTION check_domain_lock(p_user_id INTEGER, p_domain_name VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    v_lock_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM domain_locks 
        WHERE user_id = p_user_id 
        AND domain_name = p_domain_name
    ) INTO v_lock_exists;
    
    RETURN v_lock_exists;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Funktion: Check Fix Limit
-- Prüft, ob User noch Fixes verfügbar hat (für spezifische Domain)
-- ============================================================================
CREATE OR REPLACE FUNCTION check_fix_limit(p_user_id INTEGER, p_domain_name VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    v_plan_type VARCHAR;
    v_plan_fixes_limit INTEGER;
    v_domain_lock RECORD;
BEGIN
    -- Hole User Plan Info
    SELECT plan_type, fixes_limit 
    INTO v_plan_type, v_plan_fixes_limit
    FROM user_limits 
    WHERE user_id = p_user_id;
    
    -- Wenn kein Eintrag existiert, erstelle einen (Free Plan)
    IF NOT FOUND THEN
        INSERT INTO user_limits (user_id, plan_type, fixes_limit, fixes_used, websites_max, exports_max)
        VALUES (p_user_id, 'free', 1, 0, 1, 5);
        v_plan_type := 'free';
        v_plan_fixes_limit := 1;
    END IF;
    
    -- Prüfe, ob Domain-Lock existiert
    SELECT * INTO v_domain_lock
    FROM domain_locks
    WHERE user_id = p_user_id AND domain_name = p_domain_name;
    
    -- Domain noch nicht gelockt → Erstelle Lock mit Plan-Limits
    IF NOT FOUND THEN
        INSERT INTO domain_locks (user_id, domain_name, fixes_used, fixes_limit, is_unlocked)
        VALUES (p_user_id, p_domain_name, 0, v_plan_fixes_limit, FALSE);
        
        -- User kann ersten Fix machen
        RETURN TRUE;
    END IF;
    
    -- Domain ist unlocked (nach Zahlung) → Unbegrenzte Fixes
    IF v_domain_lock.is_unlocked THEN
        RETURN TRUE;
    END IF;
    
    -- Prüfe Limit
    IF v_domain_lock.fixes_used < v_domain_lock.fixes_limit THEN
        RETURN TRUE;
    END IF;
    
    -- Limit erreicht
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Funktion: Increment Fix Counter
-- Erhöht den Fix-Counter für eine Domain
-- ============================================================================
CREATE OR REPLACE FUNCTION increment_fix_counter(p_user_id INTEGER, p_domain_name VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    -- Erstelle Domain-Lock falls nicht existiert
    INSERT INTO domain_locks (user_id, domain_name, fixes_used, fixes_limit)
    VALUES (p_user_id, p_domain_name, 0, 1)
    ON CONFLICT (user_id, domain_name) DO NOTHING;
    
    -- Inkrementiere Counter
    UPDATE domain_locks
    SET fixes_used = fixes_used + 1
    WHERE user_id = p_user_id AND domain_name = p_domain_name;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Funktion: Unlock Domain (nach Zahlung)
-- Setzt is_unlocked = true für unbegrenzte Fixes
-- ============================================================================
CREATE OR REPLACE FUNCTION unlock_domain(p_user_id INTEGER, p_domain_name VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE domain_locks
    SET 
        is_unlocked = TRUE,
        unlocked_at = CURRENT_TIMESTAMP,
        fixes_limit = 999999
    WHERE user_id = p_user_id AND domain_name = p_domain_name;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Funktion: Get User Domain Locks
-- Gibt alle Domain-Locks eines Users zurück
-- ============================================================================
CREATE OR REPLACE FUNCTION get_user_domain_locks(p_user_id INTEGER)
RETURNS TABLE(
    domain_name VARCHAR,
    fixes_used INTEGER,
    fixes_limit INTEGER,
    is_unlocked BOOLEAN,
    created_at TIMESTAMP,
    unlocked_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dl.domain_name,
        dl.fixes_used,
        dl.fixes_limit,
        dl.is_unlocked,
        dl.created_at,
        dl.unlocked_at
    FROM domain_locks dl
    WHERE dl.user_id = p_user_id
    ORDER BY dl.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Cleanup: Entferne alte locked_domain Spalte (falls vorhanden)
-- ============================================================================
ALTER TABLE user_limits DROP COLUMN IF EXISTS locked_domain;

COMMIT;

