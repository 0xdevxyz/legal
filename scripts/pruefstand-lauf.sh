#!/bin/sh
# Pruefstand-Lauf: den Scanner ueber den Bestand echter Seiten schicken und mit
# dem vorigen Lauf vergleichen.
#
# Warum ein Skript: der Pruefstand lag bisher als Einzelaufruf in zwei
# Docstrings, die Ergebnisse unter /tmp (dort ging der Lauf vom 09.09. bis auf
# eine Datei verloren) und die Seitenliste in niemandes Kopf. Ein Vergleich
# braucht aber zwei Laeufe, und der zweite nur dann Aussagekraft, wenn er unter
# denselben Bedingungen entsteht.
#
# Gemessen wird das AUSGELIEFERTE Image (was ein Kunde heute bekommt), nicht der
# Arbeitsbaum: der geteilte Checkout steht oft auf einem fremden Branch.
# Soll Branch-Code gemessen werden: PRUEFSTAND_CODE=/home/clawd/saas/legal/backend
# mountet ihn nach /src (nicht /app, sonst verdeckt der Mount die Playwright-
# Browser unter /app/.cache und der Scan faellt still auf Heuristik zurueck).
#
# Die Seitenliste gehoert NICHT ins Repo: es sind die Domains der Hosting-Kunden.
# Sie liegt unter $PRUEFSTAND_DIR/sites.txt, eine URL oder Domain je Zeile,
# Kommentarzeilen mit #.
#
# Datenbank, Redis und KI-Zugang kommen aus dem LAUFENDEN Backend-Container
# (docker inspect), nicht aus der .env: das Passwort steht dort in einfachen
# Quotes, die `docker run --env-file` nicht entfernt (Falle vom SMTP-Livegang
# am 11.08.). Die Werte laufen ueber eine Pipe und beruehren keine Platte;
# mehrzeilige Werte werden dabei ausgelassen (siehe unten).
#
# Crontab (sudo), sonntags 03:30, nach dem Wochenend-Deploy-Fenster:
#   30 3 * * 0 /home/clawd/saas/legal/scripts/pruefstand-lauf.sh >> /var/log/complyo-pruefstand.log 2>&1
#
# Exitcode 0: Lauf sauber (oder erster Lauf, nichts zu vergleichen).
# Exitcode 1: gegenueber dem vorigen Lauf neue Verdachtsart oder Score-Absturz.
# Exitcode 2: Voraussetzung fehlt (Liste, Container, Image).
set -u

BASIS="${PRUEFSTAND_DIR:-/home/clawd/pruefstand}"
LISTE="${PRUEFSTAND_LISTE:-$BASIS/sites.txt}"
PARALLEL="${PRUEFSTAND_PARALLEL:-2}"
IMAGE="${PRUEFSTAND_IMAGE:-legal-backend}"
CONTAINER="${PRUEFSTAND_CONTAINER:-complyo-backend}"
SPEICHER="${PRUEFSTAND_SPEICHER:-3g}"
HIER="$(cd "$(dirname "$0")" && pwd)"

[ -r "$LISTE" ] || { echo "Seitenliste fehlt oder ist nicht lesbar: $LISTE" >&2; exit 2; }
docker inspect "$CONTAINER" >/dev/null 2>&1 \
  || { echo "Container $CONTAINER laeuft nicht, keine Umgebung zu uebernehmen" >&2; exit 2; }

STAND="${PRUEFSTAND_STAND:-$(date +%Y-%m-%d-%H%M%S)}"
OUT="$BASIS/laeufe/$STAND"
mkdir -p "$OUT" || exit 2

# Der vorige Lauf, bevor der neue angelegt ist. Nur Laeufe mit Ergebnisdatei:
# ein abgebrochener Lauf ist kein Vergleichswert.
VORHER=""
for d in "$BASIS"/laeufe/*/; do
  d="${d%/}"
  [ "$d" = "$OUT" ] && continue
  [ -s "$d/pruefstand.json" ] && VORHER="$d"
done

CODE_MOUNT=""
ARBEITSVERZEICHNIS="/app"
if [ -n "${PRUEFSTAND_CODE:-}" ]; then
  CODE_MOUNT="-v $PRUEFSTAND_CODE:/src:ro"
  ARBEITSVERZEICHNIS="/src"
fi

echo "Pruefstand $STAND: $(grep -cv '^[[:space:]]*\(#\|$\)' "$LISTE") Seiten, Image $IMAGE, ${PARALLEL} parallel"

# Mehrzeilige Werte (der Container traegt einen privaten Schluessel) lehnt
# `--env-file` ab: "variable '-----END PRIVATE KEY-----' contains whitespaces".
# Der Scanner braucht sie nicht, deshalb filtert der Python-Einzeiler jede
# Variable heraus, deren Wert einen Zeilenumbruch enthaelt. Das gilt zugleich als
# Mindestweitergabe: ein Schluessel, den niemand braucht, gehoert nicht in einen
# Scan-Container, der fremde Seiten laedt.
# shellcheck disable=SC2086
docker inspect -f '{{json .Config.Env}}' "$CONTAINER" \
  | python3 -c 'import json, sys; [print(e) for e in json.load(sys.stdin) if "\n" not in e]' \
  | docker run --rm --user root \
      --network legal_complyo-network \
      --env-file /dev/stdin \
      --memory "$SPEICHER" --shm-size 1g \
      -v "$OUT:/out" \
      -v "$LISTE:/liste.txt:ro" \
      $CODE_MOUNT \
      -w "$ARBEITSVERZEICHNIS" \
      "$IMAGE" python tools/pruefstand.py \
        --datei /liste.txt --out /out --parallel "$PARALLEL" \
  | tee "$OUT/lauf.txt"

if [ ! -s "$OUT/pruefstand.json" ]; then
  echo "Lauf ohne Ergebnisdatei: $OUT" >&2
  exit 2
fi

ln -sfn "$OUT" "$BASIS/letzter"

if [ -z "$VORHER" ]; then
  echo "Erster Lauf, nichts zu vergleichen. Verdachtsliste:"
  python3 "$HIER/../backend/tools/pruefstand_vergleich.py" "$OUT/pruefstand.json" \
    > "$OUT/vergleich.txt" 2>&1
  cat "$OUT/vergleich.txt"
  exit 0
fi

echo "Vergleich mit $VORHER"
python3 "$HIER/../backend/tools/pruefstand_vergleich.py" \
  "$VORHER/pruefstand.json" "$OUT/pruefstand.json" --streng \
  > "$OUT/vergleich.txt" 2>&1
RC=$?
cat "$OUT/vergleich.txt"
exit "$RC"
