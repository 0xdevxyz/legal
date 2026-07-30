-- Migration: Neue RSS-Feed-Quellen für Legal News
-- Datum: 2026-02-07
-- Beschreibung: Fügt BfDI, DSK, BMAS und weitere wichtige Quellen hinzu

-- Neue hochprioritäre Quellen (Behörden & offizielle Stellen)
INSERT INTO rss_feed_sources (name, url, category, priority, keywords, fetch_frequency_hours) VALUES
-- BfDI - Bundesbeauftragter für den Datenschutz
('BfDI Pressemitteilungen', 'https://www.bfdi.bund.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/RSSNewsfeed_Presse.xml', 'Datenschutz-Behörde', 'critical', ARRAY['DSGVO', 'Datenschutz', 'BfDI', 'Bußgeld', 'Aufsichtsbehörde', 'Beschwerden'], 4),
('BfDI Meldungen', 'https://www.bfdi.bund.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/RSSNewsfeed_Meldungen.xml', 'Datenschutz-Behörde', 'critical', ARRAY['DSGVO', 'Datenschutz', 'BfDI', 'Orientierungshilfe', 'Beschluss'], 4),

-- BMAS - Barrierefreiheit (BFSG)
('BMAS Pressemitteilungen', 'https://www.bmas.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/RSSNewsfeed_Presse.xml', 'Barrierefreiheit', 'high', ARRAY['Barrierefreiheit', 'BFSG', 'Inklusion', 'Accessibility', 'WCAG'], 6),

-- IT-Recht Kanzlei - Praxisnahe Urteile
('IT-Recht Kanzlei', 'https://www.it-recht-kanzlei.de/rss/news.xml', 'Internetrecht', 'high', ARRAY['DSGVO', 'Cookie', 'Impressum', 'Abmahnung', 'AGB', 'Widerruf', 'Datenschutz'], 4),

-- Datenschutz-Notizen (Dr. Datenschutz)
('Dr. Datenschutz', 'https://www.dr-datenschutz.de/feed/', 'Datenschutz-Praxis', 'high', ARRAY['DSGVO', 'Datenschutz', 'Praxistipp', 'Cookie', 'Consent', 'Auftragsdatenverarbeitung'], 6),

-- Haufe Datenschutz
('Haufe Datenschutz', 'https://www.haufe.de/thema/datenschutz.rss', 'Datenschutz-Fachmedien', 'medium', ARRAY['DSGVO', 'Datenschutz', 'Compliance', 'Datenschutzbeauftragter', 'TTDSG'], 8),

-- Heise Online - Recht (Tech-Datenschutz)
('Heise Recht', 'https://www.heise.de/thema/Recht.rss', 'Tech-Recht', 'medium', ARRAY['Datenschutz', 'DSGVO', 'Cookie', 'Tracking', 'AI Act', 'Digital Services Act'], 8),

-- Golem - IT-Recht
('Golem IT-Recht', 'https://rss.golem.de/rss.php?tp=pol&feed=RSS2.0', 'Tech-Recht', 'low', ARRAY['Datenschutz', 'DSGVO', 'Cookie', 'Tracking', 'AI', 'Überwachung'], 12)

ON CONFLICT (url) DO UPDATE SET
    priority = EXCLUDED.priority,
    keywords = EXCLUDED.keywords,
    fetch_frequency_hours = EXCLUDED.fetch_frequency_hours,
    updated_at = CURRENT_TIMESTAMP;

-- Tabelle für E-Mail-Benachrichtigungen bei Gesetzesänderungen
CREATE TABLE IF NOT EXISTS legal_change_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    legal_change_id VARCHAR(100),
    legal_news_id INTEGER REFERENCES legal_news(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL, -- 'email', 'in_app', 'push'
    severity VARCHAR(50) NOT NULL, -- 'critical', 'high', 'medium', 'low', 'info'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'sent', 'confirmed', 'dismissed'
    sent_at TIMESTAMP,
    confirmed_at TIMESTAMP,
    confirmation_token VARCHAR(255) UNIQUE,
    action_required BOOLEAN DEFAULT FALSE,
    action_deadline TIMESTAMP,
    action_taken_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Präferenzen für Legal News Benachrichtigungen
CREATE TABLE IF NOT EXISTS user_legal_notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT FALSE,
    min_severity VARCHAR(50) DEFAULT 'medium', -- Nur ab dieser Severity benachrichtigen
    notify_areas TEXT[] DEFAULT ARRAY['dsgvo', 'ttdsg', 'cookie', 'impressum', 'barrierefreiheit', 'ai_act'],
    instant_for_critical BOOLEAN DEFAULT TRUE, -- Sofort bei kritischen Änderungen
    digest_frequency VARCHAR(50) DEFAULT 'daily', -- 'instant', 'daily', 'weekly'
    digest_time TIME DEFAULT '09:00:00',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_legal_change_notifications_user ON legal_change_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_legal_change_notifications_status ON legal_change_notifications(status);
CREATE INDEX IF NOT EXISTS idx_legal_change_notifications_severity ON legal_change_notifications(severity);

-- Trigger für updated_at
CREATE TRIGGER update_legal_change_notifications_updated_at
    BEFORE UPDATE ON legal_change_notifications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_legal_notification_settings_updated_at
    BEFORE UPDATE ON user_legal_notification_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
