"""
Logo der Website aus der gerenderten Seite lesen.

Anlass (12.11.2026): Im Einstellungsfenster des Cookie-Banners stand ein
festes "C" in einem Kreis. Das ist die Stelle, an der ein Besucher den
Absender erwartet, also das Logo des Kunden. Das Feld `custom_logo_url` gab es
in `cookie_banner_configs` von Anfang an, nur fuellte es niemand und das
Widget las es nicht.

Wie bei den Markenfarben (markenfarben_gerendert.py) wird nichts von Hand
gesetzt: die Seite laeuft im Browser, und genommen wird, was ein Besucher im
Kopf der Seite als Logo sieht. Reihenfolge der Quellen:

  1. sichtbares Bild im Kopfbereich (Kennzeichen "logo", Link auf die
     Startseite, liegt in header/nav), mit der Hintergrundfarbe dahinter,
  2. das in schema.org angegebene Logo (JSON-LD, Organization.logo),
  3. apple-touch-icon,
  4. Favicon (SVG oder PNG).

Ist nichts davon da, gibt es kein Logo und der Banner zeigt den
Anfangsbuchstaben der Website. Lieber keins als ein falsches.

Die Adresse zeigt auf die Datei, die die Kundenseite ohnehin selbst laedt. Der
Banner laeuft auf derselben Seite, es entsteht also kein neuer fremder Abruf
und complyo speichert keine Kopie.

Kennzeichnung: automatisch erkannte Adressen tragen das Fragment
`#complyo-auto` (auf dunklem Kopfbereich `#complyo-auto-dunkel`). Ein Fragment
geht nie an den Server der Kundenseite. Daran erkennt der Scan, was er beim
naechsten Lauf erneuern darf; eine von Hand gesetzte Adresse hat kein Fragment
und wird nie ueberschrieben. Das Widget liest aus dem Fragment, ob das Logo
fuer einen dunklen Grund gezeichnet ist.

bewerte_logokandidaten ist reines Python und ohne Browser testbar.
"""
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

MARKE_AUTO = "#complyo-auto"
MARKE_DUNKEL = "#complyo-auto-dunkel"
MAX_LAENGE = 500

# Bilder im Kopf, die kein Logo sind.
KEIN_LOGO = re.compile(
    r"(facebook|instagram|linkedin|youtube|twitter|whatsapp|tiktok|xing|pinterest|"
    r"flag|flagge|sprache|lang-|avatar|gravatar|banner|hero|slider|sprite|pixel|"
    r"spacer|loading|spinner|trustpilot|siegel|badge|award|payment|paypal|klarna|visa)",
    re.I,
)

