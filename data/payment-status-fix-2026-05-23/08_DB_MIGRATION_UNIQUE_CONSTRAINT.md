# Migration: UNIQUE Constraint auf subscriptions.stripe_subscription_id

## Problem

`verify-checkout` schlug mit **500 Internal Server Error** fehl:

```
asyncpg.exceptions.InvalidColumnReferenceError: 
there is no unique or exclusion constraint matching the ON CONFLICT specification
```

Die `INSERT ... ON CONFLICT (stripe_subscription_id)` Anweisung in `stripe_routes.py:401`
setzt einen UNIQUE-Constraint auf `stripe_subscription_id` voraus, der in der DB fehlte.

Die Tabelle hatte nur einen normalen `btree`-Index (`idx_subscriptions_stripe`), 
keinen UNIQUE-Constraint.

## Fix

```sql
ALTER TABLE subscriptions 
ADD CONSTRAINT uq_subscriptions_stripe_sub_id UNIQUE (stripe_subscription_id);
```

**Ausgeführt:** 2026-05-23 direkt via `docker exec complyo-postgres psql ...`

## Verifiziert

```
"uq_subscriptions_stripe_sub_id" UNIQUE CONSTRAINT, btree (stripe_subscription_id)
```

## Hinweis für künftige Deployments

Dieser Constraint fehlt in allen bisherigen `CREATE TABLE`-Migrations-Skripten.
Er sollte in eine neue Migrations-Datei aufgenommen werden:
`backend/migrations/add_unique_stripe_subscription_id.sql`
