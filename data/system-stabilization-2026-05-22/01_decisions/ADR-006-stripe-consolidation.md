# ADR-006: Stripe-Path-Konsolidierung

Datum: 2026-05-22
Status: Accepted

## Context
RC-7: Frontend createCheckoutSession ruft /api/v2/payments/create-checkout-session auf.
Dieser Pfad existiert nicht. Backend hat /api/stripe/create-checkout.
Inkonsistenz zwischen frontend api.ts und backend stripe_routes.py.

## Decision
Alle Stripe-Calls im Frontend auf /api/stripe/* konsolidieren.
Neue Backend-Endpoints ergänzen falls fehlend: subscription-status, payment-history, plans.

## Consequences
- api.ts/api-client.ts: createCheckoutSession → /api/stripe/create-checkout
- createPortalSession → /api/stripe/create-portal
- getSubscriptionStatus → /api/stripe/subscription-status (neu in backend falls fehlend)
- SubscriptionPlans.tsx, StripePaywallModal.tsx anpassen
