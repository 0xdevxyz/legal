# 🚀 Complyo V2 - Deployment-Anleitung

## Übersicht

Diese Anleitung führt Sie durch die finale Integration und Inbetriebnahme des **Complyo V2 Systems** mit:
- ✅ Enhanced AI Fix Engine
- ✅ eRecht24 Full Integration
- ✅ Widget-System (Cookie-Banner & Accessibility)
- ✅ White-Labeling
- ✅ Comprehensive Monitoring

---

## 📋 Checkliste: Was wurde bereits erledigt

### ✅ Backend (100% Fertig)
- [x] Neue Module implementiert (`ai_fix_engine/`, `erecht24_integration.py`, `widget_manager.py`)
- [x] API-Routes erstellt (`erecht24_routes_v2.py`)
- [x] Routes in `main_production.py` eingebunden (Zeile 79 & 359)
- [x] Datenbank-Migrations-SQL erstellt (`migration_erecht24_full.sql`)

### ✅ Frontend (100% Fertig)
- [x] `AIFixDisplay.tsx` erstellt (mit Syntax-Highlighting)
- [x] `ERecht24Setup.tsx` erstellt (Guided Setup Flow)
- [x] NPM-Dependencies installiert (`react-syntax-highlighter`)
- [x] Import in `ComplianceIssueCard.tsx` hinzugefügt

### ⏳ Deployment (Manuell erforderlich)
- [ ] Datenbank-Migration ausführen
- [ ] Environment Variables konfigurieren
- [ ] Widget-Dateien auf CDN deployen
- [ ] Backend neustarten
- [ ] Frontend neu bauen & deployen

---

## 🗄️ Schritt 1: Datenbank-Migration

### Option A: Über Docker (Empfohlen)

```bash
# 1. PostgreSQL-Container-Name herausfinden
docker ps | grep postgres

# 2. Migration ausführen
docker exec -i <postgres_container_name> psql -U complyo_user -d complyo_db < /opt/projects/saas-project-2/backend/migration_erecht24_full.sql

# Beispiel:
docker exec -i saas-project-2-db-1 psql -U complyo_user -d complyo_db < /opt/projects/saas-project-2/backend/migration_erecht24_full.sql
```

### Option B: Direkt auf Host-System

```bash
cd /opt/projects/saas-project-2/backend

# Mit psql
psql -U complyo_user -d complyo_db -f migration_erecht24_full.sql

# Mit docker-compose exec
docker-compose exec db psql -U complyo_user -d complyo_db -f /app/migration_erecht24_full.sql
```

### Verifizierung

```sql
-- Prüfen, ob Tabellen erstellt wurden
\dt erecht24*

-- Erwartete Tabellen:
-- erecht24_projects
-- erecht24_texts_cache
-- erecht24_sync_history
-- erecht24_webhooks
```

---

## ⚙️ Schritt 2: Environment Variables

### Datei: `/opt/projects/saas-project-2/.env` oder `docker-compose.yml`

Fügen Sie folgende Variablen hinzu oder aktualisieren Sie sie:

```env
# ============================================================================
# eRecht24 Integration (Optional - für Premium-Features)
# ============================================================================
ERECHT24_API_KEY=your_erecht24_api_key_here
ERECHT24_API_SECRET=your_erecht24_secret_here
ERECHT24_API_URL=https://api.e-recht24.de
ERECHT24_CACHE_DAYS=7

# ============================================================================
# Widget-System
# ============================================================================
COMPLYO_WIDGET_BASE_URL=https://widgets.complyo.tech
# Alternative für lokale Entwicklung:
# COMPLYO_WIDGET_BASE_URL=http://localhost:8002/widgets

# ============================================================================
# Existing (überprüfen, ob vorhanden)
# ============================================================================
OPENROUTER_API_KEY=your_openrouter_key_here
DATABASE_URL=postgresql://complyo_user:password@db:5432/complyo_db
REDIS_HOST=redis
REDIS_PORT=6379
```

