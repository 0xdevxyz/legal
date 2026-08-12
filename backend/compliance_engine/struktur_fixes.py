"""
Struktur-Reparaturen, die sich im Browser selbst prüfen.

Was hier drin ist und warum genau das
-------------------------------------
Die Auswahl kommt aus der Messung über 24 echte deutsche KMU-Websites
(06.08.2026), nicht aus der WCAG-Gliederung. Nach Kontrast (192) und
Link-Namen (57) bleiben diese Posten übrig:

    region                        331   auf 83 % der Seiten
    landmark-one-main              12   auf 50 %
    meta-viewport                   7   Pflicht, trivial behebbar
    link-in-text-block              3   Pflicht (1.4.1)
    scrollable-region-focusable     1   Pflicht (2.1.1)
    frame-title                     1   Pflicht (4.1.2)

`region` allein ist damit der grösste Einzelposten des ganzen Bestands.

Warum das Ziel gemessen und nicht geraten wird
----------------------------------------------
Der bisherige Weg riet zur Laufzeit mit einer festen Selektorliste
(`main, [role="main"], #content, #content-main, #primary`). Im echten Bestand
heissen die Inhalts-Container aber `.wrapper`, `#main`, `#Content`,
`#Wrapper`, `.content` — die Liste trifft die wenigsten. Ein `role="main"` an
der falschen Stelle ist schlimmer als keins: es behauptet eine Struktur, die
nicht stimmt, und der Sprunglink landet im Nirgendwo.

axe weiss dagegen genau, welche Knoten ausserhalb jeder Landmark liegen. Aus
denen laesst sich der gemeinsame Vorfahr bestimmen — das ist der Container, um
den es geht. Dieses Modul bestimmt ihn im Browser, setzt `role="main"`, misst
erneut und liefert nur aus, was die Nachmessung bestanden hat.

Nicht enthalten und warum
-------------------------
`nested-interactive` (9 Fundstellen): ein Link in einem Button ist ein
Strukturfehler, dessen Auflösung Inhalt umbaut. `heading-order` und
`page-has-heading-one`: welche Zeile die H1 ist, ist eine redaktionelle
Entscheidung. `aria-required-parent`: die fehlende Rolle haengt am Bauplan des
Bedienelements. Alle drei brauchen ein Urteil, das Mechanik nicht hat.
"""
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Bekannte Einbettungen — der Titel eines iframes muss sagen, was drin ist.
_IFRAME_QUELLEN = [
    (r"google\.[a-z.]+/maps|maps\.google", "Karte von Google Maps"),
    (r"openstreetmap\.org", "Karte von OpenStreetMap"),
    (r"youtube\.com|youtu\.be", "Video von YouTube"),
    (r"vimeo\.com", "Video von Vimeo"),
    (r"spotify\.com", "Player von Spotify"),
    (r"soundcloud\.com", "Player von SoundCloud"),
    (r"facebook\.com", "Inhalt von Facebook"),
    (r"instagram\.com", "Inhalt von Instagram"),
    (r"recaptcha|hcaptcha", "Sicherheitsabfrage"),
    (r"calendly\.com|terminland|doctolib", "Terminbuchung"),
]


def iframe_titel(src: str) -> Optional[str]:
    """Sagt der Titel, was in der Einbettung steckt?

    Ohne erkennbare Quelle wird nichts erfunden: "Eingebetteter Inhalt" waere
    formal ein Titel und fuer einen Screenreader-Nutzer wertlos.
    """
    if not src:
        return None
    for muster, titel in _IFRAME_QUELLEN:
        if re.search(muster, src, re.I):
            return titel
    host = (urlparse(src).netloc or "").lower().removeprefix("www.")
    return f"Eingebetteter Inhalt von {host}" if host else None


