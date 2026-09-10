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
# Inhalt: erste Zeile das Ziel, z.B.  user@host:/pfad/zu/complyo-sicherungen
# Danach optional, je Zeile:  PORT=58796  und  SCHLUESSEL=/root/.ssh/eigener_key
#
# Eingerichtet am 11.09.2026 (Entscheidung Daniel, Nachtschicht): Ziel ist
# ionos-web, Nutzer `complyo-sicherung`, dessen Schluessel per rrsync auf
# *Schreiben in ein Verzeichnis* beschraenkt ist. Wer diesen Server
# uebernimmt, bekommt damit weder Lesezugriff auf die abgelegten Abzuege noch
# eine Shell auf der Gegenseite. Gelesen wird die Kopie nur von Hand, mit dem
# Schluessel, der NICHT hier liegt. Deshalb rsync statt scp: rrsync versteht
# nur das rsync-Protokoll, ein scp-Aufruf wuerde abgewiesen.
ZIELDATEI="/home/clawd/saas/legal/.sicherung-ziel"

# Schlüsseldatei für die Verschlüsselung des Abzugs (Prüfung 10.09.2026).
#
# Der Abzug enthält den gesamten Kundenbestand: E-Mail-Adressen, bcrypt-Hashes,
# 1.151 Einwilligungsprotokolle, verschlüsselte Git-Token. Bis heute lag er als
# unverschlüsselte Datei neben der Datenbank, und die Kopie ausser Haus hätte
# ihn genau so auf eine fremde Maschine getragen. Eine Sicherung, die man nicht
# aus der Hand geben kann, ist als Sicherung gegen Serververlust wertlos —
# und ohne Verschlüsselung darf man sie nicht aus der Hand geben.
#
# Verfahren: AES-256-CBC über openssl mit PBKDF2 und 600.000 Runden. Kein gpg,
# weil dessen Schlüsselbund auf einem unbeaufsichtigten Server mehr bewegliche
# Teile hat als Nutzen bringt; openssl ist ohnehin installiert.
#
# Die Schlüsseldatei gehört NICHT auf diese Maschine allein. Wer nur den Server
# verliert, verliert sonst mit ihm den Schlüssel zu allen Kopien ausser Haus.
# Anlegen mit:
#   openssl rand -base64 48 > /home/clawd/saas/legal/.sicherung-schluessel
#   chmod 600 /home/clawd/saas/legal/.sicherung-schluessel
# und danach eine Kopie an einen Ort, der nicht dieser Server ist.
SCHLUESSELDATEI="/home/clawd/saas/legal/.sicherung-schluessel"

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
VERSCHLUESSELT="nein"
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
  "verschluesselt": "$VERSCHLUESSELT",
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
# ROHDATEI ist der Klartext-Abzug. Er existiert nur, solange die Probe läuft,
# und wird danach überschrieben. DATEI ist das, was liegen bleibt.
ROHDATEI="$ABLAGE/.complyo-$STEMPEL.dump.roh"
DATEI="$ABLAGE/complyo-$STEMPEL.dump.enc"

# Auch bei Abbruch darf kein Klartext-Abzug zurückbleiben.
aufraeumen_roh() { [ -n "${ROHDATEI:-}" ] && [ -f "$ROHDATEI" ] && shred -u "$ROHDATEI" 2>/dev/null || rm -f "$ROHDATEI" 2>/dev/null; }
trap 'aufraeumen_roh; marke_schreiben' EXIT

if [ ! -s "$SCHLUESSELDATEI" ]; then
  ERGEBNIS="fehlgeschlagen"
  MELDUNG="Schlüsseldatei $SCHLUESSELDATEI fehlt — ohne sie würde der Abzug im Klartext liegen"
  sage "FEHLER: $MELDUNG"
  sage "Anlegen mit: openssl rand -base64 48 > $SCHLUESSELDATEI && chmod 600 $SCHLUESSELDATEI"
  sage "Danach eine Kopie des Schlüssels an einen Ort ausserhalb dieses Servers."
  exit 1
