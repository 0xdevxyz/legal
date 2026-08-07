"""
Auth-Tests für admin_routes
===========================

Befund (2026-07-29): Der Adminbereich lief über einen gemeinsamen Schlüssel,
der als **Query-Parameter** übergeben wurde (`?api_key=...`). Drei Probleme:

1. Der Schlüssel landete in nginx-Access-Logs, Browser-History und
   Referer-Headern jeder verlinkten Ressource.
2. Im Dashboard stand er als `NEXT_PUBLIC_ADMIN_API_KEY` — durch das
   `NEXT_PUBLIC_`-Präfix hätte Next.js ihn in das ausgelieferte JS-Bundle
   gebacken und damit an jeden Besucher ausgeliefert.
3. Er wurde als `reviewed_by` in `fix_application_audit` geschrieben, stand also
   im Klartext in der Datenbank — und ein Audit-Eintrag benannte damit keine
   Person, sondern ein Geheimnis.

Umgestellt auf die rollenbasierte Dependency `require_admin` (JWT + users.role),
die im Projekt bereits von ai_legal_routes, cookie_compliance_routes,
legal_change_routes und i18n_api genutzt wird.

Der Test ist ein statischer Wächter über den Quelltext — er braucht weder
fastapi noch DB und schlägt an, sobald eine Route ohne Schutz hinzukommt.
"""
import os
import re

import pytest

_ROUTES_FILE = os.path.join(os.path.dirname(__file__), "..", "admin_routes.py")
_PAGE_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "dashboard-react", "src", "app", "admin", "fix-review", "page.tsx",
)

# Erfasst ein- UND mehrzeilige Signaturen. Die innere Alternative laesst eine
# Klammerebene zu (Depends(...), Query(...)), sonst bricht die Erkennung bei
# einzeiligen Koepfen wie `async def f(admin: dict = Depends(require_admin)):`.
_ROUTE_PATTERN = re.compile(
    r'@admin_router\.(get|post|patch|delete|put)\("([^"]*)"\)\s*\n'
    r'async def (\w+)\(((?:[^()]|\([^()]*\))*)\)\s*:',
    re.S,
)


def _quelltext(pfad: str) -> str:
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


def _routen():
    src = _quelltext(_ROUTES_FILE)
    for m in _ROUTE_PATTERN.finditer(src):
        methode, pfad, fn, signatur = m.group(1), m.group(2), m.group(3), m.group(4)
        yield methode.upper(), pfad, fn, "require_admin" in signatur


class TestAdminRouten:
    def test_routen_werden_erkannt(self):
        """Findet der Regex nichts, sind alle folgenden Tests wertlos."""
        assert len(list(_routen())) >= 10

    def test_jede_route_verlangt_require_admin(self):
        offen = {f"{m} {p}" for m, p, _, geschuetzt in _routen() if not geschuetzt}
        assert not offen, (
            "Admin-Route(n) ohne require_admin: " + ", ".join(sorted(offen))
        )

    def test_kein_shared_secret_mehr(self):
        """Weder Env-Schlüssel noch die alte Query-Prüfung dürfen zurückkehren."""
        src = _quelltext(_ROUTES_FILE)
        # Kommentare ausblenden — die Begründung nennt die alten Namen bewusst.
        code = "\n".join(re.sub(r"#.*$", "", z) for z in src.splitlines())
        for verboten in ("_ADMIN_API_KEY", "verify_admin_access", 'alias="api_key"'):
            assert verboten not in code, (
                f"{verboten} ist zurück in admin_routes.py — "
                "der Adminbereich soll über require_admin laufen"
            )

    def test_reviewer_ist_eine_person_kein_schluessel(self):
        """reviewed_by muss den angemeldeten Admin benennen."""
        src = _quelltext(_ROUTES_FILE)
        assert "_reviewer_name(admin)" in src
        assert src.count("reviewer,\n            fix_id,") == 2, (
            "Approve und Reject sollen beide den Reviewer-Namen schreiben"
        )


class TestFixReviewSeite:
    """Das Frontend darf den Schlüssel nicht wieder ins Bundle holen."""

    @pytest.mark.skipif(
        not os.path.exists(_PAGE_FILE), reason="Dashboard-Quelltext nicht im Container"
    )
    def test_kein_public_admin_key_im_frontend(self):
        # Kommentare ausblenden — wie beim Backend-Pendant oben. Die Begruendung
        # im Quelltext nennt den alten Variablennamen absichtlich; ohne diese
        # Zeile schlaegt der Waechter an der eigenen Erklaerung an.
        src = "\n".join(
            re.sub(r"//.*$", "", z) for z in _quelltext(_PAGE_FILE).splitlines()
        )
        assert "NEXT_PUBLIC_ADMIN_API_KEY" not in src, (
            "NEXT_PUBLIC_-Variablen landen im ausgelieferten JS-Bundle — "
            "ein Admin-Schlüssel gehört dort niemals hin"
        )
        assert "api_key=" not in src, (
            "Der Schlüssel darf nicht wieder als Query-Parameter in die URL"
        )
