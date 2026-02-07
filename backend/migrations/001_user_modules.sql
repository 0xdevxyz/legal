-- Migration: User Modules System
-- Ermöglicht die Buchung einzelner Module (Cookie, Barrierefreiheit, etc.)

-- Modul-Tabelle: Definiert alle verfügbaren Module
CREATE TABLE IF NOT EXISTS modules (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10,2) NOT NULL DEFAULT 19.00,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Standard-Module einfügen
INSERT INTO modules (id, name, description, price_monthly) VALUES
    ('cookie', 'Cookie & DSGVO', 'Cookie-Banner, Consent-Management, DSGVO-Prüfung', 19.00),
    ('accessibility', 'Barrierefreiheit', 'WCAG 2.1 AA Prüfung, Accessibility-Scanner, KI-Fixes', 19.00),
    ('legal_texts', 'Rechtliche Texte', 'Impressum, Datenschutzerklärung, AGB-Generator', 19.00),
    ('monitoring', 'Monitoring & Scan', 'Automatische Compliance-Scans, Alerts, Reports', 19.00)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    price_monthly = EXCLUDED.price_monthly;

-- User-Module Junction-Tabelle
CREATE TABLE IF NOT EXISTS user_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
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

CREATE INDEX IF NOT EXISTS idx_user_modules_user ON user_modules(user_id);
CREATE INDEX IF NOT EXISTS idx_user_modules_status ON user_modules(user_id, status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_user_modules_module ON user_modules(module_id);

-- Pläne aktualisieren mit korrekten Preisen (Frontend = Backend)
DELETE FROM subscription_plans WHERE id IN ('price_ai_monthly', 'price_expert_monthly', 'price_single_monthly', 'price_complete_monthly');

-- Einzelmodul-Plan (19€/Monat pro Säule)
INSERT INTO subscription_plans (
    id, stripe_product_id, name, description, 
    price_monthly, price_yearly, features, is_active
) VALUES (
    'price_single_monthly',
    'prod_complyo_single',
    'Einzelmodul',
    '1 Säule nach Wahl: Cookie, Barrierefreiheit, Rechtliche Texte oder Monitoring',
    19.00,
    190.00,
    '["1 Modul nach Wahl", "KI-generierte Lösungen", "Automatischer Scanner", "E-Mail Support"]'::json,
    true
) ON CONFLICT (id) DO UPDATE SET
    price_monthly = 19.00,
    price_yearly = 190.00,
    name = 'Einzelmodul',
    description = EXCLUDED.description;

-- Komplett-Paket (49€/Monat - alle 4 Säulen)
INSERT INTO subscription_plans (
    id, stripe_product_id, name, description, 
    price_monthly, price_yearly, features, is_active
) VALUES (
    'price_complete_monthly',
    'prod_complyo_complete',
    'Komplett-Paket',
    'Alle 4 Säulen: Cookie, Barrierefreiheit, Rechtliche Texte und Monitoring',
    49.00,
    490.00,
    '["Alle 4 Säulen inklusive", "Unbegrenzte Analysen", "KI-generierte Code-Fixes", "eRecht24 Integration", "Priority Support", "API-Zugang"]'::json,
    true
) ON CONFLICT (id) DO UPDATE SET
    price_monthly = 49.00,
    price_yearly = 490.00,
    name = 'Komplett-Paket',
    description = EXCLUDED.description;

-- Expertenservice (2.990€ einmalig + 39€/Monat)
INSERT INTO subscription_plans (
    id, stripe_product_id, name, description, 
    price_monthly, price_yearly, features, is_active
) VALUES (
    'price_expert_monthly',
    'prod_complyo_expert',
    'Expertenservice',
    'Vollständige Umsetzung durch Experten + laufende Betreuung',
    39.00,
    390.00,
    '["Vollständige Umsetzung", "WCAG 2.1 AA Zertifizierung", "Persönlicher Ansprechpartner", "Laufende Updates", "SLA & Garantie", "Priority Support"]'::json,
    true
) ON CONFLICT (id) DO UPDATE SET
    price_monthly = 39.00,
    price_yearly = 390.00,
    name = 'Expertenservice',
    description = EXCLUDED.description;

-- Setup-Gebühr für Expert Plan aktualisieren (2.990€)
INSERT INTO plan_setup_fees (plan_id, setup_fee, setup_fee_description)
VALUES (
    'price_expert_monthly',
    2990.00,
    'Einmalige Setup-Gebühr für vollständige Umsetzung durch Experten'
)
ON CONFLICT (plan_id) DO UPDATE SET
    setup_fee = 2990.00,
    setup_fee_description = EXCLUDED.setup_fee_description;

-- Hilfsfunktion: Prüft ob User ein bestimmtes Modul hat
CREATE OR REPLACE FUNCTION user_has_module(p_user_id UUID, p_module_id VARCHAR(50))
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
CREATE OR REPLACE FUNCTION get_user_modules(p_user_id UUID)
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
