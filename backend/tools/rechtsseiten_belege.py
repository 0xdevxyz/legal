#!/usr/bin/env python3
"""
Belege fuer die Rechtsseiten-Erkennung: was steht auf der Seite wirklich?

Der Scanner sucht Impressum und Datenschutzerklaerung ueber Links und Stichworte.
Ob er dabei trifft, laesst sich nur gegen einen Wahrheitsmassstab sagen, und der
muss unabhaengig vom Scanner entstehen. Dieses Werkzeug sammelt dafuer die
Rohbelege, die ein Mensch zum Etikettieren braucht, und benutzt ausdruecklich
NICHTS aus compliance_engine: sonst pruefte der Finder sich an seiner eigenen
Brille.

Je Seite im echten Browser (Playwright, JavaScript ausgefuehrt):
- alle Links, Schaltflaechen und Elemente mit Rechtsbezug (Text, Adresse, onclick,
  Kennung), mit Hinweis ob sichtbar und ob im Fussbereich;
- alle Bereiche (div, section, dialog, aside, article) mit Rechtsbezug in id oder
  class, samt Ueberschriften und Text;
- der sichtbare Text jeder verlinkten Seite derselben Website (bis 6) und jedes
  Anker-Ziels.

Ausgabe: eine JSON-Datei. Sie enthaelt Texte fremder Websites und gehoert nicht ins
Repo. Nur Python-Standardbibliothek plus Playwright.

Aufruf im Backend-Image, Mount auf /src (NICHT /app, sonst verdeckt der Mount die
Playwright-Browser unter /app/.cache):
    python tools/rechtsseiten_belege.py --datei sites.txt --out /out/belege.json
"""
import argparse
import asyncio
import json
import re
import sys
from urllib.parse import urljoin, urlparse

RECHT = re.compile(
    r"impressum|imprint|legal[-_ ]?notice|datenschutz|privacy|dsgvo|gdpr|rechtlich|"
    r"anbieterkennzeichnung|pflichtangaben|haftungsausschluss|cookie", re.I)

# Skript im Browser: sammelt Kandidaten und Bereiche.
SAMMELN = r"""
(rechtSrc) => {
  const RECHT = new RegExp(rechtSrc, 'i');
  const sichtbar = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
  };
  const imFuss = (el) => !!el.closest('footer, [class*=footer], [id*=footer]');
  const kandidaten = [];
  document.querySelectorAll('a, button, [role=button], [onclick], summary, label').forEach((el) => {
    const text = (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80);
    const href = el.getAttribute('href') || '';
    const onclick = (el.getAttribute('onclick') || '').slice(0, 120);
    const aria = (el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('title') || '') +
                 ' ' + (el.getAttribute('aria-controls') || '') + ' ' + (el.getAttribute('data-target') || '');
    const kenn = (el.id || '') + ' ' + (el.className && el.className.toString ? el.className.toString() : '');
    if (!RECHT.test(text + ' ' + href + ' ' + onclick + ' ' + aria) && !RECHT.test(kenn)) return;
    kandidaten.push({
      tag: el.tagName.toLowerCase(), text, href, onclick,
      abs: el.href || '', aria: aria.trim().slice(0, 80), kennung: kenn.trim().slice(0, 80),
      sichtbar: sichtbar(el), fuss: imFuss(el),
    });
  });
  const bereiche = [];
  document.querySelectorAll('div, section, dialog, aside, article, main, details').forEach((el) => {
    const kenn = (el.id || '') + ' ' + (el.className && el.className.toString ? el.className.toString() : '');
    if (!RECHT.test(kenn)) return;
    const text = (el.textContent || '').trim().replace(/\s+/g, ' ');
    if (text.length < 150) return;
    const koepfe = [...el.querySelectorAll('h1,h2,h3,h4')].slice(0, 25)
        .map(h => (h.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80));
    bereiche.push({
      tag: el.tagName.toLowerCase(), id: el.id || '', klasse: (el.className || '').toString().slice(0, 80),
      laenge: text.length, sichtbar: sichtbar(el), koepfe, anfang: text.slice(0, 200),
      text: text.slice(0, 60000),
    });
  });
  return { kandidaten, bereiche, titel: document.title,
           text_laenge: (document.body.innerText || '').length,
           sprache: document.documentElement.lang || '' };
}
"""

