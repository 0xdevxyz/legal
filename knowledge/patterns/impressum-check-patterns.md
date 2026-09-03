---
affected_checks:
- impressum_check
category: pattern
date: '2026-08-12'
embedding_hash: ''
impact: high
last_embedded: ''
law_areas:
- TMG
- UWG
obsidian_links:
- '[[TMG]]'
- '[[UWG]]'
relevance_score: 0.9
source_type: internal
source_url: ''
status: active
tags:
- pattern
- TMG
- UWG
title: 'Muster: Impressum Fehler'
---

# Muster: Impressum Fehler

Typische Fehler bei der Impressumspflicht nach § 5 TMG

## Muster 1: Nur Kontaktformular ohne E-Mail

**Häufigkeit:** sehr häufig

**Rechtsgrundlage:** § 5 Abs. 1 Nr. 2 TMG – E-Mail-Adresse Pflicht

### Fehlerhafte Implementierung

```html
<!-- Impressum -->
Kontaktformular: <a href='/kontakt'>Kontakt</a>
```

### Korrekte Implementierung

```html
<!-- Impressum -->
E-Mail: <a href='mailto:info@beispiel.de'>info@beispiel.de</a>
```

## Muster 2: Impressum nur 3+ Klicks erreichbar

**Häufigkeit:** mittel

**Rechtsgrundlage:** § 5 TMG – muss leicht erkennbar und unmittelbar erreichbar sein

### Fehlerhafte Implementierung

```html
<!-- Impressum im verschachtelten Menü -->
Über uns > Rechtliches > Impressum
```

### Korrekte Implementierung

```html
<!-- Impressum direkt im Footer -->
<footer>
  <a href='/impressum'>Impressum</a>
</footer>
```

## Betroffene complyo-Checks

- [[impressum_check]]

## Verwandte Gesetze

[[TMG]] | [[UWG]]

---
*Automatisch generiert am 2026-08-12 durch complyo Pattern Extractor*
