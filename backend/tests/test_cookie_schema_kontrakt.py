"""
Waechtertests fuer den Cookie-Bereich:

1) Schema-Kontrakt: Die in cookie_compliance_routes.py und widget_routes.py
   per SQL angesprochenen Spalten der Tabellen cookie_banner_configs und
   cookie_custom_services muessen in der Live-DB existieren. Hintergrund:
   Der Reconsent-Check und der Widget-Config-Endpoint selektierten Spalten
   (requires_reconsent, language), die es in der DB nicht gab — der Fehler
   fiel erst zur Laufzeit als 500/Fallback auf. Die Extraktion laeuft
   statisch per Regex ueber den Quelltext; der DB-Abgleich braucht eine
   erreichbare Datenbank (DATABASE_URL) und ueberspringt sonst sauber.

2) Platzhalter-Ablehnung: site_id 'SITE_ID_PLACEHOLDER' (und offensichtliche
   Varianten) muessen im Config-Endpoint UND im Widget-Config-Endpoint mit
   400 abgelehnt werden — vorher lieferten beide 200 mit Default-Config und
   der Einbaufehler des Kunden blieb unsichtbar.

3) Reconsent-Logik: Hash-Vergleich ODER site-weites Flag; Config-Save mit
   geaendertem Hash setzt das Flag, ein Consent-Log setzt es zurueck.
"""

import datetime
import os
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import cookie_compliance_routes
import widget_routes
from cookie_compliance_routes import compute_config_hash, router as cookie_router
from widget_routes import router as widget_router

BACKEND_DIR = Path(__file__).resolve().parents[1]
QUELLDATEIEN = ["cookie_compliance_routes.py", "widget_routes.py"]
TABELLEN = ["cookie_banner_configs", "cookie_custom_services"]

# ============================================================================
# 1) Schema-Kontrakt (statische Extraktion + Live-DB-Abgleich)
# ============================================================================

# Tokens, die in SELECT-Listen/WHERE-Klauseln auftauchen, aber keine Spalten sind
_SQL_KEYWORDS = {
    "select", "from", "where", "and", "or", "not", "is", "in", "as", "like",
    "case", "when", "then", "else", "end", "true", "false", "null",
    "distinct", "coalesce", "count", "sum", "min", "max", "avg", "now",
    "excluded", "interval", "limit", "order", "group", "by", "desc", "asc",
    "returning", "set", "update", "insert", "into", "values", "on",
    "conflict", "do", "nothing", "left", "right", "inner", "outer", "join",
    "array_agg", "filter", "jsonb", "text", "integer", "boolean", "cast",
    "current_timestamp", "current_date", "exists", "between",
}


def _sql_strings(quelltext: str):
    """Alle String-Literale einsammeln, die SQL enthalten koennten."""
    teile = []
    for m in re.finditer(r'"""(.*?)"""', quelltext, re.S):
        teile.append(m.group(1))
    for m in re.finditer(r"'''(.*?)'''", quelltext, re.S):
        teile.append(m.group(1))
    # Einzeilige Strings (z.B. "SELECT id FROM cookie_banner_configs WHERE ...").
    # Implizit konkatenierte Mehrzeiler werden je Zeile einzeln erfasst.
    muster = r'(?:cookie_banner_configs|cookie_custom_services)'
    for m in re.finditer(r'"([^"\n]*%s[^"\n]*)"' % muster, quelltext):
        teile.append(m.group(1))
    for m in re.finditer(r"'([^'\n]*%s[^'\n]*)'" % muster, quelltext):
        teile.append(m.group(1))
    return teile


def _spalten_aus_liste(listen_text: str):
    """Spaltennamen aus einer SELECT-Liste oder INSERT-Spaltenliste ziehen."""
    spalten = set()
    for eintrag in listen_text.split(","):
        eintrag = eintrag.strip()
        if not eintrag or eintrag.startswith("*") or eintrag.startswith("$"):
            continue
        m = re.match(r"(?:[A-Za-z_][A-Za-z0-9_]*\.)?([A-Za-z_][A-Za-z0-9_]*)", eintrag)
        if not m:
            continue
        name = m.group(1)
        if name.lower() not in _SQL_KEYWORDS:
            spalten.add(name.lower())
    return spalten


def _identifikatoren(klausel_text: str):
    """Alle Spalten-Kandidaten einer WHERE-/SET-Klausel (Keywords gefiltert)."""
    return {
        t.lower()
        for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", klausel_text)
        if t.lower() not in _SQL_KEYWORDS
    }


