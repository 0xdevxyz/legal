-- ============================================================================
-- Master User erstellen: master@complyo.tech
-- Passwort: master123
-- ============================================================================

-- Passwort-Hash für "master123" (bcrypt)
-- Hash: $2b$12$duKTkPb0Qz7/8lFSlkW9auMsAlsyW6.1jH25SAv5/dbarblcs52iW

-- Prüfe ob User existiert und erstelle/aktualisiere ihn
DO $$
DECLARE
    user_exists BOOLEAN;
    user_id_var INTEGER;
    password_hash TEXT := '$2b$12$duKTkPb0Qz7/8lFSlkW9auMsAlsyW6.1jH25SAv5/dbarblcs52iW';
BEGIN
    -- Prüfe ob User existiert
    SELECT EXISTS(SELECT 1 FROM users WHERE email = 'master@complyo.tech') INTO user_exists;
    
    IF user_exists THEN
        -- User existiert - setze Passwort zurück und aktiviere
        UPDATE users 
        SET hashed_password = password_hash,
            is_active = TRUE, 
            is_verified = TRUE
        WHERE email = 'master@complyo.tech';
        
        SELECT id INTO user_id_var FROM users WHERE email = 'master@complyo.tech';
        
        RAISE NOTICE 'User master@complyo.tech wurde aktualisiert (ID: %)', user_id_var;
    ELSE
        -- User erstellen
        INSERT INTO users (email, hashed_password, full_name, is_active, is_verified)
        VALUES (
            'master@complyo.tech',
            password_hash,
            'Master User',
            TRUE,
            TRUE
        )
        RETURNING id INTO user_id_var;
        
        -- User Limits initialisieren (Expert Plan - unbegrenzt)
        INSERT INTO user_limits (user_id, plan_type, websites_max, exports_max, exports_reset_date)
        VALUES (user_id_var, 'expert', -1, -1, CURRENT_DATE + INTERVAL '1 month')
        ON CONFLICT (user_id) DO UPDATE SET
            plan_type = 'expert',
            websites_max = -1,
            exports_max = -1;
        
        RAISE NOTICE 'User master@complyo.tech wurde erstellt (ID: %)', user_id_var;
    END IF;
END $$;

-- Zeige User-Info
SELECT 
    id,
    email,
    full_name,
    is_active,
    is_verified,
    created_at
FROM users 
WHERE email = 'master@complyo.tech';
