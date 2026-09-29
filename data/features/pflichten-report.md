# Pflichten-Report (Firmenprofil → individuelle Pflichten-Einordnung + Änderungs-Feed + Abmahn-Radar + Tarifempfehlung)

**Stand:** 2026-09-28 · **Status:** 🟢 live (Report, Feed, Abmahn-Radar); Tarifempfehlung nur in der API

## Ziel
Nutzer beantworten rund 15 Profilfragen (Größe, Umsatz, B2C, Shop, KI-Einsatz, B2B-Rechnungen,
Cloud/Hosting, Sektor …) und bekommen einen priorisierten Report: **welche Regulierung trifft
wahrscheinlich zu, warum, mit welcher Frist, welchem Bußgeldrahmen und welchem nächsten
Schritt.** Premium-Feature: Free sieht Teaser (Top 3 + Zähler), zahlende Pläne alles.

## Haftungs-Design (RDG, nicht verhandelbar)
- Drei Status, nie ein Rechtsurteil: `applies` („trifft wahrscheinlich zu"),
  `check` („bitte prüfen"), `not_indicated` („keine Indizien im Profil").
- Jede Einordnung trägt `confidence`, `evidence` (auslösende Profilantworten), `why` und
  `legal_basis`.
- Einzelfallabhängige Einstufungen (AI-Act-Hochrisiko, NIS2) sind hart auf höchstens `check`
  begrenzt (per Test abgesichert).
- Disclaimer „Information, keine Rechtsberatung" in jedem Response (Report, Feed, Radar).
- **Offen vor öffentlichem Marketing-Launch: externe RDG-Klärung.** Im Repo nicht belegt, ob
  inzwischen erfolgt.

## Architektur
- **Katalog:** `backend/pflichten_katalog.py` (348 Z.), **14 Pflichten** als Rules-as-Code:
  `dsgvo_datenschutzerklaerung`, `impressum`, `ttdsg_cookie_consent`, `bfsg` (inkl.
  Kleinstunternehmen-Ausnahme), `ai_act_transparenz`, `ai_act_hochrisiko`, `e_rechnung`, `nis2`,
  `cra`, `data_act`, `uwg_newsletter`, `dsgvo_verzeichnis`, `dsgvo_dsb`, `widerruf_shop`.
  `evaluate_pflichten(profile)` (Z. 310) ist deterministisch (keine KI), sortiert
  applies → check → not_indicated, innerhalb nach Bußgeld-Obergrenze. Fehler in einer Regel
  ergeben `check` statt Absturz.
  - Fristen gegen Quellen aktualisiert (`5e3c553`, 16.09.): NIS2 gilt seit 06.12.2025
    (Registrierungsfristen verstrichen), E-Rechnung Versandpflicht ab 2027-01-01 (> 800.000 €)
    bzw. 2028-01-01, Art. 50 KI-VO seit 2026-08-02 bußgeldbewehrt; Omnibus-Nachfrist
    ausdrücklich als nicht in Kraft markiert.
  - `data_act` neu (`07692a9`, 16.09.): Wechselrecht, ab 2027-01-12 keine Wechselentgelte,
    DADG seit 2026-05-30; neues Profilfeld `provides_cloud_service`. CRA-Meldepflichten als
    „seit 2026-09-11".
  - Säulenbezug (`scan_pillar`): Datenschutzerklärung → `gdpr`, Impressum und Widerruf → `legal`,
    Cookie → `cookies`, BFSG → `accessibility`; die übrigen zehn ohne Scanbezug.
- **API:** `backend/pflichten_report_routes.py` (310 Z., `/api/pflichten-report`, eingebunden
  `main_production.py:746`), kanonische Auth (live ohne Token: 401):
  - `PUT /profile` (Z. 52): Whitelist `ALLOWED_KEYS` (Z. 32, 15 Schlüssel), Upsert, JSONB per
    `json.dumps`. Leere Auswahl → 422.
  - `GET /profile` (Z. 74).
  - `GET ""` (Z. 240): Report. Ohne Profil 404. Hängt an Pflichten mit `scan_pillar` den
    Säulenwert des jüngsten `scan_history`-Eintrags (`scan_status`) und liefert `scan_context`.
    Plan-Gating über `user_limits.plan_type`: `free`/`freemium` → `locked: true`, 3 sichtbare
    Einträge + `teaser` (versteckte Anzahl, davon `applies`).
  - `GET /updates` (Z. 125): Änderungs-Feed (siehe unten).
  - `GET /abmahnwellen` (Z. 189): Abmahn-Radar (siehe unten).
- **Ist-Zustand aus dem Scan:** `_latest_scan_pillars()` (Z. 91) liest `overall_score`,
  `accessibility_score`, `cookie_score`, `legal_score`, `privacy_score` und seit `3b56959` auch
  `jurisdiction`. Bis 25.09. waren diese Spalten in allen Zeilen leer (kein INSERT schrieb sie),
  der Ist-Zustand erschien also nie. Behoben mit `3b56959`: Migration 0035 hat die Werte aus
  `scan_data` nachgetragen, die drei INSERTs schreiben sie über `backend/scan_persistenz.py`.
  Live 28.09.: 45 bzw. 50 von 51 Zeilen mit Säulenwerten; die zwei Profilnutzer mit Scan haben
  Werte im letzten Scan.
- **Tarifempfehlung:** `backend/tarifempfehlung.py` (185 Z., `b142962`, 23.09.).
  `empfehlung(report, websites)` (Z. 141): Punkte = `applies` voll + `check` halb (Z. 99);
  Stufen `schlank` < 6,5 ≤ `voll` < 10,0 ≤ `voll_plus` (Z. 69-70), Schwellen aus einer
  Vollzählung von 20.480 Profilen und Archetypen. Liefert `punkte`, `stufe`, `beschreibung`,
  bis zu 4 `treiber`, `hinweise` (mehrere Websites, Free-Kürzung), `grundlage`. Keine Preise im
  Modul, keine Sperre. Wird in `GET ""` **vor** der Teaser-Kürzung berechnet (Z. 284-292) und als
  `report["tarifempfehlung"]` ausgeliefert.
- **Dashboard:** `dashboard-react/src/app/pflichten-report/page.tsx` (306 Z.): Fragebogen
  (Ja/Nein + Selects, inkl. `provides_cloud_service`), Report mit Status-Karten, Law-/Deadline-Badges,
  Konfidenz + Evidence, Ist-Zustand „Score x/100" (grün ab 80), `AbmahnRadar`, Feed, Upgrade-CTA,
  Disclaimer. Sidebar-Eintrag „Pflichten-Report" (`components/dashboard/Sidebar.tsx:75`).

## DB
- `company_profiles` (user_id PK → users, `answers` JSONB), Alembic
  `20260717_0002_company_profiles.py`. Live 28.09.: 3 Profile (1 x free, 2 x agency).
- `pflichten_events`, Alembic `20260717_0004_pflichten_events.py`, UNIQUE(legal_update_id, rule_id),
  FK auf `legal_updates` mit ON DELETE CASCADE.
- Liest `scan_history` (Säulenwerte + `jurisdiction`, Migration 0035), `user_limits.plan_type`,
  `tracked_websites` (Anzahl für die Tarifempfehlung).

## Änderungs-Feed (🟢 live)
- **Mapping:** `backend/pflichten_events.py`, `map_update_to_rules()` (Z. 52) ordnet
  `legal_updates` per Keyword-Regex auf Titel+Beschreibung den Regeln zu (`RULE_KEYWORDS` Z. 25,
  deckt alle 14 Katalogregeln ab; `update_type` nur als Zusatzhinweis).
- **Persistenz:** `sync_pflichten_events(db, limit=300)` (Z. 64) ist idempotent, läuft lazy beim
  Feed-Abruf (kein Cron) und betrachtet nur die 300 jüngsten `legal_updates`.
  Live 28.09.: 238 Events über 11 Regeln aus 413 `legal_updates`, jüngstes Event 17.09.;
  keine Events für `e_rechnung`, `cra`, `data_act`.
- **API:** `GET /api/pflichten-report/updates`: nur Events zu Regeln mit `applies`/`check`,
  höchstens 50; free → 2 Events + Upgrade-Hinweis, paid → alle; ohne Profil 404.
- **UI:** Abschnitt „Aktuelle Entwicklungen zu Ihren Pflichten" auf `/pflichten-report`.

## Abmahn-Radar (🟢 live, `b9dadc4`, 10.09.)
- `backend/abmahnwellen.py` (389 Z.): 9 kuratierte Wellen (Google Fonts, Banner ohne Ablehnen,
  Tracking vor Einwilligung, Drittanbieter, Datenschutzerklärung, Impressum, Widerruf, BFSG,
  Newsletter ohne Double-Opt-in), je Welle `rule_id`, Säule, Stichwörter, Forderungsspanne nur
  wo belegbar, Hinweis auf § 13 Abs. 4 UWG.
- `GET /abmahnwellen`: Betroffenheit aus Profilstatus und Säulenwert des letzten Scans
  („wahrscheinlich" nur bei `applies` UND Säule < 80). Ohne Profil kein 404, sondern „unbekannt".
  Free: alle Wellen sichtbar, Betroffenheit nur für die zwei relevantesten.
- `dashboard-react/src/components/pflichten/AbmahnRadar.tsx` (317 Z.) ordnet Befunde aus dem
  Scan-Cache des Dashboards per Stichwort zu (Einzelbefunde liegen nicht in einer eigenen Tabelle).
- Nicht verwechseln: `2eb4d4a` hat die **Auswertung von Abmahnschreiben** abgeschaltet, nicht
  den Radar.

## Tests
`backend/tests/test_pflichten_katalog.py` (12: Pflichtfelder/Haftungsdesign, Evidence+Why,
B2C-Shop → BFSG+Widerruf, Kleinstunternehmen → check, KI-Hochrisiko nie `applies`, NIS2,
Sortierung, Robustheit, Fristen konkret, Data Act, CRA), `test_pflichten_events.py` (7),
`test_abmahnwellen.py` (17), `test_tarifempfehlung.py` (11, u. a. Lücke zwischen Archetypen,
keine Beträge im Quelltext), `test_scan_persistenz.py` (9). Suite am 28.09. nicht selbst ausgeführt.

## Bekannte Lücken / Offen
- **Tarifempfehlung ohne Oberfläche:** `grep` über `dashboard-react/src` und `landing-react/src`
  nach `tarifempfehlung`: 0 Treffer. Die Stufen `schlank`/`voll`/`voll_plus` sind nicht auf die
  verkauften Tarife abgebildet.
- **Treiber verraten im Free-Tarif einen Eintrag mehr:** `treiber` wird aus der ungekürzten Liste
  gebildet (bis 4 Titel), sichtbar sind 3 Einträge. Aus dem Code abgeleitet, nicht am Live-Konto
  geprüft.
- **Neuer Säulen-Schreibweg live noch unbelegt:** seit dem Deploy von `3b56959` (25.09.) wurde kein
  Scan in `scan_history` gespeichert (letzter 20.09.); die Befüllung stammt bisher nur aus der
  Nachtrag-Migration.
- **Rechtsraum:** Der Katalog ist deutsches Recht. `scan_context.jurisdiction` wird mitgeliefert,
  vom Dashboard aber nicht angezeigt; bei einem Scan im Profil `eu` fehlt die Säule `legal`, dann
  entfällt der Ist-Zustand bei Impressum und Widerruf. Derzeit laufen alle Scans als `de`
  (siehe [[jurisdiction-kontext]]).
- **Feed-Abdeckung:** Sync nur über die 300 jüngsten `legal_updates`; für `e_rechnung`, `cra`,
  `data_act` liegen live keine Events vor.
- **Nicht gebaut:** E-Mail-/Push-Alert bei neuen Events zu `applies`-Pflichten, PDF-Export des
  Reports, Katalog-Erweiterung (GPSR, Verpackungsgesetz, LkSG-Ausstrahlung, DSA).
