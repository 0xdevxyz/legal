# Architektur-Entscheidungen

## ADR-001: verify-checkout als Fallback, Webhook als primär

**Entscheidung:** Stripe-Webhook (`POST /api/payment/webhook`) bleibt primäre Quelle der Plan-Aktivierung.
`GET /api/stripe/verify-checkout` dient als Fallback, falls der Webhook noch nicht verarbeitet wurde.

**Begründung:** Webhooks sind zuverlässiger und serverseitig, aber können verzögert sein. Der Fallback via `verify-checkout` stellt sicher, dass der User unmittelbar nach Rückkehr den korrekten Status sieht.

## ADR-002: Frontend liefert vollständige success_url inkl. Platzhalter

**Entscheidung:** Das Frontend ist verantwortlich für die korrekte `success_url` inklusive `{CHECKOUT_SESSION_ID}`-Platzhalter. Das Backend übergibt diese URL **unverändert** an Stripe.

**Begründung:** Vermeidet doppelte Query-String-Konstruktion und macht die URL-Struktur für den Frontend-Entwickler transparent.

## ADR-003: Subscription-Status als Wahrheitsquelle für Plan-Anzeige

**Entscheidung:** `GET /api/stripe/subscription-status` ist die primäre Quelle für Plan-Name und Status in der UI. Die NextAuth-Session dient als Fallback wenn kein Abo-Eintrag vorhanden.

**Begründung:** Die Session wird nur bei Login aktualisiert. Subscription-Änderungen müssen explizit nachgeladen werden.

## ADR-004: Polling max 6 Versuche × 5 s = 30 s Wartefenster

**Entscheidung:** Bei fehlgeschlagenem `verify-checkout` wird bis zu 6× alle 5 Sekunden retried.

**Begründung:** Stripe-Webhooks kommen typischerweise < 10 s an. 30 s Fenster deckt auch langsame Verbindungen ab.
