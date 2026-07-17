# Alt-Text-KI-Generierung

**Stand:** 2026-07-17 · **Status:** 🟢 live

## Ziel
KI-Vision generiert Alt-Texte für Bilder ohne `alt`-Attribut (WCAG 1.1.1). Vorschläge
landen als `pending` im kanonischen Fix-Speicher, gehen erst nach menschlicher Freigabe
(`approved`) live und speisen dann Fix-Manifest, Runtime-Channels und Patch-ZIP.

## Abgrenzung zu [[accessibility-remediation]]
- **Diese Doku** = der **Erzeuger** von Alt-Text-Vorschlägen (KI-Vision-Pfad) plus der
  Patch-Download als Auslieferungsform.
- **[[accessibility-remediation]]** = die **Architektur drumherum**: das Fix-Manifest
  `GET /api/accessibility/fix-manifest/{site_id}` (bedient von `backend/widget_routes.py`,
  liefert **nur Status `approved`**, ETag-revalidiert), die stabile `derive_site_id`, der
  Review-Workflow und die drei Channels (SPA-JS / HTML-CLI / WordPress).
- **Zwei getrennte Alt-Text-Erzeuger — bewusst:**
  - `backend/accessibility_post_scan_processor.py` — läuft automatisch nach jedem Scan,
    ist **heuristisch** (kein KI-Call). Beschrieben in [[accessibility-remediation]].
  - `backend/alt_text_routes.py` + `compliance_engine/ai_alt_text_generator.py` — der
    **KI-Vision-Pfad**, nutzerausgelöst. Diese Doku.
  Beide schreiben in dieselbe Tabelle über denselben Saver → identischer Downstream.
- **Tabellen-Namensfalle:** die dokumentweiten Fixes heißen `accessibility_document_fixes`
  (nicht `document_fixes`); Alt-Texte liegen in `accessibility_alt_text_fixes`. Beide in
  der Baseline verifiziert.

## Architektur (end-to-end)
- **Generator:** `backend/compliance_engine/ai_alt_text_generator.py`
  - Modell: `DEFAULT_ALT_TEXT_MODEL = 'anthropic/claude-haiku-4.5'` (**Zeile 21**,
    Claude Vision, kosteneffizient für Massen-Alt-Texte), Aufruf **über OpenRouter**
    (`OPENROUTER_API_KEY`, im Container gesetzt). Override per ENV
    `COMPLYO_ALT_TEXT_MODEL` (:36). Ergebnis trägt `source: 'claude_vision'` (:183).
  - `generate_alt_text(image_url, context, language)` und
    `generate_alt_text_from_base64(...)`. Ohne API-Key → deterministischer Fallback
    (`source: 'fallback'`, :334) statt Fehler.
- **Routen:** `backend/alt_text_routes.py`, Prefix `/api/accessibility`, **8 Endpunkte**,
  alle mit `Depends(get_required_user)` (kanonische Auth aus `dependencies.py`):
  - `POST /generate-alt-texts` — `rate_limit("alt_text", 5, 60)` → **5/min, erfüllt
    Plan 1.4**. Speichert via `AccessibilityFixSaver.save_alt_text_fixes(status='pending')`.
  - `POST /scan-images` — `rate_limit("a11y_scan_images", 5, 60)`; rendert die Seite
    (`smart_fetch_html`), findet `img` ohne `alt`, zieht Kontext aus `figcaption` bzw.
    Eltern-Element, **deckelt auf 20 Bilder**, überspringt `data:`-URIs.
  - `GET /alt-text-review-queue`, `POST /approve-alt-text` (`custom_alt` überschreibbar;
    `PermissionError` → 403), `GET /link-review-queue`, `POST /approve-link`,
    `GET /worklist` (ein Call für die UI), `POST /rescan` (`a11y_rescan`, 3/60).
  - `db_pool`/`auth_service` werden in `main_production.py:638-640` injiziert.
