# Jurisdiction-Kontext (internationale Compliance, Stufe 1)

**Stand:** 2026-09-28 · **Status:** 🟡 Engine rechtsraumfähig (Block 0 + 1), im Produkt nicht angeschlossen: jeder Live-Scan läuft als `de`

> Die Engine kann seit `726f699` (23.09.) je Rechtsraum andere Prüfungen und Säulen werten.
> Kein Produktivaufrufer reicht den Rechtsraum aber durch: alle Scan-Einstiege rufen
> `scan_website(url)` bzw. `scan_website_multipage(...)` ohne `jurisdiction` auf, und
> `scan_website_multipage` hat den Parameter gar nicht. Ergebnis: Ein Website-Override `eu`
> wird gespeichert und in der API angezeigt, wirkt aber auf keinen Scan.
> Live-DB 28.09.: `user_limits` 21 x `de`, `tracked_websites` 7 x NULL, kein einziges `eu`.

## Ziel
Das DE-Produkt an EU-Kunden außerhalb Deutschlands verkaufen, ohne einen zweiten Rechtsraum
zu forken. Leitsatz aus `planning/STUFE1_INTERNATIONAL_PLAN.md`: „Ein Codebase, Jurisdiction
als Config". Kernproblem: Die Engine prüft deutsche Pflichten (Impressum, AGB, UWG, PAngV,
Widerruf) und nennt deutsche Gesetze (BFSG, TDDDG) auch dort, wo sie nicht gelten.

Die Umsetzung läuft in Blöcken (Benennung aus den Commits und Code-Kommentaren):
- **Block 0** (`c50d166`, 23.09.): Rechtsgrundlagen als Daten, europäischer Kern + nationaler Anker. Erledigt.
- **Block 1** (`726f699`, 23.09.): Engine liest den Rechtsraum. Erledigt, aber nicht verdrahtet (siehe oben).
- **Block 3**: Textkatalog mit stabilen Befundcodes, Titel/Beschreibungen/Empfehlungen ohne deutsche Gesetzesnamen. Offen.
- Block 2: Inhalt nicht geprüft.

## Architektur (end-to-end)
- **SSOT:** `backend/compliance_engine/jurisdictions.py` (111 Z.)
  - `DEFAULT_JURISDICTION = "de"` (Z. 18), `JURISDICTION_PROFILES` (Z. 20-44),
    `UNIONSWEIT` (Z. 53), `SUPPORTED_JURISDICTIONS` (Z. 55).
  - Helper: `normalize_jurisdiction()` (Z. 58), `is_supported_jurisdiction()` (Z. 70),
    `active_checks()` (Z. 75), `active_pillars()` (Z. 80), `profile_language()` (Z. 85),
    `get_effective_jurisdiction(conn, website_id, user_id)` (Z. 90).
  - `normalize_jurisdiction` fällt bei leeren, unbekannten oder Nicht-String-Werten still auf
    `"de"` zurück. Altdaten brechen keinen Scan.
- **Profile** (genau zwei; ein Profil `at` oder andere Länderprofile gibt es nicht):

  | Key | Sprache | aktive Prüfungen | Säulen |
  |---|---|---|---|
  | `de` | de | datenschutz, cookie, impressum, barrierefreiheit, agb, uwg, pangv, widerruf, tcf + unionsweit (15) | accessibility, gdpr, legal, cookies |
  | `eu` | en | datenschutz, cookie, barrierefreiheit, tcf + unionsweit (10) | accessibility, gdpr, cookies |

  Unionsweit (`UNIONSWEIT`, in beiden Profilen): ai_act, ki_bild, ssl, kontakt, social,
  deklarativ. Seit `726f699` nennt die Registry alles, was der Scanner ausführt (vorher 9 von 14).
- **Kontext-Objekt:** `backend/compliance_engine/context.py`, `@dataclass ScanContext` (Z. 22)
  mit `url`, `jurisdiction`, `language`, `session`. `__post_init__` normalisiert und leitet die
  Sprache aus dem Profil ab. Die Sprache wird derzeit von keinem Check für Texte genutzt.
- **Scanner:** `backend/compliance_engine/scanner.py`
  - `scan_website(url, progress_token=None, jurisdiction=DEFAULT_JURISDICTION)` (Z. 695):
    baut `ScanContext` (Z. 714), `aktive_pruefungen = active_checks(...)` (Z. 715).
  - Prüfliste benannt statt positionsweise: `_wenn(name, koroutine)` (Z. 865) startet eine
    Prüfung nur, wenn sie im Profil aktiv ist, sonst wird die Koroutine geschlossen.
  - `MODUL_DECKT_AB = {"shop": ("pangv", "widerruf")}` (Z. 350): shop_check läuft, sobald
    einer der beiden Registry-Namen aktiv ist (Z. 894).
  - Punktestand nur über `active_pillars()` (Z. 1060, `ScoreCalculator.compute_with_status(..., aktive_saeulen=...)`).
  - Ergebnis trägt `jurisdiction`, `gewertete_saeulen`, `score_hinweis` (Z. 1110-1118; `53cea2f`).
    Gemessen laut Commit an panoart360.de: `de` 50 Punkte über vier Säulen, `eu` 34 über drei.
    Punktestände verschiedener Rechtsräume sind nicht vergleichbar.
  - `scan_website_multipage(url, max_seiten, progress_token, zeitbudget)` (Z. 491) hat
    **keinen** `jurisdiction`-Parameter und ruft `scan_website(url, progress_token=...)` (Z. 520).
