# -*- coding: utf-8 -*-
"""Die Wartelisten-Mails sehen aus wie complyo und tragen nichts Fremdes.

Bis zum 29.09.2026 kam die Bestaetigungsmail in Tailwind-Blau mit Verlauf,
gebaut aus div und flex (Outlook rendert beides nicht), und der Name aus dem
Formular ging unmaskiert ins HTML. Seitdem baut sie auf mail_layout.py auf,
nach der Vorlage einer Terminmail: Karten auf heller Flaeche, Logo, grosse
Schlagzeile, dunkles Band mit einem Knopf, Gruss, Kontakt.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("ENVIRONMENT", "test")

WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

LINK = "https://api.complyo.de/api/leads/waitlist/confirm?token=abc123&x=1"


@pytest.fixture
def gesendet():
    import email_service
    svc = email_service.EmailService()
    svc.admin_notify_email = "admin@example.org"
    liste = []

    def _fangen(to_email, subject, html_body, text_body, **_):
        liste.append({"an": to_email, "betreff": subject, "html": html_body, "text": text_body})
        return True

    svc._send_email = _fangen
    return svc, liste


class TestBestaetigungsmail:
    def test_baut_auf_dem_rahmen_auf(self, gesendet):
        import mail_layout
        svc, liste = gesendet
        assert svc.send_waitlist_confirmation("a@example.org", "Anna", LINK)
        html = liste[0]["html"]
        assert mail_layout.LOGO_URL in html, "Logo fehlt"
        assert "Bitte bestätige deine Anmeldung" in html
        assert "Beste Grüße" in html and "Kontakt" in html
        assert mail_layout.AKZENT in html, "Knopf nicht in der Logofarbe"

    def test_kein_altes_layout(self, gesendet):
        """Outlook kennt weder flex noch Verlaeufe; #2563eb ist Tailwind-Blau."""
        svc, liste = gesendet
        svc.send_waitlist_confirmation("a@example.org", "", LINK)
        html = liste[0]["html"].lower()
        for verboten in ("display:flex", "display:inline-flex", "linear-gradient", "#2563eb"):
            assert verboten not in html, f"{verboten} steht wieder in der Mail"

    def test_name_wird_maskiert(self, gesendet):
        svc, liste = gesendet
        svc.send_waitlist_confirmation(
            "a@example.org", '<a href="https://boese.example">Konto gesperrt</a>', LINK)
        html = liste[0]["html"]
        assert "boese.example\">" not in html and '<a href="https://boese.example' not in html
        assert "&lt;a href=" in html

    def test_link_kommt_heil_an(self, gesendet):
        svc, liste = gesendet
        svc.send_waitlist_confirmation("a@example.org", "", LINK)
        html, text = liste[0]["html"], liste[0]["text"]
        # Im HTML maskiert, im Klartext woertlich: beide oeffnen dieselbe Adresse.
        assert LINK.replace("&", "&amp;") in html
        assert LINK in text
        assert html.count(LINK.replace("&", "&amp;")) >= 2, "Knopf und Ersatzlink"

    def test_kein_doppeltes_complyo_de(self, gesendet):
        svc, liste = gesendet
        svc.send_waitlist_confirmation("a@example.org", "", LINK)
        for teil in (liste[0]["html"], liste[0]["text"]):
            assert "complyo.de / complyo.de" not in teil


class TestInterneMeldung:
    def test_maskiert_angaben(self, gesendet):
        svc, liste = gesendet
        svc.send_waitlist_admin_notification(
            "a@example.org", "<script>x</script>", "", "early-access", "", "pro-89")
        html = liste[0]["html"]
        assert "<script>x</script>" not in html
        assert "&lt;script&gt;" in html

    def test_bestaetigung_zeigt_platz_gross(self, gesendet):
        svc, liste = gesendet
        svc.send_waitlist_admin_notification(
            "a@example.org", "", "", "early-access", "", "pro-89", True, 7)
        assert "Platz 7" in liste[0]["betreff"]
        assert re.search(r"font-size:36px[^>]*>Platz 7<", liste[0]["html"])


class TestAnbieterangaben:
    def test_kontakt_wie_im_impressum(self):
        """Die Kontaktkarte darf dem Impressum nicht widersprechen."""
        import mail_layout
        ts = open(os.path.join(WURZEL, "landing-react", "src", "lib", "anbieter.ts"),
                  encoding="utf-8").read()

        def feld(name):
            t = re.search(name + r":\s*'([^']*)'", ts)
            assert t, f"{name} nicht in anbieter.ts gefunden"
            return t.group(1)

        a = mail_layout.ANBIETER
        assert a["name"] == feld("name")
        assert a["geschaeftsbezeichnung"] == feld("geschaeftsbezeichnung")
        assert a["strasse"] == feld("strasse")
        assert a["plz_ort"] == feld("plz") + " " + feld("ort")
        assert a["email"] == feld("email")
