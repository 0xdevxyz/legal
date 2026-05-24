# 📜 Legal Update Integration - Dokumentation

## Übersicht

Die **Legal Update Integration** bindet aktuelle Gesetzesänderungen automatisch in das Compliance-Scanning und die Fix-Engine ein.

---

## 🎯 Funktionsweise

### 1. **Automatische Update-Erfassung**

Gesetzesänderungen werden über drei Kanäle erfasst:

```
eRecht24 Webhooks  →  legal_updates Tabelle
        ↓
RSS-Feeds         →  legal_news Tabelle
        ↓
AI Monitoring     →  Automatische Kategorisierung
```

### 2. **Scanner-Integration**

```python
# Beim Website-Scan:
1. Normale Compliance-Checks laufen
2. Legal Updates werden aus DB geladen
3. Scan-Ergebnisse werden angepasst:
   - Severity wird erhöht bei kritischen Updates
   - Risk-Euro steigt um 50% bei betroffenen Issues
   - Relevante Updates werden Issues zugeordnet
4. User sieht angepasste Ergebnisse mit Hinweis
```

**Beispiel:**

```json
{
  "issue": {
    "category": "cookies",
    "severity": "critical",  // ← erhöht von "warning"
    "risk_euro": 6000,       // ← erhöht von 4000
    "legal_update_affected": true,
    "relevant_updates": [
      {
        "id": 2,
        "title": "BGH-Urteil: Cookie-Banner ohne Vorauswahl zwingend",
        "url": "https://..."
      }
    ],
    "risk_increase_reason": "Aktuelle Gesetzesänderung erhöht Abmahnrisiko"
  }
}
```

### 3. **Fix-Engine Integration**

Die Fix-Engine berücksichtigt Legal Updates bei der Priorisierung:

```python
# Prioritäts-Boost basierend auf Updates:
priority_boost = {
    "cookies": 100,        # Critical Update → +100
    "datenschutz": 50,     # High Update → +50
    "barrierefreiheit": 100  # Critical Update → +100
}

# Fixes werden in folgender Reihenfolge generiert:
1. Kategorie mit höchstem Priority-Boost
2. Critical Issues zuerst
3. Auto-fixable Issues bevorzugt
```

### 4. **User-Benachrichtigungen**

```sql
-- Bei neuem Legal Update:
1. Finde alle User mit aktiven Websites
2. Prüfe, ob letzte Scans betroffen sind
3. Erstelle Benachrichtigung:
   
INSERT INTO user_legal_notifications 
(user_id, legal_update_id, website_id, notification_type)
VALUES (..., 'rescan_required', ...)
```

---

## 🔧 Technische Details

### Kategorien-Mapping

```python
category_mapping = {
    'impressum': ['regulation_change', 'new_law'],
    'datenschutz': ['regulation_change', 'court_ruling', 'new_law', 'enforcement'],
    'cookies': ['court_ruling', 'regulation_change', 'enforcement'],
    'barrierefreiheit': ['new_law', 'regulation_change']
}
```

### Keyword-Filterung

Updates werden zusätzlich nach Keywords gefiltert:

```python
keywords = {
    'impressum': ['impressum', 'tmg', 'anbieterkennzeichnung'],
    'datenschutz': ['dsgvo', 'datenschutz', 'privacy', 'gdpr'],
    'cookies': ['cookie', 'tracking', 'consent', 'einwilligung', 'ttdsg'],
    'barrierefreiheit': ['barrierefreiheit', 'accessibility', 'wcag', 'bfsg']
}
```

### Severity-Mapping

```python
severity_impact = {
    'critical': {
        'severity_boost': 2,    # warning → critical
        'risk_multiplier': 1.5  # +50% Risk
    },
    'high': {
        'severity_boost': 1,    # info → warning
        'risk_multiplier': 1.3  # +30% Risk
    },
    'medium': {
        'severity_boost': 0,
        'risk_multiplier': 1.2  # +20% Risk
    }
}
```

---

## 📊 Beispiel-Workflow

### Szenario: BGH-Urteil zu Cookie-Bannern

