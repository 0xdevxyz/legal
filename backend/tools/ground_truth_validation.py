# -*- coding: utf-8 -*-
"""
Ground-Truth-Validierung des complyo-Scanners (READ-ONLY gegen Prod-Container).

4 Fixture-Websites mit exakt bekannten Eigenschaften werden lokal serviert und
durch die ECHTE Pipeline (ComplianceScanner.scan_website inkl. Render, axe,
deklarative DB-Checks) gescannt. Auswertung: erwartete Befunde vorhanden
(Recall) + verbotene Befunde abwesend (Precision) + Saeulen-Klassifikation.
"""

import asyncio
import http.server
import json
import socketserver
import threading

PORT = 8099

IMPRESSUM_OK = """<!doctype html><html lang="de"><head><title>Impressum</title></head><body>
<main><h1>Impressum</h1>
<p>Angaben gemäß § 5 DDG</p>
<p>Muster GmbH<br>Musterweg 1<br>04109 Leipzig</p>
<p>Vertreten durch: Max Mustermann (Geschäftsführer)</p>
<p>Kontakt: E-Mail info@muster-firma.de, Telefon: 0341 123456</p>
<p>Registergericht: Amtsgericht Leipzig, HRB 12345</p>
<p>USt-IdNr: DE123456789</p>
<p>Verantwortlich für den Inhalt: Max Mustermann</p>
</main></body></html>"""

DATENSCHUTZ_OK = """<!doctype html><html lang="de"><head><title>Datenschutz</title></head><body>
<main><h1>Datenschutzerklärung</h1>
<p>Verantwortlicher im Sinne der DSGVO: Muster GmbH, Musterweg 1, 04109 Leipzig, info@muster-firma.de.</p>
<p>Zwecke der Verarbeitung: Bereitstellung der Website, Beantwortung von Anfragen.</p>
<p>Rechtsgrundlage ist Art. 6 Abs. 1 lit. b und f DSGVO.</p>
<p>Speicherdauer: Wir verarbeiten personenbezogene Daten nur solange erforderlich; Server-Logs werden nach 7 Tagen gelöscht.</p>
<p>Ihre Betroffenenrechte: Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit, Widerspruch.</p>
<p>Beschwerderecht: Sie haben das Recht auf Beschwerde bei einer Aufsichtsbehörde (Sächsischer Datenschutzbeauftragter).</p>
<p>Für eingesetzte Google-Dienste bestehen Standardvertragsklauseln (SCC) gemäß Art. 46 DSGVO.</p>
</main></body></html>"""

