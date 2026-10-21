"""
Markenfarben aus der gerenderten Seite statt aus dem Quelltext.

Der Quelltext-Extraktor (WebsiteCrawler.extract_brand_colors) zaehlt Hex-Werte
in HTML und CSS. Das misst, wie oft eine Farbe geschrieben steht, nicht, was
ein Besucher sieht: Theme-Stylesheets fuehren ganze Paletten (Warnrot,
Erfolgsgruen, Social-Media-Blau, Bootstrap-Grundfarben), SVG-Icons bringen
eigene Farben mit, und die eigentliche Markenfarbe steht oft in einer einzigen
Regel. Ergebnis am 21.10.2026: "meist falsch".

Hier laeuft die Seite im Browser, und gezaehlt wird, was gerendert ist: die
Hintergrundfarbe der Knoepfe, des Kopfbereichs und grosser Flaechen, die
Farbe von Links und Ueberschriften, jeweils nur fuer sichtbare Elemente in den
ersten zwei Bildschirmen. Ein vorhandener Cookie-Banner (fremder Anbieter)
bleibt aussen vor, sonst kaeme dessen Knopffarbe als Marke zurueck.

Die Bewertung (bewerte_farbproben) ist reines Python und ohne Browser
testbar; das Einsammeln (PROBEN_JS) laeuft in Playwright. Faellt der Browser
aus, liefert markenfarben_gerendert None und der Aufrufer nimmt den
Quelltext-Extraktor.
"""
import asyncio
import colorsys
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_VERFUEGBAR = True
except Exception:  # pragma: no cover - ohne Playwright gibt es nur den Rueckfall
    async_playwright = None
    PLAYWRIGHT_VERFUEGBAR = False

# Gewichte je Rolle: Knoepfe und Kopfbereich tragen die Marke, Links und
# Ueberschriften stuetzen sie, grosse Flaechen zaehlen, aber nicht je Pixel.
GEWICHTE = {
    'knopf': 6,
    'kopf': 5,
    'flaeche': 3,
    'link': 2,
    'ueberschrift': 2,
    'knopfschrift': 1,
}

# Elemente eines fremden Cookie-Banners oder einer Consent-Verwaltung: deren
# Knoepfe sind nicht die Marke der Website.
CONSENT_SELEKTOR = (
    '[id*="cookie" i],[class*="cookie" i],[id*="consent" i],[class*="consent" i],'
    '[id*="cmp" i],[class*="cmp-" i],[id*="borlabs" i],[class*="borlabs" i],'
    '[id*="Cybot" i],[id*="usercentrics" i],[class*="uc-" i],[id*="complyo" i],'
    '[class*="complyo" i],[id*="gdpr" i],[class*="gdpr" i],[aria-modal="true"]'
)