LOGO_JS = """
(consentSelektor) => {
  const aus = { bilder: [], jsonld: [], icons: [], breite: window.innerWidth || 1280 };
  const imConsent = (el) => { try { return !!el.closest(consentSelektor); } catch (e) { return false; } };
  const sichtbar = (el, r) => {
    const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.1;
  };
  const hintergrund = (el) => {
    for (let k = el; k && k !== document.documentElement; k = k.parentElement) {
      const f = getComputedStyle(k).backgroundColor;
      const m = f && f.match(/rgba?\\(([^)]+)\\)/);
      if (!m) continue;
      const t = m[1].split(',').map((x) => parseFloat(x));
      if (t.length < 4 || t[3] > 0.5) return [t[0], t[1], t[2]];
    }
    const b = getComputedStyle(document.body).backgroundColor.match(/rgba?\\(([^)]+)\\)/);
    if (b) { const t = b[1].split(',').map((x) => parseFloat(x)); if (t.length < 4 || t[3] > 0.5) return [t[0], t[1], t[2]]; }
    return [255, 255, 255];
  };
  const startseite = (a) => {
    if (!a) return false;
    try {
      const u = new URL(a.getAttribute('href') || '', location.href);
      return u.host === location.host && (u.pathname === '/' || u.pathname === '' || /^\\/(index\\.(html?|php)|de\\/?|home\\/?)$/i.test(u.pathname));
    } catch (e) { return false; }
  };
  for (const img of Array.from(document.images).slice(0, 400)) {
    if (imConsent(img)) continue;
    const r = img.getBoundingClientRect();
    const oben = r.top + (window.scrollY || 0);
    if (oben > 420 || !sichtbar(img, r)) continue;
    const src = img.currentSrc || img.src || '';
    if (!src) continue;
    const kennung = [img.className && String(img.className), img.id, img.alt, src,
      img.parentElement && String(img.parentElement.className), img.parentElement && img.parentElement.id].join(' ');
    aus.bilder.push({
      src: src.slice(0, 2100), b: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.left), y: Math.round(oben),
      logoWort: /logo|(^|[^a-z])brand|site-title/i.test(kennung), kennung: kennung.slice(0, 300),
      imKopf: !!img.closest('header, nav, [role="banner"], [class*="header" i], [id*="header" i], [class*="navbar" i], [class*="topbar" i]'),
      zurStartseite: startseite(img.closest('a')),
      grund: hintergrund(img),
    });
  }
  for (const s of Array.from(document.querySelectorAll('script[type="application/ld+json"]')).slice(0, 20)) {
    try {
      const lauf = (o, tiefe) => {
        if (!o || tiefe > 4) return;
        if (Array.isArray(o)) { o.forEach((x) => lauf(x, tiefe + 1)); return; }
        if (typeof o !== 'object') return;
        if (o.logo) { const l = typeof o.logo === 'string' ? o.logo : (o.logo.url || o.logo.contentUrl || ''); if (l) aus.jsonld.push(String(l).slice(0, 2100)); }
        if (o['@graph']) lauf(o['@graph'], tiefe + 1);
        if (o.publisher) lauf(o.publisher, tiefe + 1);
      };
      lauf(JSON.parse(s.textContent || 'null'), 0);
    } catch (e) {}
  }
  for (const l of Array.from(document.querySelectorAll('link[rel~="apple-touch-icon"], link[rel~="apple-touch-icon-precomposed"], link[rel~="icon"]'))) {
    const href = l.href || '';
    if (!href) continue;
    const g = (l.getAttribute('sizes') || '').match(/(\\d+)x(\\d+)/);
    aus.icons.push({ href: href.slice(0, 2100), apple: /apple-touch-icon/i.test(l.rel), groesse: g ? parseInt(g[1], 10) : 0, typ: (l.type || '').toLowerCase() });
  }
  return aus;
}
"""


def _absolut(adresse: Any, basis_url: str) -> Optional[str]:
    """Nur http(s), keine data:-Adressen, begrenzte Laenge. Sonst None."""
    if not isinstance(adresse, str):
        return None
    adresse = adresse.strip()
    if not adresse or adresse.lower().startswith(("data:", "blob:", "javascript:")):
        return None
    try:
        voll = urljoin(basis_url, adresse)
        teile = urlparse(voll)
    except Exception:
        return None
    if teile.scheme not in ("http", "https") or not teile.netloc:
        return None
    voll = voll.split("#", 1)[0]
    if len(voll) > MAX_LAENGE or re.search(r"[\s\"'<>`]", voll):
        return None
    return voll


