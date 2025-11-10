-- eRecht24 Projects Table
-- Speichert eRecht24 Projekt-Credentials für jede getrackte Website

CREATE TABLE IF NOT EXISTS erecht24_projects (
    id SERIAL PRIMARY KEY,
    website_id INTEGER REFERENCES tracked_websites(id) ON DELETE CASCADE,
    erecht24_project_id VARCHAR(255) UNIQUE NOT NULL,
    erecht24_api_key VARCHAR(500),
    erecht24_secret VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    last_synced TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'suspended', 'error'
    
    CONSTRAINT unique_website_erecht24 UNIQUE(website_id)
);

CREATE INDEX IF NOT EXISTS idx_erecht24_projects_website ON erecht24_projects(website_id);
CREATE INDEX IF NOT EXISTS idx_erecht24_projects_project_id ON erecht24_projects(erecht24_project_id);

-- Kommentar
COMMENT ON TABLE erecht24_projects IS 'Speichert eRecht24 API-Credentials für automatisch erstellte Projekte';
COMMENT ON COLUMN erecht24_projects.website_id IS 'Referenz zu tracked_websites';
COMMENT ON COLUMN erecht24_projects.erecht24_project_id IS 'Eindeutige Projekt-ID von eRecht24';
COMMENT ON COLUMN erecht24_projects.last_synced IS 'Zeitpunkt der letzten Synchronisation';

