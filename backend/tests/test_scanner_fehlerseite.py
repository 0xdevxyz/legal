"""
Der Scanner darf keine Fehlerseite als Kundenseite vermessen.

`page.goto()` liefert die HTTP-Antwort zurueck; der Rueckgabewert wurde
verworfen. Damit vermass der axe-Pfad die 404-Seite des Hosters, als waere sie
die Website des Kunden — ein Tippfehler in der Adresse oder eine Stunde
Ausfall genuegten. Die Befunde landeten unter der echten site_id und
ueberschrieben die gueltige Messung.

Gefunden an einem Pruefstueck: ein Scan auf /gibtsnicht.html lieferte zwei
Befunde und `error=None`.

Der HTML-Pfad in public_routes.py prueft `status == 200` seit jeher. Nur der
Browser-Pfad, der die Seite selbst laedt, tat es nicht.
"""
import io
import os
import sys
import tokenize

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.axe_scanner import AxeScanner  # noqa: E402


def _quelle_ohne_kommentare() -> str:
    """
    Quelltext ohne Kommentare und Docstrings.

    Ohne das findet der Waechter seine Suchzeichenkette in der Begruendung, die
    ueber der Reparatur steht, und gilt als bestanden — obwohl der Fehler
    wieder im Code stuende. Das ist in diesem Projekt schon mehrfach passiert.
    """
    pfad = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "compliance_engine", "axe_scanner.py")
    with open(pfad, encoding="utf-8") as fh:
        quelle = fh.read()

    stuecke = []
    vorher = tokenize.INDENT
    for tok in tokenize.generate_tokens(io.StringIO(quelle).readline):
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING and vorher in (
                tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE,
                tokenize.NL, tokenize.ENCODING):
            continue
        stuecke.append(tok.string)
        if tok.type not in (tokenize.NL, tokenize.NEWLINE):
            vorher = tok.type
    return " ".join(stuecke)


class TestAntwortWirdGeprueft:
    def test_goto_rueckgabewert_wird_benutzt(self):
        q = _quelle_ohne_kommentare()
        assert "antwort = await page . goto" in q or "antwort=await page.goto" in q, \
            "Rueckgabewert von goto() wieder verworfen"

    def test_statuscode_wird_geprueft(self):
        q = _quelle_ohne_kommentare()
        assert "antwort . status >= 400" in q or "antwort.status>=400" in q, \
            "HTTP-Status wird nicht mehr geprueft"

    def test_keine_antwort_wird_abgefangen(self):
        assert "antwort is None" in _quelle_ohne_kommentare()


class TestFehlerErgebnisIstAlsFehlerErkennbar:
    """
    Der Aufrufer erkennt einen Fehler an `by_impact["error"]` und gibt dann
    None zurueck, statt eine Null-Messung weiterzureichen. Diese Zusage muss
    halten, sonst nuetzt die Statuspruefung nichts.
    """

    def test_fehlerergebnis_traegt_den_schluessel(self):
        r = AxeScanner()._create_empty_result("https://x.de", "HTTP 404")
        assert isinstance(r.by_impact, dict) and "error" in r.by_impact
        assert r.total_violations == 0 and r.violations == []

    def test_grund_steht_im_ergebnis(self):
        r = AxeScanner()._create_empty_result(
            "https://x.de", "Seite antwortet mit HTTP 503 — gemessen wurde nicht")
        assert "503" in r.by_impact["error"]
