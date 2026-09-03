"""
Eine erteilte Freigabe muss den naechsten Scan ueberleben.

complyos zentrale Zusage lautet: nichts geht ungeprueft auf die Website eines
Kunden. Drei getrennte Upserts haben sie auf drei Arten gebrochen — alle drei
still, alle drei erst bei einem Wiederholungslauf sichtbar. Bis dahin war
nur EIN Scan je Seite gelaufen; deshalb hat es nie jemand gesehen.

  Bildbeschreibung  `suggested_alt = EXCLUDED.suggested_alt` galt unbedingt.
                    Der Kunde gab "Firmengebaeude der Spedition in Zwickau"
                    frei, der naechste Scan formulierte "Ein LKW steht vor
                    einer Halle" — und weil der Status unberuehrt blieb, ging
                    der neue Text ALS FREIGEGEBEN live. Nachgewiesen, nicht
                    vermutet.

  Dokument-Fix      `status = EXCLUDED.status`. Kontrast wird immer als
                    'pending' gespeichert, also fiel jede erteilte
                    Farbfreigabe beim naechsten Scan zurueck — die Reparatur
                    verschwand still von der Website. Bei woechentlichem Scan
                    haelt so keine Freigabe eine Woche.

  Linkname          wie die Bildbeschreibung.

Diese Tests pruefen den SQL-Text, weil die Zusage im SQL steht. Ein
Durchstich gegen eine echte Datenbank liegt daneben (tools/freigabe_haelt.py)
und deckt dasselbe im Betrieb ab.
"""
import io
import os
import re
import sys
import tokenize

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _sql_ohne_kommentare() -> str:
    """
    Der Quelltext ohne Python-Kommentare, -Docstrings und SQL-Kommentare.

    Ohne das findet ein Waechter seine Suchzeichenkette in der Begruendung,
    die ueber der Reparatur steht, und gilt als bestanden — obwohl der Fehler
    wieder im Code stuende. In diesem Projekt ist das schon fuenfmal passiert,
    zuletzt hier: die SQL-Kommentare nennen die alten, verbotenen Zeilen
    woertlich.
    """
    pfad = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "accessibility_fix_saver.py")
    with open(pfad, encoding="utf-8") as fh:
        quelle = fh.read()

    stuecke = []
    vorher = tokenize.INDENT
    for tok in tokenize.generate_tokens(io.StringIO(quelle).readline):
        if tok.type == tokenize.COMMENT:
            continue
        text = tok.string
        if tok.type == tokenize.STRING:
            if vorher in (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE,
                          tokenize.NL, tokenize.ENCODING):
                continue  # Docstring
            # SQL-Kommentare innerhalb der Abfragen ebenfalls entfernen
            text = re.sub(r"--[^\n]*", "", text)
        stuecke.append(text)
        if tok.type not in (tokenize.NL, tokenize.NEWLINE):
            vorher = tok.type
    return " ".join(stuecke)


def _normal(s: str) -> str:
    return re.sub(r"\s+", " ", s)


class TestBildbeschreibung:
    def test_vorschlag_wird_nur_bei_offenen_ersetzt(self):
        sql = _normal(_sql_ohne_kommentare())
        assert "suggested_alt = CASE WHEN accessibility_alt_text_fixes.status = " \
               "'pending' THEN EXCLUDED.suggested_alt" in sql

    def test_kein_unbedingtes_ueberschreiben_mehr(self):
        sql = _normal(_sql_ohne_kommentare())
        assert "suggested_alt = EXCLUDED.suggested_alt," not in sql, \
            "Freigegebener Text wird wieder ueberschrieben"

    def test_abweichung_geht_nicht_verloren(self):
        sql = _normal(_sql_ohne_kommentare())
        assert "'abweichender_vorschlag'" in sql


class TestDokumentFix:
    def test_freigabe_wird_nicht_zurueckgesetzt(self):
        sql = _normal(_sql_ohne_kommentare())
        assert "status = CASE WHEN accessibility_document_fixes.status = " \
               "'approved' THEN 'approved'" in sql

    def test_kein_status_uebernehmen_mehr(self):
        sql = _normal(_sql_ohne_kommentare())
        assert "status = EXCLUDED.status," not in sql, \
            "Jeder Rescan wuerde wieder alle Farbfreigaben abschalten"

    def test_freigegebenes_payload_bleibt_aktiv(self):
        sql = _normal(_sql_ohne_kommentare())
        assert "'neuer_vorschlag'" in sql


class TestLinkname:
    def test_beschriftung_wird_nur_bei_offenen_ersetzt(self):
        sql = _normal(_sql_ohne_kommentare())
        assert "suggested_label = CASE WHEN accessibility_link_fixes.status = " \
               "'pending' THEN EXCLUDED.suggested_label" in sql

    def test_kein_unbedingtes_ueberschreiben_mehr(self):
        sql = _normal(_sql_ohne_kommentare())
        assert "suggested_label = EXCLUDED.suggested_label," not in sql


class TestDerWaechterPrueftDenCodeUndNichtSichSelbst:
    """
    Diese Datei nennt die verbotenen Zeilen im eigenen Docstring. Wenn die
    Filterung kaputtgeht, muessen die Tests oben rot werden — nicht gruen.
    """

    def test_sql_kommentare_sind_entfernt(self):
        sql = _sql_ohne_kommentare()
        assert "-- Eine erteilte Freigabe" not in sql

    def test_docstrings_sind_entfernt(self):
        assert "STABILE, domain-abgeleitete" not in _sql_ohne_kommentare()

    def test_aber_das_sql_selbst_ist_noch_da(self):
        assert "ON CONFLICT" in _sql_ohne_kommentare()
