"""
Gemeinsamer Rahmen fuer die Mails, die complyo an Menschen schickt.

Vorlage war eine Terminmail einer Arztpraxis (29.09.2026): helle Flaeche,
darauf weisse Karten mit runden Ecken, oben Logo und eine grosse
Schlagzeile, darunter der Text, ein dunkles Band mit dem einen Knopf, um
den es geht, ein Gruss und eine Kontaktkarte. Die Wartelisten-Mail sah bis
dahin anders aus als alles andere von complyo: blauer Verlauf in
Tailwind-Blau statt Logofarbe, Aufbau mit div und flex, das Outlook nicht
rendert.

Regeln, die hier eingebaut sind und nicht jede Mail neu entscheiden muss:

* Nur Tabellen und Inline-Stile. Outlook kennt weder flex noch grid, Gmail
  wirft <style>-Bloecke teils weg, externe Schriften laedt kein
  Mailprogramm zuverlaessig.
* Akzent #00FFF7 nur als Flaeche mit dunkler Schrift darauf (14,06:1), nie
  als Schrift auf Weiss (1,26:1). Siehe landing-react/tailwind.config.ts.
* Alles, was von aussen kommt (Name, Adresse), geht durch html.escape. Der
  Name kam frei aus dem Formular in die Mail; wer eine fremde Adresse
  eintraegt, haette sonst Links in eine Mail von complyo.de setzen koennen.
* Anbieterangaben wie in landing-react/src/lib/anbieter.ts. Aendert sich
  dort etwas, hier nachziehen (test_mail_layout.py vergleicht beide).
"""

from html import escape

SCHRIFT = ("-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,"
           "Helvetica,Arial,sans-serif")

FLAECHE = "#edf5f6"       # Seitengrund, ein Hauch des Logotons
KARTE = "#ffffff"
BAND = "#111827"          # dunkles Band, gray-900
TEXT = "#111827"          # 17,7:1 auf Weiss
TEXT_LEISE = "#4b5563"    # gray-600, 7,56:1 auf Weiss
TEXT_FUSS = "#5b6b78"     # 4,97:1 auf FLAECHE
AKZENT = "#00fff7"        # nur als Flaeche
AUF_AKZENT = "#111827"
LINK = "#00706c"          # akzent-700, 5,94:1 auf Weiss

LOGO_URL = "https://complyo.de/logo-dark-trim.png"   # 852x287, dunkle Schrift

ANBIETER = {
    "geschaeftsbezeichnung": "Complyo",
    "name": "Yvonne Weishar",
    "strasse": "Pappelallee 64",
    "plz_ort": "10437 Berlin",
    "email": "info@complyo.de",
    "homepage": "complyo.de",
}


def _abstand(px: int) -> str:
    return (f'<tr><td style="height:{px}px;line-height:{px}px;font-size:0;">'
            '&nbsp;</td></tr>')


def karte(inhalt: str, *, dunkel: bool = False, innen: str = "36px 40px") -> str:
    grund = BAND if dunkel else KARTE
    return (
        f'<tr><td bgcolor="{grund}" style="background:{grund};border-radius:14px;'
        f'padding:{innen};font-family:{SCHRIFT};">{inhalt}</td></tr>'
    )


def kopf(kicker: str, schlagzeile: str, unterzeile: str = "") -> str:
    """Logo, darunter die eine Nachricht der Mail, gross."""
    unter = (f'<div style="margin:12px 0 0;color:{TEXT_LEISE};font-size:18px;'
             f'line-height:1.4;">{unterzeile}</div>') if unterzeile else ""
    return karte(
        f'<img src="{LOGO_URL}" width="180" height="61" alt="complyo" '
        'style="display:block;border:0;outline:none;width:180px;height:auto;'
        f'color:{TEXT};font-size:22px;font-weight:700;">'
        f'<div style="margin:36px 0 0;color:{TEXT_LEISE};font-size:16px;">{kicker}</div>'
        f'<div style="margin:10px 0 0;color:{TEXT};font-size:36px;line-height:1.15;'
        f'font-weight:700;word-break:break-word;">{schlagzeile}</div>'
        f'{unter}',
        innen="36px 40px 40px",
    )