- **Landesgatter deklarativer Prüfungen:** `backend/compliance_engine/declarative_check_runner.py`,
  `_gate_passes(..., jurisdiction)` (Z. 167, Schlüssel `applies_when.land` ab Z. 184).
  `land` schlägt `always`; fehlt der Schlüssel, gilt die Prüfung überall.
  Live 28.09.: 34 aktive `compliance_checks`, davon 0 mit `land`.
- **Rechtsgrundlagen:** `backend/compliance_engine/rechtsgrundlagen.py` (228 Z., `c50d166`)
  - Themen (10) mit `EUROPAEISCH` (Z. 93), `VERBUND` (Z. 108), `ANKER` je Rechtsraum (Z. 129).
  - Zwei Verbundarten: `ZUSAMMEN` (Barrierefreiheit: „WCAG 2.1 ..., BFSG §12" bzw.
    „..., EN 301 549") und `ERSETZT` (Cookies, Impressum, Shop, UWG: in `de` der nationale
    Anker, ohne Anker die Richtlinie). Bei `ERSETZT` entfällt `detail` ohne Anker, damit keine
    erfundene Fundstelle entsteht.
  - `grundlage(thema, jurisdiction, detail)` (Z. 171), `anker()` (Z. 164). Unbekanntes Thema wirft.
  - Live im Container geprüft: `grundlage(COOKIE_EINWILLIGUNG, "eu")` → „Richtlinie 2002/58/EG
    Art. 5 Abs. 3", `"de"` → „TDDDG §25".
  - Umgestellt sind die `legal_basis`-Werte der Barrierefreiheits- und Cookie-Säule (39 Fundstellen
    laut `c50d166`) sowie Kontaktweg, Newsletter, Direktwerbung und der säulenweite KI-Befund
    (`726f699`). Impressum, AGB, Shop, UWG nennen weiter feste deutsche Angaben (im Profil `eu`
    ohnehin abgeschaltet).
- **Auflösungskette** (`jurisdictions.py:90`): `tracked_websites.jurisdiction` (Site-Override)
  → `user_limits.jurisdiction` (Account-Default) → `DEFAULT_JURISDICTION`. Keine
  Auto-Erkennung (keine IP-Geolokalisierung, keine TLD-Heuristik, kein `Accept-Language`).
  `get_effective_jurisdiction()` hat **keinen** Aufrufer im Produktivcode.
- **API:** `backend/website_routes.py` (Prefix `/api/v2/websites`)
  - `GET ""` (Z. 98): `LEFT JOIN user_limits`, liefert je Site `jurisdiction` (Roh-Override)
    und `effective_jurisdiction` (aufgelöst, Z. 131-133).
  - `POST ""` (Z. 151): `WebsiteCreate.jurisdiction` optional (Z. 78). Unbekannter Wert → 400
    (Z. 165-168). Sentinel `jurisdiction_sent = "jurisdiction" in data.model_fields_set` (Z. 162):
    Feld nicht gesendet = unangetastet, explizit null/"" = Override löschen, `de`/`eu` = setzen.
    Update-Zweig `CASE WHEN $5 THEN $4 ELSE jurisdiction END` (Z. 191), INSERT-Zweig schreibt
    den Override mit (Z. 219-230). Kein eigener PATCH/PUT.
- **Registrierung:** `backend/auth_routes.py`, `init_user_limits()` (Z. 118) schreibt
  `DEFAULT_JURISDICTION` beim INSERT in `user_limits` (Z. 139-143).
- **Persistenz:** `backend/scan_persistenz.py` (97 Z., `3b56959`): `werte_fuer_insert()` liefert
  Gesamtwert, vier Säulenwerte und `jurisdiction` für alle drei INSERTs in `scan_history`
  (`public_routes.py:600`, `main_production.py:1309` und `:1442`). `public_routes.py` legt
  zusätzlich `jurisdiction`, `gewertete_saeulen`, `score_hinweis` in `scan_data` ab (Z. 584-586).
- **Frontend:** keins. `grep` über `dashboard-react/src` nach `effective_jurisdiction`,
  `score_hinweis`, `gewertete_saeulen`: 0 Treffer. Keine Rechtsraumauswahl im Dashboard.
  Nicht verwechseln: `jurisdiction` in `components/legal/LegalDocumentGenerator.tsx`,
  `lib/api.ts:780` und `backend/legal_text_routes.py:103` ist der **Gerichtsstand** im
  AGB-Generator, fachlich unverwandt.

## DB
Quelle ist die Alembic-Kette (live `alembic_version` = `0036_ki_erlaubnis`).

