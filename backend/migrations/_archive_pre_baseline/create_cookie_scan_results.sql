-- Migration: Automated Cookie Scanner Results Table
-- Speichert die Ergebnisse des automatischen Playwright-Cookie-Scans

CREATE TABLE IF NOT EXISTS cookie_scan_results (
    id               BIGSERIAL PRIMARY KEY,
    site_id          TEXT        NOT NULL UNIQUE,
    url              TEXT        NOT NULL,
    scanned_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cookies          JSONB       NOT NULL DEFAULT '[]',
    services         JSONB       NOT NULL DEFAULT '[]',
    has_cmp          BOOLEAN     NOT NULL DEFAULT FALSE,
    cmp_name         TEXT,
    config_hash      TEXT,
    scan_duration_ms INTEGER,
    error            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cookie_scan_results_site_id    ON cookie_scan_results (site_id);
CREATE INDEX IF NOT EXISTS idx_cookie_scan_results_scanned_at ON cookie_scan_results (scanned_at DESC);

COMMENT ON TABLE  cookie_scan_results                  IS 'Ergebnisse des automatischen Playwright-Cookie-Scans';
COMMENT ON COLUMN cookie_scan_results.site_id          IS 'Eindeutige Site-ID (referenziert cookie_banner_configs)';
COMMENT ON COLUMN cookie_scan_results.cookies          IS 'JSONB-Array aller gefundenen Cookies mit Metadaten';
COMMENT ON COLUMN cookie_scan_results.services         IS 'JSONB-Array erkannter Tracking-Services';
COMMENT ON COLUMN cookie_scan_results.config_hash      IS 'SHA256-Hash des Scan-Ergebnisses – für Reconsent-Erkennung';
COMMENT ON COLUMN cookie_scan_results.has_cmp          IS 'True wenn ein CMP-Tool erkannt wurde';
