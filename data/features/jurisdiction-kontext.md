# Jurisdiction-Kontext (internationale Compliance, Stufe 1)

**Stand:** 2026-07-17 · **Status:** 🟡 Datenfundament — **ohne Laufzeitwirkung**

> ⚠️ Der Commit-Titel (`3749063 feat: Jurisdiction-Kontext + internationale Compliance-Stufe 1`)
> und der Plan-Name legen ein fertiges Feature nahe. Gebaut ist bisher **nur EPIC B0**
> (Fundament). Die Spalten werden befüllt und ausgeliefert, aber **kein Scan liest sie**.
> Ein EU-Kunde bekommt weiterhin die vollen DE-Fehlalarme und einen verfälschten Score.

## Ziel
Das DE-Produkt an englischsprachige EU-Kunden verkaufen, **ohne** einen zweiten Rechtsraum
zu bauen. Leitsatz aus `planning/STUFE1_INTERNATIONAL_PLAN.md`: „Ein Codebase, Jurisdiction
als Config" — kein Fork. Kernproblem: Die Engine prüft hart deutsche Pflichten (Impressum,
AGB, UWG, PAngV, Widerruf) und bestraft EU-Kunden dafür.

## Architektur (end-to-end)
- **SSOT:** `backend/compliance_engine/jurisdictions.py` (93 Z.)
  - `DEFAULT_JURISDICTION = "de"` (Z. 17), `JURISDICTION_PROFILES` (Z. 19–32),
    `SUPPORTED_JURISDICTIONS` (Z. 34).
  - Helper: `normalize_jurisdiction()` (Z. 37), `is_supported_jurisdiction()` (Z. 48),
    `active_checks()` (Z. 57), `active_pillars()` (Z. 62), `profile_language()` (Z. 67),
    `get_effective_jurisdiction(conn, website_id, user_id)` (Z. 72).
  - `normalize_jurisdiction` fällt bei leeren/unbekannten/Nicht-String-Werten still auf
    `"de"` zurück — Altdaten brechen keinen Scan.
- **Kontext-Objekt:** `backend/compliance_engine/context.py` — `@dataclass ScanContext` (Z. 22)
  mit `url`, `jurisdiction`, `language`, `session`. `__post_init__` normalisiert und leitet
  die Sprache aus dem Profil ab.
- **Profile** (genau zwei):

  | Key | Sprache | aktive Checks | Säulen |
  |---|---|---|---|
  | `de` | de | datenschutz, cookie, impressum, barrierefreiheit, agb, uwg, pangv, widerruf, tcf (9) | accessibility, gdpr, legal, cookies |
  | `eu` | en | datenschutz, cookie, barrierefreiheit, tcf (4) | accessibility, gdpr, cookies |

  Das `eu`-Profil deaktiviert bewusst die DE-only-Checks und die `legal`-Säule.
- **Auflösungskette** (`jurisdictions.py:72`): `tracked_websites.jurisdiction` (Site-Override)
  → `user_limits.jurisdiction` (Account-Default) → `DEFAULT_JURISDICTION`.
  **Keine Auto-Erkennung** — keine IP-Geolokalisierung, keine TLD-Heuristik, kein
  `Accept-Language`. Rein konfigurativ.
- **API:** `backend/website_routes.py` (Prefix `/api/v2/websites`)
  - `GET ""` (Z. 55) — `LEFT JOIN user_limits`; liefert pro Site `jurisdiction` (Roh-Override)
    und `effective_jurisdiction` (aufgelöst).
  - `POST ""` (Z. 108) — `WebsiteCreate.jurisdiction` optional (Z. 32), Validierung mit 400
    bei unbekanntem Wert (Z. 115–122). Im **Update**-Zweig `jurisdiction = COALESCE($4, jurisdiction)` (Z. 140).
- **Registrierung:** `backend/auth_routes.py:65-70` — `init_user_limits()` schreibt
  `DEFAULT_JURISDICTION` beim INSERT in `user_limits`.
- **Frontend:** **keins.** Der Commit hat ausser zwei `tsconfig.tsbuildinfo` keine
  Frontend-Datei angefasst; `grep -rni "effective_jurisdiction" dashboard-react/src` → 0 Treffer.
  ⚠️ Nicht verwechseln: `dashboard-react/src/app/compliance/countries/page.tsx` (11.06., älter
  als dieses Feature) und das `jurisdiction`-Feld im AGB-Generator
  (`components/legal/LegalDocumentGenerator.tsx`) sind der **Gerichtsstand** — fachlich
  unverwandt.

