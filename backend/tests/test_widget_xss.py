# -*- coding: utf-8 -*-
"""
Was unser Widget in eine Kundenseite schreibt, darf kein Code sein.

Die Struktur-Ansicht des Barrierefreiheits-Widgets liest Ueberschriften,
Landmarken und Links AUS der Kundenseite und setzte sie bis zum 09.09.2026 roh
per innerHTML wieder ein. Auf jeder Seite mit fremden Beitraegen — ein Blog mit
Kommentaren genuegt — reicht dafuer ein Linktext wie "<img src=x onerror=...>":
`textContent` gibt die spitzen Klammern als Zeichen zurueck, `innerHTML` macht
daraus wieder ein Element. Complyo waere damit der Weg gewesen, ueber den
fremder Code auf einer Kundenseite laeuft. Bei einem Produkt, das
Rechtssicherheit verkauft, ist das die teuerste Art von Fehler.

Der Test prueft statisch, dass in den betroffenen Vorlagen keine Einsetzung
ohne Entschaerfer steht.
"""

import os
import re

import pytest

WIDGETS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "widgets"
)

ENTSCHAERFER = ("complyoEsc", "complyoSichereUrl", "sanitizeText", "sanitizeUrl")

# Funktion -> Datei. Jede baut HTML aus Fremddaten.
AUS_FREMDDATEN = [
    ("accessibility-v6.js", "getHeadingsHTML"),
    ("accessibility-v6.js", "getLandmarksHTML"),
    ("accessibility-v6.js", "getLinksHTML"),
]


def _funktionsrumpf(quelle: str, name: str) -> str:
    start = quelle.index(name + "(")
    tiefe, i, begonnen = 0, start, False
    while i < len(quelle):
        if quelle[i] == "{":
            tiefe += 1
            begonnen = True
        elif quelle[i] == "}":
            tiefe -= 1
            if begonnen and tiefe == 0:
                return quelle[start:i + 1]
        i += 1
    raise AssertionError(f"Rumpf von {name} nicht gefunden")


@pytest.mark.parametrize("datei,funktion", AUS_FREMDDATEN)
def test_seiteninhalt_wird_entschaerft(datei, funktion):
    quelle = open(os.path.join(WIDGETS, datei), encoding="utf-8").read()
    rumpf = _funktionsrumpf(quelle, funktion)
    roh = [
        a.strip() for a in re.findall(r"\$\{([^{}]{1,90})\}", rumpf)
        if not any(e in a for e in ENTSCHAERFER)
        and not re.fullmatch(r"[\w.\s?:'+*/\-\[\]()]*", a.replace("isExternal", ""))
    ]
    # Nur Einsetzungen, die tatsaechlich Fremddaten fuehren koennen
    verdaechtig = [
        a for a in re.findall(r"\$\{([^{}]{1,90})\}", rumpf)
        if not any(e in a for e in ENTSCHAERFER)
        and any(q in a for q in ("text", "label", "role", "href", "name", "title"))
    ]
    assert not verdaechtig, (
        f"{datei}::{funktion} setzt Fremddaten ohne Entschaerfer ein: {verdaechtig}"
    )


def test_entschaerfer_existiert_und_deckt_die_gefaehrlichen_zeichen_ab():
    quelle = open(os.path.join(WIDGETS, "accessibility-v6.js"), encoding="utf-8").read()
    assert "function complyoEsc" in quelle
    rumpf = _funktionsrumpf(quelle, "complyoEsc")
    for zeichen in ("&amp;", "&lt;", "&gt;", "&quot;", "&#x27;"):
        assert zeichen in rumpf, f"complyoEsc ersetzt {zeichen} nicht"


@pytest.mark.parametrize("datei,helfer", [
    ("accessibility-v6.js", "complyoSichereUrl"),
    ("cookie_banner_v2.js", "sanitizeUrl"),
])
def test_nur_oeffnende_schemata_in_links(datei, helfer):
    """`javascript:` in einem href ist Code, kein Ziel."""
    quelle = open(os.path.join(WIDGETS, datei), encoding="utf-8").read()
    rumpf = _funktionsrumpf(quelle, helfer)
    assert "https?:" in rumpf, f"{helfer} prueft das Schema nicht"
    assert "javascript" not in rumpf.lower() or "return '#'" in rumpf


def test_anbieterdaten_im_banner_werden_entschaerft():
    quelle = open(os.path.join(WIDGETS, "cookie_banner_v2.js"), encoding="utf-8").read()
    for roh in ("${provider.address}", "${provider.privacy_url}", "${provider.cookie_url}"):
        assert roh not in quelle, f"{roh} steht roh in einer HTML-Vorlage"
