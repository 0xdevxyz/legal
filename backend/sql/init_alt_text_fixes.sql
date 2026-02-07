-- Alt-Text Fixes Table
-- Speichert KI-generierte Alt-Texte für Bilder ohne Alt-Attribut

-- Erstelle Tabelle nur wenn sie nicht existiert
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'accessibility_alt_text_fixes') THEN
        CREATE TABLE accessibility_alt_text_fixes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            image_url TEXT NOT NULL,
            image_selector TEXT,
            original_alt TEXT,
            generated_alt TEXT NOT NULL,
            confidence DECIMAL(3,2) DEFAULT 0.9,
            source VARCHAR(50) DEFAULT 'openai_vision',
            status VARCHAR(20) DEFAULT 'pending',
            is_approved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(site_id, image_url)
        );
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_alt_fixes_site ON accessibility_alt_text_fixes(site_id);
CREATE INDEX IF NOT EXISTS idx_alt_fixes_user ON accessibility_alt_text_fixes(user_id);
CREATE INDEX IF NOT EXISTS idx_alt_fixes_status ON accessibility_alt_text_fixes(status);
CREATE INDEX IF NOT EXISTS idx_alt_fixes_approved ON accessibility_alt_text_fixes(site_id, is_approved);
