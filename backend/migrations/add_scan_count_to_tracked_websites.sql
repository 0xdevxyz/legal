-- Add scan_count column to tracked_websites if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tracked_websites' 
        AND column_name = 'scan_count'
    ) THEN
        ALTER TABLE tracked_websites ADD COLUMN scan_count INTEGER DEFAULT 0;
        COMMENT ON COLUMN tracked_websites.scan_count IS 'Anzahl der durchgeführten Scans für diese Website';
    END IF;
    
    -- Also add is_primary if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tracked_websites' 
        AND column_name = 'is_primary'
    ) THEN
        ALTER TABLE tracked_websites ADD COLUMN is_primary BOOLEAN DEFAULT FALSE;
        COMMENT ON COLUMN tracked_websites.is_primary IS 'Ist dies die primäre Website des Benutzers?';
    END IF;
END $$;
