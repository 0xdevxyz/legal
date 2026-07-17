# Legal Text Generator (Rechtstexte)

**Stand:** 2026-07-17 · **Status:** 🟢 live — **Auto-Update jedoch tot** (s. u.)

## Ziel
Interner Ersatz für die entfernte eRecht24-Anbindung: KI-generierte Rechtstexte ohne externen
API-Key. **Kein Abmahnschutz-Versprechen** — ein Disclaimer wird automatisch angehängt
(`backend/legal_disclaimer.py`).

## Architektur (end-to-end)
- **Kern:** `backend/legal_text_generator.py` (625 Z.) — Template laden, Prompt bauen,
  KI-Call, deterministische Klauseln anhängen, persistieren.
- **Router:** `backend/legal_text_routes.py` (Prefix `/api/legal-texts`, registriert in
  `backend/main_production.py:614`). `user_id` kommt **serverseitig aus dem Token**
  (`get_current_user_id`, Z. 31–41) — bewusst als IDOR-Schutz.

  | Methode | Pfad | Z. | Zweck |
  |---|---|---|---|
  | GET | `/{doc_type}` | 209 | aktives Dokument; 404 wenn keins |
  | POST | `/{doc_type}/generate` | 246 | neu generieren + speichern · Limit `5/60s` |
  | GET | `/{doc_type}/history` | 299 | Versionshistorie (1–50, default 10) |
  | GET | `/{doc_type}/preview` | 320 | Preview **ohne** Speichern (Onboarding) · Limit `10/60s` · **kein Auth** |

- **Generierung — Template ≠ Output.** Das Markdown-Template ist Prompt-*Input*:
  1. `_load_template(doc_type, language)` (Z. 519) → `knowledge/templates/legal/{type}_{lang}.md`
  2. `_load_laws_context(...)` (Z. 530) → je Gesetz max. 2000 Zeichen aus `knowledge/laws/`
  3. `_build_prompt` (Z. 485) → `{{key}}`-Platzhalter aus `user_data` ersetzen, als
     „## Firmendaten"-Block in den Prompt
  4. `_call_ai` (Z. 445) → **OpenRouter, `anthropic/claude-sonnet-4.5`**, `temperature=0.2`,
     `max_tokens=4000`, Timeout 90 s (Z. 80–82)
  5. deterministische Klauseln + Disclaimer anhängen → `_save` (Z. 581)
- **Deterministische Bausteine** (nur `privacy`, Z. 141–180): `build_complyo_privacy_clause`
  (`backend/complyo_privacy_clause.py`) und `build_third_country_clause`
  (`backend/third_country_clause.py`, Art. 44 ff./49) werden **nach** dem KI-Output angehängt;
  der Prompt weist die KI explizit an, dazu keinen eigenen Abschnitt zu schreiben. Zweck:
  KI-Varianz aus rechtlich heiklen Passagen heraushalten. Siehe [[drittlandtransfer-erkennung]].
- **Dokumenttypen** (`DocumentType`, Z. 49–54) und ihr Gesetzes-Kontext:

  | Typ | Gesetze im Prompt |
  |---|---|
  | `imprint` | Impressumspflicht |
  | `privacy` | DSGVO, TTDSG |
  | `tos` | AGB-Recht, UWG |
  | `cookie-policy` | TTDSG, DSGVO (Bindestrich! eigener Test) |
  | `withdrawal` | Widerrufsrecht, Verbraucherrecht, AGB-Recht |

- **Frontend:** `dashboard-react/src/components/legal/LegalDocumentGenerator.tsx` (1109 Z.),
  5-Step-Wizard, Mapping UI→Backend in `DOC_CONFIG` (Z. 25–37: `impressum`→`imprint`,
  `datenschutz`→`privacy`, `agb`→`tos`, `cookie`→`cookie-policy`, `widerruf`→`withdrawal`).
  API-Client: `dashboard-react/src/lib/api.ts:690/710/731/747`.

## DB
Kanonisches Schema: `backend/init_documents_table.sql` — die Datei deklariert sich selbst als
kanonisch (idempotent, `IF NOT EXISTS`) und hat das frühere, inkompatible Schema
(`doc_type`/`audit_trail`/`version`) ersetzt. Tabelle `generated_documents`:

`id`, `user_id`, `document_type`, `title`, `content` (Plain), `html_content`,
`metadata` (JSONB), `status` (active/archived/draft), `language`, `legal_update_id`,
`template_version`, `regeneration_trigger`, `is_active`, `created_at`, `updated_at`,
`last_reviewed_at`.

- **`user_data` lebt in `metadata`** (Z. 566) — Pflicht, sonst kann nicht automatisch
  regeneriert werden (Z. 418–421: ohne `user_data` → skip). Abgesichert durch
  `tests/test_legal_text_generator.py::test_save_writes_user_data_into_metadata`.
  Für Altbestände: `_archive_pre_baseline/backfill_user_data_in_generated_documents.sql`.

