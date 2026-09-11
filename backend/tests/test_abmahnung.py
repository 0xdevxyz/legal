"""Wächter und Unit-Tests für „Abmahnung prüfen" (abmahnung_routes.py).

Drei Zusagen stehen hier fest:

  1. Das Schreiben wird nicht gespeichert. Es nennt Abmahner, Anwälte und
     Aktenzeichen; die Datei enthält keine Schreibanweisung an die Datenbank.
  2. Die Zuordnung sagt ehrlich, was sie weiß: bestätigt, nicht gefunden,
     nicht prüfbar, ohne Messung. Nie "nicht gefunden", wenn gar nicht
     gemessen wurde.
  3. Die Route ist angemeldet, nimmt nur echte PDFs bis 10 MB und antwortet
     ohne pypdf mit 503 statt mit einem Stacktrace.
"""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import abmahnung_routes as ab  # noqa: E402
from dependencies import get_current_user, get_db  # noqa: E402

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WURZEL = os.path.dirname(_BACKEND)


def _lese(*teile):
    with open(os.path.join(_WURZEL, *teile), encoding="utf-8") as fh:
        return fh.read()


SCHREIBEN = """Sehr geehrte Damen und Herren,

wir zeigen an, dass wir die Firma Muster GmbH anwaltlich vertreten. Vollmacht liegt bei.

Auf Ihrer Website www.beispiel.de werden Google Fonts von US-Servern nachgeladen, ohne dass eine Einwilligung der Besucher eingeholt wird. Damit wird die IP-Adresse an Google übermittelt (Verstoß gegen Art. 6 Abs. 1 DSGVO).

Ferner setzen Sie Cookies von Google Analytics bereits vor einer Einwilligung. Das Cookie-Banner bietet keine gleichwertige Ablehnen-Option (§ 25 TDDDG).

Ihr Impressum enthält keine ladungsfähige Anschrift und keine E-Mail-Adresse (§ 5 DDG).

Zudem verwenden Sie auf der Startseite ein Lichtbild unseres Mandanten ohne Lizenz. Für die Nutzung des Fotos fordern wir Schadensersatz nach § 97 UrhG in Höhe von 1.200,00 EUR.

Wir fordern Sie auf, bis zum 25.09.2026 die beigefügte Unterlassungserklärung abzugeben und die Kosten unserer Inanspruchnahme in Höhe von 1.171,67 € zu erstatten.

Mit freundlichen Grüßen
Rechtsanwalt Dr. Beispiel
"""

ISSUES = [
    {"category": "datenschutz", "severity": "critical",
     "title": "Google Fonts werden von Google-Servern geladen",
     "description": "IP-Adresse geht an Google", "legal_basis": "Art. 6 DSGVO"},
    {"category": "datenschutz", "severity": "warning",
     "title": "Datenschutzerklärung unvollständig",
     "description": "Betroffenenrechte fehlen", "legal_basis": "Art. 13 DSGVO"},
    {"category": "cookies", "severity": "critical",
     "title": "Tracking-Cookies vor Einwilligung gesetzt",
     "description": "_ga vor Consent", "legal_basis": "§ 25 TDDDG"},
    {"category": "barrierefreiheit", "severity": "warning",
     "title": "Bilder ohne Alternativtext",
     "description": "12 Bilder", "legal_basis": "BFSG"},
]


# ---------------------------------------------------------------------------
# Heuristik
# ---------------------------------------------------------------------------

