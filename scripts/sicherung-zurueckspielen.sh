#!/bin/bash
# Eine verschlüsselte Sicherung zurückspielen.
#
# Seit dem 10.09.2026 liegen die Abzüge verschlüsselt (AES-256-CBC, PBKDF2).
# Damit ist der Rückweg nicht mehr selbsterklärend — und eine Sicherung, deren
# Rückweg im Ernstfall erst gesucht werden muss, ist im Ernstfall keine.
# Deshalb dieses Skript.
#
#   ./sicherung-zurueckspielen.sh <abzug.dump.enc> [zieldatenbank]
#
# Ohne Zieldatenbank wird in `complyo_wiederherstellung` eingespielt, NICHT in
# die laufende Datenbank. Das ist Absicht: der häufigste Grund, eine Sicherung
# anzufassen, ist nicht der Totalverlust, sondern die Frage "was stand da
# gestern?". Wer wirklich die Produktionsdatenbank überschreiben will, muss
# ihren Namen hinschreiben und die Rückfrage beantworten.

set -eu

DB_CONTAINER="complyo-postgres"
DB_USER="complyo_user"
DB_NAME="complyo_db"
SCHLUESSELDATEI="${SCHLUESSELDATEI:-/home/clawd/saas/legal/.sicherung-schluessel}"

ABZUG="${1:-}"
ZIEL="${2:-complyo_wiederherstellung}"

if [ -z "$ABZUG" ]; then
  echo "Aufruf: $0 <abzug.dump.enc> [zieldatenbank]"
  echo
  echo "Vorhandene Sicherungen:"
  ls -1sh /home/clawd/backups/taeglich/*.dump.enc 2>/dev/null | tail -14
  ls -1sh /home/clawd/backups/monatlich/*.dump.enc 2>/dev/null | tail -6
  exit 1
fi

[ -s "$ABZUG" ] || { echo "FEHLER: $ABZUG nicht gefunden"; exit 1; }
[ -s "$SCHLUESSELDATEI" ] || { echo "FEHLER: Schlüsseldatei $SCHLUESSELDATEI fehlt"; exit 1; }

if [ "$ZIEL" = "$DB_NAME" ]; then
  echo "ACHTUNG: Ziel ist die LAUFENDE Datenbank $DB_NAME."
  echo "Der vorhandene Inhalt wird dabei überschrieben."
  printf 'Zum Fortfahren den Namen der Datenbank eintippen: '
  read -r bestaetigung
  [ "$bestaetigung" = "$DB_NAME" ] || { echo "Abgebrochen."; exit 1; }
fi

KLARTEXT="$(mktemp /tmp/complyo-wiederherstellung.XXXXXX)"
chmod 600 "$KLARTEXT"
# Auch bei Abbruch bleibt kein entschlüsselter Abzug liegen.
trap 'shred -u "$KLARTEXT" 2>/dev/null || rm -f "$KLARTEXT"' EXIT

echo "Entschlüsseln …"
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 \
  -pass "file:$SCHLUESSELDATEI" -in "$ABZUG" -out "$KLARTEXT"

# Kein Vertrauen auf den Rückgabewert allein: openssl meldet bei falschem
# Schlüssel je nach Version auch mal Erfolg und liefert Unsinn.
docker exec -i "$DB_CONTAINER" pg_restore -l < "$KLARTEXT" > /dev/null 2>&1 \
  || { echo "FEHLER: Entschlüsseltes Ergebnis ist kein pg_dump — falscher Schlüssel?"; exit 1; }

echo "Zieldatenbank $ZIEL vorbereiten …"
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres \
  -c "DROP DATABASE IF EXISTS $ZIEL;" >/dev/null
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres \
  -c "CREATE DATABASE $ZIEL;" >/dev/null

echo "Einspielen …"
docker exec -i "$DB_CONTAINER" pg_restore -U "$DB_USER" -d "$ZIEL" \
  --no-owner --no-privileges < "$KLARTEXT" 2>&1 | tail -5 || true

docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$ZIEL" -c "ANALYZE;" >/dev/null 2>&1
ANZAHL=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$ZIEL" -tAc \
  "SELECT count(*) FROM pg_stat_user_tables WHERE n_live_tup > 0")

echo
echo "Fertig: $ZIEL, $ANZAHL Tabellen mit Inhalt."
echo "Ansehen mit: docker exec -it $DB_CONTAINER psql -U $DB_USER -d $ZIEL"
