"""
Checkout-Härtung: kein stiller Fallback auf den Pro-Preis
=========================================================

Befund (2026-08-03): ``POST /api/stripe/create-checkout`` nahm jeden beliebigen
Plan-String entgegen. Fand sich dazu keine Price-ID, fiel der Code still auf
``STRIPE_PRICES["pro_monthly"]`` zurück — der Kunde bezahlte 49 €/Monat für
einen Plan, den er nie gewählt hatte. Die Registrierung sendete per
Voreinstellung ``plan: 'complete'``, ``SocialLoginButtons`` sendete
``plan: 'ki'``; beide liefen genau in diesen Fallback und landeten anschließend
als ``plan_type`` in der Datenbank, wo ``PLAN_WEBSITES_MAX.get(plan, 999)``
ihnen ein 999er-Domainkontingent gab.

Zwei weitere Löcher im selben Pfad: ``stripe_routes`` fasste ``user_modules``
nie an (wer eine Einzelsäule für 19 € kaufte, blieb ausgesperrt), und die
Checkout-Menge stand fest auf 1, egal wie viele Säulen gewählt waren.

Zwei Ebenen, analog zu test_addon_plan_escalation.py:
1. Statische Wächter über den Quelltext — brauchen weder fastapi noch DB.
2. Unit-Tests der reinen Hilfsfunktionen, sofern das Modul importierbar ist.
"""
import os
import re

import pytest

_STRIPE_FILE = os.path.join(os.path.dirname(__file__), "..", "stripe_routes.py")


def _quelltext():
    with open(_STRIPE_FILE, encoding="utf-8") as fh:
        return fh.read()


def _quelltext_ohne_kommentare():
    """Kommentare/Docstrings dürfen die statischen Wächter nicht triggern."""
    src = _quelltext()
    src = re.sub(r'"""(?:.|\n)*?"""', "", src)
    return "\n".join(re.sub(r"#.*$", "", z) for z in src.splitlines())


class TestStatischeWaechter:
    """Der Quelltext darf nicht in die alten Muster zurückfallen."""

    def test_kein_stiller_preis_fallback(self):
        src = _quelltext_ohne_kommentare()
        assert 'STRIPE_PRICES["pro_monthly"]' not in src, (
            "Der stille Fallback auf den Pro-Preis ist zurück — unbekannte Pläne "
            "würden wieder als 49-€-Abo abgerechnet."
        )

    def test_planliste_existiert_und_ist_eng(self):
        src = _quelltext_ohne_kommentare()
        assert "SELF_SERVE_PLANS" in src, "Plan-Whitelist fehlt."
        treffer = re.search(r"SELF_SERVE_PLANS\s*=\s*\{([^}]*)\}", src)
        assert treffer, "SELF_SERVE_PLANS ist kein einfaches Set-Literal mehr."
        eintraege = treffer.group(1)
        for verboten in ("expert", "update", "complete", "ki", "ai", "free"):
            assert f"'{verboten}'" not in eintraege, (
                f"Plan {verboten!r} darf nicht per Selbstbedienung buchbar sein."
            )
        for erlaubt in ("single", "pro", "agency"):
            assert f"'{erlaubt}'" in eintraege, f"Plan {erlaubt!r} fehlt in der Whitelist."

    def test_unbekannter_plan_wird_abgelehnt(self):
        src = _quelltext_ohne_kommentare()
        assert "not in SELF_SERVE_PLANS" in src, (
            "Der Checkout prüft den Plan nicht mehr gegen die Whitelist."
        )

    def test_saeulen_werden_freigeschaltet(self):
        # Rohtext: der INSERT steht in einem Triple-Quote-String, den die
        # Kommentarfilterung mit entfernen würde.
        src = _quelltext()
        assert "INSERT INTO user_modules" in src, (
            "stripe_routes schaltet keine Säulen frei — bezahlte Einzelmodule "
            "bleiben gesperrt."
        )

    def test_menge_haengt_an_den_gewaehlten_saeulen(self):
        src = _quelltext_ohne_kommentare()
        assert "len(checkout_modules)" in src, (
            "Die Checkout-Menge ist wieder fix — vier gebuchte Säulen würden "
            "als eine abgerechnet."
        )

    def test_kein_unbegrenztes_domainkontingent_als_default(self):
        src = _quelltext_ohne_kommentare()
        assert "PLAN_WEBSITES_MAX.get(plan, 999)" not in src, (
            "Unbekannte Pläne bekämen wieder 999 Domains."
        )

    def test_http_fehler_werden_nicht_zu_500ern(self):
        src = _quelltext_ohne_kommentare()
        assert "except HTTPException:" in src, (
            "400er aus dem Checkout werden vom generischen Handler wieder in "
            "500er verwandelt."
        )

    def test_keine_internen_details_in_der_fehlerantwort(self):
        src = _quelltext_ohne_kommentare()
        checkout = src[src.index("async def create_checkout_session"):]
        checkout = checkout[: checkout.index("async def create_portal_session")]
        assert "detail=str(e)" not in checkout, (
            "Interne Fehlermeldungen gehen wieder an den Client."
        )


