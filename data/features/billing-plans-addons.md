# Abos, Pläne & Add-ons (Stripe)

**Stand:** 2026-09-28 · **Status:** 🟢 live (Kaufweg seit 14.09.2026; Add-on-Aktivierung und Webhook-Überkreuzung fehlerhaft, siehe Lücken)

## Ziel
Freemium zu bezahltem Plan über Stripe: Checkout, Webhook-Aktivierung, Self-Service-Portal,
Plan-Gating der Premium-Features und separat kaufbare Add-ons (ComploAI Guard, Priority
Support, Extra Sites, Einmal-Leistungen). Der Plan (`user_limits.plan_type`), die gebuchten
Säulen (`user_modules`) und das Website-Kontingent (`websites_max`) sind die Größen, gegen die
die anderen Features gaten.

## Live-Lage (gemessen 2026-09-28, nur lesend)
- Stripe läuft im **Live-Modus** (`STRIPE_SECRET_KEY` ist ein `sk_live_`-Schlüssel im Container
  `complyo-backend`). Live-Schaltung am 14.09.2026: 5f5b9d0, 1b6cd88, afe94c1, 308fdbf,
  Umschaltskript `scripts/stripe-live-umschalten.py` (fd0986a), Checkliste
  `planning/STRIPE_LIVE_CHECKLISTE.md`.
- Im Stripe-Konto: **0 Subscriptions** (auch keine gekündigten), Gutschein `early-access-12m`
  mit 0 Einlösungen. Es gab also noch keinen echten Kauf.
- Zwei Webhook-Endpunkte registriert und `enabled`:
  `https://api.complyo.de/api/stripe/webhook` (checkout.session.completed,
  customer.subscription.created/updated/deleted, invoice.payment_succeeded/failed) und
  `https://api.complyo.de/api/addons/webhook` (dieselben ohne customer.subscription.created).
- DB (`complyo-postgres`): `subscriptions` 3 Zeilen (agency/active, pro/active,
  free/cancelled), keine davon aus einem Stripe-Live-Kauf; `user_limits` 18 × free, 3 × agency;
  `user_addons` leer; `waitlist_leads` 1 Zeile, 0 bestätigte Plätze. Alembic-Kopf `0036_ki_erlaubnis`.

## Architektur (end-to-end)
- **Ein Bezahlweg für Pläne, einer für Add-ons** (ae26b04, 03.09.2026): `payment_routes.py`
  (`/api/payment/*`), `payment/stripe_service.py` und die Inline-Routen `/api/v2/payments/*` sind
  entfernt. Registriert in `backend/main_production.py`:
  - `backend/stripe_routes.py` → `/api/stripe/*` (Zeile 723): Pläne.
  - `backend/addon_payment_routes.py` → `/api/addons/*` (Zeile 728): Add-ons.
  - Frontend-Aufrufer: `dashboard-react/src/lib/api.ts`, `src/app/subscription/page.tsx`,
    `src/app/agency/page.tsx`, `src/app/register/page.tsx`, `src/app/cookie-compliance/page.tsx`,
    `src/components/SocialLoginButtons.tsx`; Add-ons über `src/lib/ai-compliance-api.ts`.
    Kein Frontend-Aufruf von `/api/payment/*` oder `/api/v2/payments/*` mehr.
