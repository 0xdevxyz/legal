# Legal News Rescan-Workflow + CSS-Fix
**Implementiert:** 2026-05-02

---

## Problem

Der Rescan-Workflow aus der Legal News Sektion war inkonsistent:
- Alle Action-Buttons (`scan_website`, `update_cookie_banner`, etc.) navigierten via `window.location.href` weg — Page-Reload, kein automatischer Scan
- `DomainHeroSection` las nur URL-Parameter aus und zeigte eine Info-Box, startete aber **keinen Scan**
- CSS: Tab-Buttons nutzten `hover:glass-strong` (keine Hover-Utility), Banner hatte kein Design-System-konformes Styling

---

## Lösung: Hybrid Store-basierter Trigger

### Datenfluss (nach Fix)

```
LegalNews.tsx (Action-Button)
  └─ setPendingRescanContext({ legal_update_id, focus_category, ... })
       └─ useDashboardStore.pendingRescanContext
            └─ DomainHeroSection.tsx (useEffect Listener)
                 ├─ zeigt Info-Banner (glass-card, animate-fade-in)
                 └─ handleAnalyze(currentWebsite.url, legal_update_id)
                      └─ analyzeWebsite(url, legalUpdateId) [api.ts]
                           └─ POST /api/analyze { url, legal_update_id }
                                └─ public_routes.py
                                     ├─ force_refresh Legal Update Cache
                                     └─ INSERT scan_history ... legal_update_id
```

---

## Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `dashboard-react/src/stores/dashboard.ts` | `RescanContext` Interface + `pendingRescanContext` State + `setPendingRescanContext` Action |
| `dashboard-react/src/components/dashboard/LegalNews.tsx` | CSS Tab-Fix; `triggerRescan()` Helper; alle `window.location.href`-Redirects durch `setPendingRescanContext()` ersetzt; `handleStartScan(update?)` mit Store-Trigger |
| `dashboard-react/src/components/dashboard/DomainHeroSection.tsx` | `X`-Icon Import; Store-Destrukturierung erweitert; URL-Parameter-`useEffect` durch Store-Listener ersetzt; `handleAnalyze(forceUrl?, legalUpdateId?)` Signatur; Banner-CSS auf `glass-card + animate-fade-in` |
| `dashboard-react/src/lib/api.ts` | `analyzeWebsite(url, legalUpdateId?)` Signatur; `legal_update_id` im Payload |
| `backend/public_routes.py` | `AnalyzeRequest.legal_update_id: Optional[int]`; force-refresh bei Legal-Update-Scans; `scan_history` INSERT um `legal_update_id`-Spalte erweitert |
| `backend/migrations/add_legal_update_id_to_scan_history.sql` | Neue Spalte + Index in `scan_history` |

---

## CSS-Fixes

### Tab-Buttons (LegalNews.tsx)
- **Vorher:** `hover:glass-strong` (nicht funktionsfähig als Hover-Utility)
- **Nachher:** `bg-zinc-900/50 border border-zinc-800/50 hover:bg-zinc-800/60 hover:text-white hover:border-zinc-700/60`

### Info-Banner (DomainHeroSection.tsx)
- **Vorher:** `bg-sky-500/10 border border-sky-500/30 rounded-xl` + `×`-Text-Button
- **Nachher:** `glass-card border border-sky-500/30 rounded-2xl animate-fade-in` + Zap-Icon + `<X>`-Icon-Button

---

## DB-Migration ausführen

```bash
psql $DATABASE_URL -f backend/migrations/add_legal_update_id_to_scan_history.sql
```

---

## Testing

1. Dashboard öffnen → Legal News Sektion → Tab "Gesetzesänderungen"
2. Auf einen Update-Button klicken (z.B. "Jetzt scannen")
3. Erwartetes Verhalten:
   - **Kein Page-Reload**
   - Info-Banner erscheint im Hero-Bereich mit `glass-card`-Styling und Zap-Icon
   - Scan startet sofort (falls Website verknüpft)
   - In der DB: `scan_history.legal_update_id` enthält die Update-ID

---

## Rollback

Falls Probleme auftreten:
- Frontend: `git revert` der Änderungen in `LegalNews.tsx`, `DomainHeroSection.tsx`, `dashboard.ts`, `api.ts`
- Backend: `AnalyzeRequest.legal_update_id` entfernen (optional, backward-kompatibel da `Optional`)
- DB: Spalte bleibt — `legal_update_id IS NOT NULL` ist nie required, kein Breaking Change
