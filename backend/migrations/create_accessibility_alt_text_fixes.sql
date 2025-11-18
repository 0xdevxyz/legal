-- ============================================================================
-- Complyo Accessibility: Alt-Text-Fixes Tabelle
-- ============================================================================
-- Datum: 2025-11-15
-- Beschreibung: Speichert AI-generierte Alt-Texte für Widget-Runtime-Injection
--               und HTML-Patch-Generation
-- ============================================================================

-- 1. Haupttabelle: AI-generierte Alt-Texte
CREATE TABLE IF NOT EXISTS accessibility_alt_text_fixes (
    id SERIAL PRIMARY KEY,
    
    -- Identifikation
    site_id VARCHAR(100) NOT NULL,
    scan_id VARCHAR(255), -- Keine FK wegen fehlender UNIQUE constraint in scan_history
    user_id UUID, -- UUID statt INTEGER (kompatibel mit bestehenden Tabellen)
    
    -- Bild-Identifikation (mehrere Möglichkeiten für Matching)
    page_url TEXT NOT NULL,
    image_src TEXT NOT NULL, -- Relativer oder absoluter Pfad
    image_filename VARCHAR(500),
    image_url_hash VARCHAR(64), -- SHA256 Hash für eindeutiges Matching
    
    -- AI-Generierter Alt-Text
    suggested_alt TEXT NOT NULL,
    confidence DECIMAL(4,3) CHECK (confidence >= 0 AND confidence <= 1), -- 0.000 - 1.000
    
    -- Context (für AI-Generierung)
    page_title TEXT,
    surrounding_text TEXT, -- Text um das Bild herum
    element_html TEXT, -- Vollständiges <img> Tag
    image_context JSONB, -- Zusätzlicher Kontext als JSON
    
    -- Status-Management
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'deployed')),
    approved_at TIMESTAMP,
    approved_by UUID, -- UUID, keine FK (optional)
    rejected_reason TEXT,
    
    -- Deployment-Tracking
    deployed_via VARCHAR(20), -- 'widget', 'patch', 'expert_service'
    deployed_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Eindeutigkeit: Ein Alt-Text pro Bild pro Site
    UNIQUE(site_id, image_src)
);

-- 2. Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_alt_fixes_site_id ON accessibility_alt_text_fixes(site_id);
CREATE INDEX IF NOT EXISTS idx_alt_fixes_scan_id ON accessibility_alt_text_fixes(scan_id);
CREATE INDEX IF NOT EXISTS idx_alt_fixes_user_id ON accessibility_alt_text_fixes(user_id);
CREATE INDEX IF NOT EXISTS idx_alt_fixes_status ON accessibility_alt_text_fixes(status);
CREATE INDEX IF NOT EXISTS idx_alt_fixes_page_url ON accessibility_alt_text_fixes(page_url);
CREATE INDEX IF NOT EXISTS idx_alt_fixes_created_at ON accessibility_alt_text_fixes(created_at DESC);

-- 3. Trigger: Auto-Update updated_at
CREATE OR REPLACE FUNCTION update_alt_fixes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_alt_fixes_timestamp ON accessibility_alt_text_fixes;
CREATE TRIGGER trigger_update_alt_fixes_timestamp
    BEFORE UPDATE ON accessibility_alt_text_fixes
    FOR EACH ROW
    EXECUTE FUNCTION update_alt_fixes_updated_at();

-- 4. Funktion: Hole Alt-Texte für Widget
CREATE OR REPLACE FUNCTION get_widget_alt_text_fixes(p_site_id VARCHAR(100))
RETURNS TABLE (
    image_src TEXT,
    image_filename VARCHAR(500),
    suggested_alt TEXT,
    page_url TEXT,
    confidence DECIMAL(4,3)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        atf.image_src,
        atf.image_filename,
        atf.suggested_alt,
        atf.page_url,
        atf.confidence
    FROM accessibility_alt_text_fixes atf
    WHERE atf.site_id = p_site_id
      AND atf.status = 'approved'
    ORDER BY atf.confidence DESC, atf.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- 5. Funktion: Statistiken für Dashboard
CREATE OR REPLACE FUNCTION get_accessibility_stats(p_site_id VARCHAR(100))
RETURNS TABLE (
    total_fixes INTEGER,
    approved_fixes INTEGER,
    pending_fixes INTEGER,
    avg_confidence DECIMAL(4,3),
    pages_with_fixes INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_fixes,
        COUNT(*) FILTER (WHERE status = 'approved')::INTEGER as approved_fixes,
        COUNT(*) FILTER (WHERE status = 'pending')::INTEGER as pending_fixes,
        AVG(confidence)::DECIMAL(4,3) as avg_confidence,
        COUNT(DISTINCT page_url)::INTEGER as pages_with_fixes
    FROM accessibility_alt_text_fixes
    WHERE site_id = p_site_id;
END;
$$ LANGUAGE plpgsql;

-- 6. View: Alt-Text-Fixes Übersicht für Dashboard
CREATE OR REPLACE VIEW accessibility_fixes_overview AS
SELECT 
    atf.id,
    atf.site_id,
    atf.user_id,
    u.email as user_email,
    atf.page_url,
    atf.image_src,
    atf.image_filename,
    atf.suggested_alt,
    atf.confidence,
    atf.status,
    atf.deployed_via,
    atf.created_at,
    atf.deployed_at,
    sh.compliance_score as scan_score
FROM accessibility_alt_text_fixes atf
LEFT JOIN users u ON atf.user_id = u.id
LEFT JOIN scan_history sh ON atf.scan_id = sh.scan_id
ORDER BY atf.created_at DESC;

-- 7. Kommentare für Dokumentation
COMMENT ON TABLE accessibility_alt_text_fixes IS 'AI-generierte Alt-Texte für Barrierefreiheits-Widget und HTML-Patches';
COMMENT ON COLUMN accessibility_alt_text_fixes.site_id IS 'Eindeutige Site-ID (z.B. scan-91778ad450e1)';
COMMENT ON COLUMN accessibility_alt_text_fixes.suggested_alt IS 'AI-generierter Alt-Text für das Bild';
COMMENT ON COLUMN accessibility_alt_text_fixes.confidence IS 'AI-Konfidenz 0.000-1.000 (höher = besser)';
COMMENT ON COLUMN accessibility_alt_text_fixes.status IS 'pending=wartend, approved=genehmigt, rejected=abgelehnt, deployed=eingesetzt';
COMMENT ON COLUMN accessibility_alt_text_fixes.deployed_via IS 'widget=runtime injection, patch=HTML download, expert_service=manuell';

-- 8. Sample-Daten für Testing (optional, kann auskommentiert werden)
-- INSERT INTO accessibility_alt_text_fixes (
--     site_id, user_id, page_url, image_src, image_filename,
--     suggested_alt, confidence, status
-- ) VALUES 
-- ('scan-test123', 1, 'https://example.com/', '/images/logo.png', 'logo.png',
--  'Firmenlogo Example GmbH mit blauem Schriftzug', 0.95, 'approved'),
-- ('scan-test123', 1, 'https://example.com/about', '/images/team.jpg', 'team.jpg',
--  'Team-Foto der Mitarbeiter vor dem Bürogebäude', 0.89, 'approved');

-- ============================================================================
-- Migration abgeschlossen
-- ============================================================================