def text(*absaetze: str) -> str:
    return karte("".join(
        f'<p style="margin:0 0 16px;color:{TEXT};font-size:16px;line-height:1.6;">{a}</p>'
        for a in absaetze
    ), innen="32px 40px 20px")


def aktion(ueberschrift: str, knopf_text: str, url: str) -> str:
    """Das dunkle Band mit dem einen Knopf. Ohne Ueberschrift nur der Knopf,
    wenn die Schlagzeile oben schon sagt, worum es geht.

    Der Knopf ist eine Tabellenzelle mit Hintergrund plus Link mit Innenabstand
    ("bulletproof"): so bleibt er auch in Outlook eine Flaeche und nicht nur
    ein unterstrichenes Wort.
    """
    kopfzeile = (
        '<tr>'
        f'<td style="padding:6px 0 16px;color:#ffffff;font-family:{SCHRIFT};font-size:20px;'
        f'line-height:1.3;font-weight:700;">{ueberschrift}</td>'
        '</tr>'
    ) if ueberschrift else ""
    return karte(
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
        f'{kopfzeile}<tr><td style="padding:0;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td bgcolor="{AKZENT}" style="background:{AKZENT};border-radius:10px;">'
        f'<a href="{url}" style="display:inline-block;padding:14px 28px;'
        f'font-family:{SCHRIFT};font-size:16px;font-weight:700;color:{AUF_AKZENT};'
        f'text-decoration:none;border-radius:10px;">{knopf_text}</a>'
        '</td></tr></table>'
        '</td></tr></table>',
        dunkel=True, innen="28px 40px 32px",
    )


def angaben(zeilen, titel: str = "") -> str:
    """Bezeichnung links, Wert rechts. Werte kommen maskiert herein."""
    kopfzeile = (f'<div style="color:{TEXT};font-size:20px;font-weight:700;'
                 f'margin:0 0 18px;">{titel}</div>') if titel else ""
    reihen = "".join(
        '<tr>'
        f'<td valign="top" style="padding:0 16px 12px 0;width:40%;color:{TEXT_LEISE};'
        f'font-family:{SCHRIFT};font-size:14px;">{bez}</td>'
        f'<td valign="top" style="padding:0 0 12px;color:{TEXT};font-family:{SCHRIFT};'
        f'font-size:15px;word-break:break-word;">{wert}</td>'
        '</tr>'
        for bez, wert in zeilen
    )
    return karte(
        kopfzeile + '<table role="presentation" width="100%" cellpadding="0" '
        f'cellspacing="0" border="0">{reihen}</table>',
        innen="30px 40px 20px",
    )


def liste(titel: str, punkte) -> str:
    """Aufzaehlung als Tabelle: Outlook setzt Einzuege von <ul> unberechenbar."""
    reihen = "".join(
        '<tr>'
        f'<td valign="top" style="padding:0 10px 10px 0;color:{LINK};font-size:15px;'
        f'font-family:{SCHRIFT};">&#8226;</td>'
        f'<td valign="top" style="padding:0 0 10px;color:{TEXT};font-size:15px;'
        f'line-height:1.5;font-family:{SCHRIFT};">{p}</td>'
        '</tr>'
        for p in punkte
    )
    kopfzeile = (f'<div style="color:{TEXT};font-size:20px;font-weight:700;'
                 f'margin:0 0 16px;">{titel}</div>') if titel else ""
    return karte(
        kopfzeile + '<table role="presentation" cellpadding="0" cellspacing="0" '
        f'border="0">{reihen}</table>',
        innen="30px 40px 22px",
    )


# Randfarbe je Ton. Die Farbe ist nur Rand, die Schrift bleibt TEXT: so
# haengt die Lesbarkeit nie an der Signalfarbe.
_TOENE = {"gefahr": "#b91c1c", "warnung": "#b45309", "info": LINK}


