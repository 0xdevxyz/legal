-- ============================================================================
-- Complyo Accessibility: Document-Level Fixes (Fix-Manifest)
-- ============================================================================
-- Datum: 2026-06-26
-- Beschreibung: Persistiert auto-sichere, dokumentweite Barrierefreiheits-Fixes
--               (html-lang, skip-link, landmarks, page-title, kontrast/fokus-css),
--               die NICHT an ein einzelnes Bild gebunden sind. Quelle ist die
--               deterministische Ableitung aus den Scan-Issues (Stufe 1 = auto-sicher).
--               Gemeinsam mit accessibility_alt_text_fixes bildet diese Tabelle das
--               vereinheitlichte "Fix-Manifest", das ALLE Auslieferungskanäle
--               (WordPress / HTML-CLI / SPA-Runtime) konsumieren.
-- ============================================================================

CREATE TABLE IF NOT EXISTS accessibility_document_fixes (
    id SERIAL PRIMARY KEY,

    -- Identifikation (stabile, domain-abgeleitete site_id — gleich wie die Channels abfragen)
    site_id VARCHAR(100) NOT NULL,
    scan_id VARCHAR(255),
    user_id UUID,
    page_url TEXT,

    -- Fix-Beschreibung
    -- fix_type ∈ ('html-lang','skip-link','landmark-main','landmark-nav',
    --             'document-title','css-rule')
    fix_type VARCHAR(40) NOT NULL,
    -- Strukturierte Nutzdaten je fix_type, z.B.
    --   html-lang:      {"value":"de"}
    --   skip-link:      {"target":"#main","label":"Zum Inhalt springen"}
    --   document-title: {"value":"Startseite – Beispiel GmbH"}
    --   css-rule:       {"selector":":focus","declarations":"outline:2px solid #1a73e8"}
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- WCAG-Referenz + Herkunft + Vertrauen
    wcag_criterion VARCHAR(20),       -- z.B. '3.1.1', '2.4.1'
    confidence DECIMAL(4,3) CHECK (confidence >= 0 AND confidence <= 1),
    source VARCHAR(20) DEFAULT 'scan', -- 'scan' (deterministisch) | 'ai' | 'manual'

    -- Status-Management (deterministische Stufe-1-Fixes können auto-approved sein)
    status VARCHAR(20) DEFAULT 'approved'
        CHECK (status IN ('pending', 'approved', 'rejected', 'deployed')),
    approved_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Ein Fix pro Typ pro Site (dokumentweite Fixes sind site-global, nicht je Bild)
    UNIQUE(site_id, fix_type)
);

CREATE INDEX IF NOT EXISTS idx_doc_fixes_site_id ON accessibility_document_fixes(site_id);
CREATE INDEX IF NOT EXISTS idx_doc_fixes_status  ON accessibility_document_fixes(status);
CREATE INDEX IF NOT EXISTS idx_doc_fixes_scan_id ON accessibility_document_fixes(scan_id);

CREATE OR REPLACE FUNCTION update_doc_fixes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_doc_fixes_timestamp ON accessibility_document_fixes;
CREATE TRIGGER trigger_update_doc_fixes_timestamp
    BEFORE UPDATE ON accessibility_document_fixes
    FOR EACH ROW
    EXECUTE FUNCTION update_doc_fixes_updated_at();

COMMENT ON TABLE accessibility_document_fixes IS 'Dokumentweite, auto-sichere A11y-Fixes (lang/skip-link/landmarks/css) – Teil des Fix-Manifests';
COMMENT ON COLUMN accessibility_document_fixes.fix_type IS 'html-lang | skip-link | landmark-main | landmark-nav | document-title | css-rule';
COMMENT ON COLUMN accessibility_document_fixes.payload IS 'Strukturierte Nutzdaten je fix_type (JSON)';
COMMENT ON COLUMN accessibility_document_fixes.source IS 'scan=deterministisch abgeleitet, ai=KI, manual=manuell';

-- ============================================================================
-- Migration abgeschlossen
-- ============================================================================
