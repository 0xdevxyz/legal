-- ============================================================================
-- Fix: Domain-Lock Logik für Per-Domain-Subscriptions
-- Jede Domain startet mit 1 kostenlosen Fix, unabhängig vom Plan
-- ============================================================================

-- Aktualisierte check_fix_limit Funktion
CREATE OR REPLACE FUNCTION check_fix_limit(p_user_id INTEGER, p_domain_name VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    v_domain_lock RECORD;
BEGIN
    -- Prüfe, ob Domain-Lock existiert
    SELECT * INTO v_domain_lock
    FROM domain_locks
    WHERE user_id = p_user_id AND domain_name = p_domain_name;
    
    -- Domain noch nicht gelockt → Erstelle Lock mit 1 kostenlosem Fix
    IF NOT FOUND THEN
        INSERT INTO domain_locks (user_id, domain_name, fixes_used, fixes_limit, is_unlocked)
        VALUES (p_user_id, p_domain_name, 0, 1, FALSE);
        
        -- User kann ersten Fix machen
        RETURN TRUE;
    END IF;
    
    -- Domain ist unlocked (nach Zahlung) → Unbegrenzte Fixes
    IF v_domain_lock.is_unlocked THEN
        RETURN TRUE;
    END IF;
    
    -- Prüfe Limit (Standard: 1 kostenloser Fix pro Domain)
    IF v_domain_lock.fixes_used < v_domain_lock.fixes_limit THEN
        RETURN TRUE;
    END IF;
    
    -- Limit erreicht → Paywall
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Kommentar hinzufügen
COMMENT ON FUNCTION check_fix_limit IS 'Prüft Fix-Limit pro Domain. Jede Domain startet mit 1 kostenlosen Fix, danach Paywall (39€/Monat pro Domain).';

COMMIT;

