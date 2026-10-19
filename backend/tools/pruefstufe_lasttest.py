"""Lasttest der Prüfstufe mit echtem Chromium: N Nutzer gleichzeitig.

Misst, was die Einheitstests nur behaupten: wie viele Browser wirklich laufen,
wie viel Speicher alle Chromium-Prozesse zusammen belegen und wie lange die
letzte Prüfung wartet. Die Seiten sind lokal (ein Server, N Pfade), die
Fremdhosts im HTML sind echt (static.hotjar.com, fonts.googleapis.com), damit
der Browser wie bei einer Kundenseite Netzwerk braucht.

Aufruf (im Backend-Verzeichnis, mit installiertem Playwright und Chromium):

    SSRF_PRUEFSTAND_LOOPBACK=1 python tools/pruefstufe_lasttest.py --nutzer 100

Im Container auf openclaw (Speichergrenze wie im Betrieb):

    docker run --rm --memory 2g --memory-swap 2g -v $PWD:/src -w /src \\
        -e SSRF_PRUEFSTAND_LOOPBACK=1 legal-backend python tools/pruefstufe_lasttest.py --nutzer 100

Ausgabe: eine Zusammenfassung und je Sekunde eine Zeile mit Browsern und MiB.
Exit-Code 1, wenn ein Auftrag verloren ging oder die Spitze über dem Limit lag.
"""

import argparse
import asyncio
import http.server
import json
import os
import socketserver
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("SSRF_PRUEFSTAND_LOOPBACK", "1")

from compliance_engine import cookie_pruefstufe as ps  # noqa: E402