def viewport_reparieren(inhalt: str) -> Optional[str]:
    """
    Entfernt Sperren gegen das Zoomen aus dem viewport-Meta.

    `user-scalable=no` und ein `maximum-scale` unter 2 verhindern, dass jemand
    die Seite vergroessern kann — WCAG 1.4.4 verlangt 200 %. Auf 7 der 24
    gemessenen Seiten stand genau das drin, meist als Altlast aus einer
    Theme-Vorlage. Der Fix nimmt nur die Sperren heraus und laesst den Rest
    (`width`, `initial-scale`) unangetastet.

    Returns:
        Den bereinigten Wert, oder None wenn nichts zu tun ist.
    """
    if not inhalt:
        return None
    teile = [t.strip() for t in inhalt.split(",") if t.strip()]
    behalten: List[str] = []
    geaendert = False
    for teil in teile:
        name, _, wert = teil.partition("=")
        name, wert = name.strip().lower(), wert.strip().lower()
        if name == "user-scalable" and wert in ("no", "0"):
            geaendert = True
            continue
        if name == "maximum-scale":
            try:
                if float(wert) < 2.0:
                    geaendert = True
                    continue
            except ValueError:
                geaendert = True
                continue
        behalten.append(teil)
    return ", ".join(behalten) if geaendert else None


# =============================================================================
# Browser-Logik
# =============================================================================
#
# Als JavaScript, weil die Entscheidungen den gerenderten Baum brauchen: welcher
# Container die bemängelten Knoten umschliesst, ob er in einer Landmark liegt,
# wie viel Text darin steht. Aus Python heraus liesse sich das nur raten.

HAUPTINHALT_JS = r"""
() => {
  // Der gemeinsame Vorfahr aller Knoten, die axe als "ausserhalb jeder
  // Landmark" gemeldet hat. Das IST der Hauptinhalts-Container — er muss
  // nicht erraten werden.
  const knoten = window.__complyoRegionKnoten || [];
  const elemente = [];
  for (const sel of knoten) {
    try { const el = document.querySelector(sel); if (el) elemente.push(el); }
    catch (e) { /* Selektor aus fremdem Markup — ueberspringen */ }
  }
  if (!elemente.length) return null;

  const kette = (el) => { const k = []; while (el) { k.unshift(el); el = el.parentElement; } return k; };
  let gemeinsam = kette(elemente[0]);
  for (const el of elemente.slice(1)) {
    const k = kette(el);
    let i = 0;
    while (i < gemeinsam.length && i < k.length && gemeinsam[i] === k[i]) i++;
    gemeinsam = gemeinsam.slice(0, i);
  }
  let ziel = gemeinsam[gemeinsam.length - 1];
  if (!ziel) return null;

  // Namen, die einen Container als Kopf-, Fuss- oder Navigationsbereich
  // ausweisen. Ein `role="main"` darauf waere schlimmer als keins: es faellt
  // niemandem auf und behauptet trotzdem eine falsche Struktur. Im ersten
  // Messlauf ist genau das passiert — auf naturheilpraxis-decker.de landete
  // die Rolle auf `elementor-location-header`.
  const NICHT_MAIN = /(^|[-_ ])(header|footer|nav|navigation|topbar|menu|sidebar|widget|cookie|banner)([-_ ]|$)/i;
  const istRandbereich = (el) =>
    ['HEADER', 'NAV', 'FOOTER', 'ASIDE'].includes(el.tagName) ||
    NICHT_MAIN.test(el.id || '') ||
    NICHT_MAIN.test((el.className || '').toString());

  // <body> und <html> taugen nicht als main: dann waere die ganze Seite
  // Hauptinhalt, samt Kopf- und Fusszeile. Stattdessen das Kind von body mit
  // den meisten bemaengelten Knoten — Randbereiche ausgenommen.
  if (ziel === document.body || ziel === document.documentElement) {
    let bestes = null, meiste = 0;
    for (const kind of document.body.children) {
      if (istRandbereich(kind)) continue;
      const n = elemente.filter((e) => kind.contains(e)).length;
      if (n > meiste) { meiste = n; bestes = kind; }
    }
    ziel = bestes;
  }
  if (!ziel || ziel === document.body) return null;

  // Nichts anfassen, was schon eine Rolle oder eine Landmark ist.
  const verboten = ['HEADER', 'NAV', 'FOOTER', 'ASIDE', 'MAIN'];
  while (ziel && (verboten.includes(ziel.tagName) || ziel.getAttribute('role'))) {
    ziel = ziel.parentElement;
    if (!ziel || ziel === document.body) return null;
  }
  if (istRandbereich(ziel)) return null;

  // Der Container muss die MEHRHEIT der bemaengelten Knoten umschliessen.
  // Sonst ist es ein einzelner Abschnitt und nicht der Hauptinhalt — im
  // ersten Messlauf wurden so `#reviews`, `#kontakt` und `#behandlung`
  // gewaehlt, jeweils ein Abschnitt unter vielen.
  const drin = elemente.filter((e) => ziel.contains(e)).length;
  if (drin * 2 < elemente.length) return null;

  // Einen stabilen Selektor bilden. Vorhandene id gewinnt; sonst wird eine
  // vergeben, damit auch der Sprunglink ein Ziel hat.
  if (ziel.id) return '#' + CSS.escape(ziel.id);
  const klassen = (ziel.className || '').toString().trim().split(/\s+/).filter(Boolean);
  if (klassen.length) {
    const sel = ziel.tagName.toLowerCase() + '.' + klassen.map(CSS.escape).join('.');
    try { if (document.querySelectorAll(sel).length === 1) return sel; } catch (e) {}
  }
  ziel.id = 'complyo-main';
  return '#complyo-main';
}
"""