## Bekannte Lücken / Offen
- **Auto-Update feuert nie — das Kernversprechen ist tot.** [[legal-change-monitoring]] ruft
  `on_legal_change` → `regenerate_affected_users(affected_laws=[area.value for area in
  change.affected_areas])` (`legal_change_monitor.py:173`). Übergeben werden **Rechtsbereiche**
  (`datenschutz`, `cookie_compliance`, `impressum`, …), die `doc_type_map` (Z. 378) erwartet
  aber **Gesetzesnamen** (`DSGVO`, `TTDSG`, `Impressumspflicht`, …). Der Substring-Vergleich
  `key.lower() in law.lower()` (Z. 391) trifft für **keinen** der 7 `LegalArea`-Werte je zu
  (durchgezählt) → jeder Lauf endet mit „no affected document types". Es wurde noch nie ein
  Rechtstext automatisch regeneriert. Fix: Mapping `LegalArea` → Gesetzesnamen ergänzen.
- **`generate_withdrawal` ohne Widerrufsrecht im Kontext:** `knowledge/laws/Widerrufsrecht.md`
  und `Verbraucherrecht.md` **existieren nicht**. Von drei angeforderten Gesetzen landet nur
  `AGB-Recht` im Prompt — beim Dokument, dessen ganzer Zweck das Widerrufsrecht ist.
- **Spalten vs. `metadata` divergieren:** `_save` (Z. 581–595) schreibt nur `user_id`,
  `document_type`, `language`, `html_content`, `content`, `metadata`, `status`. Die Spalten
  `is_active`, `legal_update_id`, `template_version`, `regeneration_trigger` werden **nie**
  beschrieben; alle Aktiv-Queries lesen `(metadata->>'is_active')::boolean IS NOT FALSE`
  (Z. 330/403/576). Wer per SQL `WHERE is_active = true` filtert, bekommt **alle** Versionen;
  `status` bleibt immer `'active'`. Die `COMMENT ON COLUMN` der Migration behaupten das
  Gegenteil.
- **EN ist faktisch tot:** Templates für `en` existieren (10 Dateien), aber System-Prompt und
  alle Anweisungen (Z. 459–464, 498–517) sind hartkodiert deutsch, das Frontend sendet fest
  `language: 'de'` (`LegalDocumentGenerator.tsx:279`). `language` ist zudem unvalidiert
  (`_load_template` fällt still auf `_de.md` zurück). Relevant für [[jurisdiction-kontext]] B2.
- **`_fallback_template` (Z. 610) ist kein Template-Fallback:** ohne `OPENROUTER_API_KEY` oder
  bei HTTP≠200 kommt ein Stub („KI-Generierung aktuell nicht verfügbar") statt eines
  Dokuments — entgegen dem Klassen-Docstring (Z. 88).
- **`/preview` ohne Auth:** nur Rate-Limit `10/60s`. Kein Datenleck (verarbeitet nur
  mitgesendete Daten), aber ein **unauthentifizierter OpenRouter-Kostenpfad** (4000 Tokens/Call).
- **Zwei Wizards nebeneinander:** `dashboard-react/src/components/dashboard/LegalTextWizard.tsx:75`
  ruft `/api/v2/legal/generate` (Prefix von `legal_document_routes.py` = AVV/DPA) statt
  `/api/legal-texts/*` — vermutlich Legacy/tot, zu prüfen. Siehe [[avv-dpa-generator]].
- **Toter Code:** `legal_text_routes._get_generator` (Z. 137) unbenutzt; `website_routes.py:301`
  instanziiert den Generator und loggt nur („Trigger Legal Text Generator für neue Website") —
  die im Kommentar beschriebene Funktion existiert nicht. `get_legal_text_generator` (Z. 618)
  ist ein Prozess-Singleton und ignoriert `db_pool` nach dem ersten Aufruf; `website_routes.py:302`
  übergibt eine Connection statt eines Pools → latente Reihenfolgen-Abhängigkeit.
- **Docstring-Drift:** Z. 6 behauptet Nutzung von `ai_document_generator._call_openrouter` —
  trifft nicht zu, der Generator hat ein eigenes `_call_ai`. `legal_text_routes.py:11` listet
  `withdrawal` nicht, obwohl implementiert.
- **eRecht24** steht im Demo-Modus, ist aber bewusst zurückgestellt
  (`planning/STRUKTUR_FIXES_LAUNCH_PLAN.md` Phase 6: „hochziehen, sobald erster Kunde fragt").
  ⚠️ Nicht verwechseln mit dem `demo_mode` in `legal_notification_service.py` — das ist SMTP.

## Abgrenzung
Die **öffentlich gehostete** Cookie-Richtlinie (`GET /cookie-richtlinie/{site_id}`) ist ein
**anderer** Pfad: sie kommt aus `cookie_banner_configs` + Katalog und kennt die echten
konfigurierten Dienste. Der Doctype `cookie-policy` hier ist ein KI-Volltext zum Download im
Dashboard. Bewusst zwei Systeme — siehe [[cookie-richtlinie-seite]] und
[[cookie-consent-management]].
