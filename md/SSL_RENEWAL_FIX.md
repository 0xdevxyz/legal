# 🔒 SSL-Zertifikat-Erneuerung - Problem & Lösung

## Problem

Die SSL-Zertifikate für `complyo.tech` und `app.complyo.tech` werden nicht automatisch erneuert, obwohl:
- ✅ Certbot installiert ist
- ✅ Certbot-Timer aktiv ist
- ✅ Cron-Jobs für Erneuerung vorhanden sind

## Ursache

1. **Abgelaufenes Zertifikat**: Das alte `complyo.tech` Zertifikat ist am **29.12.2025 abgelaufen**
2. **Neues Zertifikat vorhanden**: Es gibt ein gültiges `complyo.tech-0001` Zertifikat (läuft bis 24.01.2026)
3. **ACME-Challenge nicht erreichbar**: Die automatische Erneuerung schlägt fehl, weil `/.well-known/acme-challenge/` nicht erreichbar ist (404)

## Lösung

### Schritt 1: Script ausführen

```bash
sudo /opt/projects/saas-project-2/scripts/fix-ssl-renewal.sh
```

Das Script:
- ✅ Prüft Zertifikat-Status
- ✅ Erstellt Symlink zum gültigen Zertifikat
- ✅ Erneuert abgelaufene Zertifikate
- ✅ Richtet ACME-Challenge-Route ein
- ✅ Aktiviert Certbot-Timer
- ✅ Testet Erneuerung
- ✅ Lädt Nginx neu

### Schritt 2: Nginx-Konfiguration prüfen

Stelle sicher, dass in allen Nginx-Server-Blocks die ACME-Challenge-Route vorhanden ist:

```nginx
# HTTP-Server für ACME-Challenge
server {
    listen 80;
    server_name complyo.tech api.complyo.tech app.complyo.tech;
    
    # ACME Challenge für Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        try_files $uri =404;
    }
    
    # Redirect zu HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}
```

### Schritt 3: Zertifikat-Pfade in Nginx korrigieren

**Wichtig**: Die Nginx-Konfiguration muss auf das **gültige** Zertifikat verweisen:

```nginx
# Für complyo.tech, api.complyo.tech, app.complyo.tech
ssl_certificate /etc/letsencrypt/live/complyo.tech-0001/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/complyo.tech-0001/privkey.pem;
```

**ODER** (nach Symlink-Erstellung):
```nginx
ssl_certificate /etc/letsencrypt/live/complyo.tech/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/complyo.tech/privkey.pem;
```

### Schritt 4: Manuelle Erneuerung (falls nötig)

Falls die automatische Erneuerung weiterhin fehlschlägt:

```bash
# Erneuere manuell mit nginx-Plugin
sudo certbot certonly --nginx \
    -d complyo.tech \
    -d api.complyo.tech \
    -d app.complyo.tech \
    --non-interactive \
    --agree-tos \
    --email admin@complyo.tech

# Oder mit webroot-Methode
sudo certbot certonly --webroot \
    -w /var/www/html \
    -d complyo.tech \
    -d api.complyo.tech \
    -d app.complyo.tech \
    --non-interactive \
    --agree-tos \
    --email admin@complyo.tech
```

## Automatische Erneuerung sicherstellen

### Certbot-Timer prüfen

```bash
sudo systemctl status certbot.timer
sudo systemctl list-timers certbot.timer
```

### Cron-Job prüfen

```bash
sudo crontab -l | grep certbot
```

Sollte enthalten:
```
0 12 * * * /usr/bin/certbot renew --quiet
```

### Erneuerung testen

```bash
sudo certbot renew --dry-run
```

## Aktueller Status

**Zertifikate:**
- ❌ `complyo.tech` (alt): **ABGELAUFEN** (29.12.2025)
- ✅ `complyo.tech-0001`: **GÜLTIG** (bis 24.01.2026) - enthält: complyo.tech, api.complyo.tech, app.complyo.tech
- ✅ `app.complyo.tech` (separat): **GÜLTIG** (bis 20.02.2026)

**Empfehlung:**
- Verwende `complyo.tech-0001` für alle drei Domains (complyo.tech, api.complyo.tech, app.complyo.tech)
- Oder erneuere `app.complyo.tech` separat, wenn gewünscht

## Nächste Schritte

1. ✅ Script ausführen: `sudo /opt/projects/saas-project-2/scripts/fix-ssl-renewal.sh`
2. ✅ Nginx-Konfiguration prüfen und ggf. anpassen
3. ✅ Erneuerung testen: `sudo certbot renew --dry-run`
4. ✅ Nginx neu laden: `sudo systemctl reload nginx`
5. ✅ SSL-Status prüfen: `sudo certbot certificates`

## Monitoring

Zertifikat-Status regelmäßig prüfen:

```bash
# Zertifikat-Status anzeigen
sudo certbot certificates

# Ablaufdatum prüfen
sudo openssl x509 -in /etc/letsencrypt/live/complyo.tech-0001/cert.pem -noout -dates

# Erneuerung testen
sudo certbot renew --dry-run
```

## Troubleshooting

### Problem: ACME-Challenge gibt 404

**Lösung**: Stelle sicher, dass in Nginx die Route `/.well-known/acme-challenge/` auf `/var/www/html` zeigt.

### Problem: Zertifikat wird nicht erneuert

**Lösung**: 
1. Prüfe Certbot-Logs: `sudo tail -f /var/log/letsencrypt/letsencrypt.log`
2. Prüfe Nginx-Error-Logs: `sudo tail -f /var/log/nginx/error.log`
3. Teste manuelle Erneuerung: `sudo certbot renew --force-renewal`

### Problem: Nginx verwendet abgelaufenes Zertifikat

**Lösung**: 
1. Prüfe welche Zertifikate Nginx verwendet: `sudo nginx -T | grep ssl_certificate`
2. Aktualisiere Nginx-Konfiguration mit gültigem Zertifikat-Pfad
3. Teste Nginx-Konfiguration: `sudo nginx -t`
4. Lade Nginx neu: `sudo systemctl reload nginx`
