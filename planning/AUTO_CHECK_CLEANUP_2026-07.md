# Review-Liste: Bereinigung auto-generierter Compliance-Checks (2026-07)

**Status: WARTET AUF FREIGABE — noch NICHTS ausgeführt.**
Alle Angaben aus Live-Read-only-Queries gegen die Prod-DB (2026-07-30).
Aktion ist ausschließlich `status='disabled'` (reversibel, kein DELETE);
`reviewed_by='audit-cleanup-2026-07'` + Grund in `generation_notes`.

Bestand vor Bereinigung: **112 aktive** Checks (49 datenschutz, 39 cookie,
19 shop, 4 barrierefreiheit, 1 impressum). Erwarteter Effekt: **~58 disabled**
(mit Überschneidungen zwischen den Gruppen), Rest bleibt aktiv.

Hinweis: Die Code-Härtung (dieser PR) skippt neutralisierte Checks bereits zur
Laufzeit und kappt risk_euro auf 25.000 € — die DB-Bereinigung macht den
Zustand zusätzlich explizit und die Admin-Queue sauber.

---

## Gruppe 1 — Neutralisierte Detection (15)

Detection fällt immer auf generische DS-Link-Keywords zurück (kein
`content_requirements`) → jede Seite mit Datenschutz-Link „besteht", obwohl der
Titel Inhaltstiefe verspricht. Wirkungslos bzw. täuschend.

`datenschutzerklaerung-vorhanden`¹, `drittlandtransfer-information-datenschutzerklaerung`,
`drittlandtransfer-transparenz-dsgvo`, `drittstaatentransfer-information-pflicht`,
`ga4-datenschutzerklaerung-aktualisierung`, `ga4-us-transfer-information`,
`ki-chatbot-datenschutzerklaerung-hinweis`, `ki-information-datenschutzerklaerung`,
`ki-systeme-datenschutzerklaerung`, `ki-tools-transparenz-datenschutzerklaerung`,
`newsletter-datenschutz-information`, `speicherfristen-datenschutzerklaerung`,
`ttdsg-cmp-einwilligungsdauer-12-monate`, `ttdsg-consent-management-fingerprinting`,
`usa-datentransfer-tia-datenschutzerklaerung`

¹ Existenz-Prüfung ist legitim, aber vollständig vom hartcodierten
`datenschutz_check` abgedeckt (inkl. Soft-404-Guard) — als Duplikat disabled.

```sql
UPDATE compliance_checks SET status='disabled', reviewed_by='audit-cleanup-2026-07',
  generation_notes = COALESCE(generation_notes,'') || ' | disabled 2026-07: detection neutralized (generic privacy-link keywords, no content_requirements)'
WHERE status='active'
  AND detection->'link_href_keywords' ?| ARRAY['datenschutz','privacy','dsgvo']
  AND NOT (detection ? 'content_requirements');
-- erwartet: 15 Zeilen
```

## Gruppe 2 — Invertierte Logik (1)

`google-fonts-lokal-hosting` (id 71): sucht `fonts.googleapis.com` als
PFLICHT-Element → feuert das 5.000-€-Issue genau bei Seiten OHNE externe Google
Fonts und schweigt beim Verstoß. Der korrekte Check läuft über
`privacy_transfer_findings`.

```sql
UPDATE compliance_checks SET status='disabled', reviewed_by='audit-cleanup-2026-07',
  generation_notes = COALESCE(generation_notes,'') || ' | disabled 2026-07: inverted logic (violation indicator as required element)'
WHERE status='active' AND slug='google-fonts-lokal-hosting';
-- erwartet: 1 Zeile
```

## Gruppe 3 — Always-gated Cookie-Banner-Duplikate (32)

Alle duplizieren den hartcodierten `cookie_check` (Banner/Reject/Kategorien/
Widerruf/Dark-Patterns — seit Tier 3 zusätzlich mit Netzwerk-Evidenz), aber mit
vom LLM erfundenen Exakt-Begriffen → chronische False Positives. Darunter
**drei 300.000-€-Checks** (`ttdsg-cookie-consent-mechanism`,
`ttdsg-consent-management-fingerprinting`, `ttdsg-fingerprinting-consent-disclosure`)
und zwei 50.000-€-Checks. Vollständige Liste (32 Slugs) per Query below.

```sql
UPDATE compliance_checks SET status='disabled', reviewed_by='audit-cleanup-2026-07',
  generation_notes = COALESCE(generation_notes,'') || ' | disabled 2026-07: duplicates hardcoded cookie_check; always-gate + exotic patterns => chronic FPs'
WHERE status='active' AND category='cookie' AND applies_when @> '{"always": true}';
-- erwartet: 32 Zeilen
```

