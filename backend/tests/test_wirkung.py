"""
Wächter für die Wirksamkeitsüberwachung.

Das Widget meldet von fremden Domains, ohne Anmeldung. Genau dort entscheidet
sich, ob complyo ein Messwerkzeug ist oder ein Trackingskript. Drei Zusagen:

  1. Es werden keine personenbezogenen Daten verarbeitet — die Tabelle hat
     schlicht keine Spalte, in die ein Besucher passen würde.
  2. Abfrageparameter und Anker werden abgeschnitten. In ihnen stehen
     Suchbegriffe, Warenkorb-Inhalte und Tracking-Kennungen.
  3. Eine kaputte Statistik darf nie eine Kundenseite beeinträchtigen.
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


class TestDatensparsamkeit:
    def test_tabelle_hat_keine_besucherspalte(self):
        """Was nicht gespeichert werden kann, kann auch nicht auslaufen."""
        for verboten in ("ip", "user_agent", "referrer", "session", "besucher",
                         "cookie", "fingerprint"):
            assert verboten not in wr.SCHEMA.lower(), verboten

    def test_meldung_kennt_nur_pfad_und_zaehler(self):
        felder = set(wr.WirkungsMeldung.model_fields)
        assert felder == {"pfad", "alt_texte", "link_labels", "struktur",
                          "css_regeln", "erwartet"}

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

    def test_nur_einmal_je_seite_und_sitzung(self):
        """Ein Besucher, der blaettert, erzeugt keine zehn Meldungen derselben Seite."""
        js = _lese("widgets", "a11y_remediation.js")
        block = js[js.index("function melde()"):js.index("function load()")]
        assert "sessionStorage" in block


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
