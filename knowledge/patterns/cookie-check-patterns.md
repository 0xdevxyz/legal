---
affected_checks:
- cookie_check
category: pattern
date: '2026-08-12'
embedding_hash: ''
impact: high
last_embedded: ''
law_areas:
- TTDSG
- DSGVO
obsidian_links:
- '[[TTDSG]]'
- '[[DSGVO]]'
relevance_score: 0.9
source_type: internal
source_url: ''
status: active
tags:
- pattern
- TTDSG
- DSGVO
title: 'Muster: Cookie-Consent Fehler'
---

# Muster: Cookie-Consent Fehler

Häufige Fehler bei der Cookie-Einwilligung nach § 25 TTDSG

## Muster 1: Kein Ablehn-Button

**Häufigkeit:** sehr häufig

**Rechtsgrundlage:** § 25 TTDSG – Einwilligung muss freiwillig sein

### Fehlerhafte Implementierung

```html
<button onclick="acceptAll()">Alle akzeptieren</button>
```

### Korrekte Implementierung

```html
<button onclick="acceptAll()">Alle akzeptieren</button>
<button onclick="rejectAll()">Ablehnen</button>
```

## Muster 2: Tracking vor Einwilligung

**Häufigkeit:** häufig

**Rechtsgrundlage:** DSGVO Art. 6 + § 25 TTDSG

### Fehlerhafte Implementierung

```html
<!-- Google Analytics vor Consent-Check -->
<script async src='https://www.googletagmanager.com/gtag/js?id=GA_ID'></script>
```

### Korrekte Implementierung

```html
<!-- Erst laden wenn Consent gegeben -->
<script>
if (window.cookieConsent && window.cookieConsent.analytics) {
  // Google Analytics laden
}
</script>
```

## Muster 3: Vorausgewählte Checkboxen

**Häufigkeit:** häufig

**Rechtsgrundlage:** DSGVO Art. 7 Abs. 2 – Opt-In Pflicht

### Fehlerhafte Implementierung

```html
<input type="checkbox" name="analytics" checked> Analytics aktivieren
```

### Korrekte Implementierung

```html
<input type="checkbox" name="analytics"> Analytics aktivieren
```

## Betroffene complyo-Checks

- [[cookie_check]]

## Verwandte Gesetze

[[TTDSG]] | [[DSGVO]]

---
*Automatisch generiert am 2026-08-12 durch complyo Pattern Extractor*
