"""
Härtungs-Wächter: Rate-Limits auf teuren Pfaden + keine Fehler-Detail-Leaks
===========================================================================

Launch-Plan Punkte 1.3 (Fehler-Detail-Leaks) und 1.4 (Rate-Limiting).

Rein statische Wächter über den Quelltext — brauchen weder fastapi noch DB,
laufen daher unabhängig von der übrigen Test-Infrastruktur.

1. Kein `detail=str(e)` / `detail=f"...{e}..."` mehr in den gehärteten Dateien
   (Wächter gegen Rückfall — interne Exception-Texte dürfen nicht mehr an den
   Client geleakt werden).
2. Die teuren KI-/Scan-/PDF-Endpunkte tragen ein Rate-Limit (Redis-`rate_limit(...)`
   oder slowapi-`@limiter.limit`), oder sind in einer begründeten Allowlist gelistet.
3. Negativkontrolle: die Leak-Erkennung schlägt bei einem synthetischen Leak an.
"""
import os
import re

import pytest

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _quelltext(dateiname: str) -> str:
    with open(os.path.join(_BACKEND, dateiname), encoding="utf-8") as fh:
        return fh.read()


def _quelltext_ohne_kommentare(dateiname: str) -> str:
    """Kommentare/Docstrings dürfen die statischen Wächter nicht triggern."""
    src = _quelltext(dateiname)
    src = re.sub(r'"""(?:.|\n)*?"""', "", src)
    src = re.sub(r"'''(?:.|\n)*?'''", "", src)
    return "\n".join(re.sub(r"#.*$", "", z) for z in src.splitlines())


# --- Leak-Erkennung -------------------------------------------------------

# Trifft `detail=str(e)` sowie `detail=f"...{e}..."` / `{str(e)}` / `{type(e)...}`.
_LEAK_STR_E = re.compile(r"detail\s*=\s*str\(\s*e\s*\)")
_LEAK_FSTRING = re.compile(
    r'detail\s*=\s*f["\'][^"\']*\{[^}]*(?:\be\b|str\(\s*e\s*\)|type\(\s*e\s*\))[^}]*\}'
)


def _finde_leaks(quelltext: str):
    treffer = []
    for nr, zeile in enumerate(quelltext.splitlines(), start=1):
        if _LEAK_STR_E.search(zeile) or _LEAK_FSTRING.search(zeile):
            treffer.append((nr, zeile.strip()))
    return treffer


# Dateien, deren Fehler-Detail-Leaks in dieser Härtung geschlossen wurden.
_LEAK_GEHAERTETE_DATEIEN = [
    "cookie_compliance_routes.py",  # Zusatzmodule geo/forwarding/age/tcf/import etc.
    "main_production.py",           # Audit-Log SELECT/Export
    "user_routes.py",               # Profil-Update (bereits generisch)
]


@pytest.mark.parametrize("dateiname", _LEAK_GEHAERTETE_DATEIEN)
def test_keine_error_detail_leaks(dateiname):
    """Gehärtete Dateien geben keine internen Exception-Texte mehr an den Client."""
    leaks = _finde_leaks(_quelltext_ohne_kommentare(dateiname))
    assert not leaks, (
        f"{dateiname}: interne Fehler-Details werden an den Client geleakt: {leaks}"
    )


def test_negativkontrolle_leak_erkennung():
    """Die Leak-Erkennung muss synthetische Leaks zuverlässig fangen."""
    synthetisch = "\n".join([
        '        raise HTTPException(status_code=500, detail=str(e))',
        '        raise HTTPException(status_code=500, detail=f"boom: {e}")',
        '        raise HTTPException(status_code=500, detail=f"x {str(e)}")',
        '        raise HTTPException(status_code=500, detail=f"y {type(e).__name__}")',
    ])
    assert len(_finde_leaks(synthetisch)) == 4
    # Generische Meldungen dürfen NICHT anschlagen (kein False Positive).
    sauber = "\n".join([
        '        raise HTTPException(status_code=500, detail="Interner Fehler")',
        '        raise HTTPException(status_code=400, detail=f"Ungültiger Typ: {feld}")',
    ])
    assert _finde_leaks(sauber) == []