- **Flow (Pläne):**
  1. `POST /api/stripe/create-checkout` (`stripe_routes.py:260`) mit
     `{plan, billing_period, modules, domain?, success_url, cancel_url}`.
     Plan-Whitelist `SELF_SERVE_PLANS` = `single`, `pro`, `agency`, `agency_extra`, `agency2`,
     `monitor` (`:134`, 67e5674, 2dfd072); anderes → 400. `billing_period` nur monthly/yearly.
     `single` braucht mindestens eine Säule, Menge = Anzahl Säulen.
     Preis-ID aus `STRIPE_PRICES[f"{plan}_{period}"]` (`:66`); fehlt sie → 500 "Dieser Tarif ist
     derzeit nicht buchbar" (`:390`), **kein Rückfall** auf einen anderen Preis.
  2. Keine fest verdrahteten Bezahlarten mehr (5f5b9d0): Stripe zeigt, was im Dashboard aktiv
     ist. `billing_address_collection='required'`, `locale='de'`. Ohne Gutschein
     `allow_promotion_codes=True`.
  3. **Early Access** (`:366`, 8fe5da3): nur `pro` monatlich, nur wenn die E-Mail einen
     bestätigten Wartelistenplatz `platz_nr <= EARLY_ACCESS_PLAETZE` (Env, 100) hält
     (`_hat_early_access_platz`, `:636`, fail-closed). Dann regulärer Pro-Preis plus Gutschein
     `STRIPE_COUPON_EARLY_ACCESS` = `early-access-12m` (Stripe: amount_off 40,00 EUR,
     duration repeating, 12 Monate). Fehlt der Gutschein, wird voll gebucht und laut geloggt.
     Der frühere eigene 49-Euro-Preis wird nicht mehr genutzt.
  4. Webhook `POST /api/stripe/webhook` (`:681`), Signatur via `stripe.Webhook.construct_event`.
     `checkout.session.completed` → `handle_checkout_completed` (`:733`) →
     `_apply_plan_activation` (`:162`). Fehler werden weitergereicht (500), damit Stripe
     wiederholt (1b6cd88).
  5. `_apply_plan_activation`: schaltet `user_modules` per UPSERT frei (`_resolve_modules`:
     pro/agency/expert/update alle vier Säulen, single die gewählten, monitor keine), setzt
     `user_limits.plan_type`, `fixes_limit=999999`, `websites_max` (`PLAN_WEBSITES_MAX`),
     `exports_max=999` und legt die Ledger-Zeile in `subscriptions` an. Existiert die
     `stripe_subscription_id` schon, nur Status auf active und Rückgabe `False`.
  6. Fallback ohne Webhook: `GET /api/stripe/verify-checkout?session_id=…` (`:556`), prüft
     `payment_status == 'paid'`, ruft denselben Helper. Success-Seite pollt
     (`src/app/subscription/page.tsx:137`) und ruft danach `updateSession()` (`:142`).
  7. Frontend-Plan im NextAuth-JWT (`dashboard-react/src/auth.config.ts:67`); bei
     `trigger === "update"` (`:104`) frisch aus `GET /api/auth/session-info`
     (`backend/auth_routes.py:730`). Säulen-Zugang serverseitig aus Tarif plus gebuchten Modulen
     (`backend/auth_service.py:50`, `_module_zugang`).
  8. Kündigung `customer.subscription.deleted` (`:831`): `user_limits` auf free
     (`websites_max=1`, `fixes_limit=1`, `exports_max=5`), Module **dieser** Subscription auf
     `cancelled`, Ledger `canceled` (1b6cd88).
- **CSRF:** `/api/stripe/webhook` und `/api/addons/webhook` stehen in `EXEMPT_PATHS`
  (`backend/csrf_middleware.py:56-57`, 1b6cd88); vorher wurde jeder Webhook mit 403 abgewiesen.
  Wächter `tests/test_webhook_csrf.py` prüft jede POST-Route mit "webhook" im Pfad.
- **Portal & Historie:** `POST /api/stripe/create-portal-session` (`:467`),
  `GET /api/stripe/subscription-status` (`:524`), `GET /api/stripe/payment-history` (`:614`,
  letzte 20 `subscriptions`-Zeilen, keine Stripe-Rechnungen).