PROBEN_JS = """
(consentSelektor) => {
  const proben = [];
  const vh = window.innerHeight || 900;
  const vw = window.innerWidth || 1280;
  const grenze = vh * 2;
  const flaecheMin = vw * vh * 0.15;
  const sichtbar = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0 || r.top > grenze || r.bottom < 0) return null;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) === 0) return null;
    return { r, cs };
  };
  const imConsent = (el) => { try { return !!el.closest(consentSelektor); } catch (e) { return false; } };
  const melde = (rolle, farbe, el, flaeche) => {
    if (!farbe || farbe === 'transparent' || farbe === 'rgba(0, 0, 0, 0)') return;
    proben.push({ rolle, farbe, flaeche: flaeche || 0, tag: el.tagName.toLowerCase() });
  };
  const sammle = (selektor, rolle, eigenschaft, max) => {
    let n = 0;
    for (const el of document.querySelectorAll(selektor)) {
      if (n >= max) break;
      if (imConsent(el)) continue;
      const s = sichtbar(el);
      if (!s) continue;
      n++;
      melde(rolle, s.cs[eigenschaft], el, s.r.width * s.r.height);
      if (rolle === 'knopf') melde('knopfschrift', s.cs.color, el, 0);
    }
  };
  sammle('button, [role="button"], input[type="submit"], a.btn, a.button, .btn, .button, '
       + '.wp-block-button__link, .elementor-button, a[class*="btn"], a[class*="button"], '
       + '.cta, [class*="cta"]', 'knopf', 'backgroundColor', 60);
  sammle('header, nav, .site-header, #header, #masthead, .navbar, .elementor-location-header, '
       + '[role="banner"]', 'kopf', 'backgroundColor', 6);
  sammle('a', 'link', 'color', 300);
  sammle('h1, h2, h3', 'ueberschrift', 'color', 60);
  // Grosse Flaechen: Abschnitte, deren Hintergrund einen guten Teil des
  // Bildschirms fuellt (Hero, Streifen, Fusszeile).
  let flaechen = 0;
  for (const el of document.querySelectorAll('section, div, footer, main, article')) {
    if (flaechen >= 40) break;
    if (imConsent(el)) continue;
    const s = sichtbar(el);
    if (!s) continue;
    const a = s.r.width * s.r.height;
    if (a < flaecheMin) continue;
    flaechen++;
    melde('flaeche', s.cs.backgroundColor, el, a);
  }
  const body = getComputedStyle(document.body);
  melde('seite', body.backgroundColor, document.body, vw * vh);
  melde('text', body.color, document.body, 0);
  return proben;
}
"""

_RGB = re.compile(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([0-9.]+)\s*)?\)')


def _farbe_zu_hex(farbe: str) -> Optional[str]:
    """rgb()/rgba() aus getComputedStyle nach #rrggbb; None bei durchsichtig."""
    m = _RGB.match((farbe or '').strip())
    if not m:
        return None
    if m.group(4) is not None and float(m.group(4)) < 0.5:
        return None
    r, g, b = (max(0, min(255, int(m.group(i)))) for i in (1, 2, 3))
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def _hsv(farbe: str):
    r, g, b = (int(farbe[i:i + 2], 16) for i in (1, 3, 5))
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)


def ist_neutral(farbe: str) -> bool:
    """Grau, Weiss, Schwarz: Saettigung unter 12 % oder fast ohne Licht."""
    h, s, v = _hsv(farbe)
    return s < 0.12 or v < 0.08


def _verschieden(a: str, b: str) -> bool:
    """Zwei Farben, die als Primaer- und Akzentfarbe nebeneinander taugen."""
    ha, sa, va = _hsv(a)
    hb, sb, vb = _hsv(b)
    d = abs(ha - hb)
    d = min(d, 1 - d) * 360
    return d > 15 or abs(va - vb) > 0.15 or abs(sa - sb) > 0.25


