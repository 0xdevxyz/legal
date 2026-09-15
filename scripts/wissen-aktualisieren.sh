#!/bin/sh
# Wrapper fuer den taeglichen Wissens-Cronjob.
#
# Grund fuer den Wrapper, gefunden am 15.09.2026: seit alle KI-Aufrufe ueber
# backend/ki_zugang.py am Budget haengen, braucht auch dieser Cron Redis. Er
# laeuft als eigener `docker run` und bekam seine Umgebung aus der .env - dort
# steht aber weder REDIS_URL (die baut docker-compose erst zusammen) noch ein
# brauchbarer REDIS_HOST (`shared-redis`, ohne Passwort). Folge: ai_budget
# faellt fail-closed zurueck und blockiert JEDEN KI-Aufruf. Der Cron lief dann
# zwar "erfolgreich" durch, ordnete aber nichts mehr ein.
#
# Deshalb wie beim Betriebswaechter mit SMTP: den Wert aus dem LAUFENDEN
# Backend-Container nehmen, nicht aus der .env. Der Container traegt die
# Fassung, die docker-compose gebaut hat, inklusive korrektem Passwort.
#
# Crontab (sudo): 0 7 * * * /home/clawd/saas/legal/scripts/wissen-aktualisieren.sh
set -u
cd /home/clawd/saas/legal

REDIS_URL_C="$(docker exec complyo-backend printenv REDIS_URL 2>/dev/null || true)"
if [ -z "$REDIS_URL_C" ]; then
    echo "$(date -Is) wissen-aktualisieren: REDIS_URL nicht aus complyo-backend zu holen." >&2
    echo "  Ohne Redis blockiert das KI-Budget fail-closed jeden Aufruf. Abbruch," >&2
    echo "  damit der Lauf nicht still ohne KI durchlaeuft." >&2
    exit 1
fi

exec docker run --rm \
  --network legal_complyo-network \
  --env-file /home/clawd/saas/legal/.env \
  -e REDIS_URL="$REDIS_URL_C" \
  -e KNOWLEDGE_VAULT_PATH=/data/knowledge \
  -v /home/clawd/saas/legal/knowledge:/data/knowledge \
  legal-backend python3 cronjobs/knowledge_updater.py
