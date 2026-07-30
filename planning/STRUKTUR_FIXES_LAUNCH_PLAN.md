# Complyo – Struktur-Fixes & Launch-Vorbereitung

Stand: 2026-07-17 · Basis: Vollaudit (Backend, Frontend/Plugins, Produkt)
Ziel: Alle strukturellen Audit-Befunde beheben und Complyo vor dem Launch auf einen
separaten Server isolieren. Kanonische Domain ist **complyo.de** — alle Abhängigkeiten
enden auf `.de`, `complyo.tech` wird vollständig eliminiert.

---

## Phase 1 — Sicherheits-Quick-Wins (Woche 1, ~2–3 Tage)

Kleine, isolierte Fixes mit dem höchsten Risiko-Nutzen-Verhältnis. Jeder Punkt ein eigener Commit + Deploy.

- [x] **1.1 OAuth-Signaturprüfung**: `backend/oauth_service.py:134` dekodiert ID-Tokens mit
  `verify_signature: False`. Prüfen, ob nachgelagert validiert wird; sonst Signaturprüfung
  gegen die JWKS des Providers (Google/…) einbauen.
- [x] **1.2 Stilles Auth-Schlucken beheben**: `backend/cookie_compliance_routes.py:60` fängt
  Auth-Fehler und gibt `None` zurück → durch die kanonische Dependency ersetzen (siehe Phase 2),
  bis dahin mindestens `HTTPException(401)` statt `return None`.
- [x] **1.3 Fehler-Detail-Leaks entfernen**: alle `detail=f"...{str(e)}"`-Stellen
  (u. a. `backend/user_routes.py:238`) → generische Client-Meldung, Details nur ins Log.
  Suche: `grep -rn 'detail=f' backend/*.py | grep -i 'str(e)\|{e}'`.
- [x] **1.4 Rate-Limiting auf teure Endpunkte**: slowapi ist registriert, aber nur ~10 Endpunkte
  gedrosselt. `@limiter.limit` ergänzen für: KI-Generierung (ai_fix, legal-texts, alt-text),
  Scanner/Analyze, Deep-Scan, PDF-Export. Richtwerte: KI 5/min, Scan 3/min pro User/IP.
- [x] **1.5 Abnahme**: `pytest backend/tests/test_auth_hardening.py` grün + manueller Smoke
  (Login, Scan, KI-Fix) auf app.complyo.de.

## Phase 2 — Auth-Konsolidierung (Woche 1–2, ~2 Tage)

Befund: 13 eigenständige `get_current_user`-Implementierungen mit abweichender ID-Semantik
(`id` vs. `user_id`, `int` vs. `str`) trotz kanonischer Dependency in `backend/dependencies.py:144`.

- [x] **2.1 Inventur**: `grep -rn "def get_current_user" backend/*.py` → Liste aller 13 Stellen.
- [x] **2.2** Alle Router auf `from dependencies import get_current_user` umstellen; lokale
  Kopien löschen. Rückgabe-Shape der kanonischen Dependency dokumentieren (welche Keys, welche Typen).
- [x] **2.3** ID-Zugriffe vereinheitlichen (ein Key, ein Typ) — Suchen: `.get('user_id')` vs `.get('id')`.
- [x] **2.4 Abnahme**: kompletter Test-Lauf + Smoke aller Hauptflows (Login, Dashboard,
  Cookie-Config, Deep-Scan, Rechtstexte, Billing). Ein Fehler hier = Auth-Bypass-Risiko,
  daher Router-für-Router committen, nicht als Big Bang.

## Phase 3 — Migrations-Konsolidierung (Woche 2, ~1–2 Tage)

Befund: Alembic (2 Versionen) parallel zu 46 losen SQL-Dateien in `backend/migrations/`
plus Ad-hoc-Skripten → kein reproduzierbarer Schema-Stand. **Blocker für die Server-Migration
(Phase 5), daher vor dieser abschließen.**

**Erledigt in Phase 3:** fehlende Tabellen (domain_locks + ComploAI-Guard-Satz) wurden angelegt.
**Ursprünglicher Befund:** Tabellen `domain_locks` und
`ai_scheduled_scans` fehlen in der Prod-DB (500er in user_routes / Worker-Fehler
im Log) — bei der Baseline mit anlegen oder die Features entfernen.

- [x] **3.1 Baseline ziehen**: Live-Schema dumpen (`pg_dump --schema-only`) und als neue
  Alembic-Revision „baseline_2026_07" einfrieren. Alembic `stamp head` auf Prod.
- [x] **3.2 Alte Artefakte archivieren**: die 46 `.sql`-Dateien nach
  `backend/migrations/_archive_pre_baseline/` verschieben; `migrate.py`, `run_migration.py`,
  `init_lead_tables.py` u. ä. Einmal-Skripte ebenfalls archivieren oder löschen.
- [x] **3.3 Regel ab jetzt**: jede Schema-Änderung ausschließlich als Alembic-Revision;
  Hinweis in `CONTRIBUTING.md` + Memory.
