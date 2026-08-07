"""
Die lesbare Fassung des Prüfnachweises.

Eine JSON-Antwort ist ein Beleg für Entwickler. Der Nachweis wird aber an eine
Prüfstelle geschickt, an einen Anwalt, an einen Besucher, der eine Barriere
gemeldet hat. Für die muss er lesbar sein — sonst ist er nur ein Datensatz.

Bewusst eine einzelne, eigenständige Seite ohne Aufbauten: kein
JavaScript-Rahmen, keine Schriften von fremden Servern, kein Analyse-Skript.
Ein Nachweis, der selbst Daten an Dritte abgibt, wäre ein schlechter Witz —
und ein Nachweis über Barrierefreiheit, der selbst nicht barrierefrei ist,
wäre schlimmer. Die Seite hat deshalb `lang`, eine Überschriftenordnung, einen
Sprunglink, echte Tabellenköpfe und Kontraste über 7:1.
"""
import html
from typing import Any, Dict, List


def _e(text: Any) -> str:
    return html.escape(str(text if text is not None else ""))


def _tabelle(kopf: List[str], zeilen: List[List[str]], beschriftung: str) -> str:
    kopfzeilen = "".join(f'<th scope="col">{_e(k)}</th>' for k in kopf)
    koerper = "".join(
        "<tr>" + "".join(f"<td>{z}</td>" for z in zeile) + "</tr>" for zeile in zeilen
    )
    return (
        f"<table><caption>{_e(beschriftung)}</caption>"
        f"<thead><tr>{kopfzeilen}</tr></thead><tbody>{koerper}</tbody></table>"
    )


STIL = """
:root { color-scheme: light dark; }
*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; padding: 2rem 1rem 4rem; font: 16px/1.6 system-ui, -apple-system,
       "Segoe UI", Roboto, sans-serif; color: #1a1a1a; background: #fff; }
main { max-width: 52rem; margin: 0 auto; }
h1 { font-size: 1.6rem; line-height: 1.25; margin: 0 0 .25rem; }
h2 { font-size: 1.15rem; margin: 2.5rem 0 .75rem; padding-top: .75rem;
     border-top: 1px solid #d8d8d8; }
p, li { max-width: 42rem; }
.kopf { color: #444; margin: 0 0 2rem; }
.kennzahl { display: flex; flex-wrap: wrap; gap: 1.5rem; margin: 1.5rem 0;
            padding: 1.25rem; background: #f4f4f5; border-radius: .5rem; }
.kennzahl div { min-width: 8rem; }
.kennzahl b { display: block; font-size: 1.8rem; line-height: 1.1; }
.kennzahl span { color: #444; font-size: .875rem; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: .95rem; }
caption { text-align: left; color: #444; font-size: .875rem; padding-bottom: .5rem; }
th, td { text-align: left; padding: .5rem .75rem; border-bottom: 1px solid #e2e2e2;
         vertical-align: top; }
th { background: #f4f4f5; font-weight: 600; }
td.zahl, th.zahl { text-align: right; font-variant-numeric: tabular-nums; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .9em;
       background: #f0f0f1; padding: .1em .35em; border-radius: .25rem; }
.hinweis { background: #f4f4f5; border-left: 4px solid #6b6b6b; padding: 1rem 1.25rem;
           margin: 1.5rem 0; }
.offen { background: #fdf6e7; border-left: 4px solid #8a6100; }
.fuss { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #d8d8d8;
        color: #444; font-size: .875rem; }
a { color: #0b4f9e; }
a:focus-visible, .sprung:focus { outline: 3px solid #0b4f9e; outline-offset: 2px; }
.sprung { position: absolute; left: -9999px; top: 0; background: #0b4f9e; color: #fff;
          padding: .5rem 1rem; z-index: 10; }
.sprung:focus { left: .5rem; top: .5rem; }
@media (prefers-color-scheme: dark) {
  body { background: #121214; color: #ececee; }
  h2 { border-color: #3a3a3e; }
  .kopf, caption, .fuss, .kennzahl span { color: #b9b9bd; }
  .kennzahl, th, code { background: #1e1e21; }
  th, td { border-color: #34343a; }
  .hinweis { background: #1e1e21; border-color: #7a7a82; }
  .offen { background: #2a2214; border-color: #d3a343; }
  a { color: #8ab8ee; }
}
"""


