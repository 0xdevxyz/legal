# -*- coding: utf-8 -*-
"""Die Kanalmessung gegen ein ECHTES Postgres-Schema.

Warum zusaetzlich zu `test_kanal_auswertung.py`: Dort ist die Datenbank eine
Attrappe, und eine Attrappe, die die Zielklasse nicht kennt, testet die eigene
Fantasie (so war die Warteliste im September wochenlang gruen und tot). Hier
laufen die SQL-Abfragen und beide Schreibstellen gegen das Schema, das
`alembic upgrade head` baut, also das der Produktion.

Der Test braucht eine WEGWERF-Datenbank und ueberspringt ohne sie:

    docker network create kanal-test
    docker run -d --name kanal-pg --network kanal-test -e POSTGRES_PASSWORD=test \\
        -e POSTGRES_DB=complyo_test postgres:16-alpine
    docker run --rm --network kanal-test -v "$PWD:/repo" -w /repo/backend \\
        -e DATABASE_URL=postgresql://postgres:test@kanal-pg:5432/complyo_test \\
        legal-backend alembic upgrade head
    docker run --rm --network kanal-test -v "$PWD:/repo" -w /repo/backend \\
        -e KANAL_TEST_DATABASE_URL=postgresql://postgres:test@kanal-pg:5432/complyo_test \\
        legal-backend python -m pytest tests/test_kanal_auswertung_db.py -q

Ein uebersprungener Test bewacht nichts: der Lauf mit dieser Datenbank steht im
Pull-Request, der den Test einfuehrt, mit Zahlen.

Sicherung: der Test schreibt (Testdaten mit der Endung @kanal-test.invalid) und
weigert sich, gegen eine Datenbank zu laufen, deren Name nicht `test` enthaelt.
"""
import asyncio
import os
from datetime import datetime, timezone
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import pytest

URL = os.environ.get("KANAL_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not URL,
    reason="KANAL_TEST_DATABASE_URL nicht gesetzt (Wegwerf-Postgres noetig, Aufruf im Kopf der Datei)",
)

if URL:
    _name = urlparse(URL).path.strip("/")
    if "test" not in _name:
        raise RuntimeError(f"Datenbank {_name!r} sieht nicht nach Test aus, Abbruch")

import asyncpg  # noqa: E402

import herkunft  # noqa: E402
import kanal_auswertung as ka  # noqa: E402

ENDE = "@kanal-test.invalid"
UTC = timezone.utc


def _utc(*a):
    return datetime(*a, tzinfo=UTC)


def _naiv(*a):
    return datetime(*a)


async def _aufraeumen(conn):
    await conn.execute("DELETE FROM kauf_herkunft WHERE stripe_subscription_id LIKE 'sub_kt_%'")
    await conn.execute(
        "DELETE FROM subscriptions WHERE user_id IN (SELECT id FROM users WHERE email LIKE $1)", "%" + ENDE)
    await conn.execute("DELETE FROM users WHERE email LIKE $1", "%" + ENDE)
    await conn.execute("DELETE FROM waitlist_leads WHERE email LIKE $1", "%" + ENDE)


async def _nutzer(conn, name, angelegt):
    return await conn.fetchval(
        "INSERT INTO users (email, password_hash, full_name, created_at) VALUES ($1, 'x', $2, $3) RETURNING id",
        name + ENDE, name, angelegt)