- **Add-ons:** `GET /api/addons/catalog` (`addon_payment_routes.py:280`, je Eintrag `buchbar`
  = Preis-ID gesetzt, d8f5a8e), `/my-addons` (`:305`), `POST /subscribe/{key}` (`:319`),
  `POST /purchase/{key}` (`:408`, einmalig, löst nur Sales-Mail aus), `POST /cancel/{key}`
  (`:483`, `cancel_at_period_end`), `POST /api/addons/webhook` (`:535`, Secret
  `STRIPE_WEBHOOK_SECRET_ADDONS`). Stripe-Schlüssel jetzt `STRIPE_SECRET_KEY` (bebb832, `:60`).
  Plan für Add-on-Limits nur serverseitig über `resolve_addon_plan()` (`:237`), Body-Feld
  `user_plan` wirkungslos (`tests/test_addon_plan_escalation.py`). Aktivierung →
  `db_service.create_user_addon` (`backend/database_service.py:449`, UPSERT auf
  `(user_id, addon_key)`); Prüfung `check_user_addon` (`:390`, `status='active'` und
  `expires_at` NULL/zukünftig, fail-closed). Kündigung zieht `extra_sites` wieder von
  `websites_max` ab, Untergrenze 1, nur auf der aktiven Zeile (`:662`, 1b6cd88).
- **Widget-Lizenz zur Laufzeit:** `backend/license_check.py`, `evaluate_license()` (`:193`) mit
  Status `active` / `revoked` (Site im Dashboard gelöscht, blockt immer) /
  `unlicensed_domain` (Origin/Referer passt nicht zur gebuchten Domain, 03372ec; Subdomains der
  gebuchten Domain zählen mit, 4f14890). Durchsetzung über `COMPLYO_LICENSE_ENFORCEMENT`, live
  `warn`. Fail-open bei fehlenden Headern, DB-Fehler, unbekannter site_id. Kein Bezug zu
  `plan_type`.

## Pläne & Limits
- Definiert im Code (`backend/stripe_routes.py`), abgerechnet wird der Betrag des Stripe-Preises
  aus der Env. Anzeigebeträge stehen hart in `GET /api/stripe/plans` (`:666`). Beträge unten:
  Stripe-Live-Preisobjekte, gelesen 2026-09-28; sie stimmen mit der Anzeige überein.
  Preisrunde Weg B 07.09.2026 (589f2af).
  - `free`: 0 EUR, `websites_max` 1, 1 Fix, kein Checkout.
  - `monitor`: 39 EUR/Monat, 390 EUR/Jahr, `websites_max` 10, keine Säulen/Fixes (Tarif aus
    2dfd072 mit damals 19 EUR, seit 589f2af 39 EUR).
  - `pro`: 89 EUR/Monat, 890 EUR/Jahr, `websites_max` 1, alle vier Säulen.
    Early Access: 49 EUR/Monat für 12 Monate per Gutschein.
  - `agency`: 599 EUR/Monat, 5.990 EUR/Jahr, `websites_max` 25 → [[agentur-white-label]].
  - `single`: 29 EUR/Monat je Säule, nur monatlich; nicht in `/plans` gelistet, aber über
    Registrierung/Checkout buchbar.
  - `expert` (Stripe-Preis 3.990 EUR einmalig) und `update` (29 EUR/Monat): Preis-IDs gesetzt,
    aber **nicht** in `SELF_SERVE_PLANS` und ohne Schlüssel in `STRIPE_PRICES`, also nicht
    online buchbar. Expert läuft als Anfrage per Mail (`register/page.tsx:361ff`).
- **Agentur-Zusatzkontingent** (`ADDON_PLANS`, `stripe_routes.py:123`): `agency_extra` +1
  Website (Stripe 29 EUR/Monat), `agency2` +25 Websites (599 EUR/Monat bzw. 5.990 EUR/Jahr).
  Erhöhen `websites_max` additiv, Ledger wird als `agency` geführt. Jede Preis-ID hat ihre eigene
  Variable ohne Rückfall (afe94c1). Der Code-Kommentar an `ADDON_PLANS` nennt für
  `agency_extra` noch 19 EUR, gilt aber nicht.
