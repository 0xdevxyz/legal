"""
Installiert ist nicht genutzt: WooCommerce kommt nur mit Shop-Funktion ins Banner.

Befund 21.10.2026 (rru-chemnitz.de): der Cookie-Scan meldete WooCommerce, die
Seite hat keinen Shop. Das Plugin haengt CSS, JavaScript und die Body-Klasse
woocommerce-no-js an jede Seite; das Muster 'woocommerce' traf damit jede
WordPress-Seite mit aktivem Plugin. Cookies setzt WooCommerce erst bei
Warenkorb, Kasse oder Produktseite.
"""
import os
import sys

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cookie_scanner_service import CookieScanner  # noqa: E402
from compliance_engine.plugin_nutzung import hat_shop_funktion, pruefe_nutzung  # noqa: E402
from compliance_engine.checks.shop_check import detect_shop  # noqa: E402
from compliance_engine.deep_scanner import DeepScanner  # noqa: E402

# Vereinsseite mit aktivem, aber ungenutztem WooCommerce: nur die Dateien,
# die das Plugin auf jede Seite haengt, dazu das Wort "kaufen" im Text.
NUR_INSTALLIERT = """
<html><head>
<link rel='stylesheet' href='https://rru-chemnitz.de/wp-content/plugins/woocommerce/assets/css/woocommerce.css' />
<script src='https://rru-chemnitz.de/wp-content/plugins/woocommerce/assets/js/frontend/woocommerce.min.js'></script>
<script src='https://rru-chemnitz.de/wp-content/plugins/woocommerce/assets/js/frontend/cart-fragments.min.js' id='wc-cart-fragments-js'></script>
<script>var woocommerce_params = {"ajax_url":"/wp-admin/admin-ajax.php","wc_ajax_url":"/?wc-ajax=%%endpoint%%"};</script>
<link rel='stylesheet' href='https://rru-chemnitz.de/wp-includes/css/dist/block-library/style.min.css' />
</head><body class="home page-template-default woocommerce-no-js">
<h1>Rudergemeinschaft</h1>
<p>Trikots kann man beim Vereinsabend kaufen.</p>
<a href="/kontakt/">Kontakt</a>
</body></html>
"""

MIT_SHOP = NUR_INSTALLIERT.replace(
    '<a href="/kontakt/">Kontakt</a>',
    '<a href="/shop/">Shop</a>'
    '<a class="button add_to_cart_button" href="?add-to-cart=12">In den Warenkorb</a>',
)


def _erkenne(html):
    ergebnis = CookieScanner()._detect_services(html, [], [], [], [])
    return ergebnis


class TestCookieScanner:
    def test_nur_installiertes_plugin_kommt_nicht_ins_banner(self):
        e = _erkenne(NUR_INSTALLIERT)
        assert 'woocommerce' not in e['services'], e
        assert 'woocommerce' not in e['confidence']
        assert 'woocommerce' in e['inaktive_dienste']
        assert 'keine Cookies' in e['inaktive_dienste']['woocommerce']
        # WordPress selbst bleibt erkannt, der Scan wird nicht leer
        assert 'wordpress' in e['services']

    def test_mit_shop_funktion_bleibt_woocommerce_im_banner(self):
        e = _erkenne(MIT_SHOP)
        assert 'woocommerce' in e['services'], e
        assert 'woocommerce' not in e['inaktive_dienste']

    def test_dienste_ohne_regel_bleiben_unberuehrt(self):
        e = _erkenne(MIT_SHOP)
        assert 'wordpress' in e['services']
        assert pruefe_nutzung('wordpress', NUR_INSTALLIERT) is None


class TestNachweise:
    def test_warenkorb_cookie_zaehlt_als_nutzung(self):
        assert hat_shop_funktion('<script>document.cookie="woocommerce_items_in_cart=1"</script>')

    def test_produktseite_zaehlt_als_nutzung(self):
        assert hat_shop_funktion('<body class="single single-product postid-7">')

    def test_shop_link_zaehlt_als_nutzung(self):
        assert hat_shop_funktion('<a href="https://x.de/warenkorb/">Warenkorb</a>')

    def test_nur_dateien_und_body_klasse_sind_kein_nachweis(self):
        assert not hat_shop_funktion(NUR_INSTALLIERT)


class TestShopErkennung:
    def test_vereinsseite_mit_plugin_ist_kein_shop(self):
        # 'woocommerce' + 'cart' (wc-cart-fragments) + 'kaufen' waeren drei
        # Treffer und damit "Online-Shop erkannt", AGB fehlen, kritisch.
        assert detect_shop(BeautifulSoup(NUR_INSTALLIERT, 'html.parser')) is False

    def test_echter_shop_bleibt_shop(self):
        assert detect_shop(BeautifulSoup(MIT_SHOP, 'html.parser')) is True

    def test_deep_scanner_nennt_woocommerce_nur_mit_shop(self):
        ds = DeepScanner()
        assert ds._detect_shop_system(BeautifulSoup(NUR_INSTALLIERT, 'html.parser')) is None
        assert ds._detect_shop_system(BeautifulSoup(MIT_SHOP, 'html.parser')) == 'WooCommerce'
