#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⏰ COMPLYO BACKUP CRON SETUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Automatische tägliche Backups
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup-postgres.sh"
LOG_FILE="/var/log/complyo-backup.log"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏰ COMPLYO BACKUP CRON SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Prüfe ob Script existiert
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "❌ Backup-Script nicht gefunden: $BACKUP_SCRIPT"
    exit 1
fi

# Prüfe ob Script ausführbar ist
if [ ! -x "$BACKUP_SCRIPT" ]; then
    echo "⚠️ Script ist nicht ausführbar, mache es ausführbar..."
    chmod +x "$BACKUP_SCRIPT"
fi

# Erstelle Log-Datei falls nicht vorhanden
sudo touch "$LOG_FILE" 2>/dev/null || {
    LOG_FILE="${SCRIPT_DIR}/backup.log"
    echo "⚠️ Kann /var/log nicht schreiben, verwende: $LOG_FILE"
}

# Cron-Job Konfiguration
CRON_JOB="0 3 * * * ${BACKUP_SCRIPT} >> ${LOG_FILE} 2>&1"
CRON_COMMENT="# Complyo Postgres Backup - Täglich um 3:00 Uhr"

echo "📋 Cron-Job der konfiguriert wird:"
echo "$CRON_COMMENT"
echo "$CRON_JOB"
echo ""

# Prüfe ob Cron-Job bereits existiert
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo "⚠️ Cron-Job existiert bereits!"
    echo ""
    echo "Aktuelle Cron-Jobs:"
    crontab -l | grep -A 1 "Complyo"
    echo ""
    read -p "Überschreiben? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "❌ Abgebrochen"
        exit 0
    fi
    
    # Entferne alten Job
    (crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT") | crontab -
    echo "🗑️ Alter Cron-Job entfernt"
fi

# Füge neuen Cron-Job hinzu
(crontab -l 2>/dev/null; echo "$CRON_COMMENT"; echo "$CRON_JOB") | crontab -

echo ""
echo "✅ Cron-Job erfolgreich eingerichtet!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "KONFIGURATION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏰ Zeitplan:    Täglich um 3:00 Uhr"
echo "📁 Log-Datei:   $LOG_FILE"
echo "🔧 Script:      $BACKUP_SCRIPT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "NÄCHSTE SCHRITTE:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. ✅ Konfiguriere .env.backup mit iDrive e2 Credentials"
echo "2. ✅ Teste Backup: ${BACKUP_SCRIPT}"
echo "3. ✅ Prüfe Logs: tail -f ${LOG_FILE}"
echo "4. ✅ Liste Backups: ./backup-scripts/restore-postgres.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Zeige alle Cron-Jobs
echo "Alle Cron-Jobs:"
crontab -l

exit 0

