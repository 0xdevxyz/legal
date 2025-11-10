-- ============================================================================
-- Cookie Compliance System - Database Schema
-- ============================================================================
-- Complyo Cookie-Compliance-Tool Datenbank-Tabellen
-- Erstellt: November 2025
-- Version: 1.0
-- ============================================================================

-- ============================================================================
-- 1. Cookie Consent Logs (DSGVO-konforme Dokumentation)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cookie_consent_logs (
    id BIGSERIAL PRIMARY KEY,
    site_id VARCHAR(255) NOT NULL,
    visitor_id VARCHAR(255) NOT NULL, -- Hash/UUID für Pseudonymisierung
    consent_categories JSONB NOT NULL, -- {"necessary": true, "analytics": false, "marketing": true, "functional": false}
    services_accepted JSONB, -- ["google_analytics", "youtube", "facebook_pixel"]
    ip_address_hash VARCHAR(64), -- SHA256 Hash der IP (Datensparsamkeit)
    user_agent TEXT,
    revision_id INTEGER NOT NULL, -- Banner/Config Version
    language VARCHAR(10), -- Sprache des Banners (de, en, fr, etc.)
    banner_shown BOOLEAN DEFAULT true, -- Wurde Banner angezeigt oder automatisch akzeptiert (Bot)
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '3 years') -- Auto-Löschung nach 3 Jahren (DSGVO)
);

CREATE INDEX IF NOT EXISTS idx_consent_site_visitor ON cookie_consent_logs(site_id, visitor_id);
CREATE INDEX IF NOT EXISTS idx_consent_timestamp ON cookie_consent_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_consent_expires ON cookie_consent_logs(expires_at);
CREATE INDEX IF NOT EXISTS idx_consent_site_date ON cookie_consent_logs(site_id, DATE(timestamp));

COMMENT ON TABLE cookie_consent_logs IS 'DSGVO-konforme Dokumentation aller Cookie-Consents (3 Jahre Aufbewahrung)';
COMMENT ON COLUMN cookie_consent_logs.visitor_id IS 'Pseudonymisierter Visitor (UUID/Hash) - kein PII';
COMMENT ON COLUMN cookie_consent_logs.ip_address_hash IS 'SHA256 Hash der IP-Adresse (nicht reversibel)';
COMMENT ON COLUMN cookie_consent_logs.revision_id IS 'Banner-Konfiguration Version - für Revision History';

-- ============================================================================
-- 2. Cookie Banner Configurations
-- ============================================================================
CREATE TABLE IF NOT EXISTS cookie_banner_configs (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Banner Design
    layout VARCHAR(50) DEFAULT 'banner_bottom', -- banner_bottom, banner_top, box_modal, floating_widget
    primary_color VARCHAR(7) DEFAULT '#6366f1', -- Hex color
    accent_color VARCHAR(7) DEFAULT '#8b5cf6',
    text_color VARCHAR(7) DEFAULT '#333333',
    bg_color VARCHAR(7) DEFAULT '#ffffff',
    button_style VARCHAR(50) DEFAULT 'rounded', -- rounded, square, pill
    
    -- Banner Position & Size
    position VARCHAR(50) DEFAULT 'bottom', -- bottom, top, center
    width_mode VARCHAR(50) DEFAULT 'full', -- full, boxed, compact
    
    -- Texts (Multi-Language Support)
    texts JSONB NOT NULL DEFAULT '{
        "de": {
            "title": "🍪 Wir respektieren Ihre Privatsphäre",
            "description": "Wir verwenden Cookies, um Ihre Erfahrung zu verbessern. Weitere Informationen finden Sie in unserer Datenschutzerklärung.",
            "accept_all": "Alle akzeptieren",
            "reject_all": "Ablehnen",
            "accept_selected": "Auswahl akzeptieren",
            "settings": "Einstellungen",
            "privacy_policy": "Datenschutzerklärung",
            "imprint": "Impressum"
        },
        "en": {
            "title": "🍪 We respect your privacy",
            "description": "We use cookies to enhance your experience. More information in our privacy policy.",
            "accept_all": "Accept all",
            "reject_all": "Reject",
            "accept_selected": "Accept selection",
            "settings": "Settings",
            "privacy_policy": "Privacy Policy",
            "imprint": "Imprint"
        }
    }'::jsonb,
    
    -- Services Configuration
    services JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of enabled service IDs
    
    -- Advanced Settings
    show_on_pages JSONB DEFAULT '{"all": true, "exclude": []}'::jsonb,
    geo_restriction JSONB DEFAULT '{"enabled": false, "countries": []}'::jsonb,
    auto_block_scripts BOOLEAN DEFAULT true,
    respect_dnt BOOLEAN DEFAULT true, -- Do Not Track Header
    cookie_lifetime_days INTEGER DEFAULT 365,
    
    -- Branding (Expert Plan)
    show_branding BOOLEAN DEFAULT true, -- "Powered by Complyo"
    custom_logo_url TEXT,
    
    -- Metadata
    revision INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_banner_config_site ON cookie_banner_configs(site_id);
