#!/bin/bash

# Prüfe auf hohe Angriffslast
ATTACKS_PER_MINUTE=$(docker logs nginx-proxy --since 1m 2>/dev/null | \
    grep -E "(wp-admin|wp-login|wordpress)" | \
    grep " 404 " | wc -l)

# Alert wenn mehr als 10 Angriffe pro Minute
if [[ $ATTACKS_PER_MINUTE -gt 10 ]]; then
    echo "🚨 HIGH ATTACK LOAD: $ATTACKS_PER_MINUTE WordPress scans in last minute"
    echo "Time: $(date)"
    echo "Recent attacks:"
    docker logs nginx-proxy --since 1m 2>/dev/null | \
        grep -E "(wp-admin|wp-login|wordpress)" | \
        grep " 404 " | tail -5
    
    # Verschärfe Fail2ban für 1 Stunde
    fail2ban-client set nginx-wordpress bantime 7200
    fail2ban-client set nginx-wordpress maxretry 1
    
    echo "⚡ Temporarily hardened fail2ban rules"
fi
