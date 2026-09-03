-- Migration: create_waitlist_leads
-- Erstellt: 2026-05-15
-- Zweck: Persistenzschicht für Early-Access Waitlist-Anmeldungen (Double-Opt-In, DSGVO-konform)

CREATE TABLE IF NOT EXISTS waitlist_leads (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                   VARCHAR(255) NOT NULL,
    name                    VARCHAR(120),
    phone                   VARCHAR(40),
    consent_given_at        TIMESTAMPTZ NOT NULL,
    confirmed_at            TIMESTAMPTZ,
    confirm_token           VARCHAR(64),
    confirm_token_expires_at TIMESTAMPTZ,
    source                  VARCHAR(40) NOT NULL DEFAULT 'early-access',
    ip_hash                 VARCHAR(64),
    user_agent              VARCHAR(500),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique constraint auf email (keine Duplikate, aber kein Fehler bei UPSERT)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'waitlist_leads_email_unique'
    ) THEN
        ALTER TABLE waitlist_leads
            ADD CONSTRAINT waitlist_leads_email_unique UNIQUE (email);
    END IF;
END
$$;

-- Unique constraint auf confirm_token
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'waitlist_leads_confirm_token_unique'
    ) THEN
        ALTER TABLE waitlist_leads
            ADD CONSTRAINT waitlist_leads_confirm_token_unique UNIQUE (confirm_token);
    END IF;
END
$$;

-- Indizes für häufige Queries
CREATE INDEX IF NOT EXISTS idx_waitlist_leads_email
    ON waitlist_leads (email);

CREATE INDEX IF NOT EXISTS idx_waitlist_leads_confirm_token
    ON waitlist_leads (confirm_token)
    WHERE confirm_token IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_waitlist_leads_created_at
    ON waitlist_leads (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_waitlist_leads_confirmed
    ON waitlist_leads (confirmed_at)
    WHERE confirmed_at IS NOT NULL;
