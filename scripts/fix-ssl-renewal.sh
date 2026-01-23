#!/bin/bash
# SSL-Zertifikat-Erneuerung für Complyo fixen
# Behebt abgelaufene Zertifikate und richtet automatische Erneuerung ein

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}" >&2; }
warning() { echo -e "${YELLOW}[WARNING] $1${NC}"; }

# Prüfe ob als root ausgeführt
if [[ $EUID -ne 0 ]]; then
   error "Dieses Script muss als root ausgeführt werden (sudo)"
   exit 1
fi

log "🔒 SSL-Zertifikat-Erneuerung für Complyo einrichten"

# 1. Prüfe Zertifikat-Status
log "📋 Prüfe Zertifikat-Status..."
CERT_STATUS=$(sudo certbot certificates 2>/dev/null | grep -A 10 "complyo.tech" | grep "Expiry Date" || echo "")

if echo "$CERT_STATUS" | grep -q "EXPIRED"; then
    warning "Abgelaufenes Zertifikat gefunden!"
    
    # Prüfe ob es ein neueres Zertifikat gibt
    if [ -d "/etc/letsencrypt/live/complyo.tech-0001" ]; then
        log "✅ Neueres Zertifikat gefunden: complyo.tech-0001"
        
        # Erstelle Symlink zum neueren Zertifikat
        if [ -d "/etc/letsencrypt/live/complyo.tech" ]; then
            log "📦 Sichere altes Zertifikat..."
            mv /etc/letsencrypt/live/complyo.tech /etc/letsencrypt/live/complyo.tech.expired.$(date +%Y%m%d)
        fi
        
        log "🔗 Erstelle Symlink zum gültigen Zertifikat..."
        ln -sf /etc/letsencrypt/live/complyo.tech-0001 /etc/letsencrypt/live/complyo.tech
        log "✅ Symlink erstellt"
    fi
fi

# 2. Erneuere abgelaufene Zertifikate manuell
log "🔄 Erneuere abgelaufene Zertifikate..."

# Erneuere complyo.tech (mit allen Subdomains)
if [ -f "/etc/letsencrypt/renewal/complyo.tech.conf" ] || [ -f "/etc/letsencrypt/renewal/complyo.tech-0001.conf" ]; then
    log "🔄 Erneuere Zertifikat für complyo.tech, api.complyo.tech, app.complyo.tech..."
    
    # Verwende webroot-Methode für Erneuerung
    sudo certbot renew --cert-name complyo.tech-0001 --force-renewal \
        --webroot \
        --webroot-path=/var/www/html \
        --quiet || {
        
        warning "Automatische Erneuerung fehlgeschlagen. Versuche manuelle Erneuerung..."
        
        # Manuelle Erneuerung mit nginx-Plugin
        sudo certbot certonly --nginx \
            -d complyo.tech \
            -d api.complyo.tech \
            -d app.complyo.tech \
            --non-interactive \
            --agree-tos \
            --email admin@complyo.tech \
            --keep-until-expiring || {
            error "Manuelle Erneuerung fehlgeschlagen"
            exit 1
        }
    }
fi

# 3. Stelle sicher, dass ACME-Challenge-Route in Nginx vorhanden ist
log "🔧 Prüfe Nginx-Konfiguration für ACME-Challenge..."

NGINX_CONF="/etc/nginx/sites-available/complyo.tech"
if [ ! -f "$NGINX_CONF" ]; then
    warning "Nginx-Konfiguration nicht gefunden. Erstelle ACME-Challenge-Route..."
    
    # Erstelle Basis-Konfiguration für ACME-Challenge
    cat > /tmp/complyo-acme.conf << 'EOF'
# ACME Challenge für Let's Encrypt
location /.well-known/acme-challenge/ {
    root /var/www/html;
    try_files $uri =404;
}
EOF
    
    log "✅ ACME-Challenge-Konfiguration erstellt"
fi

# 4. Stelle sicher, dass Certbot-Timer aktiv ist
log "⏰ Prüfe Certbot-Timer..."
if systemctl is-active --quiet certbot.timer; then
    log "✅ Certbot-Timer ist aktiv"
else
    warning "Certbot-Timer ist nicht aktiv. Aktiviere..."
    systemctl enable certbot.timer
    systemctl start certbot.timer
    log "✅ Certbot-Timer aktiviert"
fi

# 5. Teste Erneuerung
log "🧪 Teste Erneuerung (Dry-Run)..."
if sudo certbot renew --dry-run > /dev/null 2>&1; then
    log "✅ Erneuerung-Test erfolgreich"
else
    warning "Erneuerung-Test fehlgeschlagen. Prüfe Logs: /var/log/letsencrypt/letsencrypt.log"
fi

# 6. Reload Nginx
log "🔄 Lade Nginx neu..."
if nginx -t > /dev/null 2>&1; then
    systemctl reload nginx
    log "✅ Nginx neu geladen"
else
    error "Nginx-Konfiguration hat Fehler. Bitte prüfen: sudo nginx -t"
    exit 1
fi

# 7. Zeige finalen Status
log "📊 Finaler Zertifikat-Status:"
sudo certbot certificates 2>/dev/null | grep -A 10 "complyo.tech" || true

log "✅ SSL-Zertifikat-Erneuerung eingerichtet!"
log ""
log "📅 Nächste automatische Erneuerung:"
systemctl list-timers certbot.timer --no-pager | grep certbot || true