# --- Rate-Limit-Wächter ---------------------------------------------------

def _throttle_im_umfeld(dateiname: str, pfad_literal: str, fenster: int = 4) -> bool:
    """
    True, wenn im Umfeld (± `fenster` Zeilen) der Route-Definition ein Rate-Limit
    steht — entweder Redis-`rate_limit(...)` oder slowapi-`@limiter.limit`.
    """
    zeilen = _quelltext(dateiname).splitlines()
    idx = [i for i, z in enumerate(zeilen) if pfad_literal in z and "router" in z.lower() or (pfad_literal in z and "@app." in z)]
    assert idx, f"{dateiname}: Route {pfad_literal!r} nicht gefunden"
    for i in idx:
        lo, hi = max(0, i - fenster), min(len(zeilen), i + fenster + 1)
        umfeld = "\n".join(zeilen[lo:hi])
        if "rate_limit(" in umfeld or "@limiter.limit" in umfeld:
            return True
    return False


# Teure Endpunkte, die ein Rate-Limit tragen MÜSSEN. (datei, pfad-literal)
_GEDROSSELTE_ENDPUNKTE = [
    # KI-Generierung
    ("legal_text_routes.py", '"/{doc_type}/generate"'),
    ("fix_routes.py", '"/generate"'),                       # slowapi @limiter.limit
    ("fix_apply_routes.py", '"/apply"'),
    ("fix_apply_routes.py", '"/apply/preview"'),
    ("alt_text_routes.py", '"/generate-alt-texts"'),
    ("ai_compliance_routes.py", '"/systems/{system_id}/documentation/generate"'),
    ("ai_legal_routes.py", '"/updates/{update_id}/classify"'),
    ("ai_legal_routes.py", '"/generate-impressum"'),
    ("ai_legal_routes.py", '"/generate-datenschutz"'),
    # PDF-Export
    ("main_production.py", '"/api/v2/reports/{scan_id}/download"'),
    # Scan
    ("public_routes.py", '"/analyze-preview"'),
    ("main_production.py", '"/api/v2/analyze"'),
    ("main_production.py", '"/api/v2/analyze/quick"'),
    ("main_production.py", '"/api/v2/analyze/complete"'),
]

# Begründete Allowlist: teure Endpunkte, die BEWUSST kein Rate-Limit tragen.
# (Format: (datei, pfad, begründung)). Aktuell leer — jeder gelistete teure
# Endpunkt ist gedrosselt. Öffentliche Besucher-Endpunkte mit legitimem
# Hochlast-Traffic (z. B. POST /consent) sind hier absichtlich NICHT als
# "teure KI/Scan/PDF-Pfade" geführt und haben eigene, angepasste Limits.
_ALLOWLIST_UNGEDROSSELT: list = []


@pytest.mark.parametrize("dateiname,pfad", _GEDROSSELTE_ENDPUNKTE)
def test_teure_endpunkte_gedrosselt(dateiname, pfad):
    """Jeder teure KI-/Scan-/PDF-Endpunkt trägt ein Rate-Limit."""
    assert _throttle_im_umfeld(dateiname, pfad), (
        f"{dateiname}: teurer Endpunkt {pfad} ist NICHT rate-limitiert "
        f"(weder rate_limit(...) noch @limiter.limit im Umfeld)"
    )


def test_allowlist_konsistent():
    """Allowlist-Einträge sind vollständig begründet (datei, pfad, begründung)."""
    for eintrag in _ALLOWLIST_UNGEDROSSELT:
        assert len(eintrag) == 3 and all(eintrag), f"Unvollständiger Allowlist-Eintrag: {eintrag}"
