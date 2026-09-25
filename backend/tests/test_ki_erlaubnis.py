"""Die Zusage der Datenschutzerklaerung, als Test.

Die veroeffentlichte Datenschutzerklaerung sagt (Abschnitt 4):

    "Wer das vermeiden moechte, kann die KI-gestuetzten Funktionen ungenutzt
     lassen; die technische Pruefung und die Reparaturen ohne Sprachmodell
     laufen vollstaendig auf unseren Servern in Deutschland."

Am 25.09.2026 gemessen: der Satz stimmte nicht. Es gab keinen Schalter, und
ungenutzt lassen liess sich die KI auch nicht, denn sie haengt am Scan. Nach
jedem Scan startet public_routes.py den AccessibilityPostScanProcessor, und
fand der Scan Bilder ohne Alternativtext, gingen deren Adressen an Claude
Vision ueber OpenRouter, also in die USA. Gefragt wurde vorher das
Tagesbudget, der Tarif und der Zugangsschluessel, nicht der Kunde.

Dieser Test haelt die Zusage fest. Er ist absichtlich streng an den Stellen,
die Kundendaten in ein Drittland schicken, und er schreibt auf, welche
Stellen NICHT dahinter liegen: eine Luecke, die benannt ist, kann man
schliessen, eine unbenannte nicht.
"""
import os
import re

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import ki_erlaubnis  # noqa: E402


def _quelle(*teile):
    pfad = os.path.join(_BACKEND, *teile)
    if not os.path.exists(pfad):
        pytest.skip(f"{'/'.join(teile)} nicht eingehaengt")
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


# Stellen, an denen ein Sprachmodell auf Bilddaten einer KUNDENSEITE angesetzt
# wird und ein Konto dahintersteht. Sie muessen die Erlaubnis abfragen.
HINTER_DER_SCHRANKE = [
    ("accessibility_post_scan_processor.py", "_generate_alt_text_fixes"),
    ("alt_text_routes.py", "generate-alt-texts"),
    ("alt_text_routes.py", "scan-images"),
]

# Bewusst NICHT dahinter, mit Grund. Wer eine Zeile hier ergaenzt, muss den
# Grund mitschreiben; das ist der Zweck dieser Liste.
BEWUSST_OFFEN = {
    "public_routes.py": (
        "Die Erlaeuterung eines Befundes auf dem oeffentlichen Scanweg. Dort "
        "gibt es kein Konto, das eine Einstellung tragen koennte, und die "
        "Datenschutzerklaerung beschreibt genau diesen Vorgang fuer Besucher "
        "ohne Konto."
    ),
    "ai_fix_engine": (
        "Die Fix-Maschinen bekommen weder Konto noch Datenbankzugang "
        "durchgereicht. Bis das nachgezogen ist, gilt die Zusage fuer sie "
        "nicht, und das steht hier, damit es nicht in Vergessenheit geraet."
    ),
    "knowledge": (
        "Auswertung oeffentlicher Rechtsquellen. Es werden keine Kundendaten "
        "uebermittelt, also gibt es nichts abzuwaehlen."
    ),
}


def test_die_gemessenen_stellen_fragen_die_erlaubnis():
    fehlt = []
    gefunden = 0
    for datei, marke in HINTER_DER_SCHRANKE:
        quelle = _quelle(datei)
        if marke not in quelle:
            fehlt.append(f"{datei}: Stelle '{marke}' nicht mehr auffindbar")
            continue
        gefunden += 1
        # Die Abfrage muss VOR der Stelle stehen, nicht irgendwo in der Datei.
        i = quelle.index(marke)
        davor = quelle[max(0, i - 3000):i + 3000]
        if "darf_ki(" not in davor:
            fehlt.append(f"{datei}: '{marke}' ohne darf_ki() in der Naehe")

    assert gefunden == len(HINTER_DER_SCHRANKE), (
        f"Nur {gefunden} von {len(HINTER_DER_SCHRANKE)} Stellen gelesen. "
        "Ein Waechter, der seine Stellen nicht findet, prueft nichts."
    )
    assert not fehlt, (
        "Diese Stellen schicken Bilddaten einer Kundenseite an ein "
        "Sprachmodell, ohne das Konto zu fragen. Die Datenschutzerklaerung "
        "sagt aber zu, dass man die KI-Funktionen ungenutzt lassen kann: "
        + "; ".join(fehlt)
    )


def test_jede_offene_stelle_hat_einen_grund():
    """Die Gegenliste darf nicht zur Sammelstelle werden."""
    for stelle, grund in BEWUSST_OFFEN.items():
        assert len(grund) > 60, (
            f"'{stelle}' steht ohne tragfaehigen Grund in BEWUSST_OFFEN. "
            "Eine Ausnahme ohne Begruendung ist eine vergessene Luecke."
        )


def test_der_weg_zum_umschalten_existiert():
    quelle = _quelle("gdpr_api.py")
    assert '@gdpr_router.put("/ki-erlaubnis")' in quelle, (
        "Ohne Weg zum Umschalten ist die Spalte eine Behauptung. Genau das "
        "war der Zustand, den die Datenschutzerklaerung schon beschrieben hat."
    )
    assert '@gdpr_router.get("/ki-erlaubnis")' in quelle


