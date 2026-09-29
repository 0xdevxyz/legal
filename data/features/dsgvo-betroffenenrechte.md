# DSGVO-Betroffenenrechte & Retention

**Stand:** 2026-09-28 · **Status:** 🟢 live (Export, zweistufige Löschung, KI-Erlaubnis und
Löschfristen laufen; offen: Löschknopf im Dashboard nur per Mail, zwei Fristen für Einwilligungsprotokolle)

## Ziel
Compliance am eigenen Produkt: Auskunft (Art. 15/20), Löschung (Art. 17), Wahl gegen die
KI-Übermittlung in die USA (Zusage der Datenschutzerklärung) und automatisierte
Aufbewahrungsbegrenzung (Art. 5 Abs. 1 lit. e) samt Nachweis (Art. 5 Abs. 2) für die von
Complyo selbst verarbeiteten Daten.

## Architektur (end-to-end)
- **Routes:** `backend/gdpr_api.py` (519 Z.), `gdpr_router` (Prefix `/api/gdpr`), Include
  `main_production.py:713`. **12 Operationen auf 10 Pfaden, alle live in `openapi.json`
  (geprüft 2026-09-28):**
  - Betroffener = Token-Inhaber. Alle Betroffenen-Wege hängen an `get_verified_user`
    (`gdpr_api.py:29`), das die Person ausschliesslich aus dem JWT nimmt. Ein `email`-Feld
    im Body oder in der Query gibt es nicht mehr. Live ohne Token: 401.
  - `POST /request-deletion` (Z. 76): registriert einen Kontolöschantrag in
    `gdpr_deletion_requests` (Status `pending`), 400 ohne `confirmation`. Keine sofortige Löschung.
  - `DELETE /request-deletion` (Z. 132): offenen Antrag zurückziehen.
  - `GET /deletion-status` (Z. 148): Status des letzten Antrags.
  - `GET /export-data` (Z. 162): JSON-Download (`complyo-daten-export.json`).
  - `POST /export-data` (Z. 188): derselbe Export per Mail (`email_service.send_data_export_email`
    als `BackgroundTask`).
  - `GET /retention-info` (Z. 239): Fristen des Token-Inhabers, einheitlich 24 Monate
    (`RETENTION_MONATE`, Z. 25). Der frühere `?email=`-Parameter ist entfallen.
  - `GET|PUT /ki-erlaubnis` (Z. 468/506): siehe „KI-Erlaubnis".
  - `GET /privacy-policy` (Z. 411): öffentlich (live 200), Verantwortlicher und Kontakt aus
    `anbieter.py` (`VERANTWORTLICHER`, `DATENSCHUTZ_EMAIL`), kein Datenschutzbeauftragter.
  - Admin: `POST /admin/confirm-deletion` (Stufe 2 der Kontolöschung),
    `POST /admin/update-retention`, `GET /admin/cleanup-status`, `POST /admin/run-cleanup`.
    Alle über `require_admin` (JWT plus `users.role`, `dependencies.py:292`). Der frühere
    `ADMIN_API_KEY` als Query-Parameter ist entfallen.
- **Dashboard:** Einstellungen, Reiter Datenschutz (`dashboard-react/src/app/settings/page.tsx`):
  - Export ruft `GET /api/user/export-data` (`backend/user_routes.py:176`), das an denselben
    `gdpr_service.export_user_data()` delegiert.
  - KI-Schalter liest und setzt `/api/gdpr/ki-erlaubnis` (Z. 93/107, Schalter ab Z. 477).
  - „Konto löschen" (Z. 516 ff.) öffnet nur `mailto:support@complyo.de`; der API-Weg
    `POST /api/gdpr/request-deletion` hat keinen Aufrufer im Dashboard (grep über
    `dashboard-react/src` und `landing-react/src`).
