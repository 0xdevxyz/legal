# 📦 Complyo Postgres Backup System

Automatisches Backup-System für Complyo Postgres mit iDrive e2 (S3-kompatibel)

## 🚀 Features

- ✅ **Automatische tägliche Backups** via Cron
- ☁️ **Cloud-Backup** zu iDrive e2 (S3-kompatibel)
- 💾 **Lokale Backups** als Fallback
- 🔄 **Einfache Wiederherstellung** mit interaktivem Script
- 🧹 **Automatische Bereinigung** alter Backups (30 Tage)
- 🔐 **Sichere Verschlüsselung** bei Übertragung
- 📧 **Benachrichtigungen** bei Erfolg/Fehler (optional)

## 📋 Voraussetzungen

1. **Docker** - Container muss laufen
2. **AWS CLI** - Für S3-Upload zu iDrive e2
3. **iDrive e2 Account** - Für Cloud-Backups

### AWS CLI Installation

```bash
# Ubuntu/Debian
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Test
aws --version
```

## ⚙️ Installation

### 1. iDrive e2 einrichten

1. Gehe zu [iDrive e2 Console](https://www.idrive.com/e2/)
2. Erstelle einen **Bucket** (z.B. `complyo-backups`)
3. Erstelle **Access Keys** (Access Key ID + Secret Key)
4. Notiere deinen **Endpoint** (z.B. `https://s6xw.la.idrivee2.com`)

### 2. Konfiguration

```bash
cd /opt/projects/saas-project-2/backup-scripts

# Kopiere Example-Config
cp .env.backup.example .env.backup

# Bearbeite mit deinen Credentials
nano .env.backup
```

**Wichtig:** Trage ein:
- `IDRIVE_E2_ENDPOINT` - Dein iDrive e2 Endpoint
- `IDRIVE_E2_ACCESS_KEY` - Access Key ID
- `IDRIVE_E2_SECRET_KEY` - Secret Access Key
- `IDRIVE_E2_BUCKET` - Bucket Name

### 3. Cron-Job einrichten

```bash
# Automatische tägliche Backups um 3:00 Uhr
./setup-cron.sh
```

## 🔧 Verwendung

### Manuelles Backup

```bash
# Einmaliges Backup
./backup-postgres.sh
```

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 COMPLYO POSTGRES BACKUP START
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2025-01-15 10:30:00] 🔍 Prüfe Dependencies...
[2025-01-15 10:30:01] 📦 Erstelle Backup...
[2025-01-15 10:30:05] ✅ Backup erstellt: complyo_db_2025-01-15_10-30-00.sql.gz (2.4M)
[2025-01-15 10:30:06] ☁️ Upload zu iDrive e2...
[2025-01-15 10:30:12] ✅ Backup hochgeladen zu iDrive e2
[2025-01-15 10:30:12] 🧹 Räume alte Backups auf...
[2025-01-15 10:30:13] ✅ Alte Backups entfernt
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BACKUP ABGESCHLOSSEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Restore (Wiederherstellung)

```bash
# Interaktives Restore-Menu
./restore-postgres.sh
```

**Optionen:**
1. **Aus lokalem Backup** - Schnellste Option
2. **Aus iDrive e2 (neuestes)** - Letztes Cloud-Backup
3. **Aus iDrive e2 (spezifisch)** - Bestimmtes Datum wählen

**⚠️ Wichtig:** Vor jedem Restore wird automatisch ein Sicherungs-Backup der aktuellen DB erstellt!

### Backups anzeigen

```bash
# Liste alle verfügbaren Backups
./restore-postgres.sh
# -> Wähle Option 4 (Abbrechen) zum nur Anzeigen
```

## 📁 Backup-Struktur

```
/opt/backups/complyo/
├── complyo_db_2025-01-15_03-00-00.sql.gz  # Täglich 3:00 Uhr
├── complyo_db_2025-01-14_03-00-00.sql.gz
└── pre_restore_20250115_103000.sql.gz     # Vor Restore

iDrive e2: s3://complyo-backups/
└── postgres/
    ├── complyo_db_2025-01-15_03-00-00.sql.gz
    └── complyo_db_2025-01-14_03-00-00.sql.gz
```

## 🔍 Monitoring

### Logs prüfen

```bash
# Backup-Logs (bei Cron)
tail -f /var/log/complyo-backup.log

# Oder im Script-Verzeichnis
tail -f ./backup.log
```

### Status prüfen

```bash
# Letztes Backup
ls -lh /opt/backups/complyo/ | tail -1

# iDrive e2 Backups
aws s3 ls s3://complyo-backups/postgres/ \
  --endpoint-url https://your-endpoint.idrivee2.com \
  --region us-east-1
```

