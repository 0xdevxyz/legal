"""Genau eine Seite ist die Startseite, und genau die ist indexierbar.

Am 02.09.2026 ist die Kampagnenseite auf "/" gezogen, die Produktseite nach
/produkt. Beim Verschieben mussten `noindex` und `canonical` zwingend
mitgezogen werden: die Kampagnenseite trug beides auf sich selbst, und
unveraendert auf "/" gelegt haette das complyo.de aus dem Index genommen.

Sobald Stripe auf Live-Schluessel steht, wird zurueckgetauscht - /produkt
gehoert dann wieder auf "/". Dabei droht derselbe Fehler in die andere
Richtung: wer nur die Komponente tauscht und die Metadaten vergisst, setzt
entweder die Startseite auf noindex oder laesst zwei Seiten um dieselben
Begriffe konkurrieren, mit canonical-Angaben, die aufeinander zeigen.

Dieser Test prueft die Invariante, nicht den Zustand: welche Komponente auf
"/" liegt, ist ihm gleich. Er besteht auch nach dem Rueckbau.
"""

import os
import re

import pytest

# ACHTUNG ZUM AUSFUEHREN: unter dem sonst ueblichen Aufruf
#     docker run -v $(pwd)/backend:/app -w /app ...
# ist landing-react nicht gemountet, und diese Tests werden UEBERSPRUNGEN -
# ein uebersprungener Test bewacht nichts. Damit sie greifen:
#     docker run -v $(pwd):/repo -w /repo/backend ... python3 -m pytest tests/
# oder COMPLYO_LANDING_SRC auf das app-Verzeichnis der Landing zeigen lassen.
LANDING = os.path.abspath(
    os.getenv("COMPLYO_LANDING_SRC")
    or os.path.join(os.path.dirname(__file__), "..", "..", "landing-react", "src", "app")
)

SEITEN = {
    "/": "page.tsx",
    "/produkt/": os.path.join("produkt", "page.tsx"),
    "/early-access/": os.path.join("early-access", "page.tsx"),
}


def _quelle(relpfad):
    pfad = os.path.join(LANDING, relpfad)
    if not os.path.exists(pfad):
        pytest.skip(
            f"{relpfad} nicht gefunden unter {LANDING}. Diese Pruefung braucht das "
            "Repo-Wurzelverzeichnis im Container (-v $(pwd):/repo -w /repo/backend) "
            "oder COMPLYO_LANDING_SRC."
        )
    return open(pfad, encoding="utf-8").read()


def _indexierbar(text):
    m = re.search(r"robots:\s*\{[^}]*index:\s*(true|false)", text)
    assert m, "robots.index ist nicht gesetzt - der Standard waere indexierbar"
    return m.group(1) == "true"


def _canonical(text):
    m = re.search(r"canonical:\s*['\"]([^'\"]+)['\"]", text)
    assert m, "alternates.canonical fehlt"
    return m.group(1)


class TestIndexierung:
    def test_genau_eine_seite_ist_indexierbar(self):
        indexierbar = [
            pfad for pfad, datei in SEITEN.items() if _indexierbar(_quelle(datei))
        ]
        assert indexierbar == ["/"], (
            f"Indexierbar sind: {indexierbar}. Es darf genau die Startseite sein - "
            "zwei indexierbare Seiten konkurrieren um dieselben Begriffe, keine "
            "nimmt complyo.de aus der Suche."
        )

    def test_jede_seite_zeigt_kanonisch_auf_sich_selbst(self):
        for pfad, datei in SEITEN.items():
            assert _canonical(_quelle(datei)) == pfad, (
                f"{datei} hat canonical != {pfad}. Genau dieser Fehler haette beim "
                "Verschieben am 02.09. die Startseite aus dem Index genommen."
            )

    def test_kampagnenseite_bleibt_auf_noindex(self):
        """Bezahlter Traffic braucht keine Suchsichtbarkeit, aber der
        Preisvorteil soll nicht ueber die Suche allgemein auffindbar sein."""
        assert not _indexierbar(_quelle(SEITEN["/early-access/"]))


class TestKampagnenkennung:
    def test_jede_einstiegsseite_traegt_eine_eigene_kennung(self):
        """Ohne getrennte Kennung ist bezahlter nicht von organischem Traffic
        zu trennen - dann misst die Kampagne sich selbst."""
        start = _quelle(SEITEN["/"])
        kampagne = _quelle(SEITEN["/early-access/"])

        kennungen = {}
        for name, text in (("start", start), ("early-access", kampagne)):
            treffer = re.findall(r"kampagne=[\"']([^\"']+)[\"']|kampagne=\{[\"']([^\"']+)[\"']\}", text)
            flach = {a or b for a, b in treffer}
            assert flach, f"{name}: keine Kampagnenkennung gefunden"
            kennungen[name] = flach

        assert kennungen["start"].isdisjoint(kennungen["early-access"]), (
            f"Beide Seiten benutzen dieselbe Kennung: {kennungen}"
        )
