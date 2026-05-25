# Smoke Test Report — 2026-05-22

## Login
- **Credentials:** mail@panoart360.de / Panoart2026!
- **Login successful:** YES
- **Dashboard URL after login:** https://app.complyo.de/ (redirected from /login)

## Score visible
- **Score shown:** YES — "Compliance Score: 0%" visible on the dashboard gauge
- **Score value:** 0/100
- **Label:** Kritisch
- **Metric card "Gesamt-Score":** 0

## Visible info on dashboard
- Account plan: "Kostenlos"
- Registered website: https://complyo.de (domain-locked)
- Websites used: 4/3 — "Limit erreicht" (over-limit warning)
- KI-Optimierungen: 0/1 (1 verfügbar)
- Kritische Issues: 0
- Optimierungsprozess: 1/5 steps

## Console errors
| Level   | Message                                                                 |
|---------|-------------------------------------------------------------------------|
| ERROR   | `GET /api/cookie-compliance/stats/complyo-de?days=7` → **500 Internal Server Error** |
| WARNING | `⚠️ Keine issue_groups in analysisData! null` (fired twice)            |
| WARNING | Input elements should have autocomplete attributes (suggested: "current-password") |

## Other console observations
- `hasData: false` — no analysis data loaded for https://complyo.de (no scan result cached)
- `📊 Legal Updates geladen: 3` — legal news feed OK
- Cookie widget loaded but no services configured → no banner shown (expected)
- Accessibility widget v6.0.0 initialized OK

## Visible error messages in UI
- None explicitly shown in the page UI (no red error banners to the user)
- The 500 on cookie-compliance stats endpoint is silent in UI

## Screenshot
- Saved to: `/tmp/final_smoke.png`
- Source: `.playwright-cli/page-2026-05-22T17-16-21-921Z.png`
