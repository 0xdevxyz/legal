"""Eine Sicherung, die nie zurückgespielt wurde, ist eine Vermutung.

Bis zum 07.09.2026 gab es für die complyo-Datenbank weder einen Zeitplan noch
eine Prüfung: gesichert wurde nur, wenn jemand vor einer Migration von Hand
einen Abzug zog, und alle Abzüge lagen auf derselben Maschine wie die
Datenbank.

Diese Tests halten die beiden Eigenschaften fest, an denen sich eine echte von
einer scheinbaren Sicherung unterscheidet:

1. **Jeder Abzug wird sofort zurückgespielt und verglichen.** Sonst faellt eine
   Sicherung, die nur das Schema enthaelt, erst im Ernstfall auf.
2. **Ein stillschweigender Fehlschlag wird gemeldet.** Eine Sicherung, die
   nicht laeuft, sieht von aussen genauso aus wie eine, die laeuft — das ist
   dieselbe Fehlerklasse wie beim Banner-Ausfall und bei der toten
   Alt-Text-Speicherung.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

HIER = os.path.dirname(__file__)
BACKEND = os.path.abspath(os.path.join(HIER, '..'))
WURZEL = os.path.abspath(os.path.join(BACKEND, '..'))
sys.path.insert(0, os.path.join(BACKEND, 'cronjobs'))

SKRIPT = os.path.join(WURZEL, 'scripts', 'datensicherung.sh')


def _lies(pfad):
    with open(pfad, encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Das Skript
# ---------------------------------------------------------------------------

class TestSicherungsskript:
    def test_es_gibt_das_skript_und_es_ist_ausfuehrbar(self):
        assert os.path.exists(SKRIPT)
        assert os.access(SKRIPT, os.X_OK), "ohne Ausführungsrecht startet der Cron es nicht"

    def test_zeigt_auf_den_container_den_es_wirklich_gibt(self):
        """Das alte backup-system.sh zeigt auf `shared-postgres-production`
        und auf /opt/projects/saas-project-2/.env. Beides gibt es hier nicht.
        Ein Skript, das beim ersten Lauf scheitert, ist schlechter als keins:
        es sieht aus wie Vorsorge."""
        s = _lies(SKRIPT)
        # Auf die Zuweisung pruefen, nicht auf das Wort: der Kommentar im
        # Skript nennt den alten Container, um zu erklaeren, warum es ihn
        # nicht mehr benutzt. Ein Test, der das Wort verbietet, verbietet die
        # Begruendung mit.
        zuweisungen = [z.strip() for z in s.splitlines()
                       if z.strip().startswith('DB_CONTAINER=')]
        assert zuweisungen == ['DB_CONTAINER="complyo-postgres"']

    def test_spielt_jeden_abzug_zur_probe_zurueck(self):
        s = _lies(SKRIPT)
        assert 'CREATE DATABASE $TESTDB' in s
        assert 'pg_restore -U "$DB_USER" -d "$TESTDB"' in s
        assert 'DROP DATABASE IF EXISTS $TESTDB' in s

    def test_vergleicht_zeilen_und_nicht_nur_den_rueckgabewert(self):
        """pg_restore meldet auch Kleinigkeiten wie fehlende Erweiterungen.
        Wer seinen Rückgabewert als Urteil nimmt, verwirft brauchbare
        Sicherungen — oder schlimmer, haelt eine Schema-only-Sicherung fuer
        gueltig, weil sie fehlerfrei einspielt."""
        s = _lies(SKRIPT)
        assert 'pg_stat_user_tables' in s
        assert 'ZU_LEER' in s
        assert 'FEHLEND' in s

    def test_erkennt_einen_abzug_der_zu_klein_ist(self):
        s = _lies(SKRIPT)
        assert '-lt 100000' in s

    def test_schreibt_die_marke_bei_jedem_ausstieg(self):
        """`trap ... EXIT`: auch der Fehlschlag hinterlaesst eine Marke.
        Nur so laesst sich "lief und scheiterte" von "lief gar nicht"
        unterscheiden."""
        s = _lies(SKRIPT)
        assert 'trap marke_schreiben EXIT' in s
        assert '"wiederherstellung_geprueft"' in s

    def test_haelt_zwei_laeufe_auseinander(self):
        """Zwei gleichzeitige Läufe würden sich über dieselbe
        Wegwerf-Datenbank in die Quere kommen."""
        s = _lies(SKRIPT)
        assert 'flock -n 9' in s

    def test_kopie_ausser_haus_ist_vorbereitet_aber_nicht_erfunden(self):
        """Solange kein Ziel hinterlegt ist, sagt die Marke das auch. Eine
        Sicherung, die neben der Datenbank liegt, darf sich nicht als
        auswaertige ausgeben."""
        s = _lies(SKRIPT)
        assert 'ZIELDATEI=' in s
        assert 'nicht eingerichtet' in s

    def test_raeumt_auf(self):
        s = _lies(SKRIPT)
        assert 'TAGE_TAEGLICH=14' in s
        assert '-mtime "+$TAGE_TAEGLICH" -print -delete' in s


# ---------------------------------------------------------------------------
# Der Wächter
# ---------------------------------------------------------------------------

@pytest.fixture()
def waechter(tmp_path, monkeypatch):
    monkeypatch.setenv("WAECHTER_SICHERUNG_MARKE", str(tmp_path / "marke.json"))
    for modul in ("betriebswaechter",):
        sys.modules.pop(modul, None)
    import betriebswaechter
    return betriebswaechter, tmp_path / "marke.json"


def marke(pfad, **felder):
    grund = {
        "zeitpunkt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ergebnis": "erfolgreich",
        "meldung": "Abzug geschrieben und Wiederherstellung geprüft",
        "wiederherstellung_geprueft": "ja",
    }
    grund.update(felder)
    pfad.write_text(json.dumps(grund))


class TestWaechter:
    def test_frische_geprueft_sicherung_meldet_nichts(self, waechter):
        bw, pfad = waechter
        marke(pfad)
        assert bw.pruefe_datensicherung() == []

    def test_fehlende_marke_ist_ein_befund(self, waechter):
        """Der gefährlichste Zustand: es läuft gar nichts, und von aussen
        sieht das genauso aus wie ein stiller, erfolgreicher Lauf."""
        bw, _ = waechter
        befunde = bw.pruefe_datensicherung()
        assert [s for s, _ in befunde] == ["sicherung-nie-gelaufen"]

    def test_fehlgeschlagene_sicherung_wird_gemeldet(self, waechter):
        bw, pfad = waechter
        marke(pfad, ergebnis="fehlgeschlagen", meldung="pg_dump gescheitert")
        schluessel = [s for s, _ in bw.pruefe_datensicherung()]
        assert "sicherung-fehlgeschlagen" in schluessel

    def test_abzug_ohne_probe_wird_gemeldet(self, waechter):
        """Es gibt eine Datei, aber keine Zusage. Genau der Unterschied,
        um den es geht."""
        bw, pfad = waechter
        marke(pfad, wiederherstellung_geprueft="nein")
        schluessel = [s for s, _ in bw.pruefe_datensicherung()]
        assert "sicherung-ungeprueft" in schluessel

    def test_veraltete_sicherung_wird_gemeldet(self, waechter):
        bw, pfad = waechter
        alt = datetime.now(timezone.utc) - timedelta(hours=40)
        marke(pfad, zeitpunkt=alt.strftime("%Y-%m-%dT%H:%M:%SZ"))
        schluessel = [s for s, _ in bw.pruefe_datensicherung()]
        assert "sicherung-veraltet" in schluessel

    def test_gerade_noch_frisch_meldet_nicht(self, waechter):
        """Der Lauf um 02:30 und die stündliche Prüfung dürfen sich nicht
        gegenseitig auslösen."""
        bw, pfad = waechter
        knapp = datetime.now(timezone.utc) - timedelta(hours=29)
        marke(pfad, zeitpunkt=knapp.strftime("%Y-%m-%dT%H:%M:%SZ"))
        assert bw.pruefe_datensicherung() == []

    def test_uebersprungener_lauf_ist_kein_fehlschlag(self, waechter):
        """Ein paralleler Lauf, der die Sperre nicht bekommt, hat nichts
        falsch gemacht. Sein Vorgänger ist noch frisch."""
        bw, pfad = waechter
        marke(pfad, ergebnis="uebersprungen", meldung="paralleler Lauf",
              wiederherstellung_geprueft="nein")
        assert bw.pruefe_datensicherung() == []

    def test_unlesbare_marke_ist_ein_befund(self, waechter):
        bw, pfad = waechter
        pfad.write_text("{kein json")
        schluessel = [s for s, _ in bw.pruefe_datensicherung()]
        assert schluessel == ["sicherung-marke-unlesbar"]

    def test_haengt_im_hauptlauf(self, waechter):
        """Eine Prüfung, die niemand aufruft, ist keine Prüfung."""
        bw, _ = waechter
        quelltext = _lies(os.path.join(BACKEND, 'cronjobs', 'betriebswaechter.py'))
        hauptteil = quelltext.split('async def main()')[1]
        assert 'pruefe_datensicherung()' in hauptteil