### Hinweis zu eRecht24:
- **Ohne API-Key**: System nutzt AI-Fallback (funktioniert, aber weniger rechtssicher)
- **Mit API-Key**: System nutzt anwaltlich geprüfte Texte von eRecht24

---

## 📦 Schritt 3: Widget-Deployment

### Optionen:

#### Option A: Über CDN (Produktion - Empfohlen)

**1. Widget-Dateien auf S3/CloudFront/Cloudflare Pages hochladen:**

```bash
# Dateien, die deployed werden müssen:
/opt/projects/saas-project-2/backend/widgets/cookie_banner_v2.js
/opt/projects/saas-project-2/backend/widgets/accessibility_smart.js

# Ziel-URLs:
https://widgets.complyo.tech/cookie-banner-v2.0.0.min.js
https://widgets.complyo.tech/accessibility-v2.0.0.min.js
https://widgets.complyo.tech/combined-compliance-v1.0.0.min.js
```

**2. Beispiel mit AWS S3:**
```bash
# S3 Bucket erstellen
aws s3 mb s3://complyo-widgets

# Dateien hochladen
aws s3 cp backend/widgets/cookie_banner_v2.js s3://complyo-widgets/cookie-banner-v2.0.0.min.js --acl public-read
aws s3 cp backend/widgets/accessibility_smart.js s3://complyo-widgets/accessibility-v2.0.0.min.js --acl public-read

# CloudFront-Distribution erstellen (optional)
```

#### Option B: Über Backend-Server (Entwicklung/Testing)

```bash
# Widgets über FastAPI bereitstellen
# Keine Aktion erforderlich - werden automatisch unter /widgets/* bereitgestellt
# Environment Variable setzen:
COMPLYO_WIDGET_BASE_URL=http://localhost:8002/widgets
```

#### Option C: Nginx Static Files (Hybrid)

```nginx
# nginx.conf erweitern
location /widgets/ {
    alias /opt/projects/saas-project-2/backend/widgets/;
    add_header Access-Control-Allow-Origin *;
    add_header Cache-Control "public, max-age=31536000";
}
```

---

## 🔄 Schritt 4: Services Neustarten

### Docker-Compose (Standard)

```bash
cd /opt/projects/saas-project-2

# Backend & Frontend neu bauen und starten
docker-compose down
docker-compose up -d --build

# Logs überprüfen
docker-compose logs -f backend
docker-compose logs -f frontend

# Nach "Application startup complete" suchen
```

### Einzelne Services (Entwicklung)

```bash
# Backend
cd /opt/projects/saas-project-2/backend
source .venv/bin/activate
uvicorn main_production:app --reload --host 0.0.0.0 --port 8002

# Frontend
cd /opt/projects/saas-project-2/dashboard-react
npm run dev
```

---

## ✅ Schritt 5: Verifizierung

### Backend-Tests

```bash
# Health-Check (Neue V2 API)
curl http://localhost:8002/api/v2/health

# Erwartete Antwort:
# {
#   "status": "healthy",
#   "version": "2.0.0",
#   "ai_engine": "unified",
#   "erecht24": "available" | "mock"
# }

# Testen: Fix-Generierung (benötigt Auth-Token)
curl -X POST http://localhost:8002/api/v2/fixes/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "issue_id": "test-123",
    "issue_type": "legal_text",
    "context": {"domain": "example.com"}
  }'
```

### Frontend-Tests

```bash
# Dashboard öffnen
open http://localhost:3002/dashboard

# Prüfen:
# 1. Login funktioniert
# 2. Compliance-Issues werden angezeigt
# 3. "Fix generieren" öffnet AIFixDisplay-Komponente
# 4. Syntax-Highlighting wird korrekt dargestellt
```

### Datenbank-Tests

```sql
-- Prüfen, ob eRecht24-Tabellen leer sind
SELECT COUNT(*) FROM erecht24_projects;  -- Sollte 0 sein (initial)

-- Nach erstem Setup sollten Einträge existieren
SELECT * FROM erecht24_projects LIMIT 1;
```