- Master-Account: `websites_max = -1` = unbegrenzt (Konvention, siehe [[deep-cookie-scanner]]).
- **Add-on-Katalog** (`addon_payment_routes.py:69/145`), alle sechs laut `/catalog` live
  `buchbar: true`, Stripe-Beträge = Katalogbeträge: monatlich `comploai_guard` 99 EUR
  (→ [[ai-act-compliance]]), `priority_support` 89 EUR, `agency_sites_extra` 599 EUR (+25 Sites,
  308fdbf, gleich teuer wie `agency2`, Wächter `test_25_projekte_kosten_ueberall_gleich`);
  einmalig `expert_ai_audit` 2.999 EUR, `implementation_support` 1.999 EUR,
  `custom_integration` 3.999 EUR.
- `DEV_MODE`/`BYPASS_PAYMENT` simulieren Zahlungen; Hard-Guard wirft beim Start mit
  `ENVIRONMENT=production` (`stripe_routes.py:40`). Live: `ENVIRONMENT=production`, beide nicht
  gesetzt.
- Wächtertests: `test_checkout_plan_validation.py`, `test_stripe_namen.py`,
  `test_konfig_erreicht_code.py` (Env erreicht den Container), `test_kuendigung.py`,
  `test_wiederholung.py`, `test_webhook_csrf.py`, `test_addon_plan_escalation.py`,
  `test_license_enforcement.py`. Nicht selbst ausgeführt.

## DB
Schema-Referenz ist die Alembic-Kette unter `backend/alembic/versions/` (Kopf live
`0036_ki_erlaubnis`).
- `subscriptions`: Ledger je Stripe-Abo, `user_id` integer, `stripe_subscription_id` unique
  (Idempotenz-Anker), `stripe_customer_id`, `plan_type`, `status`, Refund-Felder.
- `user_limits`: effektive Limits je User, `plan_type` Default `'free'`, `websites_max`,
  `fixes_limit`, `exports_max`, `locked_domain` ([[jurisdiction-kontext]]).
- `user_modules`: gebuchte Säulen `(user_id, module_id)` unique, `status`,
  `stripe_subscription_id`, `cancelled_at`.
- `user_addons`: `user_id` **integer**, `addon_key`, `status`, `price_monthly`,
  `stripe_subscription_id`, `limits` (JSONB, mit `json.dumps()` schreiben).
- `waitlist_leads.platz_nr`: Anspruch auf Early Access.
- Keine `payments`-, `invoices`- oder `stripe_events`-Tabelle (live geprüft).

## Bekannte Lücken / Offen
- **Add-on-Kauf schaltet nichts frei (aus Code und Live-DB-Typ abgeleitet, kein Echtkauf
  gemessen).** `handle_addon_checkout_completed` (`addon_payment_routes.py:577`) reicht
  `user_id` als String aus der Stripe-Metadata an `create_user_addon` weiter; die Spalte ist
  integer, asyncpg wirft `DataError` (live nachgestellt mit lesendem SELECT), die Funktion
  fängt das und gibt `""` zurück. Der Webhook antwortet trotzdem 200. Folge: bezahltes
  ComploAI Guard / Priority Support ohne `user_addons`-Zeile, `check_user_addon` bleibt False.
  Nur der `extra_sites`-Zweig nutzt `int(user_id)` und würde greifen. Fix: `int(user_id)` wie
  in `_apply_plan_activation`.
- **Beide Webhook-Endpunkte bekommen jedes `checkout.session.completed` (live bestätigt).**
  - Add-on-Kauf am Plan-Webhook: Metadata ohne `plan` → `handle_checkout_completed` nimmt
    `'pro'` als Standard und setzt den Käufer auf `plan_type='pro'`, `websites_max=1`.
    Eine Agentur, die das Extra-Sites-Paket kauft, würde damit auf Pro und 1 Website gesetzt;
    ein Einmalkauf (ohne Subscription) schaltet ebenso Pro frei.
  - Plan-Kauf am Add-on-Webhook: `session['metadata']['addon_key']` wirft KeyError → 500,
    Stripe wiederholt drei Tage und meldet den Endpunkt als fehlerhaft.
  Fix: Handler filtern auf ihre eigene Metadata (`plan` bzw. `addon_key`) und ignorieren den
  Rest mit 200. Nicht gemessen, nur aus Code und Endpunkt-Konfiguration abgeleitet.