class TestHeuristik:
    def test_findet_die_vier_vorwuerfe(self):
        vorwuerfe = ab.heuristik_vorwuerfe(SCHREIBEN)
        kategorien = [v["kategorie"] for v in vorwuerfe]
        assert "datenschutz" in kategorien
        assert "cookies" in kategorien
        assert "impressum" in kategorien
        assert "urheberrecht" in kategorien

    def test_ein_eintrag_je_kategorie(self):
        vorwuerfe = ab.heuristik_vorwuerfe(SCHREIBEN)
        kategorien = [v["kategorie"] for v in vorwuerfe]
        assert len(kategorien) == len(set(kategorien))

    def test_betrag_frist_und_norm(self):
        vorwuerfe = {v["kategorie"]: v for v in ab.heuristik_vorwuerfe(SCHREIBEN)}
        assert vorwuerfe["urheberrecht"]["forderung_euro"] == 1200.0
        assert "§ 97 UrhG" in (vorwuerfe["urheberrecht"]["rechtsgrundlage"] or "")
        assert "Art. 6 Abs. 1 DSGVO" in (vorwuerfe["datenschutz"]["rechtsgrundlage"] or "")
        assert "§ 5 DDG" in (vorwuerfe["impressum"]["rechtsgrundlage"] or "")

    def test_rahmen_ist_kein_vorwurf(self):
        """Grußformel und Vollmacht ergeben keinen Eintrag."""
        text = "Vollmacht liegt bei.\n\nMit freundlichen Grüßen\nRechtsanwalt Dr. Beispiel\n"
        assert ab.heuristik_vorwuerfe(text) == []

    def test_bild_allein_ist_kein_urheberrechtsvorwurf(self):
        """"Bilder ohne Alternativtext" ist Barrierefreiheit, nicht Urheberrecht."""
        text = ("Auf Ihrer Website fehlen bei zahlreichen Bildern die Alternativtexte, "
                "ein Verstoß gegen das BFSG und die WCAG 2.1.")
        kategorien = [v["kategorie"] for v in ab.heuristik_vorwuerfe(text)]
        assert kategorien == ["barrierefreiheit"]

    def test_betraege_im_text(self):
        assert ab.betraege_im_text(SCHREIBEN) == [1200.0, 1171.67]

    def test_leerer_text(self):
        assert ab.heuristik_vorwuerfe("") == []


# ---------------------------------------------------------------------------
# Zuordnung
# ---------------------------------------------------------------------------

def _vorwurf(kategorie, text="Vorwurf", euro=None):
    return {"vorwurf": text, "rechtsgrundlage": None, "kategorie": kategorie,
            "forderung_euro": euro, "frist": None}