# Seitenstabile Alternativ-Selektoren fuer den bereits bestimmten Container.
# Hintergrund (Audit 11.08.): der exakte Selektor traegt bei Elementor die
# Post-ID der gemessenen Seite (z.B. `div.elementor.elementor-12735`) und
# trifft auf jeder Unterseite nichts — angewendet=0 bei konstantem verfehlt.
# Die Alternativen werden HIER, auf der gemessenen Seite, auf Eindeutigkeit
# verifiziert; das Widget prueft sie zur Laufzeit erneut (genau ein Treffer,
# kein Randbereich, keine vorhandene main-Landmark). Gemessen, nicht geraten.
ALTERNATIVEN_JS = r"""
(exakt) => {
  let ziel = null;
  try { ziel = document.querySelector(exakt); } catch (e) { return []; }
  if (!ziel) return [];

  const alternativen = [];
  const eindeutig = (sel) => {
    try { const t = document.querySelectorAll(sel); return t.length === 1 && t[0] === ziel; }
    catch (e) { return false; }
  };

  // 1) Elementor markiert den Seiten-Wrapper mit data-elementor-type
  //    (wp-page/single/...). Der Attributwert ist ueber Unterseiten
  //    desselben Typs stabil, die Post-ID-Klasse nicht.
  const eltyp = ziel.getAttribute('data-elementor-type');
  if (eltyp) {
    const sel = 'div[data-elementor-type="' + CSS.escape(eltyp) + '"]';
    if (eindeutig(sel)) alternativen.push(sel);
  }

  // 2) Klassenkette ohne volatile ID-Klassen (elementor-123, post-456,
  //    page-id-789 ...). Bleibt etwas uebrig und ist es eindeutig, ist es
  //    ein stabiler Kandidat.
  const VOLATIL = /^(elementor|postid|post|page-id|page)-\d+$/;
  const klassen = (ziel.className || '').toString().trim().split(/\s+/)
    .filter(Boolean).filter((k) => !VOLATIL.test(k));
  if (klassen.length) {
    const sel = ziel.tagName.toLowerCase() + '.' + klassen.map(CSS.escape).join('.');
    if (sel !== exakt && eindeutig(sel)) alternativen.push(sel);
  }

  return alternativen.filter((s) => s !== exakt);
}
"""

STRUKTUR_ANWENDEN_JS = r"""
(fixes) => {
  // Guarded wie ueberall: nur setzen, wo nichts steht.
  let gesetzt = 0;
  for (const f of fixes) {
    // Ein fehlender <title> existiert nicht — er wird angelegt.
    if (f.attribut === '__text__' && f.selector === 'title' &&
        !document.querySelector('title')) {
      const t = document.createElement('title');
      document.head.appendChild(t);
    }
    let ziele = [];
    try { ziele = Array.from(document.querySelectorAll(f.selector)); }
    catch (e) { continue; }
    for (const el of ziele) {
      if (f.attribut === '__text__') {
        // <title> traegt keinen Attributwert, sondern Text.
        el.textContent = f.wert; gesetzt++;
      } else if (f.attribut === 'content' && el.tagName === 'META') {
        el.setAttribute('content', f.wert); gesetzt++;
      } else if (!el.hasAttribute(f.attribut) || !el.getAttribute(f.attribut)) {
        el.setAttribute(f.attribut, f.wert); gesetzt++;
      }
    }
  }
  return gesetzt;
}
"""


