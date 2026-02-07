Ziel: Eine komplette Cookie-Compliance-Lösung in complaio bauen – umsetzbar in Cursor

Das Konzept ist so strukturiert, dass ihr es Schritt-für-Schritt in Cursor implementieren könnt.
Alle Module sind darauf ausgelegt, dass Cursor automatisch Code generiert, testet und verknüpft.

1) Gesamtsystem-Architektur
Backend (Node.js / NestJS oder Express)

Cookie-Scanner (Headless-Browser + Parser)

Cookie-Datenbank

Provider-Katalog (Meta, Google, TikTok etc.)

Consent-Protokollierung

Script-Blocking Engine (Server-Seite Logik)

REST-/GraphQL-API

Frontend (Next.js / React)

Cookie-Banner-Komponente
-Kategorie-Auswahl

Detailansicht aller Cookies

Opt-out Center (Settings UI)

Barrierefreie UI (BFGS-ready)

Client Script (Vanilla JS, 20–30kb)

Blockiert Skripte

Ersetzt Iframes

Liest Consent aus

Kommuniziert mit Backend

Lädt erst nach Zustimmung Tracking-Skripte nach

2) Ordner- & Projektstruktur für Cursor
/complaio-cookie
│
├── backend/
│   ├── src/
│   │   ├── scanner/
│   │   │   ├── scanner.service.ts
│   │   │   ├── puppeteer.ts
│   │   │   └── parser.ts
│   │   ├── consent/
│   │   │   ├── consent.controller.ts
│   │   │   └── consent.service.ts
│   │   ├── cookies/
│   │   │   ├── cookies.service.ts
│   │   │   └── providers.json
│   │   └── api/
│   │       ├── public.controller.ts
│   │       └── public.service.ts
│   └── package.json
│
├── client/
│   ├── complaio-cookie.js
│   ├── blockers/
│   ├── iframe-replacements/
│   └── style.css
│
├── ui/
│   ├── Banner.tsx
│   ├── Modal.tsx
│   ├── Preferences.tsx
│   └── Theme.css
│
└── shared/
    └── types.ts

3) Module im Detail
🔍 3.1 Cookie-Scanner (Backend)
Technologien

Puppeteer oder Playwright

HTML-Parser

Request-Interceptor

Aufgaben

✔ Seite laden
✔ Alle Skripte vor DOM-Laden abfangen
✔ Cookies, Local Storage, Session Storage auslesen
✔ Third-Party Requests detektieren (z. B. www.google-analytics.com)
✔ Für jede Ressource → Kategorie bestimmen (via Provider-Katalog)

Cursor Prompt für diesen Schritt

"Erstelle einen Cookie-Scanner mit Puppeteer, der alle Third-Party-Requests, Cookies, Local-Storage-Einträge und Skript-URLs ausliest und diese in einem JSON-Array strukturiert zurückgibt. Jede URL soll über eine Provider-Liste einem Typ zugeordnet werden."

🧱 3.2 Cookie-Provider-Katalog

providers.json (Ausschnitt):

{
  "google-analytics.com": { "category": "analytics", "provider": "Google", "purpose": "Tracking" },
  "facebook.com/tr": { "category": "marketing", "provider": "Meta", "purpose": "Retargeting" }
}


Cursor kann diese Datei automatisiert erweitern.

🧊 3.3 Blocking Engine (Client Script)
Aufgaben:

✔ Verhindert das Laden von Tracking-Skripten
✔ Wandelt Tracking-Skripte um in:

<script type="text/plain" data-category="marketing">…</script>


✔ Blockiert externe Skripte per Mutation-Observer
✔ Ersetzt YouTube/TikTok/Iframe Inhalte durch Platzhalter
✔ Bei Consent → Skripte injecten

Cursor Prompt:

"Programmiere ein Script, das inline- und externes JavaScript mit Trackingmerkmalen abfängt, blockiert und stattdessen als type='text/plain' speichert. Nutze MutationObserver um dynamisch nachgeladene Skripte ebenfalls zu blockieren."

🎛 3.4 Banner & Modal (Next.js UI)
Funktionen:

Kategorien aktivierbar

"Alle akzeptieren"

"Alle ablehnen"

Cookie-Details

Barrierefrei (ARIA, Fokusfallen, Kontrast)

Dynamische Erkennung der Sprache

Cursor Prompt:

"Erstelle eine React-Komponente für ein DSGVO-konformes Cookie-Banner mit Accessibility-Funktionen, ARIA-Rollen und vollständiger Tastaturnavigation. Buttons: Alle akzeptieren, Alle ablehnen, Einstellungen."

📝 3.5 Consent-Protokollierung (Backend)
Speichert:

userId oder hash aus IP/UA

timestamp

Entscheidung pro Kategorie

Banner-Version

Widerrufe

Cursor Prompt:

"Schreibe ein Consent-Modell (PostgreSQL/Prisma), inkl. Endpunkte für CREATE, UPDATE, GET. Speichere: timestamp, ipHash, userAgent, categories, version."

⚙️ 3.6 Opt-out Center

Eine kleine React-Komponente, über window.complaio.openPreferences() aufrufbar.

4) Ablaufdiagramm – End-to-End
[User besucht Website]
      |
[complaio-cookie.js lädt]
      |
[Check: consent-cookie vorhanden?]
      |             \
 NEIN |              JA
      |               |
[Banner öffnen]    [Consent laden → Blocking Engine aktiv/inaktiv]
      |
[Nutzer trifft Auswahl]
      |
[Consent wird gespeichert (Backend)]
      |
[Blocking Engine lädt erlaubte Skripte]

5) API-Layer
Endpunkte:
Methode	Endpoint	Beschreibung
GET	/api/v1/cookies/scan?url=	Cookie/Tracker-Scan
POST	/api/v1/consent	Consent speichern
GET	/api/v1/consent/:hash	Consent abrufen
GET	/api/v1/providers	Cookie-Provider-Liste
POST	/api/v1/preview	Banner-UI testen
6) Vorgehensweise in Cursor
Schritt 1 – Projekt erzeugen

Im Cursor Terminal:

npx create-nx-workspace@latest complaio-cookie

Schritt 2 – Scanner generieren

In Cursor Chat:

"Implementiere den Cookie-Scanner gemäß Ordnerstruktur."

Cursor erzeugt automatisch:

Puppeteer-Setup

Request-Interceptor

Parser

Schritt 3 – Blocking Engine generieren

"Erstelle die blocking-engine.js Datei, basierend auf aufgeführten Anforderungen."

Schritt 4 – UI Komponenten erweitern

Cursor:

"Erstelle Banner.tsx & Preferences.tsx nach Schema."

Schritt 5 – API & Datenbank

Cursor:

"Erstelle Prisma-Schema für Consent, Provider-Katalog, und API-Endpunkte."

7) Erweiterungen, die später leicht integrierbar sind

TCF 2.2 Mode (Marketing-optimiert)

A/B Tests für Banner

Consent Rate Analysen

Browser-Fingerprint-Hash statt IP

8) Wert für complaio

Durch die Kombination aus:

echtem Blocking

echtem Scanner

automatischem Rechtstext-Update

Barrierefreiheit

DS-GVO Dokumentation

habt ihr eine Lösung, die Cookiebot, OneTrust & Usercentrics technisch überlegen ist – und perfekt mit euren anderen Säulen (BFGS, DSGVO, Rechtstexte) zusammenspielt.

Wenn du willst, generiere ich dir die ersten fertigen Code-Dateien für:
👉 den Scanner,
👉 das Client-Blocking-Script,
👉 das Banner-UI
– vollständig kompatibel mit Cursor.