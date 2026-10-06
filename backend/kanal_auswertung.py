#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kanalmessung: Warteliste, Registrierungen und Kaeufe je utm_source und utm_content.

Die Entscheidungsregel nach Woche 45 des Launchplans lautet "Kaeufe je Kanal".
Dieses Skript liefert die Zahlen dazu als Wochenbericht in Markdown, jeden
Freitag derselbe Aufbau, damit zwei Wochen vergleichbar bleiben.

NUR LESEND. Die Abfragen laufen in einer Transaktion `READ ONLY`; die Datenbank
verweigert jeden Schreibversuch. Es werden keine E-Mail-Adressen ausgegeben
(sie dienen nur dem Abgleich zwischen Konto und Warteliste), und es wird kein
Stripe-Schluessel gebraucht: den Tarif und die Herkunft eines Kaufs schreibt der
Webhook seit Migration 0037 in `kauf_herkunft`.

Aufruf im Backend-Container:

    docker exec complyo-backend python kanal_auswertung.py --woche 2026-W42
    docker exec complyo-backend python kanal_auswertung.py --woche aktuell \\
        --seit 2026-10-13 --ausser mail@panoart360.de

Optionen:
    --woche    ISO-Woche (2026-W42), `aktuell` oder `letzte`. Mo 00:00 bis
               naechster Mo 00:00, Zeitzone Europe/Berlin.
    --seit     Startdatum fuer eine zweite Tabelle "seit Start" (kumuliert).
    --ausser   E-Mail-Adressen, die nicht zaehlen (eigene Testkonten),
               kommagetrennt. Ohne Angabe zaehlt jedes Konto.
    --out      Datei statt Standardausgabe.

Was gezaehlt wird, steht im Bericht unter "Lesehinweise", damit niemand die
Zahlen ohne ihre Grenzen weitergibt.
"""
import argparse
import asyncio
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")
OHNE = "(ohne Herkunft)"
NICHT_AUF_LISTE = "(nicht auf der Warteliste)"

# Tarife, die ein Zusatz zu einem Abo sind und kein eigener Kauf. Muss mit
# stripe_routes.ADDON_PLANS uebereinstimmen (ein Test haelt das fest).
ADDON_TARIFE = ("agency_extra", "agency2")

AKTIV = ("active", "trialing")
GEKUENDIGT = ("canceled", "cancelled")

_TABELLEN = ("registrierung_herkunft", "kauf_herkunft")

# Die E-Mail-Adresse steht nur in der Verbindungsbedingung, nie in der
# Auswahlliste: der Bericht kennt keine Adressen.
_WARTELISTE_JOIN = """
    LEFT JOIN LATERAL (
        SELECT w.id, w.utm_source, w.utm_content
        FROM waitlist_leads w
        WHERE lower(w.email) = lower(u.email)
        ORDER BY (w.platz_nr IS NULL), w.created_at
        LIMIT 1
    ) w ON true
"""

SQL_WARTELISTE = """
    SELECT utm_source, utm_content,
           (confirmed_at IS NOT NULL) AS bestaetigt,
           (platz_nr IS NOT NULL)     AS mit_platz
    FROM waitlist_leads
    WHERE created_at >= $1 AND created_at < $2
"""


def sql_registrierungen(mit_herkunft: bool) -> str:
    quelle = "r.utm_source, r.utm_content" if mit_herkunft else \
        "NULL::text AS utm_source, NULL::text AS utm_content"
    join = "LEFT JOIN registrierung_herkunft r ON r.user_id = u.id" if mit_herkunft else ""
    return f"""
    SELECT {quelle},
           w.utm_source AS w_source, w.utm_content AS w_content,
           (w.id IS NOT NULL) AS auf_warteliste
    FROM users u
    {join}
    {_WARTELISTE_JOIN}
    WHERE u.created_at >= $1 AND u.created_at < $2
      AND lower(u.email) <> ALL($3::text[])
