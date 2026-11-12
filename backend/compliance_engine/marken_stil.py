"""
Schrift und Ecken der Website fuer den Cookie-Banner.

Der Banner uebernimmt Farben und Logo schon aus der Website; hier kommen die
Schrift des Fliesstextes und der Eckenradius des Hauptknopfs dazu. Gemessen wird
im selben Browser-Durchlauf wie die Markenfarben (markenfarben_gerendert.py).

Schrift
    Der Banner laeuft auf der Seite des Kunden und erbt deren @font-face. Eine
    Webfont der Seite wird also nicht nachgeladen, der Besucher hat sie ohnehin.
    Das ist der Grund, warum nur die Schrift der Seite selbst uebernommen wird und
    nie eine, die wir von irgendwoher holen muessten (das braeuchte eine eigene
    Einwilligung). Der Name landet in einem <style>: nur Buchstaben, Ziffern,
    Leerzeichen und Bindestrich, nie Klammern, Semikolon, Schraegstrich.
    Symbolschriften (Font Awesome, Dashicons ...) sind nie die Textschrift.

Ecken
    Radius der sichtbaren Knoepfe mit eigener Hintergrundfarbe; der haeufigste
    Wert gewinnt. Ein Radius von mindestens der halben Knopfhoehe ist eine
    Pille (100).

Die Bewertung (bewerte_stilproben) ist reines Python und ohne Browser testbar.
"""
import logging
import re
from collections import Counter
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PILLE = 100
RADIUS_MAX = 24
MAX_SCHRIFTNAMEN = 4
MAX_LAENGE = 200

GENERISCH = ("serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
             "ui-sans-serif", "ui-serif", "ui-monospace", "ui-rounded")

# Schriften, die Symbole statt Text zeichnen. Auf einem Fliesstext-Element stehen
# sie, wenn ein Theme die Schrift fehlerhaft vererbt; als Bannerschrift waeren sie
# unlesbar.
SYMBOLSCHRIFT = re.compile(
    r"awesome|dashicons|eicons?|glyphicons?|icomoon|ionicons?|material[ -]?(icons|symbols)|"
    r"swiper-icons|themify|linearicons|feather|elegant ?icons|^fa$|^fa[srlbd]?$|ui-icons|"
    r"wp-?icons|genericons|entypo|typicons|simple-line|slick|bootstrap-icons|lucide|"
    r"emoji|symbol|dingbats|wingdings|webdings",
    re.IGNORECASE,
)
NAME_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 \-_]{0,58}$")
SYSTEMSCHRIFT_ANFANG = re.compile(r"^-apple-system$|^BlinkMacSystemFont$", re.IGNORECASE)

STIL_JS = """
(consentSelektor) => {
  const vh = window.innerHeight || 900;
  const grenze = vh * 2;
  const sichtbar = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0 || r.top > grenze || r.bottom < 0) return null;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) === 0) return null;
    return { r, cs };
  };
  const imConsent = (el) => {
    try {
      const c = el.closest(consentSelektor);
      return !!c && c !== document.documentElement && c !== document.body;
    } catch (e) { return false; }
  };
  let schrift = null;
  for (const el of document.querySelectorAll('main p, article p, p, li')) {
    if (imConsent(el)) continue;
    const s = sichtbar(el);
    if (!s) continue;
    if ((el.textContent || '').trim().length < 40) continue;
    schrift = s.cs.fontFamily;
    break;
  }
  if (!schrift) schrift = getComputedStyle(document.body).fontFamily;
  const knoepfe = [];
  let n = 0;
  const auswahl = 'button, [role="button"], input[type="submit"], a.btn, a.button, .btn, .button, '
    + '.wp-block-button__link, .elementor-button, a[class*="btn"], a[class*="button"], .cta, [class*="cta"]';
  for (const el of document.querySelectorAll(auswahl)) {
    if (n >= 60) break;
    if (imConsent(el)) continue;
    const s = sichtbar(el);
    if (!s) continue;
    const bg = s.cs.backgroundColor;
    if (!bg || bg === 'transparent' || bg === 'rgba(0, 0, 0, 0)') continue;
    if (s.r.height < 24 || s.r.height > 90 || s.r.width < 48) continue;
    n++;
    knoepfe.push({ radius: s.cs.borderTopLeftRadius, hoehe: s.r.height });
  }
  return { schrift, knoepfe };
}
"""


