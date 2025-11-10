-- Legal Updates Table
-- Speichert Gesetzesänderungen und rechtliche Updates (z.B. von eRecht24 Webhooks)

CREATE TABLE IF NOT EXISTS legal_updates (
    id SERIAL PRIMARY KEY,
    update_type VARCHAR(100) NOT NULL,  -- 'dsgvo', 'tmg', 'cookie_law', 'bfsg', etc.
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity VARCHAR(50) DEFAULT 'info',  -- 'info', 'warning', 'critical'
    action_required BOOLEAN DEFAULT false,
    source VARCHAR(100) DEFAULT 'erecht24',  -- 'erecht24', 'manual', 'scraped'
    published_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    effective_date DATE,  -- Datum, ab dem das Gesetz gilt
    url TEXT  -- Link zur offiziellen Quelle
);

-- User Legal Notifications Table
-- Speichert welcher User welche Updates gesehen/bearbeitet hat

CREATE TABLE IF NOT EXISTS user_legal_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    legal_update_id INTEGER REFERENCES legal_updates(id) ON DELETE CASCADE,
    website_id INTEGER REFERENCES tracked_websites(id) ON DELETE CASCADE,
    read BOOLEAN DEFAULT false,
    action_taken BOOLEAN DEFAULT false,  -- Hat User darauf reagiert? (z.B. neu gescannt)
    created_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP,
    action_at TIMESTAMP,
    
    CONSTRAINT unique_user_update UNIQUE(user_id, legal_update_id, website_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_legal_updates_type ON legal_updates(update_type);
CREATE INDEX IF NOT EXISTS idx_legal_updates_severity ON legal_updates(severity);
CREATE INDEX IF NOT EXISTS idx_legal_updates_published ON legal_updates(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_legal_updates_action_required ON legal_updates(action_required);

CREATE INDEX IF NOT EXISTS idx_user_notifications_user ON user_legal_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_user_notifications_update ON user_legal_notifications(legal_update_id);
CREATE INDEX IF NOT EXISTS idx_user_notifications_read ON user_legal_notifications(read);

-- Kommentare
COMMENT ON TABLE legal_updates IS 'Gesetzesänderungen und rechtliche Updates von eRecht24 oder manuell';
COMMENT ON COLUMN legal_updates.severity IS 'Schweregrad: info (informativ), warning (wichtig), critical (sofortiges Handeln erforderlich)';
COMMENT ON COLUMN legal_updates.action_required IS 'Ob User aktiv werden muss (z.B. Website neu scannen)';
COMMENT ON TABLE user_legal_notifications IS 'Tracking welcher User welche Updates gesehen/bearbeitet hat';


-- Beispiel-Daten für Demo
INSERT INTO legal_updates (update_type, title, description, severity, action_required, published_at, effective_date, url) VALUES
('dsgvo', 'DSGVO Anpassung 2025: Neue Cookie-Consent Anforderungen', 
 'Ab 01.01.2026 gelten verschärfte Anforderungen für Cookie-Consent-Banner. Opt-Out Lösungen sind nicht mehr ausreichend.', 
 'warning', true, NOW() - INTERVAL '2 days', '2026-01-01', 'https://example.com/dsgvo-update'),

('bfsg', 'Barrierefreiheitsstärkungsgesetz tritt in Kraft', 
 'Ab 28. Juni 2025 müssen digitale Produkte und Dienstleistungen barrierefrei nach WCAG 2.1 Level AA sein.', 
 'critical', true, NOW() - INTERVAL '7 days', '2025-06-28', 'https://example.com/bfsg'),

('tmg', 'TMG § 5 Ergänzung: Impressumspflicht für Social Media', 
 'Unternehmen müssen nun auch in Social-Media-Profilen ein vollständiges Impressum hinterlegen.', 
 'info', false, NOW() - INTERVAL '14 days', '2025-03-01', 'https://example.com/tmg-update')
ON CONFLICT DO NOTHING;
