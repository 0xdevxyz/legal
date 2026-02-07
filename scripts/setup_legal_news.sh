#!/bin/bash
# Setup Script für Legal News System
# Führe aus: bash scripts/setup_legal_news.sh

set -e

echo "=== Complyo Legal News System Setup ==="

# Prüfe ob DATABASE_URL gesetzt ist
if [ -z "$DATABASE_URL" ]; then
    echo ""
    echo "ERROR: DATABASE_URL ist nicht gesetzt!"
    echo ""
    echo "Bitte setze die Umgebungsvariable:"
    echo "  export DATABASE_URL='postgresql://user:password@host:5432/database'"
    echo ""
    exit 1
fi

echo "DATABASE_URL gefunden: ${DATABASE_URL:0:30}..."

# Prüfe Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 nicht gefunden"
    exit 1
fi
echo "Python3: $(python3 --version)"

# Installiere psycopg2 falls nicht vorhanden (für direkte DB-Verbindung)
echo ""
echo "=== Prüfe Python Dependencies ==="
pip3 install asyncpg feedparser aiohttp --quiet 2>/dev/null || true

# Führe Migration via Python aus (kein psql nötig)
echo ""
echo "=== Führe Datenbank-Migration aus ==="

python3 << 'PYTHON_SCRIPT'
import asyncio
import asyncpg
import os

async def run_migration():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL nicht gesetzt")
        return False
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Lese SQL-Datei
        script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '/opt/projects/saas-project-2/backend'
        sql_path = os.path.join(script_dir, 'migrations', 'add_legal_news_sources.sql')
        
        # Fallback Pfad
        if not os.path.exists(sql_path):
            sql_path = '/opt/projects/saas-project-2/backend/migrations/add_legal_news_sources.sql'
        
        if not os.path.exists(sql_path):
            print(f"ERROR: SQL-Datei nicht gefunden: {sql_path}")
            return False
        
        with open(sql_path, 'r') as f:
            sql = f.read()
        
        # Führe SQL aus
        await conn.execute(sql)
        
        print("Migration erfolgreich!")
        
        # Zeige Anzahl der Feed-Quellen
        count = await conn.fetchval("SELECT COUNT(*) FROM rss_feed_sources WHERE is_active = TRUE")
        print(f"Aktive RSS-Feed-Quellen: {count}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

asyncio.run(run_migration())
PYTHON_SCRIPT

echo ""
echo "=== Setup Cronjobs ==="
echo ""
echo "Füge folgende Zeilen zu deiner Crontab hinzu (crontab -e):"
echo ""
echo "# Complyo Legal News - RSS Fetch alle 4 Stunden"
echo "0 */4 * * * cd /opt/projects/saas-project-2/backend && DATABASE_URL='$DATABASE_URL' python3 cronjobs/legal_news_cronjob.py --mode all >> /var/log/complyo_legal_news.log 2>&1"
echo ""
echo "# Complyo Legal News - Täglicher Digest um 09:00"
echo "0 9 * * * cd /opt/projects/saas-project-2/backend && DATABASE_URL='$DATABASE_URL' python3 cronjobs/legal_news_cronjob.py --mode digest >> /var/log/complyo_legal_digest.log 2>&1"
echo ""
echo "=== Setup abgeschlossen ==="
