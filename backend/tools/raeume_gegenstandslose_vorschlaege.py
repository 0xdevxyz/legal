"""Raeumt wartende Reparatur-Vorschlaege weg, die nichts Neues sagen.

Ein freigegebener Fix wird beim naechsten Scan nicht ueberschrieben; der neue
Vorschlag wartet unter `neuer_vorschlag` im Payload auf eine Entscheidung. Bis
zum 15.09.2026 entstand so ein Vorschlag ohne jeden Vergleich — bei
`kontrast-css` deshalb bei JEDEM Scan, denn so eine Zeile wird immer als
'pending' gespeichert. Gemessen an diesem Tag waren sechs von sieben wartenden
Vorschlaegen mit der laufenden Reparatur identisch; einer stand seit dem 12.08.

Geprueft wird hier mit derselben Funktion, die kuenftig verhindert, dass solche
Vorschlaege ueberhaupt entstehen. Was sie fuer neu haelt, bleibt stehen.

Aufruf (Trockenlauf; ANWENDEN=ja schreibt):
    docker run --rm --network legal_complyo-network \
      -v /home/clawd/saas/legal/backend:/app -w /app \
      -e DATABASE_URL="..." legal-backend \
      python tools/raeume_gegenstandslose_vorschlaege.py
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, "/app")

import asyncpg

from accessibility_fix_saver import _vorschlag_ist_neu

ANWENDEN = os.environ.get("ANWENDEN") == "ja"


async def main() -> None:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        rows = await conn.fetch(
            "SELECT id, site_id, fix_type, payload "
            "FROM accessibility_document_fixes "
            "WHERE payload ? 'neuer_vorschlag' ORDER BY id"
        )
        geraeumt = 0
        for r in rows:
            payload = r["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            laufend = {k: v for k, v in payload.items()
                       if k not in ("neuer_vorschlag", "bemerkt_am")}
            vorschlag = payload.get("neuer_vorschlag") or {}

            if _vorschlag_ist_neu(laufend, vorschlag):
                print(f"BLEIBT  id={r['id']:>3} {r['site_id']:<24} {r['fix_type']}")
                continue

            print(f"raeumen id={r['id']:>3} {r['site_id']:<24} {r['fix_type']}")
            if ANWENDEN:
                await conn.execute(
                    "UPDATE accessibility_document_fixes "
                    "SET payload = payload - 'neuer_vorschlag' - 'bemerkt_am', "
                    "    updated_at = NOW() "
                    "WHERE id = $1",
                    r["id"],
                )
                geraeumt += 1

        nachsatz = "" if ANWENDEN else " (Trockenlauf: nichts geschrieben)"
        print(f"\n{len(rows)} wartende Vorschlaege geprueft, "
              f"{geraeumt} geraeumt{nachsatz}")
    finally:
        await conn.close()


if __name__ == "__main__":
    if not ANWENDEN:
        print("== Trockenlauf. ANWENDEN=ja schreibt wirklich. ==")
    asyncio.run(main())
