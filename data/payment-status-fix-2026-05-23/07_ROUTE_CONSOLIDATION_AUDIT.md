# Konsistenz-Audit: payment_routes.py vs stripe_routes.py

## Befund

Beide Routen sind aktiv in `main_production.py` registriert:

| Route | Prefix | Endpunkt |
|-------|--------|----------|
| `payment_routes.py` | `/api/payment` | `POST /create-checkout`, `POST /webhook`, `GET /subscription-status`, `GET /health` |
| `stripe_routes.py` | `/api/stripe` | `POST /create-checkout`, `POST /create-portal-session`, `GET /subscription-status`, `GET /verify-checkout` |

## Von der UI verwendete Route

**Alle** Frontend-Aufrufe gehen ausschließlich zu `/api/stripe/...`:

```
dashboard-react/src/lib/api.ts:332          → /api/stripe/create-checkout
dashboard-react/src/lib/api.ts:627          → /api/stripe/create-checkout
dashboard-react/src/components/SocialLoginButtons.tsx:61 → /api/stripe/create-checkout
dashboard-react/src/app/cookie-compliance/page.tsx:43   → /api/stripe/create-checkout
dashboard-react/src/app/agency/page.tsx:166             → /api/stripe/create-checkout
dashboard-react/src/app/subscription/page.tsx           → /api/stripe/create-checkout
dashboard-react/src/app/register/page.tsx:81            → /api/stripe/create-checkout
```

`/api/payment/create-checkout` wird von **keiner Frontend-Komponente** aufgerufen.

## Stripe-Webhook

`payment_routes.py:293` enthält `POST /api/payment/webhook`.
`stripe_routes.py` enthält **keinen** Webhook-Endpunkt.

→ Der Webhook läuft **weiterhin über `payment_routes.py`**. Das ist korrekt und darf nicht entfernt werden.

## Empfehlung (keine Aktion in diesem Fix-Lauf)

1. `payment_routes.py` auf folgende Endpunkte reduzieren (die tatsächlich noch gebraucht werden):
   - `POST /webhook` — bleibt aktiv
   - `GET /health` — kann bleiben
   - `POST /create-checkout` und `GET /subscription-status` mit `HTTP 410 Gone` oder `HTTP 301 → /api/stripe/...` versehen.

2. Referenz: `data/system-stabilization-2026-05-22/01_decisions/ADR-006-stripe-consolidation.md`

## Risiko ohne Änderung
Niedrig. Da kein Frontend-Code `/api/payment/create-checkout` aufruft, gibt es keine
Verwechslungsgefahr im normalen Betrieb. Webhook bleibt korrekt registriert.
