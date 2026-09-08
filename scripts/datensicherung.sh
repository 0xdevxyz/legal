#!/bin/bash
# Tägliche Datensicherung der complyo-Datenbank — mit Wiederherstellungsprobe.
#
# Anlass: die Prüfung vom 07.09.2026. Es gab keinen Zeitplan, keinen Timer und
# keine Kopie ausser Haus. Gesichert wurde nur, wenn jemand vor einer Migration
# von Hand einen Abzug zog. Bei 36 MB Datenbankgröße ist das keine Frage von
# Aufwand, sondern eine, die niemand gestellt hat.
#
# **Der Kern ist nicht der Abzug, sondern die Probe.** Eine Sicherung, die nie
# zurückgespielt wurde, ist eine Vermutung. Deshalb wird JEDER Abzug sofort in
# eine Wegwerf-Datenbank eingespielt und Tabelle für Tabelle mit dem Original
# verglichen. Das kostet bei dieser Größe wenige Sekunden und ist der einzige
# Teil, der die Frage "können wir wiederherstellen?" wirklich beantwortet.
#
# Das alte scripts/backup-system.sh (Februar 2026) bleibt liegen, aber es läuft
# nicht mehr: es zeigt auf den Container `shared-postgres-production` und auf
# /opt/projects/saas-project-2/.env. Beides gibt es hier nicht. Ein Skript, das
# beim ersten Lauf scheitert, ist schlechter als keins — es sieht aus wie
# Vorsorge.
#
# Crontab (root):
#   30 2 * * * /home/clawd/saas/legal/scripts/datensicherung.sh >> /var/log/complyo-sicherung.log 2>&1

set -u

DB_CONTAINER="complyo-postgres"
DB_NAME="complyo_db"
DB_USER="complyo_user"
ABLAGE="/home/clawd/backups/taeglich"
MONATSABLAGE="/home/clawd/backups/monatlich"
MARKE="/home/clawd/saas/legal/data/waechter/datensicherung.json"
SPERRE="/var/lock/complyo-sicherung.lock"
TESTDB="complyo_sicherungstest"

# Wie lange was bleibt. Ein Abzug ist rund 11 MB — Platz ist hier nicht das
# knappe Gut, deshalb lieber grosszügig.
TAGE_TAEGLICH=14
TAGE_MONATLICH=190

# Ziel für die Kopie ausser Haus. Solange die Datei fehlt, liegt die Sicherung
# nur auf derselben Maschine wie die Datenbank — was gegen einen Plattenschaden
# nicht hilft. Bewusst als Datei und nicht fest verdrahtet: das Ziel ist eine
# Entscheidung des Betreibers, kein Detail dieses Skripts.
# Inhalt: eine Zeile, z.B.  user@host:/pfad/zu/complyo-sicherungen
ZIELDATEI="/home/clawd/saas/legal/.sicherung-ziel"

zeit() { date -u +"%Y-%m-%d %H:%M:%S"; }
sage() { echo "$(zeit) $*"; }

# Bei jedem Ausstieg eine Marke schreiben. Der Betriebswächter liest sie und
# meldet, wenn sie zu alt ist oder auf Fehlschlag steht. Ohne das wäre eine
# stillschweigend gescheiterte Sicherung genau so unsichtbar wie vorher gar
# keine — der Fehler, den complyo schon dreimal hatte.
ERGEBNIS="unbekannt"
MELDUNG="Lauf nicht abgeschlossen"
DATEI=""
GROESSE=0
GEPRUEFT="nein"
TABELLEN_QUELLE=0
TABELLEN_PROBE=0
AUSSER_HAUS="nicht eingerichtet"

marke_schreiben() {
  mkdir -p "$(dirname "$MARKE")" 2>/dev/null
  cat > "$MARKE" <<ENDE
{
  "zeitpunkt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "ergebnis": "$ERGEBNIS",
  "meldung": "$MELDUNG",
  "datei": "$DATEI",
  "groesse_bytes": $GROESSE,
  "wiederherstellung_geprueft": "$GEPRUEFT",
  "tabellen_quelle": $TABELLEN_QUELLE,
  "tabellen_probe": $TABELLEN_PROBE,
  "ausser_haus": "$AUSSER_HAUS"
}
ENDE
}
trap marke_schreiben EXIT

