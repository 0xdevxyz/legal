"""
Betriebswächter (Audit-Nachzug 11.08.2026): Herzschlag-Logik, 24h-Dedupe
und Host-Signal-Auswertung. Die DB-Checks selbst laufen nur produktiv —
hier wird die Entscheidungslogik festgenagelt, damit der Wächter weder
rauscht noch verstummt.
"""
import importlib
import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def waechter(tmp_path, monkeypatch):
    monkeypatch.setenv("WAECHTER_STATE_PFAD", str(tmp_path / "state.json"))
    import cronjobs.betriebswaechter as m
    importlib.reload(m)
    return m


class TestHerzschlag:
    def test_stille_nach_regelmaessigem_signal_ist_alarm(self, waechter):
        assert waechter.bewerte_herzschlag(5.0, 0, 3.0) is True

    def test_wenig_verkehr_ist_kein_alarm(self, waechter):
        # Eine Site mit 1 Consent/Tag darf still sein — sonst rauscht es.
        assert waechter.bewerte_herzschlag(1.0, 0, 3.0) is False

    def test_signal_vorhanden_ist_kein_alarm(self, waechter):
        assert waechter.bewerte_herzschlag(50.0, 1, 3.0) is False


class TestDedupe:
    def test_neuer_befund_geht_durch_und_wird_gemerkt(self, waechter):
        state = {}
        jetzt = datetime(2026, 8, 11, 12, 0)
        frisch = waechter.dedupliziere([("k1", "Text")], state, jetzt)
        assert [s for s, _ in frisch] == ["k1"]
        assert state["k1"] == jetzt.isoformat()

    def test_gleicher_befund_binnen_24h_wird_unterdrueckt(self, waechter):
        jetzt = datetime(2026, 8, 11, 12, 0)
        state = {"k1": (jetzt - timedelta(hours=5)).isoformat()}
        assert waechter.dedupliziere([("k1", "Text")], state, jetzt) == []

    def test_nach_24h_wird_erneut_gemeldet(self, waechter):
        jetzt = datetime(2026, 8, 11, 12, 0)
        state = {"k1": (jetzt - timedelta(hours=25)).isoformat()}
        frisch = waechter.dedupliziere([("k1", "Text")], state, jetzt)
        assert [s for s, _ in frisch] == ["k1"]
        assert state["k1"] == jetzt.isoformat()

    def test_kaputter_state_blockiert_keine_meldung(self, waechter):
        frisch = waechter.dedupliziere(
            [("k1", "Text")], {"k1": "kein-datum"}, datetime(2026, 8, 11, 12, 0))
        assert [s for s, _ in frisch] == ["k1"]


class TestHostSignale:
    def test_unhealthy_container_wird_gemeldet(self, waechter, monkeypatch):
        monkeypatch.setenv(
            "WAECHTER_CONTAINER_STATUS",
            "complyo-backend: Up 2 hours (healthy)\n"
            "complyo-postgres: Up 2 hours (unhealthy)",
        )
        befunde = waechter.pruefe_host_signale()
        assert any("complyo-postgres" in text for _, text in befunde)
        # der gesunde Container taucht nicht als Befund auf
        assert not any("backend: Up" in text for _, text in befunde)

    def test_alles_healthy_kein_befund(self, waechter, monkeypatch):
        monkeypatch.setenv(
            "WAECHTER_CONTAINER_STATUS",
            "complyo-backend: Up 2 hours (healthy)",
        )
        monkeypatch.setenv("WAECHTER_FEHLER_1H", "3")
        assert waechter.pruefe_host_signale() == []

    def test_fehlerdruck_ueber_schwelle_meldet_mit_beispielen(self, waechter, monkeypatch):
        monkeypatch.setenv("WAECHTER_CONTAINER_STATUS", "")
        monkeypatch.setenv("WAECHTER_FEHLER_1H", "37")
        monkeypatch.setenv("WAECHTER_FEHLER_BEISPIELE", "ERROR:x:kaputt")
        befunde = waechter.pruefe_host_signale()
        assert len(befunde) == 1
        assert "37" in befunde[0][1] and "kaputt" in befunde[0][1]

    def test_ohne_host_signale_kein_befund(self, waechter, monkeypatch):
        monkeypatch.delenv("WAECHTER_CONTAINER_STATUS", raising=False)
        monkeypatch.delenv("WAECHTER_FEHLER_1H", raising=False)
        assert waechter.pruefe_host_signale() == []


class TestTelegram:
    def test_ohne_konfiguration_kein_versand(self, waechter, monkeypatch):
        monkeypatch.setattr(waechter, "TELEGRAM_TOKEN", "")
        monkeypatch.setattr(waechter, "TELEGRAM_CHAT", "")
        assert waechter.sende_telegram([("k", "Text")]) is False

    def test_text_traegt_anzahl_und_befunde(self, waechter):
        text = waechter.baue_telegram_text([("a", "Erster"), ("b", "Zweiter")])
        assert "2 Befund(e)" in text
        assert "• Erster" in text and "• Zweiter" in text

    def test_alarm_meldet_nur_kanaele_die_wirklich_trugen(self, waechter, monkeypatch):
        """
        Der Wächter darf nie „verschickt" behaupten, wenn der Kanal scheiterte
        — im ersten Livetest stand genau das im Log (Telegram trug, Mail
        scheiterte an SMTP, gemeldet wurde trotzdem „Alarm-Mail verschickt").
        """
        monkeypatch.setattr(waechter, "sende_telegram", lambda b: True)
        monkeypatch.setattr(waechter, "sende_mail", lambda b: False)
        assert waechter.sende_alarm([("k", "Text")]) == ["Telegram"]

        monkeypatch.setattr(waechter, "sende_telegram", lambda b: False)
        monkeypatch.setattr(waechter, "sende_mail", lambda b: True)
        assert waechter.sende_alarm([("k", "Text")]) == ["Mail"]

        monkeypatch.setattr(waechter, "sende_telegram", lambda b: True)
        assert waechter.sende_alarm([("k", "Text")]) == ["Telegram", "Mail"]

    def test_kein_kanal_traegt_ist_kein_erfolg(self, waechter, monkeypatch):
        monkeypatch.setattr(waechter, "sende_telegram", lambda b: False)
        monkeypatch.setattr(waechter, "sende_mail", lambda b: False)
        assert waechter.sende_alarm([("k", "Text")]) == []