async def _saeen():
    conn = await asyncpg.connect(URL)
    try:
        await _aufraeumen(conn)
        # Woche 41 = Mo 05.10.2026 00:00 bis Mo 12.10.2026 00:00 Berlin
        #           = 04.10. 22:00 UTC bis 11.10. 22:00 UTC (Sommerzeit, UTC+2).
        # Warteliste
        wl = [
            # (mail, source, content, angelegt UTC, bestaetigt, platz)
            ("lead1", "linkedin", "P01", _utc(2026, 10, 6, 8), True, 9001),
            ("lead2", "linkedin", "p01", _utc(2026, 10, 7, 9), False, None),
            ("lead3", "tiktok", None, _utc(2026, 10, 11, 21, 30), True, 9003),   # 23:30 Berlin, innen
            ("lead4", "youtube", None, _utc(2026, 10, 11, 22, 30), False, None),  # 00:30 Berlin Mo 12.10., aussen
            ("lead5", "linkedin", "p01", _utc(2026, 10, 4, 21, 30), False, None),  # 23:30 Berlin So 04.10., aussen
            ("lead6", None, None, _utc(2026, 10, 8, 12), False, None),
        ]
        for mail, s, c, an, best, platz in wl:
            await conn.execute(
                """INSERT INTO waitlist_leads (email, consent_given_at, confirmed_at, created_at,
                                               utm_source, utm_content, platz_nr)
                   VALUES ($1, $2, $3, $2, $4, $5, $6)""",
                mail + ENDE, an, an if best else None, s, c, platz)

        u = {}
        u["u1"] = await _nutzer(conn, "lead1", _utc(2026, 10, 6, 10))     # auf der Liste (linkedin/P01)
        u["u2"] = await _nutzer(conn, "lead3", _utc(2026, 10, 9, 10))     # auf der Liste (tiktok)
        u["u3"] = await _nutzer(conn, "LEAD2", _utc(2026, 10, 7, 12))     # Grossschreibung: lower() muss greifen
        u["u4"] = await _nutzer(conn, "fremd", _utc(2026, 10, 10, 12))    # nicht auf der Liste
        u["u5"] = await _nutzer(conn, "zuspaet", _utc(2026, 10, 11, 22, 10))  # 00:10 Berlin Mo 12.10., aussen
        u["u6"] = await _nutzer(conn, "eigen", _utc(2026, 10, 8, 8))      # eigenes Testkonto

        await herkunft.registrierung_festhalten(_Pool(conn), u["u1"], {"utm_source": "linkedin", "utm_content": "P01"})
        await herkunft.registrierung_festhalten(_Pool(conn), u["u3"], {"utm_source": "warteliste", "utm_content": "mail-a"})
        await herkunft.registrierung_festhalten(_Pool(conn), u["u6"], {"utm_source": "linkedin", "utm_content": "P01"})

        subs = [
            # (nutzer, abo, ledger-Tarif, Status, angelegt (naiv, DB-Zeit UTC), kauf_herkunft: (plan, source, content) oder None)
            ("u1", "sub_kt_1", "pro", "active", _naiv(2026, 10, 7, 10), ("pro", "linkedin", "P01")),
            ("u3", "sub_kt_2", "pro", "canceled", _naiv(2026, 10, 9, 10), ("agency", "warteliste", "mail-a")),
            ("u4", "sub_kt_3", "pro", "active", _naiv(2026, 10, 10, 10), None),
            ("u1", "sub_kt_4", "agency", "active", _naiv(2026, 10, 8, 10), ("agency_extra", "linkedin", "P01")),
            ("u4", "sub_kt_5", "single", "active", _naiv(2026, 10, 11, 22, 30), ("single", "youtube", "x1")),  # 00:30 Berlin Mo 12.10., aussen; waere er innen, tauchte youtube/x1 auf
            ("u6", "sub_kt_6", "pro", "active", _naiv(2026, 10, 8, 9), ("pro", "linkedin", "P01")),
            ("u2", "sub_kt_7", "pro", "active", _naiv(2026, 10, 4, 22, 30), ("pro", None, None)),   # 00:30 Berlin Mo 05.10., innen
        ]
        for nutzer, abo, tarif, status, an, kh in subs:
            await conn.execute(
                """INSERT INTO subscriptions (user_id, stripe_subscription_id, plan_type, status, created_at)
                   VALUES ($1, $2, $3, $4, $5)""", u[nutzer], abo, tarif, status, an)
            if kh:
                plan, s, c = kh
                meta = {k: v for k, v in (("utm_source", s), ("utm_content", c)) if v}
                assert await herkunft.kauf_festhalten(conn, u[nutzer], abo, plan, meta)
        # Ledger-Zeile ohne Stripe-Kennung: kein Kauf
        await conn.execute(
            "INSERT INTO subscriptions (user_id, stripe_subscription_id, plan_type, status, created_at) "
            "VALUES ($1, NULL, 'free', 'active', $2)", u["u4"], _naiv(2026, 10, 8, 10))
        return u
    finally:
        await conn.close()


class _Pool:
    """Einen Pool vorgeben, der immer dieselbe Verbindung reicht."""
    def __init__(self, conn):
        self.conn = conn

    def acquire(self):
        conn = self.conn

        class Ctx:
            async def __aenter__(self_):
                return conn

            async def __aexit__(self_, *a):
                return False
        return Ctx()


@pytest.fixture(scope="module")
def saat():
    ids = asyncio.run(_saeen())
    yield ids

    async def weg():
        conn = await asyncpg.connect(URL)
        try:
            await _aufraeumen(conn)
        finally:
            await conn.close()
    asyncio.run(weg())


def _zaehlung(ausser=()):
    async def lauf():
        conn = await asyncpg.connect(URL)
        try:
            von, bis, _ = ka.woche_grenzen("2026-W41")
            daten = await ka.lade(conn, von, bis, ausser)
            return daten, ka.zaehle(daten)
        finally:
            await conn.close()
    return asyncio.run(lauf())