class TestZuordnung:
    def test_bestaetigt_mit_passenden_befunden(self):
        z = ab.zuordnen([_vorwurf("cookies")], ISSUES, "2026-09-11T10:00:00")
        assert z[0]["status"] == "bestaetigt"
        assert [b["title"] for b in z[0]["befunde"]] == ["Tracking-Cookies vor Einwilligung gesetzt"]
        assert "11.09.2026" in z[0]["hinweis"]

    def test_woertlicher_treffer_steht_vorn(self):
        z = ab.zuordnen([_vorwurf("datenschutz", "Google Fonts ohne Einwilligung")],
                        ISSUES, None)
        assert z[0]["befunde"][0]["title"].startswith("Google Fonts")
        # Die unvollstaendige Datenschutzerklaerung liegt zwar in derselben
        # Saeule, beruehrt den Fonts-Vorwurf aber nicht: sie bestaetigt nichts.
        assert len(z[0]["befunde"]) == 1

    def test_stichwort_findet_befund_unter_nachbarsaeule(self):
        """Google-Fonts-Befund liegt unter datenschutz, der Vorwurf sagt "Tracking"."""
        issues = [{"category": "datenschutz", "severity": "critical",
                   "title": "Tracking-Pixel vor Einwilligung", "description": "",
                   "legal_basis": ""}]
        z = ab.zuordnen([_vorwurf("cookies")], issues, None)
        assert z[0]["status"] == "bestaetigt"

    def test_info_befund_bestaetigt_nie(self):
        """Live am 11.09.2026: "Kein Cookie-Banner erforderlich" (info) galt als
        Beleg fuer fuenf Vorwuerfe. Ein Hinweis ist kein Befund."""
        issues = [{"category": "cookies", "severity": "info",
                   "title": "Kein Cookie-Banner erforderlich",
                   "description": "TDDDG §25 Abs. 2", "legal_basis": "TDDDG §25 Abs. 2"}]
        for kat, text in (("cookies", "Cookie-Banner bietet keine Ablehnen-Möglichkeit"),
                          ("impressum", "Impressum enthält keine Umsatzsteuer-Identifikationsnummer"),
                          ("datenschutz", "Google Fonts werden von Google-Servern geladen")):
            z = ab.zuordnen([_vorwurf(kat, text)], issues, None)
            assert z[0]["status"] == "nicht_gefunden", (kat, z[0])

    def test_stichwort_braucht_wortgrenze(self):
        """"ddg" darf nicht in "TDDDG" treffen."""
        issues = [{"category": "cookies", "severity": "warning",
                   "title": "Cookie-Banner ohne TDDDG-Hinweis", "description": "",
                   "legal_basis": ""}]
        z = ab.zuordnen([_vorwurf("impressum", "Impressum enthält keine Anschrift")], issues, None)
        assert z[0]["status"] == "nicht_gefunden"

    def test_befund_muss_den_vorwurf_beruehren(self):
        """Gleiche Saeule reicht nicht: ein Kontrast-Befund bestaetigt keinen
        Alt-Text-Vorwurf, ein Cookie-Laufzeit-Hinweis keinen fehlenden Ablehnen-Knopf."""
        issues = [{"category": "cookies", "severity": "warning",
                   "title": "Banner nennt die Gültigkeitsdauer der Einwilligung nicht",
                   "description": "", "legal_basis": ""},
                  {"category": "cookies", "severity": "critical",
                   "title": "Ablehnen-Knopf fehlt im Cookie-Banner",
                   "description": "", "legal_basis": ""}]
        z = ab.zuordnen([_vorwurf("cookies", "Cookie-Banner bietet keine Möglichkeit, die Einwilligung ebenso einfach abzulehnen")], issues, None)
        assert z[0]["status"] == "bestaetigt"
        assert [b["title"] for b in z[0]["befunde"]] == ["Ablehnen-Knopf fehlt im Cookie-Banner"]

    def test_verwandte_befunde_stehen_daneben_ohne_zu_bestaetigen(self):
        issues = [{"category": "impressum", "severity": "warning",
                   "title": "Impressum: Handelsregister fehlt", "description": "",
                   "legal_basis": "§ 5 DDG"}]
        z = ab.zuordnen([_vorwurf("impressum", "Impressum enthält keine Umsatzsteuer-Identifikationsnummer")],
                        issues, None)
        assert z[0]["status"] == "nicht_gefunden"
        assert z[0]["befunde"] == []
        assert [b["title"] for b in z[0]["verwandt"]] == ["Impressum: Handelsregister fehlt"]
        assert "demselben Bereich" in z[0]["hinweis"]

    def test_teilwort_bestaetigt_nicht(self):
        """Live am 11.09.2026: "Telefonnummer fehlt" galt als Beleg fuer
        "keine Umsatzsteuer-Identifikationsnummer" (gemeinsam: "nummer")."""
        issues = [{"category": "impressum", "severity": "critical",
                   "title": "Telefonnummer fehlt im Impressum", "description": "",
                   "legal_basis": "DDG §5"}]
        z = ab.zuordnen([_vorwurf("impressum", "Impressum enthält keine Umsatzsteuer-Identifikationsnummer")],
                        issues, None)
        assert z[0]["status"] == "nicht_gefunden"
        assert [b["title"] for b in z[0]["verwandt"]] == ["Telefonnummer fehlt im Impressum"]
        # Der echte Treffer bleibt einer:
        issues.append({"category": "impressum", "severity": "warning",
                       "title": "USt-IdNr. fehlt im Impressum", "description": "",
                       "legal_basis": "DDG §5"})
        z = ab.zuordnen([_vorwurf("impressum", "Impressum enthält keine Umsatzsteuer-Identifikationsnummer")],
                        issues, None)
        assert z[0]["status"] == "bestaetigt"
        assert [b["title"] for b in z[0]["befunde"]] == ["USt-IdNr. fehlt im Impressum"]

    def test_nicht_gefunden(self):
        z = ab.zuordnen([_vorwurf("impressum")], ISSUES, "2026-09-11T10:00:00")
        assert z[0]["status"] == "nicht_gefunden"
        assert z[0]["befunde"] == []
        assert "heißt nicht, dass der Vorwurf falsch ist" in z[0]["hinweis"]

    def test_nicht_pruefbar(self):
        for kategorie in ("urheberrecht", "sonstiges"):
            z = ab.zuordnen([_vorwurf(kategorie)], ISSUES, None)
            assert z[0]["status"] == "nicht_pruefbar"

    def test_ohne_messung(self):
        """Ohne Kennung darf nichts als "nicht gefunden" erscheinen."""
        z = ab.zuordnen([_vorwurf("cookies"), _vorwurf("urheberrecht")], None, None)
        assert z[0]["status"] == "ohne_messung"
        assert z[1]["status"] == "nicht_pruefbar"

    def test_zusammenfassung(self):
        z = ab.zuordnen([_vorwurf("cookies", euro=500), _vorwurf("urheberrecht", euro=1200),
                         _vorwurf("impressum")], ISSUES, None)
        s = ab.zusammenfassen(z, "Kosten 1.171,67 €")
        assert s["anzahl"] == 3
        assert s["je_status"] == {"bestaetigt": 1, "nicht_gefunden": 1,
                                  "nicht_pruefbar": 1, "ohne_messung": 0}
        assert s["forderung_summe_euro"] == 1700.0
        assert s["betraege_im_schreiben"] == [1171.67]

    def test_ki_eintrag_wird_bereinigt(self):
        roh = {"vorwurf": "Cookies ohne Einwilligung", "kategorie": "Cookies ",
               "forderung_euro": "1.500 €", "rechtsgrundlage": None, "frist": None}
        v = ab._vorwurf_bereinigen(roh)
        assert v["kategorie"] == "cookies"
        assert v["forderung_euro"] == 1500.0
        assert ab._vorwurf_bereinigen({"vorwurf": "x", "kategorie": "quatsch"})["kategorie"] == "sonstiges"
        assert ab._vorwurf_bereinigen({"kategorie": "cookies"}) is None

    def test_ergebnis_aus_auftrag_liest_beide_formen(self):
        issues, wann = ab._ergebnis_aus_auftrag(
            {"ergebnis": {"success": True, "data": {"issues": ISSUES, "scan_timestamp": "2026-09-11T10:00:00"}}})
        assert len(issues) == 4 and wann == "2026-09-11T10:00:00"
        issues, wann = ab._ergebnis_aus_auftrag({"ergebnis": {"issues": ISSUES[:1]}, "beendet": 1757584800})
        assert len(issues) == 1 and wann and wann.startswith("2025-09-11")


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

