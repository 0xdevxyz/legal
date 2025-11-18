#!/bin/bash

# ============================================
# Deployment-Script für AI Legal System
# app.complyo.tech Production Deployment
# ============================================

set -e  # Exit bei Fehler

echo "============================================"
echo "🚀 AI Legal System - Production Deployment"
echo "============================================"
echo ""

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktionen
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Pre-flight Checks
echo "1️⃣ Pre-flight Checks..."
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    log_warn "Script läuft nicht als root. Einige Befehle brauchen sudo."
fi

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    log_error "DATABASE_URL ist nicht gesetzt!"
    echo "Setze: export DATABASE_URL='postgresql://user:pass@localhost/complyo_production'"
    exit 1
fi
log_info "DATABASE_URL ist gesetzt"

# Check OPENROUTER_API_KEY
if [ -z "$OPENROUTER_API_KEY" ]; then
    log_warn "OPENROUTER_API_KEY ist nicht gesetzt!"
    echo "KI-Klassifizierung wird nicht funktionieren."
    echo "Setze: export OPENROUTER_API_KEY='sk-or-v1-...'"
    read -p "Trotzdem fortfahren? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    log_info "OPENROUTER_API_KEY ist gesetzt"
fi

# Check if in project directory
if [ ! -f "backend/migration_ai_legal_classifier.sql" ]; then
    log_error "Nicht im Project-Root-Directory!"
    echo "Navigiere zu: cd /opt/projects/saas-project-2"
    exit 1
fi
log_info "Im korrekten Directory"

echo ""

# Backup
echo "2️⃣ Database Backup..."
echo ""

BACKUP_FILE="backup_before_ai_legal_$(date +%Y%m%d_%H%M%S).sql"
BACKUP_DIR="./backups"

mkdir -p $BACKUP_DIR

