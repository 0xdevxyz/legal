#!/bin/bash
# Installiert die complyo-Cronjobs. Idempotent: vorhandene Eintraege werden nicht dupliziert.
#
# Ausfuehrungsmodelle:
#   - fetch_news / legal_change_monitor / tcf_gvl_sync: laufen IM Backend-Container
#     (docker exec), erben Secrets aus der Container-Umgebung.
#   - knowledge_updater / eurlex_crawler: SCHREIBEN den Gesetzes-Vault. Der Vault ist
#     in den Backend-Container nur read-only gemountet, daher laufen sie als
#     eigener `docker run --rm` mit einem read-write Vault-Mount (gleiches Image,
#     also gleiche Dependencies), damit die Schreibvorgaenge auf dem Host landen.

set -e

REPO="/home/clawd/saas/legal"
ENV_FILE="$REPO/.env"
VAULT="$REPO/knowledge"

DATABASE_URL=$(grep "^DATABASE_URL" "$ENV_FILE" | cut -d "=" -f2-)
OPENROUTER_API_KEY=$(grep "^OPENROUTER_API_KEY" "$ENV_FILE" | cut -d "=" -f2-)
OPENAI_API_KEY=$(grep "^OPENAI_API_KEY" "$ENV_FILE" | cut -d "=" -f2-)

IMAGE=$(docker inspect complyo-backend --format "{{.Config.Image}}")
NETWORK=$(docker inspect complyo-postgres --format "{{range \$k,\$v := .NetworkSettings.Networks}}{{\$k}}{{end}}")

echo "Repo=$REPO Image=$IMAGE Network=$NETWORK"

FETCH_NEWS_CRON="0 6 * * * docker exec complyo-backend python3 /app/cronjobs/fetch_news.py >> /var/log/complyo-news-fetch.log 2>&1"

KNOWLEDGE_CRON="0 7 * * * docker run --rm --network $NETWORK --env-file $ENV_FILE -e KNOWLEDGE_VAULT_PATH=/data/knowledge -v $VAULT:/data/knowledge $IMAGE python3 cronjobs/knowledge_updater.py >> /var/log/complyo-knowledge-updater.log 2>&1"

EURLEX_CRON="0 4 * * 1 docker run --rm -e KNOWLEDGE_VAULT_PATH=/data/knowledge -e EURLEX_MAX_AGE_DAYS=30 -v $VAULT:/data/knowledge $IMAGE python3 cronjobs/eurlex_crawler.py >> /var/log/complyo-eurlex.log 2>&1"

GVL_CRON="0 3 * * * docker exec complyo-backend python3 /app/cronjobs/tcf_gvl_sync.py >> /var/log/complyo-tcf-gvl-sync.log 2>&1"

LEGAL_MONITOR_CRON="0 5 * * * docker exec complyo-backend python3 /app/cronjobs/legal_change_monitor_cron.py >> /var/log/complyo-legal-monitor.log 2>&1"

add_job() {
  local marker="$1"; local job="$2"; local logfile="$3"
  if crontab -l 2>/dev/null | grep -qF "$marker"; then
    echo "= vorhanden: $marker"
  else
    (crontab -l 2>/dev/null || true; echo "$job") | crontab -
    [ -n "$logfile" ] && { touch "$logfile" 2>/dev/null || true; chmod 666 "$logfile" 2>/dev/null || true; }
    echo "+ hinzugefuegt: $marker"
  fi
}

add_job "fetch_news.py"                 "$FETCH_NEWS_CRON"     "/var/log/complyo-news-fetch.log"
add_job "cronjobs/knowledge_updater.py" "$KNOWLEDGE_CRON"      "/var/log/complyo-knowledge-updater.log"
add_job "cronjobs/eurlex_crawler.py"    "$EURLEX_CRON"         "/var/log/complyo-eurlex.log"
add_job "tcf_gvl_sync.py"               "$GVL_CRON"            "/var/log/complyo-tcf-gvl-sync.log"
add_job "legal_change_monitor_cron.py"  "$LEGAL_MONITOR_CRON"  "/var/log/complyo-legal-monitor.log"

echo "Fertig. Aktuelle complyo-Cronjobs:"
crontab -l 2>/dev/null | grep -E "complyo|cronjobs/" || true
