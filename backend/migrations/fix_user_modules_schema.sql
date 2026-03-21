-- Migration: Fix user_modules Schema
-- Problem: user_modules.user_id war UUID, aber users.id ist INTEGER
-- Lösung: Tabelle neu erstellen mit INTEGER user_id
-- Außerdem: modules Tabelle sicherstellen

-- modules Tabelle (falls noch nicht vorhanden)
CREATE TABLE IF NOT EXISTS modules (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10,2) NOT NULL DEFAULT 19.00,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO modules (id, name, description, price_monthly) VALUES
    ('cookie',        'Cookie & DSGVO',    'Cookie-Banner, Consent-Management, DSGVO-Prüfung', 19.00),
    ('accessibility', 'Barrierefreiheit',  'WCAG 2.1 AA Prüfung, Accessibility-Scanner, KI-Fixes', 19.00),
    ('legal_texts',   'Rechtliche Texte',  'Impressum, Datenschutzerklärung, AGB-Generator', 19.00),
    ('monitoring',    'Monitoring & Scan', 'Automatische Compliance-Scans, Alerts, Reports', 19.00)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    price_monthly = EXCLUDED.price_monthly;

-- Alte user_modules Tabelle entfernen falls mit UUID user_id angelegt
DROP TABLE IF EXISTS user_modules;

-- user_modules mit korrektem INTEGER user_id
CREATE TABLE IF NOT EXISTS user_modules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    module_id VARCHAR(50) NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired')),
    stripe_subscription_id VARCHAR(255),
    enabled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cancelled_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, module_id)
);

CREATE INDEX IF NOT EXISTS idx_user_modules_user   ON user_modules(user_id);
CREATE INDEX IF NOT EXISTS idx_user_modules_status ON user_modules(user_id, status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_user_modules_module ON user_modules(module_id);

-- Hilfsfunktion: Hat der User ein bestimmtes Modul?
CREATE OR REPLACE FUNCTION user_has_module(p_user_id INTEGER, p_module_id VARCHAR(50))
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_modules
        WHERE user_id = p_user_id
          AND module_id = p_module_id
          AND status = 'active'
          AND (expires_at IS NULL OR expires_at > NOW())
    );
END;
$$ LANGUAGE plpgsql;

-- Hilfsfunktion: Gibt alle aktiven Module eines Users zurück
CREATE OR REPLACE FUNCTION get_user_modules(p_user_id INTEGER)
RETURNS TABLE(module_id VARCHAR(50), module_name VARCHAR(100), enabled_at TIMESTAMP WITH TIME ZONE) AS $$
BEGIN
    RETURN QUERY
    SELECT um.module_id, m.name, um.enabled_at
    FROM user_modules um
    JOIN modules m ON um.module_id = m.id
    WHERE um.user_id = p_user_id
      AND um.status = 'active'
      AND (um.expires_at IS NULL OR um.expires_at > NOW());
END;
$$ LANGUAGE plpgsql;
