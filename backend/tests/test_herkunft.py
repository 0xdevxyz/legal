# -*- coding: utf-8 -*-
"""Herkunft von Registrierung und Kauf kommt in der Datenbank an.

Anlass (07.10.2026): Die utm-Werte reisten bis in die Stripe-Metadaten, der
Webhook schrieb sie nicht in die Datenbank, die Registrierung schrieb sie
nirgends hin. "Kaeufe je Kanal" war damit nur ueber einen Stripe-Schluessel
auswertbar. Diese Tests halten die Strecke fest, ohne eine Datenbank zu
brauchen; `test_kanal_auswertung_db.py` prueft dieselben Schreibstellen gegen
ein echtes Schema.
"""
import ast
import asyncio
import os
import re

import pytest

os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")

import herkunft  # noqa: E402
import stripe_routes  # noqa: E402

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------

class TestFilter:
    def test_nur_die_fuenf_utm_schluessel(self):
        roh = {"utm_source": "linkedin", "utm_content": "P01", "user_id": "7", "plan": "agency",
               "domain": "x.de", "modules": "[]"}
        assert herkunft.bereinige(roh) == {"utm_source": "linkedin", "utm_content": "P01"}

    def test_herkunft_kann_user_und_plan_nie_liefern(self):
        """Die Metadaten tragen user_id und plan, auf denen die Freischaltung haengt."""
        for schluessel in herkunft.SCHLUESSEL:
            assert schluessel.startswith("utm_")
        assert herkunft.bereinige({"user_id": "1", "plan": "agency"}) == {}

    def test_boese_werte_fallen_weg(self):
        roh = {"utm_source": "tiktok", "utm_medium": "<script>", "utm_campaign": "x" * 121,
               "utm_term": 42, "utm_content": "mit leerzeichen"}
        assert herkunft.bereinige(roh) == {"utm_source": "tiktok"}

    @pytest.mark.parametrize("wert", ["linkedin\n", "linkedin\r\n", "\nlinkedin", "a\nb"])
    def test_zeilenumbruch_im_wert_wird_abgelehnt(self, wert):
        # `$` liesse in Python ein Zeilenende am Ende durch; fullmatch nicht.
        assert herkunft.bereinige({"utm_source": wert}) == {}

    def test_grenzen_der_laenge(self):
        assert herkunft.bereinige({"utm_source": "a" * 120}) == {"utm_source": "a" * 120}
        assert herkunft.bereinige({"utm_source": "a" * 121}) == {}
        assert herkunft.bereinige({"utm_source": ""}) == {}

    @pytest.mark.parametrize("roh", [None, "utm_source=li", ["utm_source"], 7, b"x", ("a",)])
    def test_kein_dict_ergibt_nichts(self, roh):
        assert herkunft.bereinige(roh) == {}

    def test_dict_unterklasse_wie_ein_stripe_objekt(self):
        class StripeNah(dict):
            pass
        assert herkunft.bereinige(StripeNah(utm_source="youtube")) == {"utm_source": "youtube"}

    def test_dieselbe_positivliste_wie_der_kaufweg_aus_pr_10(self):
        """PR #10 filtert beim Checkout mit eigener Liste und eigenem Muster. Beide
        muessen gleich bleiben, sonst schreibt der Checkout Werte, die die Datenbank
        ablehnt (oder umgekehrt). Der Test greift, sobald #10 gemergt ist."""
        if not hasattr(stripe_routes, "_HERKUNFT_SCHLUESSEL"):
            pytest.skip("PR #10 ist noch nicht in diesem Stand")
        assert tuple(stripe_routes._HERKUNFT_SCHLUESSEL) == herkunft.SCHLUESSEL
        assert stripe_routes._HERKUNFT_MUSTER.pattern.strip("^$") == herkunft._MUSTER.pattern


# ---------------------------------------------------------------------------
# Schreibstellen mit falscher Verbindung
# ---------------------------------------------------------------------------

