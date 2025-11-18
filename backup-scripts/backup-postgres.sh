#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔐 COMPLYO POSTGRES BACKUP SCRIPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Backup zu iDrive e2 (S3-kompatibel)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e  # Exit on error

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONTAINER_NAME="complyo-postgres"
DB_NAME="complyo_db"
DB_USER="complyo_user"
DB_PASSWORD="ComplYo2025SecurePass"

# iDrive e2 S3 Credentials (aus .env laden)
source /opt/projects/saas-project-2/.env.backup 2>/dev/null || {
    echo "⚠️ .env.backup nicht gefunden, verwende Umgebungsvariablen"
}

IDRIVE_ENDPOINT="${IDRIVE_E2_ENDPOINT:-https://xyz.idrivee2.com}"
IDRIVE_ACCESS_KEY="${IDRIVE_E2_ACCESS_KEY}"
IDRIVE_SECRET_KEY="${IDRIVE_E2_SECRET_KEY}"
IDRIVE_BUCKET="${IDRIVE_E2_BUCKET:-complyo-backups}"
IDRIVE_REGION="${IDRIVE_E2_REGION:-us-east-1}"

# Backup-Verzeichnis
BACKUP_DIR="/opt/backups/complyo"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="complyo_db_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Retention (wie lange Backups aufbewahren)
RETENTION_DAYS=30

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

check_dependencies() {
    log "🔍 Prüfe Dependencies..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        error_exit "Docker nicht installiert"
    fi
    
    # Container läuft?
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        error_exit "Container $CONTAINER_NAME läuft nicht"
    fi
    
    # AWS CLI für S3 (optional, wird für Upload benötigt)
    if ! command -v aws &> /dev/null; then
        log "⚠️ AWS CLI nicht installiert - Backup wird nur lokal gespeichert"
        SKIP_S3_UPLOAD=true
    fi
}

create_backup() {
    log "📦 Erstelle Backup..."
    
    # Erstelle Backup-Verzeichnis
    mkdir -p "$BACKUP_DIR"
    
    # PostgreSQL Dump
    docker exec "$CONTAINER_NAME" pg_dump \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --clean \
        --if-exists \
        --no-owner \
        --no-privileges \
        | gzip > "$BACKUP_PATH" || error_exit "Backup fehlgeschlagen"
    
    # Prüfe Backup-Größe
    BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
    log "✅ Backup erstellt: $BACKUP_FILE ($BACKUP_SIZE)"
}

upload_to_idrive() {
    if [ "$SKIP_S3_UPLOAD" = true ]; then
        log "⏭️ S3 Upload übersprungen (AWS CLI fehlt)"
        return
    fi
    
    log "☁️ Upload zu iDrive e2..."
    
    # AWS CLI konfigurieren für iDrive e2
    export AWS_ACCESS_KEY_ID="$IDRIVE_ACCESS_KEY"
    export AWS_SECRET_ACCESS_KEY="$IDRIVE_SECRET_KEY"
    export AWS_DEFAULT_REGION="$IDRIVE_REGION"
    
    # Upload mit AWS CLI (S3-kompatibel)
    aws s3 cp "$BACKUP_PATH" \
        "s3://${IDRIVE_BUCKET}/postgres/${BACKUP_FILE}" \
        --endpoint-url "$IDRIVE_ENDPOINT" \
        --region "$IDRIVE_REGION" || {
        log "⚠️ S3 Upload fehlgeschlagen - Backup bleibt lokal"
        return 1
    }
    
    log "✅ Backup hochgeladen zu iDrive e2"
}

cleanup_old_backups() {
    log "🧹 Räume alte Backups auf (älter als ${RETENTION_DAYS} Tage)..."
    
    # Lokale Backups
    find "$BACKUP_DIR" -name "complyo_db_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    
    # iDrive e2 Backups (optional)
    if [ "$SKIP_S3_UPLOAD" != true ]; then
        aws s3 ls "s3://${IDRIVE_BUCKET}/postgres/" \
            --endpoint-url "$IDRIVE_ENDPOINT" \
            --region "$IDRIVE_REGION" \
            | while read -r line; do
                createDate=$(echo "$line" | awk '{print $1" "$2}')
                createTimestamp=$(date -d "$createDate" +%s 2>/dev/null || echo 0)
                oldTimestamp=$(date -d "${RETENTION_DAYS} days ago" +%s)
                
                if [ "$createTimestamp" -lt "$oldTimestamp" ]; then
                    fileName=$(echo "$line" | awk '{print $4}')
                    aws s3 rm "s3://${IDRIVE_BUCKET}/postgres/${fileName}" \
                        --endpoint-url "$IDRIVE_ENDPOINT" \
                        --region "$IDRIVE_REGION" 2>/dev/null || true
                fi
            done
    fi
    
    log "✅ Alte Backups entfernt"
}

send_notification() {
    local status=$1
    local message=$2
    
    # Optional: Webhook oder Email-Benachrichtigung
    # curl -X POST "https://your-webhook-url" -d "{\"status\":\"$status\",\"message\":\"$message\"}"
    log "📧 Benachrichtigung: $status - $message"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "🚀 COMPLYO POSTGRES BACKUP START"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Prüfungen
check_dependencies

# Backup erstellen
create_backup

# Upload zu iDrive e2
if upload_to_idrive; then
    send_notification "SUCCESS" "Backup erfolgreich zu iDrive e2 hochgeladen"
else
    send_notification "WARNING" "Backup erstellt, aber Upload zu iDrive e2 fehlgeschlagen"
fi

# Alte Backups löschen
cleanup_old_backups

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ BACKUP ABGESCHLOSSEN"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "📁 Lokales Backup: $BACKUP_PATH"
log "☁️ Cloud Backup: s3://${IDRIVE_BUCKET}/postgres/${BACKUP_FILE}"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0

