# Pflichten-Report (Firmenprofil → individuelle Pflichten-Einordnung)

**Stand:** 2026-07-17 · **Status:** 🟢 live (Stufe 7.2 des Pflichtenradar-Plans)

## Ziel
Stufe 2 der Pflichtenradar-Evolution: Nutzer beantworten ~12 Profil-Fragen
(Größe, Umsatz, B2C, Shop, KI-Einsatz, B2B-Rechnungen, Sektor …) und bekommen
einen priorisierten Report: **welche Regulierung trifft wahrscheinlich zu,
warum, mit welcher Frist, welchem Bußgeldrahmen und welchem nächsten Schritt.**
Premium-Feature: Free sieht Teaser (Top 3 + Zähler), zahlende Pläne alles.

## Haftungs-Design (RDG, nicht verhandelbar)
- Drei Status, nie ein Rechtsurteil: `applies` („trifft wahrscheinlich zu"),
  `check` („bitte prüfen"), `not_indicated` („keine Indizien im Profil").
- Jede Einordnung trägt `confidence`, `evidence` (die auslösenden
  Profil-Antworten), `why` (Begründung) und `legal_basis`.
- Einzelfallabhängige Einstufungen (AI-Act-Hochrisiko, NIS2) sind hart auf
  maximal `check` begrenzt (per Test abgesichert).
- Disclaimer „Information, keine Rechtsberatung" in jedem Response.
- **Offen vor öffentlichem Marketing-Launch: externe RDG-Klärung** (Positionierung
  als Selbst-Check ist eingebaut, anwaltliche Bestätigung steht aus).

## Architektur
- **Katalog:** `backend/pflichten_katalog.py` — 13 Pflichten als Rules-as-Code
  (DSGVO-Basics, Impressum/DDG, TDDDG-Consent, BFSG inkl.
  Kleinstunternehmen-Ausnahme, AI-Act Art. 50 + Hochrisiko-Check, E-Rechnung,
  NIS2, CRA, UWG-Newsletter, VVT, DSB, Widerruf). `evaluate_pflichten(profile)`
  ist rein deterministisch (keine KI), sortiert applies → check → not_indicated,
  innerhalb nach Bußgeld-Obergrenze.
- **DB:** `company_profiles` (user_id PK → users, answers JSONB) — angelegt als
  **erste reguläre Alembic-Revision nach der Baseline**
  (`alembic/versions/20260717_0002_company_profiles.py`). JSONB-Writes via
  `json.dumps` (asyncpg-Codec-Regel).
- **API:** `backend/pflichten_report_routes.py` (`/api/pflichten-report`),
  kanonische Auth:
  - `PUT /profile` — Whitelist-Filter auf erlaubte Keys, Upsert.
  - `GET /profile` — Antworten laden.
  - `GET /` — Report; hängt an Pflichten mit `scan_pillar` den Ist-Zustand aus
    dem jüngsten `scan_history`-Eintrag des Users (`scan_status.score`).
    Plan-Gating über `user_limits.plan_type`: free/freemium → `locked: true`,
    3 sichtbare Items + `teaser.upgrade_hint`.
- **Dashboard:** `dashboard-react/src/app/pflichten-report/page.tsx` —
  Fragebogen-Wizard (Ja/Nein + Selects), Report mit Status-Karten,
  Law-/Deadline-Badges, Konfidenz + Evidence-Zeile, Scan-Ist-Zustand,
  Upgrade-CTA bei Teaser. Sidebar-Eintrag „Pflichten-Report" (`Sidebar.tsx`).

## Tests
`backend/tests/test_pflichten_katalog.py` (9 Tests): Pflichtfelder/Haftungs-
design je Regel, Evidence+Why je Ergebnis, B2C-Shop→BFSG+Widerruf,
Kleinstunternehmen→check, KI-Hochrisiko nie hartes applies, NIS2-Logik,
Sortierung, Robustheit bei kaputtem Profil. Live-Smoke: Free-User → Teaser
(3/13 sichtbar), Agency-User → 13/13, Kleinstunternehmen-BFSG korrekt `check`.

## Nächste Stufen (gesperrt bis zahlende Kunden, Fokus-Regel)
- 7.3 lebender Pflichten-Graph: Katalog aus dem Legal-Change-Monitoring
  befüllen/aktualisieren, „Pflicht neu/geändert/entfallen"-Alerts als Abo.
- Katalog-Erweiterung (GPSR, Verpackungsgesetz, LkSG-Ausstrahlung, DSA) ist
  Datenpflege im selben Format.
- PDF-Export des Reports (Assets im pdf_report_generator vorhanden).
