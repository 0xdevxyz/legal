# -*- coding: utf-8 -*-
"""
Jede Tabelle, die eine Abfrage anspricht, muss es auch geben.

Gemessen am 10.09.2026 gegen die Produktionsdatenbank: neun Tabellennamen im
Code existierten nicht. Die Folgen waren nicht "ein Fehler im Log", sondern
tote Funktionen, die nach aussen wie funktionierende aussahen:

  * `cookie_consent_revisions` — die Tabelle heisst `cookie_banner_revisions`.
    Der Endpunkt fuer die Fassungshistorie lief in einen 500er, obwohl der
    Trigger `trigger_banner_revision` bei jeder Aenderung brav einen
    Schnappschuss ablegt. Der Nachweis nach Art. 7 Abs. 1 DSGVO war da, nur
    nicht abrufbar.
  * `widget_analytics` und `widget_usage_stats` — die Tabelle heisst
    `widget_events`. Der Schreibweg rief zusaetzlich eine Datenbankfunktion
    `track_widget_feature`, die es nicht gibt, und meldete im Fehlerfall
    trotzdem `{"success": true}`. Seit dem ersten Tag wurde kein einziges
    Ereignis gespeichert.
  * `analysis_results` — die vier TCF-Endpunkte antworten mit 500.

Ein Test, der die Funktionen einzeln aufruft, haette das nur dort gefunden, wo
jemand hinsieht. Dieser hier prueft die Regel: Namen im SQL gegen Namen im
Schema.

`schema_tabellen.txt` ist der Stand der Produktionsdatenbank. Wer eine Tabelle
anlegt, traegt sie dort ein (der Test sagt, welche fehlt).
"""

import ast
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIER = os.path.dirname(os.path.abspath(__file__))

SQL = re.compile(r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b", re.I)
TAB = re.compile(r"\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-z_][a-z0-9_]{2,})", re.I)

# Woerter, die in SQL hinter FROM/INTO/UPDATE stehen koennen, ohne Tabelle zu
# sein — plus deutsche Prosa aus Kommentaren innerhalb von SQL-Zeichenketten.
KEINE_TABELLE = {
    "select", "where", "values", "set", "table", "only", "lateral", "unnest",
    "generate_series", "jsonb_array_elements", "json_array_elements", "jsonb_each",
    "jsonb_to_recordset", "public", "dual", "conflict", "returning", "exists",
    "each", "row", "rows", "the", "and", "das", "der", "die", "den", "dem",
    "eine", "einen", "einem", "mit", "von", "aus", "bei", "auf", "nicht",
    "bereits", "betroffen", "erkannt", "falsch", "grundsaetzlich", "inklusive",
    "next", "not", "update_row", "details", "site_id", "session", "banner",
    "cookie", "consent", "custom", "geo", "google", "tcf", "age", "cache",
    "data", "file", "lead", "retention", "success", "test", "tests", "und",
    "integration", "scan", "user", "url", "query", "list", "main", "app",
    # "from update #123" in einer Protokollmeldung ist kein Tabellenname.
    "update",
}

# Tabellen, die eine Migration anlegt oder loescht — dort ist der Name Absicht.
NUR_IN_MIGRATIONEN = {
    "fix_acceptance_metrics",
    "_archived_erecht24_projects",
    # Der Aufraeumlauf in main_production faengt die fehlende Tabelle
    # ausdruecklich ab und meldet "existiert nicht — uebersprungen". Das ist
    # kein stiller Fehlschlag, sondern eine benannte Ausnahme.
    "ai_call_logs",
}


def _bekannte_tabellen():
    pfad = os.path.join(HIER, "schema_tabellen.txt")
    with open(pfad, encoding="utf-8") as f:
        return {z.strip().lower() for z in f if z.strip()}


def _referenzen():
    """Tabellennamen aus echten SQL-Zeichenketten, mit Fundstelle."""
    gefunden = {}
    for wurzel, ordner, dateien in os.walk(BACKEND):
        teile = wurzel.split(os.sep)
        if any(t in ("_archive_pre_baseline", "venv", "__pycache__", "tests",
                     "alembic", "node_modules") for t in teile):
            continue
        for name in dateien:
            if not name.endswith(".py") or ".bak" in name:
                continue
            pfad = os.path.join(wurzel, name)
            try:
                quelle = open(pfad, encoding="utf-8", errors="replace").read()
                baum = ast.parse(quelle)
            except Exception:
                continue
            for knoten in ast.walk(baum):
                if not (isinstance(knoten, ast.Constant) and isinstance(knoten.value, str)):
                    continue
                if not SQL.search(knoten.value):
                    continue
                for t in TAB.findall(knoten.value):
                    t = t.lower()
                    if t in KEINE_TABELLE or t.startswith(("pg_", "information_")):
                        continue
                    gefunden.setdefault(t, set()).add(
                        f"{os.path.relpath(pfad, BACKEND)}:{knoten.lineno}")
    return gefunden


def test_jede_angesprochene_tabelle_existiert():
    bekannt = _bekannte_tabellen()
    fehlend = {
        t: sorted(o) for t, o in _referenzen().items()
        if t not in bekannt and t not in NUR_IN_MIGRATIONEN
    }
    assert not fehlend, (
        "SQL spricht Tabellen an, die es im Schema nicht gibt:\n"
        + "\n".join(f"  {t:34s} <- {', '.join(o)[:110]}" for t, o in sorted(fehlend.items()))
        + "\n\nEntweder ist der Name falsch (haeufiger) oder die Tabelle fehlt in "
          "schema_tabellen.txt (dann eintragen)."
    )


def test_schemaliste_ist_gepflegt():
    """Eine leere oder geschrumpfte Liste wuerde den Test oben wertlos machen."""
    bekannt = _bekannte_tabellen()
    assert len(bekannt) >= 80, f"Nur {len(bekannt)} Tabellen in schema_tabellen.txt"
    for pflicht in ("users", "cookie_consent_logs", "cookie_banner_revisions",
                    "widget_events", "tracked_websites", "vertragsannahmen"):
        assert pflicht in bekannt, f"{pflicht} fehlt in schema_tabellen.txt"
