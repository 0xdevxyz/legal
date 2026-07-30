# Knowledge-Base / Gesetzes-Vault

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit

## Ziel
Durchsuchbares Rechts-Archiv mit **Doppelrolle**:
- **Kunden-Feature:** Gesetzes-Stammseiten + Rechts-Updates im Dashboard (`/knowledge`),
  inkl. semantischer Suche.
- **Interne Datenbasis:** derselbe Vault liefert Templates und Gesetzeskontext als
  Prompt-Input für den [[legal-text-generator]].

## Architektur (end-to-end)
- **Vault:** Verzeichnis `knowledge/` — echter **Obsidian-Vault** (`.obsidian/`), 30 Markdown-Dateien.
  - `knowledge/laws/` (7 Stammseiten): `DSGVO`, `TTDSG`, `UWG`, `BFSG`, `NIS2`,
    `Impressumspflicht`, `AGB-Recht` — YAML-Frontmatter mit `law_areas`, `affected_checks`, `tags`.
  - `knowledge/laws/de|en|fr|it|pl/`: `GDPR`, `DSA`, `AI_ACT`, `RGPD`, `DSGVO` + `README`s
    (mehrsprachige Ebene, siehe [[jurisdiction-kontext]]).
  - `knowledge/laws/_mapping.yaml`: Cross-linguale Norm-Ontologie (DE-Norm → EU-Norm →
    Übersetzung + `eur_lex_id` + Artikel-Mappings).
  - `knowledge/templates/legal/`: 10 Rechtstext-Templates (`privacy`, `imprint`, `tos`,
    `cookie-policy`, `withdrawal` × `_de`/`_en`).
  - `knowledge/updates/`: existiert, ist aber **leer** (0 Dateien).
- **Deployment:** `docker-compose.yml` mountet `./knowledge:/data/knowledge:ro`,
  `KNOWLEDGE_VAULT_PATH=/data/knowledge`. Befüllung laut Compose-Kommentar durch einen
  Host-Cron (`knowledge_updater`) — im Repo nicht auffindbar, **zu prüfen**.
- **Routes:** `backend/knowledge_routes.py` (Prefix `/api/knowledge`), in
  `main_production.py:635` unbedingt registriert. Alle 6 Routen live.
  - `GET /updates` (Filter `impact`, `law_area`), `GET /updates/{id}` — lesen `updates/*.md`
    Frontmatter; liefern derzeit `[]` bzw. 404, da `updates/` leer ist.
  - `GET /laws` — listet nur `laws/*.md` **auf oberster Ebene** (7); die Sprach-Unterordner
    tauchen im Dashboard nicht auf.
  - `GET /search` — `KnowledgeRetriever.retrieve()` (`backend/knowledge/knowledge_retriever.py`),
    OpenAI `text-embedding-3-small` + Keyword-Score, Cache `_meta/embeddings.json`.
  - `GET /stats` — live verifiziert: `total_documents: 7`, `cached_embeddings: 0`.
  - `POST /trigger-refresh` — startet `ingest_all()` → `classify_batch()` → `MDWriter.write_batch()`
    → `refresh_index()` als `BackgroundTasks`-Job; antwortet sofort `{"status":"started"}`.
- **Retriever-Scope:** `_load_documents()` globt nur `updates/*.md`, `laws/*.md`,
  `patterns/*.md` — **nicht** `laws/<lang>/` und **nicht** `templates/`.
- **Generator-Kopplung:** `backend/legal_text_generator.py`
  - `TEMPLATES_DIR`/`LAWS_DIR` = `os.path.dirname(__file__)/../knowledge/...`
  - `_load_laws_context(names, language)` sucht `laws/<lang>/<Name>.md`, Fallback `laws/<Name>.md`;
    schneidet je Gesetz auf **2000 Zeichen** (`content[:2000]`).
- **Frontend:** `dashboard-react/src/app/knowledge/page.tsx` — ruft `/laws`, `/updates?limit=20`,
  `/search?q=`. `components/dashboard/LegalArchiveModal.tsx` gehört **nicht** hierher: es liest
  `/api/legal-ai/archive` ([[legal-change-monitoring]]).

## DB
- Keine. Der Vault ist reines Dateisystem; Index/Embeddings liegen in `knowledge/_meta/`.
- Damit auch **nicht** von der Alembic-Baseline (`backend/alembic/versions/20260717_baseline_2026_07.py`)
  berührt.

## Bekannte Lücken / Offen
- **[BEHOBEN 2026-07-17] Vault-Pfad im Generator kaputt:** `LAWS_DIR` löste zu
  `/app/../knowledge/laws` = `/knowledge` auf — existiert nicht (Vault liegt auf
  `/data/knowledge`); der [[legal-text-generator]] lief produktiv ohne Templates und ohne
  Gesetzeskontext. Fix: `KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_VAULT_PATH", <repo-relativ>)`
  (`legal_text_generator.py:55`), Fehlschlag loggt jetzt `error` statt stillem Fallback.
  Abgesichert durch `tests/test_knowledge_vault_wiring.py`.
- **[BEHOBEN 2026-07-17] Fehlende Gesetzesseiten:** `generate_withdrawal` fordert
  `_load_laws_context(["Widerrufsrecht", "Verbraucherrecht", "AGB-Recht"])` an, aber
  `knowledge/laws/Widerrufsrecht.md` und `knowledge/laws/Verbraucherrecht.md` fehlten — nur
  `AGB-Recht` griff. Fix: beide Stammseiten im Vault ergänzt (`knowledge/laws/`), Wächter
  `tests/test_knowledge_vault_wiring.py` auf den neuen Sollzustand gezogen. (`_mapping.yaml`
  kennt beide weiterhin nicht — offen.) Siehe [[legal-text-generator]].
- **`updates/` ist leer** → `/updates` liefert dauerhaft `[]`, die Update-Ansicht im Dashboard
  ist faktisch tot. Ob der genannte Host-Cron existiert und läuft: **unklar, zu prüfen**.
- **`trigger-refresh` kann nichts schreiben:** der Mount ist `:ro`. `MDWriter.write_batch()` und
  `_save_cache()` (→ `_meta/embeddings.json`) schlagen im Container fehl; Fehler werden nur
  geloggt, der Endpoint meldet trotzdem `started`. Passt zu `cached_embeddings: 0` → jede Suche
  embeddet neu bzw. fällt auf Keyword-Score zurück.
- **[BEHOBEN 2026-07-17] Auth `trigger-refresh`:** der Code hatte trotz Docstring „(Admin)"
  **keine** Dependency — jede Session mit CSRF-Token konnte den Ingestion-Lauf (OpenAI-Kosten)
  auslösen. Fix: `admin: dict = Depends(require_admin)` (`knowledge_routes.py:158`). Abgesichert
  durch `tests/test_gdpr_knowledge_auth.py`.
- Alle `GET`-Routen sind unauthentifiziert öffentlich. Für Gesetzestexte vertretbar, aber
  bewusst zu entscheiden.
- Sprach-Unterordner und `_mapping.yaml` sind weder in `/laws` noch in der Suche sichtbar.