def _user():
    return {"id": 7, "user_id": 7, "email": "test@example.com", "plan_type": "pro"}


@pytest.fixture(autouse=True)
def _kein_rate_limit():
    """rate_limit ist fail-open ohne Redis; im TestClient teilen sich alle Tests
    eine IP, ein echtes Fenster von einer Stunde würde ab dem 6. Aufruf 429 liefern."""
    with patch("dependencies.get_redis", AsyncMock(return_value=None)):
        yield


def _app(user=None):
    app = FastAPI()
    app.include_router(ab.router)
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: None
    return TestClient(app)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(ab, "_besitzt_website", AsyncMock(return_value=True))
    # Kein Netz im Test: die KI meldet "nichts", die Heuristik übernimmt.
    monkeypatch.setattr(ab, "ki_vorwuerfe", AsyncMock(return_value=None))
    return _app(_user())


def _felder(**extra):
    felder = {"website_url": "https://www.beispiel.de", "text": SCHREIBEN}
    felder.update(extra)
    return felder


class TestRoute:
    def test_ohne_anmeldung(self):
        r = _app().post("/api/abmahnung/pruefen", data=_felder())
        assert r.status_code in (401, 403)

    def test_fremde_website(self, monkeypatch):
        monkeypatch.setattr(ab, "_besitzt_website", AsyncMock(return_value=False))
        r = _app(_user()).post("/api/abmahnung/pruefen", data=_felder())
        assert r.status_code == 403

    def test_durchlauf_mit_text_und_messung(self, client, monkeypatch):
        auftrag = {"kennung": "scan-abc", "url": "https://beispiel.de/", "zustand": "fertig",
                   "user_id": "7",
                   "ergebnis": {"success": True,
                                "data": {"issues": ISSUES, "scan_timestamp": "2026-09-11T10:00:00"}}}
        from compliance_engine import scan_auftraege
        monkeypatch.setattr(scan_auftraege, "hole", AsyncMock(return_value=auftrag))
        import nachweis_routes
        monkeypatch.setattr(nachweis_routes, "_daten_fuer", AsyncMock(return_value={"site_url": "x"}))
        monkeypatch.setenv("COMPLYO_NACHWEIS_SECRET", "s3cret")
        monkeypatch.setenv("COMPLYO_PUBLIC_URL", "https://complyo.de")

        r = client.post("/api/abmahnung/pruefen", data=_felder(kennung="scan-abc"))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["quelle"] == "heuristik"
        assert d["mit_messung"] is True
        assert d["gemessen_am"] == "2026-09-11T10:00:00"
        status = {v["kategorie"]: v["status"] for v in d["vorwuerfe"]}
        assert status["datenschutz"] == "bestaetigt"
        assert status["cookies"] == "bestaetigt"
        assert status["impressum"] == "nicht_gefunden"
        assert status["urheberrecht"] == "nicht_pruefbar"
        assert d["zusammenfassung"]["je_status"]["bestaetigt"] == 2
        assert d["beleg_url"].startswith("https://complyo.de/nachweis/beispiel-de/")
        assert len(d["hinweise"]) == 5
        assert any("keine rechtliche Bewertung" in h for h in d["hinweise"])

    def test_ohne_kennung_keine_zuordnung(self, client, monkeypatch):
        monkeypatch.delenv("COMPLYO_NACHWEIS_SECRET", raising=False)
        r = client.post("/api/abmahnung/pruefen", data=_felder())
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["mit_messung"] is False
        assert d["beleg_url"] is None  # kein Geheimnis gesetzt
        assert {v["status"] for v in d["vorwuerfe"]} <= {"ohne_messung", "nicht_pruefbar"}

    def test_fremde_kennung_ist_404(self, client, monkeypatch):
        from compliance_engine import scan_auftraege
        monkeypatch.setattr(scan_auftraege, "hole",
                            AsyncMock(return_value={"user_id": "99", "zustand": "fertig"}))
        r = client.post("/api/abmahnung/pruefen", data=_felder(kennung="scan-x"))
        assert r.status_code == 404

    def test_kennung_anderer_website(self, client, monkeypatch):
        from compliance_engine import scan_auftraege
        monkeypatch.setattr(scan_auftraege, "hole", AsyncMock(return_value={
            "user_id": "7", "zustand": "fertig", "url": "https://andere.de", "ergebnis": {}}))
        r = client.post("/api/abmahnung/pruefen", data=_felder(kennung="scan-x"))
        assert r.status_code == 400

    def test_weder_text_noch_datei(self, client):
        r = client.post("/api/abmahnung/pruefen", data={"website_url": "https://beispiel.de"})
        assert r.status_code == 400

    def test_text_zu_lang(self, client):
        r = client.post("/api/abmahnung/pruefen",
                        data=_felder(text="x" * (ab.MAX_TEXT_ZEICHEN + 1)))
        assert r.status_code == 413

    def test_pdf_ohne_magic_bytes(self, client):
        r = client.post("/api/abmahnung/pruefen", data={"website_url": "https://beispiel.de"},
                        files={"datei": ("brief.pdf", b"kein pdf, nur text", "application/pdf")})
        assert r.status_code == 400
        assert "keine PDF" in r.json()["detail"]

    def test_pdf_falscher_typ(self, client):
        r = client.post("/api/abmahnung/pruefen", data={"website_url": "https://beispiel.de"},
                        files={"datei": ("brief.docx", b"%PDF-1.4", "application/msword")})
        assert r.status_code == 400

    def test_pdf_zu_gross(self, client):
        gross = b"%PDF-1.4\n" + b"0" * ab.MAX_PDF_BYTES
        r = client.post("/api/abmahnung/pruefen", data={"website_url": "https://beispiel.de"},
                        files={"datei": ("brief.pdf", gross, "application/pdf")})
        assert r.status_code == 413

    def test_ohne_pypdf_503(self, client, monkeypatch):
        monkeypatch.setattr(ab, "PdfReader", None)
        r = client.post("/api/abmahnung/pruefen", data={"website_url": "https://beispiel.de"},
                        files={"datei": ("brief.pdf", b"%PDF-1.4 leer", "application/pdf")})
        assert r.status_code == 503
        assert "Text einfügen" in r.json()["detail"]

    def test_pdf_wird_gelesen(self, client, monkeypatch):
        """Mit pypdf (oder einem Ersatz) landet der PDF-Text in der Auswertung."""
        class _Seite:
            def extract_text(self):
                return "Ihr Impressum enthält keine ladungsfähige Anschrift (§ 5 DDG)."

        class _Leser:
            is_encrypted = False
            pages = [_Seite()]

            def __init__(self, _):
                pass

        monkeypatch.setattr(ab, "PdfReader", _Leser)
        r = client.post("/api/abmahnung/pruefen", data={"website_url": "https://beispiel.de"},
                        files={"datei": ("brief.pdf", b"%PDF-1.4 x", "application/pdf")})
        assert r.status_code == 200, r.text
        assert [v["kategorie"] for v in r.json()["vorwuerfe"]] == ["impressum"]

    def test_verschluesseltes_pdf(self, client, monkeypatch):
        class _Leser:
            is_encrypted = True
            pages = []

            def __init__(self, _):
                pass

        monkeypatch.setattr(ab, "PdfReader", _Leser)
        r = client.post("/api/abmahnung/pruefen", data={"website_url": "https://beispiel.de"},
                        files={"datei": ("brief.pdf", b"%PDF-1.4 x", "application/pdf")})
        assert r.status_code == 400
        assert "verschlüsselt" in r.json()["detail"]

    def test_ki_ergebnis_hat_vorrang(self, monkeypatch):
        monkeypatch.setattr(ab, "_besitzt_website", AsyncMock(return_value=True))
        monkeypatch.setattr(ab, "ki_vorwuerfe", AsyncMock(return_value=[
            _vorwurf("werbung_uwg", "Irreführende Garantiewerbung", 800)]))
        r = _app(_user()).post("/api/abmahnung/pruefen", data=_felder())
        assert r.status_code == 200
        d = r.json()
        assert d["quelle"] == "ki"
        assert d["vorwuerfe"][0]["kategorie"] == "werbung_uwg"

    def test_ki_prueft_budget_zuerst(self, monkeypatch):
        """Ohne Budget kein Netzaufruf: der Vorfall vom 04.09.2026."""
        import asyncio
        from compliance_engine import ai_budget
        monkeypatch.setattr(ai_budget, "budget_frei", AsyncMock(return_value=False))
        aufruf = AsyncMock(return_value=("{}", {}))
        monkeypatch.setattr(ab, "_ki_rohantwort", aufruf)
        assert asyncio.run(ab.ki_vorwuerfe("text", 7, "pro")) is None
        aufruf.assert_not_called()

    def test_ki_kosten_werden_gebucht(self, monkeypatch):
        import asyncio
        from compliance_engine import ai_budget
        monkeypatch.setattr(ai_budget, "budget_frei", AsyncMock(return_value=True))
        buchung = AsyncMock()
        monkeypatch.setattr(ai_budget, "kosten_buchen", buchung)
        monkeypatch.setattr(ab, "_ki_rohantwort", AsyncMock(return_value=(
            '```json\n{"vorwuerfe": [{"vorwurf": "Cookies", "kategorie": "cookies"}]}\n```',
            {"prompt_tokens": 1000, "completion_tokens": 100})))
        liste = asyncio.run(ab.ki_vorwuerfe("text", 7, "pro"))
        assert liste and liste[0]["kategorie"] == "cookies"
        buchung.assert_called_once()
        assert buchung.call_args[0][1] > 0


