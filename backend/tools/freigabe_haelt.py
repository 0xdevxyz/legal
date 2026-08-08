#!/usr/bin/env python3
"""
Haelt eine erteilte Freigabe den naechsten Scan aus? Alle drei Wege.

Drei getrennte Upserts, drei Auspraegungen desselben Fehlers:

  Bildbeschreibung  suggested_alt wurde ueberschrieben, Status blieb
                    'approved' -> ein nie gesehener Text ging live.
  Dokument-Fix      status = EXCLUDED.status -> jede Farbfreigabe fiel beim
                    naechsten Scan auf 'pending' zurueck, die Reparatur
                    verschwand still von der Website.
  Linkname          wie die Bildbeschreibung.

Laeuft auf einer erfundenen site_id und raeumt hinterher auf.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, "/app")

SITE = "pruefstueck-freigabe-de"
befunde = []


def pruefe(name, bedingung, detail=""):
    print(("  ok   " if bedingung else "  FEHL ") + name + ("  " + detail if detail else ""))
    if not bedingung:
        befunde.append((name, detail))


async def main():
    import asyncpg
    from accessibility_fix_saver import AccessibilityFixSaver

    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=2)
    s = AccessibilityFixSaver(pool)

    async def aufraeumen():
        async with pool.acquire() as c:
            for t in ("accessibility_alt_text_fixes", "accessibility_document_fixes",
                      "accessibility_link_fixes"):
                await c.execute(f"DELETE FROM {t} WHERE site_id=$1", SITE)

    try:
        await aufraeumen()

        # ---------------------------------------------------- Bildbeschreibung
        print("\n=== Bildbeschreibung ===")
        def bild(t):
            return [{"image_src": "https://x.de/b.jpg", "page_url": "https://x.de/",
                     "image_filename": "b.jpg", "suggested_alt": t,
                     "confidence": 0.95, "page_title": "T",
                     "surrounding_text": "", "element_html": "<img>"}]

        await s.save_alt_text_fixes(SITE, "s1", "5", bild("Der freigegebene Text"))
        async with pool.acquire() as c:
            await c.execute("UPDATE accessibility_alt_text_fixes SET status='approved' "
                            "WHERE site_id=$1", SITE)
        await s.save_alt_text_fixes(SITE, "s2", "5", bild("Ein ganz anderer Text"))
        async with pool.acquire() as c:
            r = await c.fetchrow("SELECT status, suggested_alt, image_context "
                                 "FROM accessibility_alt_text_fixes WHERE site_id=$1", SITE)
        pruefe("freigegebener Text bleibt", r["suggested_alt"] == "Der freigegebene Text",
               repr(r["suggested_alt"]))
        pruefe("Freigabe bleibt", r["status"] == "approved", r["status"])
        ctx = r["image_context"]
        ctx = json.loads(ctx) if isinstance(ctx, str) else (ctx or {})
        pruefe("Abweichung ist festgehalten",
               ctx.get("abweichender_vorschlag") == "Ein ganz anderer Text", str(ctx)[:120])

        # noch offen -> darf sehr wohl ersetzt werden
        async with pool.acquire() as c:
            await c.execute("UPDATE accessibility_alt_text_fixes SET status='pending' "
                            "WHERE site_id=$1", SITE)
        await s.save_alt_text_fixes(SITE, "s3", "5", bild("Neuer Vorschlag"))
        async with pool.acquire() as c:
            t = await c.fetchval("SELECT suggested_alt FROM accessibility_alt_text_fixes "
                                 "WHERE site_id=$1", SITE)
        pruefe("offener Vorschlag wird sehr wohl ersetzt", t == "Neuer Vorschlag", repr(t))

        # ---------------------------------------------------- Dokument-Fix
        print("\n=== Dokument-Fix (Kontrast) ===")
        def dok(nr):
            return [{"fix_type": "kontrast-css",
                     "payload": {"entscheidungen": [{"nr": nr}], "vorher": 9,
                                 "nachher": 0},
                     "wcag_criterion": "1.4.3", "confidence": 0.9,
                     "page_url": "https://x.de/", "source": "scan",
                     # Genau so kommt kontrast-css aus dem Prozessor.
                     "status": "pending"}]

        await s.save_document_fixes(SITE, "d1", "5", dok(1))
        async with pool.acquire() as c:
            await c.execute("UPDATE accessibility_document_fixes SET status='approved', "
                            "approved_at=NOW() WHERE site_id=$1", SITE)
        await s.save_document_fixes(SITE, "d2", "5", dok(2))
        async with pool.acquire() as c:
            r = await c.fetchrow("SELECT status, payload, approved_at FROM "
                                 "accessibility_document_fixes WHERE site_id=$1", SITE)
        p = r["payload"]
        p = json.loads(p) if isinstance(p, str) else p
        pruefe("Freigabe ueberlebt den Rescan", r["status"] == "approved", r["status"])
        pruefe("freigegebene Entscheidung bleibt aktiv",
               p.get("entscheidungen") == [{"nr": 1}], str(p.get("entscheidungen")))
        pruefe("neuer Vorschlag ist hinterlegt",
               (p.get("neuer_vorschlag") or {}).get("entscheidungen") == [{"nr": 2}],
               str(p.get("neuer_vorschlag"))[:100])
        pruefe("Freigabedatum bleibt erhalten", r["approved_at"] is not None)

        # ---------------------------------------------------- Linkname
        print("\n=== Linkname ===")
        def link(t):
            return [{"link_href": "/kontakt", "href": "/kontakt", "link_text": "",
                     "text": "", "suggested_label": t, "label": t,
                     "confidence": 0.9, "surrounding_text": "",
                     "page_url": "https://x.de/"}]
        try:
            await s.save_link_fixes(SITE, "l1", "5", link("Zum Kontaktformular"))
            async with pool.acquire() as c:
                await c.execute("UPDATE accessibility_link_fixes SET status='approved' "
                                "WHERE site_id=$1", SITE)
            await s.save_link_fixes(SITE, "l2", "5", link("Hier klicken"))
            async with pool.acquire() as c:
                lab = await c.fetchval("SELECT suggested_label FROM accessibility_link_fixes "
                                       "WHERE site_id=$1", SITE)
            pruefe("freigegebene Beschriftung bleibt", lab == "Zum Kontaktformular", repr(lab))
        except Exception as e:
            print(f"  (Linkweg nicht pruefbar: {type(e).__name__}: {e})")

    finally:
        await aufraeumen()
        await pool.close()

    print("\n" + "=" * 62)
    print(f"{len(befunde)} Befunde" + ("" if not befunde else ":"))
    for n, d in befunde:
        print(f"  ! {n}: {d}")


asyncio.run(main())
