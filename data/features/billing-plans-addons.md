# Abos, Pläne & Add-ons (Stripe)

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit

## Ziel
Freemium → bezahlter Plan über Stripe: Checkout, Webhook-Aktivierung, Self-Service-Portal,
Plan-Gating der Premium-Features und separat kaufbare Add-ons (ComplyoAI Guard, Priority
Support, Extra-Sites). Der Plan (`plan_type`) und das Website-Kontingent (`websites_max`)
sind die zwei Größen, gegen die alle anderen Features gaten.

## Architektur (end-to-end)
- **Drei Payment-Router — alle drei in `backend/main_production.py` registriert:**
  - `backend/stripe_routes.py` → `/api/stripe/*` (Zeile 612) — **der aktive Router.**
    Alle Dashboard-Aufrufe gehen hierher (`dashboard-react/src/lib/api.ts`,
    `src/app/subscription/page.tsx`, `src/app/agency/page.tsx`, `src/app/register/page.tsx`,
    `src/components/SocialLoginButtons.tsx`, `src/app/cookie-compliance/page.tsx`).
  - `backend/payment_routes.py` → `/api/payment/*` (Zeile 611) — **Legacy, aber live.**
    Eigenes Plan-/Modul-Modell (`single`/`complete`/`expert`/`update`, `ALL_MODULES`), nutzt
    `payment/stripe_service.py` via Globals (Zeilen 567–569). **Kein Frontend-Aufruf gefunden**
    → toter Pfad mit offenem Webhook.
  - `backend/main_production.py` Zeilen 1809–1897 → `/api/v2/payments/*` (inline `@app.post`,
    kein Router) — dritter Satz über `payment/stripe_service.py`. Ebenfalls **kein
    Frontend-Aufruf**. `create-checkout-session` / `create-portal-session` /
    `subscription-status` / `history` / `plans` / `webhook`.
  - `backend/addon_payment_routes.py` → `/api/addons/*` (Zeile 617) — **aktiv**, aber ein
    eigenständiges Modell (Add-ons, nicht Basispläne).
  - Ursache: drei Generationen (v2-Inline → `payment_routes` → `stripe_routes` „Freemium").
    Es wurde nie aufgeräumt. **Zu tun:** `payment_routes` + `/api/v2/payments/*` entfernen.
- **Flow (aktiver Pfad):**
  1. Signup/Upgrade → Dashboard `POST /api/stripe/create-checkout` (`stripe_routes.py:176`)
     mit `{plan, billing_period, domain?, success_url, cancel_url}`. Preis-ID aus
     `STRIPE_PRICES` (Env), Fallback `pro_monthly`. Metadaten `user_id`/`plan`/`domain`.
  2. Stripe-Checkout → Webhook `POST /api/stripe/webhook` (`stripe_routes.py:478`),
     `checkout.session.completed` → `handle_checkout_completed` → `_apply_plan_activation`
     (`stripe_routes.py:99`).
  3. `_apply_plan_activation` = Single Source of Truth: setzt `user_limits.plan_type`,
     `fixes_limit`, `websites_max`, `exports_max` und schreibt den Ledger-Eintrag in
     `subscriptions` (`ON CONFLICT (stripe_subscription_id)`).
  4. Fallback ohne Webhook: `GET /api/stripe/verify-checkout?session_id=…`
     (`stripe_routes.py:387`) holt die Session aus Stripe, prüft `payment_status == 'paid'`
     und ruft denselben Helper. Die Success-Seite pollt mit Retries
     (`src/app/subscription/page.tsx:137`).
  5. Frontend-Plan: `plan_type` liegt im NextAuth-JWT (`dashboard-react/src/auth.config.ts`).
     Bei `trigger === "update"` zieht der JWT-Callback `GET /api/auth/session-info`
     (`backend/auth_routes.py:539`) frisch nach — ohne dieses Refresh bleibt der Plan auf dem
     Login-Wert stehen (Paywall trotz bezahltem Abo). `subscription/page.tsx` ruft nach
     erfolgreichem verify `updateSession()`.
  6. Gating im Backend liest `subscriptions.plan_type` / `user_limits.websites_max`
     (z. B. [[deep-cookie-scanner]]); im Frontend `session.user.plan_type`
     (`components/dashboard/OptimizationModeLock.tsx:33`, `StripePaywallModal.tsx` → Redirect
     auf `checkout_url`).
- **Portal & Historie:** `POST /api/stripe/create-portal-session` (`:298`),
  `GET /api/stripe/payment-history` (`:443`) — liest **nicht** Stripe-Invoices, sondern die
  letzten 20 `subscriptions`-Zeilen; es gibt keine `payments`-Tabelle.
- **Add-ons (separat):** `GET /api/addons/catalog`, `/my-addons`,
  `POST /subscribe/{key}` (monatlich, `:224`), `POST /purchase/{key}` (einmalig, `:295`),
  `POST /cancel/{key}` (`:353`), `POST /api/addons/webhook` (`:405`, eigenes Secret
  `STRIPE_WEBHOOK_SECRET_ADDONS`). Aktivierung → `db_service.create_user_addon` → Zeile in
  `user_addons`. Prüfung überall via `db_service.check_user_addon(user_id, key)`
  (`backend/database_service.py:367`: `status='active'` und `expires_at` NULL/zukünftig,
  fail-**closed** bei DB-Fehler). UI: `dashboard-react/src/app/dashboard/addons/page.tsx`
  über `src/lib/ai-compliance-api.ts`.
- **Widget-Lizenz zur Laufzeit:** `backend/license_check.py` — `site_has_active_license(pool,
  site_id)` prüft, ob zur `site_id` (abgeleitet per `url_to_site_id`, identisch zu
  `website_routes.py`) noch eine `tracked_websites`-Zeile des Owners existiert. Verhindert,
  dass Agenturen Sites löschen und Banner/Widget gratis weiterlaufen lassen. **Fail-open** bei
  fehlender Config oder DB-Fehler. Kein Bezug zu `plan_type` — nur Site-Existenz.

## Pläne & Limits
- Definiert **im Code** (`backend/stripe_routes.py`), Preise nur als Stripe-Price-IDs aus Env;
  die DB hält nur den Ist-Zustand pro User. Kein Plan-Katalog in der DB.
  - `free` — 0 €, `websites_max` 1, 1 Fix
  - `pro` — 49 €/Mon, 490 €/Jahr, `websites_max` 1, `fixes_limit` 999999
  - `agency` — 299 €/Mon, 2.990 €/Jahr, `websites_max` 25 → [[agentur-white-label]]
  - `single` (19 €/Mon, 1 Säule), `expert`, `update` — in `PLAN_WEBSITES_MAX` (je 1), aber
    **nicht** in `GET /api/stripe/plans` gelistet → im Dashboard nicht buchbar.
- **Agentur-Add-ons** (`ADDON_PLANS`, `stripe_routes.py:88`): `agency_extra` = +1 Website
  (19 €/Mon), `agency2` = +25 Websites. Sie erhöhen `websites_max` **additiv**;
  `plan_type` bleibt `agency`, auch der Ledger-Eintrag wird als `agency` geführt, damit
  `/subscription-status` weiterhin den Basisplan zeigt.
- Master-Account: `websites_max = -1` = unbegrenzt (Konvention, siehe [[deep-cookie-scanner]]).
- **Add-on-Katalog** (`addon_payment_routes.py:64/130`): monatlich `comploai_guard` (99 €,
  → [[ai-act-compliance]]), `priority_support` (49 €), `agency_sites_extra` (200 €, +25 Sites);
  einmalig `expert_ai_audit` (2.999 €), `implementation_support` (1.999 €),
  `custom_integration` (3.999 €) — One-Time löst nur eine Sales-Mail aus (`_notify_sales`).
- `DEV_MODE`/`BYPASS_PAYMENT` simulieren Zahlungen; Hard-Guard wirft beim Start, wenn eines
  davon mit `ENVIRONMENT=production` gesetzt ist (`stripe_routes.py:37`, `payment_routes.py:25`).

## DB
Schema-Referenz ist die Alembic-Baseline (`backend/alembic/baseline_schema.sql`, Revision
`backend/alembic/versions/20260717_baseline_2026_07.py`). Die 46 Altskripte unter
`backend/migrations/_archive_pre_baseline/` sind **nicht** mehr anzuwenden.
- `subscriptions` — Ledger je Stripe-Abo: `user_id`, `stripe_subscription_id` (unique →
  Idempotenz-Anker), `stripe_customer_id`, `plan_type`, `status`, Refund-Felder
  (`refund_eligible`, `refund_deadline`, `refund_*`), `fix_first_used_at`.
- `user_limits` — effektive Limits je User: `plan_type` (Default `'ai'`), `websites_count`,
  `websites_max`, `exports_this_month`/`exports_max`, `fixes_used`/`fixes_limit`,
  `locked_domain`, `money_back_eligible`, `jurisdiction` ([[jurisdiction-kontext]]).
- `user_addons` — `addon_key`, `addon_name`, `status`, `price_monthly`,
  `stripe_subscription_id`, `limits`/`usage` (JSONB → immer mit `json.dumps()` schreiben).
- **Keine** `payments`-/`invoices`-Tabelle; Zahlungshistorie = `subscriptions`.

## Bekannte Lücken / Offen
- **Drei parallele Payment-Pfade.** `payment_routes` (`/api/payment/*`) und die Inline-Routen
  `/api/v2/payments/*` sind ohne Frontend-Nutzer, aber öffentlich erreichbar und schreiben
  über `payment/stripe_service.py` in dieselben Tabellen — mit **anderem** Plan-Modell
  (`single`/`complete`/`expert`). Kollisionsgefahr; abzuschalten.
- **Keine Webhook-Idempotenz auf Event-Ebene.** Nirgends wird `event['id']` gespeichert/geprüft
  (keine `stripe_events`-Tabelle). Schutz besteht nur indirekt: `_apply_plan_activation` dedupt
  über `stripe_subscription_id` und liefert `False` bei Retries. Add-on-Webhook
  (`handle_addon_checkout_completed`) hat **keinen** solchen Schutz → doppelte Events können
  doppelte `user_addons`-Zeilen anlegen (zu prüfen, ob `create_user_addon` upsertet).
- **Add-on-Gate lückenhaft** (bestätigt): `check_user_addon("comploai_guard")` wird nur in
  `POST /systems` (`ai_compliance_routes.py:95`), `GET /systems` (`:169`) und `GET /stats`
  (`:607`) geprüft. Ungegated: `POST /systems/{id}/scan` (`:336`),
  `POST /systems/{id}/documentation/generate` (`:655`), `POST /systems/{id}/schedule` (`:1296`)
  sowie alle Detail-/Doku-Downloads → Nutzung nach Kündigung möglich. **Hohe Priorität**,
  Details in [[ai-act-compliance]].
- **[BEHOBEN 2026-07-17] `user_plan` war client-gesteuert (Rechteausweitung):**
  `POST /api/addons/subscribe/{key}` übernahm `AddAddonRequest.user_plan` aus dem Request-Body
  und leitete daraus `limits_by_plan` ab → Client konnte `"enterprise"` senden und sich
  `ai_systems: -1` (unbegrenzt) verschaffen. Fix: `user_plan` aus dem Body wird ignoriert; der
  Plan wird serverseitig über `resolve_addon_plan()` aus der neuesten `subscriptions`-Zeile
  gelesen (`PLAN_TYPE_TO_ADDON_PLAN`-Mapping; unbekannt → kleinster Satz `FALLBACK_ADDON_PLAN`).
  Abgesichert durch `tests/test_addon_plan_escalation.py`.
- **Plan-Namensraum inkonsistent:** Add-on-Katalog nutzt `starter`/`professional`/`business`/
  `enterprise`, die reale Welt `free`/`pro`/`agency`. `compatible_plans` matcht deshalb faktisch
  nie den echten `plan_type` — Auswirkung auf `/catalog`-Anzeige zu prüfen.
- **[BEHOBEN 2026-07-17] `agency_sites_extra` bumpte `websites_max` nicht.** Der Add-on-Webhook
  legte nur eine `user_addons`-Zeile mit `limits` an; `user_limits.websites_max` blieb
  unverändert (200 €/Monat ohne jede Wirkung). Fix: die Aktivierung erhöht `websites_max` jetzt
  additiv (`UPDATE user_limits SET websites_max = COALESCE(websites_max, 0) + extra_sites`),
  `plan_type` bleibt unverändert. (Zwei konkurrierende Mechanismen mit `stripe_routes`
  `agency2`/`agency_extra` bleiben ein offener Aufräumpunkt.)
- **Fallback-Preis-IDs:** fehlt eine Env-Price-ID, fällt `create-checkout` still auf
  `pro_monthly` zurück (`stripe_routes.py:246`) — Kunde zahlt den falschen Betrag. Add-on-
  Defaults sind Dummy-Strings (`"price_1234"`), die im Checkout hart fehlschlagen.
- **Kündigung/Downgrade:** `customer.subscription.deleted` setzt den Status; ob
  `user_limits.websites_max` dabei zurückgesetzt wird, ist **zu prüfen** —
  additive Add-on-Erhöhungen werden beim Wegfall des Add-ons vermutlich nicht abgezogen.
- Webhook-Signatur wird in **allen vier** Handlern via `stripe.Webhook.construct_event`
  geprüft (`stripe_routes.py:491`, `addon_payment_routes.py:418`, `payment_routes.py:290`,
  `main_production.py:1879`); die Secrets sind Pflicht-Env (Start bricht sonst ab). Keine Lücke.
- **JWT_SECRET-Rotation** (Server-Migration, Plan-Phase 5.2) invalidiert alle Sessions →
  `plan_type` wird nach Re-Login ohnehin frisch geholt, kein Billing-Risiko. Die Stripe-Keys
  (`STRIPE_SECRET_KEY`, beide Webhook-Secrets) müssen beim Umzug mitgenommen und die
  Webhook-Endpunkt-URLs im Stripe-Dashboard nachgezogen werden.
