# Drittlandtransfer-Erkennung (cookielose Datentransfers)

**Stand:** 2026-06-26 · **Status:** 🟢 live

## Ziel
Erkennt Drittanbieter-Ressourcen, die beim Seitenaufruf die IP-Adresse des Besuchers
**ohne Einwilligung** an Server außerhalb der EU/des EWR übertragen — **auch wenn dabei
kein Cookie gesetzt wird**. Der reine Cookie-/Banner-Check sieht diese Verstöße strukturell
nicht. Leitfall: Google Fonts extern geladen (LG München I, 3 O 17493/20, 100 €/Nutzer).

## SSOT
`backend/compliance_engine/privacy_transfer_findings.py` — Registry `TRANSFER_SERVICES`
(google_fonts, google_recaptcha, google_maps, youtube_embed, adobe/typekit). Funktion
`detect_transfers(html=…, request_urls=…)` matcht Regex gegen **drei Quellen** und liefert
pro Dienst max. 1 Finding (mit `evidence`, `source`, Drittland-Details aus
`data_processing_countries`). Konforme Varianten (youtube-nocookie, self-hosted) werden
per `exclude`-Guard nie abgestraft.

## Die drei Erkennungsquellen (wichtig!)
Aufruf in `compliance_engine/checks/datenschutz_check.py::check_datenschutz_compliance`:
1. **HTML der Seite** (`str(soup)`) — direkte Embeds/Script-URLs.
2. **Verlinkte Same-Origin-CSS** (`_collect_linked_css`) — Google Fonts liegen bei
   WordPress/Avada oft als `@font-face`-URL in der Theme-CSS (`fusion-styles`), **nicht im
   HTML**. Ohne diese Quelle blieb der Google-Fonts-Verstoß komplett unentdeckt.
3. **Echte Netzwerk-Requests** aus dem Headless-Render — `browser_renderer.render_page`
   schneidet `request_urls` mit (`page.on('request')`), `smart_fetch_html` reicht sie via
   `render_meta['request_urls']` durch, `scanner.py` gibt sie an den Datenschutz-Check
   weiter (`render_request_urls`). Fängt JS-injizierte Transfers (z. B. GA via GTM).

## Warum nicht im scanner.py duplizieren
`detect_transfers` ist die **einzige** Quelle. Kein paralleler Eigen-Check im scanner —
das würde Doppel-Findings erzeugen. Erweiterungen IMMER an der Registry/den drei Quellen.

## Abgrenzung
- Reiner Cookie-Consent: `compliance_engine/checks/cookie_check.py` (TDDDG §25) — getrennt.
- Social-Media-Plugins ohne Consent: `scanner._check_social_media_plugins` (Fashion ID).
- YouTube-Embeds: über `youtube_embed` im SSOT (nicht im Social-Check, sonst Doppelung).
