# Legal Change Monitoring System 🔍⚖️

## Übersicht

Das **Legal Change Monitoring System** ist ein KI-gestütztes System, das automatisch Gesetzesänderungen erkennt, auf betroffene Bereiche zuordnet und automatische Compliance-Fixes generiert.

## Features

### 🤖 Automatische Erkennung
- Überwacht EU-Recht, deutsche Gesetzgebung und Gerichtsurteile
- Erkennt Änderungen in:
  - Cookie-Compliance & ePrivacy
  - DSGVO / Datenschutz
  - Impressumspflicht
  - Barrierefreiheit (BFSG, WCAG)
  - Wettbewerbsrecht
  - EU AI Act

### 📊 Impact Analysis
- Analysiert automatisch welche Kunden betroffen sind
- Bewertet Dringlichkeit und Risiken
- Schätzt Aufwand für Umsetzung

### 🔧 Automatische Fixes
- Generiert konkrete Lösungen für Gesetzesänderungen
- Unterscheidet zwischen:
  - **Automated**: Vollautomatische Anwendung
  - **Semi-Automated**: Teilautomatisch mit Bestätigung
  - **Manual**: Manuelle Anleitung mit Schritt-für-Schritt-Guide

### 🔔 Benachrichtigungen
- In-App Notifications
- Email-Benachrichtigungen
- Prioritätsbasierte Alerts

## Datenbank-Schema

### Tabellen

1. **legal_changes** - Erkannte Gesetzesänderungen
2. **legal_change_impacts** - Impact-Analysen pro Kunde
3. **compliance_fixes** - Generierte Fixes
4. **legal_monitoring_logs** - Monitoring-History
5. **legal_change_notifications** - User-Benachrichtigungen

## API Endpoints

### Gesetzesänderungen

```http
GET /api/legal-changes/changes
```
Liste alle erkannten Gesetzesänderungen

**Query Parameters:**
- `severity`: Filter nach Dringlichkeit (critical, high, medium, low)
- `area`: Filter nach Bereich (cookie_compliance, datenschutz, etc.)
- `active_only`: Nur aktive Änderungen (default: true)

**Response:**
```json
[
  {
    "id": "dsgvo-update-2025-01",
    "title": "DSGVO: Verschärfte Cookie-Banner-Pflicht",
    "description": "...",
    "affected_areas": ["cookie_compliance", "datenschutz"],
    "severity": "high",
    "effective_date": "2025-01-01T00:00:00",
    "source": "EU-Urteil C-xxx/24",
    "source_url": "https://...",
    "requirements": ["..."],
    "detected_at": "2024-11-10T12:00:00",
    "is_active": true
  }
]
```

### Impact-Analyse

```http
GET /api/legal-changes/changes/{change_id}/impact
```
Hole die Impact-Analyse für eine Gesetzesänderung

```http
POST /api/legal-changes/changes/{change_id}/analyze
```
Starte eine neue Impact-Analyse für den aktuellen User

```http
GET /api/legal-changes/my-impacts
```
Hole alle Impact-Analysen für den aktuellen User

**Query Parameters:**
- `status`: Filter nach Status (pending, in_progress, completed)
- `affected_only`: Nur betroffene Änderungen

### Compliance-Fixes

```http
GET /api/legal-changes/changes/{change_id}/fixes
```
Hole alle Fixes für eine Gesetzesänderung

```http
POST /api/legal-changes/fixes/apply
```
Wende einen Fix an

**Request Body:**
```json
{
  "fix_id": 123,
  "auto_apply": true
}
```

### Dashboard

```http
GET /api/legal-changes/dashboard/summary
```
Dashboard-Zusammenfassung

**Response:**
```json
{
  "affected_changes": 3,
  "critical_changes": 1,
  "pending_fixes": 5,
  "next_deadline": {
    "title": "DSGVO Update",
    "date": "2025-01-01T00:00:00"
  }
}
```

### Monitoring

```http
POST /api/legal-changes/monitor/run
```
Triggere manuell eine Überprüfung (Admin only)

## Integration

### Backend-Integration

Das System ist in `main_production.py` integriert:

```python
from legal_change_routes import router as legal_change_router
from legal_change_monitor import init_legal_monitor

app.include_router(legal_change_router)

# Bei Startup
openrouter_key = os.getenv("OPENROUTER_API_KEY")
init_legal_monitor(openrouter_key)
```