def test_der_schalter_steht_auch_in_der_oberflaeche():
    """Eine Wahl, die nur ueber die Schnittstelle geht, ist fuer den Kunden keine.

    Der Test liegt hier und nicht bei den Oberflaechentests, weil er zur
    Zusage gehoert: die Datenschutzerklaerung sagt dem Kunden, er koenne die
    KI-Funktionen ungenutzt lassen, und der Kunde liest keine OpenAPI.
    """
    pfad = os.path.join(
        os.path.dirname(_BACKEND), "dashboard-react", "src", "app",
        "settings", "page.tsx",
    )
    if not os.path.exists(pfad):
        pytest.skip("dashboard-react nicht eingehaengt")
    with open(pfad, encoding="utf-8") as fh:
        quelle = fh.read()
    assert "/api/gdpr/ki-erlaubnis" in quelle, (
        "Die Einstellungsseite ruft die KI-Erlaubnis nicht mehr ab. Dann gibt "
        "es den Schalter im Backend, aber nicht fuer den Kunden."
    )
    assert "method: 'PUT'" in quelle or 'method: "PUT"' in quelle, (
        "Die Seite liest die Erlaubnis, setzt sie aber nicht."
    )


def test_was_der_weg_zurueckmeldet_stimmt_mit_der_schranke():
    """Die Aufzaehlung im Endpunkt darf nicht mehr versprechen als gebaut ist.

    Der Endpunkt nennt, was die Einstellung betrifft. Steht dort etwas, das
    nicht hinter der Schranke liegt, ist es wieder eine Zusage ohne
    Mechanismus.
    """
    quelle = _quelle("gdpr_api.py")
    marke = '"betrifft": ['
    i = quelle.index(marke) + len(marke)
    betrifft = quelle[i:quelle.index("]", i)]
    zeilen = re.findall(r'"([^"]{10,})"', betrifft)
    assert zeilen, "Die Aufzaehlung 'betrifft' ist leer."
    for zeile in zeilen:
        assert "Alt-Text" in zeile or "Vision" in zeile, (
            f"Der Endpunkt nennt '{zeile}' als betroffen. Hinter der Schranke "
            "liegen bisher nur die Alt-Text-Vorschlaege. Entweder die Stelle "
            "mit aufnehmen (HINTER_DER_SCHRANKE) oder die Aussage streichen."
        )


class TestDarfKi:
    class FakePool:
        def __init__(self, wert, wirft=False):
            self.wert = wert
            self.wirft = wirft
            self.abfragen = 0

        async def fetchval(self, frage, *args):
            self.abfragen += 1
            if self.wirft:
                raise RuntimeError("Datenbank weg")
            return self.wert

    def setup_method(self):
        ki_erlaubnis.vergessen()

    @pytest.mark.asyncio
    async def test_erlaubt(self):
        assert await ki_erlaubnis.darf_ki(self.FakePool(True), 7) is True

    @pytest.mark.asyncio
    async def test_abgeschaltet(self):
        assert await ki_erlaubnis.darf_ki(self.FakePool(False), 7) is False

    @pytest.mark.asyncio
    async def test_datenbankfehler_haelt_die_uebermittlung_an(self):
        """Anders als beim Budget gilt hier: im Zweifel nicht senden.

        Ein Budgetfehler kostet Geld, ein Erlaubnisfehler uebermittelt
        Kundendaten in ein Drittland. Das ist nicht dasselbe Risiko, also
        nicht dieselbe Richtung im Zweifel.
        """
        assert await ki_erlaubnis.darf_ki(self.FakePool(None, wirft=True), 7) is False

    @pytest.mark.asyncio
    async def test_unbekanntes_konto_haelt_die_uebermittlung_an(self):
        assert await ki_erlaubnis.darf_ki(self.FakePool(None), 999) is False

    @pytest.mark.asyncio
    async def test_ohne_konto_kein_kundenweg(self):
        assert await ki_erlaubnis.darf_ki(self.FakePool(True), None) is False

    @pytest.mark.asyncio
    async def test_zwischenspeicher_spart_abfragen_im_selben_scan(self):
        pool = self.FakePool(True)
        for _ in range(5):
            assert await ki_erlaubnis.darf_ki(pool, 7) is True
        assert pool.abfragen == 1

    @pytest.mark.asyncio
    async def test_umschalten_wirkt_sofort(self):
        """Ein Widerspruch, der eine Minute braucht, ist keiner.

        Der Kunde prueft die Wirkung in genau dieser Minute.
        """
        pool = self.FakePool(True)
        assert await ki_erlaubnis.darf_ki(pool, 7) is True
        ki_erlaubnis.vergessen(7)
        pool.wert = False
        assert await ki_erlaubnis.darf_ki(pool, 7) is False

    @pytest.mark.asyncio
    async def test_unbrauchbare_kontonummer(self):
        assert await ki_erlaubnis.darf_ki(self.FakePool(True), "kein-konto") is False
