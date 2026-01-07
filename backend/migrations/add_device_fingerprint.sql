-- ============================================================================
-- Migration: Add Device Fingerprint to Cookie Consent Logs
-- ============================================================================
-- Adds device_fingerprint column as privacy-friendly alternative to IP hash
-- 
-- The fingerprint is generated client-side from non-identifying characteristics:
-- - Browser language
-- - Screen resolution category
-- - Timezone offset
-- - Hardware concurrency category
-- - Platform type
-- - Touch capability
--
-- This is NOT a tracking fingerprint - it's for consent documentation only.
-- ============================================================================

-- Add device_fingerprint column
ALTER TABLE cookie_consent_logs 
ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(64);

-- Add comment
COMMENT ON COLUMN cookie_consent_logs.device_fingerprint IS 
'Privacy-friendly device fingerprint as alternative to IP hash. Generated from non-identifying browser characteristics.';

-- Create index for lookups
CREATE INDEX IF NOT EXISTS idx_consent_device_fingerprint 
ON cookie_consent_logs(device_fingerprint) 
WHERE device_fingerprint IS NOT NULL;

-- ============================================================================
-- Also add storage columns to cookie_services for Phase 2
-- ============================================================================

-- Add local_storage_keys column
ALTER TABLE cookie_services 
ADD COLUMN IF NOT EXISTS local_storage_keys JSONB DEFAULT '[]'::jsonb;

-- Add session_storage_keys column
ALTER TABLE cookie_services 
ADD COLUMN IF NOT EXISTS session_storage_keys JSONB DEFAULT '[]'::jsonb;

-- Add comments
COMMENT ON COLUMN cookie_services.local_storage_keys IS 
'Known Local Storage keys used by this service';

COMMENT ON COLUMN cookie_services.session_storage_keys IS 
'Known Session Storage keys used by this service';

-- ============================================================================
-- Migration complete
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration abgeschlossen!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Neue Spalten:';
    RAISE NOTICE '  ✓ cookie_consent_logs.device_fingerprint';
    RAISE NOTICE '  ✓ cookie_services.local_storage_keys';
    RAISE NOTICE '  ✓ cookie_services.session_storage_keys';
    RAISE NOTICE '========================================';
END $$;

