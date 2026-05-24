# Obsidian Setup – complyo Knowledge Vault

## Schritt-für-Schritt Anleitung

### 1. Obsidian installieren

Download: https://obsidian.md/download

### 2. Vault öffnen

1. Obsidian starten
2. **"Open folder as vault"** klicken
3. Ordner auswählen: `/home/clawd/saas/legal/knowledge/`
4. **"Open"** klicken

Der Vault ist sofort einsatzbereit mit allen Law-Pages, Pattern-Files und dem Index.

### 3. Dataview Plugin installieren (für dynamische Tabellen)

1. `Settings` → `Community plugins` → `Browse`
2. Suchen: **"Dataview"**
3. **Install** → **Enable**

Danach zeigen alle Index-Files (`/index/`) automatisch aktuelle Tabellen.

### 4. Graph View konfigurieren

1. Graph-View öffnen: `Ctrl+G` (Windows/Linux) oder `Cmd+G` (Mac)
2. Oben rechts: **Filter-Icon** → **Groups** aktivieren
3. Die Farben sind voreingestellt:
   - Orange: `#law-update`
   - Rot: `#court-ruling`
   - Blau: `#law`
   - Grün: `#pattern`

### 5. Empfohlene Community Plugins

| Plugin | Zweck | Priorität |
|--------|-------|-----------|
| **Dataview** | Dynamische Tabellen aus Frontmatter | Pflicht |
| **Calendar** | Kalenderansicht für Update-Dates | Empfohlen |
| **Obsidian Git** | Vault mit Git synchronisieren | Empfohlen |
| **Tag Wrangler** | Tag-Verwaltung | Optional |

### 6. Obsidian Git einrichten (automatische Synchronisierung)

```bash
# Im Vault-Ordner
cd /home/clawd/saas/legal/knowledge
git init
git remote add origin git@github.com:your-org/complyo-knowledge.git
```

Plugin-Einstellungen:
- Auto-commit: alle 10 Minuten
- Auto-pull: beim Starten

### 7. Obsidian auf weiteren Geräten einrichten

**Option A: Obsidian Sync** (kostenpflichtig, einfachste Option)

**Option B: Git + Plugin**
- Repository klonen: `git clone ... knowledge/`
- Obsidian Git Plugin installieren
- Vault auf dem Ordner öffnen

**Option C: Syncthing / Dropbox**
- Vault-Ordner in Sync-Tool einbinden
- Auf anderen Geräten Obsidian auf denselben Ordner zeigen lassen

---

## Vault-Struktur in Obsidian

```
knowledge/
├── _meta/           # Vault-Konfiguration (nicht bearbeiten)
├── index/           # Übersichtsseiten (auto-generiert)
│   ├── README.md    # Vault-Startseite
│   ├── updates-index.md
│   └── laws-index.md
├── laws/            # Stammwissen (manuell + KI-angereichert)
│   ├── DSGVO.md
│   ├── BFSG.md
│   └── ...
├── patterns/        # Gelernte Fehler-Muster
│   └── cookie-check-patterns.md
└── updates/         # Täglich neue Einträge (täglich 07:00 Uhr)
    └── 2026-05-15-*.md
```

---

## Nützliche Obsidian-Hotkeys

| Aktion | Shortcut |
|--------|---------|
| Graph-View | `Ctrl/Cmd + G` |
| Suche | `Ctrl/Cmd + F` |
| Quick-Switcher | `Ctrl/Cmd + O` |
| Neues File | `Ctrl/Cmd + N` |
| Command Palette | `Ctrl/Cmd + P` |

---

## Dataview-Beispiele für eigene Dashboards

### Alle High-Impact Updates der letzten 30 Tage
```dataview
TABLE date, law_areas, source_type
FROM "updates"
WHERE impact = "high"
AND date >= date(today) - dur(30 days)
SORT date DESC
```

### DSGVO-relevante Updates
```dataview
TABLE date, title, impact
FROM "updates"
FLATTEN law_areas as area
WHERE area = "DSGVO"
SORT date DESC
LIMIT 10
```

### Alle Muster nach Check-Name
```dataview
TABLE affected_checks, law_areas
FROM "patterns"
SORT title ASC
```

---

## Automatischer Update-Loop

Der Cronjob läuft täglich um **07:00 Uhr**:
```bash
# Manuell ausführen
cd /home/clawd/saas/legal/backend
DATABASE_URL='...' OPENAI_API_KEY='...' python3 cronjobs/knowledge_updater.py

# Logs prüfen
tail -f /var/log/complyo-knowledge-updater.log
```

Neue `.md`-Files erscheinen automatisch im Obsidian Vault (bei aktiviertem Auto-Reload oder nach Neustart).
