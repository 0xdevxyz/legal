# -*- coding: utf-8 -*-
"""Die Kanalmessung zaehlt, was sie zu zaehlen vorgibt.

Anlass (07.10.2026): Die Entscheidungsregel nach Woche 45 verlangt "Kaeufe je
Kanal". Eine Auswertung, die falsch zaehlt, ist schlimmer als keine, weil an
ihr eine Preis- und Kanalentscheidung haengt. Jede Sollzahl unten ist von Hand
aus den Eingabezeilen nachgerechnet und steht als Rechnung im Kommentar, nicht
aus dem Ergebnis des Codes uebernommen.

Die Zaehlung selbst laeuft ohne Datenbank. Dass die SQL-Abfragen gegen das
echte Schema laufen, prueft `test_kanal_auswertung_db.py` (braucht eine
Test-Datenbank und ueberspringt sonst mit Begruendung).
"""
import asyncio
import os
import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")

import kanal_auswertung as ka  # noqa: E402
from kanal_auswertung import OHNE, Rohdaten, zaehle  # noqa: E402

BERLIN = ZoneInfo("Europe/Berlin")
FREITAG = datetime(2026, 10, 16, 10, 0, tzinfo=BERLIN)


def _daten(**kw):
    von, bis, _ = ka.woche_grenzen("2026-W41")
    return Rohdaten(von=von, bis=bis, **kw)


# ---------------------------------------------------------------------------
# Eingaben, bewusst mit den Schmutzfaellen aus dem Alltag: Gross/Kleinschreibung,
# Leerraum, fehlende Werte, bestaetigt ohne Platz.
# ---------------------------------------------------------------------------

WARTELISTE = [
    {"utm_source": "linkedin", "utm_content": "p01", "bestaetigt": True,  "mit_platz": True},
    {"utm_source": "linkedin", "utm_content": "P01", "bestaetigt": True,  "mit_platz": True},
    {"utm_source": "linkedin", "utm_content": "p02", "bestaetigt": False, "mit_platz": False},
    {"utm_source": "tiktok",   "utm_content": None,  "bestaetigt": True,  "mit_platz": True},
    {"utm_source": None,       "utm_content": None,  "bestaetigt": False, "mit_platz": False},
    {"utm_source": " LinkedIn ", "utm_content": "p01", "bestaetigt": False, "mit_platz": False},
    {"utm_source": "youtube",  "utm_content": "",    "bestaetigt": True,  "mit_platz": False},
]

REGISTRIERUNGEN = [
    # a: kam mit linkedin/p01 und stand schon auf der Liste (linkedin/p01)
    {"utm_source": "linkedin", "utm_content": "p01", "auf_warteliste": True,
     "w_source": "linkedin", "w_content": "p01"},
    # b: ohne Markierung, aber auf der Liste (tiktok, ohne Beitrag)
    {"utm_source": None, "utm_content": None, "auf_warteliste": True,
     "w_source": "tiktok", "w_content": None},
    # c: kam ueber die Launch-Mail, Erstkontakt war linkedin/p02
    {"utm_source": "warteliste", "utm_content": "mail-a", "auf_warteliste": True,
     "w_source": "linkedin", "w_content": "p02"},
    # d: weder Markierung noch Liste
    {"utm_source": None, "utm_content": None, "auf_warteliste": False,
     "w_source": None, "w_content": None},
    # e: linkedin/p01, nicht auf der Liste
    {"utm_source": "linkedin", "utm_content": "p01", "auf_warteliste": False,
     "w_source": None, "w_content": None},
]