# Hand gerechnet aus den Saatdaten oben (Woche 41, ohne das eigene Testkonto "eigen"):
#
#  Warteliste innen: lead1 (linkedin/P01, bestaetigt, Platz), lead2 (linkedin/p01),
#                    lead3 (tiktok, bestaetigt, Platz), lead6 (ohne).  lead4 und lead5 liegen
#                    eine halbe Stunde nach bzw. vor der Woche (Berliner Zeit).
#  Konten innen:     lead1, lead3, LEAD2, fremd (4). "zuspaet" liegt 10 Minuten dahinter.
#  Abos innen:       sub_kt_1, 2, 3, 4 (Add-on), 7 (naive Zeit 22:30 UTC = 00:30 Berlin am Montag).
#                    sub_kt_5 liegt 30 Minuten hinter der Woche, die Zeile ohne Stripe-Kennung zaehlt nie.
class TestGegenEchtesSchema:
    def test_warteliste(self, saat):
        _, z = _zaehlung(["eigen" + ENDE])
        assert sum(z.wartelisten.values()) == 4
        assert z.wartelisten[("linkedin", "p01")] == 2       # lead1 + lead2, P01 und p01 sind ein Kanal
        assert z.bestaetigt[("linkedin", "p01")] == 1        # lead1
        assert z.mit_platz[("linkedin", "p01")] == 1
        assert z.wartelisten[("tiktok", ka.OHNE)] == 1 and z.mit_platz[("tiktok", ka.OHNE)] == 1
        assert z.wartelisten[(ka.OHNE, ka.OHNE)] == 1        # lead6
        assert ("youtube", ka.OHNE) not in z.wartelisten     # lead4: 00:30 Berlin am Montag danach

    def test_registrierungen_und_erstkontakt(self, saat):
        _, z = _zaehlung(["eigen" + ENDE])
        assert z.registrierungen_gesamt == 4
        assert z.registrierungen[("linkedin", "p01")] == 1                 # lead1
        assert z.registrierungen[("warteliste", "mail-a")] == 1            # LEAD2
        assert z.registrierungen[(ka.OHNE, ka.OHNE)] == 2                  # lead3, fremd
        # Erstkontakt: lead1 -> linkedin/p01, LEAD2 -> linkedin/p01 (Gross/klein egal), lead3 -> tiktok
        assert z.erst_registrierungen[("linkedin", "p01")] == 2
        assert z.erst_registrierungen[("tiktok", ka.OHNE)] == 1
        assert z.nicht_auf_liste_reg == 1                                  # fremd

    def test_kaeufe(self, saat):
        _, z = _zaehlung(["eigen" + ENDE])
        # innen: 1, 2, 3, 4 (Add-on), 7 -> Kaeufe ohne Add-on: 1, 2, 3, 7 = 4
        assert z.kaeufe_gesamt == 4
        assert z.kaeufe[("linkedin", "p01")] == 1          # sub_kt_1
        assert z.kaeufe[("warteliste", "mail-a")] == 1     # sub_kt_2
        assert z.kaeufe[(ka.OHNE, ka.OHNE)] == 2           # sub_kt_3 (ohne Eintrag), sub_kt_7 (nur Tarif)
        # Pro nach Tarif: 1 (pro), 3 (Ledger pro), 7 (pro) = 3; sub_kt_2 ist laut Checkout 'agency'
        assert sum(z.kaeufe_pro.values()) == 3
        assert z.kaeufe_pro[("linkedin", "p01")] == 1 and z.kaeufe_pro[(ka.OHNE, ka.OHNE)] == 2
        # Erstkontakt: 1 -> linkedin/p01 (lead1), 2 -> linkedin/p01 (LEAD2), 7 -> tiktok (lead3)
        assert z.erst_kaeufe[("linkedin", "p01")] == 2
        assert z.erst_kaeufe[("tiktok", ka.OHNE)] == 1
        assert z.erst_kaeufe_pro[("linkedin", "p01")] == 1 and z.erst_kaeufe_pro[("tiktok", ka.OHNE)] == 1
        assert z.nicht_auf_liste_kauf == 1                 # sub_kt_3
        assert z.kaeufe_ohne_eintrag == 1                  # sub_kt_3

    def test_tarife_nehmen_die_checkout_metadaten_vor_dem_ledger(self, saat):
        _, z = _zaehlung(["eigen" + ENDE])
        assert z.tarife[("pro", "aktiv")] == 3             # 1, 3, 7
        assert z.tarife[("agency", "gekündigt")] == 1      # sub_kt_2: Ledger sagt pro, Checkout agency
        assert z.tarife[("agency_extra", "aktiv")] == 1    # Add-on bleibt sichtbar
        assert sum(z.tarife.values()) == 5

    def test_eigenes_testkonto_zaehlt_ohne_ausnahme_mit(self, saat):
        _, z = _zaehlung([])
        assert z.registrierungen_gesamt == 5               # plus "eigen"
        assert z.kaeufe_gesamt == 5                        # plus sub_kt_6
        assert z.kaeufe[("linkedin", "p01")] == 2

    def test_wochengrenzen_gelten_fuer_beide_zeitspaltentypen(self, saat):
        """timestamptz (Konten, Warteliste) und timestamp ohne Zeitzone (subscriptions)."""
        daten, _ = _zaehlung(["eigen" + ENDE])
        assert daten.db_zeitzone == "UTC"
        assert len(daten.kaeufe) == 5                      # sub_kt_7 innen, sub_kt_5 aussen

    def test_der_bericht_laeuft_vollstaendig_und_ohne_adresse(self, saat):
        async def lauf():
            conn = await asyncpg.connect(URL)
            try:
                return await ka.erstelle_bericht(
                    conn, "2026-W41", None, ["eigen" + ENDE],
                    jetzt=datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("Europe/Berlin")))
            finally:
                await conn.close()
        text = asyncio.run(lauf())
        assert "| linkedin | p01 | 2 | 1 | 1 | 1 | 1 |" in text
        assert "| Käufe (neue Abos, ohne Add-ons) | 4 | 2 | 2 |" in text
        assert "kanal-test" not in text and "@" not in text.replace("`", "")