class FalscheVerbindung:
    def __init__(self, existiert=False, scheitert_bei=None):
        self.ausgefuehrt = []   # (sql, args)
        self.existiert = existiert
        self.scheitert_bei = scheitert_bei

    async def execute(self, sql, *args):
        self.ausgefuehrt.append((" ".join(sql.split()), args))
        if self.scheitert_bei and self.scheitert_bei in sql:
            raise RuntimeError('relation "kauf_herkunft" does not exist')
        return "OK"

    async def fetchrow(self, sql, *args):
        return {"id": 1} if self.existiert and "FROM subscriptions" in sql else None


class FalscherPool:
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


class TestRegistrierung:
    def test_schreibt_die_herkunft_mit_allen_fuenf_werten(self):
        conn = FalscheVerbindung()
        ok = asyncio.run(herkunft.registrierung_festhalten(
            FalscherPool(conn), "12",
            {"utm_source": "linkedin", "utm_medium": "social", "utm_campaign": "ea100",
             "utm_content": "P01", "utm_term": "bfsg", "plan": "agency"}))
        assert ok is True
        sql, args = conn.ausgefuehrt[0]
        assert "INSERT INTO registrierung_herkunft" in sql
        assert "ON CONFLICT (user_id) DO NOTHING" in sql
        assert args == (12, "linkedin", "social", "ea100", "P01", "bfsg")

    def test_ohne_herkunft_wird_nichts_geschrieben(self):
        conn = FalscheVerbindung()
        for leer in (None, {}, {"plan": "pro"}, {"utm_source": "<x>"}):
            assert asyncio.run(herkunft.registrierung_festhalten(FalscherPool(conn), 1, leer)) is False
        assert conn.ausgefuehrt == []

    def test_ein_datenbankfehler_bricht_die_registrierung_nicht(self):
        conn = FalscheVerbindung(scheitert_bei="registrierung_herkunft")
        ok = asyncio.run(herkunft.registrierung_festhalten(
            FalscherPool(conn), 3, {"utm_source": "tiktok"}))
        assert ok is False   # kein raise


class TestKauf:
    def test_schreibt_tarif_und_herkunft(self):
        conn = FalscheVerbindung()
        ok = asyncio.run(herkunft.kauf_festhalten(
            conn, "5", "sub_123", "pro",
            {"user_id": "5", "plan": "pro", "utm_source": "linkedin", "utm_content": "P01"}))
        assert ok is True
        sql, args = conn.ausgefuehrt[0]
        assert "INSERT INTO kauf_herkunft" in sql
        assert "ON CONFLICT (stripe_subscription_id) DO NOTHING" in sql
        # Reihenfolge der Spalten: Abo, Konto, Tarif, source, medium, campaign, content, term
        assert args == ("sub_123", 5, "pro", "linkedin", None, None, "P01", None)

    def test_auch_ohne_utm_bleibt_der_tarif_erhalten(self):
        conn = FalscheVerbindung()
        asyncio.run(herkunft.kauf_festhalten(conn, 5, "sub_9", "agency", {"plan": "agency"}))
        assert conn.ausgefuehrt[0][1] == ("sub_9", 5, "agency", None, None, None, None, None)

    @pytest.mark.parametrize("plan", [None, "", "Pro", "pro; DROP", "x" * 21, 5])
    def test_unbrauchbarer_tarif_wird_zu_null(self, plan):
        conn = FalscheVerbindung()
        asyncio.run(herkunft.kauf_festhalten(conn, 5, "sub_1", plan, {}))
        assert conn.ausgefuehrt[0][1][2] is None

    def test_ohne_abo_kennung_wird_nichts_geschrieben(self):
        conn = FalscheVerbindung()
        assert asyncio.run(herkunft.kauf_festhalten(conn, 5, None, "pro", {})) is False
        assert conn.ausgefuehrt == []

    def test_ein_datenbankfehler_wird_geschluckt(self):
        conn = FalscheVerbindung(scheitert_bei="kauf_herkunft")
        assert asyncio.run(herkunft.kauf_festhalten(conn, 5, "sub_1", "pro", {})) is False


