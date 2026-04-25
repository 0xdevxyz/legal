# Requirements: Technical Debt & Feature Completeness

## AUTH-10: cookie_compliance_routes.py — ungesicherte Endpoints absichern

**Problem:** Mehrere Endpoints prüfen Auth nicht konsequent oder verwenden lokale Helfer statt `dependencies.py`.
**Fix:** Wo `get_current_user_required` (lokale Implementierung) verwendet wird, sicherstellen dass 401 zurückgegeben wird ohne JWT. Kein Refactor auf `dependencies.get_current_user` nötig — lokale Implementierung ist korrekt.
**Akzeptanzkriterium:** Alle geschützten Endpoints geben 401 ohne gültigen Bearer Token.

## AUTH-11: widget_routes.py — generate-patches Endpoint absichern

**Problem:** `generate_accessibility_patches` verwendet `db_pool: asyncpg.Pool = Depends(lambda: None)` und hat `user_id: int = Depends(get_current_user_id)` auskommentiert.
**Fix:** `get_current_user` aus `dependencies.py` importieren und als Dependency einbinden. `user_id` aus `current_user["user_id"]` lesen statt Hardcode `1`.
**Akzeptanzkriterium:** Endpoint gibt 401 ohne JWT; `user_id=1` Hardcode entfernt.

## DB-01: Widget-Tracking-Events persistieren

**Problem:** `/api/widgets/track` loggt nur via print, kein DB-Insert.
**Fix:** INSERT in `widget_events` Tabelle via `db_pool` (falls vorhanden). Migration anlegen falls Tabelle nicht existiert.
**Akzeptanzkriterium:** Events landen in DB; Endpoint schlägt nicht fehl wenn DB nicht verfügbar (silent fail).

## DB-02: Upsell-Check mit echter DB-Abfrage

**Problem:** `_check_upsell_opportunity` enthält nur auskommentierten Code + `pass`.
**Fix:** Auskommentierten Code aktivieren — COUNT aus `widget_usage_stats` WHERE `site_id=$1` AND `timestamp > NOW() - INTERVAL '30 days'`.
**Akzeptanzkriterium:** Funktion führt echte DB-Abfrage durch; silent fail bei DB-Fehler.

## DB-03: Widget-Config aus DB laden

**Problem:** `/api/widgets/config/{site_id}` gibt immer Hard-coded Default-Config zurück.
**Fix:** Versuch, Config aus `cookie_banner_configs` Tabelle zu laden (nach site_id). Fallback auf Default wenn nicht gefunden.
**Akzeptanzkriterium:** Existierende Site-Config wird aus DB geladen; Default-Fallback bleibt.

## DB-04: ML-Feedback in DB speichern

**Problem:** `ai_legal_routes.py` Feedback-Endpoint (ca. Zeile 173) speichert nichts.
**Fix:** INSERT Feedback-Daten in `legal_update_feedback` oder äquivalente Tabelle via `db_pool`.
**Akzeptanzkriterium:** Feedback landet in DB; Endpoint bleibt funktionsfähig auch ohne DB.

## DB-05: Widget-Feedback in public_routes persistieren

**Problem:** `/sites/{site_id}/widget-feedback` in `public_routes.py` loggt nur, kein DB-Insert.
**Fix:** INSERT in `widget_events` Tabelle analog zu DB-01.
**Akzeptanzkriterium:** Feedback-Events in DB; silent fail bei Fehler.

## FEAT-01: Email-Service Integration in expert_service_routes

**Problem:** `_send_expert_request_email` loggt nur, ruft `email_service` nicht auf.
**Fix:** `EmailService` importieren, `_send_email` für Kunden-Bestätigung und Team-Notification aufrufen. Bestehende Log-Inhalte als Email-Body verwenden.
**Akzeptanzkriterium:** Bei Expert-Anfrage werden 2 Emails verschickt (oder geloggt bei SMTP-Fehler); Anfrage schlägt nicht fehl wenn Email-Versand scheitert.

## FEAT-02: Cookie-Settings-Modal

**Problem:** Cookie-Settings-Modal in `widgets/cookie_consent.js` ist nicht implementiert (TODO bei ca. Zeile 214).
**Fix:** Modal-Logik implementieren — Kategorien anzeigen (Notwendig, Funktional, Analytik, Marketing), Toggle pro Kategorie, Speichern-Button der Consent-Update auslöst.
**Akzeptanzkriterium:** Modal öffnet sich via Settings-Button; Änderungen werden in Consent-Log gespeichert; UI konsistent mit bestehendem Banner-Stil.
