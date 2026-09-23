"""Rechtsgrundlagen als Daten: europäischer Kern, nationaler Anker.

Warum es dieses Modul gibt
--------------------------
Gezählt am 23.09.2026 standen im Prüfkern 158 ausgegebene Nennungen deutscher
Gesetze, verteilt auf 20 Dateien, davon 67 mal das BFSG. Da die Engine den
Rechtsraum bis dahin nicht las, hätte ein niederländischer Kunde Befunde
bekommen, die ihm die Verletzung des deutschen
Barrierefreiheitsstärkungsgesetzes vorwerfen. In einem Produkt, das Rechtstreue
verkauft, ist das der teuerste denkbare Fehler: nicht weil er auffällt, sondern
weil er beim ersten Blick eines Fachkundigen das ganze Ergebnis entwertet.

Der Aufbau folgt dem, was die Messung gezeigt hat. Die Angaben waren bereits
zweiteilig:

    "WCAG 2.1 (1.4.3), BFSG §12"

Vorn steht die europäisch einheitliche Prüfsubstanz, hinten der Paragraf, der
sie im jeweiligen Land anordnet. EN 301 549 verweist auf WCAG 2.1 Stufe AA, und
das BFSG verweist auf EN 301 549. National ist nur der Anker.

Die Regel bei Lücken
--------------------
Fehlt für einen Rechtsraum der nationale Anker, wird **ausschliesslich die
europäische Grundlage genannt**. Nie geraten, nie das deutsche Gesetz als
Rückfall. Dieselbe Regel wie bei den Alternativtexten und bei `role=main`:
lieber keine Angabe als eine falsche.

Was hier (noch) nicht geregelt ist
----------------------------------
**Sprache.** "DSGVO" und "GDPR" bezeichnen dasselbe Recht; welcher Name
erscheint, hängt an der Ausgabesprache, nicht am Rechtsraum. Das gehört in
Block 3 und wird hier vorbereitet, indem die europäischen Angaben an einer
Stelle stehen: eine Sprachebene lässt sich darüber legen, ohne die Aufrufer
anzufassen.

**Rein nationale Pflichten.** Impressum, AGB-Kontrolle, Preisangaben,
Widerrufsrecht und Kündigungsbutton haben zwar europäische Richtlinien im
Hintergrund, aber die konkrete Pflicht steht im nationalen Umsetzungsrecht und
unterscheidet sich erheblich. Die zugehörigen Prüfungen sind im Profil `eu`
abgeschaltet (`jurisdictions.py`). Ihre Themen stehen hier, ihre Fundstellen im
Prüfkern werden aber erst mit Block 1 umgestellt, wenn die Engine den
Rechtsraum tatsächlich liest. Bis dahin wäre die Umstellung eine Änderung ohne
Wirkung, die nur das Risiko trägt, deutsche Detailangaben zu verlieren.
"""

import logging
from typing import Dict, Optional

