-- Legal News Table für Complyo
-- Speichert RSS-Feed-News zu Datenschutz, DSGVO, TTDSG

CREATE TABLE IF NOT EXISTS legal_news (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    content TEXT,
    url VARCHAR(1000),
    source VARCHAR(200) NOT NULL,
    source_feed VARCHAR(200) NOT NULL,
    published_date TIMESTAMP NOT NULL,
    fetched_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    news_type VARCHAR(50) DEFAULT 'info', -- 'critical', 'update', 'tip', 'info'
    severity VARCHAR(50) DEFAULT 'info', -- 'critical', 'warning', 'info'
    keywords TEXT[], -- Array von Keywords für Filterung
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_legal_news_published ON legal_news(published_date DESC);
CREATE INDEX IF NOT EXISTS idx_legal_news_source ON legal_news(source);
CREATE INDEX IF NOT EXISTS idx_legal_news_active ON legal_news(is_active);
CREATE INDEX IF NOT EXISTS idx_legal_news_featured ON legal_news(is_featured);

-- Index für Keyword-Suche
CREATE INDEX IF NOT EXISTS idx_legal_news_keywords ON legal_news USING GIN(keywords);

-- RSS Feed Sources Table
CREATE TABLE IF NOT EXISTS rss_feed_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    url VARCHAR(1000) NOT NULL UNIQUE,
    category VARCHAR(100),
    priority VARCHAR(50) DEFAULT 'medium', -- 'high', 'medium', 'low'
    keywords TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    last_fetch TIMESTAMP,
    fetch_frequency_hours INTEGER DEFAULT 6,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initiale RSS-Feed-Quellen
INSERT INTO rss_feed_sources (name, url, category, priority, keywords) VALUES
('BMJ Pressemitteilungen', 'https://www.bmj.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/RSSNewsfeed_Presse.xml', 'Gesetzgebung', 'high', ARRAY['DSGVO', 'TTDSG', 'Datenschutz', 'Cookie', 'Telemedien', 'Impressum']),
('Legal Tribune Online - Datenschutzrecht', 'https://www.lto.de/recht/kategorie/datenschutzrecht/feed/', 'Urteile', 'high', ARRAY['DSGVO', 'Datenschutz', 'Compliance', 'Bußgeld', 'TTDSG']),
('Rechtslupe', 'https://www.rechtslupe.de/feed', 'Allgemein', 'medium', ARRAY['Datenschutz', 'DSGVO', 'Impressum', 'TTDSG', 'Barrierefreiheit']),
('eRecht24', 'https://www.e-recht24.de/news.rss', 'Internetrecht', 'high', ARRAY['Datenschutz', 'DSGVO', 'Impressum', 'Cookie-Consent', 'TTDSG', 'Website'])
ON CONFLICT (url) DO NOTHING;

-- Trigger für updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_legal_news_updated_at
    BEFORE UPDATE ON legal_news
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rss_feed_sources_updated_at
    BEFORE UPDATE ON rss_feed_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View für aktuelle News (letzte 30 Tage)
CREATE OR REPLACE VIEW recent_legal_news AS
SELECT 
    id,
    title,
    summary,
    url,
    source,
    published_date,
    news_type,
    severity,
    keywords,
    is_featured
FROM legal_news
WHERE is_active = TRUE
  AND published_date >= CURRENT_TIMESTAMP - INTERVAL '30 days'
ORDER BY is_featured DESC, published_date DESC
LIMIT 50;