_ENDE = r"(?:\bORDER\s+BY\b|\bGROUP\s+BY\b|\bLIMIT\b|\bRETURNING\b|$)"


def verwendete_spalten(quelltext: str, tabelle: str):
    """
    Extrahiert die in SELECT/UPDATE/INSERT/DELETE einer Tabelle verwendeten
    Spalten. Bewusst pragmatisch: Statements mit Tabellen-Alias oder JOIN
    werden uebersprungen, weil dort eine eindeutige Spalte→Tabelle-Zuordnung
    per Regex nicht mehr verlaesslich ist.
    """
    spalten = set()
    for sql in _sql_strings(quelltext):
        if tabelle not in sql:
            continue

        # Alias/JOIN → Zuordnung unklar → auslassen
        alias = re.search(r"FROM\s+%s\s+([A-Za-z_][A-Za-z0-9_]*)" % tabelle, sql, re.I)
        if (alias and alias.group(1).lower() not in _SQL_KEYWORDS) or re.search(r"\bJOIN\b", sql, re.I):
            continue

        # SELECT <liste> FROM <tabelle> [WHERE <bedingung>]
        for m in re.finditer(
            r"SELECT\s+(.+?)\s+FROM\s+%s\b(?:\s+WHERE\s+(.+?))?\s*%s" % (tabelle, _ENDE),
            sql, re.S | re.I,
        ):
            spalten |= _spalten_aus_liste(m.group(1))
            if m.group(2):
                spalten |= _identifikatoren(m.group(2))

        # UPDATE <tabelle> SET <zuweisungen> [WHERE <bedingung>]
        for m in re.finditer(
            r"UPDATE\s+%s\s+SET\s+(.+?)(?:\s+WHERE\s+(.+?))?\s*%s" % (tabelle, _ENDE),
            sql, re.S | re.I,
        ):
            for lhs in re.finditer(r"(?:^|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", m.group(1)):
                if lhs.group(1).lower() not in _SQL_KEYWORDS:
                    spalten.add(lhs.group(1).lower())
            if m.group(2):
                spalten |= _identifikatoren(m.group(2))

        # INSERT INTO <tabelle> (<spalten>)
        for m in re.finditer(
            r"INSERT\s+INTO\s+%s\s*\(\s*(.+?)\s*\)\s*VALUES" % tabelle,
            sql, re.S | re.I,
        ):
            spalten |= _spalten_aus_liste(m.group(1))

        # DELETE FROM <tabelle> WHERE <bedingung>
        for m in re.finditer(
            r"DELETE\s+FROM\s+%s\s+WHERE\s+(.+?)\s*%s" % (tabelle, _ENDE),
            sql, re.S | re.I,
        ):
            spalten |= _identifikatoren(m.group(1))

    return spalten


def _alle_verwendeten_spalten(tabelle: str):
    gesamt = set()
    for datei in QUELLDATEIEN:
        quelltext = (BACKEND_DIR / datei).read_text(encoding="utf-8")
        gesamt |= verwendete_spalten(quelltext, tabelle)
    return gesamt


def test_extraktion_findet_kernspalten():
    """Selbsttest des Extraktors: Kernspalten muessen gefunden werden."""
    banner = _alle_verwendeten_spalten("cookie_banner_configs")
    assert {"site_id", "config_hash", "requires_reconsent", "is_active", "language"} <= banner, (
        f"Extraktor unvollstaendig — gefunden: {sorted(banner)}"
    )
    custom = _alle_verwendeten_spalten("cookie_custom_services")
    assert {"site_id", "service_key"} <= custom, (
        f"Extraktor unvollstaendig — gefunden: {sorted(custom)}"
    )


def _lade_db_spalten(dsn: str, tabelle: str):
    """Spalten der Tabelle aus information_schema — psycopg, psycopg2 oder asyncpg."""
    abfrage = (
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s"
    )
    try:
        import psycopg  # psycopg 3
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(abfrage, (tabelle,))
                return {r[0] for r in cur.fetchall()}
    except ImportError:
        pass
    try:
        import psycopg2
        conn = psycopg2.connect(dsn, connect_timeout=3)
        try:
            with conn.cursor() as cur:
                cur.execute(abfrage, (tabelle,))
                return {r[0] for r in cur.fetchall()}
        finally:
            conn.close()
    except ImportError:
        pass
    # Fallback: asyncpg ist im Backend-Image garantiert vorhanden
    import asyncio
    import asyncpg

    async def _laden():
        conn = await asyncpg.connect(dsn, timeout=3)
        try:
            rows = await conn.fetch(
                "SELECT column_name FROM information_schema.columns WHERE table_name = $1",
                tabelle,
            )
            return {r["column_name"] for r in rows}
        finally:
            await conn.close()

    return asyncio.run(_laden())


