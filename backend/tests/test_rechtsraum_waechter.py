"""Kein deutsches Gesetz in einer Pruefung, die auch ausserhalb Deutschlands laeuft.

Der Waechter leitet seine Zustaendigkeit aus `jurisdictions.py` ab, statt eine
Liste von Dateien zu pflegen. Sobald ein Profil ausserhalb von `de` eine
weitere Pruefung aktiviert, faellt deren Datei automatisch unter diese
Pruefung. Eine handgepflegte Ausnahmeliste waere genau die Sorte Wissen, die
beim naechsten Profil vergessen wird.

Warum es ihn braucht
--------------------
Gezaehlt am 23.09.2026, vor Block 0: 158 ausgegebene Nennungen deutscher
Gesetze im Pruefkern, 67 davon BFSG, verteilt auf 20 Dateien. Weil die Engine
den Rechtsraum nicht las, haette ein niederlaendischer Kunde Befunde bekommen,
die ihm die Verletzung des deutschen Barrierefreiheitsstaerkungsgesetzes
vorwerfen. Nicht auffaellig genug, um einen Fehler zu melden, aber genug, um
einen Fachkundigen das ganze Ergebnis verwerfen zu lassen.

Was der Waechter NICHT prueft
-----------------------------
Nur `legal_basis`. Titel, Beschreibungen und Empfehlungen nennen weiterhin
deutsche Gesetze im Fliesstext ("Barrierefreiheitserklaerung fehlt (BFSG
§14)"). Das ist Block 3, der Textkatalog mit stabilen Befundcodes. Damit diese
Menge nicht unbemerkt wieder waechst, gibt es daneben die Bestandsaufnahme:
eine Zahl, die nur sinken darf.

Erkennungsmuster bleiben ausgenommen. `deep_content_analyzer.py` sucht auf
deutschen Seiten nach "Angaben gemaess § 5 TMG" und muss das auch weiterhin
duerfen; wer diese Zeichenkette uebersetzt, macht den Impressum-Check blind.
"""
import ast
import io
import pathlib
import re
import tokenize
from collections import Counter

import pytest

from compliance_engine.jurisdictions import JURISDICTION_PROFILES

KERN = pathlib.Path(__file__).resolve().parent.parent / "compliance_engine"
TABELLE = "rechtsgrundlagen.py"

NORM = re.compile(r"\b(DDG|TMG|TTDSG|TDDDG|UWG|PAngV|BGB|BFSG|EGBGB|HGB|MStV|GewO|RStV)\b")

# Welche Dateien eine Pruefung ausmachen. Mehrere Dateien je Pruefung sind der
# Normalfall: die Barrierefreiheit verteilt sich auf vier.
DATEIEN_JE_PRUEFUNG = {
    "datenschutz": ["checks/datenschutz_check.py"],
    "cookie": ["checks/cookie_check.py"],
    "tcf": ["checks/tcf_check.py"],
    "barrierefreiheit": [
        "checks/barrierefreiheit_check.py",
        "checks/aria_checker.py",
        "checks/media_accessibility_check.py",
        "axe_scanner.py",
    ],
    "impressum": ["checks/impressum_check.py"],
    "agb": ["checks/agb_check.py"],
    "uwg": ["checks/uwg_check.py"],
    "pangv": ["checks/shop_check.py"],
    "widerruf": ["checks/shop_check.py"],
}

# Erkennungsmuster und Modellanweisungen, nicht Ausgabe an den Kunden.
KEINE_AUSGABE = {
    # Sucht auf deutschen Seiten nach der Impressum-Ueberschrift. Uebersetzen
    # hiesse den Check blind machen.
    "deep_content_analyzer.py",
    # Anweisungen an das Sprachmodell. Jurisdiction-abhaengig zu machen ist
    # richtig, gehoert aber zu Block 3; die Ausgabe laeuft ohnehin durch das
    # Qualitaetsgate und die Freigabe.
    "bfsg_prompts.py",
}


def _pruefungen_ausserhalb_de():
    aktiv = set()
    for name, profil in JURISDICTION_PROFILES.items():
        if name == "de":
            continue
        aktiv.update(profil["checks"])
    return aktiv


def _legal_basis_werte(pfad: pathlib.Path):
    """Alle Werte, die als legal_basis beim Kunden landen koennen."""
    baum = ast.parse(pfad.read_text(encoding="utf-8"))
    werte = []

    def roh(knoten):
        if isinstance(knoten, ast.Constant) and isinstance(knoten.value, str):
            return [(knoten.lineno, knoten.value)]
        if isinstance(knoten, ast.JoinedStr):
            text = "".join(t.value for t in knoten.values
                           if isinstance(t, ast.Constant) and isinstance(t.value, str))
            return [(knoten.lineno, text)]
        if isinstance(knoten, ast.IfExp):
            return roh(knoten.body) + roh(knoten.orelse)
        if isinstance(knoten, ast.BinOp):  # 'x' + grundlage(...) + 'y'
            return roh(knoten.left) + roh(knoten.right)
        return []

    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Dict):
            for s, w in zip(knoten.keys, knoten.values):
                if isinstance(s, ast.Constant) and s.value == "legal_basis":
                    werte += roh(w)
        elif isinstance(knoten, ast.keyword) and knoten.arg == "legal_basis":
            werte += roh(knoten.value)
    return werte