---

## 🔧 Schritt 6: Erste Nutzung

### A) eRecht24-Setup durchführen

**Über Frontend:**
1. Navigiere zu `/setup/erecht24` (Route muss im Router hinzugefügt werden - siehe unten)
2. Folge dem Guided Setup Flow
3. Wähle: Mit/Ohne eRecht24-Account
4. Gib Firmendaten ein
5. Bestätige Setup

**Über API:**
```bash
curl -X POST http://localhost:8002/api/v2/erecht24/setup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "domain": "example.com",
    "company_info": {
      "company_name": "Meine Firma GmbH",
      "email": "info@example.com",
      "address": "Musterstraße 1",
      "postal_code": "12345",
      "city": "Berlin"
    }
  }'
```

### B) AI-Fix generieren

1. Gehe zum Dashboard
2. Wähle eine Website
3. Klicke auf Compliance-Issue
4. Klicke "Fix generieren"
5. Neue `AIFixDisplay`-Komponente zeigt den Fix an

### C) Rechtliche Texte abrufen

```bash
# Impressum
curl http://localhost:8002/api/v2/legal-texts/impressum?domain=example.com \
  -H "Authorization: Bearer YOUR_TOKEN"

# Datenschutzerklärung
curl http://localhost:8002/api/v2/legal-texts/datenschutz?domain=example.com \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔗 Schritt 7: Router-Integration (Frontend)

### Datei: `/opt/projects/saas-project-2/dashboard-react/src/App.tsx` (oder äquivalent)

**Route für ERecht24Setup hinzufügen:**

```tsx
import { ERecht24Setup } from '@/components/setup/ERecht24Setup';

// In den Routes:
<Route 
  path="/setup/erecht24" 
  element={
    <ProtectedRoute>
      <ERecht24Setup
        domain={currentWebsite?.domain || ''}
        onComplete={(data) => {
          console.log('Setup erfolgreich:', data);
          navigate('/dashboard');
        }}
        onSkip={() => {
          console.log('Setup übersprungen');
          navigate('/dashboard');
        }}
      />
    </ProtectedRoute>
  } 
/>
```

**Link im Dashboard hinzufügen:**

```tsx
// z.B. in Settings oder Dashboard-Menü
<button 
  onClick={() => navigate('/setup/erecht24')}
  className="btn btn-primary"
>
  eRecht24 einrichten
</button>
```

---

## 📊 Schritt 8: Monitoring (Optional)

### Admin-Dashboard-Zugriff aktivieren

```sql
-- User als Admin markieren
UPDATE users 
SET is_admin = true 
WHERE email = 'admin@complyo.tech';
```

### Monitoring-Endpoints testen

```bash
# Dashboard-Metriken (nur für Admins)
curl http://localhost:8002/api/v2/monitoring/dashboard \
  -H "Authorization: Bearer ADMIN_TOKEN"

# AI-Call-Statistiken
curl http://localhost:8002/api/v2/monitoring/ai-calls?days=7 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 🐛 Troubleshooting

### Problem: "Module erecht24_routes_v2 not found"

**Lösung:**
```bash
# Prüfen, ob Datei existiert
ls -la /opt/projects/saas-project-2/backend/erecht24_routes_v2.py

# Python-Path überprüfen
cd /opt/projects/saas-project-2/backend
python3 -c "import erecht24_routes_v2; print('OK')"
```

### Problem: "Table erecht24_projects does not exist"

**Lösung:**
```bash
# Migration erneut ausführen
docker exec -i <postgres_container> psql -U complyo_user -d complyo_db < backend/migration_erecht24_full.sql
```

### Problem: Frontend zeigt "Module not found: AIFixDisplay"

**Lösung:**
```bash
# Prüfen, ob Datei existiert
ls -la /opt/projects/saas-project-2/dashboard-react/src/components/ai/AIFixDisplay.tsx

# Frontend neu bauen
cd dashboard-react
npm run build
```

### Problem: Widgets laden nicht (404)

