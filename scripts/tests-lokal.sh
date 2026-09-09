#!/usr/bin/env bash
#
# Der lokale Testaufruf fuer das Backend.
#
# Warum ein Skript und kein Satz in einer Dokumentation: der Aufruf stand
# bisher in zwei Docstrings, und beide waren unvollstaendig. Wer stattdessen
#     docker exec complyo-backend python3 -m pytest tests/
# benutzt, testet den ins Image gebackenen Stand statt des Arbeitsbaums und
# bekommt Fehlschlaege, die es im Repo gar nicht gibt.
#
# Gemountet wird das GANZE Repo, nicht nur backend/. Mehrere Tests lesen
# Dateien oberhalb von backend/: scripts/datensicherung.sh, dashboard-react/,
# landing-react/. Fehlen die, faellt test_datensicherung.py mit neun
# Fehlschlaegen um, und 23 weitere Tests ueberspringen stillschweigend. Ein
# uebersprungener Test bewacht nichts.
#
# Aufruf:
#     scripts/tests-lokal.sh                        # ganze Suite
#     scripts/tests-lokal.sh tests/test_waitlist.py # eine Datei
#
set -eu

WURZEL="$(cd "$(dirname "$0")/.." && pwd)"

if [ "$#" -eq 0 ]; then
    set -- tests/ -q
fi

# -p no:cacheprovider: pytest darf sonst .pytest_cache in den Arbeitsbaum
# schreiben, was je nach Nutzerkennung im Container an den Rechten scheitert.
exec docker run --rm \
    -v "$WURZEL:/repo" \
    -v "$WURZEL/knowledge:/data/knowledge:ro" \
    -w /repo/backend \
    legal-backend \
    python -m pytest -p no:cacheprovider "$@"
