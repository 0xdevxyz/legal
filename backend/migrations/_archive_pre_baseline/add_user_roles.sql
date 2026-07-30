-- Migration: add_user_roles.sql
-- Phase 1 - Backend Auth-Hardening
-- Datum: 2026-05-22

BEGIN;

-- Add role column to users table
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'customer'
  CHECK (role IN ('admin', 'agency', 'customer'));

-- All existing users get role='customer'
UPDATE users SET role = 'customer' WHERE role IS NULL OR role NOT IN ('admin', 'agency', 'customer');

-- Index for role-based queries
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);

-- Instructions after migration:
-- Set admin user:
-- UPDATE users SET role = 'admin' WHERE email = 'YOUR_ADMIN_EMAIL';

COMMIT;
