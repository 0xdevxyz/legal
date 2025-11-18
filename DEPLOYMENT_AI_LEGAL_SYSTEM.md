# 🚀 Deployment: AI Legal System auf app.complyo.tech

## Deployment-Checkliste für Production

### ✅ Pre-Deployment Checklist

- [ ] OpenRouter API-Key vorhanden
- [ ] Database-Zugriff auf Production-DB
- [ ] Backup der Production-DB erstellt
- [ ] Backend-Code auf Server
- [ ] Frontend-Code auf Server
- [ ] Environment-Variablen konfiguriert
- [ ] SSL-Zertifikate aktuell

---

## 🔧 Schritt 1: Environment-Variablen

### Backend (.env auf Production-Server)

```env
# Existing
DATABASE_URL=postgresql://user:password@localhost:5432/complyo_production
JWT_SECRET=your_production_secret
OPENROUTER_API_KEY=your_existing_key

# NEU für AI Legal System
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
AI_CLASSIFIER_MODEL=anthropic/claude-3.5-sonnet
AI_CLASSIFICATION_TEMPERATURE=0.2
AI_LEARNING_THRESHOLD=50
```

### Frontend (.env.production)

```env
NEXT_PUBLIC_API_URL=https://api.complyo.tech
```

---

## 🗄️ Schritt 2: Datenbank-Migration

### Option A: Manuell auf Production-Server

```bash
# SSH in Production-Server
ssh user@app.complyo.tech

# Navigiere zu Backend
cd /opt/projects/saas-project-2/backend

# Backup erstellen (WICHTIG!)
pg_dump -U complyo_user complyo_production > backup_before_ai_legal_$(date +%Y%m%d_%H%M%S).sql

# Migration ausführen
psql -U complyo_user -d complyo_production -f migration_ai_legal_classifier.sql

# Verify
psql -U complyo_user -d complyo_production -c "\dt ai_*"
```

### Option B: Mit Setup-Script

```bash
cd /opt/projects/saas-project-2/backend

# Environment-Variablen setzen
export DATABASE_URL='postgresql://complyo_user:password@localhost:5432/complyo_production'
export OPENROUTER_API_KEY='sk-or-v1-YOUR_KEY'

# Setup ausführen
python setup_ai_legal_system.py
```

**Expected Output:**
```
✅ Datenbank-Migration erfolgreich!
✅ 4 Beispiel-Updates erstellt
✅ AI Classifier Test erfolgreich
✅ Feedback Learning bereit
```

---

## 🔌 Schritt 3: Backend-Integration

### In `main_production.py` einfügen:

```python
# ============================================
# AI Legal System Integration
# ============================================

# Imports (am Anfang der Datei)
import os
from ai_legal_classifier import init_ai_classifier
from ai_feedback_learning import init_feedback_learning
from ai_legal_routes import router as ai_legal_router

# ... (existing code)

# Initialisierung (nach FastAPI-App-Erstellung)
@app.on_event("startup")
async def startup_event():
    # Existing startup code...
    
    # NEU: AI Legal System
    try:
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            global ai_classifier
            ai_classifier = init_ai_classifier(openrouter_key)
            logger.info("✅ AI Legal Classifier initialized")
            
            global feedback_learning
            feedback_learning = init_feedback_learning(db_service)
            logger.info("✅ Feedback Learning System initialized")
        else:
            logger.warning("⚠️ OPENROUTER_API_KEY not set - AI classification disabled")
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI Legal System: {e}")

# Router registrieren (nach anderen Routern)
app.include_router(ai_legal_router, prefix="", tags=["AI Legal"])
logger.info("✅ AI Legal Routes registered")

# ... (rest of the code)
```

### Backend neu starten:

```bash
# Systemd Service
sudo systemctl restart complyo-backend

# Oder Docker
docker-compose restart backend

# Oder PM2
pm2 restart complyo-backend

# Logs prüfen
tail -f /var/log/complyo/backend.log
# Oder
pm2 logs complyo-backend
```

**Expected in Logs:**
```
✅ AI Legal Classifier initialized
✅ Feedback Learning System initialized
✅ AI Legal Routes registered
INFO:     Application startup complete.
```

---

## 🎨 Schritt 4: Frontend-Deployment

### Build & Deploy

```bash
cd /opt/projects/saas-project-2/dashboard-react

# Install dependencies (falls neu)
npm install

# Build für Production
npm run build

# Wenn mit PM2
pm2 restart complyo-dashboard

# Wenn mit Docker
docker-compose restart dashboard

# Wenn mit Nginx (Static)
sudo cp -r .next/out/* /var/www/app.complyo.tech/
sudo systemctl restart nginx
```

### Nginx-Konfiguration überprüfen:

