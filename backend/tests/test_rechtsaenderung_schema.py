# -*- coding: utf-8 -*-
"""
Jede Spalte, die der Benachrichtigungsdienst fuer Rechtsaenderungen anspricht,
muss es im Schema geben: Baseline plus Migrationen.

Anlass (08.10.2026): GET /api/legal-notifications/confirm/<token> lief live in

    Error confirming notification: column "confirmation_token" does not exist

legal_notification_service.py benutzte seit Februar 2026 sechs Spalten von
legal_change_notifications (legal_news_id, severity, confirmation_token,
action_required, action_deadline, confirmed_at), die es in der
Produktionstabelle nie gab. Beim Nachstellen gegen ein Postgres mit Baseline
kam eine siebte dazu: die Nutzerabfrage las u.firebase_uid, eine Spalte, die
users nicht hat (live gemessen: 0 Treffer in information_schema). Selbst mit
den sechs Spalten waere also keine Benachrichtigung entstanden.

Kein Test hat es gemerkt: test_schema_deckung.py prueft Tabellennamen, nicht
Spalten, und die Dienst-Tests laufen gegen einen Mock, der jede Spalte annimmt.

Dieser Test liest beide Seiten aus den Dateien:
  * Schema: CREATE TABLE in alembic/baseline_schema.sql (Stand der
    Produktionsdatenbank am 17.07.2026), dann je Migration in upgrade():
    CREATE TABLE IF NOT EXISTS, ALTER TABLE ... ADD/DROP COLUMN,
    op.add_column/op.drop_column.
  * Benutzt: die SQL-Zeichenketten in legal_notification_service.py und
    legal_notification_routes.py. Gelesen werden Spalten mit Tabellenalias
    (lcn.x, u.x), INSERT-Spaltenlisten, und bei legal_change_notifications
    ohne Alias auch SET/WHERE/RETURNING.
"""

import ast
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABELLE = "legal_change_notifications"
DATEIEN = ("legal_notification_service.py", "legal_notification_routes.py")

SQL_WOERTER = {
    "select", "from", "where", "and", "or", "in", "is", "not", "null", "set",
    "update", "insert", "into", "values", "returning", "join", "left", "on",
    "as", "order", "by", "case", "when", "then", "else", "end", "desc", "asc",
    "count", "filter", "true", "false", "current_timestamp", "interval", "limit",
}
KEIN_ALIAS = SQL_WOERTER | {"inner", "outer", "lateral"}


# ---------------------------------------------------------------- Schema --

def _spalten_aus_create(rumpf):
    """Spaltennamen aus dem Rumpf eines CREATE TABLE, Kommas in Klammern
    (DEFAULT ARRAY[...], VARCHAR(50)) zaehlen nicht."""
    teile, tiefe, aktuell = [], 0, ""
    for z in rumpf:
        if z in "([":
            tiefe += 1
        elif z in ")]":
            tiefe -= 1
        if z == "," and tiefe == 0:
            teile.append(aktuell)
            aktuell = ""
        else:
            aktuell += z
    teile.append(aktuell)
    namen = set()
    for t in teile:
        wort = t.strip().split()[0].strip('"') if t.strip() else ""
        if wort and wort.upper() not in {"CONSTRAINT", "PRIMARY", "UNIQUE", "FOREIGN", "CHECK"}:
            namen.add(wort.lower())
    return namen


def _baseline():
    with open(os.path.join(BACKEND, "alembic", "baseline_schema.sql"), encoding="utf-8") as f:
        sql = f.read()
    return {m.group(1): _spalten_aus_create(m.group(2))
            for m in re.finditer(r"CREATE TABLE public\.(\w+) \((.*?)\n\);", sql, re.S)}


def _upgrade(quelle):
    for knoten in ast.parse(quelle).body:
        if isinstance(knoten, ast.FunctionDef) and knoten.name == "upgrade":
            return knoten
    return None


def _create_rumpf(sql, start):
    """Rumpf ab der oeffnenden Klammer bis zur passenden schliessenden."""
    tiefe = 0
    for i in range(start, len(sql)):
        if sql[i] == "(":
            tiefe += 1
        elif sql[i] == ")":
            tiefe -= 1
            if tiefe == 0:
                return sql[start + 1:i]
    return ""


