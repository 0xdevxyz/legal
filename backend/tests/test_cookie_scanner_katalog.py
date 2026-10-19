"""
Wächter: Der HTML-Scanner darf nichts erkennen, was der Dienstekatalog nicht kennt.

Anlass (19.10.2026, spedition-mahn.de): DETECTION_PATTERNS kannte 'wordpress',
'woocommerce', 'shopify' usw., cookie_services hatte dazu keine Zeile. Der Scan
speichert nur Katalogtreffer, also blieb services = [] und das Banner zeigte
"Keine Services in dieser Kategorie", obwohl WordPress Cookies setzt und
Emoji-Grafiken von s.w.org (Automattic, USA) nachlädt.

Der Katalog wird aus den SQL-Seeds im Repo gelesen (kein Datenbankzugriff);
der Live-Katalog hatte am 19.10.2026 dieselben 217 Schlüssel wie die Seeds.
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cookie_scanner_service import CookieScanner  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
import glob

# Alle SQL-Seeds, die cookie_services befüllen (Archiv-Migrationen und data/).
SEEDS = sorted(
    glob.glob(os.path.join(REPO, 'backend', '_archive_pre_baseline', '*.sql'))
    + glob.glob(os.path.join(REPO, 'backend', 'migrations', '_archive_pre_baseline', '*.sql'))
    + glob.glob(os.path.join(REPO, 'data', '*', '*.sql'))
)

# Erkennungen ohne Einwilligungsbezug: setzen keine Cookies und laden nichts von
# Dritten. Sie bleiben im Scanner (Hinweis für den Betreiber), gehören aber nicht
# ins Banner. Wer hier etwas einträgt, begründet es in einem Kommentar.
OHNE_KATALOG_ERLAUBT = {
    'elementor',   # Page-Builder, nur lokaler Speicher für die Darstellung
    'yoast_seo',   # Metadaten im HTML, keine Besucherdaten
}


def _katalog_schluessel():
    assert SEEDS, "keine SQL-Seeds gefunden"
    keys = set()
    for pfad in SEEDS:
        text = open(pfad, encoding='utf-8').read()
        keys.update(re.findall(r"^\s*\('([a-z0-9_]+)',", text, re.M))
    return keys


def test_jeder_scanner_schluessel_hat_katalogeintrag():
    katalog = _katalog_schluessel()
    fehlen = sorted(
        k for k in CookieScanner.DETECTION_PATTERNS
        if k not in katalog and k not in OHNE_KATALOG_ERLAUBT
    )
    assert not fehlen, (
        "Scanner erkennt Dienste, die cookie_services nicht kennt; der Scan "
        f"verwirft sie still und das Banner bleibt leer: {fehlen}"
    )


def test_erlaubnisliste_nur_fuer_echte_scanner_schluessel():
    unbekannt = OHNE_KATALOG_ERLAUBT - set(CookieScanner.DETECTION_PATTERNS)
    assert not unbekannt, f"Erlaubnisliste nennt Schlüssel, die der Scanner nicht hat: {unbekannt}"


WORDPRESS_SEITE = """
<!DOCTYPE html><html lang="de"><head>
<link rel='stylesheet' href='https://spedition-mahn.de/wp-content/themes/logistica/style.css?ver=7.1.3' />
<script src="https://spedition-mahn.de/wp-includes/js/jquery/jquery.min.js?ver=3.7.1"></script>
<link rel="https://api.w.org/" href="https://spedition-mahn.de/wp-json/" />
<script>window._wpemojiSettings = {"baseUrl":"https:\\/\\/s.w.org\\/images\\/core\\/emoji\\/17.0.2\\/72x72\\/","ext":".png","svgUrl":"https:\\/\\/s.w.org\\/images\\/core\\/emoji\\/17.0.2\\/svg\\/"};</script>
</head><body><p>Spezial- und Maschinentransporte</p></body></html>
"""

KOMMENTARSEITE = WORDPRESS_SEITE.replace(
    '<body>',
    '<body><img alt="" src="https://secure.gravatar.com/avatar/3b3be63a4c2a439b013787725dfce802?s=56&d=mm&r=g" class="avatar" />',
)


def _erkenne(html):
    scanner = CookieScanner()
    ergebnis = scanner._detect_services(html, [], [], [], [])
    return ergebnis['services'], ergebnis['confidence']


def test_wordpress_seite_erkennt_wordpress_und_emoji_cdn():
    services, confidence = _erkenne(WORDPRESS_SEITE)
    assert 'wordpress' in services
    assert 'wordpress_emojis' in services
    assert confidence['wordpress_emojis'] >= 0.75, "zwei Muster (Settings und s.w.org) müssen greifen"
    assert 'gravatar' not in services, "ohne Avatar-Bild kein Gravatar-Treffer"


def test_kommentarseite_erkennt_gravatar():
    services, _ = _erkenne(KOMMENTARSEITE)
    assert 'gravatar' in services


def test_seite_ohne_wordpress_bleibt_frei():
    services, _ = _erkenne("<html><body><h1>Statische Seite</h1></body></html>")
    assert not {'wordpress', 'wordpress_emojis', 'gravatar'} & services
