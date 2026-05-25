# Payment Status Fix — 2026-05-23

## Problem
Nach erfolgreicher Stripe-Zahlung zeigt das Dashboard weiterhin „Unbekannt / Kostenlos" als Plan.
Der Verify-Checkout-Call schlägt mit 400 fehl.

## Dateien
| Datei | Inhalt |
|-------|--------|
| `01_BASELINE.md` | Ist-Zustand, Bugs, Reproduktion, betroffene Code-Stellen |
| `02_DECISIONS.md` | Architektur-Entscheidungen |
| `02_BACKEND_FIX.md` | Backend-Fix: doppelter Query-String |
| `03_FRONTEND_FIELD_MISMATCH.md` | Frontend-Fix: plan vs plan_type |
| `04_AUTH_REFRESH.md` | NextAuth-Session-Refresh |
| `05_URL_AND_BANNER.md` | URL säubern & Banner |
| `06_POLLING_FALLBACK.md` | Polling & Fehlerbehandlung |
| `07_ROUTE_CONSOLIDATION_AUDIT.md` | Audit: payment_routes vs stripe_routes |
| `99_FINAL_REPORT.md` | Abschlussbericht |

## Betroffene Dateien
- `backend/stripe_routes.py`
- `dashboard-react/src/app/subscription/page.tsx`
- `dashboard-react/src/contexts/AuthContext.tsx`
