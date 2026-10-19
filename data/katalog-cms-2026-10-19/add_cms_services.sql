-- Katalogeinträge für CMS- und Shop-Plattformen sowie WordPress-Standarddienste.
--
-- Anlass (19.10.2026, spedition-mahn.de): Der HTML-Scanner (cookie_scanner_service.py,
-- DETECTION_PATTERNS) erkennt 'wordpress', 'woocommerce', 'shopify', 'joomla', 'drupal',
-- 'magento', 'prestashop', 'php_session' und 'tawk', aber keiner dieser Schlüssel hatte eine
-- Zeile in cookie_services. POST /api/cookie-compliance/scan speichert nur Katalogtreffer,
-- deshalb blieb services = [] und das Banner zeigte "Keine Services in dieser Kategorie",
-- obwohl WordPress Cookies setzt und Emoji-Grafiken von s.w.org (Automattic, USA) lädt.
--
-- Kategorie necessary: Erstanbieter-Cookies für Sitzung, Login, Warenkorb, CSRF. Rechtsgrundlage
-- und Texte setzt der INSERT unten wie in add_200_cookie_services.sql (Art. 6 Abs. 1 lit. f/b).
-- Kategorie functional: Dienste Dritter ohne Tracking-Zweck (Avatare, Emoji-CDN, Live-Chat).
--
-- Anwenden (Live, idempotent über ON CONFLICT DO NOTHING):
--   docker exec -i complyo-postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < add_cms_services.sql
-- Danach je betroffener Website POST /api/cookie-compliance/scan {"url": "https://<domain>"}.