"""


def sql_kaeufe(mit_herkunft: bool) -> str:
    quelle = ("k.plan AS k_plan, (k.stripe_subscription_id IS NOT NULL) AS in_kauf_herkunft, "
              "k.utm_source, k.utm_content") if mit_herkunft else \
        ("NULL::text AS k_plan, false AS in_kauf_herkunft, "
         "NULL::text AS utm_source, NULL::text AS utm_content")
    join = ("LEFT JOIN kauf_herkunft k ON k.stripe_subscription_id = s.stripe_subscription_id"
            if mit_herkunft else "")
    return f"""
    SELECT s.plan_type, s.status, {quelle},
           w.utm_source AS w_source, w.utm_content AS w_content,
           (w.id IS NOT NULL) AS auf_warteliste
    FROM subscriptions s
    JOIN users u ON u.id = s.user_id
    {join}
    {_WARTELISTE_JOIN}
    WHERE s.stripe_subscription_id IS NOT NULL
      AND s.created_at >= $1 AND s.created_at < $2
      AND lower(u.email) <> ALL($3::text[])
"""


# ---------------------------------------------------------------------------
# Zeitraum
# ---------------------------------------------------------------------------

def woche_grenzen(woche: str, jetzt: Optional[datetime] = None) -> Tuple[datetime, datetime, str]:
    """(von, bis, Bezeichnung) einer ISO-Woche in Europe/Berlin, bis ausgeschlossen.

    `2026-W42`, `aktuell` oder `letzte`. Mo 00:00 Ortszeit bis zum naechsten Mo
    00:00 Ortszeit; eine Woche mit Zeitumstellung ist 167 oder 169 Stunden lang
    und wird nicht auf 168 gerechnet.
    """
    jetzt = (jetzt or datetime.now(timezone.utc)).astimezone(BERLIN)
    if woche in ("aktuell", "letzte"):
        jahr, kw, _ = jetzt.isocalendar()
        if woche == "letzte":
            montag = date.fromisocalendar(jahr, kw, 1) - timedelta(days=7)
            jahr, kw, _ = montag.isocalendar()
    else:
        try:
            jahr_text, kw_text = woche.upper().split("-W")
            jahr, kw = int(jahr_text), int(kw_text)
            date.fromisocalendar(jahr, kw, 1)
        except (ValueError, TypeError):
            raise ValueError(f"Woche {woche!r} nicht lesbar, erwartet 2026-W42, aktuell oder letzte")
    montag = date.fromisocalendar(jahr, kw, 1)
    von = datetime(montag.year, montag.month, montag.day, tzinfo=BERLIN)
    naechster = montag + timedelta(days=7)
    bis = datetime(naechster.year, naechster.month, naechster.day, tzinfo=BERLIN)
    return von, bis, f"KW {kw:02d}/{jahr}"


def in_db_zeit(moment: datetime, db_zeitzone: str) -> datetime:
    """Zeitpunkt als naive Ortszeit der Datenbank, fuer `timestamp without time zone`.

    `subscriptions.created_at` hat keine Zeitzone und wird mit CURRENT_TIMESTAMP
    in der Sitzungszeitzone der Datenbank gefuellt. Die Wochengrenzen muessen
    in genau dieser Zeit verglichen werden, sonst rutschen Kaeufe zwischen
    Mitternacht Berlin und Mitternacht UTC in die falsche Woche.
    """
    try:
        zone = ZoneInfo(db_zeitzone)
    except Exception:
        zone = timezone.utc
    return moment.astimezone(zone).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Rohdaten laden (nur lesend)
# ---------------------------------------------------------------------------

@dataclass
class Rohdaten:
    von: datetime
    bis: datetime
    warteliste: List[dict] = field(default_factory=list)
    registrierungen: List[dict] = field(default_factory=list)
    kaeufe: List[dict] = field(default_factory=list)
    herkunftstabellen: bool = True
    db_zeitzone: str = "UTC"


async def lade(conn, von: datetime, bis: datetime, ausser: Sequence[str] = ()) -> Rohdaten:
    """Liest die Zeilen des Zeitraums. Schreibt nichts: Transaktion READ ONLY."""
    ausgeschlossen = [a.strip().lower() for a in ausser if a and a.strip()]
    async with conn.transaction(readonly=True):
        zone = await conn.fetchval("SHOW timezone") or "UTC"
        vorhanden = {}
        for tabelle in _TABELLEN:
            vorhanden[tabelle] = bool(await conn.fetchval(
                "SELECT to_regclass($1) IS NOT NULL", f"public.{tabelle}"))
        mit = all(vorhanden.values())

        warteliste = await conn.fetch(SQL_WARTELISTE, von, bis)
        registrierungen = await conn.fetch(
            sql_registrierungen(vorhanden["registrierung_herkunft"]), von, bis, ausgeschlossen)
        kaeufe = await conn.fetch(
            sql_kaeufe(vorhanden["kauf_herkunft"]),
            in_db_zeit(von, zone), in_db_zeit(bis, zone), ausgeschlossen)
    return Rohdaten(
        von=von, bis=bis,
        warteliste=[dict(z) for z in warteliste],
        registrierungen=[dict(z) for z in registrierungen],
        kaeufe=[dict(z) for z in kaeufe],
        herkunftstabellen=mit, db_zeitzone=zone,
    )


# ---------------------------------------------------------------------------
# Zaehlen (rein, ohne Datenbank)
# ---------------------------------------------------------------------------

def _norm(wert) -> Optional[str]:
    """Kleinschreibung und Leerraum weg; leer ist None. LinkedIn und linkedin sind ein Kanal."""
    if wert is None:
        return None
    text = str(wert).strip().lower()
    return text or None


def _schluessel(source, content) -> Tuple[str, str]:
    s, c = _norm(source), _norm(content)
    if s is None and c is None:
        return (OHNE, OHNE)
    return (s or OHNE, c or OHNE)


def tarif_von(zeile: dict) -> str:
    """Tarif eines Kaufs: Checkout-Metadaten, sonst Ledger (`subscriptions.plan_type`)."""
    return _norm(zeile.get("k_plan")) or _norm(zeile.get("plan_type")) or "unbekannt"


def ist_addon(zeile: dict) -> bool:
    return tarif_von(zeile) in ADDON_TARIFE


def status_klasse(status) -> str:
    s = _norm(status)
    if s in AKTIV:
        return "aktiv"
    if s in GEKUENDIGT:
        return "gekündigt"
    return "sonstige"


@dataclass
class Zaehlung:
    """Alle Zahlen eines Zeitraums, abgeleitet aus `Rohdaten`."""
    wartelisten: Counter            # (source, content) -> eingetragen
    bestaetigt: Counter
    mit_platz: Counter
    registrierungen: Counter        # direkte Herkunft
    kaeufe: Counter                 # direkte Herkunft, ohne Add-ons
    kaeufe_pro: Counter
    erst_registrierungen: Counter   # Erstkontakt ueber die Warteliste
    erst_kaeufe: Counter
    erst_kaeufe_pro: Counter
    tarife: Counter                 # (tarif, statusklasse) -> Anzahl, mit Add-ons
    kaeufe_gesamt: int
    kaeufe_ohne_eintrag: int        # Kaeufe ohne Zeile in kauf_herkunft
    registrierungen_gesamt: int
    nicht_auf_liste_reg: int
    nicht_auf_liste_kauf: int


def zaehle(daten: Rohdaten) -> Zaehlung:
    wartelisten, bestaetigt, mit_platz = Counter(), Counter(), Counter()
    for z in daten.warteliste:
        k = _schluessel(z.get("utm_source"), z.get("utm_content"))
        wartelisten[k] += 1
        if z.get("bestaetigt"):
            bestaetigt[k] += 1
        if z.get("mit_platz"):
            mit_platz[k] += 1

    registrierungen, erst_reg = Counter(), Counter()
    nicht_reg = 0
    for z in daten.registrierungen:
        registrierungen[_schluessel(z.get("utm_source"), z.get("utm_content"))] += 1
        if z.get("auf_warteliste"):
            erst_reg[_schluessel(z.get("w_source"), z.get("w_content"))] += 1
        else:
            nicht_reg += 1

    kaeufe, kaeufe_pro, erst_kauf, erst_pro = Counter(), Counter(), Counter(), Counter()
    tarife = Counter()
    kaeufe_gesamt = ohne_eintrag = nicht_kauf = 0
    for z in daten.kaeufe:
        tarife[(tarif_von(z), status_klasse(z.get("status")))] += 1
        if not z.get("in_kauf_herkunft"):
            ohne_eintrag += 1
        if ist_addon(z):
            continue
        kaeufe_gesamt += 1
        ist_pro = tarif_von(z) == "pro"
        k = _schluessel(z.get("utm_source"), z.get("utm_content"))
        kaeufe[k] += 1
        if ist_pro:
            kaeufe_pro[k] += 1
        if z.get("auf_warteliste"):
            ek = _schluessel(z.get("w_source"), z.get("w_content"))
            erst_kauf[ek] += 1
            if ist_pro:
                erst_pro[ek] += 1
        else:
            nicht_kauf += 1

    return Zaehlung(
        wartelisten=wartelisten, bestaetigt=bestaetigt, mit_platz=mit_platz,
        registrierungen=registrierungen, kaeufe=kaeufe, kaeufe_pro=kaeufe_pro,
        erst_registrierungen=erst_reg, erst_kaeufe=erst_kauf, erst_kaeufe_pro=erst_pro,
        tarife=tarife, kaeufe_gesamt=kaeufe_gesamt, kaeufe_ohne_eintrag=ohne_eintrag,
        registrierungen_gesamt=len(daten.registrierungen),
        nicht_auf_liste_reg=nicht_reg, nicht_auf_liste_kauf=nicht_kauf,
    )


def _summe(zaehler: Counter) -> int:
    return sum(zaehler.values())


def _mit_herkunft(zaehler: Counter) -> int:
    return sum(n for (s, c), n in zaehler.items() if (s, c) != (OHNE, OHNE))


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def _zelle(text) -> str:
    return str(text).replace("|", "\\|")


def _tabelle(kopf: Sequence[str], zeilen: Iterable[Sequence], rechts_ab: int = 2) -> List[str]:
    zeilen = list(zeilen)
    ausgabe = ["| " + " | ".join(kopf) + " |",
               "|" + "|".join("---" if i < rechts_ab else "---:" for i in range(len(kopf))) + "|"]
    for z in zeilen:
        ausgabe.append("| " + " | ".join(_zelle(c) for c in z) + " |")
    return ausgabe


def _sortiert(schluessel: Iterable[Tuple[str, str]], *zaehler: Counter) -> List[Tuple[str, str]]:
    """Erst nach Gesamtzahl absteigend, dann alphabetisch; (ohne Herkunft) ans Ende."""
    def gewicht(k):
        return -sum(c.get(k, 0) for c in zaehler)
    return sorted(set(schluessel), key=lambda k: ((k == (OHNE, OHNE)), gewicht(k), k))


def _datum(moment: datetime) -> str:
    return moment.astimezone(BERLIN).strftime("%d.%m.%Y")


def bericht_markdown(woche: Rohdaten, bezeichnung: str, jetzt: datetime,
                     seit: Optional[Rohdaten] = None, ausser: Sequence[str] = ()) -> str:
    """Der Wochenbericht. `jetzt` ist ein Parameter, damit die Ausgabe prueffbar bleibt."""
    z = zaehle(woche)
    letzter_tag = woche.bis - timedelta(days=1)
    zeilen: List[str] = []
    zeilen.append(f"# Kanalmessung {bezeichnung}")
    zeilen.append("")
    zeilen.append(
        f"Zeitraum: Mo {_datum(woche.von)} 00:00 bis So {_datum(letzter_tag)} 24:00 (Europe/Berlin). "
        f"Stand: {jetzt.astimezone(BERLIN).strftime('%d.%m.%Y %H:%M')}. "
        "Quelle: Datenbank, nur lesend, ohne Stripe-Zugriff.")
    zeilen.append("")

    if not woche.herkunftstabellen:
        zeilen.append(
            "> **Achtung:** Die Tabellen `registrierung_herkunft` oder `kauf_herkunft` fehlen "
            "(Migration 0037 nicht gelaufen). Registrierungen und Käufe erscheinen deshalb "
            "vollständig als \"" + OHNE + "\"; nur die Warteliste und der Abgleich über die "
            "Warteliste sind belastbar.")
        zeilen.append("")

    # --- Auf einen Blick
    pro_gesamt = _summe(z.kaeufe_pro)
    zeilen.append("## Auf einen Blick")
    zeilen.append("")
    zeilen += _tabelle(
        ["Stufe", "Anzahl", "mit Herkunft", "ohne Herkunft"],
        [
            ["Warteliste eingetragen", _summe(z.wartelisten), _mit_herkunft(z.wartelisten),
             _summe(z.wartelisten) - _mit_herkunft(z.wartelisten)],
            ["Warteliste bestätigt (Double-Opt-In)", _summe(z.bestaetigt), _mit_herkunft(z.bestaetigt),
             _summe(z.bestaetigt) - _mit_herkunft(z.bestaetigt)],
            ["davon mit Platz", _summe(z.mit_platz), _mit_herkunft(z.mit_platz),
             _summe(z.mit_platz) - _mit_herkunft(z.mit_platz)],
            ["Registrierungen (neue Konten)", z.registrierungen_gesamt, _mit_herkunft(z.registrierungen),
             z.registrierungen_gesamt - _mit_herkunft(z.registrierungen)],
            ["Käufe (neue Abos, ohne Add-ons)", z.kaeufe_gesamt, _mit_herkunft(z.kaeufe),
             z.kaeufe_gesamt - _mit_herkunft(z.kaeufe)],
            ["davon Pro", pro_gesamt, _mit_herkunft(z.kaeufe_pro), pro_gesamt - _mit_herkunft(z.kaeufe_pro)],
        ],
        rechts_ab=1,
    )
    zeilen.append("")
    if _summe(z.wartelisten) == 0 and z.registrierungen_gesamt == 0 and z.kaeufe_gesamt == 0:
        zeilen.append(
            "Null Anmeldungen, null Registrierungen, null Käufe. Nach dem Launchplan (Abschnitt 6) "
            "ist dann zuerst die Strecke zu prüfen (Kurzlinks, Mail, Checkout), bevor das Angebot "
            "als Ursache gilt.")
        zeilen.append("")

    # --- Je Kanal und Beitrag
    schluessel = _sortiert(
        list(z.wartelisten) + list(z.registrierungen) + list(z.kaeufe),
        z.wartelisten, z.registrierungen, z.kaeufe)
    zeilen.append("## Je Kanal und Beitrag (Herkunft laut Anmeldung, Registrierung und Checkout)")
    zeilen.append("")
    if schluessel:
        zeilen += _tabelle(
            ["utm_source", "utm_content", "Warteliste", "bestätigt", "Registrierungen", "Käufe", "davon Pro"],
            [[s, c, z.wartelisten.get((s, c), 0), z.bestaetigt.get((s, c), 0),
              z.registrierungen.get((s, c), 0), z.kaeufe.get((s, c), 0), z.kaeufe_pro.get((s, c), 0)]
             for (s, c) in schluessel])
    else:
        zeilen.append("Keine Einträge in diesem Zeitraum.")
    zeilen.append("")

    # --- Erstkontakt ueber die Warteliste
    zeilen.append("## Erstkontakt über die Warteliste")
    zeilen.append("")
    zeilen.append(
        "Wer sich erst auf die Warteliste eintrug und später mit derselben E-Mail-Adresse ein Konto "
        "anlegte oder kaufte, wird hier dem Kanal zugerechnet, aus dem der Wartelisten-Eintrag kam. "
        "Das ist der Erstkontakt, unabhängig davon, womit der Checkout markiert war.")
    zeilen.append("")
    erst_keys = _sortiert(list(z.erst_registrierungen) + list(z.erst_kaeufe),
                          z.erst_registrierungen, z.erst_kaeufe)
    # Auf der Liste, aber ohne utm: dort heisst "ohne Herkunft" etwas anderes
    # als in den Tabellen davor, deshalb ein eigener Name.
    def _name(k):
        return ("(Eintrag ohne utm)", "") if k == (OHNE, OHNE) else k
    zeilen_erst = [[*_name((s, c)), z.erst_registrierungen.get((s, c), 0), z.erst_kaeufe.get((s, c), 0),
                    z.erst_kaeufe_pro.get((s, c), 0)] for (s, c) in erst_keys]
    zeilen_erst.append([NICHT_AUF_LISTE, "", z.nicht_auf_liste_reg, z.nicht_auf_liste_kauf, ""])
    zeilen += _tabelle(["utm_source (Warteliste)", "utm_content", "Registrierungen", "Käufe", "davon Pro"],
                       zeilen_erst)
    zeilen.append("")

    # --- Tarife
    zeilen.append("## Käufe je Tarif")
    zeilen.append("")
    if z.tarife:
        tarife = sorted({t for (t, _) in z.tarife})
        zeilen += _tabelle(
            ["Tarif", "Käufe", "aktiv", "gekündigt", "sonstige"],
            [[t + (" (Add-on)" if t in ADDON_TARIFE else ""),
              sum(n for (tt, _), n in z.tarife.items() if tt == t),
              z.tarife.get((t, "aktiv"), 0), z.tarife.get((t, "gekündigt"), 0),
              z.tarife.get((t, "sonstige"), 0)] for t in tarife])
    else:
        zeilen.append("Keine neuen Abos in diesem Zeitraum.")
    zeilen.append("")

    # --- Seit Start
    if seit is not None:
        s = zaehle(seit)
        zeilen.append(f"## Seit Start ({_datum(seit.von)} bis {_datum(seit.bis - timedelta(days=1))}, kumuliert)")
        zeilen.append("")
        zeilen += _tabelle(
            ["Stufe", "Anzahl"],
            [["Warteliste eingetragen", _summe(s.wartelisten)],
             ["Warteliste bestätigt", _summe(s.bestaetigt)],
             ["Registrierungen", s.registrierungen_gesamt],
             ["Käufe (ohne Add-ons)", s.kaeufe_gesamt],
             ["davon Pro", _summe(s.kaeufe_pro)]],
            rechts_ab=1)
        zeilen.append("")
        if s.kaeufe:
            zeilen += _tabelle(
                ["utm_source", "utm_content", "Käufe", "davon Pro"],
                [[a, b, s.kaeufe.get((a, b), 0), s.kaeufe_pro.get((a, b), 0)]
                 for (a, b) in _sortiert(s.kaeufe, s.kaeufe)])
            zeilen.append("")

    # --- Lesehinweise
    zeilen.append("## Lesehinweise")
    zeilen.append("")
    hinweise = [
        "Warteliste: Einträge, die in diesem Zeitraum angelegt wurden (`waitlist_leads.created_at`). "
        "\"Bestätigt\" und \"mit Platz\" zählen davon die, die den Link in der Bestätigungsmail geklickt haben; "
        "ein Platz entsteht erst dort.",
        "Registrierungen: alle neuen Konten, auch über Google angelegte und eigene Testkonten. "
        "Die Herkunft kommt aus `registrierung_herkunft`; sie wird nur geschrieben, wenn die Registrierungsseite "
        "sie im Registrierungsaufruf mitschickt (`herkunft`). Der Google-Weg schickt bisher keine.",
        "Käufe: neue Abonnements aus `subscriptions` (Ledger des Webhooks), ohne Add-ons "
        f"({', '.join(ADDON_TARIFE)}). Der Tarif kommt aus den Checkout-Metadaten (`kauf_herkunft.plan`), "
        "sonst aus `subscriptions.plan_type`. Erstattungen, Zahlungsausfälle und Umsatz stehen nur in Stripe "
        "und sind hier nicht erfasst.",
        "Herkunft bei Käufen und Registrierungen wird erst ab dem Deploy der Migration 0037 und des "
        "Backends geschrieben, und sie kommt nur an, wenn Landing und Registrierung sie weiterreichen; "
        "davor und sonst erscheint alles als \"" + OHNE + "\".",
        "Der Kurzlink `/scan` setzt `utm_source=social` für alle Kanäle; dort unterscheidet erst `utm_content` "
        "(die Kennung des Beitrags) den Kanal.",
        "Kanalnamen werden kleingeschrieben und von Leerzeichen befreit, `LinkedIn` und `linkedin` zählen als ein Kanal.",
        "Wochengrenzen: Mo 00:00 bis Mo 00:00 Ortszeit Berlin; `subscriptions` hat keine Zeitzone und wird "
        f"in der Datenbankzeit ({woche.db_zeitzone}) verglichen.",
    ]
    if ausser:
        hinweise.append(f"Ausgenommen wurden {len([a for a in ausser if a.strip()])} Konten (Testkonten), "
                        "ihre Registrierungen und Käufe fehlen in allen Zahlen.")
    else:
        hinweise.append("Kein Konto ausgenommen: ein eigener Testkauf zählt als Kauf (Option `--ausser`).")
    if z.kaeufe_ohne_eintrag:
        hinweise.append(
            f"{z.kaeufe_ohne_eintrag} Kauf/Käufe ohne Eintrag in `kauf_herkunft` (Tarif aus dem Ledger, "
            "dort steht nach `customer.subscription.created` fest 'pro').")
    for h in hinweise:
        zeilen.append(f"- {h}")
    zeilen.append("")
    return "\n".join(zeilen)


# ---------------------------------------------------------------------------
# Aufruf
# ---------------------------------------------------------------------------

async def erstelle_bericht(conn, woche: str, seit: Optional[date], ausser: Sequence[str],
                           jetzt: Optional[datetime] = None) -> str:
    jetzt = jetzt or datetime.now(timezone.utc)
    von, bis, bezeichnung = woche_grenzen(woche, jetzt)
    daten = await lade(conn, von, bis, ausser)
    kumuliert = None
    if seit is not None:
        seit_von = datetime(seit.year, seit.month, seit.day, tzinfo=BERLIN)
        # Vom Startdatum bis zum Ende der gewaehlten Woche. Liegt der Start
        # dahinter, gibt es noch nichts zu summieren und der Abschnitt entfaellt.
        if seit_von < bis:
            kumuliert = await lade(conn, seit_von, bis, ausser)
    return bericht_markdown(daten, bezeichnung, jetzt, kumuliert, ausser)


async def _main(args) -> int:
    import asyncpg  # erst hier: die Zaehlfunktionen brauchen keinen Treiber
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL fehlt", file=sys.stderr)
        return 2
    seit = date.fromisoformat(args.seit) if args.seit else None
    ausser = [a for a in (args.ausser or "").split(",") if a.strip()]
    conn = await asyncpg.connect(url)
    try:
        text = await erstelle_bericht(conn, args.woche, seit, ausser)
    finally:
        await conn.close()
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Kanalmessung als Wochenbericht (nur lesend).")
    p.add_argument("--woche", default="aktuell", help="2026-W42, aktuell oder letzte")
    p.add_argument("--seit", help="Startdatum JJJJ-MM-TT für die kumulierte Tabelle")
    p.add_argument("--ausser", help="E-Mail-Adressen, die nicht zählen, kommagetrennt")
    p.add_argument("--out", help="in diese Datei schreiben statt auf die Standardausgabe")
    args = p.parse_args(argv)
    try:
        woche_grenzen(args.woche)
        if args.seit:
            date.fromisoformat(args.seit)
    except ValueError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2
    return asyncio.run(_main(args))


if __name__ == "__main__":
    sys.exit(main())
