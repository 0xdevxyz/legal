#!/bin/sh
# Startet Container neu, deren Healthcheck fehlschlaegt.
#
# Anlass ist der Lasttest vom 03.09.2026: nach acht gleichzeitigen Scans stand
# complyo-backend auf "unhealthy", der Scanpfad lieferte nichts mehr, und
# NIEMAND griff ein. `restart: unless-stopped` hilft dabei nicht — das startet
# nur bei Prozessende neu, nicht bei einem gescheiterten Healthcheck. Der
# Container lief also weiter und war trotzdem kaputt.
#
# Bewusst als Host-Skript und nicht als Container mit docker.sock: wer die
# Socket einbindet, gibt Root auf dem Host weiter. Fuer einen Neustarter ist
# das ein zu hoher Preis.
#
# Crontab: * * * * * /home/clawd/saas/legal/scripts/gesundheitswaechter.sh >> /var/log/complyo-gesundheit.log 2>&1
set -u

CONTAINER="complyo-backend complyo-landing complyo-dashboard complyo-postgres complyo-redis"
ABLAGE=/home/clawd/saas/legal/data/waechter
ZAEHLER="$ABLAGE/unhealthy_zaehler"
JOURNAL="$ABLAGE/neustarts.log"

# Zwei aufeinanderfolgende Fehlschlaege, nicht einer: ein Healthcheck kann
# waehrend eines Deploys oder einer Lastspitze einmal danebengehen, ohne dass
# der Dienst kaputt ist.
SCHWELLE=2
# Ein frisch gestarteter Container darf hochfahren, bevor er beurteilt wird.
MINDESTALTER_S=180
# Mehr als drei Neustarts je Container und Stunde heisst: Neustarten hilft
# nicht. Dann lieber kaputt und laut als in einer Schleife.
MAX_JE_STUNDE=3

mkdir -p "$ABLAGE" 2>/dev/null || true
touch "$ZAEHLER" "$JOURNAL" 2>/dev/null || true

jetzt=$(date -u +%s)

zaehlerstand() {
  grep "^$1 " "$ZAEHLER" 2>/dev/null | tail -1 | cut -d' ' -f2
}

setze_zaehler() {
  grep -v "^$1 " "$ZAEHLER" > "$ZAEHLER.tmp" 2>/dev/null || true
  [ "$2" -gt 0 ] && echo "$1 $2" >> "$ZAEHLER.tmp"
  mv "$ZAEHLER.tmp" "$ZAEHLER"
}

neustarts_letzte_stunde() {
  grenze=$((jetzt - 3600))
  awk -v c="$1" -v g="$grenze" '$1 >= g && $2 == c' "$JOURNAL" 2>/dev/null | wc -l
}

for c in $CONTAINER; do
  zustand=$(docker inspect "$c" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}kein-healthcheck{{end}}' 2>/dev/null) || continue
  [ "$zustand" = "kein-healthcheck" ] && continue

  if [ "$zustand" != "unhealthy" ]; then
    setze_zaehler "$c" 0
    continue
  fi

  gestartet=$(docker inspect "$c" --format '{{.State.StartedAt}}' 2>/dev/null)
  gestartet_s=$(date -u -d "$gestartet" +%s 2>/dev/null || echo 0)
  alter=$((jetzt - gestartet_s))
  if [ "$alter" -lt "$MINDESTALTER_S" ]; then
    echo "$(date -Is) $c unhealthy, aber erst ${alter}s alt — Anlaufzeit abwarten"
    continue
  fi

  n=$(zaehlerstand "$c"); [ -z "$n" ] && n=0
  n=$((n + 1))
  setze_zaehler "$c" "$n"
  echo "$(date -Is) $c unhealthy ($n/$SCHWELLE)"
  [ "$n" -lt "$SCHWELLE" ] && continue

  bisher=$(neustarts_letzte_stunde "$c")
  if [ "$bisher" -ge "$MAX_JE_STUNDE" ]; then
    echo "$(date -Is) $c unhealthy, aber schon $bisher Neustarts in der letzten Stunde — KEIN weiterer. Das braucht einen Menschen."
    echo "$jetzt $c aufgegeben" >> "$JOURNAL"
    setze_zaehler "$c" 0
    continue
  fi

  echo "$(date -Is) $c wird neu gestartet (Grund: Healthcheck rot)"
  # Kein `up --force-recreate`: das wuerde das Image neu aufloesen und
  # womoeglich einen halbfertigen Build einspielen. `restart` nimmt genau den
  # Stand, der schon lief.
  if docker restart "$c" >/dev/null 2>&1; then
    echo "$jetzt $c neugestartet" >> "$JOURNAL"
    echo "$(date -Is) $c neu gestartet"
  else
    echo "$jetzt $c neustart-fehlgeschlagen" >> "$JOURNAL"
    echo "$(date -Is) $c Neustart FEHLGESCHLAGEN"
  fi
  setze_zaehler "$c" 0
done