- **Service:** `backend/gdpr_retention_service.py` (779 Z.), Singleton `gdpr_service`,
  `GDPR_RETENTION_DAYS` (Default 730), `GDPR_CLEANUP_INTERVAL_HOURS` (Default 24).
  - `export_user_data()` (Z. 314) aggregiert `users` samt zugehöriger Tabellen plus Alt-Lead-Daten
    derselben E-Mail (seit c5876a4, 2026-08-11; vorher lief der Export gegen die leere `leads`-Tabelle).
  - Kontolöschung **zweistufig**: `request_user_deletion()` (Z. 370, `pending`), Bestätigung durch
    Admin `confirm_user_deletion()` (Z. 460, `confirmed`), Ausführung
    `process_confirmed_user_deletions()` (Z. 492) über `_execute_user_deletion()` (Z. 536) mit
    der Liste `_LOESCH_STATEMENTS` (Z. 515): Bearbeiter-Referenzen anonymisieren, abhängige
    Tabellen löschen, zuletzt `users` (kaskadiert).
  - Eingangs- und Abschlussmails (`_send_user_deletion_received`/`_completed`, Lead-Varianten
    `_send_deletion_notification`/`_confirmation`) gehen über den echten Versandweg
    `email_service._send_email` (4dc58cd, 2026-08-10; vorher nur Logzeile).
  - `perform_retention_cleanup()` (Z. 80): abgelaufene Leads, markierte Lead-Löschanträge,
    bestätigte Kontolöschungen.
  - `start_automated_cleanup()` wird jetzt beim Start aufgerufen (`main_production.py:929`,
    c5876a4), der Loop läuft; Log belegt tägliche Läufe („GDPR cleanup completed: 0 leads …").
  - Löschlog `self.deletion_log` bleibt Prozess-Speicher; `/admin/cleanup-status` ist nach
    jedem Neustart leer. Revisionsfester Nachweis läuft stattdessen über `loeschprotokoll` (s. u.).
- **Hintergrund-Task `_daily_gdpr_cleanup()`** (`main_production.py:864`, Start Z. 921): 60 s
  Verzögerung, dann 24-h-Schleife, jedes Statement mit eigenem try (fehlende Tabelle = INFO):
  `user_sessions` (abgelaufen), `users` (`is_active = FALSE` und seit 2 Jahren unverändert),
  **`cookie_consent_logs` älter als 24 Monate (ohne Bedingung auf `expires_at`)**, `leads`
  (Retention abgelaufen bzw. Löschantrag älter 30 Tage), `ai_call_logs` (Tabelle fehlt, wird
  übersprungen), `email_verifications` (abgelaufen).
- **Löschfristen (Kontosicherheit, 9a3924b, Migration `0032_kontosicherheit`):**
  `backend/loeschfristen.py` hält alle Fristen als Daten (`FRISTEN`). Klasse `SOFORT` (Cache,
  Nonces, Telemetrie: `geo_ip_cache` 30 T., `oauth_states` 1 T., `widget_events` 90 T.,
  `accessibility_wirkung` 180 T., `deep_scan_history` und `cookie_ab_assignments` 365 T.,
  unbestätigte `waitlist_leads` 30 T.). Klasse `GESCHUETZT` nur mit `LOESCHFRISTEN_SCHARF=ja`:
  `cookie_consent_logs` 1095 T. (nur abgelaufene), `scan_history`, `score_history`,
  `accessibility_wirkungsscan`, `user_journeys` je 730 T., `fix_application_audit` und
  `communication_log` je 1095 T.
  - Ruhende Konten: ohne Anmeldung, Scan und laufendes Abo seit 1095 Tagen (36 Monate) folgt
    eine Ankündigungsmail, nach 30 Tagen die Löschung über denselben Weg wie Art. 17 (Eintrag in
    `gdpr_deletion_requests` mit `confirmed`, dann `_execute_user_deletion`). Anmelden setzt die
    Ankündigung zurück (`auth_routes.py:359`).
  - Jede Löschentscheidung mit Treffern landet in `loeschprotokoll` (Art. 5 Abs. 2).
  - Aufruf: Host-Crontab `30 3 * * * docker exec complyo-backend python -m cronjobs.loeschfristen_cron`
    (Log `/var/log/complyo-loeschfristen.log`). Live: `LOESCHFRISTEN_SCHARF=ja`, tägliche Läufe
    bis 2026-09-27 „keine Zeile über der Frist"; `loeschprotokoll` hat deshalb 0 Zeilen.

## KI-Erlaubnis je Konto (3b56959, 5c43190, 2026-09-25)
- Anlass: die Datenschutzerklärung sagte zu, man könne die KI-Funktionen ungenutzt lassen; es
  gab keinen Schalter, und nach jedem Scan gingen Bildadressen an Claude Vision (OpenRouter, USA).
- Migration `0036_ki_erlaubnis`: `users.ki_erlaubt` (Default `true`) plus
  `ki_erlaubnis_geaendert_am`. Vorbelegung bewusst „erlaubt", Rechtsgrundlage bleibt
  Art. 6 Abs. 1 lit. b, keine Einwilligung. Live: 16 Konten, alle `true`.
- `backend/ki_erlaubnis.py` (119 Z.): `darf_ki()` (Z. 49) mit 60-s-Zwischenspeicher, `setze()` (Z. 104).
  Im Zweifel wird **nicht** gesendet (unlesbare Erlaubnis oder fehlendes Konto = `False`).
- Hinter der Schranke: `accessibility_post_scan_processor.py:150` und zwei Stellen in
  `alt_text_routes.py` (Z. 144, Z. 573).
- Bewusst offen, benannt in `tests/test_ki_erlaubnis.py` (`BEWUSST_OFFEN`): öffentlicher Scanweg
  ohne Konto, die Fix-Maschinen in `ai_fix_engine` (bekommen kein Konto durchgereicht, offene
  Lücke), Rechtsupdate-Auswertung (keine Kundendaten).
- `GET /ki-erlaubnis` nennt in `betrifft`/`betrifft_nicht`, was die Schranke abdeckt.

## DB
- `gdpr_deletion_requests` (Alembic `0014`, 2026-08-11): `user_id`, `email`, `reason`, `status`
  (`pending|confirmed|completed|cancelled`), Zeitstempel. Live: 0 Zeilen.
- `loeschprotokoll` (Alembic `0032`): `lauf`, `regel`, `tabelle`, `anzahl`, `ausgefuehrt`,
  `grundlage`, `zeitpunkt`. Live: 0 Zeilen.
- `users.ki_erlaubt`, `users.ki_erlaubnis_geaendert_am` (`0036`), `users.loeschung_angekuendigt_am` (`0032`).
- Gelöscht wird ausserdem in `users`, `user_sessions`, `cookie_consent_logs`, `leads`,
  `email_verifications` und den Tabellen aus `_LOESCH_STATEMENTS`.
- `ai_call_logs` existiert live nicht (geprüft), wird übersprungen.
- Alembic-Kopf live: `0036_ki_erlaubnis`.
- `backend/backup_retention.py` ist entfernt (7b7cd13, 2026-09-10).

## Bekannte Lücken / Offen
- **Zwei Fristen für Einwilligungsprotokolle.** `_daily_gdpr_cleanup()` löscht
  `cookie_consent_logs` nach 24 Monaten ohne Bedingung, `loeschfristen.py` nennt 1095 Tage
  (36 Monate, § 195 BGB) für abgelaufene Zeilen; DB-Default `expires_at` ist `now() + 2 years`
  (Alembic 0015), die SQL-Funktion `delete_expired_consents()` löscht nach `expires_at`.
  Wirksam ist damit die kürzeste Regel, 24 Monate. Texte widersprechen sich ebenso: AVV
  (`landing-react/src/app/avv/page.tsx:133`) sagt 24 Monate, die Datenschutzerklärung
  (`landing-react/src/app/datenschutz/page.tsx:53`, Einwilligung der complyo.de-Besucher) drei
  Jahre. Auf eine Frist festlegen und den Daily-Cleanup-Eintrag entfernen oder angleichen.
  Noch ohne Wirkung, weil die ältesten Zeilen vom 2026-05-01 stammen.
- **Löschknopf im Dashboard ist eine Mail.** „Konto löschen" öffnet `mailto:support@complyo.de`;
  der zweistufige API-Weg ist live, aber aus der Oberfläche nicht erreichbar.
- **Kontolöschung braucht einen Admin.** `pending`-Anträge werden erst nach
  `POST /admin/confirm-deletion` ausgeführt; eine Frist oder Erinnerung für offene Anträge
  (Art. 12 Abs. 3: ein Monat) ist nicht geprüft.
- **Zwei Regeln für inaktive Konten:** Daily-Cleanup löscht `is_active = FALSE` nach 2 Jahren
  direkt (ohne Ankündigung, ohne `loeschprotokoll`), `loeschfristen` behandelt ruhende aktive
  Konten nach 36 Monaten mit Ankündigung. Zusammenführen.
- `/admin/cleanup-status` meldet Statistiken aus dem Prozess-Speicher, nach Neustart leer.
- `ai_fix_engine` liegt nicht hinter der KI-Erlaubnis (in `BEWUSST_OFFEN` benannt).
- Tests: `tests/test_gdpr_betroffenenrechte.py`, `tests/test_gdpr_knowledge_auth.py`,
  `tests/test_ki_erlaubnis.py` vorhanden; ob sie aktuell grün sind, nicht geprüft.