KAEUFE = [
    # 1: Pro, linkedin/p01, Erstkontakt linkedin/p01
    {"plan_type": "pro", "k_plan": "pro", "status": "active", "in_kauf_herkunft": True,
     "utm_source": "linkedin", "utm_content": "p01", "auf_warteliste": True,
     "w_source": "linkedin", "w_content": "p01"},
    # 2: Ledger sagt 'pro' (fest gesetzt), die Checkout-Metadaten sagen 'agency'
    {"plan_type": "pro", "k_plan": "agency", "status": "active", "in_kauf_herkunft": True,
     "utm_source": "warteliste", "utm_content": "mail-a", "auf_warteliste": True,
     "w_source": "linkedin", "w_content": "p02"},
    # 3: kein Eintrag in kauf_herkunft, gekuendigt, keine Herkunft
    {"plan_type": "pro", "k_plan": None, "status": "canceled", "in_kauf_herkunft": False,
     "utm_source": None, "utm_content": None, "auf_warteliste": False,
     "w_source": None, "w_content": None},
    # 4: Add-on, kein eigener Kauf
    {"plan_type": "agency", "k_plan": "agency_extra", "status": "active", "in_kauf_herkunft": True,
     "utm_source": "linkedin", "utm_content": "p01", "auf_warteliste": False,
     "w_source": None, "w_content": None},
    # 5: Einzelsaeule, Zahlung ueberfaellig
    {"plan_type": "single", "k_plan": "single", "status": "past_due", "in_kauf_herkunft": True,
     "utm_source": "tiktok", "utm_content": None, "auf_warteliste": False,
     "w_source": None, "w_content": None},
    # 6: Pro in der Probezeit, linkedin/p01, nicht auf der Liste
    {"plan_type": "pro", "k_plan": "pro", "status": "trialing", "in_kauf_herkunft": True,
     "utm_source": "linkedin", "utm_content": "p01", "auf_warteliste": False,
     "w_source": None, "w_content": None},
]


def _alles():
    return _daten(warteliste=WARTELISTE, registrierungen=REGISTRIERUNGEN, kaeufe=KAEUFE)


