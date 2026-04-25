# IAB TCF 2.2 – Offizielle Registrierung

## Was ist das?

IAB TCF 2.2 (Transparency & Consent Framework) ist ein Industriestandard für Werbenetzwerke.
Für **Publisher** (AdSense, Ad Manager, AdMob) ist ein registriertes CMP seit Januar 2024 Pflicht für personalisierte Werbung in der EEA.

## Kosten

- **€1.575/Jahr** (IAB Europe, Stand April 2026)
- Einmalige Registrierung gilt für alle Kunden unter der Complyo CMP-ID
- Break-Even: ~10 zahlende Kunden à €15/Monat

## Was dafür nötig ist

1. Registrierung bei IAB Europe: https://iabeurope.eu/tcf-for-cmps/
2. IAB CMP Validation Test bestehen
3. Global Vendor List (GVL) in der UI anzeigen
4. TC String generieren und in `euconsent-v2` Cookie speichern
5. `__tcfapi` vollständig implementieren (Stub ist bereits vorhanden in `cookie_banner_v2.js`)
6. TCF 2.3 Migration beachten (Deadline war Feb 2026 – bei Registrierung sofort auf 2.3 zielen)

## Aktueller Stand

- `__tcfapi` Stub ist implementiert (`cookie_banner_v2.js`)
- Aktivierbar via `data-tcf="true"` auf dem Script-Tag
- WP-Plugin und Joomla-Plugin haben TCF-Checkbox in der Admin-UI
- **Fehlend für offizielle Registrierung:** CMP-ID von IAB + TC String Generator

## Kurzfristige Alternative für AdSense-Kunden

Google hat ein **eigenes kostenloses CMP (ID 300)**, direkt in AdSense/Ad Manager aktivierbar:
> AdSense → Datenschutz und Nachrichten → Nachrichten erstellen

Kunden die AdSense nutzen, können das bis zur eigenen Registrierung nutzen.

## Entscheidung

Registrierung nachholen sobald Kundenbedarf da ist oder Umsatz es rechtfertigt.
