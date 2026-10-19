"""
Wächter für die Wirksamkeitsüberwachung.

Das Widget meldet von fremden Domains, ohne Anmeldung. Genau dort entscheidet
sich, ob complyo ein Messwerkzeug ist oder ein Trackingskript. Vier Zusagen:

  1. Es werden keine personenbezogenen Daten verarbeitet — die Tabelle hat
     schlicht keine Spalte, in die ein Besucher passen würde.
  2. Abfrageparameter und Anker werden abgeschnitten. In ihnen stehen
     Suchbegriffe, Warenkorb-Inhalte und Tracking-Kennungen.
  3. Eine kaputte Statistik darf nie eine Kundenseite beeinträchtigen.
  4. Das Widget legt nichts auf dem Gerät des Besuchers ab. Das ist eine eigene
     Frage neben Zusage 1: auch ein Merker ohne Personenbezug ist ein
     Schreibzugriff auf das Endgerät.
"""
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import wirkung_routes as wr  # noqa: E402

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


def _nur_code(quelltext: str) -> str:
    """Docstrings und Kommentare entfernen.

    Zum dritten Mal in dieser Sitzung hat ein Waechter an der Erklaerung
    angeschlagen, die den Fehler beschreibt. Ein Test, der Prosa liest, prueft
    nichts.
    """
    ohne_docstrings = re.sub(r'"""[\s\S]*?"""', "", quelltext)
    return "\n".join(re.sub(r"#.*$", "", z) for z in ohne_docstrings.splitlines())


def _nur_js_code(quelltext: str) -> str:
    """Block- und Zeilenkommentare aus JavaScript entfernen.

    Der Kommentar darf den Merker beim Namen nennen, der Code nicht. Ein
    Zeilenkommentar zählt nur, wenn vor `//` weder Doppelpunkt noch Wortzeichen
    steht, damit `http://localhost` im Code bleibt.
    """
    ohne_block = re.sub(r"/\*[\s\S]*?\*/", "", quelltext)
    return "\n".join(re.sub(r"(?<![:\w])//.*$", "", z) for z in ohne_block.splitlines())


class TestDatensparsamkeit:
    def test_tabelle_hat_keine_besucherspalte(self):
        """Was nicht gespeichert werden kann, kann auch nicht auslaufen."""
        for verboten in ("ip", "user_agent", "referrer", "session", "besucher",
                         "cookie", "fingerprint"):
            assert verboten not in wr.SCHEMA.lower(), verboten

    def test_meldung_kennt_nur_pfad_und_zaehler(self):
        """
        Die Feldmenge ist bewusst festgenagelt.

        Sie darf wachsen — `dokument_fixes` und `unbekannte_kennung` kamen
        hinzu, nachdem im Browser aufgefallen war, dass Skip-Link und
        landmark-main ganz ausserhalb der Bilanz liefen und dass ein falsch
        eingebautes Widget sich nicht bemerkbar machen konnte. Aber sie darf
        nur um Aussagen ueber die SEITE wachsen, nie um eine ueber den
        Menschen davor. Dieser Test ist die Stelle, an der jemand darueber
        nachdenken muss.
        """
        felder = set(wr.WirkungsMeldung.model_fields)
        assert felder == {"pfad", "alt_texte", "link_labels", "struktur",
                          "css_regeln", "dokument_fixes", "unbekannte_kennung",
                          "erwartet", "melder"}

    def test_melder_ist_kein_freies_textfeld(self):
        """`melder` kam am 25.09.2026 dazu und ist die Ausnahme von der Regel.

        Es ist keine Aussage ueber die Seite, sondern ueber das Widget. Genau
        deshalb darf es kein freier Text sein: der Endpunkt ist oeffentlich,
        und was von einer fremden Domain kommt, kann alles enthalten.

        Eine Auswahl aus bekannten Fassungen kann nichts transportieren. Wer
        das Feld wieder oeffnet, faellt hier durch.
        """
        assert wr.WirkungsMeldung(pfad="/", melder="a11y-2026-09-25").melder
        for versuch in ("besucher-12345", "ip:1.2.3.4", "<script>", "beliebig"):
            assert wr.WirkungsMeldung(pfad="/", melder=versuch).melder == "", (
                f"{versuch!r} wurde uebernommen — das Feld ist wieder frei.")

    def test_kein_feld_beschreibt_den_besucher(self):
        for feld in wr.WirkungsMeldung.model_fields:
            for verboten in ("ip", "agent", "referrer", "session", "besucher",
                             "cookie", "fingerprint", "id_"):
                assert verboten not in feld.lower(), feld

    def test_abfrageparameter_werden_abgeschnitten(self):
        assert wr._pfad_saeubern("/kontakt/?utm_source=news") == "/kontakt/"
        assert wr._pfad_saeubern("/suche?q=geheimes+wort") == "/suche"

    def test_anker_wird_abgeschnitten(self):
        assert wr._pfad_saeubern("/leistungen/#preise") == "/leistungen/"

    def test_pfad_wird_normalisiert_und_begrenzt(self):
        assert wr._pfad_saeubern("leistungen") == "/leistungen"
        assert wr._pfad_saeubern("") == "/"
        assert len(wr._pfad_saeubern("/" + "a" * 500)) <= 200

    def test_das_widget_schickt_auch_keine_kennung(self):
        js = _lese("widgets", "a11y_remediation.js")
        block = js[js.index("function melde()"):js.index("function load()")]
        for verboten in ("document.cookie", "localStorage.getItem('complyo_u",
                         "navigator.userAgent", "document.referrer"):
            assert verboten not in block, verboten
        assert "location.pathname" in block
        assert "location.search" not in block


