-- Migration: Create accessibility_fix_packages table
-- Speichert generierte BFSG/WCAG Fix-Pakete für Websites
-- Datum: 2025-01-03 (korrigiert 2026-06-11)
--
-- HINWEIS: user_id ist VARCHAR, nicht UUID/INTEGER. Der Code (accessibility_fix_routes.py)
-- übergibt die User-ID als String aus den JWT-Claims (z.B. "5"). Frühere Versionen dieser
-- Migration definierten user_id als UUID REFERENCES users(id) — das passt weder zur
-- Integer-users.id dieser Instanz noch zum String, den der Endpoint übergibt, und führte
-- dazu, dass die Tabelle nie angelegt/nutzbar war.

CREATE TABLE IF NOT EXISTS accessibility_fix_packages (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    site_id VARCHAR(100) NOT NULL,
    site_url TEXT NOT NULL,
    fix_package JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,

    -- Ein Fix-Paket pro User und Site (vom Endpoint via ON CONFLICT genutzt)
    CONSTRAINT accessibility_fix_packages_user_site_key UNIQUE (user_id, site_id)
);

-- Indizes für schnelle Lookups
CREATE INDEX IF NOT EXISTS idx_fix_packages_user_id ON accessibility_fix_packages(user_id);
CREATE INDEX IF NOT EXISTS idx_fix_packages_site_id ON accessibility_fix_packages(site_id);
CREATE INDEX IF NOT EXISTS idx_fix_packages_created ON accessibility_fix_packages(created_at DESC);

-- GIN Index für JSONB Queries
CREATE INDEX IF NOT EXISTS idx_fix_packages_jsonb ON accessibility_fix_packages USING GIN (fix_package);

-- Kommentare
COMMENT ON TABLE accessibility_fix_packages IS 'Speichert generierte BFSG/WCAG Fix-Pakete für Websites';
COMMENT ON COLUMN accessibility_fix_packages.user_id IS 'User-ID als String aus JWT-Claims (kein FK auf users.id)';
COMMENT ON COLUMN accessibility_fix_packages.fix_package IS 'JSONB mit widget_fixes, code_patches, manual_guides und summary';
