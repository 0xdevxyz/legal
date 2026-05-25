---
title: Updates Index
category: index
tags: [index, updates]
---

# Compliance Updates Index

> Automatisch generiert. Zeigt alle Compliance-Updates nach Relevanz sortiert.

## High-Impact Updates

```dataview
TABLE date, relevance_score, law_areas, source_type
FROM "updates"
WHERE impact = "high"
SORT date DESC
LIMIT 20
```

## Alle Updates

```dataview
TABLE date, impact, relevance_score, law_areas
FROM "updates"
SORT date DESC
LIMIT 50
```

## Nach Rechtsgebiet

```dataview
TABLE date, title, impact
FROM "updates"
FLATTEN law_areas as area
SORT area ASC, date DESC
```
