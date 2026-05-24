# Knowledge Vault Struktur

**Pfad:** `/home/clawd/saas/legal/knowledge/`
**Zweck:** Obsidian-Vault als selbstlernendes Compliance-Wissenssystem

## Ordnerstruktur

```
knowledge/
├── updates/          # Neue Rechts-Updates (täglich auto-generiert)
├── laws/             # Stammwissen je Gesetz
├── patterns/         # Gelernte Muster aus internen Scan-Ergebnissen
├── index/            # Auto-generierte Übersichts-Files mit WikiLinks
├── templates/        # .md-Vorlagen für jeden Dateityp
└── _meta/            # Vault-Konfiguration, Embeddings-Cache
```

## Dateinamen-Konventionen

| Typ | Muster | Beispiel |
|-----|--------|---------|
| Update | `YYYY-MM-DD-{slug}.md` | `2026-05-15-nis2-meldepflicht.md` |
| Law | `{GESETZ}.md` | `DSGVO.md` |
| Pattern | `{check-name}-patterns.md` | `cookie-check-patterns.md` |
| Index | `{category}-index.md` | `updates-index.md` |

## Relevanz-Schwellwert

- `relevance_score >= 0.6` → wird als `.md` gespeichert
- `relevance_score >= 0.85` → wird als `high` impact markiert → löst Rule-Review aus

## Update-Quellen

1. eulex_service → EUR-Lex SPARQL (EU-Recht)
2. erecht24_service → eRecht24 RSS
3. news_service → RSS-Feeds (BfDI, DSK, Heise, etc.)
4. Web-Scraping → datenschutz.org, it-recht-kanzlei.de

## Obsidian-Integration

Vault öffnen: `Obsidian → Open Folder as Vault → /knowledge/`
Dataview Plugin: erforderlich für dynamische Index-Tabellen
Graph-View: Knoten-Farben nach `category`, Größe nach `relevance_score`
