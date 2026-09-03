"""
Themen-SSOT fuer Compliance-Checks.

Warum es das braucht: Der Aehnlichkeits-Waechter in `check_generator` vergleicht
Slug und Titel. Waehlt der Generator fuer dieselbe Pflicht einen anders
gebauten Namen, rutscht das Duplikat durch — so entstanden im Bestand drei
Checks fuer Umweltaussagen (`green-claims-nachweis`,
`green-claims-nachweisseite`, `greenwashing-nachweispflicht-umweltaussagen`),
drei fuer Verpackungsangaben und vier fuer den Abo-Bestellbutton. Deren
Slug-Aehnlichkeit liegt nahe null, das Thema ist identisch.

Ein Thema ist hier die PRAKTISCHE PFLICHT, nicht die Norm. Zwei Richtlinien
koennen dieselbe Massnahme verlangen — fuer den Nutzer ist das eine Aufgabe.
Umgekehrt bleiben Pflichten getrennt, die zufaellig aehnlich klingen: die
Kennzeichnung KI-generierter Inhalte (AI Act Art. 50) ist NICHT die
Kennzeichnung eines Chatbots im Kundenkontakt.

Erkennung: Ein Text gehoert zu einem Thema, wenn er aus JEDER Begriffsgruppe
mindestens einen Treffer enthaelt und keinen der Ausschluss-Begriffe. Dieses
Und-von-Oders ist deutlich treffsicherer als eine flache Stichwortliste.

Die Reihenfolge in THEMEN entscheidet bei Mehrdeutigkeit — spezifische Themen
stehen vor allgemeinen.

GRENZEN, bewusst in Kauf genommen: Manche Themen sind groeber als die Pflichten,
die sie fassen. 'drittlandtransfer-usa' zieht auch den UK-Transfer und den
USA-Hinweis IM COOKIE-BANNER an sich, obwohl das drei getrennte Pflichten sind
(anderes Land, anderer Ort). Genau deshalb fuehrt ein Themen-Treffer im
Generator NICHT zum Verwerfen, sondern nur zu `pending_review`: ein Mensch
entscheidet. Wer die Tabelle verschaerft, darf diese Eigenschaft nicht kippen —
eine harte Sperre wuerde echte neue Pflichten verschlucken.
"""
import re