def test_insert_spalten_stehen_in_der_migration():
    """Wer eine Spalte im INSERT umbenennt, ohne die Migration anzufassen, schreibt
    ins Leere; `kauf_festhalten` meldet das nur als Warnung im Log."""
    pfad = os.path.join(BACKEND, "alembic", "versions", "20261007_0037_kanal_herkunft.py")
    migration = open(pfad, encoding="utf-8").read()
    quelle = open(os.path.join(BACKEND, "herkunft.py"), encoding="utf-8").read()
    for tabelle in ("registrierung_herkunft", "kauf_herkunft"):
        assert f'"{tabelle}"' in migration
        m = re.search(rf"INSERT INTO {tabelle}\s*\(([^)]*)\)", quelle)
        spalten = [s.strip() for s in m.group(1).split(",")]
        for spalte in spalten:
            if spalte.startswith("utm_"):
                assert spalte in herkunft.SCHLUESSEL
            else:
                assert f'"{spalte}"' in migration, f"{tabelle}.{spalte} fehlt in Migration 0037"
    # und die fuenf utm-Spalten kommen aus derselben Liste
    assert re.search(r'_UTM = \(("utm_\w+",?\s*){5}\)', migration)
    for s in herkunft.SCHLUESSEL:
        assert f'"{s}"' in migration


def test_migration_haengt_an_der_richtigen_revision():
    """Genau ein Kopf, und er ist 0037. Zwei Koepfe laessen `alembic upgrade head` scheitern."""
    pytest.importorskip("alembic")
    from alembic.script import ScriptDirectory
    skripte = ScriptDirectory(os.path.join(BACKEND, "alembic"))
    assert skripte.get_heads() == ["0037_kanal_herkunft"], skripte.get_heads()


# ---------------------------------------------------------------------------
# Verdrahtung: Webhook, verify-checkout, Registrierung
# ---------------------------------------------------------------------------

def _funktion(modul_datei, name):
    quelle = open(os.path.join(BACKEND, modul_datei), encoding="utf-8").read()
    for knoten in ast.walk(ast.parse(quelle)):
        if isinstance(knoten, (ast.AsyncFunctionDef, ast.FunctionDef)) and knoten.name == name:
            return ast.get_source_segment(quelle, knoten)
    raise AssertionError(f"{name} nicht gefunden")


class TestVerdrahtung:
    def test_webhook_haelt_den_kauf_nach_der_freischaltung_fest(self):
        text = _funktion("stripe_routes.py", "handle_checkout_completed")
        assert "kauf_festhalten(conn, user_id, subscription_id, plan, session['metadata'])" in text
        assert text.index("_apply_plan_activation(") < text.index("kauf_festhalten(")

    def test_verify_checkout_haelt_den_kauf_fest(self):
        text = _funktion("stripe_routes.py", "verify_checkout_session")
        assert "kauf_festhalten(conn, user_id, subscription_id, plan, _meta)" in text
        assert text.index("_apply_plan_activation(") < text.index("kauf_festhalten(")

    def test_registrierung_nimmt_herkunft_an_und_schreibt_sie(self):
        import auth_routes
        assert "herkunft" in auth_routes.RegisterRequest.model_fields
        assert auth_routes.RegisterRequest.model_fields["herkunft"].default is None
        text = _funktion("auth_routes.py", "register")
        assert "registrierung_festhalten(db_pool, user['id'], body.herkunft)" in text
        # nach dem Anlegen des Kontos, nicht davor
        assert text.index("auth_service.register_user(") < text.index("registrierung_festhalten(")

    def test_registrierung_ohne_herkunft_bleibt_gueltig(self):
        import auth_routes
        body = auth_routes.RegisterRequest(email="a@b.de", password="x", full_name="N")
        assert body.herkunft is None
        mit = auth_routes.RegisterRequest(email="a@b.de", password="x", full_name="N",
                                          herkunft={"utm_source": "linkedin"})
        assert mit.herkunft == {"utm_source": "linkedin"}