- [x] **3.4 Abnahme**: `alembic upgrade head` auf leerer DB erzeugt ein Schema, das mit dem
  Prod-Dump übereinstimmt (Diff via `apgdiff` oder `pg_dump`-Vergleich).

## Phase 4 — Dead Code & Domain-Sweep .tech → .de (Woche 2–3, ~2 Tage)

Reihenfolge wichtig: erst toten Code löschen, dann Domains fixen (viele der 200
`.tech`-Referenzen liegen im toten Landing-Code).

- [x] **4.1 Landing-Dead-Code entfernen** (~4–5k LOC): `ComplyoOriginalLanding.tsx` (1940 LOC),
  `ComplyoViralLanding.tsx`, `ComplyoHighConversionLanding.tsx`, `ComplyoModernLanding.tsx`,
  Verzeichnisse `modern-landing/`, `saas-landing/`, `alfima-landing/` sowie den nicht
  eingebundenen `app/ABTestRouter.tsx`. Aktiv ist nur `EarlyAccessLanding` (`app/page.tsx`).
  Vorher prüfen: `grep -rn "alfima\|ModernLanding\|ViralLanding" landing-react/src --include="*.tsx" -l`.
- [x] **4.2 Domain-Sweep**: alle verbleibenden `complyo.tech`-Referenzen → `.de`
  (`grep -rn "complyo\.tech"` über backend, dashboard-react, landing-react, Plugins, nginx).
  Betroffen u. a.: WordPress-Plugin (`app.complyo.tech` hardcoded!), Joomla-Plugin,
  `dashboard-react/next.config.js`, diverse Rechtsseiten. 301-Redirect `.tech → .de` im
  Gateway bleibt als Fangnetz bestehen.
- [x] **4.3 Plugins konfigurierbar machen**: API-/App-URL in WP- und Joomla-Plugin als
  Konstante mit Default `api.complyo.de` / `app.complyo.de` (ein Ort statt verstreuter Strings).
  Plugin-Versionen bumpen (WP → 2.6.0), neue ZIPs bauen.
- [x] **4.4 Log-Hygiene**: 313× `print()` im Backend → `logging`; 64× `console.log` in den
  Frontends entfernen (mind. aus Auth-/Payment-Pfaden).
- [x] **4.5 Abnahme**: `grep -rn "complyo\.tech"` liefert 0 Treffer in aktivem Code
  (Archiv/Snapshots ausgenommen); Landing + Dashboard bauen fehlerfrei; Widgets laden von api.complyo.de.

## Phase 5 — Server-Isolation & Migration (vor Launch, ~2–3 Tage + DNS-Vorlauf)

Aktuell teilt sich Complyo den Server mit wpma, spamify, loqal, n8n u. a. Ziel: dedizierter
Server, nur Complyo-Stack.

- [ ] **5.1 Vorbereitung (parallel zu Phase 1–4 möglich)**
  - Neuen Server provisionieren (Richtwert: 4 vCPU / 8 GB RAM — Playwright/Chromium im
    Deep-Scan ist der Speichertreiber), Docker + Docker Compose, UFW (nur 22/80/443), fail2ban.
  - DNS-TTL für complyo.de und alle Subdomains (app., api., cdn.) auf 300 s senken — mind. 24 h vor Umzug.
- [ ] **5.2 Stack übertragen**
  - Repo auf neuen Server clonen, `.env` **neu erstellen mit rotierten Secrets**
    (POSTGRES_PASSWORD, REDIS_PASSWORD, JWT_SECRET*, Stripe-Keys prüfen).
    *Achtung: JWT_SECRET-Rotation invalidiert Sessions — bei 11 Nutzern akzeptabel, im Launch-Fenster einplanen.*
  - Images frisch bauen (kein `docker cp`, siehe Deploy-Regel), nginx-Konfigs aus `gateway/`
    + `/etc/nginx/sites-available` übernehmen, Zertifikate via certbot neu ausstellen.
- [ ] **5.3 Datenmigration**
  - Wartungsfenster (nachts, Nutzerbasis klein): `pg_dump` auf altem Server →
    Restore auf neuem → `alembic stamp head` (setzt Phase 3 voraus).
  - Redis nicht migrieren (nur Cache/Blacklist) — Nutzer müssen sich neu einloggen.
- [ ] **5.4 Cutover**
  - Smoke-Test auf neuem Server via `/etc/hosts`-Override VOR DNS-Switch: Login, Scan,
    Banner-Widget-Auslieferung, Cookie-Richtlinie-Seite, Stripe-Webhook (Test-Event),
    WP-Plugin gegen neuen Server.
  - DNS umstellen, alten Server 14 Tage als Fallback behalten (Container gestoppt,
    Daten eingefroren), Stripe-Webhook-URL prüfen, Sentry-Environment umstellen.
