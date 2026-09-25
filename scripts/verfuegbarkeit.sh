#!/bin/sh
# Verfuegbarkeit messen, damit sie sich zusagen laesst.
#
# Anlass (25.09.2026): Ziffer 7 des Nutzungsvertrages bietet zwei Fassungen an,
# eine mit zugesagter Verfuegbarkeit und eine ohne. Die Fassung mit Zusage ist
# nicht waehlbar, weil niemand eine Quote belegen kann: der minuetliche
# Gesundheitswaechter schreibt nur, wenn er einen Container neu startet, und
# sein Protokoll hatte am 25.09. exakt null Zeilen. Es gab keine Messung.
#
# Dieses Skript misst nicht den Container, sondern das, was ein Kunde erlebt:
# eine Anfrage ueber die oeffentliche Adresse, also durch DNS, TLS, nginx und
# die Anwendung. Ein gesunder Container hinter einem kaputten nginx ist fuer
# den Kunden ein Ausfall, und genau so soll er gezaehlt werden.
#
# Eine Zeile je Minute, je Tag eine Datei:
#     <epoch> <http_api> <ms_api> <http_landing> <ms_landing>
#
# Was diese Messung NICHT kann, und was deshalb in jede Zusage gehoert:
#   * Sie misst von EINEM Ort aus. Ein Netzproblem zwischen Kunde und
#     Rechenzentrum sieht sie nicht.
#   * Sie misst EINMAL je Minute. Ein Ausfall von vierzig Sekunden kann durch
#     das Raster fallen.
#   * Sie misst vom Server selbst. Das ist der kuerzeste Weg und damit der
#     freundlichste; eine Messung von aussen faellt schlechter aus.
#
# Crontab: * * * * * /home/clawd/saas/legal/scripts/verfuegbarkeit.sh
set -u

ABLAGE=/home/clawd/saas/legal/data/verfuegbarkeit
mkdir -p "$ABLAGE" 2>/dev/null || true

jetzt=$(date -u +%s)
tag=$(date -u +%Y-%m-%d)
ziel="$ABLAGE/$tag.log"

# --max-time 10: laenger als zehn Sekunden ist fuer einen Gesundheitsabruf
# ohnehin ein Ausfall, und der naechste Lauf kommt in sechzig Sekunden.
messe() {
  curl -s -o /dev/null -w '%{http_code} %{time_total}' --max-time 10 "$1" 2>/dev/null \
    || echo '000 10.0'
}

api=$(messe "https://api.complyo.de/health")
landing=$(messe "https://complyo.de/")

api_code=$(echo "$api" | cut -d' ' -f1)
api_ms=$(echo "$api" | cut -d' ' -f2 | awk '{printf "%d", $1 * 1000}')
lp_code=$(echo "$landing" | cut -d' ' -f1)
lp_ms=$(echo "$landing" | cut -d' ' -f2 | awk '{printf "%d", $1 * 1000}')

echo "$jetzt $api_code $api_ms $lp_code $lp_ms" >> "$ziel"

# Aelter als 400 Tage wird nicht gebraucht: eine Zusage bezieht sich auf einen
# Monat, und ein Jahr Rueckschau reicht fuer jede Nachfrage.
find "$ABLAGE" -name '*.log' -mtime +400 -delete 2>/dev/null || true
