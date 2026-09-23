"""Der Tarif folgt der Pflichtenlast, und zwar nachvollziehbar.

Der Preis war bisher der einzige Teil von complyo, der gesetzt statt gemessen
wurde. Diese Pruefungen halten fest, dass die Ableitung stimmt, dass die
Schwellen die gemessenen bleiben und dass die Empfehlung eine Empfehlung ist
und keine Schranke.

Die Archetypen unten sind aus der Vollzaehlung vom 23.09.2026 uebernommen
(20.480 plausible Profile durch den echten Katalog). Sie sind der Grund fuer
die Schwellen; wandern sie, muessen die Schwellen mitwandern, und dann soll
dieser Test anschlagen statt stillschweigend etwas anderes zu empfehlen.
"""
import pytest

from pflichten_katalog import evaluate_pflichten
from tarifempfehlung import (
    SCHLANK,
    SCHWELLE_VOLL,
    SCHWELLE_VOLL_PLUS,
    VOLL,
    VOLL_PLUS,
    empfehlung,
    punkte,
    stufe,
)

BOOL_FELDER = [
    "b2c", "online_shop", "digital_service", "uses_ai_chat", "uses_ai_decisions",
    "ai_generated_content", "sends_b2b_invoices", "sells_connected_products",
    "provides_cloud_service", "critical_sector", "newsletter",
]


def profil(**kw):
    p = {f: False for f in BOOL_FELDER}
    p["employees_data"] = True
    p.update(kw)
    return p


ARCHETYPEN = {
    "handwerk": (profil(employees="1-9", revenue="<=2m"), 4.0, SCHLANK),
    "praxis": (profil(employees="1-9", revenue="<=2m", b2c=True,
                      digital_service=True), 4.5, SCHLANK),
    "restaurant": (profil(employees="10-49", revenue="<=2m", b2c=True,
                          newsletter=True), 5.5, SCHLANK),
    "onlineshop": (profil(employees="10-49", revenue="2-10m", b2c=True,
                          online_shop=True, newsletter=True,
                          sends_b2b_invoices=True), 8.5, VOLL),
    "mittelstand": (profil(employees="50-249", revenue="10-50m", b2c=True,
                           online_shop=True, digital_service=True,
                           uses_ai_chat=True, ai_generated_content=True,
                           newsletter=True, sends_b2b_invoices=True,
                           sells_connected_products=True), 10.5, VOLL_PLUS),
}


@pytest.mark.parametrize("name", sorted(ARCHETYPEN))
def test_archetyp_landet_wo_gemessen(name):
    p, erwartete_punkte, erwartete_stufe = ARCHETYPEN[name]
    e = empfehlung(evaluate_pflichten(p))
    assert e["punkte"] == erwartete_punkte, (
        f"{name}: {e['punkte']} statt {erwartete_punkte} Punkte. Der Katalog hat "
        "sich geaendert. Die Schwellen in tarifempfehlung.py stammen aus diesen "
        "Zahlen und muessen dann neu gemessen werden.")
    assert e["stufe"] == erwartete_stufe


def test_die_luecke_zwischen_den_archetypen_bleibt():
    """Zwischen 5,5 und 8,5 lag bei der Messung nichts.

    Genau diese Luecke traegt die untere Schwelle. Rueckt ein Archetyp hinein,
    ist die Schwelle geraten statt gemessen.
    """
    werte = sorted(p for _, p, _ in ARCHETYPEN.values())
    unten = [w for w in werte if w < SCHWELLE_VOLL]
    oben = [w for w in werte if w >= SCHWELLE_VOLL]
    assert unten and oben, "Alle Archetypen auf einer Seite der Schwelle"
    assert max(unten) <= 5.5 and min(oben) >= 8.5, (
        f"Die Luecke ist zu: unten bis {max(unten)}, oben ab {min(oben)}. "
        "Schwelle neu messen.")