WITH services(service_key, name, category, provider, description, cookies, domains, countries, privacy_policy_url, content_blocker_rules, cookie_lifetime, adequacy_decision) AS (
VALUES
-- necessary: Plattformen (Erstanbieter-Cookies, Daten bleiben beim Betreiber)
('wordpress','WordPress','necessary','Websitebetreiber (WordPress-Software)','Content-Management-System. Setzt Cookies nur bei Anmeldung, Kommentar oder Sprachwahl: Login-Sitzung, Testcookie der Anmeldeseite, Benutzereinstellungen und gespeicherte Kommentarangaben.', ARRAY['wordpress_test_cookie','wordpress_logged_in_*','wordpress_sec_*','wp-settings-*','wp-settings-time-*','comment_author_*','comment_author_email_*','comment_author_url_*','wp_lang'], ARRAY[]::text[], ARRAY[]::text[], NULL, '[{"type":"cookie","pattern":"wordpress_"},{"type":"cookie","pattern":"wp-settings-"}]'::jsonb, 'Sitzung bis 1 Jahr (Kommentarangaben 347 Tage)', NULL),
('woocommerce','WooCommerce','necessary','Websitebetreiber (WooCommerce-Shop-Software, Automattic Inc.)','Shop-System auf WordPress-Basis. Cookies für Warenkorb, Kassen-Sitzung und zuletzt angesehene Produkte; die Daten verarbeitet der Betreiber selbst.', ARRAY['woocommerce_cart_hash','woocommerce_items_in_cart','wp_woocommerce_session_*','woocommerce_recently_viewed','store_notice*'], ARRAY[]::text[], ARRAY[]::text[], 'https://automattic.com/privacy/', '[{"type":"cookie","pattern":"woocommerce_"}]'::jsonb, 'Sitzung bis 2 Tage', NULL),
('shopify','Shopify','necessary','Shopify International Ltd. (Irland) / Shopify Inc. (Kanada)','Shop-Plattform. Cookies für Warenkorb, Kasse, Kundensitzung, Sprach- und Währungswahl.', ARRAY['_shopify_y','_shopify_s','_secure_session_id','cart','cart_sig','cart_ts','checkout_token','secure_customer_sig','localization'], ARRAY['myshopify.com','cdn.shopify.com'], ARRAY['Irland','Kanada','USA'], 'https://www.shopify.com/legal/privacy', '[{"type":"cookie","pattern":"_shopify_"}]'::jsonb, 'Sitzung bis 1 Jahr', 'Angemessenheitsbeschluss Kanada'),
('magento','Magento / Adobe Commerce','necessary','Websitebetreiber (Magento-Shop-Software, Adobe Inc.)','Shop-System. Cookies für Sitzung, Formularschutz, Warenkorb-Zwischenspeicher und Hinweise im Kundenbereich.', ARRAY['PHPSESSID','form_key','mage-cache-sessid','mage-cache-storage','mage-messages','private_content_version','section_data_ids','X-Magento-Vary'], ARRAY[]::text[], ARRAY[]::text[], 'https://www.adobe.com/privacy/policy.html', '[{"type":"cookie","pattern":"mage-"}]'::jsonb, 'Sitzung bis 1 Jahr', NULL),
('prestashop','PrestaShop','necessary','Websitebetreiber (PrestaShop-Shop-Software)','Shop-System. Verschlüsseltes Sitzungscookie für Warenkorb, Kundenkonto und Sprache.', ARRAY['PrestaShop-*','PHPSESSID'], ARRAY[]::text[], ARRAY[]::text[], NULL, '[{"type":"cookie","pattern":"PrestaShop-"}]'::jsonb, 'Sitzung bis 20 Tage', NULL),
('drupal','Drupal','necessary','Websitebetreiber (Drupal-Software)','Content-Management-System. Sitzungscookie bei Anmeldung, Besucher-Einstellungen und JavaScript-Erkennung.', ARRAY['SESS*','SSESS*','has_js','Drupal.visitor.*'], ARRAY[]::text[], ARRAY[]::text[], NULL, '[{"type":"cookie","pattern":"SESS"}]'::jsonb, 'Sitzung bis 23 Tage', NULL),
('joomla','Joomla','necessary','Websitebetreiber (Joomla-Software)','Content-Management-System. Sitzungscookie mit zufälligem Namen, Anmeldestatus und Angemeldet-bleiben-Funktion.', ARRAY['<32-stelliger Sitzungsname>','joomla_user_state','joomla_remember_me_*'], ARRAY[]::text[], ARRAY[]::text[], NULL, '[{"type":"cookie","pattern":"joomla_"}]'::jsonb, 'Sitzung bis 1 Jahr', NULL),
('php_session','PHP-Sitzung','necessary','Websitebetreiber','Technisches Sitzungscookie des Webservers, hält Formulareingaben und Anmeldung während des Besuchs zusammen.', ARRAY['PHPSESSID'], ARRAY[]::text[], ARRAY[]::text[], NULL, '[{"type":"cookie","pattern":"PHPSESSID"}]'::jsonb, 'Sitzung', NULL),
-- functional: Dienste Dritter ohne Tracking-Zweck
('wordpress_emojis','WordPress Emojis','functional','Automattic Inc. / WordPress.org','WordPress lädt Emoji-Grafiken und ein Erkennungsskript vom Server s.w.org nach. Dabei wird die IP-Adresse an den Anbieter in den USA übertragen; Cookies werden nicht gesetzt.', ARRAY[]::text[], ARRAY['s.w.org'], ARRAY['USA'], 'https://automattic.com/privacy/', '[{"type":"script_src","pattern":"s.w.org"}]'::jsonb, 'Keine Cookies', 'EU-US Data Privacy Framework'),
('gravatar','Gravatar','functional','Automattic Inc.','Lädt Profilbilder zu E-Mail-Adressen (Kommentare, Autorenbilder) vom Dienst gravatar.com. Dabei werden IP-Adresse und ein Hashwert der E-Mail-Adresse an den Anbieter in den USA übertragen; Cookies werden nicht gesetzt.', ARRAY[]::text[], ARRAY['gravatar.com','secure.gravatar.com'], ARRAY['USA'], 'https://automattic.com/privacy/', '[{"type":"script_src","pattern":"gravatar.com"}]'::jsonb, 'Keine Cookies', 'EU-US Data Privacy Framework'),
('tawk','tawk.to Live-Chat','functional','tawk.to inc.','Live-Chat-Fenster auf der Website. Speichert Chat-Sitzung und Besucherkennung, Server in den USA.', ARRAY['TawkConnectionTime','tawkUUID','__tawkuuid','twk_idm_key','twk_uuid_*','ss'], ARRAY['tawk.to','embed.tawk.to','va.tawk.to'], ARRAY['USA'], 'https://www.tawk.to/privacy-policy/', '[{"type":"script_src","pattern":"embed.tawk.to"}]'::jsonb, 'Sitzung bis 6 Monate', NULL)
)
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, template, is_active, plan_required, created_at, updated_at)
SELECT
  service_key,
  name,
  category,
  provider,
  description,
  to_jsonb(cookies),
  jsonb_strip_nulls(jsonb_build_object(
    'id', service_key,
    'name', name,
    'category', category,
    'consent_type', CASE category WHEN 'analytics' THEN 'statistics' WHEN 'marketing' THEN 'marketing' WHEN 'necessary' THEN 'necessary' ELSE 'functional' END,
    'legal_basis', CASE category WHEN 'necessary' THEN 'Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse) bzw. Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung)' ELSE 'Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)' END,
    'description_de', description,
    'description_en', CASE category WHEN 'necessary' THEN name || ' is required for sessions, login, cart or technical operation of the website.' ELSE name || ' provides functional website features and loads resources from a third party.' END,
    'cookies', to_jsonb(cookies),
    'domains', to_jsonb(domains),
    'cookie_lifetime', cookie_lifetime,
    'data_processing_countries', to_jsonb(countries),
    'adequacy_decision', adequacy_decision,
    'privacy_policy_url', privacy_policy_url,
    'content_blocker_rules', content_blocker_rules
  )),
  true,
  'ai',
  NOW(),
  NOW()
FROM services
ON CONFLICT (service_key) DO NOTHING;