from compliance_engine.jurisdictions import (
    DEFAULT_JURISDICTION,
    normalize_jurisdiction,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Themen. Ein geschlossener Satz: ein Tippfehler darf keine stille Falschangabe
# erzeugen, deshalb wirft `grundlage()` bei unbekanntem Thema.
# --------------------------------------------------------------------------
# Zwei Arten, wie europäische und nationale Angabe zusammenspielen.
#
# ZUSAMMEN: beide gehören in die Angabe. Bei der Barrierefreiheit ist WCAG die
#   Prüfsubstanz und das BFSG nur der Paragraf, der sie anordnet. Wer eines von
#   beiden weglässt, verliert entweder das Kriterium oder die Pflicht.
#
# ERSETZT: der nationale Anker tritt an die Stelle der Richtlinie. Bei Cookies
#   und beim Impressum zitiert man in Deutschland § 25 TDDDG, nicht die
#   ePrivacy-Richtlinie; sie steht nur dahinter. Erst wo kein nationaler Anker
#   geprüft ist, wird die Richtlinie selbst genannt.
#
# Diese Unterscheidung hält die deutsche Ausgabe unverändert. Block 0 soll den
# Rechtsraum beweglich machen, nicht die Befunde deutscher Kunden umschreiben.
ZUSAMMEN = "zusammen"
ERSETZT = "ersetzt"

BARRIEREFREIHEIT_TECHNISCH = "barrierefreiheit_technisch"
BARRIEREFREIHEITSERKLAERUNG = "barrierefreiheitserklaerung"
COOKIE_EINWILLIGUNG = "cookie_einwilligung"
ANBIETERKENNZEICHNUNG = "anbieterkennzeichnung"
AGB_KONTROLLE = "agb_kontrolle"
WIDERRUF = "widerruf"
PREISANGABE = "preisangabe"
IRREFUEHRUNG = "irrefuehrung"
KUENDIGUNGSBUTTON = "kuendigungsbutton"


# Die europäisch einheitliche Grundlage je Thema.
# `None` heisst: es gibt keine unmittelbar zitierfähige europäische Vorgabe,
# die Pflicht entsteht erst im nationalen Recht.
EUROPAEISCH: Dict[str, Optional[str]] = {
    BARRIEREFREIHEIT_TECHNISCH: "WCAG 2.1",
    BARRIEREFREIHEITSERKLAERUNG: "EU-Richtlinie 2019/882 (European Accessibility Act)",
    COOKIE_EINWILLIGUNG: "Richtlinie 2002/58/EG Art. 5 Abs. 3",
    ANBIETERKENNZEICHNUNG: "Richtlinie 2000/31/EG Art. 5",
    AGB_KONTROLLE: "Richtlinie 93/13/EWG",
    WIDERRUF: "Richtlinie 2011/83/EU",
    PREISANGABE: "Richtlinie 98/6/EG",
    IRREFUEHRUNG: "Richtlinie 2005/29/EG",
    KUENDIGUNGSBUTTON: None,
}


# Wie die beiden Teile zusammengesetzt werden. Siehe ZUSAMMEN / ERSETZT oben.
VERBUND: Dict[str, str] = {
    BARRIEREFREIHEIT_TECHNISCH: ZUSAMMEN,
    BARRIEREFREIHEITSERKLAERUNG: ZUSAMMEN,
    COOKIE_EINWILLIGUNG: ERSETZT,
    ANBIETERKENNZEICHNUNG: ERSETZT,
    AGB_KONTROLLE: ERSETZT,
    WIDERRUF: ERSETZT,
    PREISANGABE: ERSETZT,
    IRREFUEHRUNG: ERSETZT,
    KUENDIGUNGSBUTTON: ERSETZT,
}


# Der Anker je Rechtsraum: die Vorschrift, die die europäische Vorgabe dort
# anordnet. Für `eu` steht die harmonisierte Norm selbst, weil es dort keinen
# nationalen Gesetzgeber gibt, den man zitieren könnte.
#
# Ein fehlender Eintrag ist kein Fehler, sondern eine Aussage: für dieses Thema
# ist in diesem Rechtsraum keine Fundstelle geprüft. Dann wird sie auch nicht
# genannt.
ANKER: Dict[str, Dict[str, str]] = {
    # Schreibweise bewusst so, wie sie bisher im Prüfkern stand. Block 0 macht
    # den Rechtsraum beweglich; ob "BFSG §12" die richtige Fundstelle und die
    # saubere Zitierweise ist, gehört zur anwaltlichen Prüfung (Kennung A1) und
    # nicht in einen Umbau der Technik.
    "de": {
        BARRIEREFREIHEIT_TECHNISCH: "BFSG §12",
        BARRIEREFREIHEITSERKLAERUNG: "BFSG §14",
        COOKIE_EINWILLIGUNG: "TDDDG §25",
        ANBIETERKENNZEICHNUNG: "DDG §5",
        AGB_KONTROLLE: "BGB §305 ff.",
        WIDERRUF: "BGB §355 ff., EGBGB Art. 246a §1",
        PREISANGABE: "PAngV §3",
        IRREFUEHRUNG: "UWG §5",
        KUENDIGUNGSBUTTON: "BGB §312k",
    },
    "eu": {
        BARRIEREFREIHEIT_TECHNISCH: "EN 301 549",
        # Für die übrigen Themen gibt es keinen einheitlichen europäischen
        # Anker. Die Prüfungen sind im Profil `eu` abgeschaltet; genannt wird
        # dann allein die Richtlinie aus EUROPAEISCH.
    },
}


def bekannte_themen() -> frozenset:
    """Alle Themen, die dieses Modul kennt. Grundlage des Wächtertests."""
    return frozenset(EUROPAEISCH)


def anker(thema: str, jurisdiction: str = DEFAULT_JURISDICTION) -> Optional[str]:
    """Der nationale Anker, oder None, wenn für diesen Rechtsraum keiner geprüft ist."""
    if thema not in EUROPAEISCH:
        raise ValueError(f"Unbekanntes Rechtsthema: {thema!r}")
    return ANKER.get(normalize_jurisdiction(jurisdiction), {}).get(thema)


def grundlage(
    thema: str,
    jurisdiction: str = DEFAULT_JURISDICTION,
    detail: Optional[str] = None,
) -> str:
    """Setzt die Rechtsgrundlage eines Befundes zusammen.

    `detail` ergänzt die europäische Angabe, etwa das WCAG-Kriterium:

        grundlage(BARRIEREFREIHEIT_TECHNISCH, "de", "Level A (1.1.1)")
            -> "WCAG 2.1 Level A (1.1.1), BFSG §12"      (ZUSAMMEN)
        grundlage(BARRIEREFREIHEIT_TECHNISCH, "eu", "Level A (1.1.1)")
            -> "WCAG 2.1 Level A (1.1.1), EN 301 549"
        grundlage(COOKIE_EINWILLIGUNG, "de")
            -> "TDDDG §25"                                (ERSETZT)
        grundlage(COOKIE_EINWILLIGUNG, "eu")
            -> "Richtlinie 2002/58/EG Art. 5 Abs. 3"

    Fehlt der nationale Anker, bleibt die europäische Angabe allein stehen.
    Fehlen beide, ist das Ergebnis leer; das wird protokolliert, weil ein
    Befund ohne Grundlage ein Befund ohne Begründung ist.
    """
    if thema not in EUROPAEISCH:
        raise ValueError(f"Unbekanntes Rechtsthema: {thema!r}")

    jur = normalize_jurisdiction(jurisdiction)
    eu = EUROPAEISCH[thema]
    national = ANKER.get(jur, {}).get(thema)
    teile = []

    if VERBUND[thema] == ERSETZT and national:
        # Der nationale Anker tritt an die Stelle der Richtlinie. Ein Detail
        # gehört dann davor, weil es die Fundstelle näher bestimmt.
        teile.append(f"{national} {detail}".strip() if detail else national)
    else:
        if eu:
            teile.append(f"{eu} {detail}".strip() if detail else eu)
        elif detail:
            teile.append(detail)
        if national:
            teile.append(national)

    if not teile:
        logger.warning(
            "Keine Rechtsgrundlage fuer Thema %r im Rechtsraum %r. Der Befund "
            "wird ohne Begruendung ausgegeben.", thema, jur,
        )
        return ""
    return ", ".join(teile)