**Lösung:**
```bash
# Environment Variable überprüfen
echo $COMPLYO_WIDGET_BASE_URL

# Für lokale Tests:
export COMPLYO_WIDGET_BASE_URL=http://localhost:8002/widgets

# Nginx/CDN-Konfiguration überprüfen
```

### Problem: eRecht24 API-Fehler

**Lösung:**
```bash
# Prüfen, ob API-Key gesetzt ist
echo $ERECHT24_API_KEY

# Falls leer: System nutzt AI-Fallback (kein Problem)
# Logs überprüfen:
docker-compose logs backend | grep erecht24
```

---

## 📈 Performance-Optimierungen

### 1. Redis-Caching für AI-Responses

```python
# In unified_fix_engine.py bereits implementiert
# Stelle sicher, dass Redis läuft:
docker-compose ps | grep redis
```

### 2. PostgreSQL-Indizes

```sql
-- Bereits in migration_erecht24_full.sql enthalten
-- Prüfen:
\d erecht24_texts_cache
```

### 3. CDN für Widgets

- Nutze CloudFront (AWS) oder Cloudflare Pages
- Aktiviere Gzip-Kompression
- Setze lange Cache-Headers (1 Jahr)

---

## 🔐 Sicherheit

### 1. Environment Variables sichern

```bash
# Nie in Git committen!
echo ".env" >> .gitignore

# Für Production: Secrets-Manager nutzen
# z.B. AWS Secrets Manager, Vault, etc.
```

### 2. API-Rate-Limiting

```python
# Bereits in main_production.py implementiert via SlowAPI
# Anpassen falls nötig:
@limiter.limit("10/minute")
```

### 3. CORS-Einstellungen überprüfen

```python
# In main_production.py:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://complyo.tech", "https://dashboard.complyo.tech"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📝 Checkliste: Production-Ready

### Backend
- [x] Code implementiert
- [x] Routes eingebunden
- [ ] Datenbank-Migration ausgeführt
- [ ] Environment Variables konfiguriert
- [ ] Logs-Monitoring eingerichtet
- [ ] Backup-Strategie definiert

### Frontend
- [x] Komponenten erstellt
- [x] Dependencies installiert
- [ ] Router konfiguriert (ERecht24Setup-Route)
- [ ] Build & Deploy durchgeführt
- [ ] Error-Tracking eingerichtet (z.B. Sentry)

### Infrastructure
- [ ] Widget-CDN konfiguriert
- [ ] SSL-Zertifikate aktiv
- [ ] Firewall-Regeln geprüft
- [ ] Monitoring-Alerts eingerichtet

### Testing
- [ ] API-Endpoints getestet
- [ ] Frontend-Flow getestet
- [ ] Load-Testing durchgeführt
- [ ] Security-Audit durchgeführt

---

## 🎉 Erfolgsmeldung

Nach erfolgreicher Durchführung aller Schritte sollte Ihr System:

✅ **Backend:**
- Neue `/api/v2/*` Endpoints verfügbar
- eRecht24-Integration aktiv (oder AI-Fallback)
- Widget-Manager funktional
- Monitoring aktiv

✅ **Frontend:**
- `AIFixDisplay` zeigt Fixes schön an
- `ERecht24Setup` führt durch Einrichtung
- Code-Highlighting funktioniert
- Responsive auf allen Geräten

✅ **System:**
- Alle Compliance-Checks laufen
- AI-Fixes werden generiert
- Rechtliche Texte verfügbar
- Widgets können deployed werden

---

## 📞 Support

Bei Fragen oder Problemen:

1. **Logs prüfen:** `docker-compose logs -f`
2. **GitHub Issues:** [Repository-Link]
3. **E-Mail:** support@complyo.tech
4. **Dokumentation:** Siehe `IMPLEMENTATION_SUMMARY.md` und `FRONTEND_IMPLEMENTATION.md`

---

**Version:** 2.0.0  
**Stand:** 2025-11-12  
**Autor:** Complyo Development Team

**Viel Erfolg mit Complyo V2! 🚀**

