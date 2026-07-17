# AVV/DPA-Generator

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit

## Ziel
Auftragsverarbeitungsvertrag (AV-Vertrag, Art. 28 DSGVO) als HTML generieren.
Perspektivisch: verpflichtender Onboarding-Schritt, weil Complyo durch Cookie-Banner
([[cookie-consent-widget]]) und A11y-Assistent ([[accessibility-remediation]]) selbst
Auftragsverarbeiter des Kunden wird.

## Architektur (end-to-end)
- **Route:** `backend/legal_document_routes.py` (Prefix `/api/v2/legal`, Tag `legal-documents`).
  - Registrierung: Import `main_production.py:122`, `init_legal_document_routes(db_pool, auth_service)`
    in Zeile 553, `app.include_router(legal_document_router)` in Zeile 634. Live in `openapi.json`.
  - **`POST /api/v2/legal/generate-dpa`** — einzige Route der Datei.
    - Auth: `Depends(get_current_user)` aus `backend/dependencies.py` (kanonische Dependency).
      Der Kommentar im Modul dokumentiert den Vorgängerbug: `await auth_service.verify_token(...)`
      auf einer synchronen Funktion → `TypeError` → alle Anfragen 401.
    - Body `DpaRequest`: `controller_*`, `processor_*`, `processing_purposes`, `data_categories`,
      `data_subjects`, `processing_duration`, `subprocessors`, `date` — alle mit
      `min_length`/`max_length`-Constraints.
    - Rendering: Jinja2 `Environment(autoescape=select_autoescape(['html']))` über die
      Modulkonstante `DPA_TEMPLATE_HTML` (Inline-Template, **nicht** aus dem Vault der
      [[knowledge-base-gesetzes-vault]]).
    - Response `DpaResponse`: `html`, `filename` (`av-vertrag-<TT-MM-JJJJ>.html`), `generated_at`.
- **Frontend:** `dashboard-react/src/components/legal/LegalDocumentGenerator.tsx`, eingebunden
  aus `components/dashboard/ComplianceIssueGroup.tsx:445`. Mehrschrittiger Wizard; leitet aus
  `detected_services` des Scans ([[scan-analyze-kern]]) Vorbelegungen ab und pflegt ein
  Freitextfeld `third_party_services`.
- `init_routes(pool, auth_svc)` setzt Modul-Globals `db_pool`/`auth_service` — **beide werden
  von keiner Route benutzt**.

## DB
- **Keine.** `generate-dpa` ist zustandslos: kein `INSERT`, keine Persistenz in
  `generated_documents`, kein `dpa_acceptances`. Der Vertrag existiert nur als
  Response-HTML.
- Kein Bezug zur Alembic-Baseline (`backend/alembic/versions/20260717_baseline_2026_07.py`);
  eine künftige `dpa_acceptances`-Tabelle wäre als neue Revision anzulegen (die 46 Altdateien
  in `backend/migrations/_archive_pre_baseline/` sind gesperrt).

## Bekannte Lücken / Offen
- **Toter Frontend-Pfad (verifiziert):** `dashboard-react/src/components/dashboard/LegalTextWizard.tsx:75`
  ruft `apiClient.post('/api/v2/legal/generate', ...)`. Diese Route **existiert nicht** — im
  produktiven `openapi.json` (302 Pfade) liegt unter `/api/v2/legal` ausschließlich
  `generate-dpa`. `LegalTextWizard` wird aus `components/dashboard/FixResultModal.tsx:113`
  gerendert, ist also erreichbar und läuft ins Leere. Derselbe Befund ist in
  [[legal-text-generator]] vermerkt; der lebende Generator hängt unter `/api/legal-texts/*`.
- **Titel vs. Realität:** „Generiert AVV aus den erkannten Drittanbietern" trifft nicht zu.
  `processor_*` und `subprocessors` sind Pflicht-/Freitextfelder aus dem Formular; es gibt
  **keine** automatische Ableitung aus `detected_services` oder dem `cookie_services`-Katalog
  ([[deep-cookie-scanner]]). Die Service-Erkennung im Wizard belegt nur die Rechtstext-Felder vor.
- **Ownership:** `get_current_user` authentifiziert, aber es gibt kein Objekt mit Eigentümer —
  ohne Persistenz ist Ownership derzeit nicht anwendbar. Sobald `dpa_acceptances` kommt, ist
  eine Ownership-Prüfung zwingend (vgl. die am 2026-07-17 in `cookie_compliance_routes.py`
  geschlossenen 28 offenen Routen).
- **Geplant vs. gebaut** (`planning/AVV_ONBOARDING_PLAN.md`): gebaut ist allein das HTML-Rendering.
  Offen sind alle 5 Schritte des Plans:
  - `dpa_acceptances` (user_id, accepted_at, `dpa_version`, `controller_snapshot` JSONB, IP,
    UA, Dokument/Hash) + `DPA_VERSION`-Konstante. Beim JSONB-Feld gilt die asyncpg-Regel:
    Pool ohne json-Codec → immer `json.dumps()`, sonst `DataError`/500.
  - Onboarding-Pflichtschritt + **backendseitiges** Gate auf
    `cookie_banner_configs.is_active` und Fix-Package-Deploy.
  - Bestandskunden-Migration + Report „aktive Kunden ohne AVV".
  - Wortlaut-Upgrade in `backend/complyo_privacy_clause.py` (`COMPLYO_AVV_HINT`:
    „stellt einen AVV bereit" → „hat einen AVV geschlossen") erst **nach** dem Gate.
  - Download/Nachweis im Dashboard.
  - Der Plan verweist auf `POST /api/legal-documents/generate-dpa` — der reale Prefix ist
    `/api/v2/legal`; der Plan ist an der Stelle veraltet.
- **Offene Entscheidungen laut Plan:** Firmierung („Complyo" vs. „Complyo GmbH", Handelsregister)
  und die verbindliche Unterauftragnehmer-Liste (Hosting, OpenRouter/Anthropic, E-Mail) für
  § 4 des AVV. `DPA_TEMPLATE_HTML` enthält keine Complyo-Defaults als Auftragnehmer.
