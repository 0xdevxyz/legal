-- Migration: fix_cookie_compliance_stats.sql
-- Fixes BUG-01: site_identifier -> site_id, fehlende Spalten accepted_analytics/marketing/functional, updated_at
-- Applied: 2026-05-01

BEGIN;

ALTER TABLE cookie_compliance_stats RENAME COLUMN site_identifier TO site_id;
ALTER TABLE cookie_compliance_stats ADD COLUMN IF NOT EXISTS accepted_analytics INTEGER NOT NULL DEFAULT 0;
ALTER TABLE cookie_compliance_stats ADD COLUMN IF NOT EXISTS accepted_marketing INTEGER NOT NULL DEFAULT 0;
ALTER TABLE cookie_compliance_stats ADD COLUMN IF NOT EXISTS accepted_functional INTEGER NOT NULL DEFAULT 0;
ALTER TABLE cookie_compliance_stats ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

DROP INDEX IF EXISTS idx_cookie_stats_site;
CREATE UNIQUE INDEX idx_cookie_stats_site ON cookie_compliance_stats (site_id, date);

COMMIT;