### Cron-Jobs anzeigen

```bash
crontab -l | grep complyo
```

## 🚨 Notfall-Wiederherstellung

### Szenario 1: Versehentlich gelöschte Daten

```bash
cd /opt/projects/saas-project-2/backup-scripts
./restore-postgres.sh

# Wähle: 2 (Neuestes iDrive e2 Backup)
# Bestätige mit: yes
```

### Szenario 2: Kompletter Datenbank-Verlust

```bash
# 1. Postgres Container neu starten
docker restart complyo-postgres

# 2. Warte 10 Sekunden
sleep 10

# 3. Restore durchführen
cd /opt/projects/saas-project-2/backup-scripts
./restore-postgres.sh
```

### Szenario 3: Server komplett neu aufsetzen

```bash
# 1. Docker Compose hochfahren
cd /opt/projects/saas-project-2
docker-compose up -d postgres

# 2. Backup von iDrive e2 holen
cd backup-scripts
./restore-postgres.sh
# Wähle Option 2 oder 3
```

## ⚙️ Erweiterte Konfiguration

### Backup-Zeiten ändern

```bash
# Cron-Job bearbeiten
crontab -e

# Beispiele:
# Täglich 3:00:   0 3 * * *
# Täglich 2:00:   0 2 * * *
# Alle 6h:        0 */6 * * *
# Alle 12h:       0 */12 * * *
```

### Retention ändern

In `backup-postgres.sh`:
```bash
# Ändere Zeile:
RETENTION_DAYS=30  # Auf gewünschte Anzahl Tage
```

### Webhook-Benachrichtigungen

In `backup-postgres.sh` Funktion `send_notification()`:
```bash
send_notification() {
    local status=$1
    local message=$2
    
    # Füge hier deinen Webhook ein:
    curl -X POST "https://your-webhook.com/notify" \
      -H "Content-Type: application/json" \
      -d "{\"status\":\"$status\",\"message\":\"$message\"}"
}
```

## 🛡️ Sicherheit

- ✅ Credentials in `.env.backup` (nicht in Git)
- ✅ Verschlüsselte Übertragung (HTTPS/TLS)
- ✅ Komprimierte Backups (gzip)
- ✅ Automatische Bereinigung alter Backups
- ✅ Pre-Restore Sicherungs-Backups

**Wichtig:** `.env.backup` NIEMALS ins Git committen!

## 📊 Backup-Größen

Typische Backup-Größen (komprimiert):
- **Klein** (~1-5 MB): Neue Instanz, wenige Scans
- **Mittel** (~5-20 MB): ~100 Scans, mehrere Websites
- **Groß** (~20-100 MB): ~1000+ Scans, viele Websites

## 🔧 Troubleshooting

### Problem: "AWS CLI nicht installiert"

```bash
# AWS CLI installieren
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Problem: "403 Forbidden" bei S3 Upload

- ✅ Prüfe Access Keys in `.env.backup`
- ✅ Prüfe Bucket-Name
- ✅ Prüfe Endpoint URL
- ✅ Prüfe Bucket-Permissions in iDrive e2 Console

### Problem: "Container nicht gefunden"

```bash
# Prüfe Container
docker ps | grep postgres

# Falls nicht da: Starte ihn
docker-compose up -d postgres
```

### Problem: Backup schlägt fehl

```bash
# Prüfe Logs
docker logs complyo-postgres

# Teste manuell
docker exec complyo-postgres pg_dump -U complyo_user -d complyo_db > test.sql
```

## 📚 Weitere Ressourcen

- [iDrive e2 Dokumentation](https://www.idrive.com/e2/documentation)
- [AWS CLI S3 Commands](https://docs.aws.amazon.com/cli/latest/reference/s3/)
- [PostgreSQL pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html)

## 📝 Best Practices

1. ✅ **Teste Restore regelmäßig** (z.B. monatlich)
2. ✅ **Überwache Backup-Logs** (Cron-Mails oder Log-Files)
3. ✅ **Prüfe Backup-Größen** (sollten nicht plötzlich 0 sein)
4. ✅ **Behalte lokale + Cloud-Backups** (Redundanz)
5. ✅ **Dokumentiere Änderungen** an Backup-Skripten

## 🆘 Support

Bei Problemen:
1. Prüfe Logs: `tail -f /var/log/complyo-backup.log`
2. Teste manuell: `./backup-postgres.sh`
3. Prüfe Container: `docker ps`
4. Prüfe Credentials: `cat .env.backup`

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2025-01-18

