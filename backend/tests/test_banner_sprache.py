"""Das Einwilligungsbanner spricht die Sprache des Besuchers.

Anlass (25.09.2026): Ein franzoesischer Besucher auf einer Kundenseite sah ein
deutsches Banner, obwohl die franzoesische Uebersetzung geladen war.

Der Weg dorthin hatte drei Schritte, und nur der letzte war falsch:

  1. `translations.js` haelt Texte fuer alle 17 erkannten Sprachen bereit.
  2. Das Banner mischt die Uebersetzung fuer die Browsersprache hinein.
  3. Danach ueberschrieb es sie mit der gespeicherten Konfiguration des
     Kunden — und fiel dabei auf 'de' zurueck, wenn die Sprache des Besuchers
     dort fehlte. Sie fehlt immer: die Standardtexte im Server legen nur
     Deutsch an, gemessen an der Konfiguration von loqal-io (`texts: ['de']`).

Eine Einwilligung, die der Besucher nicht lesen kann, ist keine informierte
Einwilligung (Art. 4 Nr. 11 DSGVO). Der Mangel war also nicht kosmetisch, und
ausgerechnet in dem Werkzeug, mit dem complyo genau das bei anderen prueft.
"""
import os
import re

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*teile):
    pfad = os.path.join(_BACKEND, *teile)
    if not os.path.exists(pfad):
        pytest.skip(f"{pfad} nicht eingehaengt")
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


SPRACHEN = ["de", "en", "fr", "es", "it", "nl", "pl", "pt", "sv",
            "da", "fi", "no", "cs", "hu", "ro", "el", "ru"]


def test_fuer_jede_erkannte_sprache_gibt_es_auch_texte():
    """Die Erkennungsliste und die Uebersetzungstabelle muessen sich decken.

    Eine Sprache zu erkennen, fuer die es keinen Text gibt, heisst: der
    Besucher bekommt irgendetwas, nur nicht seine Sprache.
    """
    banner = _lese("widgets", "cookie_banner_v2.js")
    m = re.search(r"const SUPPORTED_LANGUAGES = \[([^\]]+)\]", banner)
    assert m, "Die Liste der erkannten Sprachen ist nicht mehr auffindbar."
    erkannt = set(re.findall(r"'([a-z]{2})'", m.group(1)))

    tabelle = _lese("widgets", "locales", "translations.js")
    vorhanden = set(re.findall(r"^  ([a-z]{2}):\s*\{", tabelle, re.M))

    fehlen = erkannt - vorhanden
    assert not fehlen, (
        f"Diese Sprachen werden erkannt, haben aber keine Texte: {sorted(fehlen)}")


def test_kein_rueckfall_auf_deutsch():
    """Die Gegenprobe gegen den Rueckfall, namentlich.

    Die Zeile `serverConfig.texts['de']` hat die geladene Uebersetzung wieder
    zunichte gemacht. Kommt sie zurueck, kommt das deutsche Banner fuer
    franzoesische Besucher mit ihr.
    """
    banner = _lese("widgets", "cookie_banner_v2.js")
    code = "\n".join(z for z in banner.split("\n")
                     if not z.strip().startswith("//"))
    assert "serverConfig.texts['de']" not in code, (
        "Der Rueckfall auf Deutsch ist zurueck. Er ueberschreibt die "
        "Uebersetzung, die zwei Zeilen vorher geladen wurde.")


def test_kundentext_gilt_nur_in_der_sprache_des_besuchers():
    banner = _lese("widgets", "cookie_banner_v2.js")
    i = banner.index("let serverTexts = null;")
    stelle = banner[i:i + 400]
    assert "serverConfig.texts[browserLang]" in stelle, (
        "Der Kundentext wird nicht mehr an der Sprache des Besuchers "
        "festgemacht.")


def test_ablehnen_ist_in_jeder_sprache_vorhanden():
    """Gleichrangigkeit ist keine Frage der Gestaltung allein.

    Fehlt in einer Sprache der Ablehnen-Text, faellt die Schaltflaeche auf den
    Schluesselnamen oder auf Englisch zurueck — und ein Banner, dessen
    Zustimmen-Knopf uebersetzt ist und dessen Ablehnen-Knopf nicht, ist genau
    der Befund, den complyo bei seinen Kunden erhebt.
    """
    tabelle = _lese("widgets", "locales", "translations.js")
    fehlen = []
    for code in SPRACHEN:
        m = re.search(r"^  %s:\s*\{(.*?)\n  \}" % code, tabelle, re.S | re.M)
        if not m:
            fehlen.append(f"{code}: Block fehlt")
            continue
        if "rejectAll" not in m.group(1):
            fehlen.append(f"{code}: rejectAll fehlt")
    assert not fehlen, "; ".join(fehlen)