class TestZaehlung:
    def test_warteliste_je_kanal_und_beitrag(self):
        z = zaehle(_alles())
        # linkedin/p01: Zeilen 1, 2 und 6 (Gross/Kleinschreibung und Leerraum egal) = 3
        #   davon bestaetigt: 1, 2 = 2; mit Platz: 1, 2 = 2
        assert z.wartelisten[("linkedin", "p01")] == 3
        assert z.bestaetigt[("linkedin", "p01")] == 2
        assert z.mit_platz[("linkedin", "p01")] == 2
        # linkedin/p02: Zeile 3, unbestaetigt
        assert z.wartelisten[("linkedin", "p02")] == 1
        assert z.bestaetigt[("linkedin", "p02")] == 0
        # tiktok ohne Beitrag: Zeile 4, bestaetigt, Platz
        assert z.wartelisten[("tiktok", OHNE)] == 1
        assert z.mit_platz[("tiktok", OHNE)] == 1
        # youtube, leerer Beitrag zaehlt als ohne: Zeile 7, bestaetigt, KEIN Platz
        assert z.bestaetigt[("youtube", OHNE)] == 1
        assert z.mit_platz[("youtube", OHNE)] == 0
        # ohne jede Herkunft: Zeile 5
        assert z.wartelisten[(OHNE, OHNE)] == 1

    def test_warteliste_summen(self):
        z = zaehle(_alles())
        # eingetragen 7; bestaetigt = Zeilen 1, 2, 4, 7 = 4; mit Platz = Zeilen 1, 2, 4 = 3
        assert sum(z.wartelisten.values()) == 7
        assert sum(z.bestaetigt.values()) == 4
        assert sum(z.mit_platz.values()) == 3

    def test_registrierungen_nach_herkunft_im_checkout(self):
        z = zaehle(_alles())
        # a und e: linkedin/p01 = 2; c: warteliste/mail-a = 1; b und d: ohne = 2; zusammen 5
        assert z.registrierungen[("linkedin", "p01")] == 2
        assert z.registrierungen[("warteliste", "mail-a")] == 1
        assert z.registrierungen[(OHNE, OHNE)] == 2
        assert z.registrierungen_gesamt == 5

    def test_registrierungen_nach_erstkontakt(self):
        z = zaehle(_alles())
        # a: linkedin/p01, b: tiktok, c: linkedin/p02 = je 1; d und e nicht auf der Liste = 2
        assert z.erst_registrierungen[("linkedin", "p01")] == 1
        assert z.erst_registrierungen[("tiktok", OHNE)] == 1
        assert z.erst_registrierungen[("linkedin", "p02")] == 1
        assert z.nicht_auf_liste_reg == 2

    def test_kaeufe_ohne_addons_und_je_kanal(self):
        z = zaehle(_alles())
        # Kaeufe 1, 2, 3, 5, 6 = 5; Zeile 4 ist ein Add-on und zaehlt nicht
        assert z.kaeufe_gesamt == 5
        assert z.kaeufe[("linkedin", "p01")] == 2        # Zeilen 1 und 6
        assert z.kaeufe[("warteliste", "mail-a")] == 1   # Zeile 2
        assert z.kaeufe[(OHNE, OHNE)] == 1               # Zeile 3
        assert z.kaeufe[("tiktok", OHNE)] == 1           # Zeile 5
        assert sum(z.kaeufe.values()) == 5

    def test_pro_kaeufe_nehmen_den_tarif_aus_den_checkout_metadaten(self):
        z = zaehle(_alles())
        # Pro sind die Zeilen 1, 3 (Ledger 'pro', keine Metadaten) und 6 = 3.
        # Zeile 2 steht im Ledger als 'pro', die Metadaten sagen 'agency': KEIN Pro.
        assert sum(z.kaeufe_pro.values()) == 3
        assert z.kaeufe_pro[("linkedin", "p01")] == 2
        assert z.kaeufe_pro[(OHNE, OHNE)] == 1
        assert z.kaeufe_pro.get(("warteliste", "mail-a"), 0) == 0

    def test_kaeufe_nach_erstkontakt(self):
        z = zaehle(_alles())
        # auf der Liste sind nur Zeile 1 (linkedin/p01, Pro) und Zeile 2 (linkedin/p02, Agency)
        assert z.erst_kaeufe[("linkedin", "p01")] == 1
        assert z.erst_kaeufe[("linkedin", "p02")] == 1
        assert z.erst_kaeufe_pro[("linkedin", "p01")] == 1
        assert z.erst_kaeufe_pro.get(("linkedin", "p02"), 0) == 0
        # nicht auf der Liste: Zeilen 3, 5, 6 = 3 (das Add-on Zeile 4 zaehlt nicht mit)
        assert z.nicht_auf_liste_kauf == 3

    def test_tarife_mit_status_und_addons(self):
        z = zaehle(_alles())
        # pro: Zeile 1 aktiv, Zeile 3 gekuendigt, Zeile 6 Probezeit = aktiv
        assert z.tarife[("pro", "aktiv")] == 2
        assert z.tarife[("pro", "gekündigt")] == 1
        assert z.tarife[("agency", "aktiv")] == 1            # Zeile 2
        assert z.tarife[("agency_extra", "aktiv")] == 1      # Zeile 4, Add-on bleibt sichtbar
        assert z.tarife[("single", "sonstige")] == 1         # Zeile 5, past_due
        assert sum(z.tarife.values()) == 6

    def test_kaeufe_ohne_eintrag_in_kauf_herkunft(self):
        assert zaehle(_alles()).kaeufe_ohne_eintrag == 1     # nur Zeile 3

    def test_leere_daten_ergeben_nullen_und_keinen_fehler(self):
        z = zaehle(_daten())
        assert z.kaeufe_gesamt == 0 and z.registrierungen_gesamt == 0
        assert sum(z.wartelisten.values()) == 0


