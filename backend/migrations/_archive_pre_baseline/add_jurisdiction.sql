-- ============================================================================
-- Jurisdiction-Fundament (Internationalisierung Stufe 1: de + eu)
-- Account-Default auf user_limits, Pro-Site-Override auf tracked_websites
-- (NULL = Account-Default erben). Idempotent — wird bei jedem Deploy ensured.
-- ============================================================================

ALTER TABLE user_limits
    ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR(10) NOT NULL DEFAULT 'de';

ALTER TABLE tracked_websites
    ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR(10) DEFAULT NULL;

COMMENT ON COLUMN user_limits.jurisdiction IS
    'Account-Default-Rechtsraum (de | eu), Stufe 1 Internationalisierung';
COMMENT ON COLUMN tracked_websites.jurisdiction IS
    'Pro-Site-Override des Rechtsraums; NULL = Account-Default aus user_limits erben';