CREATE INDEX IF NOT EXISTS idx_banner_config_user ON cookie_banner_configs(user_id);

COMMENT ON TABLE cookie_banner_configs IS 'Cookie-Banner-Konfigurationen pro Website';
COMMENT ON COLUMN cookie_banner_configs.revision IS 'Version der Konfiguration - erhöht sich bei Änderungen';
COMMENT ON COLUMN cookie_banner_configs.show_branding IS 'false für Expert Plan (White-Label)';

-- ============================================================================
-- 3. Cookie Services (Service Templates)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cookie_services (
    id SERIAL PRIMARY KEY,
    service_key VARCHAR(100) UNIQUE NOT NULL, -- z.B. "google_analytics_ga4"
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL, -- analytics, marketing, functional, necessary
    provider VARCHAR(255), -- z.B. "Google LLC"
    
    -- Template Data
    template JSONB NOT NULL, -- Vollständige Service-Definition (siehe unten)
    
    -- Availability
    is_active BOOLEAN DEFAULT TRUE,
    plan_required VARCHAR(50) DEFAULT 'ai', -- ai, expert (für Premium-Services)
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_service_key ON cookie_services(service_key);
CREATE INDEX IF NOT EXISTS idx_service_category ON cookie_services(category);
CREATE INDEX IF NOT EXISTS idx_service_active ON cookie_services(is_active);

COMMENT ON TABLE cookie_services IS 'Service-Templates für Cookie-Management (Google Analytics, YouTube, etc.)';
COMMENT ON COLUMN cookie_services.template IS 'JSON mit: cookies, domains, privacy_policy_url, description, legal_basis, content_blocker_rules';

-- ============================================================================
-- 4. Cookie Compliance Statistics (Aggregated)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cookie_compliance_stats (
    id BIGSERIAL PRIMARY KEY,
    site_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    
    -- Impressions & Consents
    total_impressions INTEGER DEFAULT 0, -- Banner angezeigt
    accepted_all INTEGER DEFAULT 0, -- "Alle akzeptieren" geklickt
    accepted_partial INTEGER DEFAULT 0, -- Individuelle Auswahl
    rejected_all INTEGER DEFAULT 0, -- "Ablehnen" geklickt
    
    -- Category-specific
    accepted_analytics INTEGER DEFAULT 0,
    accepted_marketing INTEGER DEFAULT 0,
    accepted_functional INTEGER DEFAULT 0,
    
    -- Service-specific (Top 10)
    service_stats JSONB DEFAULT '{}'::jsonb, -- {"google_analytics": 150, "youtube": 120, ...}
    
    -- Metadata
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(site_id, date)
);

CREATE INDEX IF NOT EXISTS idx_stats_site_date ON cookie_compliance_stats(site_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_stats_date ON cookie_compliance_stats(date DESC);

COMMENT ON TABLE cookie_compliance_stats IS 'Aggregierte Statistiken für Opt-In-Rate Analyse';

-- ============================================================================
-- 5. Cookie Banner Revision History (für DSGVO-Nachweis)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cookie_banner_revisions (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR(255) NOT NULL,
    revision INTEGER NOT NULL,
    config_snapshot JSONB NOT NULL, -- Vollständige Konfiguration zu diesem Zeitpunkt
    services_snapshot JSONB NOT NULL, -- Welche Services waren aktiv
    changed_by INTEGER REFERENCES users(id),
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(site_id, revision)
);

CREATE INDEX IF NOT EXISTS idx_revision_site ON cookie_banner_revisions(site_id, revision DESC);

COMMENT ON TABLE cookie_banner_revisions IS 'Historie aller Banner-Konfigurationen für DSGVO-Nachweis';

-- ============================================================================
-- 6. Trigger für automatische Revision-Erhöhung
-- ============================================================================
CREATE OR REPLACE FUNCTION increment_banner_revision()
RETURNS TRIGGER AS $$
BEGIN
    -- Revision erhöhen bei Änderung
    IF (OLD.config IS DISTINCT FROM NEW.config) OR (OLD.services IS DISTINCT FROM NEW.services) THEN
        NEW.revision := OLD.revision + 1;
        NEW.updated_at := NOW();
        
        -- Snapshot in Revisions-Tabelle speichern
        INSERT INTO cookie_banner_revisions (site_id, revision, config_snapshot, services_snapshot, changed_by)
        VALUES (NEW.site_id, NEW.revision, row_to_json(NEW)::jsonb, NEW.services, NEW.user_id);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_banner_revision
    BEFORE UPDATE ON cookie_banner_configs
    FOR EACH ROW
    EXECUTE FUNCTION increment_banner_revision();

-- ============================================================================
-- 7. Automatische Löschung abgelaufener Consent-Logs (DSGVO Compliance)
-- ============================================================================
CREATE OR REPLACE FUNCTION delete_expired_consents()
RETURNS void AS $$
BEGIN
    DELETE FROM cookie_consent_logs
    WHERE expires_at < NOW();
    
    RAISE NOTICE 'Deleted expired consent logs (older than 3 years)';
END;
$$ LANGUAGE plpgsql;

-- Optional: Cronjob einrichten (ausführen via pg_cron oder externe Cron)
-- SELECT cron.schedule('delete-expired-consents', '0 2 * * *', 'SELECT delete_expired_consents()');

COMMENT ON FUNCTION delete_expired_consents IS 'DSGVO: Löscht Consent-Logs älter als 3 Jahre';

-- ============================================================================
-- 8. Initial Service Templates (20 wichtigste Services)
-- ============================================================================

-- Google Analytics GA4
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('google_analytics_ga4', 'Google Analytics 4', 'analytics', 'Google LLC', '{
    "id": "google_analytics_ga4",
    "name": "Google Analytics 4",
    "category": "analytics",
    "consent_type": "statistics",
    "cookies": ["_ga", "_ga_*", "_gid", "_gat"],
    "domains": ["google-analytics.com", "googletagmanager.com"],
    "privacy_policy_url": "https://policies.google.com/privacy",
    "description_de": "Web-Analyse Tool von Google zur Erfassung von Besucherstatistiken",
    "description_en": "Google web analytics tool for visitor statistics",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)",
    "data_processing_countries": ["USA"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "cookie_lifetime": "2 Jahre",
    "content_blocker_rules": [
        {"type": "script_src", "pattern": "googletagmanager.com/gtag/js"},
        {"type": "script_src", "pattern": "google-analytics.com/analytics.js"},
        {"type": "script_src", "pattern": "google-analytics.com/ga.js"}
    ]
}'::jsonb, 'ai');

-- Google Tag Manager
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('google_tag_manager', 'Google Tag Manager', 'functional', 'Google LLC', '{
    "id": "google_tag_manager",
    "name": "Google Tag Manager",
    "category": "functional",
    "consent_type": "functional",
    "cookies": ["_ga", "_gid"],
    "domains": ["googletagmanager.com"],
    "privacy_policy_url": "https://policies.google.com/privacy",
    "description_de": "Tag-Management-System zur Verwaltung von Marketing-Tags",
    "description_en": "Tag management system for marketing tags",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "content_blocker_rules": [
        {"type": "script_src", "pattern": "googletagmanager.com/gtm.js"}
    ]
}'::jsonb, 'ai');

-- YouTube
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('youtube', 'YouTube', 'marketing', 'Google LLC', '{
    "id": "youtube",
    "name": "YouTube",
    "category": "marketing",
    "consent_type": "marketing",
    "cookies": ["VISITOR_INFO1_LIVE", "YSC", "PREF"],
    "domains": ["youtube.com", "youtube-nocookie.com"],
    "privacy_policy_url": "https://policies.google.com/privacy",
    "description_de": "Video-Plattform von Google für eingebettete Videos",
    "description_en": "Google video platform for embedded videos",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "placeholder": {
        "enabled": true,
        "thumbnail": true,
        "text_de": "YouTube-Video. Zum Laden bitte Cookies akzeptieren.",
        "text_en": "YouTube video. Please accept cookies to load."
    },
    "content_blocker_rules": [
        {"type": "iframe_src", "pattern": "youtube.com/embed"},
        {"type": "iframe_src", "pattern": "youtube-nocookie.com/embed"}
    ]
}'::jsonb, 'ai');

-- Google Maps
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('google_maps', 'Google Maps', 'functional', 'Google LLC', '{
    "id": "google_maps",
    "name": "Google Maps",
    "category": "functional",
    "consent_type": "functional",
    "cookies": ["NID", "CONSENT"],
    "domains": ["google.com", "googleapis.com"],
    "privacy_policy_url": "https://policies.google.com/privacy",
    "description_de": "Kartendienst von Google für interaktive Karten",
    "description_en": "Google map service for interactive maps",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "placeholder": {
        "enabled": true,
        "thumbnail": false,
        "text_de": "Google Maps. Zum Laden bitte Cookies akzeptieren.",
        "text_en": "Google Maps. Please accept cookies to load."
    },
    "content_blocker_rules": [
        {"type": "iframe_src", "pattern": "google.com/maps/embed"},
        {"type": "script_src", "pattern": "maps.googleapis.com/maps/api/js"}
    ]
}'::jsonb, 'ai');

-- Facebook Pixel
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('facebook_pixel', 'Meta Pixel (Facebook)', 'marketing', 'Meta Platforms Ireland Limited', '{
    "id": "facebook_pixel",
    "name": "Meta Pixel (Facebook)",
    "category": "marketing",
    "consent_type": "marketing",
    "cookies": ["_fbp", "_fbc", "fr"],
    "domains": ["facebook.com", "connect.facebook.net"],
    "privacy_policy_url": "https://www.facebook.com/privacy/explanation",
    "description_de": "Marketing-Pixel von Meta für Conversion-Tracking und Retargeting",
    "description_en": "Meta marketing pixel for conversion tracking and retargeting",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA", "Irland"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "cookie_lifetime": "90 Tage",
    "content_blocker_rules": [
        {"type": "script_src", "pattern": "connect.facebook.net"}
    ]
}'::jsonb, 'ai');

-- Vimeo
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('vimeo', 'Vimeo', 'marketing', 'Vimeo Inc.', '{
    "id": "vimeo",
    "name": "Vimeo",
    "category": "marketing",
    "consent_type": "marketing",
    "cookies": ["vuid", "player"],
    "domains": ["vimeo.com"],
    "privacy_policy_url": "https://vimeo.com/privacy",
    "description_de": "Video-Plattform für eingebettete Videos",
    "description_en": "Video platform for embedded videos",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "placeholder": {
        "enabled": true,
        "thumbnail": true,
        "text_de": "Vimeo-Video. Zum Laden bitte Cookies akzeptieren.",
        "text_en": "Vimeo video. Please accept cookies to load."
    },
    "content_blocker_rules": [
        {"type": "iframe_src", "pattern": "player.vimeo.com"}
    ]
}'::jsonb, 'ai');

-- Matomo (Open Source Analytics)
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('matomo', 'Matomo Analytics', 'analytics', 'InnoCraft Ltd.', '{
    "id": "matomo",
    "name": "Matomo Analytics",
    "category": "analytics",
    "consent_type": "statistics",
    "cookies": ["_pk_id", "_pk_ses", "_pk_ref"],
    "domains": ["matomo.org", "custom"],
    "privacy_policy_url": "https://matomo.org/privacy-policy/",
    "description_de": "Open-Source Web-Analyse Tool (DSGVO-freundlich, selbst gehostet)",
    "description_en": "Open-source web analytics tool (GDPR-friendly, self-hosted)",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["EU (self-hosted)"],
    "cookie_lifetime": "13 Monate",
    "content_blocker_rules": [
        {"type": "script_src", "pattern": "matomo.js"},
        {"type": "script_src", "pattern": "piwik.js"}
    ]
}'::jsonb, 'ai');

-- LinkedIn Insight Tag
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('linkedin_insight', 'LinkedIn Insight Tag', 'marketing', 'LinkedIn Corporation', '{
    "id": "linkedin_insight",
    "name": "LinkedIn Insight Tag",
    "category": "marketing",
    "consent_type": "marketing",
    "cookies": ["li_sugr", "UserMatchHistory", "bcookie"],
    "domains": ["linkedin.com", "snap.licdn.com"],
    "privacy_policy_url": "https://www.linkedin.com/legal/privacy-policy",
    "description_de": "LinkedIn Marketing-Tag für Conversion-Tracking",
    "description_en": "LinkedIn marketing tag for conversion tracking",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "content_blocker_rules": [
        {"type": "script_src", "pattern": "snap.licdn.com"}
    ]
}'::jsonb, 'ai');

-- TikTok Pixel
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('tiktok_pixel', 'TikTok Pixel', 'marketing', 'TikTok Inc.', '{
    "id": "tiktok_pixel",
    "name": "TikTok Pixel",
    "category": "marketing",
    "consent_type": "marketing",
    "cookies": ["_ttp", "_tt_enable_cookie"],
    "domains": ["tiktok.com", "analytics.tiktok.com"],
    "privacy_policy_url": "https://www.tiktok.com/legal/privacy-policy",
    "description_de": "TikTok Marketing-Pixel für Werbekampagnen",
    "description_en": "TikTok marketing pixel for ad campaigns",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA", "Singapur"],
    "content_blocker_rules": [
        {"type": "script_src", "pattern": "analytics.tiktok.com"}
    ]
}'::jsonb, 'ai');

-- Google Ads
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('google_ads', 'Google Ads (AdWords)', 'marketing', 'Google LLC', '{
    "id": "google_ads",
    "name": "Google Ads (AdWords)",
    "category": "marketing",
    "consent_type": "marketing",
    "cookies": ["_gcl_au", "test_cookie", "IDE"],
    "domains": ["googleadservices.com", "doubleclick.net"],
    "privacy_policy_url": "https://policies.google.com/privacy",
    "description_de": "Google Werbenetzwerk für Anzeigenkampagnen",
    "description_en": "Google advertising network for ad campaigns",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "content_blocker_rules": [
        {"type": "script_src", "pattern": "googleadservices.com"},
        {"type": "script_src", "pattern": "doubleclick.net"}
    ]
}'::jsonb, 'ai');

-- Hotjar
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('hotjar', 'Hotjar', 'analytics', 'Hotjar Ltd.', '{
    "id": "hotjar",
    "name": "Hotjar",
    "category": "analytics",
    "consent_type": "statistics",
    "cookies": ["_hjid", "_hjSessionUser_*", "_hjSession_*"],
    "domains": ["hotjar.com"],
    "privacy_policy_url": "https://www.hotjar.com/legal/policies/privacy/",
    "description_de": "Heatmap und Session-Recording Tool für UX-Analyse",
    "description_en": "Heatmap and session recording tool for UX analysis",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["EU", "USA"],
    "adequacy_decision": "Standard Contractual Clauses",
    "content_blocker_rules": [
        {"type": "script_src", "pattern": "static.hotjar.com"}
    ]
}'::jsonb, 'ai');

-- Intercom
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('intercom', 'Intercom', 'functional', 'Intercom Inc.', '{
    "id": "intercom",
    "name": "Intercom",
    "category": "functional",
    "consent_type": "functional",
    "cookies": ["intercom-id-*", "intercom-session-*"],
    "domains": ["intercom.io", "intercom.com"],
    "privacy_policy_url": "https://www.intercom.com/legal/privacy",
    "description_de": "Live-Chat und Customer Messaging Platform",
    "description_en": "Live chat and customer messaging platform",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA", "EU"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "content_blocker_rules": [
        {"type": "script_src", "pattern": "widget.intercom.io"}
    ]
}'::jsonb, 'ai');

-- Zendesk
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('zendesk', 'Zendesk Chat', 'functional', 'Zendesk Inc.', '{
    "id": "zendesk",
    "name": "Zendesk Chat",
    "category": "functional",
    "consent_type": "functional",
    "cookies": ["_zendesk_cookie", "_help_center_session"],
    "domains": ["zendesk.com", "zdassets.com"],
    "privacy_policy_url": "https://www.zendesk.com/company/agreements-and-terms/privacy-notice/",
    "description_de": "Kundenservice und Live-Chat Platform",
    "description_en": "Customer service and live chat platform",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "content_blocker_rules": [
        {"type": "script_src", "pattern": "static.zdassets.com"}
    ]
}'::jsonb, 'ai');

-- Instagram Embed
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('instagram', 'Instagram', 'marketing', 'Meta Platforms Ireland Limited', '{
    "id": "instagram",
    "name": "Instagram",
    "category": "marketing",
    "consent_type": "marketing",
    "cookies": ["ig_did", "mid", "fbsr_*"],
    "domains": ["instagram.com", "cdninstagram.com"],
    "privacy_policy_url": "https://help.instagram.com/519522125107875",
    "description_de": "Social Media Plattform für eingebettete Beiträge",
    "description_en": "Social media platform for embedded posts",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA", "Irland"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "placeholder": {
        "enabled": true,
        "thumbnail": false,
        "text_de": "Instagram-Post. Zum Laden bitte Cookies akzeptieren.",
        "text_en": "Instagram post. Please accept cookies to load."
    },
    "content_blocker_rules": [
        {"type": "iframe_src", "pattern": "instagram.com/p/"},
        {"type": "script_src", "pattern": "instagram.com/embed.js"}
    ]
}'::jsonb, 'ai');