_UMLAUTE = (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"))


def normalisiere(text: str) -> str:
    """Kleinschreibung, Umlaute aufgeloest, Trennzeichen zu Leerzeichen."""
    text = (text or "").lower()
    for umlaut, ersatz in _UMLAUTE:
        text = text.replace(umlaut, ersatz)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


# thema -> Liste von Begriffsgruppen; aus jeder Gruppe muss etwas vorkommen.
THEMEN: "dict[str, list[tuple[str, ...]]]" = {
    "umweltaussagen-nachweis": [
        ("umwelt", "green", "nachhaltig", "klima", "oeko", "greenwashing"),
        ("nachweis", "beleg", "claims", "verbot", "aussage"),
    ],
    "verpackung-informationen": [
        ("verpackung", "ppwr", "packaging"),
        ("information", "kennzeichnung", "angabe", "hinweis"),
    ],
    "verpackungsregister-lucid": [
        ("lucid", "verpackungsregister", "zentrale stelle"),
        ("registrierung", "nummer", "register"),
    ],
    "preis-30-tage": [
        ("30 tage", "dreissig tage", "referenzpreis", "niedrigster"),
        ("preis", "preisangabe", "preisreduzierung", "rabatt"),
    ],
    "abo-kuendigungsbutton": [
        ("abo", "abonnement", "vertrag"),
        ("kuendigung", "kuendigen", "kuendigungsbutton"),
    ],
    "abo-bestellbutton": [
        ("abo", "abonnement", "subscription"),
        ("button", "bestellbutton", "beschriftung", "schaltflaeche"),
    ],
    "bestellbutton-zahlungspflicht": [
        ("bestellbutton", "button loesung", "button"),
        ("zahlungspflicht", "zahlungspflichtig", "kostenpflichtig"),
    ],
    "barrierefreiheitserklaerung": [
        ("barrierefreiheit", "bfsg", "accessibility"),
        ("erklaerung", "statement"),
    ],
    "cookie-ablehnen-button": [
        ("ablehnen", "ablehnung", "ablehnungsmoeglichkeit", "reject"),
        ("button", "banner", "moeglichkeit", "option", "prominent"),
    ],
    "cookie-wall-alternative": [
        ("cookie wall", "tracking wall", "cookie einwilligung", "cookie ablehnung", "trackingfrei", "tracking free"),
        ("alternative", "zugang", "gleichwertig", "option"),
    ],
    "dsa-meldemechanismus": [
        ("dsa", "rechtswidrige", "illegale"),
        ("melde", "meldemechanismus", "beschwerde", "hinweisgeber"),
    ],
    "dsa-transparenzbericht": [
        ("dsa", "digital services"),
        ("transparenzbericht", "transparency report"),
    ],
    "dsa-werbekennzeichnung": [
        ("dsa", "digital services"),
        ("werbeanzeige", "werbung", "werbe"),
        ("kennzeichnung", "transparenz"),
    ],
    "affiliate-kennzeichnung": [
        ("affiliate", "provisions", "partnerlink"),
        ("kennzeichnung", "werbung", "werbekennzeichnung"),
    ],
    "drittlandtransfer-usa": [
        ("drittland", "drittlandtransfer", "usa", "us dienste"),
        ("datenschutzerklaerung", "dokumentation", "information", "transfer", "rechtsgrundlage"),
    ],
    "chatbot-kennzeichnung": [
        ("chatbot", "virtueller assistent", "virtuellen assistenten", "ki assistent"),
        ("kennzeichnung", "transparenz", "hinweis"),
    ],
    "ki-inhalte-kennzeichnung": [
        ("ki generiert", "ai generated", "generierter inhalt", "generierte inhalte"),
        ("kennzeichnung", "label", "hinweis"),
    ],
    "analytics-widerspruch": [
        ("analytics", "web analyse", "webanalyse", "reichweitenmessung"),
        ("opt out", "widerspruch", "widerspruchsrecht", "abmeldung"),
    ],
    "newsletter-double-opt-in": [
        ("newsletter", "anmeldeformular"),
        ("double opt in", "doppelte einwilligung", "bestaetigungsmail"),
    ],
    "newsletter-abmeldung": [
        ("newsletter", "mailing"),
        ("abmeldung", "abmelden", "unsubscribe", "austragen"),
    ],
    "consent-mode": [
        ("google consent mode", "consent mode"),
        ("implementierung", "v2", "nicht implementiert", "fehlt"),
    ],
}


# thema -> Begriffe, die das Thema ausschliessen. Ohne diese griff
# 'abo-bestellbutton' auch bei `abo-kuendigung-button` — "abo" + "button"
# passte, obwohl ein Kuendigungsbutton das Gegenteil eines Bestellbuttons ist.
AUSSCHLUESSE: "dict[str, tuple[str, ...]]" = {
    "abo-bestellbutton": ("kuendigung", "kuendigen", "widerruf"),
    "bestellbutton-zahlungspflicht": ("abo", "abonnement", "kuendigung"),
    "cookie-wall-alternative": ("ablehnen button", "reject button", "ablehnungsoption"),
    "ki-inhalte-kennzeichnung": ("chatbot", "assistent"),
    "newsletter-abmeldung": ("double opt in",),
    "dsa-werbekennzeichnung": ("affiliate",),
}


def erkenne_thema(*texte: str) -> "str | None":
    """
    Liefert das Thema, zu dem die uebergebenen Texte gehoeren — oder None.

    Uebergeben wird ueblicherweise Slug UND Titel: der Slug traegt die
    Fachbegriffe, der Titel die Formulierung. Bei Mehrdeutigkeit gewinnt das
    Thema, das in THEMEN weiter oben steht.
    """
    text = " ".join(normalisiere(t) for t in texte if t)
    if not text:
        return None
    for thema, gruppen in THEMEN.items():
        if any(sperre in text for sperre in AUSSCHLUESSE.get(thema, ())):
            continue
        if all(any(begriff in text for begriff in gruppe) for gruppe in gruppen):
            return thema
    return None