### Frontend-Integration

Beispiel-Widget für das Dashboard:

```typescript
import { useEffect, useState } from 'react';

interface LegalChangeSummary {
  affected_changes: number;
  critical_changes: number;
  pending_fixes: number;
  next_deadline: {
    title: string | null;
    date: string | null;
  };
}

export function LegalChangeWidget() {
  const [summary, setSummary] = useState<LegalChangeSummary | null>(null);
  
  useEffect(() => {
    fetch('/api/legal-changes/dashboard/summary', {
      credentials: 'include'
    })
    .then(res => res.json())
    .then(data => setSummary(data));
  }, []);
  
  if (!summary) return <div>Lädt...</div>;
  
  return (
    <div className="legal-change-widget">
      <h3>Gesetzesänderungen</h3>
      
      {summary.critical_changes > 0 && (
        <div className="alert alert-danger">
          <strong>{summary.critical_changes}</strong> kritische Änderungen
        </div>
      )}
      
      <div className="stats">
        <div>
          <span>{summary.affected_changes}</span>
          <label>Betroffene Änderungen</label>
        </div>
        <div>
          <span>{summary.pending_fixes}</span>
          <label>Ausstehende Fixes</label>
        </div>
      </div>
      
      {summary.next_deadline.title && (
        <div className="next-deadline">
          <strong>Nächste Deadline:</strong>
          <p>{summary.next_deadline.title}</p>
          <small>{new Date(summary.next_deadline.date).toLocaleDateString('de-DE')}</small>
        </div>
      )}
      
      <a href="/legal-changes" className="btn btn-primary">
        Alle Änderungen anzeigen
      </a>
    </div>
  );
}
```

## Automatisierung

### Cron-Job für automatisches Monitoring

Füge in `background_worker.py` hinzu:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from legal_change_monitor import legal_monitor

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=2, minute=0)  # Täglich um 2:00 Uhr
async def daily_legal_monitoring():
    """Tägliche Überprüfung auf Gesetzesänderungen"""
    if legal_monitor:
        changes = await legal_monitor.monitor_legal_changes()
        logger.info(f"📋 Daily legal monitoring: {len(changes)} changes detected")
        
        # Speichere in Datenbank
        # Sende Benachrichtigungen an betroffene User
```

## Konfiguration

### Umgebungsvariablen

```env
OPENROUTER_API_KEY=your_api_key_here
```

## Monitoring & Logs

Logs werden in `legal_monitoring_logs` gespeichert:
- Wann wurde gescannt
- Wie viele Änderungen wurden gefunden
- Ausführungszeit
- Fehler

## Beispiel-Workflow

1. **System erkennt Gesetzesänderung**
   - KI analysiert Quellen (EU-Recht, Bundestag, etc.)
   - Erkennt: "Cookie-Banner-Buttons müssen gleich prominent sein"

2. **Impact-Analyse**
   - System prüft jeden Kunden
   - Bewertet: Ist der Kunde betroffen?
   - Ergebnis: "Ja, Cookie-Banner nicht konform"

3. **Fix-Generierung**
   - KI generiert konkreten Fix
   - Typ: "semi-automated"
   - Code: Anpassung der CSS-Klassen
   - Manual Steps: "Testen Sie das Banner"

4. **Benachrichtigung**
   - User erhält In-App-Notification
   - Email mit Details
   - Priorität: "HIGH"

5. **Anwendung**
   - User klickt "Fix anwenden"
   - System passt automatisch Cookie-Banner an
   - Bestätigung erfolgt

## Sicherheit

- Alle Fixes werden vor Anwendung validiert
- Backups vor automatischen Änderungen
- Audit-Log für alle Aktionen
- Rate-Limiting für API-Calls

## Support

Bei Fragen oder Problemen:
- 📧 support@complyo.de
- 📚 Dokumentation: https://docs.complyo.de

## Roadmap

- [ ] Machine Learning für bessere Erkennung
- [ ] Multi-Language Support
- [ ] Webhook-Integration
- [ ] Slack/Teams-Notifications
- [ ] PDF-Reports für Compliance-Audits
- [ ] Automatische PR-Erstellung für GitHub