-- Twitter/X Embed
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('twitter_x', 'X (Twitter)', 'marketing', 'X Corp.', '{
    "id": "twitter_x",
    "name": "X (Twitter)",
    "category": "marketing",
    "consent_type": "marketing",
    "cookies": ["personalization_id", "guest_id", "ct0"],
    "domains": ["twitter.com", "x.com", "twimg.com"],
    "privacy_policy_url": "https://twitter.com/privacy",
    "description_de": "Social Media Plattform für eingebettete Tweets",
    "description_en": "Social media platform for embedded tweets",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "placeholder": {
        "enabled": true,
        "thumbnail": false,
        "text_de": "X/Twitter-Post. Zum Laden bitte Cookies akzeptieren.",
        "text_en": "X/Twitter post. Please accept cookies to load."
    },
    "content_blocker_rules": [
        {"type": "script_src", "pattern": "platform.twitter.com/widgets.js"},
        {"type": "script_src", "pattern": "platform.x.com"}
    ]
}'::jsonb, 'ai');

-- Facebook Social Plugins
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('facebook_plugin', 'Facebook Social Plugins', 'marketing', 'Meta Platforms Ireland Limited', '{
    "id": "facebook_plugin",
    "name": "Facebook Social Plugins",
    "category": "marketing",
    "consent_type": "marketing",
    "cookies": ["fr", "xs", "c_user"],
    "domains": ["facebook.com", "facebook.net"],
    "privacy_policy_url": "https://www.facebook.com/privacy/explanation",
    "description_de": "Facebook Social Plugins (Like-Button, Kommentare, etc.)",
    "description_en": "Facebook social plugins (Like button, comments, etc.)",
    "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO",
    "data_processing_countries": ["USA", "Irland"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "content_blocker_rules": [
        {"type": "iframe_src", "pattern": "facebook.com/plugins"},
        {"type": "script_src", "pattern": "connect.facebook.net/*/sdk.js"}
    ]
}'::jsonb, 'ai');

-- OpenStreetMap
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('openstreetmap', 'OpenStreetMap', 'functional', 'OpenStreetMap Foundation', '{
    "id": "openstreetmap",
    "name": "OpenStreetMap",
    "category": "functional",
    "consent_type": "functional",
    "cookies": [],
    "domains": ["openstreetmap.org"],
    "privacy_policy_url": "https://wiki.osmfoundation.org/wiki/Privacy_Policy",
    "description_de": "Open-Source Kartendienst (DSGVO-freundlich, keine Tracking-Cookies)",
    "description_en": "Open-source map service (GDPR-friendly, no tracking cookies)",
    "legal_basis": "Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse)",
    "data_processing_countries": ["EU", "weltweit"],
    "cookie_lifetime": "Keine Cookies",
    "content_blocker_rules": [
        {"type": "iframe_src", "pattern": "openstreetmap.org/export/embed.html"}
    ]
}'::jsonb, 'ai');

-- Plausible Analytics (Privacy-Friendly)
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('plausible', 'Plausible Analytics', 'analytics', 'Plausible Insights OÜ', '{
    "id": "plausible",
    "name": "Plausible Analytics",
    "category": "analytics",
    "consent_type": "statistics",
    "cookies": [],
    "domains": ["plausible.io"],
    "privacy_policy_url": "https://plausible.io/privacy",
    "description_de": "Privacy-First Analytics ohne Cookies (DSGVO-konform ohne Consent)",
    "description_en": "Privacy-first analytics without cookies (GDPR compliant without consent)",
    "legal_basis": "Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse)",
    "data_processing_countries": ["EU"],
    "cookie_lifetime": "Keine Cookies",
    "content_blocker_rules": []
}'::jsonb, 'ai');

-- Stripe Payment
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('stripe', 'Stripe', 'necessary', 'Stripe Inc.', '{
    "id": "stripe",
    "name": "Stripe",
    "category": "necessary",
    "consent_type": "necessary",
    "cookies": ["__stripe_mid", "__stripe_sid"],
    "domains": ["stripe.com", "js.stripe.com"],
    "privacy_policy_url": "https://stripe.com/privacy",
    "description_de": "Payment-Provider für sichere Zahlungsabwicklung (technisch notwendig)",
    "description_en": "Payment provider for secure payment processing (technically necessary)",
    "legal_basis": "Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung)",
    "data_processing_countries": ["USA", "EU"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "cookie_lifetime": "1 Jahr",
    "content_blocker_rules": []
}'::jsonb, 'ai');

-- Google Fonts
INSERT INTO cookie_services (service_key, name, category, provider, template, plan_required) VALUES
('google_fonts', 'Google Fonts', 'functional', 'Google LLC', '{
    "id": "google_fonts",
    "name": "Google Fonts",
    "category": "functional",
    "consent_type": "functional",
    "cookies": [],
    "domains": ["fonts.googleapis.com", "fonts.gstatic.com"],
    "privacy_policy_url": "https://policies.google.com/privacy",
    "description_de": "Schriftarten von Google (kann IP-Adresse übertragen)",
    "description_en": "Fonts from Google (may transfer IP address)",
    "legal_basis": "Art. 6 Abs. 1 lit. f DSGVO oder lit. a (bei Einbindung)",
    "data_processing_countries": ["USA"],
    "adequacy_decision": "EU-US Data Privacy Framework",
    "cookie_lifetime": "Keine Cookies",
    "content_blocker_rules": [
        {"type": "link_href", "pattern": "fonts.googleapis.com"},
        {"type": "style_src", "pattern": "fonts.googleapis.com"}
    ]
}'::jsonb, 'ai');

-- ============================================================================
-- 9. Views für einfachere Abfragen
-- ============================================================================

-- Consent-Rate pro Website
CREATE OR REPLACE VIEW v_consent_rates AS
SELECT 
    site_id,
    DATE(timestamp) as date,
    COUNT(*) as total_consents,
    SUM(CASE WHEN (consent_categories->>'analytics')::boolean = true THEN 1 ELSE 0 END) as analytics_accepted,
    SUM(CASE WHEN (consent_categories->>'marketing')::boolean = true THEN 1 ELSE 0 END) as marketing_accepted,
    SUM(CASE WHEN (consent_categories->>'functional')::boolean = true THEN 1 ELSE 0 END) as functional_accepted,
    ROUND(100.0 * SUM(CASE WHEN (consent_categories->>'analytics')::boolean = true THEN 1 ELSE 0 END) / COUNT(*), 2) as analytics_rate,
    ROUND(100.0 * SUM(CASE WHEN (consent_categories->>'marketing')::boolean = true THEN 1 ELSE 0 END) / COUNT(*), 2) as marketing_rate
FROM cookie_consent_logs
GROUP BY site_id, DATE(timestamp);

COMMENT ON VIEW v_consent_rates IS 'Consent-Raten pro Website und Tag';

-- ============================================================================
-- 10. Beispiel-Abfragen (als Kommentare für Dokumentation)
-- ============================================================================

-- Consent-Log für einen Besucher anzeigen:
-- SELECT * FROM cookie_consent_logs WHERE visitor_id = 'uuid-here' ORDER BY timestamp DESC;

-- Opt-In-Rate der letzten 30 Tage:
-- SELECT site_id, AVG(analytics_rate) as avg_optin_rate 
-- FROM v_consent_rates 
-- WHERE date >= NOW() - INTERVAL '30 days'
-- GROUP BY site_id;

-- Meist akzeptierte Services:
-- SELECT 
--     jsonb_array_elements_text(services_accepted) as service,
--     COUNT(*) as acceptance_count
-- FROM cookie_consent_logs
-- WHERE services_accepted IS NOT NULL
-- GROUP BY service
-- ORDER BY acceptance_count DESC
-- LIMIT 10;

-- ============================================================================
-- Installation abgeschlossen
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Cookie Compliance System installiert!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tabellen erstellt:';
    RAISE NOTICE '  ✓ cookie_consent_logs';
    RAISE NOTICE '  ✓ cookie_banner_configs';
    RAISE NOTICE '  ✓ cookie_services (20 Services)';
    RAISE NOTICE '  ✓ cookie_compliance_stats';
    RAISE NOTICE '  ✓ cookie_banner_revisions';
    RAISE NOTICE '';
    RAISE NOTICE 'Nächste Schritte:';
    RAISE NOTICE '  1. Backend-Routes implementieren';
    RAISE NOTICE '  2. Cookie-Banner Widget entwickeln';
    RAISE NOTICE '  3. Dashboard-Integration';
    RAISE NOTICE '========================================';
END $$;