def test_die_auswertung_aendert_nichts_und_die_datenbank_verweigert_schreiben(saat):
    async def lauf():
        conn = await asyncpg.connect(URL)
        try:
            vorher = await conn.fetchval("SELECT count(*) FROM users")
            von, bis, _ = ka.woche_grenzen("2026-W41")
            await ka.lade(conn, von, bis, [])
            nachher = await conn.fetchval("SELECT count(*) FROM users")
            # Die Datenbank selbst: in einer READ ONLY Transaktion scheitert jeder Insert.
            with pytest.raises(asyncpg.exceptions.ReadOnlySQLTransactionError):
                async with conn.transaction(readonly=True):
                    await conn.execute(
                        "INSERT INTO users (email, password_hash) VALUES ('x" + ENDE + "', 'x')")
            return vorher, nachher
        finally:
            await conn.close()
    vorher, nachher = asyncio.run(lauf())
    assert vorher == nachher


class TestSchreibstellenGegenEchtesSchema:
    def test_kauf_ist_idempotent_und_kaskadiert_mit_dem_konto(self, saat):
        async def lauf():
            conn = await asyncpg.connect(URL)
            try:
                uid = await _nutzer(conn, "kaskade", _utc(2026, 10, 6, 10))
                assert await herkunft.kauf_festhalten(conn, uid, "sub_kt_k", "pro", {"utm_source": "tiktok"})
                # Wiederholung (Webhook-Retry, verify-checkout daneben): keine zweite Zeile, kein Fehler
                assert await herkunft.kauf_festhalten(conn, uid, "sub_kt_k", "pro", {"utm_source": "youtube"})
                zeilen = await conn.fetch("SELECT utm_source FROM kauf_herkunft WHERE stripe_subscription_id='sub_kt_k'")
                assert [z["utm_source"] for z in zeilen] == ["tiktok"], "die erste Zeile gilt, die Wiederholung aendert nichts"
                await herkunft.registrierung_festhalten(_Pool(conn), uid, {"utm_source": "tiktok"})
                await herkunft.registrierung_festhalten(_Pool(conn), uid, {"utm_source": "youtube"})
                assert await conn.fetchval("SELECT count(*) FROM registrierung_herkunft WHERE user_id=$1", uid) == 1
                # Loeschantrag: das Konto geht, die Herkunft geht mit
                await conn.execute("DELETE FROM users WHERE id=$1", uid)
                assert await conn.fetchval("SELECT count(*) FROM kauf_herkunft WHERE stripe_subscription_id='sub_kt_k'") == 0
                assert await conn.fetchval("SELECT count(*) FROM registrierung_herkunft WHERE user_id=$1", uid) == 0
            finally:
                await conn.close()
        asyncio.run(lauf())

    def test_eine_zu_lange_herkunft_sprengt_nichts(self, saat):
        async def lauf():
            conn = await asyncpg.connect(URL)
            try:
                uid = await _nutzer(conn, "lang", _utc(2026, 10, 6, 10))
                ok = await herkunft.kauf_festhalten(conn, uid, "sub_kt_l", "pro", {"utm_source": "a" * 500})
                assert ok is True   # der Wert faellt im Filter weg, die Zeile bleibt
                assert await conn.fetchval("SELECT utm_source FROM kauf_herkunft WHERE stripe_subscription_id='sub_kt_l'") is None
                await conn.execute("DELETE FROM users WHERE id=$1", uid)
            finally:
                await conn.close()
        asyncio.run(lauf())
