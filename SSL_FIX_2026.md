# 🔒 SSL-Zertifikat Fix - Complyo

## Aktuelle Situation (2026-02-03)

**Problem:** SSL-Zertifikat ist abgelaufen (war gültig bis 2026-01-24)

**Fehler:** `NET::ERR_CERT_DATE_INVALID`

## Quick Fix

Auf dem **Produktionsserver** ausführen:

```bash
# Option 1: Komplettes Script
cd /opt/projects/saas-project-2
sudo ./scripts/deploy-ssl-fix.sh

# Option 2: Nur SSL erneuern
sudo ./scripts/renew-ssl.sh
```

## Manuelle Erneuerung

Falls die Scripts nicht funktionieren:

```bash
# 1. Stoppe nginx temporär
sudo systemctl stop nginx
# ODER für Docker:
docker stop complyo-ssl-proxy

# 2. Erneuere Zertifikate
sudo certbot certonly --standalone \
    -d complyo.tech \
    -d www.complyo.tech \
    -d app.complyo.tech \
    -d api.complyo.tech \
    --agree-tos \
    --email admin@complyo.tech \
    --force-renewal

# 3. Starte nginx wieder
sudo systemctl start nginx
# ODER für Docker:
docker start complyo-ssl-proxy

# 4. Prüfe Status
sudo certbot certificates
```

## Docker Deployment

```bash
# Nginx Container neu starten (lädt neue Zertifikate)
docker-compose -f docker-compose.production.yml restart complyo-ssl-proxy

# Oder komplett neu deployen
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

## Konfigurationsdateien

- **Nginx Konfiguration:** `nginx/production.conf`
- **Docker Compose:** `docker-compose.production.yml`
- **Zertifikate:** `/etc/letsencrypt/live/complyo.tech/`

## SSL-Pfade in nginx/production.conf

```nginx
ssl_certificate /etc/letsencrypt/live/complyo.tech/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/complyo.tech/privkey.pem;
```

## Prüfung

```bash
# Zertifikat-Status
sudo certbot certificates

# SSL-Test
curl -I https://complyo.tech
curl -I https://app.complyo.tech
curl -I https://api.complyo.tech/health

# Online-Test
# https://www.ssllabs.com/ssltest/analyze.html?d=complyo.tech
```

## Automatische Erneuerung

Die `docker-compose.production.yml` enthält jetzt einen **Certbot-Container**, der automatisch alle 12 Stunden prüft und erneuert.

```yaml
certbot:
  image: certbot/certbot:latest
  entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
```

## Historie

| Datum | Aktion | Status |
|-------|--------|--------|
| 2025-12-29 | `complyo.tech` abgelaufen | ❌ |
| 2026-01-09 | Wechsel zu `complyo.tech-0001` | ✅ |
| 2026-01-24 | `complyo.tech-0001` abgelaufen | ❌ |
| 2026-02-03 | Erneuerung erforderlich | ⏳ |

## Support

Bei Problemen:
1. Logs prüfen: `docker logs complyo-ssl-proxy`
2. Certbot Logs: `sudo cat /var/log/letsencrypt/letsencrypt.log`