class TestRegressionsmeldung:
    def test_verfehlte_ziele_werden_gezaehlt(self):
        """
        Der eigentliche Wert: ein ausgelieferter Fix, dessen Selektor nichts
        mehr trifft, ist das Bild eines Theme-Updates. Ohne diese Zahl faellt
        so etwas erst beim naechsten Scan auf.
        """
        js = _lese("widgets", "a11y_remediation.js")
        assert "bilanz.struktur.verfehlt++" in js
        assert "if (!ziele.length)" in js

    def test_bilanz_deckt_alle_fixarten_ab(self):
        js = _lese("widgets", "a11y_remediation.js")
        for art in ("alt_texte", "link_labels", "struktur", "css_regeln"):
            assert f"bilanz.{art}.angewendet" in js, art

    def test_zusammenfassung_nennt_betroffene_pfade(self):
        src = _lese("wirkung_routes.py")
        assert "seiten_mit_verfehlten_zielen" in src


class TestStoertNie:
    def test_endpunkt_antwortet_immer_ohne_inhalt(self):
        """
        204 auch im Fehlerfall: eine Messung darf die Seite des Kunden nie
        stoeren, auch nicht durch einen roten Eintrag im Netzwerk-Reiter.
        """
        src = _nur_code(_lese("wirkung_routes.py"))
        block = src[src.index("async def melde_wirkung"):src.index("async def wirkung_preflight")]
        assert block.count("_keine_antwort()") >= 3
        assert "raise HTTPException" not in block

    def test_datenbankfehler_wird_geschluckt_aber_geloggt(self):
        src = _lese("wirkung_routes.py")
        block = src[src.index("async def melde_wirkung"):]
        assert "except Exception" in block and "logger.warning" in block

    def test_widget_meldet_fail_silent(self):
        js = _lese("widgets", "a11y_remediation.js")
        block = js[js.index("function melde()"):js.index("function load()")]
        assert "catch" in block

    def test_hoechstens_eine_meldung_je_seitenaufruf(self):
        """Ein einzelner Seitenaufruf meldet einmal, auch bei doppeltem Aufruf.

        Je Sitzung zu deduplizieren war der Grund fuer den Merker im
        sessionStorage. Das Flag lebt nur im Arbeitsspeicher des Aufrufs.
        """
        js = _lese("widgets", "a11y_remediation.js")
        code = _nur_js_code(js)
        block = code[code.index("function melde()"):code.index("function load()")]
        assert "var gemeldet = false;" in code
        assert "if (gemeldet) return;" in block
        assert "gemeldet = true;" in block
        assert len(re.findall(r"setTimeout\(melde\b", code)) == 1, (
            "melde() hat mehr als eine Aufrufstelle: ein Seitenaufruf koennte "
            "mehrfach melden.")


