-- ===========================================================================
-- Backoffice-Datenkorrekturen (Vorschlagsskript, 2026-08-11)
-- ===========================================================================
--
-- DIESES SKRIPT FUEHRT NICHTS AUS.
-- Jede schreibende Anweisung (UPDATE/DELETE/INSERT) ist AUSKOMMENTIERT und
-- bleibt es, bis der Betreiber sie einzeln geprueft und entkommentiert hat.
-- Unkommentiert sind ausschliesslich lesende SELECT-Vorschauen.
--
-- Empfohlener Ablauf:
--   1. SELECT-Vorschau ausfuehren, Ergebnis mit den Kommentaren abgleichen.
--   2. Entscheidung treffen (siehe Warnhinweise).
--   3. Die EINE gewuenschte Anweisung entkommentieren und in einer
--      Transaktion ausfuehren:  BEGIN; ...; -- pruefen --; COMMIT/ROLLBACK;
--
-- Befundstand (lesend erhoben am 2026-08-11, Produktions-DB):
--   * users: 11 Konten, davon 10 plan_type='free', 1 plan_type='ai'.
--   * Der 'ai'-User ist id=5 (mail@panoart360.de, angelegt 2026-03-23) —
--     das ist das Betreiber-Konto selbst.
--   * users hat KEINE Stripe-Spalten; stripe_customers hat KEINEN Eintrag
--     fuer user_id=5. ABER: subscriptions fuehrt fuer user_id=5 zwei AKTIVE
--     Abos mit Stripe-Subscription-IDs (id=2 plan_type='pro',
--     id=3 plan_type='agency').
--   * subscription_plans (4 Zeilen, alle is_active=true):
--       id=1 free   'Kostenlose Analyse'    0.00 /    0.00
--       id=2 ai     'KI-Automatisierung'   39.00 /  390.00   <- toter Tarif
--       id=3 expert 'Experten-Service'     39.00 /  390.00   <- falscher Preis
--       id=4 agency 'Agentur'             490.00 / 4704.00   <- falscher Preis
--   * Gueltiges Tarifmodell (Stand 2026-08):
--       free 0 | single 19 (einmalig je Modul) | pro 49/Mon | agency 299/Mon
--       expert 3.990 einmalig | update 29/Mon | monitor 19/Mon
--     Die alten 39-€-/3.900-€-Preise gelten NICHT mehr.
--   * subscription_plans.plan_type hat einen UNIQUE-Constraint
--     (subscription_plans_plan_type_key); price_* sind numeric(10,2).
--
-- ===========================================================================
-- Teil (a): User mit totem Tarif plan_type='ai'
-- ===========================================================================

-- Vorschau: Wer haengt auf 'ai', und was sagen Abos/Stripe dazu?
-- (users hat keine stripe-Spalten — Stripe-Bezug kommt aus subscriptions
--  und stripe_customers.)
SELECT
    u.id,
    u.email,
    u.plan_type,
    u.created_at,
    u.is_active,
    sc.stripe_customer_id,
    s.id                     AS subscription_id,
    s.plan_type              AS abo_plan,
    s.status                 AS abo_status,
    s.stripe_subscription_id
FROM users u
LEFT JOIN stripe_customers sc ON sc.user_id = u.id
LEFT JOIN subscriptions   s  ON s.user_id  = u.id
WHERE u.plan_type = 'ai'
ORDER BY s.id;

-- !! WARNHINWEIS — Betreiber-Entscheidung: zahlt dieser Kunde? !!
-- Der einzige 'ai'-User ist das Betreiber-Konto (mail@panoart360.de) und
-- fuehrt in subscriptions ZWEI aktive Abos mit Stripe-IDs ('pro' und
-- 'agency'). Ein pauschales Downgrade auf 'free' wuerde diesem Konto
-- Plan-Rechte entziehen, obwohl aktive Abos existieren. Alternativen:
--   * Zahlt das Konto wirklich (Stripe-Dashboard pruefen)?  Dann eher
--     plan_type auf 'agency' (das hoechste aktive Abo) korrigieren.
--   * Ist es ein reines Testkonto ohne echte Zahlung? Dann 'free'.
--
-- Variante 1 (Auftragsvorgabe): totes 'ai' -> 'free'
-- UPDATE users SET plan_type = 'free', updated_at = CURRENT_TIMESTAMP
--  WHERE id = 5 AND plan_type = 'ai';
--
-- Variante 2 (falls das Konto zahlend ist, hoechstes aktives Abo):
-- UPDATE users SET plan_type = 'agency', updated_at = CURRENT_TIMESTAMP
--  WHERE id = 5 AND plan_type = 'ai';

