"""
Alle Oberflaechen des Widgets sehen aus wie der Cookie-Banner.

Anlass (09./10.11.2026, reinhardt.coffee): Der Platzhalter fuer gesperrte
Einbettungen (content_blocker.js) war fest violett (#667eea bis #764ba2) und
kannte weder Bannerfarben noch Schrift noch Rundung. Auf der Kundenseite musste
ein eigenes Plugin die "Sperrbildschirme" nachbauen. Dasselbe galt fuer den
Lizenzhinweis (fest dunkel, Cyan-Ueberschrift).

Regel: Der Banner ist die Vorlage und schreibt seine Gestaltung als
CSS-Variablen (--complyo-*) auf :root. Jede andere Oberflaeche liest diese
Variablen. Eigene Farben stehen dort nur als Rueckfall hinter der Variable.

Bewacht wird:
1. Der Banner setzt alle Variablen, die der Blocker liest, und laesst nur Hex durch.
2. Im Platzhalter steht keine Farbe ausserhalb eines var(--complyo-...)-Rueckfalls.
3. Der Lizenzhinweis hat keine eigene (dunkle/Cyan) Gestaltung mehr.
4. Der Knopf "Inhalt laden" laeuft ueber den Banner (Einwilligung wird protokolliert).
"""

import os
import re

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _lesen(name):
    with open(os.path.join(BACKEND, "widgets", name), encoding="utf-8") as f:
        return f.read()


BLOCKER = _lesen("content_blocker.js")
BANNER = _lesen("cookie_banner_v2.js")


def _bereich(text, start, ende):
    a = text.index(start)
    return text[a:text.index(ende, a)]


PLATZHALTER = _bereich(
    BLOCKER,
    "        injectPlaceholderStyles() {",
    "        // ====================================================================\n        // Helper Methods",
)
LIZENZ = _bereich(BANNER, "        renderLicenseNotice(message, severe) {", "        /**\n         * ✅ Phase 2: Geo-Restriction Check")
TOKENS = _bereich(BANNER, "        applyDesignTokens() {", "        /**\n         * ✅ Phase 7: Detect browser language")


class TestGemeinsameVariablen:
    def test_banner_setzt_jede_variable_die_der_blocker_liest(self):
        gelesen = set(re.findall(r"var\((--complyo-[a-z-]+)", PLATZHALTER))
        gesetzt = set(re.findall(r"'(--complyo-[a-z-]+)'", TOKENS))
        assert gelesen, "Platzhalter liest keine Banner-Variablen mehr"
        assert gelesen <= gesetzt, f"vom Banner nicht gesetzt: {sorted(gelesen - gesetzt)}"

    def test_lizenzhinweis_liest_nur_gesetzte_variablen(self):
        gelesen = set(re.findall(r"var\((--complyo-[a-z-]+)", LIZENZ))
        gesetzt = set(re.findall(r"'(--complyo-[a-z-]+)'", TOKENS))
        assert gelesen <= gesetzt, f"vom Banner nicht gesetzt: {sorted(gelesen - gesetzt)}"

    def test_kundenfarben_kommen_nur_als_hex_in_den_stil(self):
        # Die Werte stammen aus der Kundenkonfiguration und landen in einem <style>.
        assert "/^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$/" in TOKENS

    def test_variablen_stehen_auf_root_und_in_style_element(self):
        assert "':root{'" in TOKENS and "complyo-design-tokens" in TOKENS


class TestPlatzhalterOhneEigeneFarben:
    def test_kein_violetter_verlauf_mehr(self):
        for name, text in (("content_blocker.js", BLOCKER), ("cookie_banner_v2.js", BANNER)):
            assert "667eea" not in text.lower(), name
            assert "764ba2" not in text.lower(), name

    def test_hex_farben_nur_als_rueckfall_hinter_der_variable(self):
        verstoesse = []
        for nr, zeile in enumerate(PLATZHALTER.splitlines(), 1):
            if re.search(r"#[0-9a-fA-F]{3,8}\b", zeile) and "var(--complyo-" not in zeile:
                verstoesse.append((nr, zeile.strip()))
        assert not verstoesse, f"feste Farben im Platzhalter: {verstoesse}"

    def test_knoepfe_sind_echte_buttons(self):
        # Tastatur und Screenreader (WCAG 2.1.1, 4.1.2): kein klickbares <div>.
        assert PLATZHALTER.count('<button type="button"') >= 2


class TestLizenzhinweisImBannerDesign:
    def test_keine_eigene_dunkle_oder_cyan_gestaltung(self):
        for verboten in ("#00FFF7", "rgba(9,9,11", "#18181b", "#1f2937"):
            assert verboten.lower() not in LIZENZ.lower(), verboten

    def test_flaeche_und_schrift_kommen_aus_dem_banner(self):
        assert "var(--complyo-bg" in LIZENZ and "var(--complyo-text" in LIZENZ


class TestInhaltLadenLaeuftUeberDenBanner:
    def test_einwilligung_wird_ueber_saveCustom_protokolliert(self):
        assert "banner.saveCustom(" in PLATZHALTER

    def test_drittland_nur_wo_der_dienst_es_verlangt(self):
        assert "requiresThirdCountryConsent(src)" in PLATZHALTER
        assert "thirdCountry: cur.third_country === true || drittland" in PLATZHALTER

    def test_drittland_wird_beim_klick_bewertet_nicht_beim_erzeugen(self):
        # Live gemessen 10.11.2026: der Dienstkatalog (und damit die Drittland-Domains)
        # kommt erst nach dem ersten Scan. Wer das beim Erzeugen festschreibt, setzt
        # beim Klick kein third_country, und der Inhalt laedt nie: "Ihr Produkt geht nicht".
        klick = PLATZHALTER.index("placeholder-btn').addEventListener('click'")
        assert PLATZHALTER.index("const drittland = this.requiresThirdCountryConsent(src);") > klick
        assert "this.aktualisierePlatzhalterTexte();" in BLOCKER

    def test_datenattribut_scan_ueberschreibt_den_platzhalter_nicht(self):
        # Der Platzhalter traegt data-complyo-consent. blockDataAttributes() hat ihn
        # beim zweiten Scan als 'data-attribute' ueberschrieben: kein Freigabe-Handler,
        # der Inhalt kam nach "Inhalt laden" nie zurueck.
        scan = _bereich(BLOCKER, "        blockDataAttributes() {", "        blockElement(element) {")
        assert "this.blockedElements.has(element)" in scan
        assert "complyo-content-placeholder" in scan

    def test_knopf_ist_nie_tot(self):
        # Ohne Banner wird wenigstens diese eine Einbettung geladen.
        assert "this.unblockElement(placeholder, original)" in PLATZHALTER