- **Kündigung eines Agentur-Zusatzkontingents stuft das ganze Konto ab.** `agency_extra` und
  `agency2` laufen als eigene Subscription im Plan-Webhook; `handle_subscription_deleted`
  unterscheidet nicht und setzt `plan_type='free'`, `websites_max=1`, obwohl das Agentur-Abo
  weiterläuft. Ebenso setzt die Kündigung des Basisplans pauschal `websites_max=1`, auch wenn
  daneben noch Kontingent-Abos laufen.
- **Reihenfolge `customer.subscription.created` vor `checkout.session.completed`.**
  `handle_subscription_created` (`stripe_routes.py:776`) legt die Ledger-Zeile mit festem
  `plan_type='pro'` an. Kommt dieses Ereignis zuerst, findet `_apply_plan_activation` die
  Subscription schon vor und kehrt zurück, **ohne** `user_limits` zu setzen (auch der
  verify-checkout-Fallback nicht). Folge: Säulen frei, aber `plan_type` bleibt free und
  `websites_max` 1; Agentur im Ledger als pro. Stripe garantiert keine Reihenfolge. Nicht live
  gemessen (der Test vom 14.09. nutzte signierte Einzelereignisse).
- **Keine Webhook-Idempotenz auf Event-Ebene.** Keine `stripe_events`-Tabelle. Plan-Weg dedupt
  über `stripe_subscription_id`; Add-on-Weg: die Zeile wird per UPSERT nicht verdoppelt, aber
  die `extra_sites`-Erhöhung von `websites_max` läuft bei jeder Wiederholung erneut.
- **Add-on-Gate lückenhaft** (unverändert): `check_user_addon("comploai_guard")` nur in
  `POST /systems` (`ai_compliance_routes.py:96`), `GET /systems` (`:170`), `GET /stats`
  (`:608`). Ungegated u. a. `POST /systems/{id}/scan` (`:337`),
  `POST /systems/{id}/documentation/generate` (`:656`), `POST /systems/{id}/schedule`
  (`:1297`) und die Doku-Downloads. Details in [[ai-act-compliance]].
- **Plan-Namensraum:** Add-on-Katalog nutzt `starter`/`professional`/`business`/`enterprise`,
  übersetzt über `PLAN_TYPE_TO_ADDON_PLAN` (`:214`); `compatible_plans` wird im Backend nicht
  zur Kaufsperre genutzt. Auswirkung auf die `/catalog`-Anzeige nicht geprüft.
- **`EARLY_ACCESS_ANGEBOT`:** `docker-compose.yml:207` setzt als Vorgabe noch
  `ea100-35eur-12m` (live gesetzt), `lead_routes.py:44` erwartet `ea100-49eur-12m`. Reines
  Etikett an der Wartelistenzeile, kein Preis; bereinigen.
- **Kommentare mit Altpreisen:** `stripe_routes.py:58-61` (49/299/19 EUR) und `:124`
  (`agency_extra` 19 EUR) widersprechen den gültigen Preisen.
- **Behoben seit 17.07.:** drei Bezahlwege auf einen (ae26b04); stiller Rückfall auf
  `pro_monthly` (67e5674, afe94c1); Platzhalter-Preis-IDs und fehlender Schlüssel im Add-on-Weg
  (b4dfa94, bebb832); Webhooks an CSRF abgeprallt, Kündigung ließ Säulen und Extra-Sites stehen,
  geschluckte Aktivierungsfehler (1b6cd88); feste Bezahlarten (5f5b9d0); Early Access ohne
  Befristung (8fe5da3); Preiskollision Zusatzplatz/Extra-Sites (afe94c1, 308fdbf).
- **Server-Umzug:** Stripe-Schlüssel und beide Webhook-Secrets mitnehmen, Endpunkt-URLs im
  Stripe-Dashboard anpassen. Env-Namen müssen in der `environment`-Liste von
  `docker-compose.yml` stehen, sonst erreichen sie den Container nicht
  (`test_konfig_erreicht_code.py`).
