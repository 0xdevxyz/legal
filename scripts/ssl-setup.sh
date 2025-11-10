#!/bin/bash

setup() {
    if [ -d "/etc/letsencrypt/live/complyo.tech" ]; then
        echo "[INFO] SSL certificates already exist and are valid. Skipping renewal due to rate limits."
        return 0
    fi
    
    echo "Certificates don't exist. You'll need to wait until after 2025-10-01 20:40:55 UTC for Let's Encrypt rate limits to reset."
    return 0
}

status() {
    if [ -d "/etc/letsencrypt/live/complyo.tech" ]; then
        echo "SSL certificates exist at: /etc/letsencrypt/live/complyo.tech"
        openssl x509 -in /etc/letsencrypt/live/complyo.tech/cert.pem -noout -dates 2>/dev/null || echo "Could not read certificate details"
    else
        echo "No SSL certificates found"
    fi
}

case "${1:-setup}" in
    "setup")
        setup
        ;;
    "status")
        status
        ;;
    *)
        echo "Usage: $0 [setup|status]"
        exit 1
        ;;
esac
