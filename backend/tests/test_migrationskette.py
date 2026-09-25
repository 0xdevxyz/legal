"""Die Migrationskette, bevor sie die Datenbank anfasst.

Anlass (25.09.2026): Migration 0035 hiess zuerst
"0035_scan_kennt_saeulen_und_rechtsraum", 37 Zeichen. Die Spalte
alembic_version ist VARCHAR(32). Das Ganze Schema-DDL lief durch, und erst der
letzte Schritt, das Fortschreiben der Versionsnummer, brach ab:

    StringDataRightTruncationError: value too long for type character varying(32)
    [SQL: UPDATE alembic_version SET version_num='0035_scan_kennt_saeulen_und_rechtsraum' ...]

Ausgegangen ist es gut, weil PostgreSQL die DDL mit zurueckgerollt hat. Das
ist Glueck, nicht Technik: eine Migration, die unterwegs etwas nicht
Transaktionsfaehiges tut (CREATE INDEX CONCURRENTLY, eine lange Datenkorrektur
in Haeppchen), haette die Datenbank halb umgebaut zurueckgelassen und den
Kopfstand unveraendert.

Ein Test, der die Datei nur liest, kostet nichts und faengt genau das ab,
bevor irgendwer eine Verbindung aufmacht.
"""
import os
import re

import pytest

_VERSIONS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "alembic", "versions",
)

# Breite der Spalte alembic_version, von Alembic selbst angelegt.
MAX_LAENGE = 32


def _revisionen():
    if not os.path.isdir(_VERSIONS):
        pytest.skip("alembic/versions nicht eingehaengt")
    gefunden = {}
    for name in sorted(os.listdir(_VERSIONS)):
        if not name.endswith(".py") or name.startswith("_"):
            continue
        with open(os.path.join(_VERSIONS, name), encoding="utf-8") as fh:
            quelle = fh.read()
        rev = re.search(r'^revision(?::\s*str)?\s*=\s*["\']([^"\']+)["\']',
                        quelle, re.M)
        if not rev:
            continue
        gefunden[name] = (rev.group(1), _vorgaenger(quelle))
    return gefunden


def _vorgaenger(quelle):
    """Die Vorgaenger einer Revision, immer als Tupel.

    Eine Zusammenfuehrung hat mehrere, und sie stehen dann ueber mehrere Zeilen
    verteilt:

        down_revision: Union[str, tuple, None] = (
            "0024_gen_docs_version",
            "0024_entscheidung_quelle",
        )

    Mein erster Anlauf las nur die einzeilige Form. Ergebnis war ein Test, der
    drei Koepfe meldete, wo `alembic heads` einen nennt: der Waechter hat die
    Zusammenfuehrung 0025_koepfe_zusammen nicht gesehen und deshalb die beiden
    0024er fuer offen gehalten. Ein Waechter, der falsch liest, ist schlimmer
    als keiner, weil man ihm glaubt.
    """
    m = re.search(r'^down_revision(?::[^=]+)?\s*=\s*(\(.*?\)|["\'][^"\']+["\']|None)',
                  quelle, re.M | re.S)
    if not m:
        return ()
    wert = m.group(1)
    if wert == "None":
        return ()
    return tuple(re.findall(r'["\']([^"\']+)["\']', wert))


def test_es_gibt_ueberhaupt_migrationen():
    """Zuerst zaehlen, was der Waechter liest.

    Ein gruener Test ueber einer leeren Liste prueft nichts.
    """
    revs = _revisionen()
    assert len(revs) >= 30, (
        f"Nur {len(revs)} Migrationsdateien gelesen. Entweder liegt der Ordner "
        "woanders, oder dieser Waechter prueft ins Leere."
    )


def test_keine_revisionsnummer_ist_zu_lang():
    zu_lang = {
        name: rev
        for name, (rev, _) in _revisionen().items()
        if len(rev) > MAX_LAENGE
    }
    assert not zu_lang, (
        "Diese Revisionsnummern passen nicht in alembic_version "
        f"(VARCHAR({MAX_LAENGE})). Die Migration laeuft durch und bricht erst "
        "beim Fortschreiben des Kopfstands ab: "
        + "; ".join(f"{n}: {r} ({len(r)} Zeichen)" for n, r in zu_lang.items())
    )


def test_die_kette_ist_geschlossen_und_hat_einen_kopf():
    revs = _revisionen()
    nummern = {rev for rev, _ in revs.values()}

    doppelt = [r for r in nummern if
               sum(1 for rev, _ in revs.values() if rev == r) > 1]
    assert not doppelt, f"Revisionsnummer doppelt vergeben: {sorted(doppelt)}"

    verwaist = {
        name: [d for d in down if d not in nummern]
        for name, (_, down) in revs.items()
        if any(d not in nummern for d in down)
    }
    assert not verwaist, (
        "Diese Migrationen zeigen auf einen Vorgaenger, den es nicht gibt: "
        + "; ".join(f"{n} -> {d}" for n, d in verwaist.items())
    )

    verwiesen = {d for _, down in revs.values() for d in down}
    koepfe = sorted(nummern - verwiesen)
    assert len(koepfe) == 1, (
        f"Die Kette hat {len(koepfe)} Koepfe: {koepfe}. "
        "`alembic upgrade head` weiss dann nicht, welcher gemeint ist. "
        "Zwei Koepfe entstehen, wenn zwei Zweige dieselbe Revision als "
        "Vorgaenger nennen; zusammengefuehrt werden sie mit einer "
        "Merge-Revision (Beispiel: 0025_koepfe_zusammen)."
    )

    wurzeln = [rev for rev, down in revs.values() if not down]
    assert len(wurzeln) == 1, f"Mehr als eine Wurzel: {sorted(wurzeln)}"


def test_der_leser_erkennt_eine_zusammenfuehrung():
    """Die Gegenprobe zum eigenen Leser.

    Die mehrzeilige Tupelform muss ankommen, sonst meldet der Test oben
    Koepfe, die es nicht gibt.
    """
    mehrfach = [
        (name, down) for name, (_, down) in _revisionen().items()
        if len(down) > 1
    ]
    assert mehrfach, (
        "Keine Migration mit mehreren Vorgaengern gefunden. Es gibt eine "
        "(0025_koepfe_zusammen); findet der Leser sie nicht, liest er die "
        "mehrzeilige Tupelform nicht und der Kopftest darueber taeuscht."
    )
