-- Migration: Create accessibility_fix_packages table
-- Speichert generierte Fix-Pakete für Websites
-- Datum: 2025-01-03

-- Tabelle für Fix-Pakete
CREATE TABLE IF NOT EXISTS accessibility_fix_packages (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    site_id VARCHAR(100) NOT NULL,
    site_url TEXT NOT NULL,
    fix_package JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    
    -- Unique constraint per user and site
    CONSTRAINT unique_user_site UNIQUE (user_id, site_id)
);

-- Index für schnelle Lookups
CREATE INDEX IF NOT EXISTS idx_fix_packages_user_id ON accessibility_fix_packages(user_id);
CREATE INDEX IF NOT EXISTS idx_fix_packages_site_id ON accessibility_fix_packages(site_id);
CREATE INDEX IF NOT EXISTS idx_fix_packages_created ON accessibility_fix_packages(created_at DESC);

-- GIN Index für JSONB Queries
CREATE INDEX IF NOT EXISTS idx_fix_packages_jsonb ON accessibility_fix_packages USING GIN (fix_package);

-- Kommentar
COMMENT ON TABLE accessibility_fix_packages IS 'Speichert generierte BFSG/WCAG Fix-Pakete für Websites';
COMMENT ON COLUMN accessibility_fix_packages.fix_package IS 'JSONB mit widget_fixes, code_patches, manual_guides und summary';

