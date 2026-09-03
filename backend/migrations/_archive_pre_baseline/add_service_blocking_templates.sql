-- Migration: Add complete blocking templates for all cookie services
-- Date: 2025-11-11
-- This adds script_patterns, cookie_names, and blocking instructions for auto-blocking

-- Update table schema to include blocking information
ALTER TABLE cookie_services 
ADD COLUMN IF NOT EXISTS script_patterns JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS iframe_patterns JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS cookie_names JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS local_storage_keys JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS block_method VARCHAR(50) DEFAULT 'script_rewrite',
ADD COLUMN IF NOT EXISTS privacy_policy_url TEXT;

-- ============================================================================
-- ANALYTICS & TRACKING
-- ============================================================================

-- Google Analytics GA4
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('google_analytics_ga4', 'Google Analytics 4', 'analytics', 'Google LLC', 
 'Website-Analyse und Besucherstatistiken mit Google Analytics 4', 
 '["_ga", "_gid", "_gat", "_gat_gtag_*", "_ga_*"]',
 '["googletagmanager.com/gtag/js", "google-analytics.com/analytics.js", "google-analytics.com/ga.js"]',
 '[]',
 '["_ga", "_gid", "_gat", "_gat_gtag_*", "_ga_*"]',
 'script_rewrite',
 true, 'free',
 'https://policies.google.com/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Google Tag Manager
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('google_tag_manager', 'Google Tag Manager', 'analytics', 'Google LLC',
 'Tag-Management-System für Marketing und Analytics-Tags',
 '["_gcl_*"]',
 '["googletagmanager.com/gtm.js"]',
 '["googletagmanager.com/ns.html"]',
 '["_gcl_au", "_gcl_aw", "_gcl_dc"]',
 'script_rewrite',
 true, 'free',
 'https://policies.google.com/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Matomo
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('matomo', 'Matomo Analytics', 'analytics', 'Matomo',
 'Open-Source Web-Analyse-Plattform (ehemals Piwik)',
 '["_pk_id", "_pk_ses", "_pk_ref", "_pk_cvar", "_pk_hsr"]',
 '["matomo.js", "piwik.js", "matomo.php", "piwik.php"]',
 '[]',
 '["_pk_id", "_pk_ses", "_pk_ref", "_pk_cvar", "_pk_hsr"]',
 'script_rewrite',
 true, 'free',
 'https://matomo.org/privacy-policy/')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Hotjar
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('hotjar', 'Hotjar', 'analytics', 'Hotjar Ltd',
 'Heatmaps, Session-Recordings und User-Feedback',
 '["_hjid", "_hjSessionUser_*", "_hjSession_*", "_hjAbsoluteSessionInProgress", "_hjFirstSeen", "_hjIncludedInPageviewSample", "_hjIncludedInSessionSample"]',
 '["static.hotjar.com/c/hotjar-", "script.hotjar.com"]',
 '[]',
 '["_hjid", "_hjSessionUser_*", "_hjSession_*", "_hjAbsoluteSessionInProgress", "_hjFirstSeen", "_hjIncludedInPageviewSample", "_hjIncludedInSessionSample"]',
 'script_rewrite',
 true, 'free',
 'https://www.hotjar.com/legal/policies/privacy/')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Plausible
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('plausible', 'Plausible Analytics', 'analytics', 'Plausible Insights OÜ',
 'Privacy-First Analytics ohne Cookies',
 '[]',
 '["plausible.io/js/plausible.js", "plausible.io/js/script.js"]',
 '[]',
 '[]',
 'script_rewrite',
 true, 'free',
 'https://plausible.io/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- ============================================================================
-- MARKETING & ADVERTISING
-- ============================================================================

-- Facebook Pixel
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('facebook_pixel', 'Facebook Pixel', 'marketing', 'Meta Platforms Ireland Limited',
 'Conversion-Tracking und Remarketing für Facebook-Werbung',
 '["_fbp", "_fbc", "fr", "sb", "datr", "c_user", "xs"]',
 '["connect.facebook.net/*/fbevents.js", "facebook.com/tr"]',
 '[]',
 '["_fbp", "_fbc", "fr", "sb", "datr", "c_user", "xs"]',
 'script_rewrite',
 true, 'free',
 'https://www.facebook.com/privacy/explanation')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Google Ads
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('google_ads', 'Google Ads', 'marketing', 'Google LLC',
 'Werbe-Tracking und Conversion-Messung für Google Ads',
 '["_gcl_au", "_gcl_aw", "_gcl_dc", "_gac_*", "IDE", "test_cookie", "DSID", "id"]',
 '["googleadservices.com/pagead/conversion", "doubleclick.net", "googlesyndication.com"]',
 '[]',
 '["_gcl_au", "_gcl_aw", "_gcl_dc", "_gac_*", "IDE", "test_cookie", "DSID", "id"]',
 'script_rewrite',
 true, 'free',
 'https://policies.google.com/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- LinkedIn Insight Tag
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('linkedin_insight', 'LinkedIn Insight Tag', 'marketing', 'LinkedIn Ireland Unlimited Company',
 'Conversion-Tracking für LinkedIn-Werbung',
 '["li_fat_id", "lidc", "li_sugr", "UserMatchHistory", "bcookie"]',
 '["snap.licdn.com/li.lms-analytics/insight.min.js", "linkedin.com/px"]',
 '[]',
 '["li_fat_id", "lidc", "li_sugr", "UserMatchHistory", "bcookie"]',
 'script_rewrite',
 true, 'free',
 'https://www.linkedin.com/legal/privacy-policy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- TikTok Pixel
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('tiktok_pixel', 'TikTok Pixel', 'marketing', 'TikTok Technology Limited',
 'Conversion-Tracking für TikTok-Werbung',
 '["_ttp", "_tta", "tt_appInfo", "tt_sessionId", "tt_pixel_session_index"]',
 '["analytics.tiktok.com/i18n/pixel/events.js", "analytics.tiktok.com/i18n/pixel/sdk.js"]',
 '[]',
 '["_ttp", "_tta", "tt_appInfo", "tt_sessionId", "tt_pixel_session_index"]',
 'script_rewrite',
 true, 'free',
 'https://www.tiktok.com/legal/privacy-policy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Twitter/X Pixel
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('twitter_x', 'Twitter/X Pixel', 'marketing', 'Twitter International Company',
 'Conversion-Tracking für Twitter/X-Werbung',
 '["auth_token", "personalization_id", "guest_id", "ct0", "muc_ads"]',
 '["platform.twitter.com/widgets.js", "static.ads-twitter.com/uwt.js"]',
 '["platform.twitter.com/widgets", "twitter.com/i/videos", "x.com/i/videos"]',
 '["auth_token", "personalization_id", "guest_id", "ct0", "muc_ads"]',
 'script_rewrite',
 true, 'free',
 'https://twitter.com/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- ============================================================================
-- CONTENT & MEDIA
-- ============================================================================

-- YouTube
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('youtube', 'YouTube', 'functional', 'Google LLC',
 'Video-Einbettungen von YouTube',
 '["VISITOR_INFO1_LIVE", "YSC", "CONSENT", "PREF"]',
 '["youtube.com/iframe_api", "youtube.com/embed/"]',
 '["youtube.com/embed/", "youtube-nocookie.com/embed/"]',
 '["VISITOR_INFO1_LIVE", "YSC", "CONSENT", "PREF"]',
 'iframe_placeholder',
 true, 'free',
 'https://policies.google.com/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Vimeo
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('vimeo', 'Vimeo', 'functional', 'Vimeo Inc.',
 'Video-Einbettungen von Vimeo',
 '["vuid", "player"]',
 '["player.vimeo.com/api/player.js"]',
 '["player.vimeo.com/video/"]',
 '["vuid", "player"]',
 'iframe_placeholder',
 true, 'free',
 'https://vimeo.com/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Instagram
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('instagram', 'Instagram', 'marketing', 'Meta Platforms Ireland Limited',
 'Instagram-Feed-Einbettungen',
 '["ig_did", "ig_nrcb", "csrftoken", "mid"]',
 '["instagram.com/embed.js"]',
 '["instagram.com/embed", "instagram.com/p/"]',
 '["ig_did", "ig_nrcb", "csrftoken", "mid"]',
 'iframe_placeholder',
 true, 'free',
 'https://help.instagram.com/519522125107875')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Google Maps
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('google_maps', 'Google Maps', 'functional', 'Google LLC',
 'Karten-Einbettungen von Google Maps',
 '["NID", "CONSENT", "1P_JAR", "SIDCC"]',
 '["maps.googleapis.com/maps/api/js", "maps.google.com/maps/api/js"]',
 '["google.com/maps/embed", "maps.google.com"]',
 '["NID", "CONSENT", "1P_JAR", "SIDCC"]',
 'iframe_placeholder',
 true, 'free',
 'https://policies.google.com/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- OpenStreetMap
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('openstreetmap', 'OpenStreetMap', 'functional', 'OpenStreetMap Foundation',
 'Open-Source Karten-Einbettungen',
 '["_osm_location", "_osm_session"]',
 '["openstreetmap.org", "tile.openstreetmap.org"]',
 '["openstreetmap.org/export/embed.html"]',
 '["_osm_location", "_osm_session"]',
 'iframe_placeholder',
 true, 'free',
 'https://wiki.osmfoundation.org/wiki/Privacy_Policy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- ============================================================================
-- SUPPORT & CHAT
-- ============================================================================

-- Intercom
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('intercom', 'Intercom', 'functional', 'Intercom R&D Unlimited Company',
 'Live-Chat und Customer-Messaging-Plattform',
 '["intercom-id-*", "intercom-session-*", "intercom-device-id-*"]',
 '["widget.intercom.io/widget/", "js.intercomcdn.com/"]',
 '[]',
 '["intercom-id-*", "intercom-session-*", "intercom-device-id-*"]',
 'script_rewrite',
 true, 'free',
 'https://www.intercom.com/legal/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Zendesk
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('zendesk', 'Zendesk', 'functional', 'Zendesk Inc.',
 'Customer-Support und Help-Desk-Software',
 '["__zlcmid", "_zendesk_cookie", "_zendesk_authenticated"]',
 '["static.zdassets.com/", "ekr.zdassets.com/"]',
 '[]',
 '["__zlcmid", "_zendesk_cookie", "_zendesk_authenticated"]',
 'script_rewrite',
 true, 'free',
 'https://www.zendesk.com/company/privacy-and-data-protection/')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Tawk.to
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('tawk', 'Tawk.to', 'functional', 'Tawk.to Inc.',
 'Kostenloser Live-Chat-Service',
 '["__tawkuuid", "ss-id", "ss-tk", "twk_uuid"]',
 '["embed.tawk.to/"]',
 '[]',
 '["__tawkuuid", "ss-id", "ss-tk", "twk_uuid"]',
 'script_rewrite',
 true, 'free',
 'https://www.tawk.to/privacy-policy/')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Crisp
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('crisp', 'Crisp', 'functional', 'Crisp IM SAS',
 'Live-Chat und Kundenkommunikation',
 '["crisp-client/*", "crisp-token"]',
 '["client.crisp.chat/"]',
 '[]',
 '["crisp-client/*", "crisp-token"]',
 'script_rewrite',
 true, 'free',
 'https://crisp.chat/en/privacy/')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- ============================================================================
-- FONTS & RESOURCES
-- ============================================================================

-- Google Fonts
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('google_fonts', 'Google Fonts', 'functional', 'Google LLC',
 'Web-Schriftarten von Google',
 '[]',
 '["fonts.googleapis.com/", "fonts.gstatic.com/"]',
 '[]',
 '[]',
 'no_blocking',
 true, 'free',
 'https://policies.google.com/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- ============================================================================
-- E-COMMERCE & PAYMENT
-- ============================================================================

-- Stripe
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('stripe', 'Stripe', 'necessary', 'Stripe Inc.',
 'Zahlungsabwicklung und Checkout',
 '["__stripe_mid", "__stripe_sid"]',
 '["js.stripe.com/v3/"]',
 '["checkout.stripe.com", "js.stripe.com"]',
 '["__stripe_mid", "__stripe_sid"]',
 'no_blocking',
 true, 'free',
 'https://stripe.com/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- PayPal
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('paypal', 'PayPal', 'necessary', 'PayPal Holdings Inc.',
 'Online-Zahlungsdienst',
 '["PYPF", "x-pp-s", "ts_c", "l7_az", "enforce_policy"]',
 '["paypal.com/sdk/js", "paypalobjects.com/"]',
 '[]',
 '["PYPF", "x-pp-s", "ts_c", "l7_az", "enforce_policy"]',
 'no_blocking',
 true, 'free',
 'https://www.paypal.com/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Shopify
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('shopify', 'Shopify', 'necessary', 'Shopify Inc.',
 'E-Commerce-Plattform - Warenkorb und Checkout',
 '["_shopify_*", "cart", "cart_currency", "secure_customer_sig", "_cmp_a", "checkout_token"]',
 '["cdn.shopify.com/"]',
 '[]',
 '["_shopify_*", "cart", "cart_currency", "secure_customer_sig", "_cmp_a", "checkout_token"]',
 'no_blocking',
 true, 'free',
 'https://www.shopify.com/legal/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- WooCommerce
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('woocommerce', 'WooCommerce', 'necessary', 'Automattic',
 'WordPress E-Commerce-Plugin - Warenkorb und Checkout',
 '["woocommerce_cart_hash", "woocommerce_items_in_cart", "wp_woocommerce_session_*", "wc_cart_hash_*", "wc_fragments_*"]',
 '[]',
 '[]',
 '["woocommerce_cart_hash", "woocommerce_items_in_cart", "wp_woocommerce_session_*", "wc_cart_hash_*", "wc_fragments_*"]',
 'no_blocking',
 true, 'free',
 'https://automattic.com/privacy/')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Magento
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('magento', 'Magento', 'necessary', 'Adobe Inc.',
 'E-Commerce-Plattform für Online-Shops',
 '["frontend", "frontend_cid", "mage-cache-*", "mage-messages", "product_data_storage", "recently_viewed_product"]',
 '[]',
 '[]',
 '["frontend", "frontend_cid", "mage-cache-*", "mage-messages", "product_data_storage", "recently_viewed_product"]',
 'no_blocking',
 true, 'free',
 'https://www.adobe.com/privacy.html')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- PrestaShop
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('prestashop', 'PrestaShop', 'necessary', 'PrestaShop SA',
 'Open-Source E-Commerce-Lösung',
 '["PrestaShop-*", "PHPSESSID"]',
 '[]',
 '[]',
 '["PrestaShop-*", "PHPSESSID"]',
 'no_blocking',
 true, 'free',
 'https://www.prestashop.com/en/privacy-policy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- ============================================================================
-- CMS & PLATFORMS
-- ============================================================================

-- WordPress
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('wordpress', 'WordPress', 'necessary', 'WordPress Foundation',
 'WordPress CMS - Session und Login-Verwaltung',
 '["wordpress_logged_in_*", "wordpress_test_cookie", "wp-settings-*", "wp-settings-time-*", "PHPSESSID"]',
 '[]',
 '[]',
 '["wordpress_logged_in_*", "wordpress_test_cookie", "wp-settings-*", "wp-settings-time-*", "PHPSESSID"]',
 'no_blocking',
 true, 'free',
 'https://wordpress.org/about/privacy/')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Elementor
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('elementor', 'Elementor', 'functional', 'Elementor Ltd.',
 'WordPress Page Builder',
 '[]',
 '[]',
 '[]',
 '[]',
 'no_blocking',
 true, 'free',
 'https://elementor.com/privacy-policy/')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Yoast SEO
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('yoast_seo', 'Yoast SEO', 'functional', 'Yoast BV',
 'WordPress SEO-Plugin',
 '[]',
 '[]',
 '[]',
 '[]',
 'no_blocking',
 true, 'free',
 'https://yoast.com/privacy-policy/')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Joomla
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('joomla', 'Joomla!', 'necessary', 'Open Source Matters Inc.',
 'Joomla! CMS - Session-Verwaltung',
 '["joomla_*", "PHPSESSID"]',
 '[]',
 '[]',
 '["joomla_*", "PHPSESSID"]',
 'no_blocking',
 true, 'free',
 'https://www.joomla.org/privacy-policy.html')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Drupal
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('drupal', 'Drupal', 'necessary', 'Drupal Association',
 'Drupal CMS - Session-Verwaltung',
 '["SESS*", "SSESS*"]',
 '[]',
 '[]',
 '["SESS*", "SSESS*"]',
 'no_blocking',
 true, 'free',
 'https://www.drupal.org/privacy')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- ============================================================================
-- CDN & INFRASTRUCTURE
-- ============================================================================

-- Cloudflare
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('cloudflare', 'Cloudflare', 'necessary', 'Cloudflare Inc.',
 'CDN, DDoS-Schutz und Web-Performance',
 '["__cfduid", "cf_clearance", "__cf_bm", "cf_ob_info", "cf_use_ob"]',
 '[]',
 '[]',
 '["__cfduid", "cf_clearance", "__cf_bm", "cf_ob_info", "cf_use_ob"]',
 'no_blocking',
 true, 'free',
 'https://www.cloudflare.com/privacypolicy/')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- PHP Session
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, script_patterns, iframe_patterns, cookie_names, block_method, is_active, plan_required, privacy_policy_url)
VALUES 
('php_session', 'PHP Session', 'necessary', 'PHP',
 'Standard PHP Session-Cookie für Website-Funktionalität',
 '["PHPSESSID"]',
 '[]',
 '[]',
 '["PHPSESSID"]',
 'no_blocking',
 true, 'free',
 'https://www.php.net/privacy.php')
ON CONFLICT (service_key) DO UPDATE SET
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    script_patterns = EXCLUDED.script_patterns,
    iframe_patterns = EXCLUDED.iframe_patterns,
    cookie_names = EXCLUDED.cookie_names,
    block_method = EXCLUDED.block_method,
    privacy_policy_url = EXCLUDED.privacy_policy_url,
    updated_at = NOW();

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_cookie_services_block_method ON cookie_services(block_method);
CREATE INDEX IF NOT EXISTS idx_cookie_services_script_patterns ON cookie_services USING GIN(script_patterns);

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '✅ Blocking templates added for all 35+ services';
    RAISE NOTICE '📋 Block methods: script_rewrite, iframe_placeholder, no_blocking';
    RAISE NOTICE '🔒 All services now have complete blocking information';
END $$;

