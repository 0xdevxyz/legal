# Bestandsaufnahme — 24 echte deutsche KMU-Websites

Gemessen 06.08.2026 · axe-core 4.11.4 (WCAG 2.1 AA + best-practice) · Startseite · complyo-Widget blockiert

Zweck: entscheiden, welche Fixes complyo als naechstes mechanisch koennen
muss. Sortiert nach Verbreitung, nicht nach WCAG-Nummer.

**289 Fundstellen sind WCAG-2.1-AA-Pflicht, 424 sind Empfehlungen.** Die Trennung ist wichtig: `region` und `heading-order` sind keine BFSG-Verstoesse.

## Was axe findet

| axe-Regel | Seiten | Anteil | Fundstellen | Schwere | Rang |
|---|---:|---:|---:|---|---|
| `region` | 20 | 83 % | 331 | moderate | Empfehlung |
| `color-contrast` | 18 | 75 % | 192 | serious | **Pflicht** |
| `link-name` | 13 | 54 % | 56 | serious | **Pflicht** |
| `heading-order` | 12 | 50 % | 42 | moderate | Empfehlung |
| `landmark-one-main` | 12 | 50 % | 12 | moderate | Empfehlung |
| `page-has-heading-one` | 8 | 33 % | 8 | moderate | Empfehlung |
| `meta-viewport` | 7 | 29 % | 7 | moderate | **Pflicht** |
| `landmark-unique` | 6 | 25 % | 10 | moderate | Empfehlung |
| `image-alt` | 4 | 17 % | 6 | critical | **Pflicht** |
| `label` | 3 | 12 % | 5 | critical | **Pflicht** |
| `landmark-complementary-is-top-level` | 3 | 12 % | 13 | moderate | Empfehlung |
| `document-title` | 2 | 8 % | 2 | serious | **Pflicht** |
| `select-name` | 2 | 8 % | 3 | critical | **Pflicht** |
| `landmark-main-is-top-level` | 2 | 8 % | 2 | moderate | Empfehlung |
| `landmark-no-duplicate-main` | 2 | 8 % | 2 | moderate | Empfehlung |
| `nested-interactive` | 2 | 8 % | 9 | serious | **Pflicht** |
| `empty-heading` | 1 | 4 % | 1 | minor | Empfehlung |
| `button-name` | 1 | 4 % | 1 | critical | **Pflicht** |
| `frame-title` | 1 | 4 % | 1 | serious | **Pflicht** |
| `landmark-no-duplicate-banner` | 1 | 4 % | 1 | moderate | Empfehlung |
| `scrollable-region-focusable` | 1 | 4 % | 1 | serious | **Pflicht** |
| `landmark-no-duplicate-contentinfo` | 1 | 4 % | 1 | moderate | Empfehlung |
| `aria-required-parent` | 1 | 4 % | 3 | critical | **Pflicht** |
| `image-redundant-alt` | 1 | 4 % | 1 | minor | Empfehlung |
| `link-in-text-block` | 1 | 4 % | 3 | serious | **Pflicht** |

## Was axe nicht findet

Diese Luecken bestehen jede axe-Pruefung und betreffen Nutzer trotzdem.
`alt=""` gilt fuer axe als bewusste Dekorativ-Markierung — WordPress
schreibt es aber an jedes Bild ohne Mediathek-Alt-Text.

| Luecke | betroffene Seiten | Anteil | Fundstellen gesamt |
|---|---:|---:|---:|
| Bilder ohne Textalternative | 20 | 83 % | 190 von 384 Bildern |
| Links ohne erkennbaren Text | 21 | 88 % | 125 |
| Links mit nichtssagendem Text | 2 | 8 % | 3 |
| kein `lang` am `<html>` | 0 | 0 % | — |
| kein `<main>`-Landmark | 18 | 75 % | — |
| kein Sprunglink | 23 | 96 % | — |
| kein Seitentitel | 2 | 8 % | — |

## Je Seite

| Seite | Pflicht-Verstoesse | Empfehlungen | stumme Bilder |
|---|---:|---:|---:|
| spedition-mahn.de | 29 | 35 | 20 |
| naturheilzentrum-freitag.de | 24 | 28 | 6 |
| zua-zwickau.de | 23 | 1 | 1 |
| container-spindler.de | 20 | 16 | 2 |
| zahnarztpraxis-mittweida.de | 20 | 51 | 0 |
| fv-wolkenburg.de | 16 | 36 | 0 |
| osteopathie-limbach.de | 16 | 20 | 14 |
| ghp-ingenieure.de | 15 | 8 | 2 |
| rhino.cafe | 15 | 40 | 52 |
| partyservice-wanka.de | 13 | 11 | 14 |
| reinhardt.coffee | 13 | 7 | 11 |
| boehme.it | 12 | 23 | 1 |
| ferienpark-waldenburg.de | 12 | 2 | 19 |
| konditorei-limbach.de | 12 | 56 | 6 |
| breathhealingart.com | 11 | 17 | 4 |
| doener-bistro-baku.de | 9 | 17 | 0 |
| lindner-maschinenbau.de | 9 | 12 | 7 |
| bauschlosserei-claus.de | 8 | 7 | 10 |
| naturheilpraxis-decker.de | 7 | 3 | 8 |
| tc-limbach.de | 3 | 2 | 8 |
| boehme-energie.com | 1 | 2 | 0 |
| cb-reisen.de | 1 | 3 | 2 |
| physiomueller.de | 0 | 21 | 2 |
| susanne-fischer.online | 0 | 6 | 1 |

## Nicht erreichbar

- https://lunismode.de — net::ERR_SSL_PROTOCOL_ERROR at https://lunismode.de/
- https://meyers.cafe — net::ERR_CERT_AUTHORITY_INVALID at https://meyers.cafe/