# A/B-Testing für das Cookie-Banner

**Stand:** 2026-07-29 · **Status:** 🟢 live

## Ziel
Zwei Bannervarianten gegeneinander laufen lassen und messen, welche die höhere
Zustimmungsquote erzielt. Variante A ist die bestehende Banner-Konfiguration
(Kontrolle), Variante B die Abwandlung. Wird ein Sieger erklärt, übernimmt complyo
dessen Gestaltung als neue Banner-Konfiguration.

## Architektur (end-to-end)
- **Routes:** `backend/ab_test_routes.py`, Prefix `/api/ab-tests`, registriert in
  `backend/main_production.py` (Import `:102`, `include_router` `:673`, `db_pool`-Wiring `:745`).
  - Verwaltung (Token + Ownership): `POST ""`, `GET /{test_id}`, `GET /site/{site_id}`,
    `PATCH /{test_id}`, `POST /{test_id}/start`, `POST /{test_id}/stop`, `DELETE /{test_id}`
  - Öffentlich (Besucher-Browser): `GET /assign/{site_id}/{visitor_id}`, `POST /track`
- **Auth/Ownership:** `get_current_user` (dependencies.py) plus `assert_site_owner` /
  `assert_test_owner`. Ownership-Anker ist `cookie_banner_configs(site_id, user_id)` —
  dieselbe Zuordnung wie bei der Banner-Konfiguration. Fremde Site/Test → **404**
  (nicht 403), damit fremde IDs nicht als existierend erkennbar sind.
- **Schema:** Revision `0005_cookie_ab_testing`
  - `cookie_ab_tests` — Testdefinition. Partieller Unique-Index
    `uq_cookie_ab_tests_one_running` erzwingt „höchstens ein laufender Test je Seite"
    auch auf DB-Ebene, nicht nur in der Route.
  - `cookie_ab_assignments` — Besucher→Variante, `UNIQUE (test_id, visitor_hash)`,
    Cascade-Delete. Der Hash ist SHA-256 über die Besucher-ID; es wird keine rohe
    Besucher-ID gespeichert.
  - `cookie_ab_results` — Tagesaggregat je Variante, `UNIQUE (test_id, variant, date)`,
    Cascade-Delete. Der Track-Endpunkt schreibt per UPSERT.
- **Zuweisung:** deterministisch über die ersten 8 Hex-Stellen des Besucher-Hashes gegen
  `traffic_split`. Derselbe Besucher bekommt immer dieselbe Variante, auch ohne
  gespeicherte Zuordnung.
- **Statistik:** Z-Test auf die Zustimmungsquote, p-Wert über eine Approximation der Fehlerfunktion
  (`calculate_z_score`, `z_to_p_value`). Ein Ergebnis gilt erst als belastbar, wenn
  `min_sample_size` je Variante erreicht ist.
- **Widget:** `backend/widgets/cookie_banner_v2.js` ruft `/assign/...` vor dem Rendern und
  meldet Impression/Entscheidung an `/track`.
- **UI:** `dashboard-react/src/components/cookie-compliance/ABTestManager.tsx`,
  eingehängt als Tab „A/B-Tests" in `src/app/cookie-compliance/page.tsx`.
  API-Client: `src/lib/ab-testing-api.ts`.

## Was am 29.07.2026 behoben wurde
1. **Die drei Tabellen fehlten komplett.** Der Baseline-Cut hatte sie nicht übernommen,
   Revision 0003 ließ sie bewusst aus (Produktentscheidung stand aus). Das Banner rief
   `/assign` bei jedem Seitenaufruf auf und erzeugte dabei rund 100 Fehler pro Tag.
2. **Der Router hatte keinerlei Auth.** Anlegen, Starten, Stoppen und Löschen von Tests
   fremder Seiten war öffentlich möglich — und damit indirekt die Manipulation der
   ausgelieferten Banner-Konfiguration fremder Kunden.
3. **`/track` nahm beliebige `test_id` an.** Jetzt nur noch Tests im Status `running`.
4. **Mittelwert der Entscheidungszeit war falsch berechnet** (Division durch
   `impressions + 1`, NULL machte den Wert dauerhaft leer) → gewichteter Mittelwert.
5. **JSONB kam als String zurück.** `asyncpg` liefert JSONB ohne registrierten Codec als
   `str`; das Widget hätte `applyServerConfig()` mit einem String aufgerufen und die
   Variante nie angewendet. Helfer `als_dict()` wandelt an allen Rückgabestellen um.
6. **Der Sieger blieb folgenlos.** `stop` vermerkte nur `winner`. Jetzt überträgt
   `wende_variante_an()` die Gestaltung des Siegers auf `cookie_banner_configs` —
   über eine Allowlist (`layout`, Farben, `button_style`, `position`, `width_mode`,
   `texts`), damit eine Variante keine Zähler oder Flags überschreiben kann.

## Tests
`backend/tests/test_ab_test_auth.py` (14 Tests):
- statischer Wächter über den Quelltext — schlägt an, sobald eine neue Route ohne
  `current_user` hinzukommt, die nicht ausdrücklich öffentlich sein soll
- prüft zusätzlich, dass `current_user` nicht nur in der Signatur steht, sondern der
  Ownership-Helfer im Rumpf auch wirklich aufgerufen wird
- Verhalten von `assert_site_owner` / `assert_test_owner` gegen eine gemockte DB
- `test_schema_completeness.py` deckt die drei Tabellen seit 29.07.2026 mit ab
  (Ausnahme-Eintrag entfernt)

## Offen
- Die Auswertung zeigt nur die Zustimmungsquote. Teilzustimmung, Ablehnung und
  Entscheidungsdauer werden erfasst, aber noch nicht dargestellt.
- Kein Zeitreihen-Verlauf — nur Gesamtaggregat je Variante.
- `PATCH /{test_id}` ist implementiert, hat aber keine Oberfläche.