```nginx
# /etc/nginx/sites-available/complyo

# Frontend (app.complyo.tech)
server {
    listen 443 ssl http2;
    server_name app.complyo.tech;
    
    ssl_certificate /etc/letsencrypt/live/app.complyo.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.complyo.tech/privkey.pem;
    
    root /var/www/app.complyo.tech;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API Proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Backend (api.complyo.tech)
server {
    listen 443 ssl http2;
    server_name api.complyo.tech;
    
    ssl_certificate /etc/letsencrypt/live/api.complyo.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.complyo.tech/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Test Nginx Config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## 🧪 Schritt 5: Testing auf Production

### 1. API-Health-Check

```bash
# Test Backend
curl https://api.complyo.tech/health

# Test neue AI-Routes
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.complyo.tech/api/legal-ai/updates

# Expected Response:
# [{"id": 1, "title": "Cookie-Banner...", "primary_action": {...}}]
```

### 2. Frontend-Test

1. Öffne: https://app.complyo.tech
2. Login
3. Navigiere zu Dashboard
4. Scroll zu "Rechtliche Updates & News"
5. **Prüfe:** Gesetzesänderungen-Tab ist aktiv ✅
6. **Prüfe:** KI-Buttons werden angezeigt 🤖
7. **Prüfe:** Impact-Score sichtbar 📊
8. **Prüfe:** Feedback-Buttons (👍👎) funktionieren
9. **Klicke:** "Archiv anzeigen" → Modal öffnet sich

### 3. End-to-End-Test

```bash
# Test kompletter Workflow
curl -X POST https://api.complyo.tech/api/legal-ai/feedback \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": "1",
    "classification_id": 1,
    "feedback_type": "explicit_helpful",
    "user_action": "click_primary_button",
    "time_to_action": 15
  }'

# Expected: {"success": true, "message": "Feedback gespeichert"}
```

---

## 📊 Schritt 6: Monitoring Setup

### Application-Monitoring

```bash
# Backend Logs
tail -f /var/log/complyo/backend.log | grep "legal-ai"

# Erwartete Log-Einträge:
# ✅ KI-klassifizierte Updates geladen: 6
# ✅ Feedback recorded: explicit_helpful for update 1
# 📊 API Usage: 2500 tokens, ~$0.0075
```

### Database-Monitoring

```sql
-- Performance Check
SELECT * FROM v_classification_performance
ORDER BY classified_at DESC
LIMIT 10;

-- Learning Insights
SELECT * FROM v_learning_insights
WHERE total_classifications >= 5;

-- Feedback Stats
SELECT 
    feedback_type,
    COUNT(*) as count,
    AVG(time_to_action) as avg_time
FROM ai_classification_feedback
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY feedback_type;
```

### Alert Setup (Optional)

```bash
# Cronjob für Monitoring
crontab -e

# Täglich um 9:00 Uhr: Check AI Classification Performance
0 9 * * * /opt/projects/saas-project-2/backend/check_ai_performance.sh

# Wöchentlich Montag 8:00: Learning Report
0 8 * * 1 /opt/projects/saas-project-2/backend/weekly_learning_report.sh
```

---

## 🔄 Schritt 7: Background Worker (Optional)

Für automatische Klassifizierung neuer Updates:

### Option A: Cronjob

```bash
crontab -e

# Täglich um 6:00 Uhr: Auto-Klassifizierung
0 6 * * * cd /opt/projects/saas-project-2/backend && python -c "import asyncio; from ai_legal_routes import classify_pending_updates; asyncio.run(classify_pending_updates())"
```

### Option B: Systemd Timer

```ini
# /etc/systemd/system/complyo-ai-classify.service
[Unit]
Description=Complyo AI Legal Classification
After=network.target

[Service]
Type=oneshot
User=www-data
WorkingDirectory=/opt/projects/saas-project-2/backend
Environment="DATABASE_URL=postgresql://..."
Environment="OPENROUTER_API_KEY=sk-or-..."
ExecStart=/usr/bin/python3 classify_pending_updates.py

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/complyo-ai-classify.timer
[Unit]
Description=Run AI Classification Daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable complyo-ai-classify.timer
sudo systemctl start complyo-ai-classify.timer
```

---

## 🔒 Schritt 8: Security-Check

### 1. API-Key Security

```bash
# Prüfe dass API-Key nicht exposed ist
grep -r "sk-or-" /opt/projects/saas-project-2/dashboard-react/src/
# Expected: Keine Treffer!

# Prüfe Environment
echo $OPENROUTER_API_KEY
# Sollte auf Production-Server gesetzt sein
```

### 2. CORS-Einstellungen

In `main_production.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.complyo.tech",
        "https://complyo.tech",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Rate-Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Auf Feedback-Route
@router.post("/feedback")
@limiter.limit("50/minute")
async def submit_feedback(...):
    ...
```

---

## 📈 Schritt 9: Post-Deployment Verification

### Checkliste nach 24h:

```bash
# 1. Prüfe Klassifizierungen
psql -U complyo_user -d complyo_production -c "
SELECT COUNT(*) as total,
       COUNT(*) FILTER (WHERE auto_classified = true) as classified
FROM legal_updates 
WHERE created_at >= NOW() - INTERVAL '24 hours';
"

# 2. Prüfe Feedback
psql -U complyo_user -d complyo_production -c "
SELECT feedback_type, COUNT(*)
FROM ai_classification_feedback
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY feedback_type;
"