SEITE = """<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Kunde {n}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jost">
<script src="https://static.hotjar.com/c/hotjar-1.js" async></script></head>
<body><h1>Kunde {n}</h1>{koerper}<script>
  // wie ein Tracker, der nachlaedt
  setTimeout(function(){{ var i=new Image(); i.src='https://www.google-analytics.com/collect?n={n}'; }}, 400);
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        n = self.path.strip("/").replace("site", "") or "0"
        koerper = "<p>" + ("Text " * 400) + "</p>" * 1
        data = SEITE.format(n=n, koerper=koerper).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


class FakePool:
    """cookie_services und cookie_banner_configs im Speicher."""

    KATALOG = [
        ("google_fonts", ["fonts.googleapis.com", "fonts.gstatic.com"]),
        ("hotjar", ["hotjar.com", "static.hotjar.com"]),
        ("google_analytics_ga4", ["google-analytics.com", "googletagmanager.com"]),
    ]

    def __init__(self, ids):
        self.cfg = {i: ["wordpress"] for i in ids}

    async def fetch(self, sql, *a):
        if "FROM cookie_services" in sql:
            return [{"service_key": k, "name": k, "category": "functional", "provider": "",
                     "template": json.dumps({"domains": d})} for k, d in self.KATALOG]
        return []

    async def fetchrow(self, sql, site_id):
        return {"services": json.dumps(self.cfg[site_id])} if site_id in self.cfg else None

    async def execute(self, sql, site_id, neu, alt):
        if self.cfg.get(site_id) != json.loads(alt):
            return "UPDATE 0"
        self.cfg[site_id] = json.loads(neu)
        return "UPDATE 1"


def chromium_messung():
    """(Hauptprozesse, Summe RSS in MiB) aller Chromium-Prozesse dieses Tests.

    Nur Nachkommen des eigenen Prozesses zaehlen: auf einem Entwicklungsrechner
    laufen sonst fremde Browser mit.
    """
    out = subprocess.run(["ps", "-axo", "pid=,ppid=,rss=,args="], capture_output=True, text=True).stdout
    zeilen = {}
    for zeile in out.splitlines():
        teile = zeile.strip().split(None, 3)
        if len(teile) < 4:
            continue
        try:
            zeilen[int(teile[0])] = (int(teile[1]), int(teile[2]), teile[3].lower())
        except ValueError:
            continue
    meine = {os.getpid()}
    wuchs = True
    while wuchs:
        wuchs = False
        for pid, (ppid, _, _) in zeilen.items():
            if ppid in meine and pid not in meine:
                meine.add(pid)
                wuchs = True
    haupt, rss = 0, 0
    for pid in meine - {os.getpid()}:
        ppid, kb, args = zeilen[pid]
        if "chrom" not in args and "headless_shell" not in args:
            continue
        rss += kb
        if "--type=" not in args and "--remote-debugging" in args:
            haupt += 1
    return haupt, rss / 1024


def cgroup_mib():
    """Speicher der Container-Gruppe in MiB (cgroup v2, sonst v1), None ausserhalb von Docker.

    Das ist die Zahl, an der das Speicherlimit hängt. Die Summe der RSS-Werte
    aller Chromium-Prozesse zählt geteilte Seiten mehrfach und liegt deutlich höher.
    """
    for pfad in ("/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory/memory.usage_in_bytes"):
        try:
            return int(open(pfad).read().strip()) / 1048576
        except Exception:
            continue
    return None


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nutzer", type=int, default=100)
    ap.add_argument("--arbeiter", type=int, default=int(os.getenv("COMPLYO_PRUEFSTUFE_ARBEITER", "2")))
    ap.add_argument("--semaphor", type=int, default=6, help="Plätze, die der Rest des Backends übrig lässt")
    ap.add_argument("--limit-browser", type=int, default=None, help="Fehler, wenn die Spitze darüber liegt")
    ap.add_argument("--limit-mib", type=int, default=None)
    ap.add_argument("--zeit", type=int, default=75)
    args = ap.parse_args()

    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
    srv.daemon_threads = True
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    ps.ARBEITER_ANZAHL = args.arbeiter
    ps.JOB_ZEIT_S = args.zeit
    ps.WOCHE_AKTIV = False
    sem = asyncio.Semaphore(args.semaphor)
    ps._browser_semaphor = lambda: sem

    async def kein_redis():
        return None
    ps._redis = kein_redis

    ids = [f"kunde-{i}-de" for i in range(args.nutzer)]
    pool = FakePool(ids)
    await ps.starte()

    spitze = {"browser": 0, "mib": 0.0, "cgroup": 0.0}
    verlauf = []
    fertig_flag = asyncio.Event()

    async def messen():
        t0 = time.time()
        while not fertig_flag.is_set():
            b, mib = chromium_messung()
            spitze["browser"] = max(spitze["browser"], b)
            spitze["mib"] = max(spitze["mib"], mib)
            cg = cgroup_mib()
            if cg is not None:
                spitze["cgroup"] = max(spitze["cgroup"], cg)
            verlauf.append((round(time.time() - t0), b, round(mib)))
            await asyncio.sleep(1)

    messer = asyncio.create_task(messen())
    t0 = time.time()
    antworten = await asyncio.gather(*[
        ps.einreihen(s, f"http://127.0.0.1:{port}/site{i}", pool=pool, html_keys=["wordpress"])
        for i, s in enumerate(ids)
    ])
    t_annahme = time.time() - t0
    angenommen = [s for s, a in zip(ids, antworten) if a["zustand"] in ("wartend", "laeuft")]

    while not all(ps._jobs[s]["zustand"] in (ps.FERTIG, ps.FEHLGESCHLAGEN) for s in angenommen):
        await asyncio.sleep(0.5)
    gesamt = time.time() - t0
    fertig_flag.set()
    await messer
    await ps.beende()

    ok = [s for s in angenommen if ps._jobs[s]["zustand"] == ps.FERTIG]
    fehl = [s for s in angenommen if ps._jobs[s]["zustand"] == ps.FEHLGESCHLAGEN]
    mit_ergebnis = [s for s in ok if "hotjar" in pool.cfg[s]]
    dauern = sorted(ps._jobs[s]["dauer_s"] for s in ok)
    wartezeit = sorted(ps._jobs[s]["gestartet"] - ps._jobs[s]["gestellt"] for s in ok)

    def p(liste, q):
        return round(liste[min(len(liste) - 1, int(len(liste) * q))], 1) if liste else None

    print("\n=== Lasttest Pruefstufe ===")
    print(f"Nutzer gleichzeitig:       {args.nutzer}   Arbeiter: {args.arbeiter}   Semaphor: {args.semaphor}")
    print(f"Annahme aller Auftraege:   {t_annahme:.2f} s (angenommen {len(angenommen)}, abgelehnt {args.nutzer - len(angenommen)})")
    print(f"Gesamtdauer:               {gesamt:.0f} s")
    print(f"Fertig / fehlgeschlagen:   {len(ok)} / {len(fehl)}")
    print(f"Hotjar im Banner ergaenzt: {len(mit_ergebnis)} von {len(ok)}")
    print(f"Dauer je Pruefung (s):     Median {p(dauern, .5)}  P95 {p(dauern, .95)}  max {p(dauern, 1)}")
    print(f"Wartezeit bis Start (s):   Median {p(wartezeit, .5)}  P95 {p(wartezeit, .95)}  max {p(wartezeit, 1)}")
    print(f"SPITZE gleichzeitige Browser: {spitze['browser']}")
    print(f"SPITZE Chromium (Summe RSS):  {spitze['mib']:.0f} MiB")
    if spitze["cgroup"]:
        print(f"SPITZE Container (cgroup):    {spitze['cgroup']:.0f} MiB  (Grenze im Betrieb 2048)")
    print("Verlauf (Sekunde, Browser, MiB), jede 10. Sekunde: " + "; ".join(f"{a}s:{b}b/{c}M" for a, b, c in verlauf[::10]))

    fehler = []
    if len(ok) + len(fehl) != len(angenommen):
        fehler.append("Auftraege verloren")
    if fehl:
        fehler.append(f"{len(fehl)} fehlgeschlagen: " + "; ".join(sorted({ps._jobs[s].get('fehler', '?') for s in fehl})))
    if len(mit_ergebnis) != len(ok):
        fehler.append("Ergebnis nicht bei allen angewendet")
    if args.limit_browser and spitze["browser"] > args.limit_browser:
        fehler.append(f"Browser-Spitze {spitze['browser']} > {args.limit_browser}")
    gemessen = spitze["cgroup"] or spitze["mib"]
    if args.limit_mib and gemessen > args.limit_mib:
        fehler.append(f"Speicher-Spitze {gemessen:.0f} MiB > {args.limit_mib}")
    if fehler:
        print("FEHLER: " + " | ".join(fehler))
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
