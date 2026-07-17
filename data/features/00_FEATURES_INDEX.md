# Feature-Übersicht (Registry)

> **Zweck:** Single Source of Truth über alle gebauten/laufenden Features, damit
> nichts doppelt gebaut wird und Kontext über Sessions hinweg erhalten bleibt.
>
> **Pflege-Pflicht (WICHTIG):** Bei JEDEM neuen Feature und bei JEDER Änderung an
> einem bestehenden Feature:
> 1. Die zugehörige `data/features/<feature>.md` aktualisieren — **alte Stände raus,
>    aktueller Stand rein** (kein Changelog-Müll, sondern der *gültige* Ist-Zustand).
> 2. Diese Registry-Zeile (Status + Stand) anpassen.
> 3. Vor dem Bauen hier prüfen, ob es das Feature/den Baustein schon gibt.
>
> Status-Werte: `🟢 live` · `🟡 in Arbeit` · `🔵 geplant` · `⚪ verworfen`

> **Vollständigkeit:** Die Registry wird seit 2026-07-17 lückenlos gepflegt (Wellen 1–4).
> Sie ist ausserdem die Quelle für die Vault-Note `complyo-tech-stand` im Hermes-Vault
> (`scripts/sync-vault.sh`, läuft automatisch bei jedem Commit) — eine fehlende Zeile hier
> heisst: das Feature existiert im Second Brain nicht.

| Feature | Doc | Status | Stand |
|---|---|---|---|
| **Scan-/Analyse-Kern** (Quick/Deep/Complete, Check-Registry, Score, Issue-Grouping) | [scan-analyze-kern.md](scan-analyze-kern.md) | 🟢 live | 2026-07-17 |
| **Regulierungs-Radar** (BFSG-Report + AI-Act-Transparenz-Check im Free-Scan) | [regulierungs-radar.md](regulierungs-radar.md) | 🟢 live | 2026-07-17 |
| **Pflichten-Report** (Firmenprofil → 13 Pflichten + lebender Änderungs-Feed; Premium-Gating) | [pflichten-report.md](pflichten-report.md) | 🟢 live (7.2+7.3) | 2026-07-17 |
| **KI-Fix-Engine** (Fix-Generierung, Quality-Gate, Fix-Jobs-Queue) | [ai-fix-engine.md](ai-fix-engine.md) | 🟡 in Arbeit | 2026-07-17 |
| **Cookie-Consent-Widget** (ausgeliefertes JS: Banner v2, Content-Blocker, Consent Mode) | [cookie-consent-widget.md](cookie-consent-widget.md) | 🟢 live (tote Pfade bereinigt) | 2026-07-17 |
| **Cookie-Consent-Management** (Server: Consent-Logging, Katalog, Banner-Config) | [cookie-consent-management.md](cookie-consent-management.md) | 🟡 in Arbeit | 2026-07-17 |
| **Legal Text Generator** (KI-Rechtstexte: Impressum, Datenschutz, AGB, Cookie, Widerruf) | [legal-text-generator.md](legal-text-generator.md) | 🟢 live (Auto-Update jetzt live) | 2026-07-17 |
| **Legal-Change-Monitoring** (EUR-Lex/RSS/KI-Recherche, Klassifikation, Benachrichtigung) | [legal-change-monitoring.md](legal-change-monitoring.md) | 🟡 in Arbeit | 2026-07-17 |
| **AI-Act-Compliance** ("ComplyoAI Guard": KI-Register, Risikoklassifizierung, Doku) | [ai-act-compliance.md](ai-act-compliance.md) | 🟡 in Arbeit | 2026-07-17 |
| **Jurisdiction-Kontext** (internationale Compliance Stufe 1) | [jurisdiction-kontext.md](jurisdiction-kontext.md) | 🟡 Fundament, ohne Wirkung | 2026-07-17 |
| **Billing / Pläne / Add-ons** (Stripe-Abos, Checkout, Webhooks, Plan-Gating) | [billing-plans-addons.md](billing-plans-addons.md) | 🟡 in Arbeit | 2026-07-17 |
| **Agentur / White-Label** (Kundengruppen, Logo, Kundenreports, Agentur-Stats) | [agentur-white-label.md](agentur-white-label.md) | 🟢 live | 2026-07-17 |
| **Lead-/Free-Scan-Funnel** (Scan ohne Login, Double-Opt-in, Warteliste) | [lead-free-scan-funnel.md](lead-free-scan-funnel.md) | 🟡 in Arbeit (leads-Tabelle+Auth gefixt; Double-Opt-in offen) | 2026-07-17 |
| **Alt-Text-KI-Generierung** (Vision-KI für Bild-Alternativtexte + Patches) | [alt-text-ki-generierung.md](alt-text-ki-generierung.md) | 🟢 live | 2026-07-17 |
| **WordPress-Plugin** (Widget, Inline-Blocker, A11y-Remediation, Local Fonts) | [wordpress-plugin.md](wordpress-plugin.md) | 🟢 live (v2.6.0) | 2026-07-17 |
| **Joomla-Plugin** (nur Widget-Einbindung) | [joomla-plugin.md](joomla-plugin.md) | 🟡 Teilstand (v2.1.0) | 2026-07-17 |
| **PDF-Report & Export** (Compliance-Report, Audit-Log) | [pdf-report-export.md](pdf-report-export.md) | 🟢 live (Audit-Log/-Export gefixt) | 2026-07-17 |
| **Admin-Bereich** (Leads, Analytics, System-Health, Fix-Review-Queue) | [admin-bereich.md](admin-bereich.md) | 🟡 faktisch inaktiv (503) | 2026-07-17 |
| **Onboarding & Journey** (Wizards, Schritt-Tracking, Skill-Level) | [onboarding-journey.md](onboarding-journey.md) | 🟡 entkoppelt | 2026-07-17 |
| **Knowledge-Base / Gesetzes-Vault** (Obsidian-Vault: Gesetze + Templates) | [knowledge-base-gesetzes-vault.md](knowledge-base-gesetzes-vault.md) | 🟡 in Arbeit | 2026-07-17 |
| **AVV/DPA-Generator** (Auftragsverarbeitungsvertrag) | [avv-dpa-generator.md](avv-dpa-generator.md) | 🟡 nur HTML-Rendering | 2026-07-17 |
| **TCF 2.2** (IAB-Vendorliste, TCF-Config) | [tcf-2-2.md](tcf-2-2.md) | 🟡 nicht IAB-registriert | 2026-07-17 |
| **DSGVO-Betroffenenrechte** (Auskunft/Löschung/Export, Retention) | [dsgvo-betroffenenrechte.md](dsgvo-betroffenenrechte.md) | 🟡 teilbehoben (Cleanup+Auth gefixt) | 2026-07-17 |
| **MCP-Server** (Complyo-API für KI-Agenten unter `/mcp`) | [mcp-server.md](mcp-server.md) | 🟡 Auth-Gate validiert JWT, Fläche unkuratiert | 2026-07-17 |
| **Channel HTML-CLI** (Fix-Manifest auf statische Projekte anwenden) | [channel-html-cli.md](channel-html-cli.md) | 🟢 live | 2026-07-17 |
| **Risiko-Radar** (Score-Trend, Frühwarnung) | [risiko-radar.md](risiko-radar.md) | 🟡 Backend ohne UI | 2026-07-17 |
| **i18n / Mehrsprachigkeit** (Übersetzungs-API, Widget-Locales) | [i18n-mehrsprachigkeit.md](i18n-mehrsprachigkeit.md) | ⚪ verworfen (alle EP 500) | 2026-07-17 |
| Barrierefreiheits-Remediation (Fix-Manifest + Channels + Link-Zweck + Worklist + Re-Scan) | [accessibility-remediation.md](accessibility-remediation.md) | 🟢 Block 1–3 live | 2026-06-26 |
| Drittlandtransfer-Erkennung (cookielose Transfers: Google Fonts/reCAPTCHA/Maps via HTML+CSS+Requests) | [drittlandtransfer-erkennung.md](drittlandtransfer-erkennung.md) | 🟢 live | 2026-06-26 |
| Cookie-Richtlinie-Seite ("Über Cookies": complyo.de-Seite + öffentlich gehostete /cookie-richtlinie/{site_id} fürs Widget) | [cookie-richtlinie-seite.md](cookie-richtlinie-seite.md) | 🟢 live | 2026-06-27 |
| Deep Cookie Scanner (Playwright-Scan + Katalog-Erkennung + 1-Klick in Banner/Cookie-Richtlinie) | [deep-cookie-scanner.md](deep-cookie-scanner.md) | 🟢 live | 2026-06-27 |

