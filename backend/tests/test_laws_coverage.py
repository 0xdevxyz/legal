"""
Gesetzes-Abdeckung des Rechtstext-Generators
=============================================

Hintergrund (2026-07-17): `generate_withdrawal` fordert über
`_load_laws_context([...])` die Gesetze *Widerrufsrecht*, *Verbraucherrecht* und
*AGB-Recht* an — die ersten beiden Wissensdateien fehlten jedoch im Vault. Ein
fehlendes Gesetz löst KEINEN Fehler aus: `_load_laws_context` überspringt es
still, und der Rechtstext entsteht ohne diesen Kontext. Beim Widerruf-Dokument
landete so ausgerechnet das Widerrufsrecht nicht im Prompt.

Dieser Test schließt die Lücke dauerhaft: Für JEDEN Dokumenttyp muss jedes im
Generator-Code angeforderte Gesetz als Datei im Vault existieren. Die
Gesetz-Zuordnung wird per AST direkt aus `legal_text_generator.py` gelesen
(nicht hartkodiert), damit eine neue `_load_laws_context([...])`-Anforderung
automatisch mitgeprüft wird.

Läuft im Backend-Container (`docker exec complyo-backend python -m pytest`).
"""
import ast
import inspect
import os

import pytest

ltg = pytest.importorskip("legal_text_generator")


def _requested_laws_from_source() -> list[str]:
    """Extrahiert alle in `_load_laws_context([...], ...)` angeforderten Gesetzes-
    namen aus dem Quelltext des Generators (String-Literale im ersten Argument).

    Bewusst quellcode-getrieben statt hartkodiert: Wird ein Dokumenttyp um ein
    weiteres Gesetz erweitert, prüft dieser Test es ohne Anpassung mit.
    """
    source = inspect.getsource(ltg)
    tree = ast.parse(source)
    laws: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name != "_load_laws_context":
            continue
        if not node.args:
            continue
        first = node.args[0]
        if not isinstance(first, (ast.List, ast.Tuple)):
            continue
        for elt in first.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                laws.append(elt.value)
    return laws


def _law_file_exists(name: str, language: str = "de") -> bool:
    """Spiegelt die Suchlogik von `_load_laws_context`: {lang}/, de/, Wurzel."""
    candidates = [
        os.path.join(ltg.LAWS_DIR, language, f"{name}.md"),
        os.path.join(ltg.LAWS_DIR, "de", f"{name}.md"),
        os.path.join(ltg.LAWS_DIR, f"{name}.md"),
    ]
    return any(os.path.exists(p) for p in candidates)


def test_mindestens_ein_gesetz_wird_angefordert():
    """Sanity: Die AST-Extraktion findet überhaupt Anforderungen."""
    laws = _requested_laws_from_source()
    assert laws, "Keine _load_laws_context([...])-Aufrufe im Generator gefunden — Extraktion defekt?"


@pytest.mark.parametrize("gesetz", sorted(set(_requested_laws_from_source())))
def test_angefordertes_gesetz_existiert_im_vault(gesetz):
    """Jedes vom Generator angeforderte Gesetz muss als Wissensdatei existieren —
    sonst geht der Kontext beim betroffenen Dokument still verloren."""
    assert _law_file_exists(gesetz), (
        f"Gesetz '{gesetz}' wird vom Generator angefordert, aber "
        f"'{gesetz}.md' existiert weder in {ltg.LAWS_DIR}, noch in de/ oder der Sprachvariante. "
        f"_load_laws_context überspringt es still — der Rechtstext entsteht ohne diesen Kontext."
    )


def test_alle_angeforderten_gesetze_liefern_kontext():
    """Aggregat-Sicht: kein stiller Kontext-Verlust über alle Dokumenttypen."""
    fehlend = sorted({g for g in _requested_laws_from_source() if not _law_file_exists(g)})
    assert not fehlend, f"Fehlende Gesetzes-Wissensdateien im Vault: {fehlend}"
