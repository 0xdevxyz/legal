-- Migration: UNIQUE Constraint auf subscriptions.stripe_subscription_id
-- Datum: 2026-05-23
-- Grund: ON CONFLICT (stripe_subscription_id) in stripe_routes.py:verify_checkout_session
--        benötigt einen UNIQUE-Constraint, der in der ursprünglichen Tabellendefinition fehlte.

ALTER TABLE subscriptions 
ADD CONSTRAINT uq_subscriptions_stripe_sub_id UNIQUE (stripe_subscription_id);
