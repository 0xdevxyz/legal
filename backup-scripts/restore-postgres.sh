#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔄 COMPLYO POSTGRES RESTORE SCRIPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Wiederherstellung aus iDrive e2 oder lokalem Backup
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONTAINER_NAME="complyo-postgres"
DB_NAME="complyo_db"
DB_USER="complyo_user"
DB_PASSWORD="ComplYo2025SecurePass"

# iDrive e2 S3 Credentials
source /opt/projects/saas-project-2/.env.backup 2>/dev/null || true

IDRIVE_ENDPOINT="${IDRIVE_E2_ENDPOINT:-https://xyz.idrivee2.com}"
IDRIVE_ACCESS_KEY="${IDRIVE_E2_ACCESS_KEY}"
IDRIVE_SECRET_KEY="${IDRIVE_E2_SECRET_KEY}"
IDRIVE_BUCKET="${IDRIVE_E2_BUCKET:-complyo-backups}"
IDRIVE_REGION="${IDRIVE_E2_REGION:-us-east-1}"

BACKUP_DIR="/opt/backups/complyo"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "❌ ERROR: $1"
    exit 1
}

list_backups() {
    log "📋 Verfügbare Backups:"
    log ""
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "LOKALE BACKUPS:"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -d "$BACKUP_DIR" ]; then
        ls -lh "$BACKUP_DIR"/complyo_db_*.sql.gz 2>/dev/null | awk '{print $9, "("$5")"}' || log "Keine lokalen Backups gefunden"
    else
        log "Keine lokalen Backups gefunden"
    fi
    
    log ""
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "IDRIVE E2 BACKUPS:"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if command -v aws &> /dev/null; then
        export AWS_ACCESS_KEY_ID="$IDRIVE_ACCESS_KEY"
        export AWS_SECRET_ACCESS_KEY="$IDRIVE_SECRET_KEY"
        export AWS_DEFAULT_REGION="$IDRIVE_REGION"
        
        aws s3 ls "s3://${IDRIVE_BUCKET}/postgres/" \
            --endpoint-url "$IDRIVE_ENDPOINT" \
            --region "$IDRIVE_REGION" 2>/dev/null || log "Keine Cloud-Backups gefunden"
    else
        log "AWS CLI nicht installiert - kann Cloud-Backups nicht listen"
    fi
    
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

download_from_idrive() {
    local backup_file=$1
    
    log "☁️ Lade Backup von iDrive e2: $backup_file"
    
    export AWS_ACCESS_KEY_ID="$IDRIVE_ACCESS_KEY"
    export AWS_SECRET_ACCESS_KEY="$IDRIVE_SECRET_KEY"
    export AWS_DEFAULT_REGION="$IDRIVE_REGION"
    
    aws s3 cp "s3://${IDRIVE_BUCKET}/postgres/${backup_file}" \
        "${BACKUP_DIR}/${backup_file}" \
        --endpoint-url "$IDRIVE_ENDPOINT" \
        --region "$IDRIVE_REGION" || error_exit "Download fehlgeschlagen"
    
    log "✅ Backup heruntergeladen"
}

restore_backup() {
    local backup_file=$1
    local backup_path="${BACKUP_DIR}/${backup_file}"
    
    # Prüfe ob Datei existiert
    if [ ! -f "$backup_path" ]; then
        error_exit "Backup-Datei nicht gefunden: $backup_path"
    fi
    
    log "⚠️ WARNUNG: Diese Aktion überschreibt die aktuelle Datenbank!"
    log "📁 Restore aus: $backup_file"
    read -p "Fortfahren? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log "❌ Abgebrochen"
        exit 0
    fi
    
    log "🔄 Starte Wiederherstellung..."
    
    # Erstelle Sicherungs-Backup der aktuellen DB
    local pre_restore_backup="/opt/backups/complyo/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
    log "📦 Erstelle Sicherungs-Backup: $pre_restore_backup"
    docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$pre_restore_backup"
    
    # Restore
    log "🔄 Wiederherstellung läuft..."
    gunzip < "$backup_path" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" || {
        log "❌ Restore fehlgeschlagen!"
        log "📦 Sicherungs-Backup verfügbar: $pre_restore_backup"
        error_exit "Restore fehlgeschlagen"
    }
    
    log "✅ Datenbank erfolgreich wiederhergestellt!"
    log "📦 Sicherungs-Backup: $pre_restore_backup"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "🔄 COMPLYO POSTGRES RESTORE"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Prüfe Container
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    error_exit "Container $CONTAINER_NAME läuft nicht"
fi

# Zeige verfügbare Backups
list_backups

log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "RESTORE-OPTIONEN:"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "1. Aus lokalem Backup"
log "2. Aus iDrive e2 (neuestes)"
log "3. Aus iDrive e2 (spezifisches Datum)"
log "4. Abbrechen"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

read -p "Wähle Option (1-4): " option

case $option in
    1)
        log "Gib den Dateinamen an (z.B. complyo_db_2025-01-15_10-30-00.sql.gz):"
        read -p "Dateiname: " filename
        restore_backup "$filename"
        ;;
    2)
        if ! command -v aws &> /dev/null; then
            error_exit "AWS CLI nicht installiert"
        fi
        
        log "Suche neuestes Backup..."
        export AWS_ACCESS_KEY_ID="$IDRIVE_ACCESS_KEY"
        export AWS_SECRET_ACCESS_KEY="$IDRIVE_SECRET_KEY"
        export AWS_DEFAULT_REGION="$IDRIVE_REGION"
        
        latest=$(aws s3 ls "s3://${IDRIVE_BUCKET}/postgres/" \
            --endpoint-url "$IDRIVE_ENDPOINT" \
            --region "$IDRIVE_REGION" \
            | sort | tail -n 1 | awk '{print $4}')
        
        if [ -z "$latest" ]; then
            error_exit "Kein Backup gefunden"
        fi
        
        log "Neuestes Backup: $latest"
        download_from_idrive "$latest"
        restore_backup "$latest"
        ;;
    3)
        log "Gib den Dateinamen von iDrive e2 an:"
        read -p "Dateiname: " filename
        download_from_idrive "$filename"
        restore_backup "$filename"
        ;;
    4)
        log "❌ Abgebrochen"
        exit 0
        ;;
    *)
        error_exit "Ungültige Option"
        ;;
esac

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ RESTORE ABGESCHLOSSEN"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0

