---
affected_checks:
- datenschutz_check
category: pattern
date: '2026-08-12'
embedding_hash: ''
impact: high
last_embedded: ''
law_areas:
- DSGVO
obsidian_links:
- '[[DSGVO]]'
relevance_score: 0.9
source_type: internal
source_url: ''
status: active
tags:
- pattern
- DSGVO
title: 'Muster: Datenschutzerklärung Fehler'
---

# Muster: Datenschutzerklärung Fehler

Typische Mängel in Datenschutzerklärungen nach DSGVO Art. 13/14

## Muster 1: Fehlende Rechtsgrundlage

**Häufigkeit:** sehr häufig

**Rechtsgrundlage:** DSGVO Art. 13 Abs. 1 lit. c – Zwecke und Rechtsgrundlage

### Fehlerhafte Implementierung

```html
Wir verarbeiten Ihre Daten für Newsletter-Zwecke.
```

### Korrekte Implementierung

```html
Wir verarbeiten Ihre Daten für Newsletter-Zwecke auf Grundlage Ihrer Einwilligung (Art. 6 Abs. 1 lit. a DSGVO). Sie können Ihre Einwilligung jederzeit widerrufen.
```

## Muster 2: Fehlende Drittland-Übermittlung

**Häufigkeit:** häufig

**Rechtsgrundlage:** DSGVO Art. 13 Abs. 1 lit. f + Art. 46

### Fehlerhafte Implementierung

```html
Wir nutzen Google Analytics zur Analyse.
```

### Korrekte Implementierung

```html
Wir nutzen Google Analytics (Google LLC, USA). Ihre Daten werden in die USA übertragen. Rechtsgrundlage: Ihre Einwilligung (Art. 6 Abs. 1 lit. a DSGVO) i.V.m. den EU-Standardvertragsklauseln.
```

## Betroffene complyo-Checks

- [[datenschutz_check]]

## Verwandte Gesetze

[[DSGVO]]

---
*Automatisch generiert am 2026-08-12 durch complyo Pattern Extractor*