# ── Funktionale Ebene ────────────────────────────────────────────────────────
# stripe_routes prüft beim Import auf die Stripe-Secrets; ohne sie ist das Modul
# nicht ladbar. Fehlt es, bleiben die statischen Wächter oben als Absicherung.
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")

try:
    import stripe_routes
except Exception as fehler:  # pragma: no cover
    stripe_routes = None
    _import_fehler = repr(fehler)


needs_module = pytest.mark.skipif(
    stripe_routes is None, reason="stripe_routes nicht importierbar"
)


@needs_module
class TestSaeulenAufloesung:
    def test_pro_schaltet_alle_saeulen_frei(self):
        assert sorted(stripe_routes._resolve_modules("pro")) == sorted(
            stripe_routes.ALL_MODULES
        )

    def test_agency_schaltet_alle_saeulen_frei(self):
        assert sorted(stripe_routes._resolve_modules("agency")) == sorted(
            stripe_routes.ALL_MODULES
        )

    def test_single_nimmt_nur_die_gewaehlten_saeulen(self):
        assert stripe_routes._resolve_modules("single", ["cookie"]) == ["cookie"]

    def test_single_verwirft_erfundene_saeulen(self):
        assert stripe_routes._resolve_modules("single", ["cookie", "quatsch"]) == [
            "cookie"
        ]

    def test_single_ohne_auswahl_bleibt_leer(self):
        assert stripe_routes._resolve_modules("single", []) == []

    def test_free_schaltet_nichts_frei(self):
        assert stripe_routes._resolve_modules("free") == []


@needs_module
class TestMetadataDekodierung:
    def test_liest_die_saeulen_aus_dem_json_string(self):
        assert stripe_routes._parse_modules_metadata('["cookie", "monitoring"]') == [
            "cookie",
            "monitoring",
        ]

    def test_leerer_wert_ergibt_leere_liste(self):
        assert stripe_routes._parse_modules_metadata(None) == []
        assert stripe_routes._parse_modules_metadata("") == []

    def test_kaputtes_json_wirft_nicht(self):
        assert stripe_routes._parse_modules_metadata("{kaputt") == []

    def test_falscher_typ_wirft_nicht(self):
        assert stripe_routes._parse_modules_metadata('{"a": 1}') == []

    def test_nicht_string_eintraege_fliegen_raus(self):
        assert stripe_routes._parse_modules_metadata('["cookie", 5, null]') == ["cookie"]


@needs_module
class TestPlanKontingente:
    def test_unbekannter_plan_bekommt_kein_freibrief_kontingent(self):
        assert stripe_routes.PLAN_WEBSITES_MAX.get("complete", 1) == 1
        assert stripe_routes.PLAN_WEBSITES_MAX.get("ki", 1) == 1

    def test_bekannte_plaene_stimmen_mit_dem_tarifmodell_ueberein(self):
        assert stripe_routes.PLAN_WEBSITES_MAX["free"] == 1
        assert stripe_routes.PLAN_WEBSITES_MAX["single"] == 1
        assert stripe_routes.PLAN_WEBSITES_MAX["pro"] == 1
        assert stripe_routes.PLAN_WEBSITES_MAX["agency"] == 25
