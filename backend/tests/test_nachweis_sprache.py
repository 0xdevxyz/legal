"""Das lang-Attribut des Pruefnachweises muss zum Text passen.

Die Seite, auf der complyo seine Messung vorzeigt, ist der letzte Ort, an dem
ein Barrierefreiheitsfehler stehen darf. Ein falsches lang-Attribut ist genau
so einer: Screenreader sprechen deutschen Text dann mit englischer Aussprache,
WCAG 3.1.1.

Bis zum 23.09.2026 stand dort fest `<html lang="de">`. Das war richtig, solange
es nur deutsche Kunden gibt, aber es war eine Annahme ohne Namen. Jetzt ist sie
eine Konstante mit Begruendung, und diese Pruefungen halten fest, dass sie den
TEXT beschreibt und nicht den Rechtsraum.
"""
from compliance_engine.nachweis_generator import baue_nachweis
from compliance_engine.nachweis_seite import (
    SPRACHE_DES_INHALTS,
    erklaerung_als_html,
    nachweis_als_html,
)

# Ueber den echten Erzeuger statt ueber ein handgeschriebenes Dict: ein
# Beispiel, das an der Wirklichkeit vorbeigeht, prueft nichts.
BEISPIEL = baue_nachweis(
    site_id="beispiel-de", site_url="https://beispiel.de",
    messung_vorher={"image-alt": 5},
    messung_nachher={"image-alt": 0},
    fixes=[{"regel": "image-alt", "fundstellen": 5}],
    vorbereitet=[],
)


def test_vorgabe_ist_deutsch():
    """Solange die Texte deutsch sind, muss das Attribut deutsch sein."""
    assert SPRACHE_DES_INHALTS == "de"
    assert '<html lang="de">' in nachweis_als_html(BEISPIEL)
    assert '<html lang="de">' in erklaerung_als_html("# Titel\n\nText.", "https://beispiel.de")


def test_sprache_ist_setzbar():
    """Block 3 braucht den Parameter, deshalb existiert er jetzt schon."""
    assert '<html lang="nl">' in nachweis_als_html(BEISPIEL, sprache="nl")
    assert '<html lang="nl">' in erklaerung_als_html(
        "# Titel\n\nText.", "https://beispiel.de", sprache="nl")


def test_sprache_wird_maskiert():
    """Der Wert landet in einem Attribut, also darf er es nicht verlassen."""
    html = nachweis_als_html(BEISPIEL, sprache='de" onload="alert(1)')
    assert 'onload="alert(1)"' not in html
    assert "&quot;" in html or "&#34;" in html


def test_kein_festes_lang_attribut_mehr_im_quelltext():
    """Die Gegenprobe gegen einen Rueckfall.

    Wer das Attribut wieder fest verdrahtet, macht den Parameter wirkungslos,
    ohne dass ein Test anschlaegt, weil die Vorgabe ja stimmt.
    """
    import pathlib
    quelle = (pathlib.Path(__file__).resolve().parent.parent
              / "compliance_engine" / "nachweis_seite.py").read_text(encoding="utf-8")
    assert '<html lang="de">' not in quelle, (
        "nachweis_seite.py verdrahtet das lang-Attribut wieder fest. "
        "Es gehoert an SPRACHE_DES_INHALTS bzw. an den Parameter.")
