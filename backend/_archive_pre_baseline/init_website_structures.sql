-- Website Structures Table für Crawler-Daten Caching
-- Verhindert unnötiges Re-Crawling und spart API-Kosten

CREATE TABLE IF NOT EXISTS website_structures (
    id SERIAL PRIMARY KEY,
    website_id INTEGER REFERENCES tracked_websites(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    structure_data JSONB NOT NULL,  -- Vollständige Crawler-Daten
    cms_type VARCHAR(50),
    cms_version VARCHAR(50),
    cms_confidence FLOAT DEFAULT 0.0,
    has_legal_pages JSONB,  -- {impressum: true, datenschutz: false, ...}
    tracking_services JSONB,  -- {google_analytics: true, facebook_pixel: false, ...}
    accessibility_score INTEGER,  -- 0-100
    technology_stack JSONB,  -- {react: true, jquery: false, ...}
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_stale BOOLEAN DEFAULT FALSE,  -- True wenn >7 Tage alt
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(website_id)
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_website_structures_website_id ON website_structures(website_id);
CREATE INDEX IF NOT EXISTS idx_website_structures_url ON website_structures(url);
CREATE INDEX IF NOT EXISTS idx_website_structures_stale ON website_structures(is_stale);
CREATE INDEX IF NOT EXISTS idx_website_structures_cms ON website_structures(cms_type);
CREATE INDEX IF NOT EXISTS idx_website_structures_crawled_at ON website_structures(crawled_at DESC);

-- JSONB-Indizes für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_website_structures_legal_pages ON website_structures USING GIN(has_legal_pages);
CREATE INDEX IF NOT EXISTS idx_website_structures_tracking ON website_structures USING GIN(tracking_services);
CREATE INDEX IF NOT EXISTS idx_website_structures_tech_stack ON website_structures USING GIN(technology_stack);

-- Trigger: Auto-Update updated_at
CREATE OR REPLACE FUNCTION update_website_structures_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_website_structures_timestamp ON website_structures;
CREATE TRIGGER trigger_website_structures_timestamp
    BEFORE UPDATE ON website_structures
    FOR EACH ROW
    EXECUTE FUNCTION update_website_structures_timestamp();

-- Funktion: Markiere alte Strukturen als stale (>7 Tage)
CREATE OR REPLACE FUNCTION mark_stale_structures()
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE website_structures
    SET is_stale = TRUE
    WHERE crawled_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
      AND is_stale = FALSE;
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- View: Aktuelle (nicht-stale) Strukturen
CREATE OR REPLACE VIEW fresh_website_structures AS
SELECT 
    id,
    website_id,
    url,
    structure_data,
    cms_type,
    cms_version,
    has_legal_pages,
    tracking_services,
    accessibility_score,
    technology_stack,
    crawled_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - crawled_at)) / 3600 AS age_hours
FROM website_structures
WHERE is_stale = FALSE
  AND crawled_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY crawled_at DESC;