## Gruppe 4 — NetzDG (aufgehoben) + DSA/AI-Act-Redundanz (6 + 13)

NetzDG ist seit Feb 2024 durch DSA/DDG **aufgehoben** — 6 aktive Checks zu einem
toten Gesetz: `netzdg-transparenzbericht-plattform`, `netzdg-meldesystem-plattform`,
`netzdg-beschwerdemechanismus`, `netzdg-meldeformular-plattform`,
`netzdg-transparenzbericht-soziale-netzwerke`, `netzdg-meldefunktion-rechtswidrige-inhalte`.

DSA/AI-Act: je Thema bleibt **ein** Vertreter aktiv, Zwillinge werden disabled
(künftige Zwillinge fängt die gehärtete Dedup + Always-Gate-Bremse):

| Thema | bleibt aktiv | disabled |
|---|---|---|
| DSA Meldemechanismus | `dsa-meldemechanismus-rechtswidrige-inhalte` | `dsa-meldewege-illegale-inhalte`, `dsa-notice-and-action-mechanism`, `dsa-beschwerdemechanismus` |
| DSA Transparenzbericht | `dsa-transparenzbericht-online-plattform` | `dsa-transparenzbericht-hosting`, `dsa-transparenzbericht-vlop`, `dsa-vlop-transparency-notice` (VLOP-only, KMU-irrelevant) |
| KI-Kennzeichnung | `eu-ai-act-chatbot-kennzeichnung` (3.500 €) | `eu-ai-act-ki-kennzeichnung`, `ai-act-transparenzhinweis-ki-einsatz` (je 15.000 €), `ki-chatbot-kennzeichnung`, `ki-chatbot-transparenzhinweis`, `ki-chatbot-opt-in-hinweis`, `ki-chatbot-einwilligung-fehlt` |
| Hochrisiko-KI (für KMU-Websites praktisch nie einschlägig) | — | `eu-ai-act-hochrisiko-ki-kennzeichnung`, `ai-act-hochrisiko-ki-transparenzhinweis` |

```sql
UPDATE compliance_checks SET status='disabled', reviewed_by='audit-cleanup-2026-07',
  generation_notes = COALESCE(generation_notes,'') || ' | disabled 2026-07: NetzDG repealed (DSA/DDG 2024)'
WHERE status='active' AND slug LIKE 'netzdg%';
-- erwartet: 6 Zeilen

UPDATE compliance_checks SET status='disabled', reviewed_by='audit-cleanup-2026-07',
  generation_notes = COALESCE(generation_notes,'') || ' | disabled 2026-07: topic duplicate / VLOP-only, irrelevant for SMB'
WHERE status='active' AND slug IN (
  'dsa-meldewege-illegale-inhalte','dsa-notice-and-action-mechanism','dsa-beschwerdemechanismus',
  'dsa-transparenzbericht-hosting','dsa-transparenzbericht-vlop','dsa-vlop-transparency-notice',
  'eu-ai-act-ki-kennzeichnung','ai-act-transparenzhinweis-ki-einsatz',
  'ki-chatbot-kennzeichnung','ki-chatbot-transparenzhinweis','ki-chatbot-opt-in-hinweis','ki-chatbot-einwilligung-fehlt',
  'eu-ai-act-hochrisiko-ki-kennzeichnung','ai-act-hochrisiko-ki-transparenzhinweis'
);
-- erwartet: 14 Zeilen
```

## Ablauf & Rollback

1. **Pre-Flight-Snapshot** (vor jedem UPDATE):
   ```sql
   SELECT id, slug, status FROM compliance_checks WHERE status='active' ORDER BY slug;
   ```
   Output wird als Datei gesichert (Rollback-Grundlage).
2. UPDATEs in obiger Reihenfolge; nach jedem: Zeilenzahl gegen Erwartung prüfen.
3. Registry-Cache invalidiert sich selbst (TTL 300 s) — kein Neustart nötig.
4. **Rollback:** `UPDATE compliance_checks SET status='active' WHERE id IN (<Snapshot-IDs>)`.
5. Nachkontrolle: aktive Checks je Kategorie zählen; Test-Scan gegen 2–3
   Referenzseiten — es dürfen ausschließlich bekannte FP-Findings verschwinden.

**Kundenkommunikation (Changelog-Vorschlag):** „Wir haben unsere automatisch
generierten Prüfungen qualitätsgesichert: fehlerhafte und redundante Prüfungen
wurden entfernt, Risikobeträge realistisch gedeckelt. Scores können sich dadurch
verbessern; neu hinzugekommen ist eine schärfere Erkennung von Tracking vor
Einwilligung (Netzwerk-Beweis)."
