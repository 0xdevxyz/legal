# -*- coding: utf-8 -*-
"""
Zu jeder Einwilligung muss belegbar sein, WELCHER Banner dem Besucher vorlag.

Art. 7 Abs. 1 DSGVO verlangt den Nachweis der Einwilligung. Das Protokoll
speicherte dafuer `revision_id` — darin stand aber die ID der
Konfigurationszeile. Die bleibt gleich, waehrend der Banner sich aendert. Zu
den 1.151 erfassten Einwilligungen liess sich damit nicht sagen, worauf sie
sich bezogen.

Die Fassungen selbst gab es die ganze Zeit: der Datenbank-Trigger
`trigger_banner_revision` legt bei jeder inhaltlichen Aenderung einen
Schnappschuss in `cookie_banner_revisions` ab. Nur:

  * das Protokoll schrieb die Fassung nicht mit, und
  * der Endpunkt, der die Fassungen zeigen soll, las
    `cookie_consent_revisions` — eine Tabelle, die es nicht gibt, und
    antwortete mit 500.

Ein Nachweis, den niemand abrufen kann, ist keiner.
"""

import ast
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUELLE = os.path.join(BACKEND, "cookie_compliance_routes.py")


def _text():
    return open(QUELLE, encoding="utf-8").read()


def test_protokoll_schreibt_die_banner_fassung_mit():
    t = _text()
    assert "banner_revision" in t, "Die Fassung wird nicht mitgeschrieben"
    einfuegung = t[t.index("INSERT INTO cookie_consent_logs"):]
    einfuegung = einfuegung[:600]
    assert "banner_revision" in einfuegung, (
        "banner_revision fehlt im INSERT des Einwilligungsprotokolls")


def test_fassung_kommt_aus_der_konfiguration():
    t = _text()
    assert "SELECT id, revision FROM cookie_banner_configs" in t, (
        "Die Fassung wird nicht aus cookie_banner_configs gelesen")


def test_protokollieren_scheitert_nicht_an_einer_fehlenden_spalte():
    """Der empfindlichste Schreibweg im System darf nicht wegen einer Spalte umfallen."""
    t = _text()
    stelle = t[t.index("banner_revision = ("):][:400]
    assert '"revision" in config_row' in stelle, (
        "Der Zugriff auf die Fassung ist nicht abgesichert")


def test_fassungshistorie_liest_die_tabelle_die_es_gibt():
    t = _text()
    assert "FROM cookie_banner_revisions" in t, (
        "Die Fassungshistorie liest nicht cookie_banner_revisions")
    assert "FROM cookie_consent_revisions" not in t, (
        "cookie_consent_revisions gibt es nicht — der Endpunkt liefe wieder in einen 500er")


def test_export_weist_die_fassung_aus():
    """Der CSV-Export ist das, was einer Aufsichtsbehoerde vorgelegt wird."""
    t = _text()
    ausschnitt = t[t.index("'ID', 'Zeitstempel (UTC)'"):][:900]
    assert "Banner-Fassung" in ausschnitt, "Der Export nennt die Fassung nicht"
    assert "nicht erfasst" in t, (
        "Fuer Altdaten muss 'nicht erfasst' stehen — eine erfundene Zahl waere "
        "ein Nachweis, der bei der ersten Nachfrage bricht")
