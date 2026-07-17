# Risiko-Radar

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit (Backend live, kein UI-Konsument)

## Ziel
Aggregierter Risiko-Score je Domain über fünf Rechtsgebiete (DSGVO, TTDSG, UWG, BFSG, AGB)
plus „Abmahnfallen"-Frühwarnungen aus der Gesetzes-Update-Pipeline
([[legal-change-monitoring]]) — als Dashboard-Karte gedacht.

## Architektur (end-to-end)
- **Router:** `backend/risk_radar_routes.py` (264 Z.), `APIRouter(prefix="/api/risk-radar",
  tags=["risk-radar"])`, registriert in `backend/main_production.py:129` + `:615`.
  Alle 3 Endpunkte live verifiziert (`200`):
  - `GET /score?domain=&user_id=` — liest den **jüngsten** Treffer aus `scan_history`
    (`WHERE url ILIKE %domain%`), rechnet `overall = 100 - compliance_score` und verteilt die
    ersten 20 Issues per `_classify_law_category()` (reines Keyword-Matching auf dem
    Issue-Text) auf die fünf Kategorien, je Treffer `+15` (Deckel 100). Ohne `domain`
    kommt eine Null-Antwort zurück.
  - `GET /early-warnings?severity_min=&limit=&unread_only=` — `legal_updates` der letzten
    90 Tage, gefiltert über `SEVERITY_ORDER`; **Fallback** auf `legal_news` (30 Tage,
    Severity hart `info`), wenn `legal_updates` fehlt/leer ist.
  - `GET /summary?domain=&user_id=` — ruft intern die beiden obigen Funktionen direkt auf
    (kein HTTP) und kürzt auf `top_risks[:3]`.
  - Antworten tragen `DISCLAIMER_SHORT` aus `backend/legal_disclaimer.py` und den Hinweis
    „kein Abmahnschutz-Versprechen".
- **Score-Berechnung:** liegt **komplett inline im Router**. Der aktive
  `RiskCalculator` (`backend/risk_calculator.py`, 349 Z., in `main_production.py:84`
  importiert, `:531` als globale `risk_calculator` instanziiert, genutzt von
  `backend/public_routes.py` → [[scan-analyze-kern]]) wird hier **nicht** verwendet —
  der Docstring in `risk_radar_routes.py:50` („Nutzt risk_calculator") ist falsch.
- **Frontend:** `dashboard-react/src/lib/api.ts` exportiert `getRiskRadarScore()` (Z. 763)
  und `getEarlyWarnings()` (Z. 774). Beide werden **von keiner Datei aufgerufen**
  (`grep -rn` über `dashboard-react/src` und `landing-react/src`: außer der Definition
  null Treffer). Es gibt keine Dashboard-Seite, keine Komponente, keinen Sidebar-Eintrag.
  `/summary` — der eigentlich für die Karte gedachte Endpunkt — hat gar keinen Client.

## DB
Nur lesend, keine eigenen Tabellen: `scan_history` (`url`, `compliance_score`, `issues`),
`legal_updates`, `legal_news`. Keine Migration nötig, kein JSONB-Schreibpfad → die
asyncpg-JSONB-Regel ist hier nicht berührt (`issues` wird per `json.loads` gelesen).

## Bekannte Lücken / Offen
- **Keine Auth, keine Ownership (hoch).** Kein `Depends(get_current_user)` im ganzen Router;
  live ohne jeden Header abrufbar (`GET /api/risk-radar/score?domain=complyo.de` → `200`).
  `domain` ist ein freier Query-Param → der Risiko-Score **jeder gescannten Fremddomain**
  ist öffentlich lesbar. `user_id` wird zwar entgegengenommen, aber in `/score` und
  `/early-warnings` **nirgends benutzt** — es ist keine Zugriffs-, sondern eine Attrappe.
  Über [[mcp-server]] sind diese Routen zusätzlich als MCP-Tools exponiert.
- **Kein Score-Trend.** Trotz Name/Anspruch existiert weder ein History- noch ein
  Trend-Endpunkt; `/score` liest genau **einen** Scan (`ORDER BY created_at DESC LIMIT 1`).
  Ein Verlauf müsste aus `scan_history` aggregiert werden.
- **Teilstand.** Backend fertig, UI fehlt vollständig. Die zwei Funktionen in `api.ts` sind
  tote Exporte. Entweder Dashboard-Karte gegen `/summary` bauen oder Feature zurückbauen.
- **Kategorisierung ist Keyword-Heuristik** (`_classify_law_category`) und die Gewichtung
  (`+15` je Issue) ist willkürlich, nicht kalibriert — Scores sind grob indikativ.
- `unread_only` in `/early-warnings` ist deklariert, aber ohne Wirkung (kein Read-State).
