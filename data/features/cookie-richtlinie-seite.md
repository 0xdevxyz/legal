# Cookie-Richtlinie-Seite ("Über Cookies")

**Stand:** 2026-06-26 · **Status:** 🟢 live

## Ziel
Der „Über Cookies"-/Cookie-Richtlinie-Link im Cookie-Banner führte überall ins Leere
(Ziel `/cookie-richtlinie` existierte nicht). Behoben für **complyo.de selbst** und als
**Produkt-Feature** für Kunden-Websites: eine öffentlich abrufbare Cookie-Richtlinie,
auf die das Widget automatisch verlinkt.

## Teil A — complyo.de eigene Seite
- `landing-react/src/app/cookie-richtlinie/page.tsx` — statische Seite im Stil der anderen
  Legal-Seiten (Datenschutz/Impressum). Cookie-Tabelle ehrlich aus dem, was der eigene
  Banner setzt: `cookie-consent`, `cookie-consent-date` (Local Storage, essenziell);
  Analytics/Marketing nur nach Einwilligung. §25 TDDDG, Rechte, Verwaltung.
- Footer-Links ergänzt: `landing-react/src/components/saas-landing/FooterSection.tsx`
  (aktiver Footer), plus Cross-Links in `datenschutz/page.tsx` und `impressum/page.tsx`.
- Kontakt-Mail bewusst `datenschutz@complyo.de` (NICHT .tech — .tech ist tot).

## Teil B — Kunden-Produkt: gehostete Cookie-Richtlinie
**SSOT:** `backend/cookie_compliance_routes.py`
- Helper `_load_cookie_policy(db_pool, site_id, lang)` → `(policy_dict, configured)`.
  Lädt aktive `cookie_banner_configs` + verknüpfte `cookie_services` (Name/Anbieter/
  Beschreibung/echte Cookies, kategorisiert necessary/functional/analytics/marketing).
  Gemeinsame Quelle für JSON **und** HTML (keine Duplikation).
- JSON-Route (unverändertes Verhalten): `GET /api/cookie-compliance/policy/{site_id}`.
- **Öffentliche HTML-Seite:** `GET /cookie-richtlinie/{site_id}` (kein Login) →
  eigenständige, gestylte HTML-Seite mit Dienst-/Cookie-Tabelle, §25 TDDDG-Rechtsgrundlage,
  Links zu Datenschutz/Impressum (falls in Config gesetzt). `noindex`, 5 min Cache.
  Erreichbar unter **`https://api.complyo.de/cookie-richtlinie/{site_id}`** (nginx
  `api.complyo.de location /` → backend:8002; Router ohne Prefix).
- **Auto-Default:** `get_banner_config` liefert `cookie_policy_url` =
  `public_cookie_policy_url(site_id)`, wenn der Kunde keine eigene URL gesetzt hat (beide
  Branches: no-row-Default + gespeicherte Config). Basis-URL: env `PUBLIC_API_BASE`,
  Fallback `https://api.complyo.de`.
- Widget übernimmt das: `backend/widgets/cookie_banner_v2.js` fetcht
  `/api/cookie-compliance/config/{site_id}` (Z. 422) und mappt `cookie_policy_url`→
  `cookiePolicyUrl` (Z. 561), rendert den Link (Z. 1967). Kunde muss nichts tun.

## Dashboard
`dashboard-react/src/components/cookie-compliance/CookieBannerDesigner.tsx`:
Feld „Cookie-Policy-URL" Default leer (statt `/cookie-richtlinie`) + Hinweis
„leer = von Complyo gehostet". Eigene URL überschreibt weiterhin.

## site_id
Hostname mit Punkten→Bindestrichen (`complyo.de` → `complyo-de`,
`_url_to_site_id` in cookie_compliance_routes.py). Öffentlich/erratbar — bei öffentlicher
Cookie-Richtlinie unkritisch (Inhalt ist ohnehin öffentlich).

## Abgrenzung
- KI-Cookie-Richtlinie (Doctype `cookie-policy`, `legal_text_generator.py`,
  `generated_documents`, JWT, Dashboard-Anzeige) ist ein **separater** Pfad (Volltext-
  Dokument zum Download). Die öffentlich gehostete Seite nutzt bewusst den
  **site-basierten** Generator, weil er die echten konfigurierten Dienste/Cookies kennt.
- Offen/optional (Teil C, noch nicht gebaut): Deep-Cookie-Scan-Ergebnisse direkt als
  Cookie-Inventar in die Seite einspeisen für eine vollständige Cookie-Tabelle.
