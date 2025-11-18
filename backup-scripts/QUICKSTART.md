# 🚀 Complyo Backup - Quick Start

## 1️⃣ Installation (5 Minuten)

```bash
cd /opt/projects/saas-project-2/backup-scripts

# 1. Konfiguration erstellen
cp .env.backup.example .env.backup

# 2. iDrive e2 Credentials eintragen
nano .env.backup
```

**Erforderliche Werte:**
- `IDRIVE_E2_ENDPOINT` → Dein Endpoint (z.B. https://s6xw.la.idrivee2.com)
- `IDRIVE_E2_ACCESS_KEY` → Access Key ID
- `IDRIVE_E2_SECRET_KEY` → Secret Key
- `IDRIVE_E2_BUCKET` → Bucket Name (z.B. complyo-backups)

## 2️⃣ Erstes Backup testen

```bash
# Test-Backup (ohne Cloud-Upload falls AWS CLI fehlt)
./backup-postgres.sh
```

**Erwartete Ausgabe:**
```
✅ Backup erstellt: complyo_db_2025-01-18_17-00-00.sql.gz (2.4M)
```

## 3️⃣ AWS CLI installieren (für Cloud-Backup)

```bash
# AWS CLI (für iDrive e2 Upload)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# Test
aws --version
```

## 4️⃣ Cloud-Backup testen

```bash
# Jetzt mit Cloud-Upload
./backup-postgres.sh
```

**Erwartete Ausgabe:**
```
✅ Backup erstellt: complyo_db_2025-01-18_17-05-00.sql.gz (2.4M)
☁️ Upload zu iDrive e2...
✅ Backup hochgeladen zu iDrive e2
```

## 5️⃣ Automatische Backups aktivieren

```bash
# Täglich um 3:00 Uhr
./setup-cron.sh
```

**Fertig!** 🎉

---

## 🔄 Restore testen (Optional)

```bash
# Restore-Menu öffnen
./restore-postgres.sh

# Wähle: 4 (Abbrechen) zum nur Backups anzeigen
```

---

## 📊 Status prüfen

```bash
# Lokale Backups
ls -lh /opt/backups/complyo/

# Cloud-Backups
aws s3 ls s3://complyo-backups/postgres/ \
  --endpoint-url YOUR_ENDPOINT \
  --region us-east-1

# Cron-Status
crontab -l | grep complyo
```

---

## 🆘 Probleme?

### AWS CLI fehlt
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install
```

### 403 Forbidden
→ Prüfe Credentials in `.env.backup`

### Container läuft nicht
```bash
docker-compose up -d postgres
```

---

**Für Details:** Siehe [README.md](./README.md)