class TestBericht:
    def _text(self, **kw):
        return ka.bericht_markdown(_alles(), "KW 41/2026", FREITAG, **kw)

    def test_kanalzeile_stimmt_mit_der_handrechnung(self):
        text = self._text()
        # linkedin/p01: Warteliste 3, bestaetigt 2, Registrierungen 2, Kaeufe 2, davon Pro 2
        assert "| linkedin | p01 | 3 | 2 | 2 | 2 | 2 |" in text
        # warteliste/mail-a: Registrierungen 1, Kaeufe 1, davon Pro 0
        assert "| warteliste | mail-a | 0 | 0 | 1 | 1 | 0 |" in text
        # ohne Herkunft steht ganz unten
        zeilen = [z for z in text.splitlines() if z.startswith("| (ohne Herkunft)")]
        assert zeilen and zeilen[0].startswith("| (ohne Herkunft) | (ohne Herkunft) | 1 | 0 | 2 | 1 | 1 |")

    def test_auf_einen_blick(self):
        text = self._text()
        assert "| Warteliste eingetragen | 7 | 6 | 1 |" in text
        assert "| Warteliste bestätigt (Double-Opt-In) | 4 | 4 | 0 |" in text
        assert "| davon mit Platz | 3 | 3 | 0 |" in text
        # Registrierungen 5: mit Herkunft a, c, e = 3, ohne b, d = 2
        assert "| Registrierungen (neue Konten) | 5 | 3 | 2 |" in text
        # Kaeufe 5: mit Herkunft 1, 2, 5, 6 = 4, ohne Zeile 3 = 1
        assert "| Käufe (neue Abos, ohne Add-ons) | 5 | 4 | 1 |" in text
        # Pro 3: mit Herkunft Zeilen 1 und 6 = 2, ohne Zeile 3 = 1
        assert "| davon Pro | 3 | 2 | 1 |" in text

    def test_tarifzeilen(self):
        text = self._text()
        assert "| pro | 3 | 2 | 1 | 0 |" in text
        assert "| agency_extra (Add-on) | 1 | 1 | 0 | 0 |" in text
        assert "| single | 1 | 0 | 0 | 1 |" in text

    def test_erstkontakt_nennt_auch_die_nicht_gelisteten(self):
        text = self._text()
        assert "| linkedin | p01 | 1 | 1 | 1 |" in text
        assert "| (nicht auf der Warteliste) |  | 2 | 3 |  |" in text

    def test_hinweis_auf_kaeufe_ohne_eintrag_und_testkonten(self):
        text = self._text()
        assert "1 Kauf/Käufe ohne Eintrag in `kauf_herkunft`" in text
        assert "Kein Konto ausgenommen" in text
        mit = self._text(ausser=["mail@panoart360.de"])
        assert "Ausgenommen wurden 1 Konten" in mit

    def test_fehlende_tabellen_werden_laut_gesagt(self):
        d = _alles()
        d.herkunftstabellen = False
        text = ka.bericht_markdown(d, "KW 41/2026", FREITAG)
        assert "Migration 0037 nicht gelaufen" in text

    def test_null_null_null_verweist_auf_die_streckenpruefung(self):
        text = ka.bericht_markdown(_daten(), "KW 41/2026", FREITAG)
        assert "Null Anmeldungen, null Registrierungen, null Käufe" in text
        assert "Keine Einträge in diesem Zeitraum." in text
        # mit Daten steht der Satz nicht da
        assert "Null Anmeldungen" not in self._text()

    def test_seit_start_summiert_getrennt_von_der_woche(self):
        seit = _daten(warteliste=WARTELISTE[:2], kaeufe=KAEUFE[:1])
        text = ka.bericht_markdown(_alles(), "KW 41/2026", FREITAG, seit=seit)
        assert "## Seit Start" in text
        # Seit-Start-Tabelle: 2 Eintraege, 1 Kauf, davon 1 Pro
        assert "| Warteliste eingetragen | 2 |" in text
        assert "| Käufe (ohne Add-ons) | 1 |" in text

    def test_der_bericht_enthaelt_keine_mailadresse(self):
        text = self._text(ausser=["mail@panoart360.de"])
        # Der Hinweis zaehlt die ausgenommenen Konten, nennt sie aber nicht.
        assert "@" not in text.replace("`", "")

    def test_kein_gedankenstrich(self):
        text = self._text()
        assert "\u2014" not in text and "\u2013" not in text

    def test_pipe_im_wert_bricht_die_tabelle_nicht(self):
        d = _daten(warteliste=[{"utm_source": "a|b", "utm_content": "x", "bestaetigt": False, "mit_platz": False}])
        text = ka.bericht_markdown(d, "KW 41/2026", FREITAG)
        assert "a\\|b" in text


