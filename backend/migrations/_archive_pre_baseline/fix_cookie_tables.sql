-- Migration: Fix Cookie Compliance Tables - Add Missing Fields
-- Date: 2025-11-21
-- Issue: Backend code references fields that don't exist in DB

-- 1. Add missing fields to cookie_banner_configs
ALTER TABLE cookie_banner_configs
    ADD COLUMN IF NOT EXISTS scan_completed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_scan_url TEXT,
    ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(255),
    ADD COLUMN IF NOT EXISTS revision_id INTEGER DEFAULT 1,
    ADD COLUMN IF NOT EXISTS config_hash VARCHAR(64);

-- 2. Add missing fields to cookie_services for extended provider info
ALTER TABLE cookie_services
    ADD COLUMN IF NOT EXISTS privacy_url TEXT,
    ADD COLUMN IF NOT EXISTS provider_address TEXT,
    ADD COLUMN IF NOT EXISTS provider_privacy_url TEXT,
    ADD COLUMN IF NOT EXISTS provider_cookie_url TEXT,
    ADD COLUMN IF NOT EXISTS provider_description TEXT,
    ADD COLUMN IF NOT EXISTS script_patterns JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS iframe_patterns JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS cookie_names JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS local_storage_keys JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS block_method VARCHAR(50) DEFAULT 'script_rewrite';

-- 3. Add missing fields to cookie_consent_logs
ALTER TABLE cookie_consent_logs
    ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(255),
    ADD COLUMN IF NOT EXISTS revision_id INTEGER,
    ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP DEFAULT NOW();

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_cookie_banner_configs_scan ON cookie_banner_configs(scan_completed_at);
CREATE INDEX IF NOT EXISTS idx_cookie_consent_logs_timestamp ON cookie_consent_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_cookie_services_block_method ON cookie_services(block_method);

-- 5. Update existing cookie_services with extended data for common services
UPDATE cookie_services SET
    privacy_url = 'https://policies.google.com/privacy',
    provider_address = 'Google Ireland Ltd., Gordon House, Barrow Street, Dublin 4, Ireland',
    provider_privacy_url = 'https://policies.google.com/privacy',
    provider_cookie_url = 'https://policies.google.com/technologies/cookies',
    provider_description = 'Google Analytics sammelt anonymisierte Daten über Website-Besucher für statistische Analysen.',
    script_patterns = '["googletagmanager.com", "google-analytics.com", "gtag"]'::jsonb,
    cookie_names = '["_ga", "_gid", "_gat", "_gat_gtag"]'::jsonb,
    block_method = 'script_rewrite'
WHERE service_key = 'google_analytics_ga4' OR service_key = 'google_analytics';

UPDATE cookie_services SET
    privacy_url = 'https://www.facebook.com/privacy/policy',
    provider_address = 'Meta Platforms Ireland Ltd., 4 Grand Canal Square, Dublin 2, Ireland',
    provider_privacy_url = 'https://www.facebook.com/privacy/policy',
    provider_cookie_url = 'https://www.facebook.com/policies/cookies/',
    provider_description = 'Facebook Pixel ermöglicht Conversion-Tracking und Remarketing auf Facebook.',
    script_patterns = '["connect.facebook.net", "fbq(", "facebook.com/tr"]'::jsonb,
    cookie_names = '["_fbp", "_fbc", "fr"]'::jsonb,
    block_method = 'script_rewrite'
WHERE service_key = 'facebook_pixel';

UPDATE cookie_services SET
    privacy_url = 'https://support.google.com/youtube/answer/10315420',
    provider_address = 'Google Ireland Ltd., Gordon House, Barrow Street, Dublin 4, Ireland',
    provider_privacy_url = 'https://policies.google.com/privacy',
    provider_cookie_url = 'https://policies.google.com/technologies/cookies',
    provider_description = 'YouTube ermöglicht das Einbetten von Videos auf Ihrer Website.',
    iframe_patterns = '["youtube.com", "youtube-nocookie.com", "youtu.be"]'::jsonb,
    cookie_names = '["VISITOR_INFO1_LIVE", "YSC", "PREF", "GPS"]'::jsonb,
    block_method = 'iframe_placeholder'
WHERE service_key = 'youtube' OR service_key = 'youtube_video';

UPDATE cookie_services SET
    privacy_url = 'https://policies.google.com/privacy',
    provider_address = 'Google Ireland Ltd., Gordon House, Barrow Street, Dublin 4, Ireland',
    provider_privacy_url = 'https://policies.google.com/privacy',
    provider_description = 'Google Maps ermöglicht das Einbetten interaktiver Karten auf Ihrer Website.',
    iframe_patterns = '["google.com/maps", "maps.google.com", "maps.googleapis.com"]'::jsonb,
    cookie_names = '["NID", "CONSENT", "__Secure-3PSID"]'::jsonb,
    block_method = 'iframe_placeholder'
WHERE service_key = 'google_maps';

UPDATE cookie_services SET
    privacy_url = 'https://www.hotjar.com/legal/policies/privacy/',
    provider_address = 'Hotjar Ltd., Dragonara Business Centre, 5th Floor, Dragonara Road, Paceville, St Julian\'s STJ 3141, Malta',
    provider_privacy_url = 'https://www.hotjar.com/legal/policies/privacy/',
    provider_description = 'Hotjar analysiert das Nutzerverhalten durch Heatmaps und Session-Recordings.',
    script_patterns = '["static.hotjar.com", "script.hotjar.com"]'::jsonb,
    cookie_names = '["_hjid", "_hjFirstSeen", "_hjAbsoluteSessionInProgress", "_hjSession"]'::jsonb,
    block_method = 'script_rewrite'
WHERE service_key = 'hotjar';

-- Log
DO $$
BEGIN
    RAISE NOTICE 'Cookie Compliance tables fixed successfully - added missing columns and indexes';
END $$;