## Registrierte Router ohne Doku — Entscheidung offen

Kein Feature-Doc, weil erst zu entscheiden ist: **nachziehen oder Router entfernen**. Ihre
Tabellen liegen ausschliesslich in `backend/migrations/_archive_pre_baseline/` und sind beim
Baseline-Cut (2026-07-17) **nicht** in `backend/alembic/baseline_schema.sql` übernommen worden —
laut Migrations-Regel darf das Archiv nicht mehr angewendet werden.

| Router | Zustand |
|---|---|
| `backend/ab_test_routes.py` | Hat einen echten Konsumenten: `widgets/cookie_banner_v2.js:445,481`. Live 200 mit `relation "cookie_ab_tests" does not exist` — das Banner schluckt es still. |
| `backend/expert_service_routes.py` | Tot, kein Frontend. Live 500 (Tabelle fehlt). **Kein `Depends(get_current_user)` im ganzen Modul.** |
| `backend/git_routes.py` | Tot, kein Frontend. Live 401 — Auth sauber. Tabellen fehlen. |

Deren Tabellen wurden in der Alembic-Revision `0003_missing_tables` **bewusst
ausgelassen** und stehen als `BEKANNTE_AUSNAHMEN` im Schema-Wächter
(`backend/tests/test_schema_completeness.py`). Entscheidung: Feature bauen (Tabellen
per neuer Revision nachziehen) oder Router entfernen.

<!-- Neue Features als Zeile ergänzen. Doc-Datei = data/features/<kebab-name>.md -->