# ---------------------------------------------------------------------------
# Die Ableitung selbst
# ---------------------------------------------------------------------------
def test_check_zaehlt_halb():
    """Unsicherheit wird abgebildet, nicht aufgeloest."""
    assert punkte({"applies": 4, "check": 0}) == 4.0
    assert punkte({"applies": 4, "check": 1}) == 4.5
    assert punkte({"applies": 4, "check": 3}) == 5.5


def test_fehlende_zaehler_ergeben_null():
    assert punkte({}) == 0.0
    assert stufe(0.0) == SCHLANK


@pytest.mark.parametrize("wert,erwartet", [
    (SCHWELLE_VOLL - 0.5, SCHLANK),
    (SCHWELLE_VOLL, VOLL),
    (SCHWELLE_VOLL_PLUS - 0.5, VOLL),
    (SCHWELLE_VOLL_PLUS, VOLL_PLUS),
])
def test_schwellen_schliessen_nach_unten_ein(wert, erwartet):
    assert stufe(wert) == erwartet


# ---------------------------------------------------------------------------
# Was die Empfehlung ueber sich selbst sagen muss
# ---------------------------------------------------------------------------
def test_empfehlung_nennt_ihre_treiber():
    """Eine Zahl ohne Begruendung ist genau das, was das Produkt seinen Kunden
    nicht durchgehen laesst."""
    p, _, _ = ARCHETYPEN["onlineshop"]
    e = empfehlung(evaluate_pflichten(p))
    assert e["treiber"], "Empfehlung ohne tragende Pflichten"
    assert all(t["status"] in ("applies", "check") for t in e["treiber"])
    assert all(t["title"] for t in e["treiber"])


def test_treiber_stehen_nach_risiko():
    p, _, _ = ARCHETYPEN["onlineshop"]
    e = empfehlung(evaluate_pflichten(p))
    # Zutreffende vor zu pruefenden
    zustaende = [t["status"] for t in e["treiber"]]
    assert zustaende == sorted(zustaende, key=lambda s: 0 if s == "applies" else 1)


def test_empfehlung_sagt_dass_sie_keine_schranke_ist():
    p, _, _ = ARCHETYPEN["handwerk"]
    e = empfehlung(evaluate_pflichten(p))
    assert "Empfehlung" in e["grundlage"]
    assert "buchbar" in e["grundlage"]


def test_empfehlung_nennt_keine_preise():
    """Die Preisliste aendert sich, der Zusammenhang nicht.

    Stehen hier Betraege, ist das Modul am Tag der naechsten Preisrunde falsch,
    ohne dass es jemand merkt.
    """
    import tarifempfehlung
    quelle = open(tarifempfehlung.__file__, encoding="utf-8").read()
    import re
    betraege = re.findall(r"\b\d{2,4}\s*(?:€|EUR|Euro)", quelle)
    assert not betraege, f"Preise im Modul: {betraege}"


def test_mehrere_websites_verweisen_auf_die_zweite_dimension():
    p, _, _ = ARCHETYPEN["handwerk"]
    e = empfehlung(evaluate_pflichten(p), websites=25)
    assert any("Projekte" in h for h in e["hinweise"]), (
        "Bei vielen Websites muss die Empfehlung sagen, dass die Pflichtenlast "
        "nicht die entscheidende Groesse ist.")


def test_gekuerzter_report_ergibt_dieselbe_punktzahl():
    """Im Free-Tarif sind die Posten gekuerzt, die Zaehler nicht.

    Sonst saehe ein Interessent eine kleinere Pflichtenlast als er hat, und der
    Report wuerde ausgerechnet dort untertreiben, wo er ueberzeugen soll.
    """
    p, erwartet, _ = ARCHETYPEN["mittelstand"]
    voll = evaluate_pflichten(p)
    gekuerzt = dict(voll)
    gekuerzt["items"] = voll["items"][:3]
    gekuerzt["locked"] = True
    assert empfehlung(gekuerzt)["punkte"] == erwartet
    assert any("Free-Tarif" in h for h in empfehlung(gekuerzt)["hinweise"])