def _eintrag_sauber(name: str) -> Optional[str]:
    n = (name or "").strip().strip("'\"").strip()
    if not n:
        return None
    if n.lower() in GENERISCH:
        return n.lower()
    if not NAME_OK.match(n):
        return None
    if SYMBOLSCHRIFT.search(n):
        return None
    return n


def bereinige_schrift(familie: Any) -> Optional[str]:
    """Aus dem computed font-family einen Wert machen, der gefahrlos in ein <style> darf.

    None, wenn kein brauchbarer Name uebrig bleibt oder nur Systemschriften da sind
    (dann aendert sich am Banner nichts, also auch nichts ablegen).
    """
    if not isinstance(familie, str) or not familie.strip():
        return None
    namen: List[str] = []
    generisch: List[str] = []
    for teil in familie.split(","):
        e = _eintrag_sauber(teil)
        if e is None:
            continue
        if e in GENERISCH:
            if e not in generisch:
                generisch.append(e)
        elif e not in namen:
            namen.append(e)
    echte = [n for n in namen if not SYSTEMSCHRIFT_ANFANG.match(n)]
    if not echte:
        return None
    namen = namen[:MAX_SCHRIFTNAMEN]
    teile = [f'"{n}"' if " " in n else n for n in namen] + (generisch or ["sans-serif"])
    wert = ", ".join(teile)
    return wert if len(wert) <= MAX_LAENGE else None


def _radius_px(roh: Any, hoehe: float) -> Optional[int]:
    """Radius aus getComputedStyle (px oder %) in ganze Pixel, Pille als PILLE."""
    s = str(roh or "").strip().split(" ")[0]
    m = re.match(r"^([0-9.]+)(px|%)?$", s)
    if not m:
        return None
    wert = float(m.group(1))
    if m.group(2) == "%":
        return PILLE if wert >= 40 else int(round(min(wert / 100 * hoehe, RADIUS_MAX)))
    if hoehe > 0 and wert >= hoehe / 2 - 1:
        return PILLE
    return int(min(round(wert), RADIUS_MAX))


def bewerte_radien(knoepfe: Any) -> Optional[int]:
    """Haeufigster Eckenradius der Knoepfe; bei Gleichstand der kleinere."""
    zaehler: Counter = Counter()
    for k in knoepfe or []:
        if not isinstance(k, dict):
            continue
        try:
            r = _radius_px(k.get("radius"), float(k.get("hoehe") or 0))
        except (TypeError, ValueError):
            continue
        if r is not None:
            zaehler[r] += 1
    if not zaehler:
        return None
    hoechste = max(zaehler.values())
    return min(r for r, n in zaehler.items() if n == hoechste)


def bewerte_stilproben(proben: Any) -> Optional[Dict[str, Any]]:
    """{'schrift': str|None, 'radius': int|None} oder None, wenn nichts Brauchbares da ist."""
    if not isinstance(proben, dict):
        return None
    schrift = bereinige_schrift(proben.get("schrift"))
    radius = bewerte_radien(proben.get("knoepfe"))
    if schrift is None and radius is None:
        return None
    return {"schrift": schrift, "radius": radius}


async def stil_aus_seite(page) -> Optional[Dict[str, Any]]:
    """Proben aus einer geladenen Playwright-Seite ziehen und bewerten. Wirft nie."""
    try:
        from compliance_engine.markenfarben_gerendert import CONSENT_SELEKTOR
        proben = await page.evaluate(STIL_JS, CONSENT_SELEKTOR)
        return bewerte_stilproben(proben)
    except Exception as e:
        logger.warning(f"Schrift und Ecken nicht lesbar: {e}")
        return None