def hinweis(titel: str, inhalt: str, ton: str = "info") -> str:
    rand = _TOENE.get(ton, LINK)
    return karte(
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
        f'<tr><td style="border-left:4px solid {rand};padding:2px 0 2px 18px;'
        f'font-family:{SCHRIFT};">'
        f'<div style="color:{TEXT};font-size:17px;font-weight:700;margin:0 0 8px;">{titel}</div>'
        f'<div style="color:{TEXT};font-size:15px;line-height:1.6;">{inhalt}</div>'
        '</td></tr></table>',
        innen="28px 40px 28px",
    )


def gruss(zeile: str = "vom complyo-Team") -> str:
    return karte(
        f'<div style="color:{TEXT};font-size:20px;font-weight:700;">Beste Grüße</div>'
        f'<div style="margin:12px 0 0;color:{TEXT};font-size:16px;">{zeile}</div>',
        innen="30px 40px 32px",
    )


def kontakt() -> str:
    a = ANBIETER

    def _eintrag(bezeichnung: str, wert: str) -> str:
        return (f'<div style="color:{TEXT_LEISE};font-size:13px;">{bezeichnung}</div>'
                f'<div style="margin:4px 0 18px;color:{TEXT};font-size:16px;line-height:1.5;">{wert}</div>')

    anschrift = (f'{a["geschaeftsbezeichnung"]}<br>{a["name"]}<br>'
                 f'{a["strasse"]}<br>{a["plz_ort"]}')
    return karte(
        f'<div style="color:{TEXT};font-size:20px;font-weight:700;margin:0 0 22px;">Kontakt</div>'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td valign="top" width="50%" style="font-family:{SCHRIFT};padding:0 16px 0 0;">'
        + _eintrag("Anschrift", anschrift) +
        '</td>'
        f'<td valign="top" width="50%" style="font-family:{SCHRIFT};">'
        + _eintrag("E-Mail", f'<a href="mailto:{a["email"]}" style="color:{LINK};'
                             f'text-decoration:none;">{a["email"]}</a>')
        + _eintrag("Homepage", f'<a href="https://{a["homepage"]}" style="color:{LINK};'
                               f'text-decoration:none;">{a["homepage"]}</a>') +
        '</td></tr></table>',
        innen="30px 40px 14px",
    )


def fuss(*zeilen: str) -> str:
    return (
        f'<tr><td style="padding:4px 40px 0;font-family:{SCHRIFT};font-size:13px;'
        f'line-height:1.6;color:{TEXT_FUSS};">'
        + "<br><br>".join(zeilen) +
        '</td></tr>'
    )


def rechtliches() -> str:
    return (f'<a href="https://complyo.de/impressum" style="color:{TEXT_FUSS};">Impressum</a>'
            ' &middot; '
            f'<a href="https://complyo.de/datenschutz" style="color:{TEXT_FUSS};">Datenschutz</a>')


def seite(titel: str, vorschau: str, *bausteine: str) -> str:
    """Setzt die Bausteine untereinander, mit 16px Luft zwischen den Karten.

    `vorschau` ist die Zeile, die Mailprogramme hinter dem Betreff zeigen.
    Ohne sie nehmen sie den ersten Text der Mail, hier also "complyo".
    Titel und Vorschau sind Rohtext und werden hier maskiert: dort landen
    Systemnamen und Nachrichtentitel aus fremden Quellen.
    """
    titel = escape(str(titel))
    vorschau = escape(str(vorschau))
    zwischen = _abstand(16)
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{titel}</title>
</head>
<body style="margin:0;padding:0;background:{FLAECHE};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{FLAECHE};">{vorschau}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       bgcolor="{FLAECHE}" style="background:{FLAECHE};">
  <tr><td align="center" style="padding:32px 12px 40px;">
    <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
           style="width:100%;max-width:600px;">
{zwischen.join(bausteine)}
    </table>
  </td></tr>
</table>
</body>
</html>"""


__all__ = ["seite", "kopf", "text", "aktion", "angaben", "liste", "hinweis",
           "gruss", "kontakt", "fuss", "rechtliches", "karte", "escape", "ANBIETER"]