- **Patch-Download:** `backend/widget_routes.py`
  - `POST /api/accessibility/patches/generate` (Auth via `get_current_user`) — lädt
    `accessibility_alt_text_fixes WHERE status = 'approved'`, baut über
    `backend/accessibility_patch_generator.py` (`AccessibilityPatchGenerator.
    generate_patch_bundle` / `generate_enhanced_bundle`) ein ZIP unter
    `tempfile.gettempdir()/complyo_patches_{download_id}.zip`,
    `download_id = f"{site_id}_{int(time.time())}"`.
  - `GET /api/accessibility/patches/download/{download_id}` — streamt das ZIP.

## DB
Gegen `backend/alembic/baseline_schema.sql` (Revision
`backend/alembic/versions/20260717_baseline_2026_07.py`) verifiziert:
- `accessibility_alt_text_fixes` (:835) — kanonisch: `image_src`, `suggested_alt`,
  `confidence`, `status` (`pending`→`approved`/`rejected`/`deployed`), SERIAL `id`,
  `site_id` als String. Der frühere UUID-Pfad (`image_url`/`generated_alt`/`is_approved`)
  ist abgelöst.
- `accessibility_document_fixes` (:929) — dokumentweit, auto-approved, read-only in der UI.
- Schreibpfad läuft ausschließlich über `AccessibilityFixSaver` → kein direkter
  JSONB-Write aus diesem Feature; asyncpg-JSONB-Regel nicht berührt.

## Bekannte Lücken / Offen
- **`GET /api/accessibility/patches/download/{download_id}` hat KEINE Auth**
  (`widget_routes.py:758-759`, Signatur nur `download_id: str`). `download_id` ist
  `{site_id}_{unix_timestamp}` — beides erratbar (site_id ist die öffentliche
  domain-abgeleitete ID) → fremde Patch-ZIPs sind per Brute-Force über das
  Sekunden-Fenster ziehbar. Gleiche Lücken-Klasse wie die 28 offenen Routen in
  `cookie_compliance_routes.py` (2026-07-17 gefixt). **Hohe Priorität.**
- **Keine Ownership-Prüfung auf `site_id`.** Weder `patches/generate` noch
  `/alt-text-review-queue`, `/link-review-queue`, `/worklist`, `/generate-alt-texts`,
  `/scan-images` prüfen, ob die `site_id` dem eingeloggten User gehört — sie nehmen sie
  als Query-/Body-Parameter. Ein beliebiger eingeloggter User liest damit fremde
  Review-Queues und erzeugt Fixes unter fremder site_id. Auth ✅, Ownership ❌.
  `get_user_site_ids()` aus `cookie_compliance_routes.py:184` wäre der passende
  (multi-site-fähige) Check.
- **`patches/generate` fällt bei DB-Fehler auf hartkodierte Demo-Fixes zurück**
  („Firmenlogo", „Hero-Bild der Website") und liefert sie als echtes Patch-ZIP aus, statt
  zu scheitern → der Kunde patcht seine Quelle mit erfundenen Alt-Texten. Sollte einen
  Fehler werfen.
- **`rate_limit` ist fail-open:** ohne Redis wird das Limit nur geloggt, nicht durchgesetzt
  (`dependencies.py:369-373`). Die 5/min aus Plan 1.4 hängen damit an der Redis-Verfügbarkeit.
- `POST /scan-images` holt eine beliebige, vom Nutzer gelieferte `site_url` serverseitig ab
  — kein SSRF-Schutz erkennbar (**zu prüfen**, ob `smart_fetch_html` intern filtert).
- Der KI-Fallback ohne `OPENROUTER_API_KEY` (`source: 'fallback'`) speichert generische
  Texte mit `confidence` 0.9 als `pending` — der Reviewer sieht der Queue nicht an, dass
  keine Vision gelaufen ist.
- Patch-ZIPs liegen in `/tmp` ohne erkennbares Aufräumen/TTL; „abgelaufen" ergibt sich nur
  aus dem Container-Neustart.
