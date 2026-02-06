#!/bin/bash
# ===========================================
# Complyo SSL-Zertifikat Erneuerung
# Datum: 2026-02-03
# ===========================================

set -e

echo "=========================================="
echo "  Complyo SSL-Zertifikat Erneuerung"
echo "=========================================="
echo ""

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Prüfen ob als root ausgeführt
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Dieses Script muss als root ausgeführt werden!${NC}"
   echo "Bitte verwende: sudo $0"
   exit 1
fi

echo -e "${YELLOW}1. Prüfe aktuellen Zertifikat-Status...${NC}"
echo ""

# Zeige alle Zertifikate
certbot certificates 2>/dev/null || {
    echo -e "${RED}Certbot nicht gefunden! Bitte installieren mit:${NC}"
    echo "sudo apt install certbot python3-certbot-nginx"
    exit 1
}

echo ""
echo -e "${YELLOW}2. Erneuere alle Zertifikate...${NC}"
echo ""

# Versuche zuerst dry-run
echo "Führe Dry-Run durch..."
if certbot renew --dry-run 2>/dev/null; then
    echo -e "${GREEN}Dry-Run erfolgreich!${NC}"
else
    echo -e "${YELLOW}Dry-Run fehlgeschlagen, versuche Force-Renewal...${NC}"
fi

# Echte Erneuerung
echo ""
echo "Führe echte Erneuerung durch..."

# Option 1: Normale Erneuerung
certbot renew --force-renewal || {
    echo -e "${YELLOW}Normale Erneuerung fehlgeschlagen, versuche mit --standalone...${NC}"
    
    # Stoppe nginx temporär für standalone
    echo "Stoppe nginx temporär..."
    systemctl stop nginx 2>/dev/null || docker stop complyo-ssl-proxy 2>/dev/null || true
    
    # Standalone Erneuerung
    certbot renew --standalone --force-renewal || {
        # Falls das auch fehlschlägt, neues Zertifikat anfordern
        echo -e "${YELLOW}Fordere neues Zertifikat an...${NC}"
        certbot certonly --standalone \
            -d complyo.tech \
            -d www.complyo.tech \
            -d app.complyo.tech \
            -d api.complyo.tech \
            --agree-tos \
            --email admin@complyo.tech \
            --non-interactive
    }
    
    # Starte nginx wieder
    echo "Starte nginx..."
    systemctl start nginx 2>/dev/null || docker start complyo-ssl-proxy 2>/dev/null || true
}

echo ""
echo -e "${YELLOW}3. Prüfe neue Zertifikate...${NC}"
echo ""
certbot certificates

echo ""
echo -e "${YELLOW}4. Lade nginx/Docker neu...${NC}"
echo ""

# Prüfe ob Docker oder systemd nginx läuft
if docker ps | grep -q complyo-ssl-proxy; then
    echo "Docker nginx gefunden - starte Container neu..."
    docker restart complyo-ssl-proxy
    echo -e "${GREEN}Docker Container neu gestartet!${NC}"
elif systemctl is-active --quiet nginx; then
    echo "Systemd nginx gefunden - lade neu..."
    nginx -t && systemctl reload nginx
    echo -e "${GREEN}Nginx neu geladen!${NC}"
else
    echo -e "${YELLOW}Weder Docker noch systemd nginx aktiv.${NC}"
    echo "Bitte manuell neu starten!"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  SSL-Erneuerung abgeschlossen!"
echo "==========================================${NC}"
echo ""
echo "Prüfe jetzt die Websites:"
echo "  - https://complyo.tech"
echo "  - https://app.complyo.tech"
echo "  - https://api.complyo.tech"
echo ""
echo "Zertifikat-Details im Browser prüfen (Schloss-Symbol)."
echo ""
