-- Migration: Add new cookie services (WordPress, CMS, E-Commerce, etc.)
-- Date: 2025-11-11

-- WordPress & Plugins
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('wordpress', 'WordPress', 'functional', 'WordPress Foundation', 'WordPress CMS Session-Cookies für Login und Admin-Funktionen', 
 '["wordpress_logged_in", "wordpress_test_cookie", "wp-settings-*", "PHPSESSID"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('woocommerce', 'WooCommerce', 'functional', 'Automattic', 'E-Commerce-Plugin für WordPress - verwaltet Warenkorb und Checkout', 
 '["woocommerce_cart_hash", "woocommerce_items_in_cart", "wp_woocommerce_session_*", "wc_cart_hash_*", "wc_fragments_*"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('elementor', 'Elementor', 'functional', 'Elementor Ltd.', 'Page Builder für WordPress - speichert Editor-Präferenzen', 
 '[]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('yoast_seo', 'Yoast SEO', 'functional', 'Yoast', 'SEO-Plugin für WordPress', 
 '[]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Other CMS Platforms
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('joomla', 'Joomla!', 'functional', 'Open Source Matters', 'Joomla CMS Session-Cookies', 
 '["joomla_*", "PHPSESSID"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('drupal', 'Drupal', 'functional', 'Drupal Association', 'Drupal CMS Session-Cookies', 
 '["SESS*", "SSESS*"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

-- E-Commerce Platforms
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('shopify', 'Shopify', 'functional', 'Shopify Inc.', 'E-Commerce-Plattform - Warenkorb und Checkout', 
 '["_shopify_*", "cart", "cart_currency", "secure_customer_sig"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('magento', 'Magento', 'functional', 'Adobe', 'E-Commerce-Plattform für Online-Shops', 
 '["frontend", "frontend_cid", "mage-cache-*"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('prestashop', 'PrestaShop', 'functional', 'PrestaShop SA', 'Open-Source E-Commerce-Lösung', 
 '["PrestaShop-*", "PHPSESSID"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

-- Payment Providers
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('paypal', 'PayPal', 'functional', 'PayPal Holdings', 'Online-Zahlungsdienst für sichere Transaktionen', 
 '["PYPF", "x-pp-s", "ts_c", "l7_az"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

-- Chat & Support Services
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('tawk', 'Tawk.to', 'functional', 'Tawk.to Inc.', 'Live-Chat-Support-Widget', 
 '["__tawkuuid", "ss-id", "ss-tk"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('crisp', 'Crisp', 'functional', 'Crisp IM SAS', 'Live-Chat und Customer-Messaging', 
 '["crisp-client/*"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

-- CDN & Infrastructure
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('cloudflare', 'Cloudflare', 'functional', 'Cloudflare Inc.', 'CDN und Web-Security - Bot-Schutz und Performance', 
 '["__cfduid", "cf_clearance", "__cf_bm"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

-- Session Management
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, is_active, plan_required, created_at, updated_at)
VALUES 
('php_session', 'PHP Session', 'necessary', 'PHP', 'Standard-Session-Cookie für PHP-basierte Websites', 
 '["PHPSESSID"]', true, 'free', NOW(), NOW())
ON CONFLICT (service_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    cookies = EXCLUDED.cookies,
    updated_at = NOW();

-- Update existing services with more cookie details
UPDATE cookie_services 
SET 
    cookies = '["_ga", "_gid", "_gat", "_gat_gtag_*", "_ga_*"]',
    description = 'Google Analytics 4 - Website-Analyse und Besucherstatistiken',
    updated_at = NOW()
WHERE service_key = 'google_analytics_ga4';

UPDATE cookie_services 
SET 
    cookies = '["_gcl_au", "_gcl_aw", "_gcl_dc", "_gac_*", "IDE", "test_cookie"]',
    description = 'Google Ads - Werbe-Tracking und Conversion-Messung',
    updated_at = NOW()
WHERE service_key = 'google_ads';

UPDATE cookie_services 
SET 
    cookies = '["_fbp", "_fbc", "fr", "sb", "datr"]',
    description = 'Facebook Pixel - Conversion-Tracking und Remarketing',
    updated_at = NOW()
WHERE service_key = 'facebook_pixel';

UPDATE cookie_services 
SET 
    cookies = '["_hjid", "_hjSessionUser_*", "_hjSession_*", "_hjAbsoluteSessionInProgress"]',
    description = 'Hotjar - Heatmaps, Session-Recordings und User-Feedback',
    updated_at = NOW()
WHERE service_key = 'hotjar';

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration completed: Added WordPress, CMS, E-Commerce and other common cookie services';
END $$;

