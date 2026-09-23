"""Die Rechtsgrundlage eines Befundes muss zum Rechtsraum passen.

Gezaehlt am 23.09.2026: 158 ausgegebene Nennungen deutscher Gesetze im
Pruefkern, davon 67 mal das BFSG, verteilt auf 20 Dateien. Die Engine las den
Rechtsraum nicht, also haette ein niederlaendischer Kunde Befunde bekommen, die
ihm die Verletzung deutschen Rechts vorwerfen.

Diese Pruefungen halten drei Dinge fest:

1. Die Zusammensetzung stimmt, und zwar in beide Richtungen: bei der
   Barrierefreiheit gehoeren WCAG und nationaler Anker zusammen, bei Cookies und
   Impressum ersetzt der nationale Anker die Richtlinie.
2. **Die deutsche Ausgabe bleibt unveraendert.** Block 0 soll den Rechtsraum
   beweglich machen, nicht die Befunde deutscher Kunden umschreiben. Die
   Zeichenketten hier sind aus dem Quelltext vor der Umstellung abgeschrieben.
3. Eine Luecke fuehrt nie zum deutschen Gesetz als Rueckfall, sondern zur
   europaeischen Angabe allein. Dieselbe Regel wie bei Alternativtexten und
   `role=main`: lieber keine Angabe als eine falsche.
"""
import pytest

from compliance_engine.rechtsgrundlagen import (
    AGB_KONTROLLE,
    ANBIETERKENNZEICHNUNG,
    ANKER,
    BARRIEREFREIHEIT_TECHNISCH,
    BARRIEREFREIHEITSERKLAERUNG,
    COOKIE_EINWILLIGUNG,
    ERSETZT,
    EUROPAEISCH,
    KUENDIGUNGSBUTTON,
    VERBUND,
    ZUSAMMEN,
    anker,
    bekannte_themen,
    grundlage,
)


# ---------------------------------------------------------------------------
# Die deutsche Ausgabe, Zeichen fuer Zeichen wie vor der Umstellung
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("thema,detail,erwartet", [
    (BARRIEREFREIHEIT_TECHNISCH, "Level A (1.1.1)", "WCAG 2.1 Level A (1.1.1), BFSG §12"),
    (BARRIEREFREIHEIT_TECHNISCH, "(4.1.2)", "WCAG 2.1 (4.1.2), BFSG §12"),
    (BARRIEREFREIHEIT_TECHNISCH, "Level AA (1.4.3)", "WCAG 2.1 Level AA (1.4.3), BFSG §12"),
    (BARRIEREFREIHEIT_TECHNISCH, "(1.3.1, 1.4.4, 4.1.2)", "WCAG 2.1 (1.3.1, 1.4.4, 4.1.2), BFSG §12"),
    (COOKIE_EINWILLIGUNG, None, "TDDDG §25"),
    (ANBIETERKENNZEICHNUNG, None, "DDG §5"),
])
def test_deutsche_ausgabe_bleibt_gleich(thema, detail, erwartet):
    assert grundlage(thema, "de", detail) == erwartet


def test_deutsche_cookie_angabe_mit_zusatz():
    """So setzt cookie_check.py die Angabe heute zusammen."""
    assert (grundlage(COOKIE_EINWILLIGUNG, "de") + ", DSGVO Art. 7 und Art. 13"
            == "TDDDG §25, DSGVO Art. 7 und Art. 13")


# ---------------------------------------------------------------------------
# Der Rechtsraum wirkt
# ---------------------------------------------------------------------------
def test_eu_nennt_die_harmonisierte_norm_statt_des_bfsg():
    wert = grundlage(BARRIEREFREIHEIT_TECHNISCH, "eu", "Level A (1.1.1)")
    assert wert == "WCAG 2.1 Level A (1.1.1), EN 301 549"
    assert "BFSG" not in wert


def test_eu_nennt_die_richtlinie_statt_des_tdddg():
    wert = grundlage(COOKIE_EINWILLIGUNG, "eu")
    assert wert == "Richtlinie 2002/58/EG Art. 5 Abs. 3"
    assert "TDDDG" not in wert


@pytest.mark.parametrize("thema", sorted(bekannte_themen()))
def test_kein_deutsches_gesetz_im_eu_profil(thema):
    """Der Kern der ganzen Uebung.

    Egal welches Thema: im Profil `eu` darf keine deutsche Vorschrift stehen.
    Faellt ein Thema hier durch, hat jemand einen Anker unter dem falschen
    Rechtsraum eingetragen.
    """
    wert = grundlage(thema, "eu")
    for norm in ("BFSG", "TDDDG", "DDG", "PAngV", "UWG", "BGB", "TMG", "EGBGB"):
        assert norm not in wert, f"{thema}: {wert!r} nennt {norm} im EU-Profil"


# ---------------------------------------------------------------------------
# Luecken
# ---------------------------------------------------------------------------
def test_fehlender_anker_faellt_nicht_auf_deutschland_zurueck():
    assert anker(ANBIETERKENNZEICHNUNG, "eu") is None
    assert grundlage(ANBIETERKENNZEICHNUNG, "eu") == "Richtlinie 2000/31/EG Art. 5"


def test_rein_nationale_pflicht_bleibt_im_eu_profil_leer(caplog):
    """Der Kuendigungsbutton hat keine europaeische Entsprechung.

    Leer ist hier die richtige Antwort: die Pflicht gibt es dort nicht. Dass
    die Pruefung im EU-Profil ueberhaupt nicht laeuft, regelt Block 1; bis
    dahin protokolliert die Stelle wenigstens, dass sie nichts sagen kann.
    """
    assert EUROPAEISCH[KUENDIGUNGSBUTTON] is None
    with caplog.at_level("WARNING"):
        assert grundlage(KUENDIGUNGSBUTTON, "eu") == ""
    assert any("kuendigungsbutton" in s.message for s in caplog.records)


def test_unbekannter_rechtsraum_wird_zu_deutschland():
    """Normalisierung wie in jurisdictions.py: unbekannt heisst Vorgabe."""
    assert grundlage(COOKIE_EINWILLIGUNG, "kl-ingonisch") == grundlage(COOKIE_EINWILLIGUNG, "de")


def test_tippfehler_im_thema_wirft():
    """Ein unbekanntes Thema darf keine stille Falschangabe erzeugen."""
    with pytest.raises(ValueError):
        grundlage("barrierefreiheit_tecnisch", "de")
    with pytest.raises(ValueError):
        anker("gibtsnicht", "de")


# ---------------------------------------------------------------------------
# Die Tabelle selbst
# ---------------------------------------------------------------------------
def test_jedes_thema_hat_einen_verbund():
    assert set(VERBUND) == bekannte_themen()
    assert set(VERBUND.values()) <= {ZUSAMMEN, ERSETZT}


def test_jeder_anker_gehoert_zu_einem_bekannten_thema():
    for jur, eintraege in ANKER.items():
        unbekannt = set(eintraege) - bekannte_themen()
        assert not unbekannt, f"Rechtsraum {jur} nennt unbekannte Themen: {unbekannt}"


def test_jedes_thema_ist_irgendwo_zitierfaehig():
    """Ein Thema ohne europaeische Grundlage braucht mindestens einen Anker.

    Sonst waere es ein Thema, zu dem das System nie etwas sagen kann.
    """
    for thema in bekannte_themen():
        if EUROPAEISCH[thema]:
            continue
        assert any(thema in e for e in ANKER.values()), (
            f"{thema} hat weder europaeische Grundlage noch irgendeinen Anker")