def _dunkler(farbe: str, faktor: float) -> str:
    r, g, b = (int(farbe[i:i + 2], 16) for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    rr, gg, bb = colorsys.hls_to_rgb(h, l * faktor, s)
    return '#{:02x}{:02x}{:02x}'.format(int(rr * 255), int(gg * 255), int(bb * 255))


def bewerte_farbproben(proben: List[Dict[str, Any]], ausgeschlossen=frozenset()) -> Optional[Dict[str, Any]]:
    """
    Macht aus den Proben des Browsers dasselbe Ergebnis wie
    WebsiteCrawler.extract_brand_colors: primary_color, accent_color,
    text_color, bg_color, raw_candidates, scraped.

    `ausgeschlossen`: Farben, die nie Marke sind (Plattform-Standardknoepfe).
    """
    bunt: Dict[str, float] = {}
    hell: Dict[str, float] = {}
    dunkel: Dict[str, float] = {}
    rollen: Dict[str, set] = {}

    for p in proben or []:
        farbe = _farbe_zu_hex(str(p.get('farbe', '')))
        if not farbe:
            continue
        rolle = str(p.get('rolle', ''))
        gewicht = GEWICHTE.get(rolle, 0)
        h, s, v = _hsv(farbe)
        if rolle in ('seite', 'flaeche') and v > 0.9 and s < 0.12:
            hell[farbe] = hell.get(farbe, 0) + (3 if rolle == 'seite' else 1)
            continue
        if rolle in ('text', 'ueberschrift') and v < 0.3:
            dunkel[farbe] = dunkel.get(farbe, 0) + (3 if rolle == 'text' else 1)
            continue
        if gewicht == 0 or ist_neutral(farbe) or farbe in ausgeschlossen:
            continue
        bunt[farbe] = bunt.get(farbe, 0) + gewicht
        rollen.setdefault(farbe, set()).add(rolle)

    if not bunt:
        return None

    reihe = sorted(bunt.items(), key=lambda kv: kv[1], reverse=True)
    kandidaten = [f for f, _ in reihe]
    primary = kandidaten[0]
    accent = next((f for f in kandidaten[1:] if _verschieden(primary, f)), None)
    if accent is None:
        accent = _dunkler(primary, 0.8)

    bg = max(hell.items(), key=lambda kv: kv[1])[0] if hell else '#ffffff'
    text = max(dunkel.items(), key=lambda kv: kv[1])[0] if dunkel else '#333333'

    return {
        'primary_color': primary,
        'accent_color': accent,
        'text_color': text,
        'bg_color': bg,
        'raw_candidates': kandidaten[:10],
        'rollen': {f: sorted(r) for f, r in rollen.items() if f in kandidaten[:10]},
        'scraped': True,
        'quelle': 'gerendert',
    }


async def markenfarben_aus_seite(page, ausgeschlossen=frozenset()) -> Optional[Dict[str, Any]]:
    """Proben aus einer geladenen Playwright-Seite ziehen und bewerten."""
    proben = await page.evaluate(PROBEN_JS, CONSENT_SELEKTOR)
    return bewerte_farbproben(proben or [], ausgeschlossen)


async def markenfarben_gerendert(url: str, timeout_s: float = 20.0) -> Optional[Dict[str, Any]]:
    """
    Seite im Browser laden und die sichtbaren Markenfarben lesen.

    None, wenn Playwright fehlt, die Seite nicht laedt oder nichts Buntes
    sichtbar ist; der Aufrufer faellt dann auf den Quelltext-Extraktor zurueck.
    Die Adresse muss der Aufrufer schon gegen SSRF geprueft haben.
    """
    # Tests und Betrieb ohne Browser: COMPLYO_OHNE_BROWSER=1 schaltet den
    # Lauf ab, der Aufrufer bleibt beim Quelltext-Extraktor.
    if not PLAYWRIGHT_VERFUEGBAR or os.getenv('COMPLYO_OHNE_BROWSER') == '1':
        return None
    try:
        from website_crawler import PLATTFORM_STANDARDFARBEN
    except Exception:  # pragma: no cover
        PLATTFORM_STANDARDFARBEN = frozenset()

    async def _lauf():
        async with async_playwright() as pw:
            start = {}
            # Lokale Laeufe ohne "playwright install": Chromium per Umgebungsvariable.
            if os.getenv('COMPLYO_CHROMIUM'):
                start['executable_path'] = os.getenv('COMPLYO_CHROMIUM')
            browser = await pw.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
                **start,
            )
            try:
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 900},
                    user_agent=('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Complyo-Scanner/2.0'),
                    locale='de-DE',
                )
                page = await context.new_page()
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                try:
                    await page.wait_for_load_state('networkidle', timeout=4000)
                except Exception:
                    pass
                await asyncio.sleep(0.8)
                return await markenfarben_aus_seite(page, PLATTFORM_STANDARDFARBEN)
            finally:
                await browser.close()

    try:
        return await asyncio.wait_for(_lauf(), timeout=timeout_s)
    except Exception as e:
        logger.warning(f"Gerenderte Markenfarben fuer {url} nicht lesbar: {e}")
        return None