def _helligkeit(rgb: Any) -> float:
    try:
        r, g, b = [max(0.0, min(255.0, float(x))) / 255.0 for x in list(rgb)[:3]]
    except Exception:
        return 1.0

    def lin(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _bild_punkte(k: Dict[str, Any], fensterbreite: int) -> int:
    """Wie sicher ist dieses Bild das Logo? Unter 3 Punkten wird es nicht genommen."""
    b, h = int(k.get("b") or 0), int(k.get("h") or 0)
    if b < 24 or h < 12 or b > 520 or h > 260:
        return 0
    kennung = str(k.get("kennung") or "")
    if KEIN_LOGO.search(kennung) and not k.get("logoWort"):
        return 0
    punkte = 0
    if k.get("logoWort"):
        punkte += 3
    if k.get("zurStartseite"):
        punkte += 2
    if k.get("imKopf"):
        punkte += 2
    if int(k.get("y") or 0) <= 160:
        punkte += 1
    if int(k.get("x") or 0) < fensterbreite * 0.6:
        punkte += 1
    return punkte


def bewerte_logokandidaten(kandidaten: Optional[Dict[str, Any]], basis_url: str) -> Optional[Dict[str, Any]]:
    """
    Aus den eingesammelten Kandidaten das Logo waehlen.

    Rueckgabe {url, quelle, grund, gespeichert} oder None.
      quelle:      "kopfbild" | "jsonld" | "apple-touch-icon" | "favicon"
      grund:       "dunkel", wenn das Logo auf dunklem Kopfbereich steht, sonst "hell"
      gespeichert: url mit Kennzeichnung, so wie sie in custom_logo_url landet
    """
    if not isinstance(kandidaten, dict):
        return None
    breite = int(kandidaten.get("breite") or 1280)

    def ergebnis(url: str, quelle: str, dunkel: bool = False) -> Dict[str, Any]:
        return {
            "url": url, "quelle": quelle, "grund": "dunkel" if dunkel else "hell",
            "gespeichert": url + (MARKE_DUNKEL if dunkel else MARKE_AUTO),
        }

    beste, beste_punkte = None, 0
    for k in kandidaten.get("bilder") or []:
        if not isinstance(k, dict):
            continue
        url = _absolut(k.get("src"), basis_url)
        if not url:
            continue
        punkte = _bild_punkte(k, breite)
        # Gleichstand: das hoeher stehende Bild gewinnt (Reihenfolge im Dokument).
        if punkte > beste_punkte:
            beste, beste_punkte = (url, k), punkte
    if beste and beste_punkte >= 3:
        url, k = beste
        return ergebnis(url, "kopfbild", dunkel=_helligkeit(k.get("grund")) < 0.2)

    for adresse in kandidaten.get("jsonld") or []:
        url = _absolut(adresse, basis_url)
        if url:
            return ergebnis(url, "jsonld")

    icons = [i for i in (kandidaten.get("icons") or []) if isinstance(i, dict)]
    apple = sorted((i for i in icons if i.get("apple")), key=lambda i: -int(i.get("groesse") or 0))
    for i in apple:
        url = _absolut(i.get("href"), basis_url)
        if url:
            return ergebnis(url, "apple-touch-icon")

    def icon_rang(i):
        typ, href = str(i.get("typ") or ""), str(i.get("href") or "").lower().split("?")[0]
        vektor = "svg" in typ or href.endswith(".svg")
        png = "png" in typ or href.endswith(".png")
        return (0 if vektor else 1 if png else 2, -int(i.get("groesse") or 0))
    for i in sorted((i for i in icons if not i.get("apple")), key=icon_rang):
        url = _absolut(i.get("href"), basis_url)
        # .ico ist meist 16 px: im Banner unscharf, lieber der Buchstabe.
        if url and not url.lower().split("?")[0].endswith(".ico"):
            return ergebnis(url, "favicon")
    return None


async def logo_aus_seite(page, basis_url: str) -> Optional[Dict[str, Any]]:
    """Kandidaten aus einer geladenen Playwright-Seite ziehen und bewerten. Wirft nie."""
    try:
        from compliance_engine.markenfarben_gerendert import CONSENT_SELEKTOR
        kandidaten = await page.evaluate(LOGO_JS, CONSENT_SELEKTOR)
        return bewerte_logokandidaten(kandidaten, basis_url)
    except Exception as e:
        logger.warning(f"Logo fuer {basis_url} nicht lesbar: {e}")
        return None


def ist_automatisch(gespeichert: Optional[str]) -> bool:
    """Darf der Scan diese gespeicherte Adresse erneuern? Leer oder selbst erkannt: ja."""
    return not gespeichert or MARKE_AUTO in gespeichert


def bereinige_eingabe(wert: Any) -> Optional[str]:
    """Wert aus dem Dashboard fuer custom_logo_url.

    None  -> nichts aendern (das Dashboard schickt das Feld nicht immer mit)
    ""    -> Logo entfernen
    sonst -> gepruefte http(s)-Adresse; Unbrauchbares aendert nichts.
    """
    if wert is None:
        return None
    if not isinstance(wert, str):
        return None
    wert = wert.strip()
    if wert == "":
        return ""
    fragment = ""
    if MARKE_DUNKEL in wert:
        fragment = MARKE_DUNKEL
    elif MARKE_AUTO in wert:
        fragment = MARKE_AUTO
    url = _absolut(wert, wert)
    return (url + fragment) if url else None
