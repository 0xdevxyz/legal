# Phase 5: Stripe-Path-Konsolidierung
Datum: 2026-05-22
Status: completed

## Root Cause
RC-7: Frontend `createCheckoutSession` rief `/api/v2/payments/create-checkout-session` auf.
Weitere `/api/v2/payments/*` Calls für Portal, Status, History, Plans.
Duplikate: `createStripeCheckout` (neu, korrekt) vs. `createCheckoutSession` (alt, falscher Pfad).

## Fixes

### dashboard-react/src/lib/api.ts
Alle `/api/v2/payments/` Pfade auf `/api/stripe/` konsolidiert:

| Alt | Neu |
|-----|-----|
| `/api/v2/payments/create-checkout-session` | `/api/stripe/create-checkout` |
| `/api/v2/payments/create-portal-session` | `/api/stripe/create-portal-session` |
| `/api/v2/payments/subscription-status` | `/api/stripe/subscription-status` |
| `/api/v2/payments/history` | `/api/stripe/payment-history` |
| `/api/v2/payments/plans` | `/api/stripe/plans` |

### backend/stripe_routes.py
Neue Endpoints ergänzt (fehlten im Router):
- `GET /api/stripe/subscription-status` — Subscription-Status aus DB
- `GET /api/stripe/payment-history` — Letzte 20 Subscriptions
- `GET /api/stripe/plans` — Verfügbare Plans mit Preisen

## Bestehende Funktionen unverändert
- `createStripeCheckout` (plan+billing_period API) — bereits korrekt auf `/api/stripe/create-checkout`
- `createStripePortal` — bereits korrekt auf `/api/stripe/create-portal-session`
- Webhook Handler `POST /api/stripe/webhook` — unverändert