def baue_struktur_fixes(befunde: Dict[str, List[Dict[str, Any]]],
                        haupt_selektor: Optional[str],
                        haupt_alternativen: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Aus axe-Fundstellen werden Attribut-Setzungen.

    Args:
        befunde: {regel_id: [node, ...]} der betroffenen Regeln.
        haupt_selektor: gemessener Container fuer role="main", oder None.
        haupt_alternativen: seitenstabile, auf der gemessenen Seite auf
            Eindeutigkeit verifizierte Alternativ-Selektoren desselben
            Containers (ALTERNATIVEN_JS). Der exakte Selektor traegt oft die
            Elementor-Post-ID der gemessenen Seite und trifft auf Unterseiten
            nichts — die Alternativen geben dem Widget dort ein Ziel.

    Returns:
        Liste von {selector, attribut, wert, regel, begruendung[, alternativen]}
        — genau das Format, das der Laufzeit-Kanal guarded anwenden kann.
    """
    fixes: List[Dict[str, Any]] = []

    if haupt_selektor:
        haupt_fix: Dict[str, Any] = {
            "selector": haupt_selektor,
            "attribut": "role",
            "wert": "main",
            "regel": "region",
            "begruendung": (
                "Inhalt ausserhalb jeder Landmark — der Container wurde aus den "
                "bemaengelten Knoten bestimmt, nicht geraten."
            ),
        }
        if haupt_alternativen:
            haupt_fix["alternativen"] = haupt_alternativen
        fixes.append(haupt_fix)

    for node in befunde.get("meta-viewport", []):
        html = node.get("html") or ""
        m = re.search(r"""content\s*=\s*["']([^"']*)["']""", html, re.I)
        neu = viewport_reparieren(m.group(1)) if m else None
        if neu:
            fixes.append({
                "selector": "meta[name=viewport]",
                "attribut": "content",
                "wert": neu,
                "regel": "meta-viewport",
                "begruendung": "Zoom war gesperrt (WCAG 1.4.4 verlangt 200 %).",
            })

    for node in befunde.get("frame-title", []):
        sel = (node.get("target") or [None])[0]
        html = node.get("html") or ""
        m = re.search(r"""src\s*=\s*["']([^"']*)["']""", html, re.I)
        titel = iframe_titel(m.group(1)) if m else None
        if sel and titel:
            fixes.append({
                "selector": sel, "attribut": "title", "wert": titel,
                "regel": "frame-title",
                "begruendung": "Einbettung ohne Titel — abgeleitet aus der Quelle.",
            })

    for node in befunde.get("scrollable-region-focusable", []):
        sel = (node.get("target") or [None])[0]
        if sel:
            fixes.append({
                "selector": sel, "attribut": "tabindex", "wert": "0",
                "regel": "scrollable-region-focusable",
                "begruendung": "Scrollbereich war per Tastatur nicht erreichbar.",
            })

    return fixes


def baue_struktur_css(befunde: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    """CSS-Anteil der Struktur-Reparatur (Format des Fix-Manifests)."""
    regeln: List[Dict[str, str]] = []
    for node in befunde.get("link-in-text-block", []):
        sel = (node.get("target") or [None])[0]
        if sel:
            # WCAG 1.4.1: Links im Fliesstext duerfen sich nicht allein durch
            # Farbe abheben. Unterstreichen ist die kleinste Aenderung, die das
            # loest — und die einzige, die ohne Kenntnis des Designs sicher ist.
            regeln.append({
                "selector": sel,
                "declarations": "text-decoration: underline !important;",
            })
    return regeln