if command -v pg_dump &> /dev/null; then
    log_info "Erstelle Backup: $BACKUP_DIR/$BACKUP_FILE"
    
    # Extract DB credentials from DATABASE_URL
    DB_USER=$(echo $DATABASE_URL | sed -n 's/.*\/\/\([^:]*\):.*/\1/p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    
    pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/$BACKUP_FILE
    
    if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        log_info "Backup erfolgreich erstellt!"
    else
        log_error "Backup fehlgeschlagen!"
        exit 1
    fi
else
    log_warn "pg_dump nicht gefunden - Backup übersprungen"
    read -p "Ohne Backup fortfahren? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# Database Migration
echo "3️⃣ Database Migration..."
echo ""

cd backend

if [ -f "migration_ai_legal_classifier.sql" ]; then
    log_info "Führe Migration aus..."
    
    python3 << EOF
import asyncio
import asyncpg
import os

async def run_migration():
    try:
        db_url = os.getenv('DATABASE_URL')
        conn = await asyncpg.connect(db_url)
        
        with open('migration_ai_legal_classifier.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        await conn.execute(migration_sql)
        await conn.close()
        
        print("✅ Migration erfolgreich!")
        return True
    except Exception as e:
        print(f"❌ Migration fehlgeschlagen: {e}")
        return False

success = asyncio.run(run_migration())
exit(0 if success else 1)
EOF

    if [ $? -eq 0 ]; then
        log_info "Database Migration erfolgreich!"
    else
        log_error "Database Migration fehlgeschlagen!"
        echo "Rollback mit: psql -U user -d db < $BACKUP_DIR/$BACKUP_FILE"
        exit 1
    fi
else
    log_error "migration_ai_legal_classifier.sql nicht gefunden!"
    exit 1
fi

cd ..

echo ""

# Backend Integration Check
echo "4️⃣ Backend Integration Check..."
echo ""

if grep -q "ai_legal_routes" backend/main_production.py; then
    log_info "AI Legal Routes bereits in main_production.py integriert"
else
    log_warn "AI Legal Routes NICHT in main_production.py gefunden!"
    echo ""
    echo "Bitte manuell einfügen in backend/main_production.py:"
    echo ""
    echo "from ai_legal_classifier import init_ai_classifier"
    echo "from ai_feedback_learning import init_feedback_learning"
    echo "from ai_legal_routes import router as ai_legal_router"
    echo ""
    echo "@app.on_event('startup')"
    echo "async def startup_event():"
    echo "    ai_classifier = init_ai_classifier(os.getenv('OPENROUTER_API_KEY'))"
    echo "    feedback_learning = init_feedback_learning(db_service)"
    echo ""
    echo "app.include_router(ai_legal_router)"
    echo ""
    read -p "Integration manuell durchgeführt? Fortfahren? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# Backend Restart
echo "5️⃣ Backend Restart..."
echo ""

# Check welcher Service-Manager verwendet wird
if command -v systemctl &> /dev/null && systemctl is-active --quiet complyo-backend; then
    log_info "Restart mit systemd..."
    sudo systemctl restart complyo-backend
    sleep 3
    if systemctl is-active --quiet complyo-backend; then
        log_info "Backend erfolgreich gestartet!"
    else
        log_error "Backend-Start fehlgeschlagen!"
        sudo systemctl status complyo-backend
        exit 1
    fi
    
elif command -v pm2 &> /dev/null && pm2 list | grep -q complyo-backend; then
    log_info "Restart mit PM2..."
    pm2 restart complyo-backend
    sleep 2
    log_info "Backend neu gestartet!"
    
elif command -v docker-compose &> /dev/null && [ -f "docker-compose.yml" ]; then
    log_info "Restart mit Docker Compose..."
    docker-compose restart backend
    sleep 3
    log_info "Backend Container neu gestartet!"
    
else
    log_warn "Kein Service-Manager erkannt!"
    echo "Bitte Backend manuell neu starten"
    read -p "Backend manuell neu gestartet? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# Frontend Build & Deploy
echo "6️⃣ Frontend Build & Deploy..."
echo ""

cd dashboard-react

if [ -f "package.json" ]; then
    log_info "Baue Frontend..."
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_info "Installiere Dependencies..."
        npm install
    fi
    
    # Build
    log_info "Build läuft..."
    npm run build
    
    if [ $? -eq 0 ]; then
        log_info "Frontend Build erfolgreich!"
    else
        log_error "Frontend Build fehlgeschlagen!"
        exit 1
    fi
    
    # Restart Frontend
    if command -v pm2 &> /dev/null && pm2 list | grep -q complyo-dashboard; then
        log_info "Restart Frontend mit PM2..."
        pm2 restart complyo-dashboard
        
    elif command -v systemctl &> /dev/null && systemctl is-active --quiet complyo-dashboard; then
        log_info "Restart Frontend mit systemd..."
        sudo systemctl restart complyo-dashboard
        
    elif command -v docker-compose &> /dev/null; then
        log_info "Restart Frontend mit Docker..."
        cd ..
        docker-compose restart dashboard
        cd dashboard-react
        
    else
        log_warn "Kein Service-Manager erkannt!"
        echo "Bitte Frontend manuell neu starten"
    fi
    
    log_info "Frontend deployed!"
else
    log_error "package.json nicht gefunden!"
    exit 1
fi

cd ..

echo ""

# API Health Check
echo "7️⃣ API Health Check..."
echo ""

log_info "Warte 5 Sekunden auf Backend-Start..."
sleep 5

# Check if Backend is running
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    log_info "Backend ist erreichbar!"
else
    log_warn "Backend nicht erreichbar auf localhost:8000"
fi

# Check new AI routes
if curl -s -f http://localhost:8000/api/legal-ai/stats > /dev/null 2>&1; then
    log_info "AI Legal Routes sind aktiv!"
else
    log_warn "AI Legal Routes nicht erreichbar (Auth erforderlich)"
fi

echo ""

# Verify Database Tables
echo "8️⃣ Database Verification..."
echo ""

python3 << EOF
import asyncio
import asyncpg
import os

async def verify_tables():
    try:
        db_url = os.getenv('DATABASE_URL')
        conn = await asyncpg.connect(db_url)
        
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE tablename LIKE 'ai_%'"
        )
        
        print(f"✅ Gefundene AI-Tabellen: {len(tables)}")
        for table in tables:
            print(f"   - {table['tablename']}")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Verification fehlgeschlagen: {e}")
        return False

asyncio.run(verify_tables())
EOF

echo ""

# Summary
echo "============================================"
echo "✅ Deployment erfolgreich abgeschlossen!"
echo "============================================"
echo ""
echo "📊 Nächste Schritte:"
echo ""
echo "1. Öffne: https://app.complyo.tech"
echo "2. Login mit deinem Account"
echo "3. Navigiere zu Dashboard"
echo "4. Prüfe 'Rechtliche Updates & News'"
echo "5. Verifiziere KI-Buttons und Funktionalität"
echo ""
echo "📝 Logs prüfen:"
echo "   Backend:  tail -f /var/log/complyo/backend.log"
echo "   Frontend: pm2 logs complyo-dashboard"
echo ""
echo "📖 Dokumentation:"
echo "   - DEPLOYMENT_AI_LEGAL_SYSTEM.md"
echo "   - AI_LEGAL_SYSTEM_DOCUMENTATION.md"
echo ""
echo "🐛 Bei Problemen:"
echo "   Rollback: psql -U user -d db < $BACKUP_DIR/$BACKUP_FILE"
echo ""
echo "🎉 Viel Erfolg mit dem KI-System!"
echo ""