class TestNichtsAufDemGeraet:
    """Zusage 4: kein Cookie, kein localStorage, kein sessionStorage.

    Am 07.10.2026 beim Nachmessen von steinhau.de gefunden: Cookies leer,
    localStorage leer, und genau ein Eintrag von complyo in sessionStorage,
    gesetzt vor jeder Einwilligung. Er diente nur dazu, eine Meldung je
    Sitzung und Seite zu unterdruecken.

    Gelesen wird NUR a11y_remediation.js, die Datei mit dem Melder.
    accessibility-v6.js schreibt Einstellungen des Besuchers in localStorage;
    alle sechs Aufrufer von savePreferences() haengen an Bedienelementen der
    Werkzeugleiste (gelesen am 07.10.2026), nicht an der Initialisierung. Dieser
    Waechter deckt diese Datei nicht ab.
    """

    VERBOTEN = ("sessionStorage", "localStorage", "document.cookie", "cookieStore",
                "indexedDB", "caches.open")

    def test_waechter_liest_die_richtige_datei(self):
        """Ein gruener Waechter ueber eine leere Datei waere nichts wert."""
        code = _nur_js_code(_lese("widgets", "a11y_remediation.js"))
        assert "function melde()" in code and "function load()" in code
        assert "sendBeacon" in code
        assert len(code) > 5000, "Zu wenig Code gelesen: stimmt der Kommentar-Filter?"

    def test_widget_beschreibt_keinen_browserspeicher(self):
        code = _nur_js_code(_lese("widgets", "a11y_remediation.js"))
        for verboten in self.VERBOTEN:
            assert verboten not in code, (
                f"a11y_remediation.js benutzt {verboten}. Das ist ein Zugriff "
                f"auf das Endgeraet des Besuchers vor jeder Einwilligung.")

    def test_meldung_haengt_nicht_am_speicher(self):
        """Sperrt der Browser den Speicher, muss trotzdem gemeldet werden.

        Vorher brach melde() dann stillschweigend ab: gemessen 0 Meldungen bei
        gesperrtem Speicher, obwohl das Widget lief.
        """
        code = _nur_js_code(_lese("widgets", "a11y_remediation.js"))
        block = code[code.index("function melde()"):code.index("function load()")]
        assert "catch (e) { return; }" not in block


class TestVerdrahtung:
    def test_router_haengt_in_der_anwendung(self):
        src = _lese("main_production.py")
        assert "app.include_router(wirkung_router)" in src
        assert "await init_wirkung_routes(db_pool)" in src

    def test_nachweis_zieht_die_betriebsdaten(self):
        src = _lese("nachweis_routes.py")
        assert "wirkung_fuer_site" in src
        assert "im_betrieb" in src

    def test_ohne_betriebsdaten_steht_das_da(self):
        """Eine geschoente Null waere schlimmer als ein ehrlicher Hinweis."""
        src = _lese("nachweis_routes.py")
        assert "noch nicht gemeldet" in src

    def test_rate_limit_ist_gesetzt(self):
        src = _lese("wirkung_routes.py")
        assert 'rate_limit("wirkung"' in src


class TestAntwortIstWirklichLeer:
    """
    Beim Ausrollen im Log aufgefallen: `JSONResponse(status_code=204,
    content=None)` schreibt `null` in den Koerper, und uvicorn wirft dann bei
    JEDER Meldung "Response content longer than Content-Length".

    Nach aussen blieb das unsichtbar — das Widget meldet fail-silent. Eine
    Statistik, die stillschweigend Fehler produziert, ist schlimmer als keine.
    """

    def test_kein_json_koerper_bei_204(self):
        """Der Docstring darf den Fehler nennen — der Code nicht enthalten."""
        assert "JSONResponse(status_code=204" not in _nur_code(_lese("wirkung_routes.py"))

    def test_es_gibt_eine_gemeinsame_leerantwort(self):
        src = _nur_code(_lese("wirkung_routes.py"))
        assert "def _keine_antwort()" in src
        assert "Response(status_code=204" in src

    def test_der_grund_steht_dabei(self):
        src = _lese("wirkung_routes.py")
        assert "Content-Length" in src