# ---------------------------------------------------------------------------
# Wächter
# ---------------------------------------------------------------------------

class TestWaechter:
    def test_keine_speicherung(self):
        """Das Schreiben enthält Daten Dritter. Die Datei darf nichts schreiben."""
        src = _lese("backend", "abmahnung_routes.py")
        for wort in ("INSERT", "UPDATE", "DELETE FROM", ".execute(", "executemany"):
            assert wort not in src, wort

    def test_log_ohne_inhalt(self):
        src = _lese("backend", "abmahnung_routes.py")
        assert ('user_id, site_id, len(zugeordnet), quelle, zusammenfassung["je_status"]'
                in src)

    def test_route_registriert(self):
        src = _lese("backend", "main_production.py")
        assert "from abmahnung_routes import router as abmahnung_router" in src
        assert "app.include_router(abmahnung_router)" in src

    def test_nicht_in_exempt_paths(self):
        """Angemeldete Route, also CSRF-geschützt."""
        assert "/api/abmahnung" not in _lese("backend", "csrf_middleware.py")

    def test_pypdf_in_requirements(self):
        assert "pypdf>=4.3" in _lese("backend", "requirements.txt")

    def test_angemeldet_und_gedrosselt(self):
        src = _lese("backend", "abmahnung_routes.py")
        assert "Depends(get_current_user)" in src
        assert 'rate_limit("abmahnung", 5, 3600)' in src

    def test_hinweise_vollstaendig(self):
        text = " ".join(ab.HINWEISE).lower()
        for wort in ("frist", "ignorieren", "unterlassungserklärung", "anwalt",
                     "keine rechtliche bewertung"):
            assert wort in text

    def test_dashboard_seite_und_menue(self):
        seite = _lese("dashboard-react", "src", "app", "abmahnung", "page.tsx")
        assert "/api/abmahnung/pruefen" in seite
        assert "analyzeWebsite" in seite
        assert "keine Rechtsberatung" in seite
        sidebar = _lese("dashboard-react", "src", "components", "dashboard", "Sidebar.tsx")
        assert "href: '/abmahnung'" in sidebar
        assert sidebar.index("/pflichten-report") < sidebar.index("href: '/abmahnung'")
