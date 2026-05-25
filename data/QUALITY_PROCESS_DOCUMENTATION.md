# Complyo — Qualitätsprozess & Legal-Update-Pipeline
_Stand: 2026-05-02 | Task 6 — Quality Process Implementation_

---

## Übersicht: Wie wird sichergestellt, dass alles up-to-date und korrekt ist?

Das System besteht aus **5 ineinandergreifenden Schichten**:

```
Rechtsquelle → Monitor → Regelwerk-Versioning → Website-Flagging → Kunden-Benachrichtigung
KI generiert Fix → Quality Gate (3 Stufen) → validated ODER pending_review → Admin-Queue
```

---

## Schicht 1: Legal Intelligence Pipeline (Aktualität)

### Wie funktioniert es?
Ein täglicher Cronjob (`backend/cronjobs/fetch_news.py`) ruft `run_legal_intelligence_pipeline()` auf:

1. `LegalChangeMonitor.monitor_and_persist()` erkennt neue Gesetzesänderungen via KI (Claude)
2. Neue Einträge werden in `legal_updates` gespeichert (Duplikat-Check: gleicher Titel + Datum)
3. `LegalUpdateIntegration.process_new_legal_update()` läuft für jeden neuen Eintrag:
   - Betroffene Regeln in `compliance_risk_matrix` werden via Keyword-Matching identifiziert
   - `RuleVersioningService.bump_rule_version()` erhöht die Regel-Version und loggt in `rule_changelog`
   - Alle aktiven `tracked_websites` werden als `rescan_required = TRUE` markiert
   - `user_legal_notifications` Einträge werden für betroffene Kunden erstellt

### Wer prüft die erkannten Änderungen?
- **Automatisch:** Die KI (Claude 3.5 Sonnet via OpenRouter) erkennt relevante Änderungen
- **Datenquelle:** EUR-Lex, BfDI, Datenschutzkonferenz, Bundesgesetzgebung
- **Manuell:** Bei `severity=critical` oder `severity=high` geht zusätzlich eine E-Mail an den Betreiber

### Cronjob-Einrichtung
```bash
# Täglich 06:00 Uhr
0 6 * * * cd /app && python backend/cronjobs/fetch_news.py >> /var/log/complyo-legal.log 2>&1
```

---

## Schicht 2: Regelwerk-Versionierung (Nachvollziehbarkeit)

### Datenbankstruktur
```sql
-- compliance_risk_matrix (erweitert)
rule_version INTEGER    -- aktuelle Version der Regel
valid_from   DATE       -- gültig ab
valid_until  DATE       -- gültig bis (NULL = aktiv)
is_active    BOOLEAN    -- FALSE = deprecated

-- rule_changelog (neu)
rule_id                     INTEGER  -- welche Regel
rule_version                INTEGER  -- welche Version
change_type                 VARCHAR  -- 'created' | 'updated' | 'deprecated'
change_description          TEXT     -- was hat sich geändert
legal_basis_ref             VARCHAR  -- z.B. "WCAG 2.2 SC 2.4.11"
triggered_by_legal_update_id INTEGER -- welcher legal_updates-Eintrag hat dies ausgelöst
changed_at                  TIMESTAMPTZ
changed_by                  VARCHAR  -- 'system' oder Admin-ID
```

### Scan-Protokollierung
Jeder Scan speichert in `scan_history`:
- `ruleset_snapshot JSONB` — Snapshot aller aktiven Regeln zum Scan-Zeitpunkt
- `ruleset_version INTEGER` — Versionssumme der Regeln

→ So ist immer nachvollziehbar: *Welche Regel galt wann, und welcher Scan hat welches Regelwerk verwendet?*

### API: Regelwerk-Historie abfragen
```
GET /api/admin/rules/{rule_id}/history?api_key=...
→ Vollständige Versionshistorie einer Regel
```

---

## Schicht 3: Fix Quality Gate (Korrektheit der KI-Fixes)

### 3 automatische Prüfstufen
Jeder KI-generierte Fix durchläuft `FixQualityGate.run()` in `backend/ai_fix_engine/fix_quality_gate.py`:

| Stufe | Name | Prüft | Zeitlimit |
|-------|------|-------|-----------|
| 1 | Syntax & Safety | Gefährliche HTML/JS-Konstrukte, ungültige ARIA-Roles, onclick-Handler | < 200ms |
| 2 | Re-Scanner | Score vorher/nachher — Fix darf Score nicht verschlechtern | < 5s |
| 3 | Regression | Keine neuen Issues durch Fix — kein Placeholder, leere Buttons, etc. | < 10s |

### Ergebnis
- **Alle 3 grün** → `quality_gate_status = "validated"` — Fix kann automatisch deployed werden
- **Mind. 1 rot** → `quality_gate_status = "pending_review"` — Fix landet in Admin-Queue

### In DB gespeichert
`fix_application_audit`:
```sql
quality_gate_status VARCHAR  -- 'validated' | 'pending_review' | 'rejected'
quality_gate_log    JSONB    -- Detailliertes Log pro Stufe mit Fehler-Beschreibungen
reviewed_by         VARCHAR  -- Admin der freigegeben/abgelehnt hat
reviewed_at         TIMESTAMPTZ
```

---

## Schicht 4: Admin Review Queue (Human-in-the-Loop)

### Wann ist manuelle Prüfung erforderlich?
- Fix hat mindestens eine Quality Gate Stufe nicht bestanden
- Neue Legal-Updates mit `severity=critical` → optionaler manueller Review der betroffenen Regeländerungen

### Admin-Interface
Dashboard-URL: `https://app.complyo.tech/admin/fix-review`

