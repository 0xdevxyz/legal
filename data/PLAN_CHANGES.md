# Plan-Änderungen — Stand 2026-05-01

## Neue Pläne

| Plan-Key | Name | Monatlich | Jährlich | Domains | Säulen |
|----------|------|-----------|----------|---------|--------|
| `free` | Kostenlos | 0 € | — | 1 | 1 Fix |
| `single` | Einzelne Säule | 19 € | — | 1 | 1 nach Wahl |
| `pro` | Pro-Paket | 49 € | 490 € | 1 | alle 4 |
| `agency` | Agentur | 299 € | 2.990 € | 25 | alle 4 |

## Alte Pläne (entfernt)

- `ai` / `AI Plan` (39 €) → ersetzt durch `pro` (49 €)
- `complete` / `Komplett-Paket` (49 €) → umbenannt zu `pro`
- `expert` / `Expertenservice` (2.990 € + 39 €/Mo) → entfernt

## Geänderte Dateien

| Datei | Änderung |
|-------|---------|
| `backend/stripe_routes.py` | STRIPE_PRICES + PLAN_WEBSITES_MAX |
| `backend/payment_routes.py` | Preise, Plan-Validierung, Checkout-Logic |
| `backend/init_user_limits.sql` | Default plan_type: `ai` → `free` |
| `backend/create_subscription_plans.sql` | Neue Plan-Einträge |
| `dashboard-react/src/contexts/AuthContext.tsx` | plan_type Union Type |
| `dashboard-react/src/app/subscription/page.tsx` | PLAN_LABELS |
| `dashboard-react/src/app/register/page.tsx` | Preisberechnung, Plan-Namen |
| `landing-react/src/components/modern-landing/PricingModern.tsx` | Pricing Cards |

## Hinweis: Stripe Dashboard

Folgende Price-IDs müssen in Stripe angelegt und in `.env` eingetragen werden:

```env
STRIPE_PRICE_SINGLE_MODULE=price_...    # 19€/Monat
STRIPE_PRICE_PRO_MONTHLY=price_...      # 49€/Monat
STRIPE_PRICE_PRO_YEARLY=price_...       # 490€/Jahr
STRIPE_PRICE_AGENCY_MONTHLY=price_...   # 299€/Monat
STRIPE_PRICE_AGENCY_YEARLY=price_...    # 2.990€/Jahr
```
