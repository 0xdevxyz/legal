-- Migration: Weitere Cookie-Services hinzufügen
-- Datum: 2026-05-24

-- Analytics
INSERT INTO cookie_services (service_key, name, category, provider, description, cookies, template, is_active, plan_required, created_at, updated_at)
VALUES 
('google_analytics_ua', 'Google Analytics (Universal)', 'analytics', 'Google LLC', 'Ältere Version von Google Analytics (UA)', '["_ga","_gid","_gat","_utma","_utmb","_utmc","_utmz"]'::jsonb,
 '{"id":"google_analytics_ua","name":"Google Analytics (Universal)","category":"analytics","consent_type":"statistics","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Ältere Version von Google Analytics zur Besucherstatistik","description_en":"Legacy Google Analytics for visitor statistics","cookies":["_ga","_gid","_gat","_utma","_utmb","_utmc","_utmz"],"domains":["google-analytics.com"],"cookie_lifetime":"2 Jahre","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://policies.google.com/privacy","content_blocker_rules":[{"type":"script_src","pattern":"google-analytics.com/analytics.js"},{"type":"script_src","pattern":"google-analytics.com/ga.js"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('microsoft_clarity', 'Microsoft Clarity', 'analytics', 'Microsoft Corporation', 'Heatmap und Session-Recording Tool von Microsoft', '["_clck","_clsk","CLID","ANONCHK","SM","MUID","MR"]'::jsonb,
 '{"id":"microsoft_clarity","name":"Microsoft Clarity","category":"analytics","consent_type":"statistics","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Heatmap und Session-Aufzeichnung von Microsoft","description_en":"Heatmap and session recording by Microsoft","cookies":["_clck","_clsk","CLID","MUID"],"domains":["clarity.ms","microsoft.com"],"cookie_lifetime":"1 Jahr","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://privacy.microsoft.com/privacystatement","content_blocker_rules":[{"type":"script_src","pattern":"clarity.ms/tag"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('mixpanel', 'Mixpanel', 'analytics', 'Mixpanel Inc.', 'Produkt-Analytics Plattform', '["mp_*"]'::jsonb,
 '{"id":"mixpanel","name":"Mixpanel","category":"analytics","consent_type":"statistics","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Produkt-Analytics Plattform für Event-Tracking","description_en":"Product analytics platform for event tracking","cookies":["mp_*"],"domains":["mixpanel.com"],"cookie_lifetime":"1 Jahr","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://mixpanel.com/legal/privacy-policy","content_blocker_rules":[{"type":"script_src","pattern":"cdn.mxpnl.com"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('amplitude', 'Amplitude', 'analytics', 'Amplitude Inc.', 'Digital Analytics Plattform', '["amplitude_id_*"]'::jsonb,
 '{"id":"amplitude","name":"Amplitude","category":"analytics","consent_type":"statistics","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Digitale Analytics-Plattform für Nutzerverhalten","description_en":"Digital analytics platform for user behavior","cookies":["amplitude_id_*"],"domains":["amplitude.com"],"cookie_lifetime":"1 Jahr","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://amplitude.com/privacy","content_blocker_rules":[{"type":"script_src","pattern":"cdn.amplitude.com"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('piwik_pro', 'Piwik PRO', 'analytics', 'Piwik PRO', 'DSGVO-konforme Analytics-Plattform', '["_pk_id.*","_pk_ses.*","_pk_ref.*"]'::jsonb,
 '{"id":"piwik_pro","name":"Piwik PRO","category":"analytics","consent_type":"statistics","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"DSGVO-konforme Analytics-Plattform aus der EU","description_en":"GDPR-compliant analytics platform from the EU","cookies":["_pk_id.*","_pk_ses.*"],"domains":["piwik.pro"],"cookie_lifetime":"13 Monate","data_processing_countries":["EU"],"privacy_policy_url":"https://piwik.pro/privacy-policy","content_blocker_rules":[{"type":"script_src","pattern":"piwik.pro/ppms.php"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('segment', 'Segment', 'analytics', 'Twilio Segment', 'Customer Data Platform', '["ajs_anonymous_id","ajs_user_id","ajs_group_id"]'::jsonb,
 '{"id":"segment","name":"Segment","category":"analytics","consent_type":"statistics","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Customer Data Platform für Datenintegration","description_en":"Customer data platform for data integration","cookies":["ajs_anonymous_id","ajs_user_id"],"domains":["segment.com","segment.io"],"cookie_lifetime":"1 Jahr","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://segment.com/legal/privacy","content_blocker_rules":[{"type":"script_src","pattern":"cdn.segment.com"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

-- Functional
('hubspot', 'HubSpot', 'functional', 'HubSpot Inc.', 'CRM, Marketing und Live-Chat', '["hubspotutk","__hstc","__hssc","__hssrc","messagesUtk"]'::jsonb,
 '{"id":"hubspot","name":"HubSpot","category":"functional","consent_type":"marketing","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"CRM, Marketing-Automatisierung und Live-Chat von HubSpot","description_en":"CRM, marketing automation and live chat by HubSpot","cookies":["hubspotutk","__hstc","__hssc","__hssrc"],"domains":["hubspot.com","hs-scripts.com","hsforms.com"],"cookie_lifetime":"13 Monate","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://legal.hubspot.com/privacy-policy","content_blocker_rules":[{"type":"script_src","pattern":"js.hs-scripts.com"},{"type":"script_src","pattern":"js.hsforms.net"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('crisp', 'Crisp Chat', 'functional', 'Crisp IM S.A.S.', 'Live-Chat und Kundensupport', '["crisp-client/session/*"]'::jsonb,
 '{"id":"crisp","name":"Crisp Chat","category":"functional","consent_type":"functional","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Live-Chat und Kunden-Messaging von Crisp","description_en":"Live chat and customer messaging by Crisp","cookies":["crisp-client/session/*"],"domains":["crisp.chat","client.crisp.chat"],"cookie_lifetime":"Sitzung","data_processing_countries":["EU","USA"],"privacy_policy_url":"https://crisp.chat/en/privacy","content_blocker_rules":[{"type":"script_src","pattern":"client.crisp.chat/l.js"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('tawk_to', 'Tawk.to', 'functional', 'Tawk.to', 'Kostenloses Live-Chat Widget', '["Tawk_*","ss"]'::jsonb,
 '{"id":"tawk_to","name":"Tawk.to","category":"functional","consent_type":"functional","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Kostenloses Live-Chat Widget","description_en":"Free live chat widget","cookies":["Tawk_*"],"domains":["tawk.to","embed.tawk.to"],"cookie_lifetime":"Sitzung","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://www.tawk.to/privacy-policy","content_blocker_rules":[{"type":"script_src","pattern":"embed.tawk.to"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('google_recaptcha', 'Google reCAPTCHA', 'functional', 'Google LLC', 'Bot-Schutz und Spam-Prävention', '["_GRECAPTCHA","NID"]'::jsonb,
 '{"id":"google_recaptcha","name":"Google reCAPTCHA","category":"functional","consent_type":"functional","legal_basis":"Art. 6 Abs. 1 lit. f DSGVO (Berechtigtes Interesse)","description_de":"Bot-Schutz und SPAM-Prävention von Google","description_en":"Bot protection and spam prevention by Google","cookies":["_GRECAPTCHA","NID"],"domains":["google.com","recaptcha.net"],"cookie_lifetime":"6 Monate","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://policies.google.com/privacy","content_blocker_rules":[{"type":"script_src","pattern":"www.google.com/recaptcha"},{"type":"script_src","pattern":"recaptcha.net/recaptcha"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('cloudflare', 'Cloudflare', 'functional', 'Cloudflare Inc.', 'CDN, Sicherheit und Performance', '["__cf_bm","__cflb","cf_clearance","__cfruid"]'::jsonb,
 '{"id":"cloudflare","name":"Cloudflare","category":"functional","consent_type":"necessary","legal_basis":"Art. 6 Abs. 1 lit. f DSGVO (Berechtigtes Interesse)","description_de":"CDN, Sicherheit und Performance-Optimierung","description_en":"CDN, security and performance optimization","cookies":["__cf_bm","cf_clearance"],"domains":["cloudflare.com"],"cookie_lifetime":"30 Minuten","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://www.cloudflare.com/privacypolicy","content_blocker_rules":[]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('typeform', 'Typeform', 'functional', 'Typeform S.L.', 'Online-Formular und Umfrage-Tool', '["__cf_bm"]'::jsonb,
 '{"id":"typeform","name":"Typeform","category":"functional","consent_type":"functional","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Online-Formulare und Umfragen von Typeform","description_en":"Online forms and surveys by Typeform","cookies":["__cf_bm"],"domains":["typeform.com","form.typeform.com"],"cookie_lifetime":"Sitzung","data_processing_countries":["USA","EU"],"privacy_policy_url":"https://www.typeform.com/help/a/typeforms-privacy-policy","content_blocker_rules":[{"type":"script_src","pattern":"embed.typeform.com"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('calendly', 'Calendly', 'functional', 'Calendly LLC', 'Online-Terminplanung', '[]'::jsonb,
 '{"id":"calendly","name":"Calendly","category":"functional","consent_type":"functional","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Online-Terminplanungs-Tool","description_en":"Online appointment scheduling tool","cookies":[],"domains":["calendly.com","assets.calendly.com"],"cookie_lifetime":"Sitzung","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://calendly.com/privacy","content_blocker_rules":[{"type":"script_src","pattern":"assets.calendly.com/assets/external/widget.js"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('youtube_embedded', 'YouTube (eingebettet)', 'functional', 'Google LLC', 'Eingebettete YouTube-Videos', '["YSC","VISITOR_INFO1_LIVE","GPS","PREF"]'::jsonb,
 '{"id":"youtube_embedded","name":"YouTube (eingebettet)","category":"functional","consent_type":"marketing","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Eingebettete YouTube-Videos auf der Website","description_en":"Embedded YouTube videos on the website","cookies":["YSC","VISITOR_INFO1_LIVE","GPS","PREF"],"domains":["youtube.com","youtube-nocookie.com","ytimg.com"],"cookie_lifetime":"2 Jahre","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://policies.google.com/privacy","content_blocker_rules":[{"type":"script_src","pattern":"www.youtube.com/iframe_api"},{"type":"iframe_src","pattern":"youtube.com/embed"},{"type":"iframe_src","pattern":"youtube-nocookie.com/embed"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

-- Marketing
('google_doubleclick', 'Google DoubleClick / Display Ads', 'marketing', 'Google LLC', 'Display-Werbung und Remarketing', '["__gads","__gpi","IDE","DSID","NID"]'::jsonb,
 '{"id":"google_doubleclick","name":"Google DoubleClick / Display Ads","category":"marketing","consent_type":"marketing","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Google Display-Werbung und Remarketing","description_en":"Google display advertising and remarketing","cookies":["__gads","__gpi","IDE","DSID"],"domains":["doubleclick.net","googleadservices.com"],"cookie_lifetime":"13 Monate","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://policies.google.com/privacy","content_blocker_rules":[{"type":"script_src","pattern":"googleadservices.com/pagead"},{"type":"script_src","pattern":"doubleclick.net"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('pinterest_tag', 'Pinterest Tag', 'marketing', 'Pinterest Inc.', 'Pinterest Conversion-Tracking und Werbung', '["_pinterest_cm","_pinterest_ct_ua","_pinterest_sess"]'::jsonb,
 '{"id":"pinterest_tag","name":"Pinterest Tag","category":"marketing","consent_type":"marketing","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Pinterest Conversion-Tracking und Retargeting","description_en":"Pinterest conversion tracking and retargeting","cookies":["_pinterest_cm","_pinterest_ct_ua"],"domains":["pinterest.com","ct.pinterest.com"],"cookie_lifetime":"1 Jahr","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://policy.pinterest.com/de/privacy-policy","content_blocker_rules":[{"type":"script_src","pattern":"s.pinimg.com/ct/core.js"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('snapchat_pixel', 'Snapchat Pixel', 'marketing', 'Snap Inc.', 'Snapchat Ads Conversion-Tracking', '["sc_at","_schn","_scid"]'::jsonb,
 '{"id":"snapchat_pixel","name":"Snapchat Pixel","category":"marketing","consent_type":"marketing","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Snapchat Ads Conversion-Tracking und Retargeting","description_en":"Snapchat ads conversion tracking and retargeting","cookies":["sc_at","_schn","_scid"],"domains":["snapchat.com","tr.snapchat.com"],"cookie_lifetime":"1 Jahr","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://snap.com/de-DE/privacy/privacy-policy","content_blocker_rules":[{"type":"script_src","pattern":"sc-static.net/scevent.min.js"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('microsoft_ads', 'Microsoft Advertising (Bing Ads)', 'marketing', 'Microsoft Corporation', 'Bing Ads und UET-Tag', '["_uetmsclkid","_uetsid","_uetvid","MR","MUID","MSPTC"]'::jsonb,
 '{"id":"microsoft_ads","name":"Microsoft Advertising (Bing Ads)","category":"marketing","consent_type":"marketing","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Microsoft/Bing Werbung und Universal Event Tracking","description_en":"Microsoft/Bing advertising and Universal Event Tracking","cookies":["_uetmsclkid","_uetsid","_uetvid","MUID"],"domains":["bing.com","bat.bing.com","clarity.ms"],"cookie_lifetime":"13 Monate","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://privacy.microsoft.com/de-de/privacystatement","content_blocker_rules":[{"type":"script_src","pattern":"bat.bing.com/bat.js"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('klaviyo', 'Klaviyo', 'marketing', 'Klaviyo Inc.', 'E-Mail Marketing und Automatisierung', '["__kla_id"]'::jsonb,
 '{"id":"klaviyo","name":"Klaviyo","category":"marketing","consent_type":"marketing","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"E-Mail Marketing und Marketing-Automatisierung","description_en":"Email marketing and marketing automation","cookies":["__kla_id"],"domains":["klaviyo.com","a.klaviyo.com"],"cookie_lifetime":"2 Jahre","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://www.klaviyo.com/legal/privacy-notice","content_blocker_rules":[{"type":"script_src","pattern":"static.klaviyo.com/onsite/js/klaviyo.js"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('reddit_pixel', 'Reddit Pixel', 'marketing', 'Reddit Inc.', 'Reddit Ads Conversion-Tracking', '["_rdt_uuid","reddaid"]'::jsonb,
 '{"id":"reddit_pixel","name":"Reddit Pixel","category":"marketing","consent_type":"marketing","legal_basis":"Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)","description_de":"Reddit Ads Conversion-Tracking und Retargeting","description_en":"Reddit ads conversion tracking and retargeting","cookies":["_rdt_uuid","reddaid"],"domains":["reddit.com","redd.it"],"cookie_lifetime":"2 Jahre","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://www.reddit.com/policies/privacy-policy","content_blocker_rules":[{"type":"script_src","pattern":"www.redditstatic.com/ads/pixel.js"}]}'::jsonb,
 true, 'ai', NOW(), NOW()),

-- Necessary
('paypal', 'PayPal', 'necessary', 'PayPal Inc.', 'Online-Zahlungsabwicklung', '["PREF","NID","ts","tsrce","x-pp-s"]'::jsonb,
 '{"id":"paypal","name":"PayPal","category":"necessary","consent_type":"necessary","legal_basis":"Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung)","description_de":"Online-Zahlungsabwicklung über PayPal","description_en":"Online payment processing via PayPal","cookies":["ts","tsrce","x-pp-s"],"domains":["paypal.com","paypalobjects.com"],"cookie_lifetime":"Sitzung","data_processing_countries":["USA"],"adequacy_decision":"EU-US Data Privacy Framework","privacy_policy_url":"https://www.paypal.com/de/webapps/mpp/ua/privacy-full","content_blocker_rules":[]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('session_cookie', 'Session-Cookie', 'necessary', 'Eigener Betrieb', 'Technisch notwendiges Session-Cookie', '["session","sessionid","PHPSESSID","connect.sid"]'::jsonb,
 '{"id":"session_cookie","name":"Session-Cookie","category":"necessary","consent_type":"necessary","legal_basis":"Art. 6 Abs. 1 lit. f DSGVO (Berechtigtes Interesse)","description_de":"Technisch notwendiges Cookie für Benutzer-Sitzungen","description_en":"Technically necessary cookie for user sessions","cookies":["session","sessionid","PHPSESSID","connect.sid"],"domains":[],"cookie_lifetime":"Sitzung","data_processing_countries":[],"privacy_policy_url":"","content_blocker_rules":[]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('csrf_protection', 'CSRF-Schutz', 'necessary', 'Eigener Betrieb', 'Schutz vor Cross-Site-Request-Forgery Angriffen', '["csrftoken","_csrf","XSRF-TOKEN"]'::jsonb,
 '{"id":"csrf_protection","name":"CSRF-Schutz","category":"necessary","consent_type":"necessary","legal_basis":"Art. 6 Abs. 1 lit. f DSGVO (Berechtigtes Interesse)","description_de":"Sicherheits-Cookie zum Schutz vor CSRF-Angriffen","description_en":"Security cookie to protect against CSRF attacks","cookies":["csrftoken","_csrf","XSRF-TOKEN"],"domains":[],"cookie_lifetime":"Sitzung","data_processing_countries":[],"privacy_policy_url":"","content_blocker_rules":[]}'::jsonb,
 true, 'ai', NOW(), NOW()),

('mollie', 'Mollie Payments', 'necessary', 'Mollie B.V.', 'Online-Zahlungsabwicklung (EU)', '[]'::jsonb,
 '{"id":"mollie","name":"Mollie Payments","category":"necessary","consent_type":"necessary","legal_basis":"Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung)","description_de":"Online-Zahlungsabwicklung über Mollie (EU-Anbieter)","description_en":"Online payment processing via Mollie (EU provider)","cookies":[],"domains":["mollie.com","www.mollie.com"],"cookie_lifetime":"Sitzung","data_processing_countries":["NL"],"privacy_policy_url":"https://www.mollie.com/de/privacy","content_blocker_rules":[]}'::jsonb,
 true, 'ai', NOW(), NOW())

ON CONFLICT (service_key) DO NOTHING;