| Tabelle | Spalte | Default | Semantik |
|---|---|---|---|
| `user_limits` | `jurisdiction` | `'de'` NOT NULL | Account-Default (Baseline) |
| `tracked_websites` | `jurisdiction` | `NULL` | Pro-Site-Override, NULL = erben (Baseline) |
| `scan_history` | `jurisdiction` | `VARCHAR(8)` | Rechtsraum des gespeicherten Punktestands (Migration `20260925_0035_scan_saeulen_rechtsraum.py`) |

- Migration 0035 hat Altzeilen auf `'de'` gesetzt und die Säulenwerte aus `scan_data` nach oben
  geholt. Live 28.09.: 51 Zeilen, alle `de`; `overall_score` 51, Säulenwerte 45 bzw. 50 befüllt.
- Letzter gespeicherter Scan 2026-09-20. Seit dem Deploy von `3b56959` (Container-Start
  25.09. 08:53 UTC) wurde **kein** Scan gespeichert: der neue Schreibweg ist live noch nicht
  an einer echten Zeile belegt.
- Die alte `backend/migrations/add_jurisdiction.sql` liegt nur noch in
  `backend/migrations/_archive_pre_baseline/` und darf nicht angewendet werden.

## Tests
`test_engine_rechtsraum.py` (17: Vorgabe bleibt `de`, Registry = Scanner, nationale Prüfungen
nicht in `eu`, keine Säule `legal` in `eu`, Landesgatter, Ergebnis nennt Rechtsraum und
Unvergleichbarkeit), `test_rechtsgrundlagen.py` (12), `test_rechtsraum_waechter.py` (4: Wächter
aus `jurisdictions.py` abgeleitet, Bestandsdeckel `DECKEL = 110` deutsche Gesetzesnennungen,
darf nur sinken), `test_scan_persistenz.py` (9, liest alle drei INSERTs),
`test_website_jurisdiction.py` (8). Laut `53cea2f`: 2816 bestanden, 23 übersprungen.
Suite am 28.09. nicht selbst ausgeführt.

## Bekannte Lücken / Offen
- **Rechtsraum nicht durchgereicht (Kernpunkt).** Kein Scan-Einstieg ruft
  `get_effective_jurisdiction()` auf oder übergibt `jurisdiction`: `public_routes.py:256`
  (Dashboard-Mehrseitenscan), `public_routes.py:2132`, `main_production.py:1174` und `:1375`,
  `cronjobs/website_monitor.py:203`, `live_validator.py`, `deep_scanner.py`. Dazu fehlt der
  Parameter in `scan_website_multipage`. Bis das verdrahtet ist, ist das Profil `eu` nur im
  Test erreichbar.
- **Keine Rechtsraumauswahl im Dashboard**, Account-Default nicht änderbar (bei Registrierung
  immer `de`, kein Endpunkt). Setzen des Site-Overrides nur per API (`POST /api/v2/websites`).
- **`score_hinweis` wird nirgends angezeigt.** Er steht im Scanergebnis und in `scan_data`,
  das Dashboard liest ihn nicht.
- **Texte bleiben deutsch (Block 3 offen).** Titel, Beschreibungen, Empfehlungen nennen weiter
  deutsche Gesetze („Barrierefreiheitserklärung fehlt (BFSG §14)"). `ScanContext.language` wird
  nicht verwendet. Das Erkennungsmuster in `deep_content_analyzer.py` bleibt bewusst deutsch.
  Der Prüfnachweis setzt `lang` über `SPRACHE_DES_INHALTS = "de"` (`nachweis_seite.py:25`).
- **Schreibweisen der Anker ungeprüft:** „BFSG §12" usw. übernommen wie im Prüfkern; die
  richtige Zitierweise gehört laut Code-Kommentar zur anwaltlichen Prüfung (Kennung A1).
- **`risk_euro`** ist weiter eine Euro-Angabe ohne Währung (Plan B2), nicht angefasst.
- **Pflichten-Report kennt keinen Rechtsraum:** der Katalog ist deutsches Recht; er liest nur den
  Rechtsraum des letzten Scans mit aus (siehe [[pflichten-report]]).
- **Dead entry:** `backend/main_production.py:524` listet `add_jurisdiction.sql` in
  `ensure_migrations`. `backend/migrations/` enthält nur noch `_archive_pre_baseline/`, damit
  werden alle sieben Einträge der Liste still übersprungen. Aufräumen.
- **Keine Kopplung an [[drittlandtransfer-erkennung]]**, obwohl „Drittland" aus `eu`-Sicht
  anders gilt als aus `de`-Sicht. Nicht gebaut.
- `knowledge/laws/_mapping.yaml` (DSGVO → GDPR) ist nicht angebunden; kein Python-Modul liest es.
- Weitere Länderprofile (z. B. `at`) existieren nicht und sind nicht begonnen.
- Frontend-i18n (Plan A1), hreflang (A3), Multi-Currency (A2) offen; Stand im Plan nicht geprüft.
