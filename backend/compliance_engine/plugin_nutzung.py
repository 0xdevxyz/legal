"""
Nutzungsnachweis fuer Plugins, deren Dateien auf jeder Seite liegen.

Befund 21.10.2026 (rru-chemnitz.de): der Cookie-Scan meldete WooCommerce,
die Seite hat aber keinen Shop. WooCommerce haengt sein CSS, sein JavaScript
und die Body-Klasse ``woocommerce-no-js`` an jede Seite, sobald das Plugin
aktiv ist; das Muster ``woocommerce`` traf also auf jede WordPress-Seite mit
installiertem Plugin, ob sie verkauft oder nicht.

Cookies setzt WooCommerce erst, wenn Shop-Funktion benutzt wird
(``woocommerce_items_in_cart`` und ``wp_woocommerce_session_*`` beim Legen in
den Warenkorb, ``woocommerce_recently_viewed`` auf Produktseiten). Ohne
Produkte, Warenkorb oder Kasse bekommt kein Besucher einen WooCommerce-Cookie.
Ein Banner, das den Dienst trotzdem nennt, behauptet eine Verarbeitung, die
nicht stattfindet; das ist keine Einwilligungsfrage (die Cookies sind
technisch notwendig, § 25 Abs. 2 Nr. 2 TDDDG), aber eine falsche Angabe
gegenueber dem Besucher und in der Datenschutzerklaerung.

Deshalb: "installiert" reicht nicht, der Scan braucht einen Nachweis, dass
die Funktion auf der Seite in Gebrauch ist. Fehlt er, bleibt der Dienst aus
dem Banner und wird dem Betreiber als "installiert, nicht genutzt" gezeigt.
"""
import re
from typing import Dict, List, Optional

# Je Dienst eine Liste von Nachweisen; einer genuegt. Die Muster laufen ueber
# das rohe HTML (mit Skript- und Link-Adressen), Gross-/Kleinschreibung egal.
NUTZUNGSNACHWEIS: Dict[str, Dict[str, object]] = {
    'woocommerce': {
        'name': 'WooCommerce',
        'nachweise': [
            # Produkt in den Warenkorb legen (Knopf, Link oder AJAX)
            r'add[-_]to[-_]cart',
            r'wc-ajax=add_to_cart',
            # Produkt-, Shop-, Warenkorb- und Kassenseiten tragen eigene Klassen
            r'\b(?:single-product|type-product|product-type-\w+|woocommerce-(?:shop|cart|checkout|account|page|mini-cart|loop-product\S*))\b',
            r'wc-block-grid',
            r'wp-block-woocommerce-',
            r'woocommerce-mini-cart|cart-contents',
            # Links auf die Shop-Seiten
            r'href=["\'][^"\']*/(?:shop|warenkorb|cart|checkout|kasse|produkt|product|mein-konto|my-account)/?["\'?#]',
            # Cookies, die nur bei genutzter Shop-Funktion entstehen
            r'woocommerce_items_in_cart|wp_woocommerce_session|woocommerce_recently_viewed',
        ],
        'grund': (
            'WooCommerce ist installiert, auf der gescannten Seite gibt es aber '
            'weder Produkte noch Warenkorb, Kasse oder Shop-Links. Ohne '
            'Shop-Funktion setzt WooCommerce keine Cookies; im Banner stünde ein '
            'Dienst, den kein Besucher bekommt.'
        ),
    },
}

_KOMPILIERT = {
    key: [re.compile(m, re.IGNORECASE) for m in regel['nachweise']]  # type: ignore[index]
    for key, regel in NUTZUNGSNACHWEIS.items()
}


def nachweise(service_key: str, html: str) -> List[str]:
    """Die Muster, die auf der Seite greifen (leer: kein Nachweis)."""
    muster = _KOMPILIERT.get(service_key)
    if not muster:
        return []
    return [m.pattern for m in muster if m.search(html or '')]


def pruefe_nutzung(service_key: str, html: str) -> Optional[str]:
    """
    None, wenn der Dienst in Gebrauch ist oder keine Regel hat; sonst der
    Grund, warum er nicht ins Banner gehoert.
    """
    regel = NUTZUNGSNACHWEIS.get(service_key)
    if not regel:
        return None
    if nachweise(service_key, html):
        return None
    return str(regel['grund'])


def hat_shop_funktion(html: str) -> bool:
    """WooCommerce-Shop in Gebrauch (Produkte, Warenkorb, Kasse, Shop-Links)."""
    return bool(nachweise('woocommerce', html))
