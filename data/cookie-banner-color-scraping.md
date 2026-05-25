# Cookie-Banner Farb-Scraping bei Website-Erstellung

## Ziel
Beim Hinzufügen einer neuen Website werden automatisch die Markenfarben der Seite gescrapt
und als Vorschlag in die Cookie-Banner-Konfiguration eingetragen.

## Implementierte Dateien

### `backend/website_crawler.py`
- `import colorsys` hinzugefügt
- `Tuple` zu Typing-Imports hinzugefügt
- `extract_brand_colors(soup, html)` — neue public Methode
  - Analysiert CSS-Variablen (`--primary-color`, `--brand-*`, etc.) mit Gewichtung x5
  - Analysiert Inline-Styles an `header`, `nav`, `button`, `a`, `h1`, `h2` mit Gewichtung x3
  - Analysiert alle Hex-Farben im HTML mit Gewichtung x1
  - Filtert Neutralfarben (near-white/near-black/entsättigt) heraus
  - Gibt zurück: `primary_color`, `accent_color`, `text_color`, `bg_color`, `raw_candidates`, `scraped`
- `crawl_website()` — `brand_colors` jetzt im zurückgegebenen structure-Dict enthalten

### `backend/website_routes.py`
- Beim POST einer neuen Website (vor INSERT in `cookie_banner_configs`):
  - Fetched die URL mit 10s Timeout (SSRF-gesichert via `validate_url`)
  - Parst HTML mit BeautifulSoup
  - Ruft `WebsiteCrawler().extract_brand_colors()` auf
  - Bei Erfolg (`scraped=True`): gescrapte Farben werden in die Banner-Config eingetragen
  - Bei Fehler: Fallback auf bisherige Defaults (`#7c3aed`, `#8b5cf6`, etc.)
  - Kein kritischer Fehler — Exception wird geloggt, Website-Erstellung läuft weiter

## Fehler-Handling
- SSRF-Schutz: ungültige/interne URLs werden blockiert
- Timeout: 10 Sekunden (nicht der volle Crawl-Timeout von 30s)
- Jede Exception wird als Warning geloggt, nicht als Fehler behandelt
- Fallback-Farben bleiben erhalten wenn Scraping fehlschlägt
