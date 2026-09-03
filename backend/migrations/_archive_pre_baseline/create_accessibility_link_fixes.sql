-- ============================================================================
-- Complyo Accessibility: Link-Zweck-Fixes (WCAG 2.4.4) — Teil des Fix-Manifests
-- ============================================================================
-- Datum: 2026-06-26
-- Beschreibung: Persistiert Vorschläge für aussagekräftige Link-Namen (aria-label)
--               zu "nichtssagenden" Links ("hier", "mehr", "weiterlesen", …).
--               Stufe 2 (Human-in-the-Loop): Vorschlag wird 'pending' gespeichert
--               und erst nach Review ('approved') über das Fix-Manifest ausgeliefert.
--               Channels matchen den konkreten Link über link_key (Hash aus href|text)
--               und setzen aria-label nur, wenn noch kein zugänglicher Name existiert.
-- ============================================================================

CREATE TABLE IF NOT EXISTS accessibility_link_fixes (
    id SERIAL PRIMARY KEY,

    -- Identifikation (stabile, domain-abgeleitete site_id — wie die Channels abfragen)
    site_id VARCHAR(100) NOT NULL,
    scan_id VARCHAR(255),
    user_id UUID,
    page_url TEXT,

    -- Link-Identifikation
    link_href TEXT NOT NULL,
    link_text TEXT NOT NULL,          -- sichtbarer (nichtssagender) Text, z.B. "mehr"
    link_key VARCHAR(64) NOT NULL,    -- SHA256(href|normalisierter_text) für Channel-Matching

    -- Vorschlag
    suggested_label TEXT NOT NULL,    -- aussagekräftiger aria-label-Vorschlag
    confidence DECIMAL(4,3) CHECK (confidence >= 0 AND confidence <= 1),
    surrounding_text TEXT,            -- Kontext, aus dem der Vorschlag abgeleitet wurde
    source VARCHAR(20) DEFAULT 'scan',-- 'scan' (heuristisch) | 'ai' | 'manual'

    -- Status-Management (Stufe 2: default 'pending' → erst nach Review live)
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'deployed')),
    approved_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Ein Vorschlag pro Link (href+text) pro Site
    UNIQUE(site_id, link_key)
);

CREATE INDEX IF NOT EXISTS idx_link_fixes_site_id ON accessibility_link_fixes(site_id);
CREATE INDEX IF NOT EXISTS idx_link_fixes_status  ON accessibility_link_fixes(status);
CREATE INDEX IF NOT EXISTS idx_link_fixes_scan_id ON accessibility_link_fixes(scan_id);

CREATE OR REPLACE FUNCTION update_link_fixes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_link_fixes_timestamp ON accessibility_link_fixes;
CREATE TRIGGER trigger_update_link_fixes_timestamp
    BEFORE UPDATE ON accessibility_link_fixes
    FOR EACH ROW
    EXECUTE FUNCTION update_link_fixes_updated_at();

COMMENT ON TABLE accessibility_link_fixes IS 'WCAG 2.4.4 — aria-label-Vorschläge für nichtssagende Links (HITL, Teil des Fix-Manifests)';
COMMENT ON COLUMN accessibility_link_fixes.link_key IS 'SHA256(href|normalisierter_text) für eindeutiges Channel-Matching';
COMMENT ON COLUMN accessibility_link_fixes.status IS 'pending=Review nötig, approved=ausliefern, rejected, deployed';

-- ============================================================================
-- Migration abgeschlossen
-- ============================================================================