fi
# Ein weltlesbarer Schlüssel ist kein Schlüssel.
RECHTE=$(stat -c %a "$SCHLUESSELDATEI")
if [ "$RECHTE" != "600" ] && [ "$RECHTE" != "400" ]; then
  ERGEBNIS="fehlgeschlagen"
  MELDUNG="Schlüsseldatei hat Rechte $RECHTE statt 600"
  sage "FEHLER: $MELDUNG"; exit 1
fi

# -Fc: eigenes Format, komprimiert, erlaubt beim Zurückspielen die Auswahl
# einzelner Tabellen. Ein reiner SQL-Text wäre grösser und nur ganz oder gar
# nicht einspielbar.
umask 077
if ! docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc \
     > "$ROHDATEI" 2>/tmp/sicherung-fehler.txt; then
  ERGEBNIS="fehlgeschlagen"
  MELDUNG="pg_dump gescheitert: $(head -c 200 /tmp/sicherung-fehler.txt | tr '\n' ' ')"
  sage "FEHLER: $MELDUNG"; exit 1
fi

GROESSE=$(stat -c %s "$ROHDATEI" 2>/dev/null || echo 0)
if [ "$GROESSE" -lt 100000 ]; then
  ERGEBNIS="fehlgeschlagen"
  MELDUNG="Abzug nur $GROESSE Bytes gross — das kann nicht die Datenbank sein"
  sage "FEHLER: $MELDUNG"; exit 1
fi
sage "Abzug geschrieben: $((GROESSE / 1024)) KiB"

# ---------------------------------------------------------------------------
# 2. Lesbar? (fängt Abbruch und Beschädigung)
# ---------------------------------------------------------------------------
if ! docker exec -i "$DB_CONTAINER" pg_restore -l < "$ROHDATEI" > /tmp/sicherung-liste.txt 2>&1; then
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
  --no-owner --no-privileges < "$ROHDATEI" > /tmp/sicherung-restore.txt 2>&1

# Exakte Zeilenzahlen, nicht n_live_tup. Der Schaetzwert aus pg_stat_user_tables
# hinkt bei kleinen Tabellen dem Bestand hinterher, bis Autovacuum vorbeikommt:
# am 10.09.2026 meldete er fuer email_bestaetigung und passwort_reset je eine
# Zeile, die es laengst nicht mehr gab (Testkonto geloescht, Zeilen per CASCADE
# mit). Die Probe verglich Schaetzung gegen Schaetzung, sah "1 gegen 0" und
# erklaerte einen korrekten Abzug fuer misslungen. Ein Fehlalarm der Sicherung
# ist gefaehrlich, weil er die echten unglaubwuerdig macht. query_to_xml ist
# der uebliche Weg, count(*) fuer jede Tabelle in EINER Abfrage zu bekommen;
# bei 11 MB Datenbank kostet das Sekundenbruchteile.
VERGLEICH="SELECT relname || ':' || (xpath('/row/c/text()', query_to_xml(format('SELECT count(*) AS c FROM %I.%I', schemaname, relname), false, true, '')))[1]::text FROM pg_stat_user_tables ORDER BY relname;"

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
# 3b. Verschlüsseln — und die Entschlüsselung gleich mitprüfen
# ---------------------------------------------------------------------------
# Dieselbe Haltung wie bei der Wiederherstellungsprobe: eine Verschlüsselung,
# die nie zurückgerechnet wurde, ist eine Vermutung. Verglichen wird über die
# Prüfsumme gegen genau den Abzug, dessen Wiederherstellung eben belegt wurde.
# Stimmen die Summen, gilt die Probe von oben auch für die Datei, die liegen
# bleibt — sonst prüfte man das eine und verwahrte das andere.
PRUEFSUMME_ROH=$(sha256sum "$ROHDATEI" | cut -d' ' -f1)

if ! openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -salt \
     -pass "file:$SCHLUESSELDATEI" -in "$ROHDATEI" -out "$DATEI" 2>/tmp/sicherung-krypto.txt; then
  ERGEBNIS="fehlgeschlagen"
  MELDUNG="Verschlüsselung gescheitert: $(head -c 160 /tmp/sicherung-krypto.txt | tr '\n' ' ')"
  sage "FEHLER: $MELDUNG"; rm -f "$DATEI"; exit 1
fi
chmod 600 "$DATEI"

PRUEFSUMME_ZURUECK=$(openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 \
  -pass "file:$SCHLUESSELDATEI" -in "$DATEI" 2>/tmp/sicherung-krypto.txt | sha256sum | cut -d' ' -f1)

if [ "$PRUEFSUMME_ROH" != "$PRUEFSUMME_ZURUECK" ]; then
  ERGEBNIS="fehlgeschlagen"
  MELDUNG="Entschlüsselung ergibt nicht den geprüften Abzug — die Sicherung wäre nicht lesbar"
  sage "FEHLER: $MELDUNG"; rm -f "$DATEI"; exit 1
fi

# Klartext weg, und zwar sofort. Ab hier existiert der Bestand auf dieser
# Platte nur noch verschlüsselt.
aufraeumen_roh
GROESSE=$(stat -c %s "$DATEI" 2>/dev/null || echo 0)
VERSCHLUESSELT="ja"
sage "Verschlüsselt und zurückgerechnet: $DATEI ($((GROESSE / 1024)) KiB), Prüfsummen gleich"

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
  ZIEL_PORT="$(grep -E '^PORT=' "$ZIELDATEI" | head -1 | cut -d= -f2 | tr -d '\r\n')"
  ZIEL_SCHLUESSEL="$(grep -E '^SCHLUESSEL=' "$ZIELDATEI" | head -1 | cut -d= -f2- | tr -d '\r\n')"
  SSH_BEFEHL="ssh -o BatchMode=yes -o ConnectTimeout=20"
  [ -n "$ZIEL_PORT" ] && SSH_BEFEHL="$SSH_BEFEHL -p $ZIEL_PORT"
  [ -n "$ZIEL_SCHLUESSEL" ] && SSH_BEFEHL="$SSH_BEFEHL -i $ZIEL_SCHLUESSEL"
  # --ignore-existing: ein Abzug wird nie ueberschrieben. Wer den Server
  # uebernimmt und die Sicherung manipuliert, kann damit die bereits
  # uebertragenen Exemplare nicht nachtraeglich ersetzen.
  if rsync -q --ignore-existing -e "$SSH_BEFEHL" "$DATEI" "$ZIEL/" 2>/tmp/sicherung-rsync.txt; then
    AUSSER_HAUS="uebertragen nach ${ZIEL%%:*}"
    sage "Kopie ausser Haus: $ZIEL"
  else
    AUSSER_HAUS="FEHLGESCHLAGEN"
    sage "WARNUNG: Kopie ausser Haus gescheitert: $(head -c 160 /tmp/sicherung-rsync.txt | tr '\n' ' ')"
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
ALT=$(find "$ABLAGE" -name 'complyo-*.dump*' -mtime "+$TAGE_TAEGLICH" -print -delete | wc -l)
ALT_M=$(find "$MONATSABLAGE" -name 'complyo-*.dump*' -mtime "+$TAGE_MONATLICH" -print -delete | wc -l)
sage "Aufgeräumt: $ALT täglich, $ALT_M monatlich entfernt"
sage "Bestand: $(ls -1 "$ABLAGE"/*.dump.enc 2>/dev/null | wc -l) täglich, $(ls -1 "$MONATSABLAGE"/*.dump.enc 2>/dev/null | wc -l) monatlich, zusammen $(du -sh /home/clawd/backups 2>/dev/null | cut -f1)"

ERGEBNIS="erfolgreich"
MELDUNG="Abzug geschrieben und Wiederherstellung geprüft"
sage "=== Datensicherung fertig ==="
exit 0