@pytest.mark.parametrize("tabelle", TABELLEN)
def test_verwendete_spalten_existieren_in_db(tabelle):
    """
    Kontrakt: Jede im Code angesprochene Spalte existiert in der Live-DB.
    Ohne erreichbare DB (docker-run-Harness) wird sauber uebersprungen —
    der Test ist fuer den CI-Betrieb mit Datenbank gedacht.
    """
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("Keine DATABASE_URL gesetzt — Schema-Kontrakt braucht die Live-DB")
    try:
        db_spalten = _lade_db_spalten(dsn, tabelle)
    except Exception as e:
        pytest.skip(f"Datenbank nicht erreichbar ({e}) — Schema-Kontrakt uebersprungen")

    if not db_spalten:
        pytest.fail(f"Tabelle {tabelle} existiert nicht in der Datenbank")

    verwendet = _alle_verwendeten_spalten(tabelle)
    fehlend = verwendet - db_spalten
    assert not fehlend, (
        f"Code verwendet Spalten, die in {tabelle} fehlen: {sorted(fehlend)}. "
        f"Migration einspielen oder Query korrigieren."
    )


# ============================================================================
# 2) Platzhalter-Ablehnung (reiner Unit-Test mit TestClient)
# ============================================================================

def make_client():
    app = FastAPI()
    app.include_router(cookie_router)
    app.include_router(widget_router)
    return TestClient(app, raise_server_exceptions=False)


PLATZHALTER = [
    "SITE_ID_PLACEHOLDER",
    "site_id_placeholder",
    "null",
    "undefined",
    "None",
    "your-site-id",
]


@pytest.mark.parametrize("platzhalter", PLATZHALTER)
def test_config_endpoint_lehnt_platzhalter_ab(monkeypatch, platzhalter):
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock()
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)

    client = make_client()
    resp = client.get(
        f"/api/cookie-compliance/config/{platzhalter}",
        headers={"referer": "https://kunde.example/"},
    )

    assert resp.status_code == 400, resp.text
    assert "site_id" in resp.json()["detail"]
    # Die Ablehnung muss VOR jedem DB-Zugriff greifen
    mock_pool.fetchrow.assert_not_called()


@pytest.mark.parametrize("platzhalter", PLATZHALTER)
def test_widget_config_lehnt_platzhalter_ab(monkeypatch, platzhalter):
    monkeypatch.setattr(widget_routes, "db_pool", None)

    client = make_client()
    resp = client.get(f"/api/widgets/config/{platzhalter}")

    assert resp.status_code == 400, resp.text


def test_config_endpoint_akzeptiert_echte_site_id(monkeypatch):
    """Regressionsschutz: echte site_ids duerfen NICHT abgelehnt werden."""
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(return_value=None)  # keine Config → Default
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)

    client = make_client()
    resp = client.get("/api/cookie-compliance/config/beispiel-kunde-de")

    assert resp.status_code == 200, resp.text
    assert resp.json()["success"] is True


def test_widget_config_akzeptiert_echte_site_id(monkeypatch):
    monkeypatch.setattr(widget_routes, "db_pool", None)

    client = make_client()
    resp = client.get("/api/widgets/config/beispiel-kunde-de")

    assert resp.status_code == 200, resp.text
    assert resp.json()["success"] is True


# ============================================================================
# 3) Reconsent-Logik
# ============================================================================

def _pool_mit_config(config_hash="hash-alt", requires_reconsent=False):
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(
        return_value={"config_hash": config_hash, "requires_reconsent": requires_reconsent}
    )
    return mock_pool


