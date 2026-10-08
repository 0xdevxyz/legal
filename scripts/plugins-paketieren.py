#!/usr/bin/env python3
"""
Baut die Plugin-Pakete fuer WordPress und Joomla aus den Quellordnern und legt
sie unter backend/plugins/ ab, wo das Backend sie ausliefert
(GET /api/cookie-compliance/plugin/{wordpress|joomla}).

Warum ein Skript: die frueher eingecheckten Zips neben den Quellordnern waren
veraltet (WordPress: zwei Dateien anders, .pot fehlte; Joomla: complyo.php
anders). Niemand hat es gemerkt, weil nichts sie auslieferte und nichts sie
pruefte. Jetzt prueft tests/test_grundsystem_einrichtung.py, dass Zip und
Ordner uebereinstimmen; wer das Plugin aendert, laesst dieses Skript laufen.

Die Zips sind reproduzierbar (feste Zeitstempel, sortierte Dateien), damit ein
Lauf ohne Quelleaenderung keinen Diff erzeugt.

Aufruf aus dem Repo:
    python3 scripts/plugins-paketieren.py
"""

import os
import sys
import zipfile

WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ZIEL = os.path.join(WURZEL, "backend", "plugins")

# (Zip-Name, Quellordner relativ zur Wurzel, Ordnername im Zip)
PAKETE = [
    ("complyo-compliance.zip", "wordpress-plugin/complyo-compliance", "complyo-compliance"),
    ("plg_system_complyo.zip", "joomla-plugin/plg_system_complyo", "plg_system_complyo"),
]

FESTER_ZEITSTEMPEL = (2026, 1, 1, 0, 0, 0)


def dateien_im_ordner(ordner: str):
    """Alle Dateien unterhalb von ordner, relativ, sortiert; ohne Zips und Build-Reste."""
    ergebnis = []
    for wurzel, verzeichnisse, dateien in os.walk(ordner):
        verzeichnisse[:] = sorted(d for d in verzeichnisse if not d.startswith("."))
        for name in sorted(dateien):
            if name.startswith(".") or name.endswith((".zip", ".pyc")):
                continue
            voll = os.path.join(wurzel, name)
            ergebnis.append(os.path.relpath(voll, ordner))
    return ergebnis


def paketieren(zip_name: str, quelle_rel: str, praefix: str) -> str:
    quelle = os.path.join(WURZEL, quelle_rel)
    if not os.path.isdir(quelle):
        sys.exit(f"Quellordner fehlt: {quelle}")
    os.makedirs(ZIEL, exist_ok=True)
    ziel = os.path.join(ZIEL, zip_name)
    with zipfile.ZipFile(ziel, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in dateien_im_ordner(quelle):
            info = zipfile.ZipInfo(f"{praefix}/{rel.replace(os.sep, '/')}", date_time=FESTER_ZEITSTEMPEL)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(os.path.join(quelle, rel), "rb") as fh:
                zf.writestr(info, fh.read())
    return ziel


def main() -> None:
    for zip_name, quelle_rel, praefix in PAKETE:
        ziel = paketieren(zip_name, quelle_rel, praefix)
        anzahl = len(zipfile.ZipFile(ziel).namelist())
        print(f"{os.path.relpath(ziel, WURZEL)}: {anzahl} Dateien aus {quelle_rel}")


if __name__ == "__main__":
    main()
