#!/usr/bin/env python3
"""Aus den Minutenmessungen eine Monatsquote rechnen, mit ihren Grenzen.

Aufruf:
    verfuegbarkeit-auswerten.py            # laufender Monat
    verfuegbarkeit-auswerten.py 2026-10    # ein bestimmter Monat

Warum die Grenzen mit ausgegeben werden: Eine Quote ohne Methode ist eine
Behauptung. Steht sie einmal in einem Vertrag, wird sie zitiert; dann muss
danebenstehen, wie sie zustande kam und was sie nicht sieht.
"""
import pathlib
import sys
from collections import defaultdict
from datetime import datetime, timezone

ABLAGE = pathlib.Path("/home/clawd/saas/legal/data/verfuegbarkeit")

# Was als erreichbar zaehlt. 000 ist ein Abbruch (Zeitueberschreitung, kein
# DNS, kein TLS) und damit ein Ausfall. 5xx ebenso: die Seite antwortet, aber
# sie arbeitet nicht.
def erreichbar(code: str) -> bool:
    return code.isdigit() and 200 <= int(code) < 400


def lies(monat: str):
    zeilen = []
    for datei in sorted(ABLAGE.glob(f"{monat}-*.log")):
        for zeile in datei.read_text(encoding="utf-8", errors="replace").splitlines():
            teile = zeile.split()
            if len(teile) == 5:
                zeilen.append(teile)
    return zeilen


def main():
    monat = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y-%m")
    zeilen = lies(monat)
    if not zeilen:
        print(f"Keine Messungen fuer {monat}.")
        print(f"Abgelegt wird unter {ABLAGE} je Tag eine Datei.")
        return 1

    gesamt = len(zeilen)
    aus_api = [z for z in zeilen if not erreichbar(z[1])]
    aus_lp = [z for z in zeilen if not erreichbar(z[3])]
    aus_beide = [z for z in zeilen if not erreichbar(z[1]) and not erreichbar(z[3])]

    def quote(ausfaelle):
        return 100.0 * (gesamt - len(ausfaelle)) / gesamt

    erste = datetime.fromtimestamp(int(zeilen[0][0]), timezone.utc)
    letzte = datetime.fromtimestamp(int(zeilen[-1][0]), timezone.utc)
    tage = (letzte - erste).days + 1
    erwartet = tage * 24 * 60

    print(f"Verfuegbarkeit {monat}")
    print("=" * 46)
    print(f"Messpunkte          {gesamt:7}  (erwartet rund {erwartet})")
    print(f"Zeitraum            {erste:%d.%m. %H:%M} bis {letzte:%d.%m. %H:%M} UTC")
    print()
    print(f"api.complyo.de      {quote(aus_api):7.3f} %   {len(aus_api)} Minuten ohne Antwort")
    print(f"complyo.de          {quote(aus_lp):7.3f} %   {len(aus_lp)} Minuten ohne Antwort")
    print(f"beide zugleich      {quote(aus_beide):7.3f} %   {len(aus_beide)} Minuten")

    if gesamt < erwartet * 0.95:
        fehlend = erwartet - gesamt
        print()
        print(f"ACHTUNG: {fehlend} Messungen fehlen ({100*fehlend/erwartet:.1f} %).")
        print("Eine Quote aus einer lueckenhaften Reihe ist zu gut, nicht zu schlecht:")
        print("ausgerechnet waehrend eines Ausfalls kann auch der Messende gestanden haben.")

    if aus_api:
        print()
        print("Laengste Unterbrechungen (api):")
        for beginn, dauer in laengste(aus_api)[:5]:
            print(f"  {beginn:%d.%m. %H:%M} UTC, {dauer} Minute(n)")

    print()
    print("Wie gemessen wurde")
    print("-" * 46)
    print("Einmal je Minute, vom Server selbst, ueber die oeffentliche Adresse")
    print("(DNS, TLS, nginx, Anwendung). Was diese Messung nicht sieht:")
    print("  * Netzprobleme zwischen Kunde und Rechenzentrum")
    print("  * Ausfaelle, die kuerzer sind als die Minute zwischen zwei Messungen")
    print("  * alles, was nur fuer angemeldete Nutzer kaputt ist")
    print("Sie misst vom kuerzesten Weg aus und faellt damit freundlicher aus")
    print("als eine Messung von aussen.")
    return 0


def laengste(ausfaelle):
    """Zusammenhaengende Minuten zu Unterbrechungen buendeln."""
    if not ausfaelle:
        return []
    zeiten = sorted(int(z[0]) for z in ausfaelle)
    bloecke = []
    start = vorher = zeiten[0]
    for t in zeiten[1:]:
        if t - vorher > 120:          # mehr als zwei Minuten Luecke = neuer Block
            bloecke.append((start, vorher))
            start = t
        vorher = t
    bloecke.append((start, vorher))
    ergebnis = [(datetime.fromtimestamp(a, timezone.utc), max(1, (b - a) // 60 + 1))
                for a, b in bloecke]
    return sorted(ergebnis, key=lambda x: -x[1])


if __name__ == "__main__":
    sys.exit(main())
