#!/bin/bash

# SSL Certificate Setup Script for Complyo Production
# Automated Let's Encrypt certificate generation and renewal
# Usage: ./ssl-setup.sh [setup|renew|status]

set -e

# Configuration
DOMAINS="complyo.tech www.complyo.tech api.complyo.tech app.complyo.tech"
EMAIL="admin@complyo.tech"
WEBROOT_PATH="/var/www/certbot"
DOCKER_COMPOSE_FILE="docker-compose.production.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Install certbot if not present
install_certbot() {
    if ! command -v certbot &> /dev/null; then
        log "Installing certbot..."
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    else
        log "Certbot already installed"
    fi
}

# Create webroot directory
setup_webroot() {
    log "Setting up webroot directory..."
    mkdir -p $WEBROOT_PATH
    chown -R www-data:www-data $WEBROOT_PATH
    chmod -R 755 $WEBROOT_PATH
}

# Generate certificates using standalone method
generate_certificates() {
    log "Generating SSL certificates for domains: $DOMAINS"
    
    # Create domain list for certbot
    DOMAIN_ARGS=""
    for domain in $DOMAINS; do
        DOMAIN_ARGS="$DOMAIN_ARGS -d $domain"
    done
    
    # Stop nginx temporarily if running
    if docker ps | grep -q complyo-gateway; then
        log "Stopping nginx for certificate generation..."
        docker-compose -f $DOCKER_COMPOSE_FILE stop complyo-gateway
    fi
    
    # Generate certificates using standalone method for initial setup
    certbot certonly \
        --standalone \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        $DOMAIN_ARGS
    
    if [ $? -eq 0 ]; then
        log "✅ Certificates generated successfully"
    else
        error "❌ Certificate generation failed"
        exit 1
    fi
}

# Setup certificate renewal via cron
setup_renewal() {
    log "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > /usr/local/bin/certbot-renew.sh << 'EOF'
#!/bin/bash
# Automated certificate renewal for Complyo

log_file="/var/log/certbot-renewal.log"
date_stamp=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$date_stamp] Starting certificate renewal check" >> $log_file

# Attempt renewal
certbot renew --quiet --post-hook "docker-compose -f /opt/projects/saas-project-2/docker-compose.production.yml restart complyo-gateway"

if [ $? -eq 0 ]; then
    echo "[$date_stamp] Certificate renewal successful or not needed" >> $log_file
else
    echo "[$date_stamp] Certificate renewal failed" >> $log_file
    # Send alert (implement notification system)
fi
EOF

    chmod +x /usr/local/bin/certbot-renew.sh
    
    # Add cron job for automatic renewal (daily at 2 AM)
    cron_job="0 2 * * * /usr/local/bin/certbot-renew.sh"
    
    # Check if cron job already exists
    if ! crontab -l 2>/dev/null | grep -q "certbot-renew.sh"; then
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        log "✅ Automatic renewal cron job added"
    else
        log "ℹ️  Cron job already exists"
    fi
}

# Check certificate status
check_certificate_status() {
    log "Checking certificate status..."
    
    for domain in $DOMAINS; do
        if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
            expiry=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$domain/fullchain.pem" | cut -d= -f2)
            log "✅ Certificate for $domain expires: $expiry"
        else
            warning "❌ No certificate found for $domain"
        fi
    done
}

# Test certificate renewal
test_renewal() {
    log "Testing certificate renewal..."
    certbot renew --dry-run
    
    if [ $? -eq 0 ]; then
        log "✅ Certificate renewal test successful"
    else
        error "❌ Certificate renewal test failed"
        exit 1
    fi
}

# Main certificate setup function
setup_ssl() {
    log "🔐 Starting SSL certificate setup for Complyo"
    
    check_root
    install_certbot
    setup_webroot
    generate_certificates
    setup_renewal
    
    log "🎉 SSL certificate setup completed successfully!"
    log "📋 Next steps:"
    log "   1. Start the production Docker Compose stack"
    log "   2. Verify all domains are accessible via HTTPS"
    log "   3. Check certificate auto-renewal: certbot renew --dry-run"
}

# Manual certificate renewal
renew_certificates() {
    log "🔄 Manually renewing certificates..."
    
    check_root
    certbot renew --force-renewal
    
    if [ $? -eq 0 ]; then
        log "✅ Certificate renewal successful"
        # Restart nginx to load new certificates
        if docker ps | grep -q complyo-gateway; then
            docker-compose -f $DOCKER_COMPOSE_FILE restart complyo-gateway
            log "🔄 Nginx restarted to load new certificates"
        fi
    else
        error "❌ Certificate renewal failed"
        exit 1
    fi
}

# Display usage information
show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup    - Initial SSL certificate setup"
    echo "  renew    - Manual certificate renewal"
    echo "  status   - Check certificate status"
    echo "  test     - Test automatic renewal"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup    # Initial setup"
    echo "  $0 renew    # Manual renewal"
    echo "  $0 status   # Check status"
}

# Main script logic
case "${1:-setup}" in
    "setup")
        setup_ssl
        ;;
    "renew")
        renew_certificates
        ;;
    "status")
        check_certificate_status
        ;;
    "test")
        test_renewal
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac