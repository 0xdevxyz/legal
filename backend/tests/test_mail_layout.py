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

    def test_keine_zustandsbehauptung(self, gesendet):
        """ "DSGVO-konform verarbeitet" behauptet einen Zustand, den niemand
        gemessen hat. Die Mail nennt stattdessen die Rechtsgrundlage und das
        Widerrufsrecht, wie in PR #10 entschieden."""
        svc, liste = gesendet
        svc.send_waitlist_confirmation("a@example.org", "", LINK)
        for teil in (liste[0]["html"], liste[0]["text"]):
            assert "DSGVO-konform" not in teil
            assert "jederzeit widerrufen" in teil

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


class TestKontomails:
    """Bestaetigung, Passwort, Loeschankuendigung: gleicher Rahmen, aber nur
    der eine Link, um den es geht. Wer eine Passwortmail bekommt, die er nicht
    angefordert hat, soll nichts anderes anklicken koennen."""

    URL = "https://app.complyo.de/passwort?token=xyz&a=1"

    def _alle(self, svc):
        svc.sende_konto_bestaetigung("k@example.org", "<i>Kai</i>", self.URL)
        svc.sende_passwort_zuruecksetzen("k@example.org", "<i>Kai</i>", self.URL, 30)
        svc.sende_loeschankuendigung("k@example.org", "<i>Kai</i>", 30, self.URL)

    def test_rahmen_und_ein_einziger_link(self, gesendet):
        import mail_layout
        svc, liste = gesendet
        self._alle(svc)
        assert len(liste) == 3
        for m in liste:
            html = m["html"]
            assert mail_layout.LOGO_URL in html, m["betreff"]
            ziele = set(re.findall(r'href="([^"]+)"', html))
            assert ziele == {self.URL.replace("&", "&amp;")}, (
                f"{m['betreff']}: weitere Links {ziele}"
            )

    def test_name_maskiert(self, gesendet):
        svc, liste = gesendet
        self._alle(svc)
        for m in liste:
            assert "<i>Kai</i>" not in m["html"]
            assert "&lt;i&gt;Kai" in m["html"]


# ---------------------------------------------------------------------------
# Die uebrigen Kundenmails (29.09.2026 umgestellt)
# ---------------------------------------------------------------------------

ALTES_LAYOUT = ("linear-gradient", "display:flex", "display: flex", "display:inline-flex",
                "#667eea", "#6366f1", "#2563eb")


def _neues_layout(html: str):
    import mail_layout
    assert mail_layout.LOGO_URL in html
    klein = html.lower()
    for alt in ALTES_LAYOUT:
        assert alt not in klein, f"{alt} steht noch in der Mail"


class TestLeadMails:
    def test_verifizierung(self, gesendet):
        svc, liste = gesendet
        svc.send_verification_email("l@example.org", "<b>Lea</b>", "tok123")
        html = liste[0]["html"]
        _neues_layout(html)
        assert "&lt;b&gt;Lea" in html and "<b>Lea</b>" not in html
        assert "verify-email?token=tok123" in html
        assert "24 Stunden" in html, "Gueltigkeit steht in database_service (24 h)"

    def test_report_erfindet_keine_werte(self, gesendet, monkeypatch):
        import email_service
        svc, liste = gesendet
        monkeypatch.setattr(email_service.pdf_generator, "generate_compliance_report",
                            lambda daten, lead: b"%PDF-1.4 probe")
        svc.send_compliance_report("l@example.org", "Lea", "kein json")
        html, text = liste[0]["html"], liste[0]["text"]
        _neues_layout(html)
        for erfunden in ("45 %", "45%", "5000-15000"):
            assert erfunden not in html and erfunden not in text, erfunden
        assert "beigefügten PDF" in html

    def test_report_zeigt_gemessene_werte(self, gesendet, monkeypatch):
        import email_service
        svc, liste = gesendet
        monkeypatch.setattr(email_service.pdf_generator, "generate_compliance_report",
                            lambda daten, lead: b"%PDF-1.4 probe")
        svc.send_compliance_report("l@example.org", "Lea", {
            "compliance_score": 72, "estimated_risk_euro": "2000-4000",
            "findings": {"a": 1, "b": 2}})
        html = liste[0]["html"]
        assert "72 %" in html
        # Seit dem 07.10.2026 (#27) nennt kein Kundentext mehr einen Betrag als
        # Rechtsfolge; ein mitgegebener Euro-Wert bleibt in der Mail ungenannt.
        assert "2000-4000" not in html and "EUR" not in html
        assert "DSGVO-konform" not in html


class TestDsgvoMails:
    def test_loeschbestaetigung_sagt_nur_was_stimmt(self, gesendet):
        svc, liste = gesendet
        svc.send_deletion_confirmation_email("k@example.org", "user-7")
        html, text = liste[0]["html"], liste[0]["text"]
        _neues_layout(html)
        for falsch in ("Datenschutzbeauftragt", "aus allen unseren Systemen",
                       "Technische Logs", "Einwilligungsnachweis"):
            assert falsch not in html and falsch not in text, falsch
        assert "190 Tage" in html and "190 Tage" in text, "Sicherungen muessen genannt sein"

    def test_datenexport_maskiert(self, gesendet):
        svc, liste = gesendet
        svc.send_data_export_email("k@example.org", {
            "users": [{"firma": "<script>alert(1)</script>"}], "export_info": {}})
        html = liste[0]["html"]
        _neues_layout(html)
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html
        assert liste[0]["betreff"].startswith("Ihr Datenexport")


def _lauf(koro):
    import asyncio
    return asyncio.new_event_loop().run_until_complete(koro)


class TestLoeschreihenfolge:
    """Bestaetigt wird erst, wenn wirklich geloescht ist."""

    def test_keine_bestaetigung_wenn_loeschen_scheitert(self, monkeypatch):
        from unittest.mock import AsyncMock
        import gdpr_retention_service as g
        dienst = g.gdpr_service
        monkeypatch.setattr(g.db_service, "get_lead_by_id",
                            AsyncMock(return_value={"id": "L1", "email": "x@example.org"}))
        monkeypatch.setattr(g.db_service, "mark_lead_for_deletion", AsyncMock(return_value=True))
        monkeypatch.setattr(g.db_service, "delete_lead_permanently", AsyncMock(return_value=False))
        mail = AsyncMock()
        monkeypatch.setattr(dienst, "_send_deletion_confirmation", mail)
        _lauf(dienst.process_deletion_request("L1"))
        mail.assert_not_awaited()

    def test_bestaetigung_nach_erfolg(self, monkeypatch):
        from unittest.mock import AsyncMock
        import gdpr_retention_service as g
        dienst = g.gdpr_service
        monkeypatch.setattr(g.db_service, "get_lead_by_id",
                            AsyncMock(return_value={"id": "L1", "email": "x@example.org"}))
        monkeypatch.setattr(g.db_service, "mark_lead_for_deletion", AsyncMock(return_value=True))
        monkeypatch.setattr(g.db_service, "delete_lead_permanently", AsyncMock(return_value=True))
        mail = AsyncMock()
        monkeypatch.setattr(dienst, "_send_deletion_confirmation", mail)
        _lauf(dienst.process_deletion_request("L1"))
        mail.assert_awaited_once()


class TestKiComplianceMails:
    def _dienst(self, monkeypatch):
        monkeypatch.delenv("DASHBOARD_URL", raising=False)
        import importlib
        import ai_compliance_notification_service as m
        importlib.reload(m)
        d = m.ai_compliance_notification_service
        liste = []
        d._send_email = lambda an, betreff, html, text: liste.append((betreff, html, text)) or True
        return d, liste

    def test_alle_drei(self, monkeypatch):
        d, liste = self._dienst(monkeypatch)
        _lauf(d.send_compliance_alert("u@example.org", "Uli", "<i>Bot</i>", "s1", 90, 60,
                                      "high", [{"title": "<b>X</b>"}]))
        _lauf(d.send_scan_reminder("u@example.org", "Uli", [{"name": "<i>Bot</i>"}]))
        _lauf(d.send_high_risk_alert("u@example.org", "Uli", "<i>Bot</i>", "s1",
                                     "prohibited", "<img src=x onerror=alert(1)>"))
        assert len(liste) == 3
        for betreff, html, _ in liste:
            _neues_layout(html)
            assert "<i>Bot</i>" not in html and "<img src=x" not in html, betreff
            assert "https://app.complyo.de/" in html, "Links gehoeren ins Dashboard"


class TestRechtsaenderungsMails:
    NEWS = {"title": "<b>Neu</b>: BFSG", "summary": "<script>x</script>", "content": "",
            "source": "BGBl", "url": "https://example.org/a", "severity": "critical"}

    def _dienst(self):
        import datetime as dt
        from legal_notification_service import LegalNewsNotificationService
        d = LegalNewsNotificationService(db_pool=None)
        self.NEWS["published_date"] = dt.datetime(2026, 9, 29)
        return d

    def test_vorlage_maskiert_und_neues_layout(self):
        d = self._dienst()
        html = d._get_notification_email_template(
            {"email": "u@example.org"}, self.NEWS,
            "https://api.complyo.de/api/legal-notifications/confirm/t",
            "https://api.complyo.de/api/legal-notifications/dismiss/t")
        _neues_layout(html)
        assert "<script>x</script>" not in html and "&lt;script&gt;" in html
        assert "<b>Neu</b>" not in html
        for tot in ("/upgrade", "/settings/notifications", "/legal/confirm", "/legal/dismiss"):
            assert tot not in html, f"{tot} ist 404"

    def test_knoepfe_zeigen_auf_die_api(self, monkeypatch):
        from unittest.mock import AsyncMock
        d = self._dienst()
        gefangen = {}

        async def _senden(an, betreff, html, text):
            gefangen["html"], gefangen["text"] = html, text
            return True

        d._send_email = _senden
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value={"confirmation_token": "tok9"})
        monkeypatch.delenv("PUBLIC_API_BASE", raising=False)
        assert _lauf(d._send_notification_email(conn, 1, {"email": "u@example.org"}, self.NEWS))
        for teil in (gefangen["html"], gefangen["text"]):
            assert "https://api.complyo.de/api/legal-notifications/confirm/tok9" in teil
            assert "https://api.complyo.de/api/legal-notifications/dismiss/tok9" in teil

    def test_bestaetigen_leitet_ins_dashboard(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import legal_notification_routes as r
        monkeypatch.delenv("DASHBOARD_URL", raising=False)
        dienst = MagicMock()
        dienst.confirm_notification = AsyncMock(return_value={"success": True})
        dienst.dismiss_notification = AsyncMock(return_value={"success": False})
        monkeypatch.setattr(r._dienst, "legal_notification_service", dienst)
        app = FastAPI()
        app.include_router(r.router)
        c = TestClient(app)
        a = c.get("/api/legal-notifications/confirm/t", follow_redirects=False)
        assert a.status_code == 303
        assert a.headers["location"] == "https://app.complyo.de/dashboard?rechtsaenderung=bestaetigt"
        b = c.get("/api/legal-notifications/dismiss/t", follow_redirects=False)
        assert b.headers["location"].endswith("rechtsaenderung=ungueltig")
