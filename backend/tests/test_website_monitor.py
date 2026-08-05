"""
Tests fuer das Website-Monitoring (cronjobs/website_monitor.py).

Die Wirtschaftlichkeit des Monitoring-Tarifs haengt an einer Zahl: wie oft der
teure Vollscan laeuft. Diese Tests sichern die beiden Entscheidungen, die das
steuern — den Fingerabdruck (was gilt als Aenderung?) und die
Vollscan-Entscheidung (wann wird gescannt?).
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cronjobs.website_monitor import (
    SCHWELLE_VERSCHLECHTERUNG,
    _fingerabdruck,
    _vollscan_noetig,
)

BASIS_HTML = """
<html><head>
<script src="https://cdn.example.com/app.js?v=123"></script>
</head><body>
<a href="/impressum">Impressum</a>
<a href="/datenschutz">Datenschutz</a>
<form action="/kontakt"><input name="email"><textarea></textarea></form>
<img src="/logo.png" alt="Logo">
<img src="/team.jpg">
<p>Willkommen bei uns. Wir machen Dinge.</p>
</body></html>
"""


class TestFingerabdruck:
    def test_stabil_bei_identischem_html(self):
        assert _fingerabdruck(BASIS_HTML) == _fingerabdruck(BASIS_HTML)

    def test_cache_buster_aendert_nichts(self):
        """
        Der Sinn des Fingerabdrucks: ?v=124 statt ?v=123 ist KEINE Aenderung.
        Sonst waere jeder Tag ein Vollscan und die Ersparnis dahin.
        """
        variiert = BASIS_HTML.replace("app.js?v=123", "app.js?v=999")
        assert _fingerabdruck(BASIS_HTML) == _fingerabdruck(variiert)

    def test_neuer_tracker_wird_erkannt(self):
        """Ein neues Tracking-Skript ist genau die Aenderung, die zaehlt."""
        mit_tracker = BASIS_HTML.replace(
            "</head>",
            '<script src="https://www.googletagmanager.com/gtag/js"></script></head>',
        )
        assert _fingerabdruck(BASIS_HTML) != _fingerabdruck(mit_tracker)

    def test_entfernter_pflichtseiten_link_wird_erkannt(self):
        ohne_impressum = BASIS_HTML.replace('<a href="/impressum">Impressum</a>', "")
        assert _fingerabdruck(BASIS_HTML) != _fingerabdruck(ohne_impressum)

    def test_neues_formularfeld_wird_erkannt(self):
        mehr_felder = BASIS_HTML.replace(
            '<input name="email">', '<input name="email"><input name="telefon">'
        )
        assert _fingerabdruck(BASIS_HTML) != _fingerabdruck(mehr_felder)

    def test_zusaetzliches_bild_ohne_alt_wird_erkannt(self):
        mehr_bilder = BASIS_HTML.replace(
            '<img src="/team.jpg">', '<img src="/team.jpg"><img src="/neu.jpg">'
        )
        assert _fingerabdruck(BASIS_HTML) != _fingerabdruck(mehr_bilder)

    def test_kaputtes_html_stuerzt_nicht_ab(self):
        assert _fingerabdruck("<<<>>>nicht mal html")
        assert _fingerabdruck("")


class TestVollscanEntscheidung:
    def _site(self, **kwargs):
        basis = {
            "rescan_required": False,
            "rescan_reason": None,
            "last_scan_date": datetime.utcnow() - timedelta(days=1),
            "scan_frequency": "weekly",
            "content_fingerprint": "abc123",
        }
        basis.update(kwargs)
        return basis

    def test_unveraendert_und_nicht_faellig_kein_scan(self):
        noetig, grund = _vollscan_noetig(self._site(), "abc123")
        assert not noetig
        assert grund == "unverändert"

    def test_neue_rechtslage_erzwingt_scan(self):
        """rescan_required setzt der Legal-Change-Monitor — hat immer Vorrang."""
        noetig, grund = _vollscan_noetig(
            self._site(rescan_required=True, rescan_reason="Widerrufsbutton-Pflicht"), "abc123"
        )
        assert noetig
        assert "Widerrufsbutton-Pflicht" in grund

    def test_nie_geprueft_erzwingt_scan(self):
        noetig, grund = _vollscan_noetig(self._site(last_scan_date=None), "abc123")
        assert noetig
        assert grund == "noch nie geprüft"

    def test_faelligkeit_nach_frequenz(self):
        alt = self._site(last_scan_date=datetime.utcnow() - timedelta(days=8))
        noetig, grund = _vollscan_noetig(alt, "abc123")
        assert noetig
        assert "turnusmäßig" in grund

    def test_monatsfrequenz_wartet_laenger(self):
        site = self._site(
            scan_frequency="monthly",
            last_scan_date=datetime.utcnow() - timedelta(days=8),
        )
        noetig, _ = _vollscan_noetig(site, "abc123")
        assert not noetig

    def test_geaenderter_inhalt_erzwingt_scan(self):
        noetig, grund = _vollscan_noetig(self._site(), "NEUER-ABDRUCK")
        assert noetig
        assert "geändert" in grund

    def test_seite_nicht_abrufbar_kein_panik_scan(self):
        """
        Ist die Seite gerade nicht erreichbar (abdruck=None), wird nicht
        gescannt — ein Vollscan gegen eine tote Seite liefert nur Fehlbefunde.
        Die Frequenz-Faelligkeit greift unabhaengig davon.
        """
        noetig, _ = _vollscan_noetig(self._site(), None)
        assert not noetig

    def test_schwelle_ist_sinnvoll(self):
        assert 1 <= SCHWELLE_VERSCHLECHTERUNG <= 15
