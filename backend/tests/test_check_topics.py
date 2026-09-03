"""
Tests fuer die Themen-Erkennung von Compliance-Checks.

Die Beispiele sind echte Slug/Titel-Paare aus der Prod-DB (Stand 2026-08-04).
Der Aehnlichkeits-Waechter in `check_generator` hat sie alle durchgelassen,
weil ihre Slugs verschieden gebaut sind — im Bestand standen dadurch 19 Checks
fuer den Cookie-Ablehnen-Button und 16 fuer die Cookie-Wall-Alternative.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.check_topics import THEMEN, AUSSCHLUESSE, erkenne_thema


class TestEchteDuplikateWerdenErkannt:
    """Jede Gruppe stand so in der Datenbank — als getrennte Checks."""

    def _alle_gleich(self, paare):
        themen = {erkenne_thema(slug, titel) for slug, titel in paare}
        assert None not in themen, f"kein Thema erkannt für {paare}"
        assert len(themen) == 1, f"uneinheitlich: {themen}"
        return themen.pop()

    def test_umweltaussagen_drei_varianten(self):
        assert self._alle_gleich([
            ("green-claims-nachweis", "Fehlender Nachweis für Umweltaussagen (Green Claims Directive)"),
            ("green-claims-nachweisseite", "Fehlende Nachweisseite für Umwelt- und Nachhaltigkeitsaussagen"),
            ("greenwashing-nachweispflicht-umweltaussagen", "Fehlende Nachweise für Umweltaussagen (Greenwashing-Verbot)"),
        ]) == "umweltaussagen-nachweis"

    def test_verpackung_drei_varianten(self):
        assert self._alle_gleich([
            ("ppwr-verpackungsinformationen-online-shop", "Fehlende digitale Verpackungsinformationen gemäß EU-Verpackungsverordnung"),
            ("ppwr-verpackungsinformationen-produktseiten", "Fehlende Verpackungsinformationen auf Produktseiten (PPWR)"),
            ("ppwr-verpackungskennzeichnung", "Fehlende Verpackungsinformationen gemäß EU-Verpackungsverordnung (PPWR)"),
        ]) == "verpackung-informationen"

    def test_dreissig_tage_preis_drei_varianten(self):
        assert self._alle_gleich([
            ("omnibus-preisangabe-30-tage", "Fehlende Angabe des niedrigsten 30-Tage-Preises bei Preisreduzierung"),
            ("preisangabe-niedrigster-preis-30-tage", "Niedrigster Preis der letzten 30 Tage fehlt bei Preisreduzierung"),
            ("preisangabenverordnung-referenzpreis-30-tage", "Fehlende Angabe des niedrigsten Preises der letzten 30 Tage bei Preisreduzierung"),
        ]) == "preis-30-tage"

    def test_barrierefreiheitserklaerung_drei_varianten(self):
        assert self._alle_gleich([
            ("barrierefreiheitserklaerung-bfsg", "Barrierefreiheitserklärung fehlt"),
            ("bfsg-barrierefreiheit-erklaerung", "Barrierefreiheitserklärung fehlt (BFSG-Pflicht ab 28.06.2025)"),
            ("bfsg-erklaerung-barrierefreiheit", "Erklärung zur Barrierefreiheit fehlt"),
        ]) == "barrierefreiheitserklaerung"

    def test_ablehnen_button_vier_varianten(self):
        assert self._alle_gleich([
            ("cookie-banner-ablehnen-button", "Cookie-Banner ohne gleichwertigen 'Ablehnen'-Button"),
            ("cookie-banner-reject-button-prominence", "Cookie-Banner: Ablehnen-Button nicht gleichwertig prominent"),
            ("cookie-consent-reject-option", "Fehlende Möglichkeit zur Ablehnung aller nicht-essenziellen Cookies"),
            ("cookie-banner-one-click-reject", "Cookie-Banner ohne One-Click-Reject-Option"),
        ]) == "cookie-ablehnen-button"

    def test_affiliate_zwei_varianten(self):
        assert self._alle_gleich([
            ("affiliate-link-kennzeichnung", "Affiliate-Links nicht als Werbung gekennzeichnet"),
            ("affiliate-link-werbekennzeichnung", "Fehlende Werbekennzeichnung bei Affiliate-Links"),
        ]) == "affiliate-kennzeichnung"

    def test_analytics_zwei_varianten(self):
        assert self._alle_gleich([
            ("analytics-opt-out-pflicht", "Fehlende Opt-Out-Möglichkeit für Web-Analytics"),
            ("dsk-web-analytics-widerspruchsrecht", "Widerspruchsrecht gegen Web Analytics fehlt in Datenschutzerklärung"),
        ]) == "analytics-widerspruch"


class TestTrennschaerfe:
    """Was verschieden ist, muss verschieden bleiben — sonst frisst der Wächter echte Pflichten."""

    def test_kuendigungsbutton_ist_kein_bestellbutton(self):
        """
        Konkreter Fehlalarm der ersten Fassung: "abo" + "button" traf zu,
        obwohl ein Kündigungsbutton das Gegenteil eines Bestellbuttons ist.
        """
        bestellen = erkenne_thema("abo-button-zahlungspflicht-kennzeichnung",
                                  "Bestellbutton bei Abo-Modellen ohne Zahlungspflicht-Kennzeichnung")
        kuendigen = erkenne_thema("abo-kuendigung-button",
                                  "Fehlende einfache Abo-Kündigungsmöglichkeit")
        assert bestellen == "abo-bestellbutton"
        assert kuendigen == "abo-kuendigungsbutton"
        assert bestellen != kuendigen

    def test_ki_inhalte_sind_kein_chatbot(self):
        """AI Act Art. 50 (generierte Inhalte) ist nicht die Chatbot-Kennzeichnung."""
        inhalte = erkenne_thema("ai-generated-content-label",
                                "Fehlende Kennzeichnung KI-generierter Inhalte")
        chatbot = erkenne_thema("eu-ai-act-chatbot-kennzeichnung",
                                "Fehlende Kennzeichnung von KI-Chatbots/virtuellen Assistenten")
        assert inhalte == "ki-inhalte-kennzeichnung"
        assert chatbot == "chatbot-kennzeichnung"

    def test_newsletter_pflichten_bleiben_getrennt(self):
        anmeldung = erkenne_thema("newsletter-double-opt-in-formular",
                                  "Newsletter-Anmeldeformular ohne Double-Opt-In-Hinweis")
        abmeldung = erkenne_thema("newsletter-abmeldung-pflicht",
                                  "Fehlende Abmeldemöglichkeit für Newsletter")
        assert anmeldung == "newsletter-double-opt-in"
        assert abmeldung == "newsletter-abmeldung"

    def test_dsa_melde_und_transparenzbericht_getrennt(self):
        melde = erkenne_thema("dsa-meldemechanismus-rechtswidrige-inhalte",
                              "DSA-Meldemechanismus für rechtswidrige Inhalte fehlt")
        bericht = erkenne_thema("dsa-transparenzbericht-online-plattform",
                                "DSA-Transparenzbericht fehlt")
        assert melde == "dsa-meldemechanismus"
        assert bericht == "dsa-transparenzbericht"

    def test_fremde_pflicht_trifft_kein_thema(self):
        """Eine Pflicht ohne Eintrag darf kein fremdes Thema kapern."""
        assert erkenne_thema("wcag-22-konsistente-hilfe",
                             "Fehlende konsistente Hilfe-Funktion (WCAG 2.2)") is None
        assert erkenne_thema("widerrufsbutton",
                             "Widerrufsbutton fehlt (wird Pflicht ab 19.06.2026)") is None


class TestTabellenHygiene:
    def test_leere_eingabe(self):
        assert erkenne_thema("") is None
        assert erkenne_thema() is None

    def test_jedes_thema_hat_mindestens_zwei_gruppen(self):
        """Eine einzelne Begriffsgruppe wäre eine flache Stichwortliste — zu grob."""
        for thema, gruppen in THEMEN.items():
            assert len(gruppen) >= 2, f"{thema}: nur {len(gruppen)} Gruppe(n)"
            for gruppe in gruppen:
                assert gruppe, f"{thema}: leere Gruppe"

    def test_ausschluesse_verweisen_auf_existierende_themen(self):
        unbekannt = set(AUSSCHLUESSE) - set(THEMEN)
        assert not unbekannt, f"Ausschluss für unbekanntes Thema: {unbekannt}"

    def test_begriffe_sind_normalisiert(self):
        """Muster mit Umlaut oder Grossbuchstabe koennen nie treffen."""
        for thema, gruppen in THEMEN.items():
            for gruppe in gruppen:
                for begriff in gruppe:
                    assert begriff == begriff.lower(), f"{thema}: '{begriff}' nicht klein"
                    assert not set(begriff) & set("äöüß"), f"{thema}: '{begriff}' mit Umlaut"
