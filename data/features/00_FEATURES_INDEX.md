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
| Barrierefreiheits-Remediation (Fix-Manifest + Channels + Link-Zweck + Worklist + Re-Scan) | [accessibility-remediation.md](accessibility-remediation.md) | 🟢 Block 1–3 live | 2026-06-26 |
| Drittlandtransfer-Erkennung (cookielose Transfers: Google Fonts/reCAPTCHA/Maps via HTML+CSS+Requests) | [drittlandtransfer-erkennung.md](drittlandtransfer-erkennung.md) | 🟢 live | 2026-06-26 |
| Cookie-Richtlinie-Seite ("Über Cookies": complyo.de-Seite + öffentlich gehostete /cookie-richtlinie/{site_id} fürs Widget) | [cookie-richtlinie-seite.md](cookie-richtlinie-seite.md) | 🟢 live | 2026-06-27 |
| Deep Cookie Scanner (Playwright-Scan + Katalog-Erkennung + 1-Klick in Banner/Cookie-Richtlinie) | [deep-cookie-scanner.md](deep-cookie-scanner.md) | 🟢 live | 2026-06-27 |

<!-- Neue Features als Zeile ergänzen. Doc-Datei = data/features/<kebab-name>.md -->
