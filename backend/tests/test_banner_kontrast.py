# -*- coding: utf-8 -*-
"""Der eigene Cookie-Banner darf keine Kontrastverstoesse mitbringen.

Am 09.09.2026 auf complyo.de gemessen: OHNE complyo 0 axe-Befunde, MIT complyo
5 — alle fuenf Kontrast, alle fuenf im eigenen Banner.

    #complyo-settings           #25bac8 auf #f0fdfa   2,25:1   (noetig 4,5)
    Fusszeilen-Links (3x)       #55837f auf #f0fdfa   4,07:1
    .complyo-branding-prefix    #769d99 auf #f0fdfa   2,85:1

Zwei Ursachen, beide klassisch:

1. Die Markenfarbe stand als SCHRIFT im Knopf. lesbareSchrift() loest den
   umgekehrten Fall (Schrift AUF der Marke) und griff hier nicht.
2. `opacity` auf Text. Sie sieht nach Gestaltung aus, rechnet die Farbe aber
   in Richtung Hintergrund — im Quelltext steht dabei nie eine verdaechtige
   Farbe.

Gefunden wurde es erst, als der Scan das eigene Widget NICHT mehr blockte. Der
regulaere Scan blendet api.complyo.de aus und konnte den eigenen Fehler damit
grundsaetzlich nicht sehen. Ein Produkt, das Barrierefreiheit verkauft, brachte
auf jede Seite mit Banner fuenf Verstoesse mit.
"""

import os
import re

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def banner():
    return open(os.path.join(BACKEND, "widgets", "cookie_banner_v2.js"),
                encoding="utf-8").read()


def regel(css: str, selektor: str) -> str:
    """Der Rumpf einer CSS-Regel aus dem Stil-Vorlagentext.

    Das Regelende wird ueber den Zeilenanfang gesucht, nicht ueber das
    naechste "}": die Regeln enthalten Platzhalter der Form ${farbe}, und ein
    naives index("}") schnitte mitten in den Wert.
    """
    i = css.index(selektor + " {")
    ende = re.search(r"\n\s*\}", css[i:])
    return css[i:i + ende.start()] if ende else css[i:]


class TestMarkenfarbeAlsSchrift:
    def test_helfer_existiert(self):
        assert "static lesbareMarkenschrift(" in banner()

    def test_knopf_nutzt_die_gerechnete_farbe(self):
        r = regel(banner(), ".complyo-btn-link")
        assert "${linkColor}" in r
        assert "${primaryColor}" not in r

    def test_farbe_wird_gegen_den_bannergrund_gerechnet(self):
        s = banner()
        assert "lesbareMarkenschrift(primaryColor, bgColor)" in s


class TestKeineDeckkraftAufSchrift:
    def test_fusszeilen_links_ohne_deckkraft(self):
        r = regel(banner(), ".complyo-footer a")
        assert "opacity" not in r, "Deckkraft auf Text ist die haeufigste Kontrastfalle"
        assert "${leiseColor}" in r

    def test_branding_ohne_deckkraft(self):
        r = regel(banner(), ".complyo-branding-prefix")
        assert "opacity" not in r
        assert "${leiseColor}" in r

    def test_gedaempfte_schrift_haelt_die_vorgabe(self):
        """Der Helfer daempft nur so weit, wie 4,5:1 es zulassen."""
        s = banner()
        assert "static gedaempfteSchrift(" in s
        block = s[s.index("static gedaempfteSchrift("):]
        block = block[:block.index("\n        }")]
        assert "ziel" in block


class TestKontrastrechnung:
    def test_verhaeltnis_nach_wcag(self):
        s = banner()
        assert "static kontrast(" in s
        block = s[s.index("static kontrast("):]
        block = block[:block.index("\n        }")]
        # (heller + 0.05) / (dunkler + 0.05)
        assert "0.05" in block

    def test_unlesbare_angabe_faellt_auf_etwas_lesbares_zurueck(self):
        """rgb()- oder Namensfarben duerfen nicht zu einem unlesbaren Wert
        fuehren — lieber die garantiert lesbare Ersatzfarbe."""
        s = banner()
        block = s[s.index("static lesbareMarkenschrift("):]
        block = block[:block.index("\n        }\n")]
        assert "lesbareSchrift(hintergrund)" in block