- [ ] **5.5 Abnahme**: alle Domains auf neuem Server, SSL gültig, Healthchecks grün,
  ein kompletter Kunden-Durchlauf (Signup → Scan → Banner einbinden → Consent-Log kommt an).

## Phase 6 — Nach dem Launch (Backlog, kein Blocker)

Bewusst NICHT vor dem Launch — Vertriebszeit geht vor:

- God-Files aufteilen: `cookie_compliance_routes.py` (3.650 LOC), `public_routes.py`,
  `main_production.py` → Router/Service/Repository-Schnitt, schrittweise bei Anfassen („Boy-Scout-Regel").
- 661× `except Exception` gezielt verengen (zuerst Payment- und Auth-Pfade).
- NextAuth v5 auf Stable heben, sobald released; `any`-Abbau im Dashboard (217 Stellen).
- Joomla-Plugin-Parität (Local Fonts, Inline-Blocker, A11y-Remediation).
- eRecht24 aus dem Demo-Modus (API-Key-Laden fixen) — **hochziehen, sobald erster Kunde danach fragt.**
- Git-Auto-Deployment (`paramiko` in requirements) — nur bei Kundenbedarf.
- Coverage-Messung + CI-Gate für Backend-Tests.

## Phase 7 — Produkt-Evolution: „Pflichtenradar" (nach Launch + ersten Kunden)

Quelle: `unicorn-idee-pflichtenradar-regulierungs-betriebssystem-fuer-kmu-complyo-evolutionsstufe.md`
(Hermes-Brain, Session 2026-07-17). Kernthese: Complyo ist bereits der Pflichtenradar
für die Nische Website-Recht — die Evolutionsstufe ist das Meta-Layer „Welche Pflichten
gelten für MICH, was kostet Ignorieren, was tue ich Montagfrüh?" als Abo. Kein neues
Projekt, sondern Verbreiterung. Jede Stufe verkauft sich einzeln:

- [x] **7.1 Scan-Verbreiterung** (✅ 2026-07-17, siehe data/features/regulierungs-radar.md) (Wochen, baut auf Vorhandenem): bestehenden Scanner um
  expliziten BFSG-Check-Report + AI-Act-Transparenz-Check erweitern. Assets da:
  AxeScanner, AI-Act-Doku-Generator, Jurisdiction-Kontext. Als Lead-Magnet ausspielen
  („Ist Ihre Website BFSG-konform? 60-Sekunden-Check" — deckt sich mit Vertriebsplan).
- [x] **7.2 Pflichten-Report als Premium-Feature** (✅ 2026-07-17 auf User-Anweisung vorgezogen; RDG-Klärung vor Marketing-Launch offen — siehe data/features/pflichten-report.md): KMU-Profil-Fragebogen (Branche,
  Größe, Produkte, Software; so viel wie möglich aus dem Website-Scan vorbefüllt)
  → generierter „Ihr Pflichten-Report" mit Deadlines und Bußgeld-Risiko in €.
  Vorarbeit nutzen: legal_changes/legal_news-Pipeline, compliance_risk_matrix-Tabelle.
- [x] **7.3 Lebender Pflichten-Graph + Monitoring-Abo** (✅ 2026-07-17: Änderungs-Feed live; E-Mail-Alerts offen): RSS/EU-Lex-Pipeline (existiert)
  → Rules-as-Code-Mapping auf Firmenprofile, „Pflicht neu/geändert/entfallen"-Alerts.
  Der Graph ist der Moat — jedes gemappte Gesetz und jedes Profil compoundet.
- [ ] **7.0 Pflicht-Hausaufgaben VOR 7.2-Launch** (aus der Idee, nicht verhandelbar):
  - **RDG-Klärung**: als Information/Selbst-Check positionieren, nicht als individuelle
    Rechtsprüfung; Anwalts-Netzwerk als Eskalation (Vorbild Smartlaw/Trusted Shops).
  - **Haftungs-Design**: Confidence-Level + Quellenangabe pro Aussage als Kern-Feature
    (nicht als Fußnote) — „dich betrifft nichts" ohne Beleg darf es nicht geben.

Reihenfolge-Regel (Fokus-Wächter): 7.x startet erst, wenn der Launch durch ist und
zahlende Kunden da sind (Ziel aus dem Audit: 10 bis Oktober). 7.1 darf als
Lead-Magnet-Arbeit parallel zum Vertrieb laufen, 7.2/7.3 nicht.

---

## Reihenfolge & Abhängigkeiten

```
Phase 1 (Security)  ──┐
Phase 2 (Auth)      ──┤
Phase 3 (Migrations)──┼──► Phase 5 (Server-Migration) ──► LAUNCH ──► Phase 6
Phase 4 (Domains)   ──┘         (3 ist harter Blocker für 5,
                                 4.2/4.3 müssen vor Cutover fertig sein)
```

Gesamtaufwand Phase 1–5: **ca. 2–3 Wochen** fokussierte Arbeit.
Jede Phase endet mit Commit + Rebuild-Deploy (Regel: nie `docker cp`).