## DB
Quelle ist die Alembic-Baseline (`backend/alembic/versions/20260717_baseline_2026_07.py` →
`backend/alembic/baseline_schema.sql`). In der Live-DB verifiziert:

| Tabelle | Spalte | Default | Semantik |
|---|---|---|---|
| `user_limits` | `jurisdiction` | `'de'` NOT NULL | Account-Default |
| `tracked_websites` | `jurisdiction` | `NULL` | Pro-Site-Override, NULL = erben |

- Die ursprüngliche `backend/migrations/add_jurisdiction.sql` liegt seit der
  Migrations-Konsolidierung in `backend/migrations/_archive_pre_baseline/` und darf **nicht**
  mehr angewendet werden.
- Ein früher geplantes `websites.jurisdiction` existiert nicht — gebaut wurde gegen
  `tracked_websites`.

## Bekannte Lücken / Offen
- **Null Laufzeitwirkung (der Kernpunkt).** Repo-weit verifiziert: `ScanContext`,
  `active_checks()`, `active_pillars()` und `get_effective_jurisdiction()` werden von
  **keinem** Produktivpfad aufgerufen. `compliance_engine/scanner.py:98` lautet unverändert
  `async def scan_website(self, url: str)` — kein `jurisdiction`-Parameter, kein
  `"jurisdiction"` im Ergebnis. Kein Check nimmt einen `context`. Siehe [[scan-analyze-kern]].
- **[BEHOBEN 2026-07-17] `POST /api/v2/websites` verwarf den Override beim Anlegen:** der
  INSERT-Zweig schrieb `jurisdiction` nicht — ein mitgesendeter Wert wurde validiert und dann
  weggeworfen. Fix: INSERT nimmt `jurisdiction` jetzt mit auf (NULL = kein Override).
- **[BEHOBEN 2026-07-17] Override ließ sich nicht zurücksetzen:** `COALESCE($4, jurisdiction)`
  machte „`None` = Override löschen" unmöglich. Fix: `CASE WHEN $5 THEN $4 ELSE jurisdiction END`
  mit `jurisdiction_sent = "jurisdiction" in data.model_fields_set` als Sentinel — „Feld nicht
  gesendet" (unangetastet) wird jetzt von „explizit null" (Override löschen) unterschieden.
  Abgesichert durch `tests/test_website_jurisdiction.py`.
- **[BEHOBEN 2026-07-17] Toter Code entfernt:** `WebsiteJurisdictionUpdate` wurde nirgends
  referenziert und ist raus. (Ein dedizierter PATCH/PUT existiert weiterhin nicht — Setzen läuft
  über `POST` mit dem Sentinel oben.)
- **Account-Default nicht änderbar:** bei Registrierung immer `"de"` (`auth_routes.py:69`),
  kein Endpunkt zum Ändern.
- **Keine Tests** — `backend/tests/` enthält nichts zu Jurisdiction/ScanContext, obwohl der
  Plan das als Abnahmekriterium für B0.2 nennt.
- **Dead entry:** `backend/main_production.py:404` listet `add_jurisdiction.sql` weiterhin in
  `ensure_migrations`; die Datei liegt im Archiv, `os.path.exists()` ist False → wird still
  übersprungen. Aufräumen.
- **Offen bis EU-verkaufsfähig** (`planning/STUFE1_INTERNATIONAL_PLAN.md`): B1 (Engine
  jurisdiction-aware), B2 (Issue-Text-Lokalisierung, `risk_euro` → `risk_amount`+`currency`,
  braucht juristisches EN-Review), A1 (Frontend-i18n, ~300–500 Strings), A3 (hreflang).
  A2 (Multi-Currency-Billing) ist bewusst aufgeschoben.
- **Keine Kopplung an [[drittlandtransfer-erkennung]]**, obwohl „Drittland" aus `eu`-Sicht
  anders definiert ist als aus `de`-Sicht. Weder gebaut noch im Plan.
- `knowledge/laws/_mapping.yaml` (DSGVO Art. 13 → GDPR Art. 13) ist laut Plan die Quelle für
  jurisdiction-abhängige `legal_basis`-Angaben — nicht angebunden.
