#!/bin/bash
# ===========================================
# Complyo SSL-Fix Quick Deploy
# Führe dieses Script auf dem Produktionsserver aus
# ===========================================

set -e

echo "=========================================="
echo "  Complyo SSL-Fix Deployment"
echo "=========================================="

cd /opt/projects/saas-project-2 || {
    echo "Projekt-Verzeichnis nicht gefunden!"
    echo "Bitte passe den Pfad an."
    exit 1
}

echo ""
echo "1. Git Pull für neueste Änderungen..."
git pull origin main || git pull origin master || echo "Git pull übersprungen"

echo ""
echo "2. SSL-Zertifikate erneuern..."
sudo ./scripts/renew-ssl.sh

echo ""
echo "3. Docker Container neu starten..."
docker-compose -f docker-compose.production.yml down complyo-ssl-proxy
docker-compose -f docker-compose.production.yml up -d complyo-ssl-proxy

echo ""
echo "4. Warte auf Container-Start..."
sleep 5

echo ""
echo "5. Prüfe Container-Status..."
docker ps | grep complyo

echo ""
echo "=========================================="
echo "  SSL-Fix Deployment abgeschlossen!"
echo "=========================================="
echo ""
echo "Teste jetzt:"
echo "  curl -I https://complyo.tech"
echo "  curl -I https://app.complyo.tech"
echo "  curl -I https://api.complyo.tech/health"
echo ""