def test_reconsent_check_liefert_200_und_vergleicht_hash(monkeypatch):
    mock_pool = _pool_mit_config(config_hash="abc")
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)
    client = make_client()

    # Abweichender Client-Hash → Reconsent noetig
    resp = client.get("/api/cookie-compliance/reconsent-check/test-site?config_hash=xyz")
    assert resp.status_code == 200, resp.text
    assert resp.json()["requires_reconsent"] is True

    # Gleicher Hash → kein Reconsent
    resp = client.get("/api/cookie-compliance/reconsent-check/test-site?config_hash=abc")
    assert resp.status_code == 200, resp.text
    assert resp.json()["requires_reconsent"] is False
    assert resp.json()["current_hash"] == "abc"


def test_reconsent_check_respektiert_site_flag(monkeypatch):
    """Gesetztes requires_reconsent-Flag gewinnt auch bei passendem Hash."""
    mock_pool = _pool_mit_config(config_hash="abc", requires_reconsent=True)
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)
    client = make_client()

    resp = client.get("/api/cookie-compliance/reconsent-check/test-site?config_hash=abc")
    assert resp.status_code == 200, resp.text
    assert resp.json()["requires_reconsent"] is True


def test_config_save_pflegt_reconsent_hash(monkeypatch):
    """POST /config muss config_hash schreiben und bei Aenderung das Flag setzen."""
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(side_effect=[{"id": 1}, {"id": 1, "revision": 3}])
    mock_pool.execute = AsyncMock()
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)
    monkeypatch.setattr(
        cookie_compliance_routes, "get_current_user_required",
        AsyncMock(return_value={"id": 1, "email": "test@example.com"}),
    )
    monkeypatch.setattr(cookie_compliance_routes, "get_user_id_from_token", AsyncMock(return_value=1))
    monkeypatch.setattr(cookie_compliance_routes, "require_module", AsyncMock(return_value=True))
    monkeypatch.setattr(cookie_compliance_routes, "get_user_site_ids", AsyncMock(return_value={"test-site"}))

    client = make_client()
    resp = client.post(
        "/api/cookie-compliance/config",
        json={"site_id": "test-site", "texts": {"de": {}}, "services": ["ga4"]},
        headers={"Authorization": "Bearer x"},
    )

    assert resp.status_code == 200, resp.text

    hash_calls = [
        c for c in mock_pool.execute.call_args_list
        if "config_hash" in c.args[0]
    ]
    assert hash_calls, "Config-Save hat config_hash nicht aktualisiert"
    sql = hash_calls[0].args[0]
    assert "requires_reconsent" in sql, "Config-Save setzt requires_reconsent nicht"
    # Der uebergebene Hash muss dem deterministischen Service-Hash entsprechen
    assert hash_calls[0].args[2] == compute_config_hash(["ga4"])


def test_config_hash_ist_reihenfolge_unabhaengig():
    assert compute_config_hash(["ga4", "maps"]) == compute_config_hash(["maps", "ga4"])
    assert compute_config_hash(["ga4"]) != compute_config_hash(["ga4", "maps"])


def test_consent_log_setzt_reconsent_flag_zurueck(monkeypatch):
    """
    Nach erfolgreichem Consent-Log wird das site-weite Flag geloescht.

    Der Reset laeuft ueber eine eigene Connection (pool.acquire), damit der
    Stats-Upsert der einzige direkte Pool-execute des Endpoints bleibt
    (siehe test_consent_flow::test_stats_upsert_is_called_once).
    """
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(side_effect=[
        {"id": 1},  # Config-Lookup (revision_id)
        {"id": 7, "timestamp": datetime.datetime.now()},  # INSERT RETURNING
    ])
    mock_pool.execute = AsyncMock()
    mock_conn = MagicMock()
    mock_conn.execute = AsyncMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)
    monkeypatch.setattr(cookie_compliance_routes, "check_rate_limit", AsyncMock(return_value=True))

    client = make_client()
    resp = client.post(
        "/api/cookie-compliance/consent",
        json={
            "site_id": "test-site",
            "visitor_id": "visitor-abc",
            "consent_categories": {
                "necessary": True,
                "functional": True,
                "analytics": False,
                "marketing": False,
            },
        },
    )

    assert resp.status_code == 200, resp.text
    reset_calls = [
        c for c in mock_conn.execute.call_args_list
        if "requires_reconsent = false" in c.args[0]
    ]
    assert reset_calls, "Consent-Log setzt requires_reconsent nicht zurueck"
    assert reset_calls[0].args[1] == "test-site"
    # Der Stats-Upsert bleibt der einzige direkte Pool-execute
    assert mock_pool.execute.await_count == 1
