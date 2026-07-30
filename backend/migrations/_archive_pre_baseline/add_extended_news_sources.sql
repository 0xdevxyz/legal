-- Migration: Erweiterte RSS-Feed-Quellen (offizielle Behörden + Fachmedien)
-- Datum: 2026-04-22
-- Beschreibung: Fügt weitere verlässliche Quellen hinzu, unabhängig von eRecht24

INSERT INTO rss_feed_sources (name, url, category, keywords, fetch_frequency_hours) VALUES

-- ===== OFFIZIELLE BEHÖRDEN / EU =====

-- Europäischer Datenschutzausschuss (EDPB)
('EDPB News', 'https://www.edpb.europa.eu/news/news_en.rss', 'Datenschutz-Behörde', ARRAY['DSGVO', 'GDPR', 'Datenschutz', 'Bußgeld', 'Leitlinien', 'Beschluss', 'Stellungnahme'], 4),

-- Europäisches Parlament - Bürgerrechte / Digitales
('EU Parlament Digitales', 'https://www.europarl.europa.eu/rss/doc/top-stories/de.xml', 'EU-Gesetzgebung', ARRAY['Datenschutz', 'DSGVO', 'AI Act', 'DSA', 'DMA', 'Digital Services Act', 'Barrierefreiheit', 'Verordnung'], 8),

-- Bundesnetzagentur (Telemedien/TTDSG)
('Bundesnetzagentur Pressemitteilungen', 'https://www.bundesnetzagentur.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/RSSNewsfeed_Presse.xml', 'Telemedien', ARRAY['TTDSG', 'Telekommunikation', 'Cookie', 'Tracking', 'Verbraucherschutz'], 8),

-- Bundesministerium für Justiz (BMJ) - Gesetzgebung
('BMJ Pressemitteilungen', 'https://www.bmj.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/RSSNewsfeed_Presse.xml', 'Bundesgesetzgebung', ARRAY['Datenschutz', 'Verbraucherschutz', 'AGB', 'Impressum', 'E-Commerce', 'Digitales', 'Barrierefreiheit'], 8),

-- Landesbeauftragte für Datenschutz Bayern (BayLDA) - sehr aktiv mit Praxisurteilen
('BayLDA Datenschutz', 'https://www.lda.bayern.de/de/rss.xml', 'Datenschutz-Behörde', ARRAY['DSGVO', 'Datenschutz', 'Bußgeld', 'Cookie', 'Tracking', 'Bescheid', 'Aufsichtsbehörde'], 4),

-- LfDI Baden-Württemberg
('LfDI Baden-Württemberg', 'https://www.baden-wuerttemberg.datenschutz.de/rss.xml', 'Datenschutz-Behörde', ARRAY['DSGVO', 'Datenschutz', 'Cookie', 'Bußgeld', 'Orientierungshilfe'], 6),

-- ===== FACHMEDIEN / JURISTISCHE QUELLEN =====

-- Datenschutz.org - Praxisnahe Urteile & Erklärungen
('Datenschutz.org', 'https://www.datenschutz.org/feed/', 'Datenschutz-Praxis', ARRAY['DSGVO', 'Datenschutz', 'Cookie', 'Impressum', 'Datenschutzerklärung', 'Urteil'], 6),

-- Kanzlei Schwenke - sehr präzise DSGVO-Praxis
('Datenschutz-Praxis (Dr. Schwenke)', 'https://datenschutz-praxis.de/feed/', 'Datenschutz-Praxis', ARRAY['DSGVO', 'Datenschutz', 'Cookie Consent', 'Tracking', 'Auftragsverarbeitung', 'Newsletter'], 6),

-- Legal Tribune Online (LTO) - Urteile & Gesetze
('Legal Tribune Online', 'https://www.lto.de/feeds/rss/', 'Rechtsprechung', ARRAY['Datenschutz', 'DSGVO', 'IT-Recht', 'E-Commerce', 'Impressum', 'Verbraucherschutz', 'Urteil'], 8),

-- Netzpolitik.org - Digitalpolitik & Datenschutz
('Netzpolitik.org', 'https://netzpolitik.org/feed/', 'Digitalpolitik', ARRAY['Datenschutz', 'DSGVO', 'Überwachung', 'AI Act', 'DSA', 'Tracking', 'Cookie'], 8),

-- WBS Law - Praxistipps Internetrecht
('WBS Law', 'https://www.wbs.legal/feed/', 'Internetrecht', ARRAY['Datenschutz', 'DSGVO', 'Impressum', 'AGB', 'Cookie', 'Urteil', 'Widerrufsrecht'], 8),

-- ===== BARRIEREFREIHEIT (BFSG / WCAG) =====

-- BFIT-Bund (Kompetenzzentrum Barrierefreiheit IT)
('BFIT-Bund', 'https://www.bfit-bund.de/DE/service/rss/rss_node.xml', 'Barrierefreiheit', ARRAY['Barrierefreiheit', 'BFSG', 'WCAG', 'Accessibility', 'BITVTest', 'EN 301 549'], 8),

-- Aktion Mensch - Barrierefreiheit im Netz
('Aktion Mensch Barrierefreiheit', 'https://www.aktion-mensch.de/inklusion/barrierefreiheit/aktuelles.rss', 'Barrierefreiheit', ARRAY['Barrierefreiheit', 'BFSG', 'WCAG', 'Inklusion', 'Accessibility'], 24)

ON CONFLICT (url) DO UPDATE SET
    keywords = EXCLUDED.keywords,
    fetch_frequency_hours = EXCLUDED.fetch_frequency_hours,
    updated_at = CURRENT_TIMESTAMP;