```
1. eRecht24 sendet Webhook:
   {
     "event": "law.updated",
     "data": {
       "update_type": "court_ruling",
       "title": "BGH: Cookie-Banner ohne Vorauswahl zwingend",
       "severity": "critical",
       "action_required": "Prüfen Sie Ihre Website"
     }
   }

2. Backend speichert in legal_updates Tabelle

3. User startet neuen Scan:
   
   a) Scanner findet: "Cookie-Banner mit Vorauswahl"
      Original: severity="warning", risk=4000€
   
   b) Legal Update Integration:
      - Findet relevantes Update (BGH-Urteil)
      - Erhöht severity auf "critical"
      - Erhöht risk auf 6000€
      - Fügt Update-Referenz hinzu
   
   c) User sieht im Dashboard:
      ⚠️ CRITICAL: Cookie-Banner mit Vorauswahl
      💰 Risiko: 6.000€ (erhöht aufgrund BGH-Urteil)
      📜 Relevante Änderung: BGH-Urteil vom [Datum]
      🔧 [Jetzt automatisch fixen]

4. User klickt auf "Automatisch fixen":
   
   a) Fix-Engine priorisiert Cookie-Fixes (Priority +100)
   b) Generiert DSGVO-konformen Cookie-Banner
   c) Berücksichtigt BGH-Urteil im generierten Code
   d) Bietet One-Click-Deployment an
```

---

## 🔌 API-Endpunkte

### Scan mit Legal Updates

```bash
POST /api/scan
{
  "url": "https://example.com"
}

Response:
{
  "compliance_score": 65,
  "total_risk_euro": 12000,
  "legal_updates_applied": true,
  "active_legal_updates_count": 3,
  "affected_issues_count": 5,
  "risk_increase_due_to_legal_updates": 3000,
  "issues": [...]
}
```

### Legal Updates abrufen

```bash
GET /api/legal/updates?limit=10

Response:
{
  "success": true,
  "updates": [
    {
      "id": 1,
      "update_type": "court_ruling",
      "title": "BGH-Urteil...",
      "severity": "critical",
      "published_at": "2025-11-10T...",
      "effective_date": "2025-12-10T..."
    }
  ]
}
```

---

## 🧪 Testing

### Test-Webhook senden

```bash
curl -X POST http://localhost:8002/webhooks/erecht24/test
```

### Scan mit Updates testen

```bash
# 1. Legal Update erstellen
INSERT INTO legal_updates (update_type, title, description, severity, ...) 
VALUES ('court_ruling', 'Test BGH-Urteil', 'Test', 'critical', ...);

# 2. Scan durchführen
curl -X POST http://localhost:8002/api/scan -d '{"url": "https://example.com"}'

# 3. Prüfe, ob Updates angewendet wurden
# Suche nach: "legal_updates_applied": true
```

---

## 🎛️ Konfiguration

### Environment Variables

```bash
# Optional: Webhook-Secret für eRecht24
ERECHT24_WEBHOOK_SECRET=your-secret-key

# Optional: Cache-Dauer für Legal Updates (Sekunden)
LEGAL_UPDATES_CACHE_TTL=3600
```

### Feature Flags

```python
# In main_production.py
ENABLE_LEGAL_UPDATE_INTEGRATION = True  # Default: True
LEGAL_UPDATE_SEVERITY_BOOST = True      # Default: True
LEGAL_UPDATE_NOTIFICATIONS = True       # Default: True
```

---

## 📈 Monitoring

### Logs überwachen

```bash
docker logs complyo-backend | grep "Legal Update"

# Erwartete Log-Ausgaben:
✅ 6 aktive Gesetzesänderungen geladen
✅ Legal Updates auf Scan angewendet
⚖️ Legal Update Integration initialized
```

### Datenbank-Abfragen

```sql
-- Aktive Legal Updates
SELECT COUNT(*) FROM legal_updates 
WHERE published_at >= NOW() - INTERVAL '90 days';

-- Betroffene Scans
SELECT COUNT(*) FROM scan_history 
WHERE metadata->>'legal_updates_applied' = 'true';

-- User-Benachrichtigungen
SELECT COUNT(*) FROM user_legal_notifications 
WHERE is_read = FALSE;
```

---

## 🚀 Deployment

```bash
# 1. Backend neu bauen
cd /opt/projects/saas-project-2
docker-compose up -d --build backend

# 2. Logs prüfen
docker logs complyo-backend --tail=50 | grep "Legal Update"

# 3. Test-Scan durchführen
curl -X POST http://localhost:8002/api/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "https://complyo.tech"}'
```

---

## 🔮 Zukünftige Erweiterungen

1. **AI-basierte Update-Relevanz**: Machine Learning zur besseren Zuordnung von Updates zu Issues
2. **Historische Analyse**: Trend-Analysen über Gesetzesänderungen
3. **Predictive Compliance**: Vorhersage kommender Änderungen
4. **Multi-Language**: Unterstützung für internationale Gesetzesänderungen
5. **Compliance-Timeline**: Visualisierung von Gesetzesänderungen über Zeit

---

## 📞 Support

Bei Fragen zur Legal Update Integration:
- Dokumentation: `/docs/LEGAL-UPDATE-INTEGRATION.md`
- API-Docs: `https://api.complyo.tech/docs#/legal-updates`
- Logs: `docker logs complyo-backend | grep "Legal Update"`

