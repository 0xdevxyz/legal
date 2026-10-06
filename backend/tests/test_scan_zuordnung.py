"""Ein fertiger Scan gehoert seiner Seite, auch wenn ein zweiter gleichzeitig laeuft.

Gemeldet am 06.10.2026: Wer mitten in einer Analyse auf eine andere Seite
wechselt, sieht deren Anzeige mit dem Ergebnis der ersten. Der Scan der alten
Seite laeuft serverseitig weiter (er laesst sich nicht abbrechen), die neue
Seite startet einen zweiten. Beide gehoeren demselben Konto.

Im Backend lag die Falle in der Rueckgabe: nach dem INSERT in `scan_history`
fragte der Code "den neuesten Scan dieses Nutzers" ab und gab dessen `scan_id`
zurueck. Mit zwei Scans pro Konto ist der neueste nicht zwingend der eigene, und
an der `scan_id` haengen KI-Fixes, PDF-Bericht und Fix-Jobs. Dazu war die
`scan_id` auf die Sekunde genau und die Spalte nicht UNIQUE: zwei Scans eines
Kontos, die in derselben Sekunde fertig wurden, teilten sich eine Kennung.

Wie `test_fortschritt_kennung.py` prueft dieser Waechter die Nahtstelle im Code,
weil die Fehlerklasse ohne zwei echte parallele Scans nicht auffaellt.
"""

import os
import re

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def quelle(*teile):
    return open(os.path.join(BACKEND, *teile), encoding="utf-8").read()


def _funktion(src: str, kopf: str) -> str:
    """Rumpf der Funktion `kopf` bis zur naechsten Funktion auf oberster Ebene."""
    start = src.index(kopf)
    rest = src[start + len(kopf):]
    m = re.search(r"\n(?:async def|def|@app\.)", rest)
    return src[start: start + len(kopf) + (m.start() if m else len(rest))]


class TestScanBekommtSeineEigeneZeile:
    def test_v2_scan_liest_seine_zeile_per_returning(self):
        rumpf = _funktion(quelle("main_production.py"), "async def fuehre_v2_scan_aus(")
        assert "RETURNING id, scan_id" in rumpf

    def test_v2_scan_fragt_nicht_den_neuesten_scan_des_nutzers_ab(self):
        rumpf = _funktion(quelle("main_production.py"), "async def fuehre_v2_scan_aus(")
        assert "ORDER BY scan_timestamp DESC LIMIT 1" not in rumpf

    def test_schnellscan_liest_seine_zeile_per_returning(self):
        rumpf = _funktion(quelle("main_production.py"), "async def quick_analyze_website(")
        assert "RETURNING id" in rumpf
        assert "ORDER BY scan_timestamp DESC LIMIT 1" not in rumpf

    def test_antwort_traegt_die_scan_id_der_eigenen_zeile(self):
        s = quelle("main_production.py")
        assert '"scan_id": new_scan[\'scan_id\']' in s
        assert '"scan_id": str(new_scan[\'id\'])' in s


class TestScanIdIstEindeutig:
    def test_v2_scan_id_traegt_einen_zufallsanteil(self):
        rumpf = _funktion(quelle("main_production.py"), "async def fuehre_v2_scan_aus(")
        m = re.search(r'scan_id = f"scan_[^"]*"', rumpf)
        assert m, "scan_id-Bildung nicht gefunden"
        assert "uuid" in m.group(0)

    def test_schnellscan_id_traegt_einen_zufallsanteil(self):
        rumpf = _funktion(quelle("main_production.py"), "async def quick_analyze_website(")
        m = re.search(r'scan_id = f"quick_[^"]*"', rumpf)
        assert m, "scan_id-Bildung nicht gefunden"
        assert "uuid" in m.group(0)

    def test_uuid_alias_ist_importiert(self):
        # Die Datei importiert das Modul als `_uuid`. Ein Aufruf als `uuid.`
        # liefe erst zur Laufzeit in einen NameError, mitten im Kundenscan.
        s = quelle("main_production.py")
        assert re.search(r"^import uuid as _uuid", s, re.M)
        assert "_uuid.uuid4()" in s
        assert not re.search(r"(?<![\w.])uuid\.uuid4\(\)", s)


class TestScanWirdDerRichtigenSeiteZugeschrieben:
    def test_tracked_website_wird_ueber_die_gescannte_url_gesucht(self):
        # Der Verlauf (score_history, last_score) haengt an der URL des Scans,
        # nicht an der "aktiven" oder zuletzt benutzten Seite des Kontos.
        rumpf = _funktion(quelle("main_production.py"), "async def fuehre_v2_scan_aus(")
        assert "FROM tracked_websites WHERE user_id = $1 AND url = $2" in rumpf
        assert 'scan_result["url"]' in rumpf
