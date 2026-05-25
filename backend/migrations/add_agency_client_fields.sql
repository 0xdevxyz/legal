-- Migration: Agency client attribution + logo storage (Phase 10 / AGENCY-01 + AGENCY-03)
-- Adds: cookie_banner_configs.client_name, client_email, index
--       users.agency_logo_path
-- Idempotent via IF NOT EXISTS

ALTER TABLE cookie_banner_configs
  ADD COLUMN IF NOT EXISTS client_name  VARCHAR(255),
  ADD COLUMN IF NOT EXISTS client_email VARCHAR(255);

COMMENT ON COLUMN cookie_banner_configs.client_name  IS 'Agency-facing client display name (Phase 10 AGENCY-01)';
COMMENT ON COLUMN cookie_banner_configs.client_email IS 'Agency-facing client contact email (Phase 10 AGENCY-01)';

-- Compound index for fast per-agency client grouping
CREATE INDEX IF NOT EXISTS idx_banner_config_user_client
  ON cookie_banner_configs(user_id, client_name)
  WHERE client_name IS NOT NULL;

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS agency_logo_path TEXT;

COMMENT ON COLUMN users.agency_logo_path IS 'Relative path under FILE_STORAGE_PATH to agency logo PNG (Phase 10 AGENCY-03)';