class TestZeitraum:
    def test_woche_41_ist_der_5_bis_11_oktober(self):
        von, bis, name = ka.woche_grenzen("2026-W41")
        assert name == "KW 41/2026"
        assert von == datetime(2026, 10, 5, 0, 0, tzinfo=BERLIN)
        assert bis == datetime(2026, 10, 12, 0, 0, tzinfo=BERLIN)
        # 5. Oktober 2026 ist ein Montag
        assert date(2026, 10, 5).weekday() == 0
        assert von.astimezone(timezone.utc) == datetime(2026, 10, 4, 22, 0, tzinfo=timezone.utc)

    def test_aktuell_und_letzte_am_freitag_der_woche_42(self):
        assert ka.woche_grenzen("aktuell", FREITAG)[2] == "KW 42/2026"
        assert ka.woche_grenzen("letzte", FREITAG)[2] == "KW 41/2026"
        von, bis, _ = ka.woche_grenzen("letzte", FREITAG)
        assert von.date() == date(2026, 10, 5)

    def test_woche_mit_zeitumstellung_ist_169_stunden_lang(self):
        # Die Uhren gehen am Sonntag, 25.10.2026, um 03:00 auf 02:00 zurueck.
        von, bis, name = ka.woche_grenzen("2026-W43")
        assert name == "KW 43/2026"
        dauer = bis.astimezone(timezone.utc) - von.astimezone(timezone.utc)
        assert dauer == timedelta(hours=169)
        assert von.astimezone(timezone.utc) == datetime(2026, 10, 18, 22, 0, tzinfo=timezone.utc)
        assert bis.astimezone(timezone.utc) == datetime(2026, 10, 25, 23, 0, tzinfo=timezone.utc)

    def test_jahreswechsel_53_wochen(self):
        assert ka.woche_grenzen("2026-W53")[0].date() == date(2026, 12, 28)
        with pytest.raises(ValueError):
            ka.woche_grenzen("2025-W53")  # 2025 hat nur 52 Wochen

    @pytest.mark.parametrize("roh", ["", "42", "2026-42", "W42", "2026-W0", "2026-W54", "gestern"])
    def test_unlesbare_wochen_werden_abgelehnt(self, roh):
        with pytest.raises(ValueError):
            ka.woche_grenzen(roh)

    def test_naive_datenbankzeit(self):
        von = datetime(2026, 10, 5, 0, 0, tzinfo=BERLIN)
        assert ka.in_db_zeit(von, "UTC") == datetime(2026, 10, 4, 22, 0)
        assert ka.in_db_zeit(von, "Europe/Berlin") == datetime(2026, 10, 5, 0, 0)
        assert ka.in_db_zeit(von, "gibt-es-nicht") == datetime(2026, 10, 4, 22, 0)
        assert ka.in_db_zeit(von, "UTC").tzinfo is None


# ---------------------------------------------------------------------------
# Nur lesend: die Datenbank selbst muss Schreiben verweigern, und die Abfragen
# duerfen keine Adresse ausgeben.
# ---------------------------------------------------------------------------

class _Transaktion:
    def __init__(self, conn, readonly):
        self.conn, self.readonly = conn, readonly

    async def __aenter__(self):
        self.conn.transaktionen.append(self.readonly)
        self.conn.offen += 1

    async def __aexit__(self, *a):
        self.conn.offen -= 1


class FalscheVerbindung:
    """Zeichnet auf, was gefragt wird, und antwortet mit festen Zeilen."""

    def __init__(self, tabellen_da=True, zeitzone="UTC"):
        self.transaktionen, self.offen = [], 0
        self.abfragen = []   # (sql, args, offen)
        self.tabellen_da, self.zeitzone = tabellen_da, zeitzone

    def transaction(self, readonly=False, **kw):
        return _Transaktion(self, readonly)

    async def fetchval(self, sql, *args):
        self.abfragen.append((sql, args, self.offen))
        if sql.strip().upper().startswith("SHOW"):
            return self.zeitzone
        return self.tabellen_da

    async def fetch(self, sql, *args):
        self.abfragen.append((sql, args, self.offen))
        art = _art(sql)
        return [dict(z) for z in {"wl": WARTELISTE, "reg": REGISTRIERUNGEN, "kauf": KAEUFE}[art]]


def _art(sql):
    """Welche der drei Abfragen ist das? Die Kaeufe-Abfrage nennt waitlist_leads
    und users ebenfalls (Verbindung ueber die Adresse), also nach dem Hauptfrom."""
    haupt = re.search(r"(?is)\bFROM\s+(\w+)", sql).group(1).lower()
    return {"waitlist_leads": "wl", "users": "reg", "subscriptions": "kauf"}[haupt]