def _schema():
    schema = _baseline()
    ordner = os.path.join(BACKEND, "alembic", "versions")
    for name in sorted(os.listdir(ordner)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(ordner, name), encoding="utf-8") as f:
            up = _upgrade(f.read())
        if up is None:
            continue
        for k in ast.walk(up):
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                sql = k.value
                for m in re.finditer(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(?:public\.)?(\w+)\s*\(", sql, re.I):
                    schema.setdefault(m.group(1).lower(), set()).update(
                        _spalten_aus_create(_create_rumpf(sql, m.end() - 1)))
                for m in re.finditer(r"ALTER\s+TABLE\s+(?:ONLY\s+)?(?:IF\s+EXISTS\s+)?(?:public\.)?(\w+)(.*?)(?:;|$)",
                                     sql, re.I | re.S):
                    tab = schema.setdefault(m.group(1).lower(), set())
                    tab |= {s.lower() for s in re.findall(
                        r"ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", m.group(2), re.I)}
                    tab -= {s.lower() for s in re.findall(
                        r"DROP\s+COLUMN\s+(?:IF\s+EXISTS\s+)?(\w+)", m.group(2), re.I)}
            if isinstance(k, ast.Call) and isinstance(k.func, ast.Attribute) \
                    and k.func.attr in ("add_column", "drop_column") and len(k.args) >= 2:
                tab = k.args[0].value if isinstance(k.args[0], ast.Constant) else None
                arg = k.args[1]
                spalte = (arg.value if isinstance(arg, ast.Constant)
                          else arg.args[0].value if isinstance(arg, ast.Call) and arg.args
                          and isinstance(arg.args[0], ast.Constant) else None)
                if tab and spalte:
                    ziel = schema.setdefault(tab, set())
                    (ziel.add if k.func.attr == "add_column" else ziel.discard)(spalte)
    return schema


# ---------------------------------------------------------------- Benutzt --

def _benutzt_im_sql(sql):
    """{tabelle: {spalten}} aus einer SQL-Zeichenkette."""
    s = re.sub(r"'[^']*'", "''", sql)
    s = re.sub(r"--[^\n]*", "", s)
    alias = {}
    for tab, al in re.findall(r"\b(?:FROM|JOIN|UPDATE)\s+(\w+)\s+(?:AS\s+)?(\w+)", s, re.I):
        if al.lower() not in KEIN_ALIAS:
            alias[al] = tab.lower()
    gefunden = {}
    for al, spalte in re.findall(r"\b(\w+)\.(\w+)\b", s):
        if al in alias:
            gefunden.setdefault(alias[al], set()).add(spalte.lower())
    for tab, liste in re.findall(r"INSERT\s+INTO\s+(\w+)\s*\(([^)]*)\)", s, re.I):
        gefunden.setdefault(tab.lower(), set()).update(
            c.strip().lower() for c in liste.split(",") if c.strip())
    # legal_change_notifications ohne Alias: unqualifizierte Namen gehoeren zu ihr.
    if re.search(rf"\b(?:UPDATE|FROM)\s+{TABELLE}\b(?!\s+(?!(?:WHERE|SET)\b)\w+\s)", s, re.I):
        namen = set(re.findall(r"\b([a-z_]\w*)\s*(?:=|\bIN\b|\bIS\b)", s, re.I))
        for liste in re.findall(r"RETURNING\s+([\w\s,]+?)\s*$", s, re.I | re.M):
            namen |= {c.strip() for c in liste.split(",") if c.strip()}
        namen |= set(re.findall(r"FILTER\s*\(\s*WHERE\s+(\w+)\b", s, re.I))
        gefunden.setdefault(TABELLE, set()).update(
            n.lower() for n in namen if n.lower() not in SQL_WOERTER)
    return gefunden


def _benutzt():
    """{(tabelle, spalte): {fundstellen}}"""
    gefunden = {}
    for datei in DATEIEN:
        with open(os.path.join(BACKEND, datei), encoding="utf-8") as f:
            quelle = f.read()
        for k in ast.walk(ast.parse(quelle)):
            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                continue
            if not re.search(r"\b(SELECT|INSERT\s+INTO|UPDATE)\b", k.value, re.I):
                continue
            for tab, spalten in _benutzt_im_sql(k.value).items():
                for sp in spalten:
                    gefunden.setdefault((tab, sp), set()).add(f"{datei}:{k.lineno}")
        # Nach "SELECT * FROM legal_change_notifications" liest der Dienst die
        # Zeile per Schluessel; das steht nicht im SQL.
        for sp in re.findall(r"\bnotification\[['\"](\w+)['\"]\]", quelle):
            gefunden.setdefault((TABELLE, sp), set()).add(f"{datei} (notification[...])")
    return gefunden


# ------------------------------------------------------------------ Tests --

def test_jede_benutzte_spalte_gibt_es():
    schema = _schema()
    fehlend = {
        (t, s): sorted(o) for (t, s), o in _benutzt().items()
        if t in schema and s not in schema[t]
    }
    unbekannt = sorted({t for t, _ in _benutzt()} - set(schema))
    assert not unbekannt, f"Tabellen weder in Baseline noch in Migrationen: {unbekannt}"
    assert not fehlend, (
        "Der Benachrichtigungsdienst spricht Spalten an, die weder die "
        "Baseline noch eine Migration anlegt:\n"
        + "\n".join(f"  {t}.{s:22s} <- {', '.join(o)}" for (t, s), o in sorted(fehlend.items()))
    )


def test_der_leser_findet_was_er_finden_muss():
    """Erst zaehlen, was der Waechter liest. Ein gruener Test ueber einer
    leeren Menge prueft nichts."""
    schema = _schema()
    assert {"id", "user_id", "legal_change_id", "status", "sent_at"} <= _baseline()[TABELLE]
    assert {"email_enabled", "digest_frequency"} <= schema["user_legal_notification_settings"], \
        "CREATE TABLE IF NOT EXISTS aus Migration 0003 nicht gelesen"
    assert "ki_erlaubt" in schema["users"], "ALTER TABLE aus Migration 0036 nicht gelesen"

    benutzt = _benutzt()
    lcn = {s for t, s in benutzt if t == TABELLE}
    erwartet = {"user_id", "legal_news_id", "severity", "status", "confirmation_token",
                "action_required", "action_deadline", "confirmed_at", "sent_at", "id"}
    assert erwartet <= lcn, f"Leser uebersieht: {sorted(erwartet - lcn)}"
    tabellen = {t for t, _ in benutzt}
    assert {"users", "legal_news", "user_legal_notification_settings",
            "user_legal_notifications", "tracked_websites"} <= tabellen, sorted(tabellen)


def test_ohne_migration_0037b_haette_der_waechter_angeschlagen():
    """Gegenprobe: gegen die Baseline allein meldet der Leser genau die sechs
    Spalten, an denen live die Bestaetigung scheiterte."""
    benutzt = {s for t, s in _benutzt() if t == TABELLE}
    assert benutzt - _baseline()[TABELLE] == {
        "legal_news_id", "severity", "confirmation_token",
        "action_required", "action_deadline", "confirmed_at"}


def test_der_leser_erkennt_eine_fehlende_nutzerspalte():
    """Gegenprobe fuer den zweiten Fund: u.firebase_uid wuerde gemeldet."""
    sql = "SELECT u.id, u.firebase_uid FROM users u LEFT JOIN x ulns ON u.id = ulns.user_id"
    assert "firebase_uid" in _benutzt_im_sql(sql)["users"]
    assert "firebase_uid" not in _schema()["users"]


def test_process_new_nur_fuer_admins():
    """Mit den Spalten legt /process-new echte Benachrichtigungen an und
    verschickt Mails an alle bestaetigten Konten."""
    with open(os.path.join(BACKEND, "legal_notification_routes.py"), encoding="utf-8") as f:
        baum = ast.parse(f.read())
    for k in ast.walk(baum):
        if isinstance(k, ast.AsyncFunctionDef) and k.name == "trigger_process_new_changes":
            abh = [ast.unparse(d) for d in k.args.defaults]
            assert "Depends(require_admin)" in abh, abh
            return
    raise AssertionError("trigger_process_new_changes nicht gefunden")
