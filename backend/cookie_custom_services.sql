-- ============================================================================
-- Custom Cookie Services (kundeneigene Dienst-Definitionen)
-- ============================================================================
-- Additiv & reversibel: legt ausschließlich eine neue Tabelle an, keine
-- Änderung an bestehenden Tabellen/Daten. Ermöglicht Kunden, eigene Dienste
-- (z. B. selten genutzte Tools) mit Domains/Cookies/Kategorie zu definieren,
-- analog zu Borlabs "Custom Cookies". service_key trägt das Präfix "custom_".
-- ============================================================================

CREATE TABLE IF NOT EXISTS cookie_custom_services (
    id              SERIAL PRIMARY KEY,
    site_id         VARCHAR(255) NOT NULL,
    user_id         INTEGER,
    service_key     VARCHAR(150) NOT NULL,
    name            VARCHAR(255) NOT NULL,
    category        VARCHAR(50)  NOT NULL DEFAULT 'functional',  -- necessary|functional|analytics|marketing
    provider        VARCHAR(255),
    description     TEXT,
    domains         JSONB NOT NULL DEFAULT '[]'::jsonb,
    cookies         JSONB NOT NULL DEFAULT '[]'::jsonb,
    legal_basis     TEXT,
    privacy_url     TEXT,
    cookie_lifetime VARCHAR(100),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (site_id, service_key)
);

CREATE INDEX IF NOT EXISTS idx_custom_services_site ON cookie_custom_services(site_id);