-- ===========================================================================
-- Teil (b): subscription_plans an das gueltige Tarifmodell angleichen
-- ===========================================================================

-- Vorschau: aktueller Zustand der Tariftabelle.
SELECT id, plan_type, name, price_monthly, price_yearly,
       stripe_price_id_monthly, stripe_price_id_yearly,
       max_websites, is_active, updated_at
FROM subscription_plans
ORDER BY id;

-- Vorschau: Haengen User oder Abos an Tarifen, die wegfallen sollen?
-- ('ai' darf erst hart geloescht werden, wenn beides 0 ist.)
SELECT
    (SELECT COUNT(*) FROM users         WHERE plan_type = 'ai') AS users_auf_ai,
    (SELECT COUNT(*) FROM subscriptions WHERE plan_type = 'ai') AS abos_auf_ai;

-- ---------------------------------------------------------------------------
-- (b1) Toten Tarif 'ai' deaktivieren.
-- DELETE ist bewusst NICHT der Vorschlag: solange users.plan_type='ai'
-- existiert (Stand 2026-08-11: 1 Konto, siehe Teil a), wuerde ein DELETE die
-- Herkunft verschleiern. Erst Teil (a) klaeren, dann deaktivieren; DELETE
-- fruehestens, wenn beide Zaehler der Vorschau oben 0 sind.
--
-- UPDATE subscription_plans
--    SET is_active = false, updated_at = CURRENT_TIMESTAMP
--  WHERE plan_type = 'ai';
--
-- Spaeter, NUR wenn users_auf_ai = 0 UND abos_auf_ai = 0:
-- DELETE FROM subscription_plans WHERE plan_type = 'ai';

-- ---------------------------------------------------------------------------
-- (b2) 'agency' auf den gueltigen Preis 299 €/Mon korrigieren (statt 490).
-- Jahrespreis: 2.990 € entspricht dem ueblichen "2 Monate geschenkt"-Muster;
-- falls der Betreiber einen anderen Jahrespreis kommuniziert, hier anpassen.
--
-- UPDATE subscription_plans
--    SET price_monthly = 299.00,
--        price_yearly  = 2990.00,   -- Betreiber-Entscheidung, s. Kommentar
--        updated_at    = CURRENT_TIMESTAMP
--  WHERE plan_type = 'agency';

-- ---------------------------------------------------------------------------
-- (b3) 'expert' ist ein EINMALIG-Preis (3.990 €), kein Abo. Die Tabelle
-- kennt nur price_monthly/price_yearly — der Einmalcharakter passt nicht in
-- das Schema. Vorschlag: Einmalpreis in price_monthly ablegen und den
-- Charakter im Namen/der Beschreibung klarstellen; die laufende
-- Folgebetreuung ist der separate Tarif 'update' (29 €/Mon, b4).
--
-- UPDATE subscription_plans
--    SET name          = 'Experten-Service (einmalig)',
--        description   = 'Einmaliger Experten-Service, 3.990 € einmalig. '
--                        'Folgebetreuung ueber Tarif update (29 €/Monat).',
--        price_monthly = 3990.00,   -- Einmalpreis, kein Monatsabo!
--        price_yearly  = NULL,
--        updated_at    = CURRENT_TIMESTAMP
--  WHERE plan_type = 'expert';

-- ---------------------------------------------------------------------------
-- (b4) Fehlende Tarife des gueltigen Modells anlegen: single/pro/update/
-- monitor fehlen in der Tabelle komplett (UNIQUE auf plan_type schuetzt vor
-- Doppelanlage). Stripe-Price-IDs danach aus der Stripe-Konsole nachtragen
-- (Spalten stripe_price_id_monthly/_yearly), sie liegen nicht in der DB vor.
--
-- INSERT INTO subscription_plans (plan_type, name, description, price_monthly, price_yearly, max_websites, is_active)
-- VALUES
--   ('single',  'Einzel-Modul',      'Einmalkauf je Modul (19 € einmalig)',            19.00,  NULL,    1, true),
--   ('pro',     'Pro',               'Pro-Abo, 1 Domain',                              49.00,  490.00,  1, true),
--   ('update',  'Update-Service',    'Folgebetreuung nach Experten-Service',           29.00,  NULL,    1, true),
--   ('monitor', 'Monitoring',        'Laufende Ueberwachung (19 €/Mon, 190 €/Jahr)',   19.00,  190.00,  1, true);

-- ---------------------------------------------------------------------------
-- Abschlusskontrolle nach jeder ausgefuehrten Korrektur (lesend):
SELECT id, plan_type, name, price_monthly, price_yearly, is_active
FROM subscription_plans
ORDER BY plan_type;
