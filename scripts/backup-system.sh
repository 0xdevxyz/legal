#!/bin/bash

# Automated Backup System for Complyo Production Database
# Includes full backups, incremental backups, and recovery procedures
# Version: 2.0
# Date: 2025-08-27

set -euo pipefail

# Configuration
BACKUP_DIR=\"/opt/backups/complyo\"
DATE_FORMAT=\"%Y%m%d_%H%M%S\"
TIMESTAMP=$(date +\"$DATE_FORMAT\")
RETENTION_DAYS=30
DB_CONTAINER=\"shared-postgres-production\"
DB_NAME=\"complyo_db\"
DB_USER=\"complyo_user\"
S3_BUCKET=\"${S3_BACKUP_BUCKET:-}\"
NOTIFY_EMAIL=\"${BACKUP_NOTIFY_EMAIL:-admin@complyo.tech}\"

# Load environment variables
if [ -f \"/opt/projects/saas-project-2/.env.production\" ]; then
    source \"/opt/projects/saas-project-2/.env.production\"
fi

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Logging
LOG_FILE=\"$BACKUP_DIR/backup.log\"
mkdir -p \"$BACKUP_DIR\"

log() {
    local message=\"[$(date +'%Y-%m-%d %H:%M:%S')] $1\"
    echo -e \"${GREEN}$message${NC}\"
    echo \"$message\" >> \"$LOG_FILE\"
}

error() {
    local message=\"[ERROR] $1\"
    echo -e \"${RED}$message${NC}\" >&2
    echo \"[$(date +'%Y-%m-%d %H:%M:%S')] $message\" >> \"$LOG_FILE\"
}

warning() {
    local message=\"[WARNING] $1\"
    echo -e \"${YELLOW}$message${NC}\"
    echo \"[$(date +'%Y-%m-%d %H:%M:%S')] $message\" >> \"$LOG_FILE\"
}

# Send notification
send_notification() {
    local subject=\"$1\"
    local body=\"$2\"
    local status=\"$3\" # success, warning, error
    
    if command -v mail >/dev/null 2>&1 && [ -n \"$NOTIFY_EMAIL\" ]; then
        echo \"$body\" | mail -s \"[Complyo Backup] $subject\" \"$NOTIFY_EMAIL\"
    fi
    
    # Log to system log
    logger -t \"complyo-backup\" \"$subject: $body\"
}

# Check if database container is running
check_database() {
    if ! docker ps | grep -q \"$DB_CONTAINER\"; then
        error \"Database container $DB_CONTAINER is not running\"
        return 1
    fi
    
    # Test database connection
    if ! docker exec \"$DB_CONTAINER\" pg_isready -U \"$DB_USER\" -d \"$DB_NAME\" >/dev/null 2>&1; then
        error \"Cannot connect to database $DB_NAME\"
        return 1
    fi
    
    return 0
}

# Create full database backup
create_full_backup() {
    log \"Starting full database backup...\"
    
    local backup_file=\"$BACKUP_DIR/complyo_full_$TIMESTAMP.sql\"
    local compressed_file=\"$backup_file.gz\"
    
    # Create database dump
    if docker exec \"$DB_CONTAINER\" pg_dump -U \"$DB_USER\" -d \"$DB_NAME\" \\n        --verbose --clean --if-exists --create --format=plain > \"$backup_file\"; then
        
        # Compress the backup
        gzip \"$backup_file\"
        
        # Verify the compressed backup
        if [ -f \"$compressed_file\" ] && [ -s \"$compressed_file\" ]; then
            local size=$(du -h \"$compressed_file\" | cut -f1)
            log \"✅ Full backup completed successfully: $compressed_file ($size)\"
            
            # Create checksum
            sha256sum \"$compressed_file\" > \"$compressed_file.sha256\"
            
            echo \"$compressed_file\"
            return 0
        else
            error \"❌ Backup file is empty or missing\"
            return 1
        fi
    else
        error \"❌ Database dump failed\"
        return 1
    fi
}

# Create incremental backup (WAL files)
create_incremental_backup() {
    log \"Starting incremental backup (WAL files)...\"
    
    local wal_backup_dir=\"$BACKUP_DIR/wal_$TIMESTAMP\"
    mkdir -p \"$wal_backup_dir\"
    
    # Archive WAL files
    if docker exec \"$DB_CONTAINER\" find /var/lib/postgresql/data/pg_wal -name \"*.ready\" -type f | \\n        docker exec -i \"$DB_CONTAINER\" xargs -I {} cp {} \"$wal_backup_dir/\" 2>/dev/null; then
        
        local count=$(find \"$wal_backup_dir\" -type f | wc -l)
        if [ \"$count\" -gt 0 ]; then
            tar -czf \"$wal_backup_dir.tar.gz\" -C \"$BACKUP_DIR\" \"wal_$TIMESTAMP\"
            rm -rf \"$wal_backup_dir\"
            log \"✅ Incremental backup completed: $count WAL files archived\"
            echo \"$wal_backup_dir.tar.gz\"
        else
            log \"ℹ️  No new WAL files to backup\"
            rm -rf \"$wal_backup_dir\"
        fi
    else
        warning \"⚠️  WAL backup failed or no files to backup\"
    fi
}

# Upload backup to S3 (if configured)
upload_to_s3() {
    local backup_file=\"$1\"
    
    if [ -z \"$S3_BUCKET\" ]; then
        log \"ℹ️  S3 backup not configured\"
        return 0
    fi
    
    if ! command -v aws >/dev/null 2>&1; then
        warning \"⚠️  AWS CLI not installed, skipping S3 upload\"
        return 0
    fi
    
    log \"Uploading backup to S3...\"
    
    local s3_path=\"s3://$S3_BUCKET/complyo-backups/$(basename \"$backup_file\")\"
    
    if aws s3 cp \"$backup_file\" \"$s3_path\" --storage-class STANDARD_IA; then
        log \"✅ Backup uploaded to S3: $s3_path\"
        
        # Upload checksum if exists
        if [ -f \"$backup_file.sha256\" ]; then
            aws s3 cp \"$backup_file.sha256\" \"$s3_path.sha256\"
        fi
        
        return 0
    else
        error \"❌ S3 upload failed\"
        return 1
    fi
}

# Clean old backups
cleanup_old_backups() {
    log \"Cleaning up backups older than $RETENTION_DAYS days...\"
    
    local deleted_count=0
    
    # Remove local backups older than retention period
    while IFS= read -r -d '' file; do
        rm \"$file\"
        ((deleted_count++))
        log \"Deleted old backup: $(basename \"$file\")\"
    done < <(find \"$BACKUP_DIR\" -name \"complyo_*.sql.gz\" -mtime +\"$RETENTION_DAYS\" -print0)
    
    # Clean up WAL backups
    while IFS= read -r -d '' file; do
        rm \"$file\"
        ((deleted_count++))
        log \"Deleted old WAL backup: $(basename \"$file\")\"
    done < <(find \"$BACKUP_DIR\" -name \"wal_*.tar.gz\" -mtime +\"$RETENTION_DAYS\" -print0)
    
    # Clean up checksums
    find \"$BACKUP_DIR\" -name \"*.sha256\" -mtime +\"$RETENTION_DAYS\" -delete
    
    if [ \"$deleted_count\" -gt 0 ]; then
        log \"✅ Cleaned up $deleted_count old backup files\"
    else
        log \"ℹ️  No old backups to clean up\"
    fi
    
    # S3 cleanup (if configured)
    if [ -n \"$S3_BUCKET\" ] && command -v aws >/dev/null 2>&1; then
        local cutoff_date=$(date -d \"-$RETENTION_DAYS days\" +%Y-%m-%d)
        aws s3 ls \"s3://$S3_BUCKET/complyo-backups/\" | \\n            awk '{print $1\" \"$2\" \"$4}' | \\n            while read -r date time file; do
                if [[ \"$date\" < \"$cutoff_date\" ]] && [[ -n \"$file\" ]]; then
                    aws s3 rm \"s3://$S3_BUCKET/complyo-backups/$file\"
                    log \"Deleted old S3 backup: $file\"
                fi
            done
    fi
}

# Verify backup integrity
verify_backup() {
    local backup_file=\"$1\"
    
    log \"Verifying backup integrity...\"
    
    # Check if file exists and is not empty
    if [ ! -f \"$backup_file\" ] || [ ! -s \"$backup_file\" ]; then
        error \"❌ Backup file is missing or empty\"
        return 1
    fi
    
    # Verify checksum if exists
    if [ -f \"$backup_file.sha256\" ]; then
        if sha256sum -c \"$backup_file.sha256\" >/dev/null 2>&1; then
            log \"✅ Checksum verification passed\"
        else
            error \"❌ Checksum verification failed\"
            return 1
        fi
    fi
    
    # Test if the backup can be read
    if zcat \"$backup_file\" | head -n 10 | grep -q \"PostgreSQL database dump\"; then
        log \"✅ Backup file format verification passed\"
        return 0
    else
        error \"❌ Backup file format verification failed\"
        return 1
    fi
}

# Restore database from backup
restore_database() {
    local backup_file=\"$1\"
    local confirm=\"${2:-}\"
    
    if [ \"$confirm\" != \"--confirm\" ]; then
        error \"Database restore requires --confirm flag\"
        error \"Usage: $0 restore <backup_file> --confirm\"
        return 1
    fi
    
    log \"⚠️  DANGER: Restoring database from backup will overwrite all current data!\"
    log \"Backup file: $backup_file\"
    
    if [ ! -f \"$backup_file\" ]; then
        error \"Backup file not found: $backup_file\"
        return 1
    fi
    
    # Verify backup before restore
    if ! verify_backup \"$backup_file\"; then
        error \"Backup verification failed, aborting restore\"
        return 1
    fi
    
    # Create a safety backup before restore
    log \"Creating safety backup before restore...\"
    local safety_backup=\"$BACKUP_DIR/safety_backup_$(date +%Y%m%d_%H%M%S).sql.gz\"
    if ! create_full_backup >/dev/null; then
        warning \"⚠️  Failed to create safety backup, continuing anyway...\"
    fi
    
    # Stop application to prevent new connections
    log \"Stopping application services...\"
    docker-compose -f \"/opt/projects/saas-project-2/docker-compose.production.yml\" \\n        stop complyo-backend-direct complyo-dashboard complyo-landing
    
    # Restore database
    log \"Restoring database from backup...\"
    if zcat \"$backup_file\" | docker exec -i \"$DB_CONTAINER\" psql -U \"$DB_USER\" -d postgres; then
        log \"✅ Database restored successfully\"
        
        # Restart application services
        log \"Restarting application services...\"
        docker-compose -f \"/opt/projects/saas-project-2/docker-compose.production.yml\" \\n            start complyo-backend-direct complyo-dashboard complyo-landing
        
        log \"🎉 Database restore completed successfully\"
        return 0
    else
        error \"❌ Database restore failed\"
        
        # Attempt to restore from safety backup
        if [ -f \"$safety_backup\" ]; then
            log \"Attempting to restore from safety backup...\"
            zcat \"$safety_backup\" | docker exec -i \"$DB_CONTAINER\" psql -U \"$DB_USER\" -d postgres
        fi
        
        return 1
    fi
}

# List available backups
list_backups() {
    log \"Available local backups:\"
    
    if [ -d \"$BACKUP_DIR\" ]; then
        find \"$BACKUP_DIR\" -name \"complyo_*.sql.gz\" -printf \"%T@ %Tc %p\n\" | \\n            sort -nr | \\n            while read -r timestamp date time file; do
                local size=$(du -h \"$file\" | cut -f1)
                echo \"  $(basename \"$file\") - $date $time ($size)\"
            done
    else
        log \"No backup directory found\"
    fi
    
    # List S3 backups if configured
    if [ -n \"$S3_BUCKET\" ] && command -v aws >/dev/null 2>&1; then
        log \"\nAvailable S3 backups:\"
        aws s3 ls \"s3://$S3_BUCKET/complyo-backups/\" --human-readable | \\n            grep \"complyo_.*\\.sql\\.gz$\" || log \"No S3 backups found\"
    fi
}

# Main backup function
run_backup() {
    local backup_type=\"${1:-full}\"
    
    log \"🚀 Starting Complyo database backup (type: $backup_type)\"
    
    if ! check_database; then
        error \"❌ Database checks failed\"
        send_notification \"Backup Failed\" \"Database connectivity check failed\" \"error\"
        return 1
    fi
    
    local backup_file=\"\"
    local success=true
    
    case \"$backup_type\" in
        \"full\")
            backup_file=$(create_full_backup) || success=false
            ;;
        \"incremental\")
            backup_file=$(create_incremental_backup) || success=false
            ;;
        *)
            error \"Unknown backup type: $backup_type\"
            return 1
            ;;
    esac
    
    if [ \"$success\" = true ] && [ -n \"$backup_file\" ]; then
        # Verify backup
        if verify_backup \"$backup_file\"; then
            # Upload to S3
            upload_to_s3 \"$backup_file\"
            
            # Cleanup old backups
            cleanup_old_backups
            
            log \"🎉 Backup completed successfully: $(basename \"$backup_file\")\"
            send_notification \"Backup Successful\" \"Backup completed: $(basename \"$backup_file\")\" \"success\"
        else
            error \"❌ Backup verification failed\"
            send_notification \"Backup Failed\" \"Backup verification failed\" \"error\"
            return 1
        fi
    else
        error \"❌ Backup creation failed\"
        send_notification \"Backup Failed\" \"Backup creation failed\" \"error\"
        return 1
    fi
}

# Show usage
show_usage() {
    echo \"Usage: $0 [command] [options]\"
    echo \"\"
    echo \"Commands:\"
    echo \"  backup [full|incremental]  - Create database backup (default: full)\"
    echo \"  restore <file> --confirm   - Restore database from backup\"
    echo \"  list                       - List available backups\"
    echo \"  verify <file>              - Verify backup integrity\"
    echo \"  cleanup                    - Clean up old backups\"
    echo \"  help                       - Show this help message\"
    echo \"\"
    echo \"Examples:\"
    echo \"  $0 backup full             # Create full backup\"
    echo \"  $0 backup incremental      # Create incremental backup\"
    echo \"  $0 restore backup.sql.gz --confirm\"
    echo \"  $0 list                    # List all backups\"
}

# Main script logic
case \"${1:-backup}\" in
    \"backup\")
        run_backup \"${2:-full}\"
        ;;
    \"restore\")
        if [ $# -lt 2 ]; then
            error \"Restore requires backup file path\"
            show_usage
            exit 1
        fi
        restore_database \"$2\" \"$3\"
        ;;
    \"list\")
        list_backups
        ;;
    \"verify\")
        if [ $# -lt 2 ]; then
            error \"Verify requires backup file path\"
            exit 1
        fi
        verify_backup \"$2\"
        ;;
    \"cleanup\")
        cleanup_old_backups
        ;;
    \"help\"|\"-h\"|\"--help\")
        show_usage
        ;;
    *)
        error \"Unknown command: $1\"
        show_usage
        exit 1
        ;;
esac