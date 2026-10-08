#!/usr/bin/env python3
"""
Pruefstand: was sagt der Scanner ueber einen Bestand echter Seiten?

Nicht der einzelne Befund ist die Frage, sondern seine HAEUFIGKEIT. Alle acht
Phantom-Regeln, die am 08.09.2026 aufflogen, sahen gleich aus: sie feuerten auf
fast jeder Seite. Eine Pflicht, die 23 von 23 deutschen Handwerks- und
Praxis-Websites gleichzeitig verletzen, ist keine Pflicht, sondern ein
Messfehler.

Aufruf im Backend-Image, Mount auf /src (NICHT /app — sonst verdeckt der Mount
die Playwright-Browser unter /app/.cache und der Scan faellt still auf
Heuristik zurueck).
"""
import argparse
import asyncio
import contextlib
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ki_schalter(ki: str):
    """
    Kontext fuer einen Lauf mit oder ohne KI-Zweitmeinung.

    "aus" misst, was der Scanner ohne fremden Dienst feststellt: Muster,
    axe, deklarative Regeln. Unsichere Pflichtangaben erscheinen dann als
    "nicht abschliessend geprueft" (info, 0 EUR) statt als Befund. Erst der
    Vergleich zweier Laeufe (an/aus, pruefstand_vergleich.py) zeigt, welche
    Befunde am KI-Budget haengen und nicht an der Website.
    """
    if ki == "aus":
        from compliance_engine import ai_budget
        return ai_budget.ki_aus()
    return contextlib.nullcontext()


async def eine_seite(url: str, sem: asyncio.Semaphore, ki: str = "an") -> dict:
    from compliance_engine.scanner import ComplianceScanner
    async with sem:
        # Der Schalter sitzt in einer contextvar; jede gather()-Aufgabe hat
        # ihre eigene Kopie, der Kontext bleibt also auf diese Seite begrenzt.
        with ki_schalter(ki):
            try:
                async with ComplianceScanner() as s:
                    r = await s.scan_website(url)
            except Exception as e:
                return {"url": url, "fehler": f"{type(e).__name__}: {e}"}

    if r.get("error"):
        return {"url": url, "fehler": r.get("error_message", "nicht scanbar")}

    return {
        "url": url,
        "score": r.get("compliance_score"),
        "issues": [
            {
                "category": i.get("category"),
                "severity": i.get("severity"),
                "title": i.get("title"),
                "risk_euro": i.get("risk_euro"),
                "slug": (i.get("metadata") or {}).get("declarative_check_slug"),
                "quelle": (i.get("metadata") or {}).get("source"),
                "axe_rule": (i.get("metadata") or {}).get("axe_rule_id"),
            }
            for i in (r.get("issues") or [])
        ],
    }


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--ki", choices=("an", "aus"), default="an",
                    help="aus: kein KI-Aufruf, nur Muster/axe/Regeln (kostet keine Token)")
    args = ap.parse_args()

    import asyncpg

    urls = [z.strip() for z in open(args.datei) if z.strip() and not z.startswith("#")]
    urls = [u if u.startswith("http") else f"https://{u}" for u in urls]

    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=3)
    from compliance_engine import declarative_check_runner as dcr
    dcr.init_declarative_check_registry(pool)
    await dcr.declarative_check_registry.get_active_checks(force_refresh=True)

    sem = asyncio.Semaphore(args.parallel)
    ergebnisse = await asyncio.gather(*(eine_seite(u, sem, args.ki) for u in urls))

    os.makedirs(args.out, exist_ok=True)
    ziel = os.path.join(args.out, "pruefstand.json")
    with open(ziel, "w", encoding="utf-8") as f:
        json.dump({"gemessen": datetime.now().isoformat(), "ki": args.ki,
                   "seiten": ergebnisse},
                  f, ensure_ascii=False, indent=1)

    ok = [e for e in ergebnisse if "issues" in e]
    print(f"\n{len(ok)}/{len(urls)} Seiten gescannt, Ablage: {ziel}")
    for e in ergebnisse:
        if "fehler" in e:
            print(f"  FEHLER {e['url']}: {e['fehler'][:90]}")
        else:
            n = len(e["issues"])
            krit = sum(1 for i in e["issues"] if i["severity"] == "critical")
            print(f"  {e['score']:>3}/100  {n:>3} Befunde ({krit} kritisch)  {e['url']}")


if __name__ == "__main__":
    asyncio.run(main())
