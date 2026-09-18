"""Eine Freigabe ist nur dann ein Beleg, wenn jemand sie erteilt hat.

Bis zum 05.09.2026 gingen dokumentweite Fixes ohne Rueckfrage live. Achtzehn
davon stehen bis heute auf `approved`. Aus Sicht einer reinen Statusabfrage
sind das achtzehn Zustimmungen bei null Ablehnungen: 100 % Annahmequote fuer
ein Verfahren, das nie jemand beurteilt hat.

Ab 30 Belegen je Befundtyp darf ein Skill `aktiv` werden. Zaehlten diese
achtzehn mit, traegt spaeter ein Verfahren das Praedikat "bewaehrt", dessen
Bewaehrung nie stattgefunden hat — genau die Sorte erfundener Erfahrung, vor
der Phase 3 der Roadmap warnt.

Die Tests halten drei Dinge fest:

1. Wer ohne Rueckfrage freigibt, vermerkt das ('automatik').
2. Ein einmal erteiltes Urteil ('mensch') ueberlebt jeden weiteren Scan.
3. Der Lernstand zaehlt nur 'mensch' als Zustimmung — und verschweigt den
   Rest trotzdem nicht.
"""

import datetime as dt
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import lernstand as ls

HIER = os.path.dirname(__file__)
BACKEND = os.path.abspath(os.path.join(HIER, '..'))
WURZEL = os.path.abspath(os.path.join(BACKEND, '..'))