# 3. Prüfe API-Errors
grep -i "error" /var/log/complyo/backend.log | grep "legal-ai" | tail -20

# 4. Prüfe Performance
curl -w "@curl-format.txt" -o /dev/null -s \
  -H "Authorization: Bearer TOKEN" \
  https://api.complyo.tech/api/legal-ai/updates
```

---

## 🐛 Troubleshooting

### Problem: "OPENROUTER_API_KEY not set"

**Lösung:**
```bash
# Check Environment
echo $OPENROUTER_API_KEY

# Set in .env
nano /opt/projects/saas-project-2/backend/.env
# Add: OPENROUTER_API_KEY=sk-or-v1-...

# Restart
sudo systemctl restart complyo-backend
```

### Problem: Migration-Fehler

**Lösung:**
```bash
# Rollback
psql -U complyo_user -d complyo_production < backup_before_ai_legal_*.sql

# Re-try Migration
psql -U complyo_user -d complyo_production -f migration_ai_legal_classifier.sql
```

### Problem: Frontend zeigt keine KI-Buttons

**Lösung:**
```bash
# 1. Check API-Response
curl -H "Authorization: Bearer TOKEN" \
  https://api.complyo.tech/api/legal-ai/updates | jq

# 2. Check Browser Console
# Öffne DevTools → Console → Suche nach Errors

# 3. Clear Cache & Rebuild
cd /opt/projects/saas-project-2/dashboard-react
rm -rf .next
npm run build
pm2 restart complyo-dashboard
```

### Problem: Langsame Performance

**Lösung:**
```sql
-- Erstelle fehlende Indexes
CREATE INDEX IF NOT EXISTS idx_legal_updates_published_at 
ON legal_updates(published_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_classifications_update 
ON ai_classifications(update_id);

-- Vacuum & Analyze
VACUUM ANALYZE legal_updates;
VACUUM ANALYZE ai_classifications;
```

---

## 📊 Monitoring Dashboard (Optional)

### Grafana-Dashboard erstellen:

```sql
-- Prometheus Metrics (wenn vorhanden)
-- Oder einfaches SQL-Dashboard:

-- KPI: Klassifizierungen pro Tag
SELECT 
    DATE(classified_at) as date,
    COUNT(*) as total,
    AVG(impact_score) as avg_impact,
    COUNT(*) FILTER (WHERE action_required = true) as action_required
FROM ai_classifications
WHERE classified_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(classified_at)
ORDER BY date DESC;

-- KPI: Feedback-Rate
SELECT 
    COUNT(DISTINCT update_id) as total_updates,
    COUNT(DISTINCT f.update_id) as updates_with_feedback,
    (COUNT(DISTINCT f.update_id)::float / NULLIF(COUNT(DISTINCT update_id), 0) * 100) as feedback_rate
FROM ai_classifications c
LEFT JOIN ai_classification_feedback f ON c.id = f.classification_id
WHERE c.classified_at >= NOW() - INTERVAL '30 days';

-- KPI: Learning Performance
SELECT * FROM v_classification_performance
WHERE total_feedback >= 5
ORDER BY performance_score DESC
LIMIT 10;
```

---

## 🎯 Success Metrics

Nach erfolgreicher Deployment sollten Sie sehen:

✅ **Backend:**
- AI Legal Routes: `/api/legal-ai/*` erreichbar
- Klassifizierungen: Neue Updates werden automatisch klassifiziert
- Feedback: User-Feedback wird gespeichert
- Learning: System lernt aus Feedback

✅ **Frontend:**
- Gesetzesänderungen-Tab ist per Default aktiv
- KI-Buttons werden angezeigt
- Impact-Score sichtbar
- Feedback-Buttons funktionieren
- Archiv öffnet sich

✅ **Database:**
- 5 neue Tabellen vorhanden
- Migrationen erfolgreich
- Indexes erstellt
- Views funktionieren

✅ **Monitoring:**
- Logs zeigen erfolgreiche Klassifizierungen
- Keine Errors in Logs
- Performance ist gut (<200ms)
- Feedback wird getrackt

---

## 📞 Support

Bei Problemen:
- 📖 Vollständige Doku: `AI_LEGAL_SYSTEM_DOCUMENTATION.md`
- 🔧 Setup-Script: `backend/setup_ai_legal_system.py`
- 📧 Email: support@complyo.tech

---

## ✅ Deployment-Checkliste (Final)

- [ ] ✅ Backup erstellt
- [ ] ✅ Migration ausgeführt
- [ ] ✅ Backend integriert & neu gestartet
- [ ] ✅ Frontend deployed & neu gestartet
- [ ] ✅ API-Tests erfolgreich
- [ ] ✅ Frontend-Tests erfolgreich
- [ ] ✅ Monitoring aktiv
- [ ] ✅ Logs prüfen (keine Errors)
- [ ] ✅ 24h-Check geplant

---

**Deployment auf app.complyo.tech ist READY! 🚀**

*Viel Erfolg mit Ihrem KI-gestützten Compliance GOAT! 🐐⚖️*