def nachweis_als_html(n: Dict[str, Any]) -> str:
    """Rendert das Protokoll als eigenständige, barrierefreie Seite."""
    s = n["summe"]
    betrieb = n.get("im_betrieb") or {}

    regel_zeilen = [
        [f"<code>{_e(z['regel'])}</code>",
         f'<span class="zahl">{z["vorher"]}</span>',
         f'<span class="zahl">{z["nachher"]}</span>',
         f'<span class="zahl">{z["behoben"]}</span>']
        for z in n["je_regel"]
    ]

    offen_html = ""
    if n["offen"]:
        punkte = "".join(
            f"<li><strong><code>{_e(o['regel'])}</code></strong> "
            f"({_e(o['fundstellen'])} Fundstellen): {_e(o['grund'])}</li>"
            for o in n["offen"]
        )
        offen_html = (
            '<h2 id="offen">Was nicht behoben wurde</h2>'
            '<div class="hinweis offen"><p>Diese Abweichungen bestehen fort. '
            "Für jede steht hier, warum sie nicht automatisch behoben wurde.</p>"
            f"<ul>{punkte}</ul></div>"
        )
    else:
        offen_html = ('<h2 id="offen">Was nicht behoben wurde</h2>'
                      "<p>In der automatisierten Prüfung sind keine Abweichungen "
                      "offen geblieben.</p>")

    reparaturen = n.get("reparaturen") or []
    rep_html = ""
    if reparaturen:
        rep_html = _tabelle(
            ["Regel", "Änderung", "Ort", "Begründung"],
            [[f"<code>{_e(r['regel'])}</code>", _e(r["was"]),
              f"<code>{_e(r['wo'])}</code>", _e(r["warum"])]
             for r in reparaturen[:60]],
            f"{len(reparaturen)} ausgelieferte Reparaturen"
            + (" (60 gezeigt)" if len(reparaturen) > 60 else ""),
        )

    betrieb_html = ""
    if betrieb.get("seiten_beobachtet"):
        verfehlt = betrieb.get("ziele_verfehlt") or 0
        betrieb_html = (
            '<h2 id="betrieb">Wirksamkeit im Betrieb</h2>'
            "<p>Der Prüflauf oben misst einen Zeitpunkt. Zusätzlich meldet das "
            "eingebundene Element bei <strong>jedem echten Seitenaufruf</strong>, "
            "welche Reparaturen tatsächlich angekommen sind — auf allen "
            "Unterseiten, nicht nur auf der geprüften.</p>"
            '<div class="kennzahl">'
            f"<div><b>{betrieb['seiten_beobachtet']}</b><span>Seiten beobachtet</span></div>"
            f"<div><b>{betrieb['reparaturen_angewendet']}</b><span>Reparaturen angewendet</span></div>"
            f"<div><b>{verfehlt}</b><span>Ziele nicht gefunden</span></div>"
            "</div>"
            f"<p>Zuletzt bestätigt am {_e(betrieb['zuletzt_bestaetigt'])}.</p>"
            + ('<div class="hinweis offen"><p>Bei einigen Reparaturen wurde das '
               "Ziel nicht mehr gefunden. Das deutet auf eine Änderung an der "
               "Website hin (etwa ein Theme-Update) und wird geprüft.</p></div>"
               if verfehlt else "")
        )
    elif betrieb.get("hinweis"):
        betrieb_html = ('<h2 id="betrieb">Wirksamkeit im Betrieb</h2>'
                        f"<p>{_e(betrieb['hinweis'])}</p>")

    bilder = ""
    if n.get("bildbeschreibungen_live"):
        bilder = (
            f"<p><strong>{n['bildbeschreibungen_live']} Bildbeschreibungen</strong> "
            f"sind hinterlegt und freigegeben. Automatische Prüfwerkzeuge erfassen "
            f"diese nicht, weil ein leeres <code>alt</code>-Attribut als gültig gilt.</p>"
        )

    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prüfnachweis Barrierefreiheit — {_e(n['site_url'])}</title>
<meta name="robots" content="noindex">
<style>{STIL}</style>
</head>
<body>
<a class="sprung" href="#inhalt">Zum Inhalt springen</a>
<main id="inhalt">
  <h1>Prüfnachweis Barrierefreiheit</h1>
  <p class="kopf">{_e(n['site_url'])} · Stand {_e(n['gemessen_am'])}</p>

  <div class="kennzahl">
    <div><b>{s['vorher']}</b><span>Abweichungen vorher</span></div>
    <div><b>{s['behoben']}</b><span>davon behoben</span></div>
    <div><b>{s['quote']}&nbsp;%</b><span>Behebungsquote</span></div>
    <div><b>{s['nachher']}</b><span>offen</span></div>
  </div>

  <h2 id="methode">Wie gemessen wurde</h2>
  <p>{_e(n['methode'])}</p>
  <p>Prüfwerkzeug: <code>{_e(n['pruefwerkzeug'])}</code>, Regelsatz
     {_e(n['regelsatz'])}.</p>
  {bilder}

  <h2 id="regeln">Ergebnis je Regel</h2>
  {_tabelle(["Regel", "vorher", "nachher", "behoben"], regel_zeilen,
            "Fundstellen vor und nach der Reparatur")}

  {offen_html}

  <h2 id="reparaturen">Was geändert wurde</h2>
  {rep_html or "<p>Keine Reparaturen ausgeliefert.</p>"}

  {betrieb_html}

  <div class="hinweis">
    <p>{_e(n['hinweis'])}</p>
  </div>

  <p class="fuss">Dieses Protokoll wird aus Messwerten erzeugt und kann jederzeit
  neu erstellt werden. Es ist kein Siegel und bescheinigt keine vollständige
  Konformität — es zeigt, was geprüft wurde, was sich geändert hat und was
  offen ist.</p>
</main>
</body>
</html>"""