@pytest.mark.parametrize("pruefung", sorted(_pruefungen_ausserhalb_de()))
def test_pruefung_ausserhalb_de_nennt_kein_deutsches_gesetz(pruefung):
    dateien = DATEIEN_JE_PRUEFUNG.get(pruefung)
    assert dateien, (
        f"Die Pruefung {pruefung!r} laeuft laut jurisdictions.py ausserhalb "
        f"Deutschlands, aber dieser Waechter weiss nicht, in welcher Datei sie "
        f"steht. Eintrag in DATEIEN_JE_PRUEFUNG ergaenzen.")

    fehler = []
    for rel in dateien:
        p = KERN / rel
        if not p.exists():
            fehler.append(f"{rel}: Datei fehlt")
            continue
        for zeile, wert in _legal_basis_werte(p):
            treffer = set(NORM.findall(wert))
            if treffer:
                fehler.append(f"{rel}:{zeile} nennt {', '.join(sorted(treffer))}: {wert!r}")

    assert not fehler, (
        f"Die Pruefung {pruefung!r} laeuft auch ausserhalb Deutschlands und gibt "
        f"trotzdem deutsche Gesetze als Rechtsgrundlage aus:\n  "
        + "\n  ".join(fehler)
        + "\n\nRichtiger Weg: compliance_engine.rechtsgrundlagen.grundlage(THEMA, "
          "jurisdiction, detail=...). Die Tabelle dort haelt den nationalen Anker."
    )


# ---------------------------------------------------------------------------
# Bestandsaufnahme: eine Zahl, die nur sinken darf
# ---------------------------------------------------------------------------
#
# Stand nach Block 0, gemessen am 23.09.2026. Titel, Beschreibungen und
# Empfehlungen nennen weiterhin deutsche Gesetze; das raeumt Block 3 mit dem
# Textkatalog aus. Bis dahin haelt diese Grenze fest, dass die Menge nicht
# wieder waechst. Wer sie senkt, senkt auch diese Zahl.
DECKEL = 110


def _ausgegebene_normnennungen():
    zaehler = Counter()
    je_datei = Counter()
    for p in sorted(KERN.rglob("*.py")):
        if ".bak" in p.name or "__pycache__" in str(p):
            continue
        if p.name == TABELLE or p.name in KEINE_AUSGABE:
            continue
        quelle = p.read_text(encoding="utf-8")
        try:
            baum = ast.parse(quelle)
        except SyntaxError:
            continue

        doczeilen = set()
        for knoten in ast.walk(baum):
            if isinstance(knoten, (ast.Module, ast.FunctionDef,
                                   ast.AsyncFunctionDef, ast.ClassDef)):
                erstes = knoten.body[0] if knoten.body else None
                if (isinstance(erstes, ast.Expr)
                        and isinstance(erstes.value, ast.Constant)
                        and isinstance(erstes.value.value, str)):
                    doczeilen.update(
                        range(erstes.lineno, (erstes.end_lineno or erstes.lineno) + 1))

        for knoten in ast.walk(baum):
            if isinstance(knoten, ast.Constant) and isinstance(knoten.value, str):
                if knoten.lineno in doczeilen:
                    continue
                for n in NORM.findall(knoten.value):
                    zaehler[n] += 1
                    je_datei[p.name] += 1
            elif isinstance(knoten, ast.JoinedStr):
                text = "".join(t.value for t in knoten.values
                               if isinstance(t, ast.Constant) and isinstance(t.value, str))
                for n in NORM.findall(text):
                    zaehler[n] += 1
                    je_datei[p.name] += 1
    return zaehler, je_datei


def test_deutsche_normnennungen_wachsen_nicht_nach():
    zaehler, je_datei = _ausgegebene_normnennungen()
    gesamt = sum(zaehler.values())
    aufstellung = "\n  ".join(f"{d}: {n}" for d, n in je_datei.most_common())
    assert gesamt <= DECKEL, (
        f"Im Pruefkern stehen {gesamt} ausgegebene Nennungen deutscher Gesetze, "
        f"erlaubt sind {DECKEL}.\n  {aufstellung}\n\n"
        "Neue deutsche Normnamen gehoeren nicht in den Quelltext, sondern als "
        "Anker in compliance_engine/rechtsgrundlagen.py."
    )


def test_der_deckel_ist_nicht_zu_locker():
    """Ein Deckel weit ueber dem Ist-Stand bewacht nichts.

    Faellt die Zahl durch Block 3 deutlich, muss DECKEL mitwandern. Sonst
    koennte jemand unbemerkt wieder zwanzig Nennungen einbauen.
    """
    zaehler, _ = _ausgegebene_normnennungen()
    gesamt = sum(zaehler.values())
    assert gesamt >= DECKEL - 10, (
        f"Nur noch {gesamt} Nennungen, der Deckel steht auf {DECKEL}. "
        "Bitte DECKEL auf den neuen Stand senken.")


def test_erkennungsmuster_bleiben_deutsch():
    """Die Gegenprobe: was NICHT uebersetzt werden darf, ist noch da.

    deep_content_analyzer.py sucht nach der deutschen Impressum-Ueberschrift.
    Wer dort TMG und DDG entfernt, macht den Check blind, ohne dass ein Test
    anschlaegt, weil dann einfach nichts mehr gefunden wird.
    """
    p = KERN / "checks" / "deep_content_analyzer.py"
    if not p.exists():
        pytest.skip("deep_content_analyzer.py nicht vorhanden")
    quelle = p.read_text(encoding="utf-8")
    assert "TMG" in quelle and "DDG" in quelle, (
        "Das Erkennungsmuster fuer die Impressum-Ueberschrift nennt TMG/DDG "
        "nicht mehr. Deutsche Seiten schreiben 'Angaben gemaess § 5 TMG'; ohne "
        "das Muster findet der Check das Impressum nicht mehr.")
