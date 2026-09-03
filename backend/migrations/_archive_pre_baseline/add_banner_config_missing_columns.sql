-- Fehlende Spalten in cookie_banner_configs ergänzen.
--
-- Diese Felder existierten im Pydantic-Model (BannerConfig) und wurden von
-- mehreren Endpoints referenziert (Consent-Mode v2, Banner-Designer, Import),
-- aber NICHT als DB-Spalten angelegt. Folge: Werte wurden beim Speichern still
-- verworfen bzw. die dedizierten Consent-Mode-Endpoints liefen auf 500
-- ("column does not exist").
--
-- Idempotent: IF NOT EXISTS, mehrfach ausführbar.

ALTER TABLE cookie_banner_configs
    ADD COLUMN IF NOT EXISTS consent_mode_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS consent_mode_default JSONB DEFAULT '{"ad_storage":"denied","analytics_storage":"denied","ad_user_data":"denied","ad_personalization":"denied"}'::jsonb,
    ADD COLUMN IF NOT EXISTS gtm_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS gtm_container_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS privacy_policy_url TEXT,
    ADD COLUMN IF NOT EXISTS cookie_policy_url TEXT,
    ADD COLUMN IF NOT EXISTS imprint_url TEXT;