def _lies(*teile):
    with open(os.path.join(*teile), encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------

MIGRATION = os.path.join(
    BACKEND, 'alembic', 'versions', '20260907_0024b_entscheidung_quelle.py')


class TestMigration:
    def test_migration_haengt_an_0023_und_nicht_an_der_schwester(self):
        """Bewusst ein Zweig hinter 0023.

        Parallel entstand am 07.09. eine zweite 0024, die auf der
        Produktionsdatenbank steht, aber in keinem Commit liegt. Eine
        Abhaengigkeit darauf wuerde jede frische Auscheckung brechen — die
        Kette risse an einer Revision, die es in der Versionsverwaltung nicht
        gibt.
        """
        s = _lies(MIGRATION)
        assert 'revision: str = "0024_entscheidung_quelle"' in s
        assert 'down_revision: Union[str, None] = "0023_ablehngrund_pruefregeln"' in s
        assert "0024_gen_docs_version" not in s.split('"""')[2]

    def test_nachtrag_nur_vor_der_freischaltung_der_freigaberoute(self):
        """Alles nach dem 05.09. bleibt NULL.

        Die Freigaberoute gab es vorher nicht, eine Freigabe von damals kann
        also nur von der Automatik stammen. Danach laesst es sich nicht mehr
        unterscheiden — und eine erfundene Herkunft waere schlimmer als eine
        Luecke, weil sie sich als Beleg ausgeben wuerde.
        """
        s = _lies(MIGRATION)
        assert "COALESCE(updated_at, created_at) < TIMESTAMP" in s
        assert "FREIGABEWEG_SEIT" in s

    def test_kontrast_bleibt_aussen_vor(self):
        """Dort steht die Entscheidung je Farbpaar im Payload.

        Der Zeilenstatus ist bei kontrast-css abgeleitet. Ihm eine Herkunft
        zuzuschreiben hiesse, eine Aussage ueber zwoelf Farbpaare aus einer
        Zeile zu erfinden.
        """
        s = _lies(MIGRATION)
        assert "fix_type <> 'kontrast-css'" in s

    def test_vorgabewert_wird_auf_pending_gezogen(self):
        """Ein Vorgabewert, der der Produktentscheidung widerspricht, ist eine
        Falle: ein Einfuegen ohne Statusangabe lief still wieder auf
        Auto-Freigabe."""
        s = _lies(MIGRATION)
        assert "ALTER COLUMN status SET DEFAULT 'pending'" in s

    def test_downgrade_nimmt_alles_zurueck(self):
        s = _lies(MIGRATION)
        unten = s.split('def downgrade')[1]
        assert 'drop_column' in unten
        assert 'drop_index' in unten
        assert "SET DEFAULT 'approved'" in unten


# ---------------------------------------------------------------------------
# Speicherung
# ---------------------------------------------------------------------------

SAVER = os.path.join(BACKEND, 'accessibility_fix_saver.py')


class TestSpeicherung:
    def test_auto_freigabe_vermerkt_sich_selbst(self):
        s = _lies(SAVER)
        assert "THEN 'automatik' ELSE NULL END" in s

    def test_jede_festgestellte_herkunft_ueberlebt_den_naechsten_scan(self):
        """Nicht nur 'mensch' — auch 'automatik'.

        Die erste Fassung schuetzte nur 'mensch' und liess sonst
        `EXCLUDED.entscheidung_quelle` gelten. EXCLUDED ist aber NULL, sobald
        der Scan 'pending' liefert, und das tut er seit dem 05.09. immer. Also
        loeschte jeder Wiederholungsscan den Vermerk 'automatik': die Zeile
        blieb freigegeben und live, las sich aber nur noch als "Herkunft
        unbekannt". Fuenf der achtzehn Vermerke aus 0024b waren am 17.09.2026
        auf diesem Weg verschwunden.

        Eine Herkunft ist eine Aussage ueber die Vergangenheit. Ein spaeterer
        Scan weiss darueber nichts Besseres, also darf er sie nur ergaenzen,
        nie ersetzen. Genau das leistet COALESCE — und ein CASE auf einen
        einzelnen Wert leistet es nicht.
        """
        s = _lies(SAVER)
        block = s.split('ON CONFLICT (site_id, fix_type)')[1].split('"""')[0]
        assert 'entscheidung_quelle = COALESCE(' in block
        assert 'accessibility_document_fixes.entscheidung_quelle,' in block
        assert 'EXCLUDED.entscheidung_quelle)' in block
        # Die Gegenprobe: kein Zweig darf die Spalte auf einen einzelnen Wert
        # festnageln, sonst faellt alles andere wieder auf NULL.
        assert "THEN 'mensch'\n" not in block

    def test_freigaberoute_schreibt_mensch(self):
        s = _lies(SAVER)
        block = s.split('async def set_dokument_status')[1].split('async def set_kontrast_freigabe')[0]
        assert "entscheidung_quelle = 'mensch'" in block

    def test_oberflaeche_bekommt_die_herkunft(self):
        s = _lies(SAVER)
        block = s.split('async def get_document_fixes_for_site')[1].split('async def ')[0]
        assert 'entscheidung_quelle' in block
        assert '"entscheidung_quelle": r[' in block


# ---------------------------------------------------------------------------
# Nachtrag: was der Wiederholungsscan geloescht hatte
# ---------------------------------------------------------------------------

NACHTRAG = os.path.join(
    BACKEND, 'alembic', 'versions',
    '20260917_0033_herkunft_ueberlebt_scan.py')


class TestNachtrag:
    def test_haengt_am_kopf(self):
        s = _lies(NACHTRAG)
        assert 'revision: str = "0033_herkunft_ueberlebt_scan"' in s
        assert 'down_revision: Union[str, None] = "0032_kontosicherheit"' in s

    def test_sieht_auf_created_at_statt_updated_at(self):
        """0024b sah auf COALESCE(updated_at, created_at). Genau dieses Feld
        hat der Wiederholungsscan verstellt — es taugt hier nicht mehr als
        Beleg dafuer, wann die Zeile zuletzt beurteilt wurde."""
        s = _lies(NACHTRAG)
        # Nur die Anweisung selbst, nicht der erklaerende Kopf: dort steht der
        # alte Ausdruck als Begruendung, und das soll er auch.
        sql = s.split('def upgrade')[1].split('def downgrade')[0]
        assert "created_at < TIMESTAMP" in sql
        assert "COALESCE(updated_at, created_at)" not in sql

    def test_verlangt_die_signatur_der_auto_freigabe(self):
        """approved_at = created_at. Die Freigaberoute setzt approved_at auf
        NOW(), also spaeter als die Anlage. Ohne diese Bedingung koennte der
        Nachtrag eine von Hand erteilte Freigabe als 'automatik' ausgeben —
        und eine erfundene Herkunft ist schlimmer als eine Luecke, weil sie
        sich als Beleg ausgibt."""
        s = _lies(NACHTRAG)
        assert "approved_at = created_at" in s.split('def downgrade')[0]

    def test_ruehrt_nur_unentschiedene_zeilen_an(self):
        s = _lies(NACHTRAG)
        oben = s.split('def downgrade')[0]
        assert "entscheidung_quelle IS NULL" in oben
        assert "fix_type <> 'kontrast-css'" in oben

    def test_downgrade_loescht_den_vermerk_nicht_erneut(self):
        """Ein Zurueck waere genau der Fehler, den die Revision behebt."""
        s = _lies(NACHTRAG)
        unten = s.split('def downgrade')[1]
        assert 'op.execute' not in unten
        assert 'UPDATE' not in unten


# ---------------------------------------------------------------------------
# Lernstand
# ---------------------------------------------------------------------------

class Zeile(dict):
    pass


class FakeConn:
    def __init__(self, je_tabelle):
        self.je_tabelle = je_tabelle
        self.sql = []

    async def fetch(self, sql, *params):
        self.sql.append(sql)
        if "SELECT payload" in sql:
            return []
        if "status = 'rejected'" in sql and "GROUP BY 1 ORDER BY 2 DESC" in sql:
            return []
        for tabelle, zeilen in self.je_tabelle.items():
            if f"FROM {tabelle}" in sql:
                return zeilen
        return []

    async def fetchrow(self, sql, *params):
        return Zeile(erzeugt=0, aktiv=0, abgeschaltet=0, wartet=0, mit_grund=0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return self._conn


def dok_zeile(typ, vor, an=0, uebernommen=0, unbekannt=0, ab=0, offen=0):
    return Zeile(typ=typ, vorgeschlagen=vor, angenommen=an,
                 uebernommen=uebernommen, unbekannt=unbekannt,
                 abgelehnt=ab, offen=offen, ausgeliefert=0,
                 konfidenz_angenommen=None, konfidenz_abgelehnt=None,
                 zuletzt=dt.datetime(2026, 9, 4))


DOK = "accessibility_document_fixes"


class TestAbfrage:
    def test_dokumentfixes_fragen_nach_der_herkunft(self):
        """Die Trennung muss in der Abfrage stehen, nicht erst in der
        Auswertung: sonst holt sie Zahlen, die den Unterschied schon verloren
        haben."""
        quelle = [q for q in ls.QUELLEN if q["tabelle"] == DOK][0]
        assert quelle["herkunft_spalte"] == "entscheidung_quelle"

    def test_alt_und_linktexte_fragen_nicht(self):
        """Dort war jedes `approved` immer ein Klick. Eine Spalte anzulegen
        hiesse, eine Frage zu stellen, die es in diesen Tabellen nicht gibt."""
        for tabelle in ("accessibility_alt_text_fixes", "accessibility_link_fixes"):
            quelle = [q for q in ls.QUELLEN if q["tabelle"] == tabelle][0]
            assert quelle["herkunft_spalte"] is None

    @pytest.mark.asyncio
    async def test_sql_trennt_mensch_von_automatik(self):
        conn = FakeConn({DOK: []})
        await ls._eine_quelle(conn, [q for q in ls.QUELLEN if q["tabelle"] == DOK][0], 90)
        sql = conn.sql[0]
        assert "entscheidung_quelle = 'mensch'" in sql
        assert "entscheidung_quelle = 'automatik'" in sql
        assert "entscheidung_quelle IS NULL" in sql

    @pytest.mark.asyncio
    async def test_ohne_herkunftsspalte_zaehlt_approved_wie_bisher(self):
        conn = FakeConn({"accessibility_alt_text_fixes": []})
        quelle = [q for q in ls.QUELLEN
                  if q["tabelle"] == "accessibility_alt_text_fixes"][0]
        await ls._eine_quelle(conn, quelle, 90)
        sql = conn.sql[0]
        assert "FILTER (WHERE status = 'approved')" in sql
        assert "entscheidung_quelle" not in sql


class TestAuswertung:
    @pytest.mark.asyncio
    async def test_automatik_ist_keine_zustimmung(self):
        """Der eigentliche Punkt: sechs live stehende Skip-Links, die niemand
        beurteilt hat, ergeben keine Annahmequote von 100 %, sondern gar
        keine."""
        conn = FakeConn({DOK: [dok_zeile("skip-link", vor=6, uebernommen=6)]})
        stand = await ls.erhebe_lernstand(FakePool(conn), tage=90)
        eintrag = [e for e in stand["befundtypen"]
                   if e["befundtyp"] == "dokument:skip-link"][0]
        assert eintrag["angenommen"] == 0
        assert eintrag["automatisch_uebernommen"] == 6
        assert eintrag["annahmequote"] is None
        assert eintrag["belege_reichen"] is False

    @pytest.mark.asyncio
    async def test_uebernommenes_verschwindet_nicht(self):
        """Nicht zaehlen heisst nicht verschweigen. Eine Reparatur, die seit
        Wochen unbestaetigt auf einer Kundenseite laeuft, ist eine Aufgabe."""
        conn = FakeConn({DOK: [dok_zeile("struktur", vor=4, uebernommen=4)]})
        stand = await ls.erhebe_lernstand(FakePool(conn), tage=90)
        assert stand["unbestaetigt_live"] == 4

    @pytest.mark.asyncio
    async def test_unbekannte_herkunft_zaehlt_auch_nicht_als_beleg(self):
        conn = FakeConn({DOK: [dok_zeile("css-rule", vor=2, unbekannt=2)]})
        stand = await ls.erhebe_lernstand(FakePool(conn), tage=90)
        eintrag = stand["befundtypen"][0]
        assert eintrag["angenommen"] == 0
        assert eintrag["herkunft_unbekannt"] == 2
        assert stand["unbestaetigt_live"] == 2

    @pytest.mark.asyncio
    async def test_echte_entscheidungen_zaehlen_weiter(self):
        conn = FakeConn({DOK: [dok_zeile("skip-link", vor=10, an=7, ab=3)]})
        stand = await ls.erhebe_lernstand(FakePool(conn), tage=90)
        eintrag = stand["befundtypen"][0]
        assert eintrag["angenommen"] == 7
        assert eintrag["annahmequote"] == 0.7
        assert stand["unbestaetigt_live"] == 0

    @pytest.mark.asyncio
    async def test_gemischt_traegt_beide_zahlen_nebeneinander(self):
        conn = FakeConn({DOK: [dok_zeile("skip-link", vor=9, an=2, uebernommen=6, ab=1)]})
        stand = await ls.erhebe_lernstand(FakePool(conn), tage=90)
        eintrag = stand["befundtypen"][0]
        assert (eintrag["angenommen"], eintrag["abgelehnt"]) == (2, 1)
        assert eintrag["automatisch_uebernommen"] == 6
        # Aus zwei Zustimmungen und einer Ablehnung, nicht aus acht zu einer.
        assert eintrag["annahmequote"] == 0.667

    @pytest.mark.asyncio
    async def test_belegschwelle_ignoriert_uebernommenes(self):
        """29 echte Entscheidungen plus 50 Uebernahmen reichen nicht."""
        conn = FakeConn({DOK: [dok_zeile("skip-link", vor=79, an=29, uebernommen=50)]})
        stand = await ls.erhebe_lernstand(FakePool(conn), tage=90)
        assert stand["befundtypen"][0]["belege_reichen"] is False
        assert stand["aussagekraeftig"] is False


# ---------------------------------------------------------------------------
# Oberflaeche
# ---------------------------------------------------------------------------

WORKLIST = os.path.join(
    WURZEL, 'dashboard-react', 'src', 'components', 'accessibility',
    'AccessibilityWorklist.tsx')


# Diese Klasse liest Frontend-Quelltext, der im Repo neben backend/ liegt. Im
# Backend-Container ist nur backend/ nach /app kopiert, dort gibt es ihn nicht —
# das ist kein Fehlschlag, sondern eine andere Umgebung. CI checkt das ganze
# Repo aus und fuehrt die Klasse aus.
_FRONTEND_QUELLEN = os.path.join(WURZEL, 'dashboard-react')
ohne_frontend = pytest.mark.skipif(
    not os.path.isdir(_FRONTEND_QUELLEN),
    reason="Frontend-Quelltext liegt nicht neben backend/ (z. B. im Container) — laeuft in CI",
)


@ohne_frontend
class TestOberflaeche:
    def test_unbestaetigte_werden_getrennt_gezeigt(self):
        s = _lies(WORKLIST)
        assert "entscheidung_quelle !== 'mensch'" in s
        assert 'läuft live, nie bestätigt' in s

    def test_bestaetigen_aendert_nichts_ablehnen_schon(self):
        """Der Unterschied muss dranstehen. "War falsch" nimmt eine Reparatur
        von einer laufenden Kundenwebsite — das darf niemanden ueberraschen."""
        s = _lies(WORKLIST)
        assert 'Passt so' in s
        assert 'War falsch' in s
        assert 'nächsten Abruf' in s

    def test_bestaetigte_bleiben_als_aktiv_stehen(self):
        s = _lies(WORKLIST)
        assert 'bestaetigt.map' in s