def test_lade_laeuft_in_einer_read_only_transaktion():
    conn = FalscheVerbindung()
    von, bis, _ = ka.woche_grenzen("2026-W41")
    daten = asyncio.run(ka.lade(conn, von, bis, ["Mail@Panoart360.de", " "]))
    assert conn.transaktionen == [True], "genau eine Transaktion, und sie ist READ ONLY"
    assert all(offen == 1 for _, _, offen in conn.abfragen), "jede Abfrage laeuft innerhalb davon"
    assert len(daten.warteliste) == 7 and len(daten.registrierungen) == 5 and len(daten.kaeufe) == 6


def test_keine_abfrage_schreibt_oder_nennt_eine_adresse_in_der_auswahl():
    conn = FalscheVerbindung()
    von, bis, _ = ka.woche_grenzen("2026-W41")
    asyncio.run(ka.lade(conn, von, bis))
    for sql, _, _ in conn.abfragen:
        grob = sql.strip()
        assert re.match(r"(?is)^(SELECT|SHOW)\b", grob), f"keine Leseabfrage: {grob[:40]}"
        assert not re.search(r"(?i)\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)\b", grob)
        auswahl = re.split(r"(?i)\bFROM\b", grob, maxsplit=1)[0]
        assert "email" not in auswahl.lower(), "die Auswahlliste nennt eine Adresse"


def test_zeitgrenzen_sind_je_spalte_richtig_typisiert():
    conn = FalscheVerbindung(zeitzone="UTC")
    von, bis, _ = ka.woche_grenzen("2026-W41")
    asyncio.run(ka.lade(conn, von, bis, ["Mail@Panoart360.de"]))
    nach_sql = {sql: args for sql, args, _ in conn.abfragen if sql.lstrip().upper().startswith("SELECT")
                and "to_regclass" not in sql}
    wl = next(a for s, a in nach_sql.items() if _art(s) == "wl")
    reg = next(a for s, a in nach_sql.items() if _art(s) == "reg")
    kauf = next(a for s, a in nach_sql.items() if _art(s) == "kauf")
    # timestamptz (Warteliste, Konten): mit Zeitzone
    assert wl[0].tzinfo is not None and reg[0].tzinfo is not None
    # timestamp ohne Zeitzone (subscriptions): naive Datenbankzeit, hier UTC = 22:00 am Vortag
    assert kauf[0] == datetime(2026, 10, 4, 22, 0) and kauf[0].tzinfo is None
    assert kauf[1] == datetime(2026, 10, 11, 22, 0)
    # ausgeschlossene Adressen klein geschrieben als Feld, nie in den Text gebaut
    assert reg[2] == ["mail@panoart360.de"] and kauf[2] == ["mail@panoart360.de"]
    assert all("panoart360" not in s for s in nach_sql), "Adresse im SQL-Text statt als Parameter"


def test_fehlende_herkunftstabellen_brechen_die_abfrage_nicht():
    conn = FalscheVerbindung(tabellen_da=False)
    von, bis, _ = ka.woche_grenzen("2026-W41")
    daten = asyncio.run(ka.lade(conn, von, bis))
    assert daten.herkunftstabellen is False
    sqls = [s for s, _, _ in conn.abfragen]
    # nicht verbinden, was es nicht gibt (der Spaltenname in_kauf_herkunft zaehlt nicht)
    assert not any("JOIN registrierung_herkunft" in s for s in sqls)
    assert not any("JOIN kauf_herkunft" in s for s in sqls)


def test_addon_tarife_stimmen_mit_dem_kaufweg_ueberein():
    import stripe_routes
    assert set(ka.ADDON_TARIFE) == set(stripe_routes.ADDON_PLANS)


def test_erstelle_bericht_ende_zu_ende_mit_falscher_verbindung():
    conn = FalscheVerbindung()
    text = asyncio.run(ka.erstelle_bericht(conn, "2026-W41", date(2026, 10, 5), [], jetzt=FREITAG))
    assert text.startswith("# Kanalmessung KW 41/2026")
    assert "## Seit Start" in text


def test_seit_nach_dem_wochenende_laesst_den_kumulierten_abschnitt_weg():
    conn = FalscheVerbindung()
    text = asyncio.run(ka.erstelle_bericht(conn, "2026-W41", date(2026, 10, 13), [], jetzt=FREITAG))
    assert "## Seit Start" not in text