ANKERZIEL = r"""
(id) => {
  const el = document.getElementById(id);
  if (!el) return null;
  return { id, tag: el.tagName.toLowerCase(),
           text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60000) };
}
"""


def _host(u: str) -> str:
    h = (urlparse(u).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def _gleich(a: str, b: str) -> bool:
    ha, hb = _host(a), _host(b)
    return bool(ha and hb and (ha == hb or ha.endswith("." + hb) or hb.endswith("." + ha)))


async def eine_seite(pw, url: str, sem: asyncio.Semaphore) -> dict:
    ergebnis = {"url": url}
    async with sem:
        browser = await pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (compatible; complyo-belege)", locale="de-DE")
            page = await ctx.new_page()
            try:
                antwort = await page.goto(url, wait_until="networkidle", timeout=40000)
                ergebnis["status"] = antwort.status if antwort else None
            except Exception as e:
                # networkidle haengt bei Seiten mit Dauerverbindung: nehmen, was da ist
                ergebnis["goto_fehler"] = f"{type(e).__name__}: {str(e)[:120]}"
                try:
                    await page.wait_for_timeout(1500)
                except Exception:
                    pass
            ergebnis["endgueltige_url"] = page.url
            try:
                daten = await page.evaluate(SAMMELN, RECHT.pattern)
            except Exception as e:
                ergebnis["fehler"] = f"Sammeln: {type(e).__name__}: {str(e)[:120]}"
                return ergebnis
            ergebnis.update(daten)

            # Verlinkte Seiten derselben Website lesen, Anker-Ziele auslesen.
            seiten, anker, gesehen = [], [], set()
            for k in daten["kandidaten"]:
                href = (k["href"] or "").strip()
                if not href or href.lower().startswith(("mailto:", "tel:", "javascript:", "sms:")):
                    continue
                if href.startswith("#"):
                    ziel = href[1:]
                    if ziel and ziel not in gesehen:
                        gesehen.add(ziel)
                        try:
                            a = await page.evaluate(ANKERZIEL, ziel)
                        except Exception:
                            a = None
                        anker.append({"ziel": ziel, "inhalt": a})
                    continue
                ziel_url = urljoin(page.url, href).split("#")[0]
                if not _gleich(ziel_url, url) or ziel_url in gesehen or len(seiten) >= 6:
                    continue
                if not RECHT.search(k["text"] + " " + href + " " + k["aria"]):
                    continue
                gesehen.add(ziel_url)
                p2 = await ctx.new_page()
                eintrag = {"url": ziel_url, "link_text": k["text"]}
                try:
                    r = await p2.goto(ziel_url, wait_until="networkidle", timeout=30000)
                    eintrag["status"] = r.status if r else None
                except Exception as e:
                    eintrag["goto_fehler"] = f"{type(e).__name__}: {str(e)[:100]}"
                try:
                    eintrag["endgueltige_url"] = p2.url
                    eintrag["titel"] = await p2.title()
                    eintrag["h1"] = await p2.evaluate(
                        "() => [...document.querySelectorAll('h1')].map(h=>h.textContent.trim()).slice(0,3)")
                    eintrag["text"] = (await p2.evaluate(
                        "() => (document.body.innerText || '')"))[:60000]
                except Exception as e:
                    eintrag["fehler"] = f"{type(e).__name__}: {str(e)[:100]}"
                await p2.close()
                seiten.append(eintrag)
            ergebnis["verlinkte_seiten"] = seiten
            ergebnis["anker_ziele"] = anker
        finally:
            await browser.close()
    return ergebnis


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--parallel", type=int, default=2)
    args = ap.parse_args()
    urls = [z.strip() for z in open(args.datei) if z.strip() and not z.startswith("#")]
    urls = [u if u.startswith("http") else f"https://{u}" for u in urls]

    from playwright.async_api import async_playwright
    sem = asyncio.Semaphore(args.parallel)
    async with async_playwright() as pw:
        res = await asyncio.gather(*(eine_seite(pw, u, sem) for u in urls))
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"seiten": res}, fh, ensure_ascii=False, indent=1)
    for r in res:
        print(f"{'FEHLER' if 'fehler' in r else 'ok':6} {len(r.get('kandidaten', [])):>3} Kandidaten, "
              f"{len(r.get('bereiche', [])):>2} Bereiche, {len(r.get('verlinkte_seiten', [])):>2} Seiten  {r['url']}")


if __name__ == "__main__":
    asyncio.run(main())