FIXTURES = {
    # A — SAUBER: alles korrekt. Erwartung: keine Criticals (ausser SSL, da http://localhost)
    "sauber": {
        "/": """<!doctype html><html lang="de"><head><title>Muster GmbH — Beratung</title></head><body>
<a href="#main" class="skip-link">Zum Inhalt springen</a>
<header><nav><a href="/">Start</a> <a href="/impressum">Impressum</a> <a href="/datenschutz">Datenschutz</a></nav></header>
<main id="main"><h1>Willkommen bei Muster GmbH</h1>
<p>Wir beraten Unternehmen zu Prozessen.</p>
<img src="/logo.png" alt="Logo der Muster GmbH">
<form><label for="mail">E-Mail</label><input id="mail" type="email" name="email">
<p>Mit dem Absenden stimmen Sie der Verarbeitung gemäß unserer <a href="/datenschutz">Datenschutzerklärung</a> zu (Einwilligung).</p>
<button type="submit">Kontakt aufnehmen</button></form>
</main>
<div class="cookie-banner"><p>Wir verwenden nur technisch notwendige Cookies.</p>
<button id="acc">Alle akzeptieren</button><button id="rej">Alle ablehnen</button>
<a href="/cookie-einstellungen">Cookie-Einstellungen (Kategorien: Statistik, Marketing)</a>
<span>Sie können Ihre Einwilligung jederzeit widerrufen.</span></div>
<footer><a href="/impressum">Impressum</a> <a href="/datenschutz">Datenschutz</a></footer>
</body></html>""",
        "/impressum": IMPRESSUM_OK,
        "/datenschutz": DATENSCHUTZ_OK,
        "expect_present": [],
        "expect_absent": [
            "Kein Impressum", "Impressum-Link", "Datenschutzerklärung fehlt",
            "vor Consent geladen", "Vorangekreuzte", "Keine Ablehnungsmöglichkeit",
            "Bild ohne Alt-Text", "Widerrufsbelehrung", "Kündigungsbutton",
            "ohne Drittland-Rechtsgrundlage", "Shop",
        ],
        "no_criticals_except": ["SSL", "HTTPS"],
    },
    # B — SUENDER: nichts vorhanden + Tracking ohne Banner + A11y-Fehler
    "suender": {
        "/": """<!doctype html><html><head>
<script src="https://google-analytics.com/analytics.js"></script>
</head><body>
<div><span>Firma Beispiel</span></div>
<img src="/team.jpg">
<img src="/produkt.jpg">
<div onclick="go()" role="button"></div>
<input type="text" name="q">
</body></html>""",
        "expect_present": [
            "Impressum", "Datenschutz", "Cookie", "Alt-Text", "lang",
        ],
        "expect_absent": ["Kündigungsbutton", "Widerrufsbelehrung"],
        "min_criticals": 4,
    },
    # C — COOKIE-SUENDER: Banner ohne Reject, GA-Script, vorangekreuzter Toggle
    "cookie-suender": {
        "/": """<!doctype html><html lang="de"><head><title>Cookie-Test GmbH</title>
<script src="https://google-analytics.com/analytics.js"></script>
</head><body>
<header><nav><a href="/impressum">Impressum</a> <a href="/datenschutz">Datenschutz</a></nav></header>
<main><h1>Cookie-Test</h1><img src="/x.png" alt="Testbild"></main>
<div class="cookie-banner"><p>Diese Seite nutzt Cookies für Statistik und Marketing.</p>
<input type="checkbox" checked name="marketing-cookies"><label>Marketing</label>
<button id="acc">Alle akzeptieren</button></div>
</body></html>""",
        "/impressum": IMPRESSUM_OK,
        "/datenschutz": DATENSCHUTZ_OK,
        "expect_present": [
            "Ablehnungsmöglichkeit", "vor Consent geladen", "Vorangekreuzte",
        ],
        "expect_absent": ["Kein Cookie-Consent-Banner", "Kein Impressum"],
    },
    # D — SAAS: Abo ohne Warenkorb, kein Widerruf, kein Kündigungsbutton
    "saas": {
        "/": """<!doctype html><html lang="de"><head><title>CloudTool — Software im Abo</title></head><body>
<header><nav><a href="/impressum">Impressum</a> <a href="/datenschutz">Datenschutz</a></nav></header>
<main><h1>CloudTool im Abonnement</h1>
<p>Unser Tarif: 29 Euro pro Monat, monatlich kündbar. Jetzt Mitgliedschaft starten.</p>
<img src="/screen.png" alt="Screenshot der Software"></main>
<footer><a href="/impressum">Impressum</a> <a href="/datenschutz">Datenschutz</a></footer>
</body></html>""",
        "/impressum": IMPRESSUM_OK,
        "/datenschutz": DATENSCHUTZ_OK,
        "expect_present": ["Widerruf", "Kündigungsbutton"],
        "expect_absent": ["AGB fehlen", "MwSt", "Versandkosten", "Grundpreis"],
    },
}

_current_fixture = {"name": "sauber"}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        pages = FIXTURES[_current_fixture["name"]]
        path = self.path.split("?")[0]
        body = pages.get(path)
        if body is None:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>404 Not Found</h1></body></html>")
            return
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def start_server():
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv


async def run():
    from compliance_engine.scanner import ComplianceScanner
    from compliance_engine.score_calculator import ScoreCalculator

    report = {}
    for name in FIXTURES:
        _current_fixture["name"] = name
        async with ComplianceScanner() as scanner:
            result = await scanner.scan_website(f"http://127.0.0.1:{PORT}/")

        issues = result.get("issues") or []
        titles = [str(i.get("title", "")) for i in issues]
        crits = [i for i in issues if i.get("severity") == "critical"]

        spec = FIXTURES[name]
        missing_expected = [
            e for e in spec.get("expect_present", [])
            if not any(e.lower() in t.lower() for t in titles)
        ]
        false_positives = [
            a for a in spec.get("expect_absent", [])
            if any(a.lower() in t.lower() for t in titles)
        ]
        bad_criticals = []
        if "no_criticals_except" in spec:
            allow = spec["no_criticals_except"]
            bad_criticals = [
                i["title"] for i in crits
                if not any(a.lower() in str(i.get("title", "")).lower() for a in allow)
            ]

        # Klassifikations-Check: jede Issue-Kategorie muss einer Saeule zuordenbar sein
        unclassified = []
        for i in issues:
            pillar = ScoreCalculator.categorize(str(i.get("category", "")))
            if pillar not in ScoreCalculator.PILLAR_IDS:
                unclassified.append(i.get("category"))

        report[name] = {
            "issues_total": len(issues),
            "criticals": len(crits),
            "score": next((result[k] for k in ("compliance_score", "score")
                           if result.get(k) is not None), None),
            "pillar_scores": (result.get("pillar_scores")
                              or (result.get("scores") or {}).get("pillar_scores")),
            "RECALL_missing_expected": missing_expected,
            "PRECISION_false_positives": false_positives,
            "bad_criticals": bad_criticals,
            "unclassified_categories": unclassified,
            "min_criticals_ok": (len(crits) >= spec["min_criticals"]) if "min_criticals" in spec else None,
            "titles": titles,
        }

    print(json.dumps(report, ensure_ascii=False, indent=1))


srv = start_server()
try:
    asyncio.run(run())
finally:
    srv.shutdown()