| Aktion | Endpoint | Beschreibung |
|--------|----------|--------------|
| Queue laden | `GET /api/admin/fix-review-queue?api_key=...` | Alle pending_review Fixes |
| Detail | `GET /api/admin/fix-review-queue/{id}?api_key=...` | Fix + Quality Gate Log |
| Freigeben | `POST /api/admin/fix-review-queue/{id}/approve?api_key=...` | Status → validated |
| Ablehnen | `POST /api/admin/fix-review-queue/{id}/reject?api_key=...` | Status → rejected + Begründung |

### Authentifizierung
Alle Admin-Endpoints verwenden `?api_key=...` Query-Parameter (Wert: `ADMIN_API_KEY` Env-Variable).

---

## Schicht 5: Kunden-Benachrichtigung (Transparenz)

### Wann bekommen Kunden einen Hinweis?
Wenn `tracked_websites.rescan_required = TRUE` → automatisch nach einem neuen Legal-Update.

### Banner im Dashboard
`RescanRequiredBanner` Component (`dashboard-react/src/components/RescanRequiredBanner.tsx`):
- Zeigt Titel des auslösenden Legal-Updates
- Zeigt Datum des letzten Scans
- Button "Jetzt neu scannen"
- Per Klick auf "Schließen" wird der Banner ausgeblendet (nur lokal, DB-Flag bleibt bis zum Rescan)

### API
```
GET /api/v2/websites/{website_id}/scan-status
Authorization: Bearer <token>

Response:
{
  "rescan_required": true,
  "rescan_reason": "WCAG 2.2 Neue Anforderungen erkannt",
  "last_scan": "2026-04-15T10:30:00",
  "triggered_by": { "id": 42, "title": "WCAG 2.2 SC 2.4.11 Focus Appearance" }
}
```

### E-Mail bei hoher Severity
- `severity=critical` oder `severity=high` → zusätzlich E-Mail an Kunden
- `severity=medium/low` → nur Dashboard-Banner

---

## Betroffene Dateien (Implementiert)

| Datei | Beschreibung |
|-------|--------------|
| `backend/migrations/add_rule_versioning.sql` | DB-Schema für Versionierung |
| `backend/compliance_engine/rule_versioning_service.py` | Service für Regel-Versionen |
| `backend/compliance_engine/legal_update_integration.py` | Erweitert um `process_new_legal_update()` |
| `backend/legal_change_monitor.py` | Erweitert um `monitor_and_persist()`, `_save_change_to_db()` |
| `backend/cronjobs/fetch_news.py` | Erweitert um `run_legal_intelligence_pipeline()` |
| `backend/ai_fix_engine/fix_quality_gate.py` | 3-stufiges Quality Gate |
| `backend/ai_fix_engine/unified_fix_engine.py` | Quality Gate eingehängt nach Fix-Generierung |
| `backend/admin_routes.py` | 4 neue Endpoints für Fix Review Queue |
| `dashboard-react/src/app/admin/fix-review/page.tsx` | Admin-UI für Review Queue |
| `backend/legal_notification_service.py` | Neue Methode `notify_rescan_required()` |
| `backend/website_routes.py` | Neuer Endpoint `GET /{id}/scan-status` |
| `dashboard-react/src/components/RescanRequiredBanner.tsx` | Dashboard-Banner für Kunden |
| `backend/tests/test_legal_update_pipeline.py` | 10 Unit-Tests |

---

## Deployment-Checkliste

```bash
# 1. DB Migration ausführen
psql $DATABASE_URL -f backend/migrations/add_rule_versioning.sql

# 2. Backend neu starten (neues Quality Gate + Routes werden geladen)
docker-compose restart backend

# 3. Frontend neu bauen (Admin-Seite + Banner)
cd dashboard-react && npm run build

# 4. Cronjob einrichten (falls noch nicht vorhanden)
crontab -e
# → 0 6 * * * cd /app && python backend/cronjobs/fetch_news.py

# 5. Tests ausführen
cd backend && pytest tests/test_legal_update_pipeline.py -v
```

---

## Onboarding: Juristen / Legal-Experten

Wenn eine neue Gesetzesänderung manuell eingetragen werden soll:

1. In der DB-Tabelle `legal_updates` einen neuen Eintrag erstellen:
   ```sql
   INSERT INTO legal_updates (update_type, title, description, severity, source, published_at, effective_date)
   VALUES ('regulation_change', 'Titel der Änderung', 'Beschreibung...', 'high', 'Quelle', NOW(), '2026-07-01');
   ```
2. Die Pipeline manuell anstoßen (oder auf den nächsten täglichen Cronjob warten)
3. Im Admin-Dashboard unter `/admin/fix-review` prüfen ob neue Fixes zur Freigabe anstehen

---

## FAQ

**Q: Was passiert wenn die KI falsche Gesetzesänderungen erkennt?**
A: Sie werden in `legal_updates` gespeichert, aber bis zum nächsten manuellen Review oder Cronjob passiert nichts. Admins können falsche Einträge in der DB auf `is_active=FALSE` setzen.

**Q: Wer trägt die rechtliche Verantwortung für KI-generierte Fixes?**
A: Fixes mit `quality_gate_status=validated` können automatisch deployed werden. Fixes mit `pending_review` MÜSSEN von einem Admin (idealerweise mit rechtlichem Hintergrund) manuell freigegeben werden.

**Q: Wie oft werden Regeln aktualisiert?**
A: Täglich via Cronjob. Bei kritischen Änderungen (z.B. neue DSGVO-Urteile) kann die Pipeline auch manuell über die API getriggert werden.

**Q: Wie verhindert man, dass alle Kunden gleichzeitig benachrichtigt werden?**
A: Aktuell werden alle aktiven Websites geflaggt. In einem nächsten Schritt kann ein Batch-Processor implementiert werden, der Notifications gestaffelt versendet.
