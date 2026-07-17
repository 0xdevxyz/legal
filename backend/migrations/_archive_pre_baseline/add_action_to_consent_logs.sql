-- Migration: add_action_to_consent_logs.sql
-- AUDIT-16: action Spalte für Consent Revocation (accept/revoke/update)
-- Applied: 2026-05-01

ALTER TABLE cookie_consent_logs ADD COLUMN IF NOT EXISTS action VARCHAR(20) DEFAULT 'accept' CHECK (action IN ('accept', 'revoke', 'update'));
