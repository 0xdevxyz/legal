"""
Waechter fuer den axe-Regelsatz.

Der Anlass: `runOnly: [wcag21aa, best-practice]` sah vollstaendig aus und war
es nicht. axe-Tags sind flach — `wcag21aa` meint nur die Regeln, die WCAG 2.1
auf Stufe AA NEU brachte. Alles aus WCAG 2.0 (image-alt, link-name, label,
color-contrast, button-name, html-has-lang, die gesamte ARIA-Familie) lief nie
mit. Gemeldet wurden ausschliesslich best-practice-Befunde; auf
spedition-mahn.de fehlten dadurch 13x link-name, 7x color-contrast, 6x
nested-interactive und 3x aria-required-parent.

Ein solcher Fehler ist von aussen unsichtbar — der Scan lief ja "erfolgreich".
Deshalb steht er hier fest, nicht nur im Code.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.axe_scanner import (  # noqa: E402
    AXE_RULE_TO_FEATURE, WCAG_TAG_MENGEN, axe_tags_fuer, ist_rechtspflicht,
)


class TestRegelsatz:
    def test_wcag21aa_schliesst_wcag20_ein(self):
        """Die entscheidende Zusage: BFSG verweist auf 2.1 AA, das enthaelt 2.0."""
        tags = set(axe_tags_fuer("wcag21aa"))
        for noetig in ("wcag2a", "wcag2aa", "wcag21a", "wcag21aa"):
            assert noetig in tags, f"{noetig} fehlt — halber Regelsatz"

    def test_best_practice_ist_dabei_aber_trennbar(self):
        assert "best-practice" in axe_tags_fuer("wcag21aa")
        assert "best-practice" not in axe_tags_fuer("wcag21aa", mit_best_practice=False)

    def test_wcag22_bleibt_draussen(self):
        """Rechtlich nicht gefordert — kein Befund, den niemand einfordern kann."""
        assert not any(t.startswith("wcag22") for t in axe_tags_fuer("wcag21aa"))

    def test_unbekannte_stufe_faellt_auf_vollen_satz_zurueck(self):
        assert set(axe_tags_fuer("quatsch")) == set(axe_tags_fuer("wcag21aa"))

    def test_niedrigere_stufen_sind_kumulativ(self):
        assert set(WCAG_TAG_MENGEN["wcag2aa"]) >= set(WCAG_TAG_MENGEN["wcag2a"])
        assert set(WCAG_TAG_MENGEN["wcag21aa"]) >= set(WCAG_TAG_MENGEN["wcag2aa"])


class TestRechtspflicht:
    def test_wcag_befund_ist_pflicht(self):
        assert ist_rechtspflicht(["cat.text-alternatives", "wcag2a", "wcag111"])

    def test_best_practice_ist_keine_pflicht(self):
        """`region` und `heading-order` duerfen nicht als BFSG-Verstoss gelten."""
        assert not ist_rechtspflicht(["cat.keyboard", "best-practice"])

    def test_wcag22_allein_ist_keine_pflicht(self):
        assert not ist_rechtspflicht(["wcag22aa", "cat.sensory-and-visual-cues"])


class TestMappingBleibtErreichbar:
    def test_die_wichtigen_wcag20_regeln_haben_ein_feature(self):
        """
        Diese Regeln waren gemappt, konnten aber nie feuern. Das Mapping ist
        der Beleg, dass sie erwartet wurden — der Filter war der Fehler.
        """
        for regel in ("image-alt", "color-contrast", "label", "link-name",
                      "button-name", "html-has-lang"):
            assert regel in AXE_RULE_TO_FEATURE, f"{regel} ohne Feature-Zuordnung"


class TestScanMisstOhneDasEigeneWidget:
    """
    Der Scan muss das complyo-Widget blockieren.

    Ohne die Sperre misst er eine Seite, die complyo bereits repariert hat —
    das Widget setzt Alt-Texte, role="main" und freigegebene Farben zur
    Laufzeit. Der Scan faende nichts mehr und wuerde den gespeicherten
    Messwert mit einer Null ueberschreiben.

    Die Folge waere absurd: je besser die Reparatur wirkt, desto leerer der
    Pruefnachweis, der sie belegen soll. Beim ersten echten Kundenscan auf
    zua-zwickau.de ist genau das passiert.
    """

    def test_die_sperre_steht_im_scanner(self):
        import os
        pfad = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "compliance_engine", "axe_scanner.py",
        )
        with open(pfad, encoding="utf-8") as fh:
            src = fh.read()
        assert "page.route" in src
        assert "api\\.complyo\\." in src or "api\\\\.complyo" in src

    def test_der_grund_steht_dabei(self):
        import os
        pfad = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "compliance_engine", "axe_scanner.py",
        )
        with open(pfad, encoding="utf-8") as fh:
            src = fh.read()
        assert "OHNE" in src and "Pruefnachweis" in src
