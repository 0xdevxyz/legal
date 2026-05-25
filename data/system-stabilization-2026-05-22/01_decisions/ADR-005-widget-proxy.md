# ADR-005: Widget-Domain-Fix + First-Party-Proxy

Datum: 2026-05-22
Status: Accepted

## Context
6 von 7 Widgets sind hardcoded auf https://api.complyo.tech (falsche Domain, nicht erreichbar).
Browser-Extensions (uBlock, Adblock Plus) blockieren externe Tracker-Skripte → ERR_BLOCKED_BY_CLIENT.

## Decision
1. Widget-Domain-Fix: Default auf api.complyo.de, konfigurierbar via data-api-base Attribut
2. First-Party-Proxy: static.complyo.de über nginx, Pfade /assets/a.js, /assets/c.js, /assets/o.js
3. AdblockerDetector.tsx: Banner wenn Extension erkannt

## Consequences
- Alle 6 Widgets: API_BASE-Logik anpassen
- gateway/nginx-static-proxy.conf: location /assets/ { proxy_pass ... }
- Widget-Embed-Code in Dashboard: data-api-base="https://api.complyo.de" Default
- Backwards-Compat: alte /widget/accessibility.js Pfade redirecten auf neuen Pfad
