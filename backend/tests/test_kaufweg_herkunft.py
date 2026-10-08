"""Ein Kauf traegt seinen Kanal bis in die Stripe-Metadaten.

Anlass (28.09.2026): Die Entscheidungsregel nach Woche 45 des Launchplans
zaehlt Kaeufe je Kanal (LinkedIn, TikTok, Instagram, Suche). Die Warteliste
speicherte utm-Parameter seit September, der Kaufweg nicht: "Pro buchen"
fuehrte nach app.complyo.de/register ohne Herkunft, und create-checkout
kannte kein Feld dafuer. Ein Kauf war keinem Kanal zuzuordnen.

Die Strecke: Landing haengt utm_* an den Buchen-Knopf, die Registrierung
merkt sie sich fuer die Sitzung und gibt sie als `herkunft` mit,
create-checkout filtert sie und schreibt sie in die Metadaten von Sitzung
und Abo.
"""

import ast
import os

import pytest

# Wie test_checkout_plan_validation: stripe_routes verweigert den Import ohne
# Webhook-Geheimnis, im Test genuegt ein Platzhalter.
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")

import stripe_routes  # noqa: E402
from stripe_routes import _herkunft_metadaten  # noqa: E402

WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestFilter:
    def test_nur_bekannte_schluessel(self):
        roh = {"utm_source": "linkedin", "utm_content": "P01", "user_id": "1", "plan": "agency"}
        assert _herkunft_metadaten(roh) == {"utm_source": "linkedin", "utm_content": "P01"}

    def test_boese_werte_fallen_weg(self):
        roh = {
            "utm_source": "tiktok",
            "utm_medium": "<script>",
            "utm_campaign": "x" * 121,
            "utm_term": 42,
        }
        assert _herkunft_metadaten(roh) == {"utm_source": "tiktok"}

    @pytest.mark.parametrize("roh", [None, "utm_source=li", ["utm_source"], 7])
    def test_kein_dict_ergibt_nichts(self, roh):
        assert _herkunft_metadaten(roh) == {}

    def test_herkunft_kann_plan_und_nutzer_nicht_ueberschreiben(self):
        """Die Metadaten tragen user_id und plan, auf denen die Freischaltung
        haengt. Die Herkunft darf diese Schluessel nie liefern."""
        for schluessel in stripe_routes._HERKUNFT_SCHLUESSEL:
            assert schluessel.startswith("utm_")


class TestVerdrahtung:
    def test_checkout_request_kennt_herkunft(self):
        assert "herkunft" in stripe_routes.CheckoutRequest.model_fields

    def test_create_checkout_schreibt_herkunft_in_die_metadaten(self):
        quelle = open(stripe_routes.__file__, encoding="utf-8").read()
        baum = ast.parse(quelle)
        funktion = next(
            n for n in ast.walk(baum)
            if isinstance(n, ast.AsyncFunctionDef) and n.name == "create_checkout_session"
        )
        text = ast.get_source_segment(quelle, funktion)
        assert "checkout_metadata.update(_herkunft_metadaten(request.herkunft))" in text
        # und die Metadaten gehen an Sitzung UND Abo, sonst fehlt der Kanal
        # bei jeder Verlaengerung
        assert "metadata=checkout_metadata" in text
        assert "'metadata': checkout_metadata" in text


def _datei(relpfad):
    pfad = os.path.join(WURZEL, relpfad)
    if not os.path.exists(pfad):
        pytest.skip(f"{relpfad} fehlt, ganzes Repo mounten (scripts/tests-lokal.sh)")
    return open(pfad, encoding="utf-8").read()


class TestOberflaeche:
    def test_registrierung_gibt_herkunft_mit(self):
        for rel in (
            "dashboard-react/src/app/register/page.tsx",
            "dashboard-react/src/components/SocialLoginButtons.tsx",
        ):
            text = _datei(rel)
            assert "herkunft: gemerkteHerkunft()" in text, f"{rel} gibt keine Herkunft an create-checkout"

    def test_buchen_knoepfe_tragen_herkunft(self):
        text = _datei("landing-react/src/components/saas-landing/PricingSection.tsx")
        assert "mitHerkunft(plan.href, herkunft)" in text

    def test_keine_sepa_zusage_auf_der_preisseite(self):
        """SEPA ist im Live-Konto nicht freigeschaltet (14.09.2026). Die Zeile
        unter der Preistabelle versprach es trotzdem."""
        text = _datei("landing-react/src/components/saas-landing/PricingSection.tsx")
        assert "SEPA" not in text
