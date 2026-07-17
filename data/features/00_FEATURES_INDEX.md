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
| **KI-Fix-Engine** (Fix-Generierung, Quality-Gate, Fix-Jobs-Queue) | [ai-fix-engine.md](ai-fix-engine.md) | 🟡 in Arbeit | 2026-07-17 |
| **Cookie-Consent-Widget** (ausgeliefertes JS: Banner v2, Content-Blocker, Consent Mode) | [cookie-consent-widget.md](cookie-consent-widget.md) | 🟢 live (tote Pfade) | 2026-07-17 |
| **Cookie-Consent-Management** (Server: Consent-Logging, Katalog, Banner-Config) | [cookie-consent-management.md](cookie-consent-management.md) | 🟡 in Arbeit | 2026-07-17 |
| **Legal Text Generator** (KI-Rechtstexte: Impressum, Datenschutz, AGB, Cookie, Widerruf) | [legal-text-generator.md](legal-text-generator.md) | 🟢 live (Auto-Update tot) | 2026-07-17 |
| **Legal-Change-Monitoring** (EUR-Lex/RSS/KI-Recherche, Klassifikation, Benachrichtigung) | [legal-change-monitoring.md](legal-change-monitoring.md) | 🟡 in Arbeit | 2026-07-17 |
| **AI-Act-Compliance** ("ComplyoAI Guard": KI-Register, Risikoklassifizierung, Doku) | [ai-act-compliance.md](ai-act-compliance.md) | 🟡 in Arbeit | 2026-07-17 |
| **Jurisdiction-Kontext** (internationale Compliance Stufe 1) | [jurisdiction-kontext.md](jurisdiction-kontext.md) | 🟡 Fundament, ohne Wirkung | 2026-07-17 |
| **Billing / Pläne / Add-ons** (Stripe-Abos, Checkout, Webhooks, Plan-Gating) | [billing-plans-addons.md](billing-plans-addons.md) | 🟡 in Arbeit | 2026-07-17 |
| **Agentur / White-Label** (Kundengruppen, Logo, Kundenreports, Agentur-Stats) | [agentur-white-label.md](agentur-white-label.md) | 🟢 live | 2026-07-17 |
| **Lead-/Free-Scan-Funnel** (Scan ohne Login, Double-Opt-in, Warteliste) | [lead-free-scan-funnel.md](lead-free-scan-funnel.md) | 🟡 in Arbeit | 2026-07-17 |
| **Alt-Text-KI-Generierung** (Vision-KI für Bild-Alternativtexte + Patches) | [alt-text-ki-generierung.md](alt-text-ki-generierung.md) | 🟢 live | 2026-07-17 |
| **WordPress-Plugin** (Widget, Inline-Blocker, A11y-Remediation, Local Fonts) | [wordpress-plugin.md](wordpress-plugin.md) | 🟢 live (v2.6.0) | 2026-07-17 |
| **Joomla-Plugin** (nur Widget-Einbindung) | [joomla-plugin.md](joomla-plugin.md) | 🟡 Teilstand (v2.1.0) | 2026-07-17 |
| Barrierefreiheits-Remediation (Fix-Manifest + Channels + Link-Zweck + Worklist + Re-Scan) | [accessibility-remediation.md](accessibility-remediation.md) | 🟢 Block 1–3 live | 2026-06-26 |
| Drittlandtransfer-Erkennung (cookielose Transfers: Google Fonts/reCAPTCHA/Maps via HTML+CSS+Requests) | [drittlandtransfer-erkennung.md](drittlandtransfer-erkennung.md) | 🟢 live | 2026-06-26 |
| Cookie-Richtlinie-Seite ("Über Cookies": complyo.de-Seite + öffentlich gehostete /cookie-richtlinie/{site_id} fürs Widget) | [cookie-richtlinie-seite.md](cookie-richtlinie-seite.md) | 🟢 live | 2026-06-27 |
| Deep Cookie Scanner (Playwright-Scan + Katalog-Erkennung + 1-Klick in Banner/Cookie-Richtlinie) | [deep-cookie-scanner.md](deep-cookie-scanner.md) | 🟢 live | 2026-06-27 |

<!-- Neue Features als Zeile ergänzen. Doc-Datei = data/features/<kebab-name>.md -->