# Zwei Läufe gleichzeitig würden sich beim Wiederherstellungstest über dieselbe
# Wegwerf-Datenbank in die Quere kommen.
exec 9>"$SPERRE"
if ! flock -n 9; then
  sage "Ein anderer Lauf hält die Sperre — dieser Lauf endet."
  ERGEBNIS="uebersprungen"; MELDUNG="paralleler Lauf"
  exit 0
fi

sage "=== Datensicherung beginnt ==="
mkdir -p "$ABLAGE" "$MONATSABLAGE"

if ! docker inspect "$DB_CONTAINER" >/dev/null 2>&1; then
  ERGEBNIS="fehlgeschlagen"; MELDUNG="Container $DB_CONTAINER nicht gefunden"
  sage "FEHLER: $MELDUNG"; exit 1
fi

# ---------------------------------------------------------------------------
# 1. Abzug
# ---------------------------------------------------------------------------
STEMPEL="$(date -u +%Y%m%d-%H%M)"
DATEI="$ABLAGE/complyo-$STEMPEL.dump"

# -Fc: eigenes Format, komprimiert, erlaubt beim Zurückspielen die Auswahl
# einzelner Tabellen. Ein reiner SQL-Text wäre grösser und nur ganz oder gar
# nicht einspielbar.
if ! docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc \
     > "$DATEI" 2>/tmp/sicherung-fehler.txt; then
  ERGEBNIS="fehlgeschlagen"
  MELDUNG="pg_dump gescheitert: $(head -c 200 /tmp/sicherung-fehler.txt | tr '\n' ' ')"
  sage "FEHLER: $MELDUNG"; rm -f "$DATEI"; exit 1
fi

GROESSE=$(stat -c %s "$DATEI" 2>/dev/null || echo 0)
if [ "$GROESSE" -lt 100000 ]; then
  ERGEBNIS="fehlgeschlagen"
  MELDUNG="Abzug nur $GROESSE Bytes gross — das kann nicht die Datenbank sein"
  sage "FEHLER: $MELDUNG"; exit 1
fi
sage "Abzug geschrieben: $DATEI ($((GROESSE / 1024)) KiB)"

# ---------------------------------------------------------------------------
# 2. Lesbar? (fängt Abbruch und Beschädigung)
# ---------------------------------------------------------------------------
if ! docker exec -i "$DB_CONTAINER" pg_restore -l < "$DATEI" > /tmp/sicherung-liste.txt 2>&1; then
  ERGEBNIS="fehlgeschlagen"
  MELDUNG="Abzug ist nicht lesbar (pg_restore -l scheitert)"
  sage "FEHLER: $MELDUNG"; exit 1
fi
sage "Inhaltsverzeichnis lesbar: $(grep -c '^[0-9]' /tmp/sicherung-liste.txt) Einträge"

