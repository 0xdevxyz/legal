"""Bannerfarben nachziehen: alle Konfigurationen gegen ihre Website messen.

Aufruf im Backend-Container (Browser und Datenbank sind dort):

    docker exec complyo-backend python tools/farben_nachziehen.py            # Trockenlauf, alle
    docker exec complyo-backend python tools/farben_nachziehen.py --anwenden # schreibt
    docker exec complyo-backend python tools/farben_nachziehen.py --site complyo-de
    docker exec complyo-backend python tools/farben_nachziehen.py --anwenden --nur-automatisch   # Wochenlauf
    docker exec complyo-backend python tools/farben_nachziehen.py --markiere complyo-de --auto
    docker exec complyo-backend python tools/farben_nachziehen.py --markiere complyo-de --manuell

Standard ist der TROCKENLAUF: er zeigt je Konfiguration, was die Erkennung findet und
was sich aendern wuerde, und schreibt nichts. Geschrieben wird nur mit --anwenden,
und nur dort, wo das Kennzeichen `farben_automatisch` an ist (siehe
compliance_engine/farben_nachziehen.py). Von Hand gewaehlte Farben bleiben, werden
aber mit dem Vorschlag angezeigt, damit man sieht, was das Einschalten brachte.

Die Seiten werden nacheinander gelesen (je ein Browser-Durchlauf), nie parallel:
das Backend teilt sich seinen Speicher mit den Scans der Kunden.
"""
import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncpg  # noqa: E402

from compliance_engine.farben_nachziehen import (  # noqa: E402
    FELDER, nachziehen, setze_automatisch, vorschlag_aus_scan,
)

KURZ = {"primary_color": "haupt", "accent_color": "akzent", "text_color": "text", "bg_color": "grund"}


def _url_fuer(site_id: str, last_scan_url):
    if last_scan_url:
        return last_scan_url if last_scan_url.startswith("http") else f"https://{last_scan_url}"
    # complyo-de -> complyo.de: nur das letzte Bindestück ist die Endung.
    kopf, _, endung = site_id.rpartition("-")
    return f"https://{kopf}.{endung}" if kopf else None


def _zeile(site_id: str, zustand: str, alt, neu, felder=None) -> str:
    teile = [f"{site_id:<30} {zustand:<20}"]
    if alt and neu:
        for f in FELDER:
            markiert = "*" if felder and f in felder else " "
            teile.append(f"{KURZ[f]}{markiert}{alt.get(f)}->{neu[f]}")
    return "  ".join(teile)


async def _markiere(pool, site_id: str, wert: bool) -> int:
    ok = await setze_automatisch(pool, site_id, wert)
    print(f"{site_id}: farben_automatisch = {wert}" if ok else f"{site_id}: NICHT gesetzt (Zeile oder Spalte fehlt)")
    return 0 if ok else 1


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", action="append", help="nur diese site_id (mehrfach moeglich)")
    ap.add_argument("--anwenden", action="store_true", help="schreiben (sonst Trockenlauf)")
    ap.add_argument("--nur-automatisch", action="store_true",
                    help="nur Konfigurationen mit Kennzeichen farben_automatisch lesen (Wochenlauf)")
    ap.add_argument("--markiere", action="append", help="Kennzeichen fuer diese site_id setzen")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--auto", action="store_true", help="mit --markiere: folgt der Website")
    g.add_argument("--manuell", action="store_true", help="mit --markiere: von Hand gewaehlt")
    ap.add_argument("--timeout", type=float, default=25.0)
    args = ap.parse_args()

    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=2)
    try:
        if args.markiere:
            if not (args.auto or args.manuell):
                print("--markiere braucht --auto oder --manuell")
                return 2
            return sum([await _markiere(pool, s, bool(args.auto)) for s in args.markiere])

        from compliance_engine.markenfarben_gerendert import markenfarben_gerendert

        rows = await pool.fetch(
            "SELECT site_id, last_scan_url FROM cookie_banner_configs WHERE is_active "
            + ("AND farben_automatisch " if args.nur_automatisch else "")
            + ("AND site_id = ANY($1::text[]) " if args.site else "")
            + "ORDER BY site_id", *([args.site] if args.site else []))
        print(("ANWENDEN" if args.anwenden else "TROCKENLAUF") + f": {len(rows)} Konfiguration(en)\n")
        zaehler = {}
        for r in rows:
            site_id, url = r["site_id"], _url_fuer(r["site_id"], r["last_scan_url"])
            if not url:
                print(_zeile(site_id, "keine_adresse", None, None))
                continue
            try:
                gerendert = await markenfarben_gerendert(url, timeout_s=args.timeout)
            except Exception as e:  # ein Browserfehler darf den Lauf nicht beenden
                print(_zeile(site_id, f"fehler:{type(e).__name__}", None, None))
                continue
            erg = await nachziehen(pool, site_id, gerendert, anwenden=args.anwenden)
            zustand = erg["zustand"]
            zaehler[zustand] = zaehler.get(zustand, 0) + 1
            if zustand == "manuell":
                # Zeigen, was die Erkennung fuer diese Seite finden wuerde.
                vorschlag = vorschlag_aus_scan(gerendert)
                print(_zeile(site_id, "manuell", erg.get("alt"), vorschlag) if vorschlag
                      else _zeile(site_id, "manuell (nichts erkannt)", None, None))
            else:
                print(_zeile(site_id, zustand, erg.get("alt"), erg.get("neu"), erg.get("felder")))
        print("\nZusammenfassung:", ", ".join(f"{k} {v}" for k, v in sorted(zaehler.items())))
        return 0
    finally:
        await pool.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