# ---------------------------------------------------------------------------
# Verhalten des Webhooks (falsche Verbindung statt Datenbank)
# ---------------------------------------------------------------------------

@pytest.fixture
def webhook(monkeypatch):
    """Webhook-Aufruf gegen eine aufzeichnende Verbindung."""
    def lauf(conn, metadata, subscription="sub_777"):
        monkeypatch.setattr(stripe_routes.db_service, "pool", FalscherPool(conn))
        session = {"metadata": metadata, "customer": "cus_1", "subscription": subscription}
        asyncio.run(stripe_routes.handle_checkout_completed(session))
    return lauf


META = {"user_id": "42", "plan": "pro", "modules": "[]",
        "utm_source": "linkedin", "utm_medium": "social", "utm_campaign": "ea100", "utm_content": "P01"}


def _kauf_zeilen(conn):
    return [(s, a) for s, a in conn.ausgefuehrt if "INSERT INTO kauf_herkunft" in s]


class TestWebhookVerhalten:
    def test_neuer_kauf_schreibt_abo_und_herkunft(self, webhook):
        conn = FalscheVerbindung(existiert=False)
        webhook(conn, META)
        sqls = [s for s, _ in conn.ausgefuehrt]
        assert any("INSERT INTO subscriptions" in s for s in sqls)
        zeilen = _kauf_zeilen(conn)
        assert len(zeilen) == 1
        assert zeilen[0][1] == ("sub_777", 42, "pro", "linkedin", "social", "ea100", "P01", None)
        # die Herkunft wird erst NACH der Freischaltung geschrieben
        erste = next(i for i, s in enumerate(sqls) if "INSERT INTO subscriptions" in s)
        letzte = next(i for i, s in enumerate(sqls) if "INSERT INTO kauf_herkunft" in s)
        assert erste < letzte

    def test_kauf_wird_auch_festgehalten_wenn_das_abo_schon_im_ledger_steht(self, webhook):
        """`customer.subscription.created` legt die Zeile in `subscriptions` an, bevor
        `checkout.session.completed` ankommt. Dann meldet die Freischaltung False,
        und der Kauf waere ohne diesen Aufruf nie eingetragen worden."""
        conn = FalscheVerbindung(existiert=True)
        webhook(conn, META)
        assert not any("INSERT INTO subscriptions" in s for s, _ in conn.ausgefuehrt)
        assert len(_kauf_zeilen(conn)) == 1

    def test_ein_fehler_beim_festhalten_laesst_den_webhook_nicht_scheitern(self, webhook):
        """Sonst wiederholt Stripe tagelang ein Ereignis, dessen Freischaltung steht."""
        conn = FalscheVerbindung(scheitert_bei="INSERT INTO kauf_herkunft")
        webhook(conn, META)   # kein raise
        assert any("INSERT INTO subscriptions" in s for s, _ in conn.ausgefuehrt)

    def test_kauf_ohne_utm_traegt_nur_den_tarif(self, webhook):
        conn = FalscheVerbindung()
        webhook(conn, {"user_id": "42", "plan": "agency", "modules": "[]"})
        assert _kauf_zeilen(conn)[0][1] == ("sub_777", 42, "agency", None, None, None, None, None)

    def test_fremde_metadaten_gelangen_nicht_in_die_herkunft(self, webhook):
        conn = FalscheVerbindung()
        webhook(conn, {**META, "utm_source": "<img src=x>", "domain": "kunde.de"})
        args = _kauf_zeilen(conn)[0][1]
        assert args[3] is None          # utm_source verworfen
        assert "kunde.de" not in args   # domain nie in die Herkunft
