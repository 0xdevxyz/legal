#!/bin/sh
# Betriebswächter-Wrapper: sammelt die Host-Signale (docker ps / docker logs),
# die im Container nicht erreichbar sind, und startet den eigentlichen
# Wächter im Backend-Image (DB + SMTP kommen aus der .env).
# Crontab (sudo): 12 * * * * /home/clawd/saas/legal/scripts/betriebswaechter.sh >> /var/log/complyo-waechter.log 2>&1
set -u
cd /home/clawd/saas/legal

CONTAINER_STATUS="$(docker ps --filter name=complyo --format '{{.Names}}: {{.Status}}')"
FEHLER_1H="$(docker logs complyo-backend --since 1h 2>&1 | grep -c 'ERROR' || true)"
FEHLER_BEISPIELE="$(docker logs complyo-backend --since 1h 2>&1 | grep 'ERROR' | head -3)"

# SMTP-Werte aus dem LAUFENDEN Backend-Container übernehmen, nicht aus der
# .env-Datei: das Passwort steht dort wegen $/# in einfachen Quotes, die
# docker-compose entfernt — `docker run --env-file` aber nicht (bekannte
# Falle vom SMTP-Livegang 11.08.). Der Container trägt die korrekten Werte.
SMTP_HOST_C="$(docker exec complyo-backend printenv SMTP_HOST 2>/dev/null || true)"
SMTP_PORT_C="$(docker exec complyo-backend printenv SMTP_PORT 2>/dev/null || true)"
SMTP_USER_C="$(docker exec complyo-backend printenv SMTP_USERNAME 2>/dev/null || true)"
SMTP_PASS_C="$(docker exec complyo-backend printenv SMTP_PASSWORD 2>/dev/null || true)"

# Backend read-only gemountet: der Wächter läuft immer mit dem aktuellen
# Code-Stand, unabhängig davon, wann das Image zuletzt gebaut wurde.
exec docker run --rm \
  --network legal_complyo-network \
  --env-file /home/clawd/saas/legal/.env \
  -v /home/clawd/saas/legal/backend:/app:ro \
  -w /app \
  -v /home/clawd/saas/legal/data/waechter:/data/waechter \
  -e SMTP_HOST="$SMTP_HOST_C" \
  -e SMTP_PORT="$SMTP_PORT_C" \
  -e SMTP_USERNAME="$SMTP_USER_C" \
  -e SMTP_PASSWORD="$SMTP_PASS_C" \
  -e WAECHTER_CONTAINER_STATUS="$CONTAINER_STATUS" \
  -e WAECHTER_FEHLER_1H="$FEHLER_1H" \
  -e WAECHTER_FEHLER_BEISPIELE="$FEHLER_BEISPIELE" \
  legal-backend python3 cronjobs/betriebswaechter.py
