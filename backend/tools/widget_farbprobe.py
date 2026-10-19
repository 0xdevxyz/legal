#!/usr/bin/env python3
"""
Lebende Probe fuer das Barrierefreiheits-Widget in der Markenfarbe des Kunden.

Laedt accessibility-v6.js aus dem Arbeitsbaum in einen echten Chromium auf
drei Probeseiten und misst, was der Browser daraus macht (nicht, was der
Code behauptet):

  1. dunkle Seite in der Markenfarbe selbst  -> Knopf in Markenfarbe, weisse
     Schrift, UND ein weisser Ring (unter 3:1 zur Seite, WCAG 1.4.11)
  2. weisse Seite mit Markenfarbe            -> Knopf in Markenfarbe, kein Ring
  3. weisse Seite ohne Farbtoken             -> complyo-Standard (#00fff7, dunkle Schrift)

Die Widget-Konfig wird abgefangen und mit den Token aus
compliance_engine.markenfarben.widget_farbtoken beantwortet, alle anderen
Aufrufe an complyo.de mit leerem JSON. Es wird nichts ins Netz geschickt.

Aufruf (venv mit playwright, Chromium aus dem Playwright-Cache):
    python3 backend/tools/widget_farbprobe.py [#1d4ed8]

Exit 0 nur, wenn alle drei Erwartungen gemessen wurden.
"""

import glob
import http.server
import json
import os
import socketserver
import sys
import tempfile
import threading

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BACKEND)

from compliance_engine.markenfarben import kontrast, widget_farbtoken  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright fehlt: pip install playwright (Chromium aus ~/Library/Caches/ms-playwright reicht)")


def chromium_pfad() -> str:
    kandidaten = sorted(glob.glob(os.path.expanduser(
        "~/Library/Caches/ms-playwright/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/*")))
    kandidaten += sorted(glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome")))
    if not kandidaten:
        sys.exit("Kein Chromium im Playwright-Cache gefunden")
    return kandidaten[-1]


def probeseiten(ordner: str, marke: str) -> None:
    js = open(os.path.join(BACKEND, "widgets", "accessibility-v6.js"), encoding="utf-8").read()
    open(os.path.join(ordner, "accessibility.js"), "w", encoding="utf-8").write(js)
    for name, bg in (("dunkel.html", marke), ("weiss.html", "#ffffff")):
        open(os.path.join(ordner, name), "w", encoding="utf-8").write(
            '<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Probe</title></head>'
            f'<body style="background:{bg};margin:0"><main id="main"><h1>Probe</h1></main>'
            '<script src="/accessibility.js" data-site-id="probe-de"></script></body></html>')


def messen(page) -> dict:
    page.wait_for_selector("#complyo-a11y-widget .complyo-toggle-btn", timeout=15000)
    return page.evaluate("""() => {
        const c = document.getElementById('complyo-a11y-widget');
        const b = c.querySelector('.complyo-toggle-btn');
        const cs = getComputedStyle(b);
        return { solidToken: c.style.getPropertyValue('--c-accent-solid'),
                 knopfHintergrund: cs.backgroundColor, knopfSchrift: cs.color,
                 randBreite: cs.borderTopWidth, ring: b.dataset.complyoRing || null,
                 schatten: cs.boxShadow };
    }""")


def main() -> int:
    marke = sys.argv[1] if len(sys.argv) > 1 else "#1d4ed8"
    token = widget_farbtoken(marke)
    if not token:
        sys.exit(f"keine gueltige Hex-Farbe: {marke}")

    ordner = tempfile.mkdtemp(prefix="complyo-widget-probe-")
    probeseiten(ordner, marke)

    class Still(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def __init__(self, *a, **k):
            super().__init__(*a, directory=ordner, **k)

    srv = socketserver.TCPServer(("127.0.0.1", 0), Still)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    def rgb(hexwert: str) -> str:
        r, g, b = (int(hexwert[i:i + 2], 16) for i in (1, 3, 5))
        return f"rgb({r}, {g}, {b})"

    # Erwartung aus derselben Regel wie im Widget, nicht fest verdrahtet: Ring
    # genau dann, wenn Knopf und Seite unter 3:1 liegen, in der Farbe (Weiss
    # oder Dunkel), die gegen die Seite besser kontrastiert. Bei einer hellen
    # Marke (#00fff7) ist der Ring auf weisser Seite deshalb dunkel.
    def ring_erwartung(seitenfarbe: str) -> dict:
        if kontrast(token["accent_solid"], seitenfarbe) >= 3:
            return {"ring": None, "randBreite": "0px"}
        ring = "#ffffff" if kontrast("#ffffff", seitenfarbe) >= kontrast("#111827", seitenfarbe) else "#111827"
        return {"ring": ring, "randBreite": "2px"}

    faelle = [
        ("dunkel.html", True,  {"knopfHintergrund": rgb(token["accent_solid"]),
                                "knopfSchrift": rgb(token["on_accent_solid"]), **ring_erwartung(marke)}),
        ("weiss.html",  True,  {"knopfHintergrund": rgb(token["accent_solid"]),
                                "knopfSchrift": rgb(token["on_accent_solid"]), **ring_erwartung("#ffffff")}),
        ("weiss.html",  False, {"knopfHintergrund": "rgb(0, 255, 247)", "knopfSchrift": "rgb(17, 24, 39)", "ring": None}),
    ]
    fehler = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_pfad())
        for seite, mit_farben, erwartet in faelle:
            ctx = browser.new_context()
            page = ctx.new_page()

            # Achtung: Playwright reicht dem Handler (route, request). Ein zweiter
            # Positionsparameter bekaeme das Request-Objekt, nicht den Schalter.
            def abfangen(r, _req=None, mit=mit_farben):
                url = r.request.url
                if "/api/widgets/config/" in url:
                    cfg = {"cookie_consent": {}, "accessibility": {"enabled": True}}
                    if mit:
                        cfg["accessibility"]["farben"] = token
                    r.fulfill(status=200, content_type="application/json",
                              body=json.dumps({"success": True, "license_active": True, "config": cfg}))
                elif "complyo.de" in url:
                    r.fulfill(status=200, content_type="application/json", body="{}")
                else:
                    r.continue_()

            page.route("**/*", abfangen)
            page.goto(f"http://127.0.0.1:{port}/{seite}")
            m = messen(page)
            abweichungen = {k: (m.get(k), v) for k, v in erwartet.items() if m.get(k) != v}
            status = "OK " if not abweichungen else "ABWEICHUNG"
            fehler += bool(abweichungen)
            print(f"{status} {seite:12s} farben={'ja' if mit_farben else 'nein':4s} {json.dumps(m, ensure_ascii=False)}")
            if abweichungen:
                print("     erwartet/gemessen:", abweichungen)
            ctx.close()
        browser.close()
    srv.shutdown()
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
