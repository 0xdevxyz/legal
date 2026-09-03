#!/bin/bash
#
# Auswertung der Early-Access-Kampagne.
#
# Die eine Frage, die der Anzeigentest beantworten soll, lautet: welche Anzeige
# bringt BESTAETIGTE Anmeldungen. Nicht Klicks, nicht Formulareingaben -
# bestaetigte. Erst der Klick in der Double-Opt-In-Mail vergibt eine Platznummer,
# und nur wer eine Platznummer hat, zaehlt gegen die beworbenen 100 Plaetze.
#
# Warum als Skript und nicht als Abfrage im Kopf: eine Kampagne, deren Auswertung
# man jedes Mal neu zusammensetzt, wird unterschiedlich ausgewertet.
#
# Aufruf:  ./scripts/kampagnen_auswertung.sh
#          ./scripts/kampagnen_auswertung.sh --seit 2026-09-05
set -euo pipefail

SEIT="1970-01-01"
if [ "${1:-}" = "--seit" ] && [ -n "${2:-}" ]; then SEIT="$2"; fi

DB_USER="${POSTGRES_USER:-complyo_user}"
DB_NAME="${POSTGRES_DB:-complyo_db}"
PSQL="docker exec complyo-postgres psql -U $DB_USER -d $DB_NAME"

echo "== Early-Access-Kampagne, Anmeldungen ab $SEIT =="
echo

echo "-- Je Herkunft: eingetragen, bestaetigt, Bestaetigungsquote --"
$PSQL -c "
SELECT
    COALESCE(campaign, '(ohne)')     AS kampagne,
    COALESCE(utm_source, '(ohne)')   AS quelle,
    COALESCE(utm_content, '(ohne)')  AS anzeige,
    count(*)                         AS eingetragen,
    count(confirmed_at)              AS bestaetigt,
    count(platz_nr)                  AS mit_platz,
    CASE WHEN count(*) > 0
         THEN round(100.0 * count(confirmed_at) / count(*), 1)
         ELSE 0 END                  AS quote_prozent
FROM waitlist_leads
WHERE created_at >= '$SEIT'
GROUP BY 1, 2, 3
ORDER BY bestaetigt DESC, eingetragen DESC;
"

echo "-- Platzvergabe: deckt die Zusage 'nur 100 Plaetze'? --"
# Ist sie nicht gedeckt, ist die Werbeaussage nach Paragraph 5 UWG irrefuehrend.
$PSQL -c "
SELECT count(platz_nr)            AS vergebene_plaetze,
       100 - count(platz_nr)      AS noch_frei,
       max(platz_nr)              AS hoechste_nummer,
       count(*) FILTER (WHERE platz_nr IS NULL AND confirmed_at IS NOT NULL)
                                  AS bestaetigt_ohne_platz
FROM waitlist_leads;
"

echo "-- Zugesagtes Angebot: was wurde wem versprochen --"
$PSQL -c "
SELECT COALESCE(angebot, '(ohne)') AS angebot,
       count(*)                    AS eintraege,
       count(platz_nr)             AS mit_platz
FROM waitlist_leads
WHERE created_at >= '$SEIT'
GROUP BY 1 ORDER BY eintraege DESC;
"

echo "-- Haengengebliebene: eingetragen, nie bestaetigt, Frist abgelaufen --"
# Diese Zeilen sind kein Erfolg und duerfen nicht als Interessenten gezaehlt
# werden. Haeufen sie sich, stimmt etwas mit der Zustellung nicht.
$PSQL -c "
SELECT count(*) AS abgelaufen_unbestaetigt
FROM waitlist_leads
WHERE confirmed_at IS NULL
  AND confirm_token_expires_at IS NOT NULL
  AND confirm_token_expires_at < NOW();
"

echo "-- Landepfad: von welcher Seite kamen die Bestaetigten --"
$PSQL -c "
SELECT COALESCE(landing_path, '(ohne)') AS landepfad,
       count(*)            AS eingetragen,
       count(confirmed_at) AS bestaetigt
FROM waitlist_leads
WHERE created_at >= '$SEIT'
GROUP BY 1 ORDER BY bestaetigt DESC;
"
