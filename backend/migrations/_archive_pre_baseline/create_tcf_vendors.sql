-- Migration: create_tcf_vendors.sql
-- Creates tcf_vendors table for IAB TCF 2.2 Global Vendor List
-- Run: docker exec complyo-postgres psql -U complyo_user -d complyo_db -f /migrations/create_tcf_vendors.sql

BEGIN;

CREATE TABLE IF NOT EXISTS tcf_vendors (
    vendor_id            INTEGER PRIMARY KEY,
    name                 TEXT NOT NULL,
    purposes             INTEGER[] DEFAULT '{}',
    legitimate_interests INTEGER[] DEFAULT '{}',
    special_purposes     INTEGER[] DEFAULT '{}',
    features             INTEGER[] DEFAULT '{}',
    special_features     INTEGER[] DEFAULT '{}',
    policy_url           TEXT,
    is_active            BOOLEAN NOT NULL DEFAULT true,
    last_updated         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tcf_vendors_active ON tcf_vendors (is_active);
CREATE INDEX IF NOT EXISTS idx_tcf_vendors_name ON tcf_vendors (name);

COMMIT;