# ---------------------------------------------------------------------------
# 3. Wiederherstellungsprobe — der eigentliche Zweck
# ---------------------------------------------------------------------------
# Eine Sicherung, die nie zurückgespielt wurde, ist eine Vermutung. Hier wird
# sie in eine Wegwerf-Datenbank eingespielt und Tabelle für Tabelle mit dem
# Original verglichen.
psql_lauf() { docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$1" -tAc "$2" 2>/dev/null; }

docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres \
  -c "DROP DATABASE IF EXISTS $TESTDB;" >/dev/null 2>&1
if ! docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres \
     -c "CREATE DATABASE $TESTDB;" >/dev/null 2>&1; then
  ERGEBNIS="fehlgeschlagen"
  MELDUNG="Wegwerf-Datenbank $TESTDB liess sich nicht anlegen"
  sage "FEHLER: $MELDUNG"; exit 1
fi

# --no-owner/--no-privileges: Rollen und Rechte sind für die Probe unerheblich
# und würden nur Rauschen erzeugen. Der Rückgabewert von pg_restore wird
# bewusst NICHT als Urteil genommen — er meldet auch Kleinigkeiten wie fehlende
# Erweiterungen. Was zählt, ist der Zeilenvergleich unten.
docker exec -i "$DB_CONTAINER" pg_restore -U "$DB_USER" -d "$TESTDB" \
  --no-owner --no-privileges < "$DATEI" > /tmp/sicherung-restore.txt 2>&1

VERGLEICH="SELECT relname || ':' || n_live_tup FROM pg_stat_user_tables ORDER BY relname;"
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$TESTDB" -c "ANALYZE;" >/dev/null 2>&1

QUELLE=$(psql_lauf "$DB_NAME" "$VERGLEICH")
PROBE=$(psql_lauf "$TESTDB" "$VERGLEICH")
TABELLEN_QUELLE=$(echo "$QUELLE" | grep -c ':')
TABELLEN_PROBE=$(echo "$PROBE"  | grep -c ':')

FEHLEND=""
ZU_LEER=""
while IFS=: read -r tab anzahl; do
  [ -z "$tab" ] && continue
  p=$(echo "$PROBE" | grep "^$tab:" | cut -d: -f2)
  if [ -z "$p" ]; then
    FEHLEND="$FEHLEND $tab"
  elif [ "${anzahl:-0}" -gt 0 ] && [ "${p:-0}" -eq 0 ]; then
    # Der harte Fall: die Tabelle ist da, aber leer, obwohl das Original
    # Zeilen hat. Genau so sieht eine Sicherung aus, die nur das Schema
    # enthaelt — und genau so eine haelt man fuer eine gueltige.
    ZU_LEER="$ZU_LEER $tab($anzahl)"
  fi
done <<< "$QUELLE"

docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres \
  -c "DROP DATABASE IF EXISTS $TESTDB;" >/dev/null 2>&1

if [ -n "$FEHLEND" ] || [ -n "$ZU_LEER" ]; then
  ERGEBNIS="fehlgeschlagen"
  MELDUNG="Probe misslungen —${FEHLEND:+ fehlende Tabellen:$FEHLEND}${ZU_LEER:+ leer geblieben:$ZU_LEER}"
  sage "FEHLER: $MELDUNG"; exit 1
fi

GEPRUEFT="ja"
sage "Wiederherstellung geprüft: $TABELLEN_PROBE von $TABELLEN_QUELLE Tabellen, keine leer geblieben"

# ---------------------------------------------------------------------------
# 4. Monatsexemplar
# ---------------------------------------------------------------------------
if [ "$(date -u +%d)" = "01" ]; then
  cp "$DATEI" "$MONATSABLAGE/" && sage "Monatsexemplar abgelegt"
fi

# ---------------------------------------------------------------------------
# 5. Kopie ausser Haus
# ---------------------------------------------------------------------------
if [ -s "$ZIELDATEI" ]; then
  ZIEL="$(head -1 "$ZIELDATEI" | tr -d '\r\n')"
  if scp -q -o BatchMode=yes -o ConnectTimeout=20 "$DATEI" "$ZIEL/" 2>/tmp/sicherung-scp.txt; then
    AUSSER_HAUS="uebertragen nach ${ZIEL%%:*}"
    sage "Kopie ausser Haus: $ZIEL"
  else
    AUSSER_HAUS="FEHLGESCHLAGEN"
    sage "WARNUNG: Kopie ausser Haus gescheitert: $(head -c 160 /tmp/sicherung-scp.txt | tr '\n' ' ')"
  fi
else
  # Kein Alarm: dass es noch kein Ziel gibt, ist eine offene Entscheidung und
  # kein Ausfall. Sichtbar bleibt es trotzdem, in der Marke und im Log.
  AUSSER_HAUS="nicht eingerichtet"
  sage "Hinweis: kein Ziel ausser Haus ($ZIELDATEI fehlt) — die Sicherung liegt auf derselben Maschine wie die Datenbank"
fi

# ---------------------------------------------------------------------------
# 6. Aufräumen
# ---------------------------------------------------------------------------
ALT=$(find "$ABLAGE" -name 'complyo-*.dump' -mtime "+$TAGE_TAEGLICH" -print -delete | wc -l)
ALT_M=$(find "$MONATSABLAGE" -name 'complyo-*.dump' -mtime "+$TAGE_MONATLICH" -print -delete | wc -l)
sage "Aufgeräumt: $ALT täglich, $ALT_M monatlich entfernt"
sage "Bestand: $(ls -1 "$ABLAGE"/*.dump 2>/dev/null | wc -l) täglich, $(ls -1 "$MONATSABLAGE"/*.dump 2>/dev/null | wc -l) monatlich, zusammen $(du -sh /home/clawd/backups 2>/dev/null | cut -f1)"

ERGEBNIS="erfolgreich"
MELDUNG="Abzug geschrieben und Wiederherstellung geprüft"
sage "=== Datensicherung fertig ==="
exit 0
