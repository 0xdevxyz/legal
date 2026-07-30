"""
Tests fuer die Shop-Erkennung (Produktionscode compliance_engine/checks/shop_check.py).
Sichert insbesondere die FP-Regression aus Tier 0: die blanken Substrings
kaufen/bestellen duerfen NICHT in verkaufen/einkaufen/abbestellen matchen.
"""

from bs4 import BeautifulSoup

from compliance_engine.checks.shop_check import detect_shop


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def test_detects_real_shop():
    html = """
    <html><body>
      <button>In den Warenkorb</button>
      <a href="/checkout">Checkout</a>
      <div class="woocommerce">Shop</div>
    </body></html>
    """
    assert detect_shop(_soup(html)) is True


def test_no_false_positive_on_german_content_with_verkaufen():
    # Enthaelt verkaufen/einkaufen/abbestellen — darf NICHT als Shop gelten
    html = """
    <html><body>
      <p>Wir verkaufen Beratung und helfen beim Einkaufen von Wissen.</p>
      <p>Newsletter jederzeit abbestellen.</p>
      <p>Wir verkaufen keine Produkte, wir beraten.</p>
    </body></html>
    """
    assert detect_shop(_soup(html)) is False


def test_single_shop_signal_below_threshold():
    # Nur ein Signal ('jetzt kaufen') -> unter Threshold 3 -> kein Shop
    html = '<html><body><a>Jetzt kaufen</a><p>Informationen</p></body></html>'
    assert detect_shop(_soup(html)) is False


def test_standalone_kaufen_still_counts():
    # Eigenstaendiges kaufen/bestellen zaehlt weiterhin (Wortgrenze), mit Warenkorb+Checkout = Shop
    html = '<html><body><a>Kaufen</a><a>Bestellen</a><div>Warenkorb</div></body></html>'
    assert detect_shop(_soup(html)) is True
