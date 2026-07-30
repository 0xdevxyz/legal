"""
Auth-/Ownership-Tests für lead_routes und alt_text_routes
=========================================================

Hintergrund (2026-07-17), analog zum Cookie-Router:

* `GET /api/leads/stats` gab Lead-Geschäftszahlen ohne jede Auth heraus
  ("public ... for transparency"). Jetzt Admin-only.
* `POST /api/leads/unsubscribe` nahm eine beliebige E-Mail entgegen — jeder
  konnte jeden abmelden. Jetzt HMAC-Token Pflicht (Muster wie /verify/{token}).
* Die A11y-Routen waren zwar authentifiziert, prüften die `site_id` aber nie —
  ein eingeloggter User kam an die Review-Queues/Worklist FREMDER Sites.
* `GET /api/accessibility/patches/download/{download_id}` (in widget_routes.py)
  hatte keine Auth bei erratbarer download_id ("{site_id}_{unix_ts}").

Zwei Ebenen (wie tests/test_cookie_consent_auth.py):
1. Statische Wächter über den Quelltext — brauchen weder fastapi noch DB und
   schlagen an, sobald eine NEUE Route ohne Auth hinzukommt.
2. Unit-Tests des tatsächlichen Verhaltens (403-Pfade) via monkeypatch.
"""
import ast
import contextlib
import importlib
import inspect
import os
import re
import sys
from unittest.mock import MagicMock

import pytest

_BACKEND = os.path.join(os.path.dirname(__file__), "..")
# Wurzel des Anwendungscodes (im Container /app) — siehe _sauberes_sys_modules.
_APP_DIR = os.path.realpath(_BACKEND) + os.sep
_LEAD_FILE = os.path.join(_BACKEND, "lead_routes.py")
_ALT_TEXT_FILE = os.path.join(_BACKEND, "alt_text_routes.py")
_WIDGET_FILE = os.path.join(_BACKEND, "widget_routes.py")

# Routen, die ein Website-BESUCHER / die Landingpage ohne Complyo-Login
# erreichen muss. NICHTS hier eintragen, das Kundendaten liest.
LEADS_OEFFENTLICH_GEWOLLT = {
    # Landing-Formular (landing-react/src/lib/api.ts:120). Double-Opt-In +
    # Rate-Limit + Honeypot schützen; ein Login gibt es hier naturgemäss nicht.
    "/waitlist",
    # Bestätigungslink aus der Opt-In-Mail. Der Token IST die Auth.
    "/waitlist/confirm",
    # Landing-Formular: Lead + Analysedaten, Double-Opt-In folgt per Mail.
    "/collect",
    # Verifizierungslink aus der Mail. Der Token IST die Auth.
    "/verify/{token}",
    # Abmeldelink aus der Mail. Kein Login, aber seit 2026-07-17 HMAC-Token
    # Pflicht (siehe TestUnsubscribeToken) — deshalb hier vertretbar.
    "/unsubscribe",
}

# Die A11y-Routen sind allesamt Dashboard-Routen. Es gibt keine legitime
# öffentliche darunter — die eine bekannte Ausnahme, der unauthentifizierte
# Abruf von GET /api/accessibility/fix-manifest/{site_id} durch den
# HTML-CLI-Channel (channels/html-cli/complyo-a11y.mjs), liegt in
# widget_routes.py und nicht in alt_text_routes.py.
ALT_TEXT_OEFFENTLICH_GEWOLLT: set = set()

_HTTP_METHODEN = {"get", "post", "patch", "delete", "put"}

# Parameternamen, die eine Auth-Dependency einbinden. `credentials` deckt das
# HTTPBearer-Muster ab, `current_user`/`admin` die Depends-Varianten.
_AUTH_PARAMETER = {"credentials", "current_user", "admin", "user"}


def _routen(pfad_datei):
    """Routen per AST statt Regex.

    Bewusst kein Regex: eine frühere Regex-Fassung übersah stillschweigend
    `@lead_router.post("/collect", response_model=...)` (Dekorator mit weiteren
    kwargs) und `async def get_lead_statistics(admin=Depends(...)):` (einzeilige
    Signatur). Ein Wächter, der Routen übersieht, meldet Grün und schützt nichts.

    Liefert (METHODE, pfad, funktionsname, geschuetzt, quelltext).
    """
    with open(pfad_datei, encoding="utf-8") as fh:
        src = fh.read()
    baum = ast.parse(src)
    for knoten in ast.walk(baum):
        if not isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deko in knoten.decorator_list:
            if not isinstance(deko, ast.Call) or not isinstance(deko.func, ast.Attribute):
                continue
            methode = deko.func.attr
            if methode not in _HTTP_METHODEN:
                continue
            if not isinstance(deko.func.value, ast.Name):
                continue
            if not deko.func.value.id.endswith("router"):
                continue
            if not (deko.args and isinstance(deko.args[0], ast.Constant)):
                continue
            pfad = deko.args[0].value

            args = knoten.args
            namen = {a.arg for a in args.args + args.posonlyargs + args.kwonlyargs}
            geschuetzt = bool(namen & _AUTH_PARAMETER)

            yield (
                methode.upper(),
                pfad,
                knoten.name,
                geschuetzt,
                ast.get_source_segment(src, knoten) or "",
            )


_MODUL_CACHE: dict = {}


@contextlib.contextmanager
def _sauberes_sys_modules():
    """Blendet MagicMock-Module vorübergehend aus und stellt sys.modules danach
    exakt wieder her.

    Hintergrund: tests/test_auth_hardening.py ersetzt beim Import global
    sys.modules["fastapi"] (u. a.) durch MagicMock. Importiert man unser Modul
    danach, sind @router-dekorierte Funktionen MagicMocks statt Coroutinen
    ("object MagicMock can't be used in 'await' expression") — je nach
    Testreihenfolge.

    Die Mocks dauerhaft zu löschen (wie test_addon_plan_escalation.py es tut)
    ist keine Option: andere Testmodule (test_auth_hardening,
    test_legal_update_pipeline, test_gdpr_knowledge_auth) verlassen sich darauf
    und kippen dann um. Deshalb Schnappschuss + Restore: unser Import sieht die
    echten Pakete, alle anderen behalten ihre Mocks.
    """
    schnappschuss = dict(sys.modules)
    try:
        # Nicht nur die MagicMocks selbst: test_auth_hardening hängt unter das
        # gemockte "fastapi" auch einen ECHTEN ModuleType-Stub
        # "fastapi.exceptions". Bliebe der stehen, scheitert der Neuimport des
        # echten fastapi an "cannot import name 'WebSocketException'" — und die
        # Tests würden sich wegskippen statt zu prüfen. Also das komplette
        # Paket jedes gemockten Top-Level-Moduls entfernen.
        mock_wurzeln = {
            name.split(".")[0]
            for name, modul in sys.modules.items()
            if isinstance(modul, MagicMock)
        }
        for name in list(sys.modules):
            if isinstance(sys.modules.get(name), MagicMock) or name.split(".")[0] in mock_wurzeln:
                del sys.modules[name]

        # Ausserdem den EIGENEN Anwendungscode entladen: Module wie
        # `dependencies` wurden ggf. importiert, während pydantic/fastapi noch
        # gemockt waren, und halten dann Mock-Symbole (z.B. eine Settings-Klasse,
        # die das echte FastAPI als Response-Field ablehnt). Sie müssen gegen die
        # echten Pakete neu gebaut werden. site-packages bleibt unangetastet.
        for name in list(sys.modules):
            datei = getattr(sys.modules.get(name), "__file__", None) or ""
            if datei.startswith(_APP_DIR) and "site-packages" not in datei:
                del sys.modules[name]
        yield
    finally:
        sys.modules.clear()
        sys.modules.update(schnappschuss)


def _echtes_modul(modulname: str, probe: str):
    """Liefert `modulname` als ECHTES Modul (nicht als MagicMock).

    `probe` ist eine Funktion des Moduls, die eine Coroutine sein MUSS — daran
    erkennen wir, ob ein bereits importiertes Modul echt oder vergiftet ist.
    Das Ergebnis wird gecacht, damit Monkeypatches innerhalb eines Tests auf
    demselben Objekt landen.
    """
    if modulname in _MODUL_CACHE:
        return _MODUL_CACHE[modulname]

    modul = sys.modules.get(modulname)
    if modul is not None and inspect.iscoroutinefunction(getattr(modul, probe, None)):
        _MODUL_CACHE[modulname] = modul
        return modul

    with _sauberes_sys_modules():
        sys.modules.pop(modulname, None)
        try:
            modul = importlib.import_module(modulname)
        except ImportError as e:
            pytest.skip(f"{modulname} nicht importierbar: {e}")

    if not inspect.iscoroutinefunction(getattr(modul, probe, None)):
        pytest.fail(
            f"{modulname}.{probe} ist keine Coroutine — Modul ist trotz Neuimport "
            "vergiftet; der Test würde sonst grün lügen."
        )
    _MODUL_CACHE[modulname] = modul
    return modul


def _route_nach_pfad(pfad_datei, pfad):
    treffer = [r for r in _routen(pfad_datei) if r[1] == pfad]
    assert treffer, f"Route {pfad} nicht gefunden — Test anpassen oder Route wiederherstellen"
    return treffer[0]


def _route_nach_funktion(pfad_datei, fn):
    treffer = [r for r in _routen(pfad_datei) if r[2] == fn]
    assert treffer, f"Funktion {fn} nicht gefunden"
    return treffer[0]


class TestLeadRoutes:
    def test_parser_findet_alle_routen(self):
        """Selbstschutz: der Wächter ist wertlos, wenn er Routen übersieht."""
        gefunden = {pfad for _, pfad, _, _, _ in _routen(_LEAD_FILE)}
        erwartet = {
            "/waitlist", "/waitlist/confirm", "/collect",
            "/verify/{token}", "/stats", "/unsubscribe",
        }
        assert erwartet <= gefunden, f"Parser übersieht Routen: {sorted(erwartet - gefunden)}"

    def test_keine_unerwartet_offene_route(self):
        offen = {pfad for _, pfad, _, geschuetzt, _ in _routen(_LEAD_FILE) if not geschuetzt}
        unerwartet = offen - LEADS_OEFFENTLICH_GEWOLLT
        assert not unerwartet, (
            "Lead-Route(n) ohne Auth-Prüfung: "
            + ", ".join(sorted(unerwartet))
            + ". Entweder require_admin/Token ergänzen oder — falls die Landingpage "
            "die Route wirklich ohne Login braucht — bewusst in "
            "LEADS_OEFFENTLICH_GEWOLLT aufnehmen."
        )

    def test_allowlist_ist_nicht_verwaist(self):
        vorhandene = {pfad for _, pfad, _, _, _ in _routen(_LEAD_FILE)}
        verwaist = LEADS_OEFFENTLICH_GEWOLLT - vorhandene
        assert not verwaist, f"Allowlist nennt nicht (mehr) existierende Routen: {sorted(verwaist)}"

    def test_stats_ist_admin_only(self):
        """Der Kernbefund: Lead-Zahlen standen öffentlich im Netz."""
        _, _, fn, geschuetzt, quelltext = _route_nach_pfad(_LEAD_FILE, "/stats")
        assert geschuetzt, "/stats ist wieder ohne Auth-Prüfung"
        assert "require_admin" in quelltext, "/stats ist nicht mehr Admin-only"

    def test_unsubscribe_verlangt_token(self):
        """Freie E-Mail ohne Token darf nicht wieder einziehen."""
        _, _, _, _, quelltext = _route_nach_pfad(_LEAD_FILE, "/unsubscribe")
        assert "UnsubscribeRequest" in quelltext, (
            "unsubscribe nimmt wieder eine freie E-Mail statt {email, token}"
        )
        assert "_verify_unsubscribe_token" in quelltext, "Token-Prüfung im Unsubscribe fehlt"

    def test_source_allowlist_ohne_duplikat(self):
        """Bugfix: 'complyo.de' stand doppelt in der allowed-Menge."""
        with open(_LEAD_FILE, encoding="utf-8") as fh:
            src = fh.read()
        m = re.search(r'allowed = \{([^}]+)\}', src)
        assert m, "allowed-Menge in validate_source nicht gefunden"
        eintraege = [e.strip() for e in m.group(1).split(",") if e.strip()]
        assert len(eintraege) == len(set(eintraege)), f"Duplikat in allowed: {eintraege}"


class TestAltTextRoutes:
    def test_keine_unerwartet_offene_route(self):
        offen = {pfad for _, pfad, _, geschuetzt, _ in _routen(_ALT_TEXT_FILE) if not geschuetzt}
        unerwartet = offen - ALT_TEXT_OEFFENTLICH_GEWOLLT
        assert not unerwartet, f"A11y-Route(n) ohne Auth-Prüfung: {sorted(unerwartet)}"

    @pytest.mark.parametrize(
        "fn",
        [
            "alt_text_review_queue",
            "generate_alt_texts",
            "link_review_queue",
            "accessibility_worklist",
            "scan_images_for_alt_text",
        ],
    )
    def test_site_id_routen_pruefen_ownership(self, fn):
        """Auth ohne Ownership ist keine Auth: jede site_id-Route muss prüfen."""
        _, _, _, _, quelltext = _route_nach_funktion(_ALT_TEXT_FILE, fn)
        assert "require_site_ownership" in quelltext, (
            f"{fn} prüft die site_id nicht gegen die Sites des Users"
        )

    def test_scan_images_validiert_url_gegen_ssrf(self):
        _, _, _, _, quelltext = _route_nach_funktion(_ALT_TEXT_FILE, "scan_images_for_alt_text")
        # Bewusst auf den AUFRUF prüfen, nicht auf den blossen Namen: der
        # `from ssrf_protection import validate_url`-Import steht mit in der
        # Funktion, ein "validate_url" in quelltext wäre also auch dann erfüllt,
        # wenn die Prüfung selbst gelöscht wird.
        assert "site_url = validate_url(site_url)" in quelltext, (
            "scan-images holt site_url ohne SSRF-Prüfung ab (validate_url wird nicht "
            "auf site_url angewendet)"
        )
        # Die Prüfung muss VOR dem Abruf stehen, sonst ist sie Dekoration.
        assert quelltext.index("site_url = validate_url(site_url)") < quelltext.index(
            "smart_fetch_html("
        ), "SSRF-Prüfung steht nach dem Fetch"


class TestPatchDownloadRoute:
    """Die Route liegt in widget_routes.py, gehört aber zum A11y-Befund."""

    def test_download_verlangt_auth_und_ownership(self):
        _, _, _, geschuetzt, quelltext = _route_nach_pfad(
            _WIDGET_FILE, "/api/accessibility/patches/download/{download_id}"
        )
        assert geschuetzt, "Patch-Download ist wieder ohne Auth erreichbar"
        assert "require_site_ownership" in quelltext, (
            "Patch-Download prüft nicht, ob das Paket dem User gehört"
        )

    def test_fix_manifest_bleibt_offen(self):
        """Regressionsschutz andersherum: der HTML-CLI-Channel ruft die Route
        bewusst ohne Token (channels/html-cli/complyo-a11y.mjs). Zusperren
        würde den Channel brechen."""
        _, _, _, geschuetzt, _ = _route_nach_pfad(
            _WIDGET_FILE, "/api/accessibility/fix-manifest/{site_id}"
        )
        assert not geschuetzt, (
            "fix-manifest wurde zugesperrt — das bricht channels/html-cli/complyo-a11y.mjs"
        )


class TestUnsubscribeToken:
    """Verhalten des Token-Mechanismus. Braucht das echte Modul -> Container."""

    def _lead_routes(self, monkeypatch):
        monkeypatch.setenv("JWT_SECRET", "test-secret-für-hmac")
        return _echtes_modul("lead_routes", "unsubscribe_lead")

    @pytest.mark.asyncio
    async def test_ohne_token_403(self, monkeypatch):
        lr = self._lead_routes(monkeypatch)
        HTTPException = lr.HTTPException

        async def _darf_nicht_aufgerufen_werden(*a, **kw):
            pytest.fail("update_lead_status_by_email trotz fehlendem Token aufgerufen")

        monkeypatch.setattr(
            lr.db_service, "update_lead_status_by_email", _darf_nicht_aufgerufen_werden
        )

        with pytest.raises(HTTPException) as exc:
            await lr.unsubscribe_lead(lr.UnsubscribeRequest(email="opfer@example.de"))
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_falscher_token_403(self, monkeypatch):
        lr = self._lead_routes(monkeypatch)
        HTTPException = lr.HTTPException

        async def _darf_nicht_aufgerufen_werden(*a, **kw):
            pytest.fail("update_lead_status_by_email trotz falschem Token aufgerufen")

        monkeypatch.setattr(
            lr.db_service, "update_lead_status_by_email", _darf_nicht_aufgerufen_werden
        )

        with pytest.raises(HTTPException) as exc:
            await lr.unsubscribe_lead(
                lr.UnsubscribeRequest(email="opfer@example.de", token="a" * 64)
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_token_einer_fremden_adresse_403(self, monkeypatch):
        """Der Token darf nicht auf eine andere E-Mail übertragbar sein."""
        lr = self._lead_routes(monkeypatch)
        HTTPException = lr.HTTPException

        fremder_token = lr.unsubscribe_token_for("angreifer@example.de")

        with pytest.raises(HTTPException) as exc:
            await lr.unsubscribe_lead(
                lr.UnsubscribeRequest(email="opfer@example.de", token=fremder_token)
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_gueltiger_token_meldet_ab(self, monkeypatch):
        lr = self._lead_routes(monkeypatch)

        aufgerufen = {}

        async def _update(email, status):
            aufgerufen["email"] = email
            aufgerufen["status"] = status
            return True

        monkeypatch.setattr(lr.db_service, "update_lead_status_by_email", _update)

        token = lr.unsubscribe_token_for("kunde@example.de")
        result = await lr.unsubscribe_lead(
            lr.UnsubscribeRequest(email="kunde@example.de", token=token)
        )
        assert result["success"] is True
        assert aufgerufen["status"] == "unsubscribed"

    def test_token_ist_case_insensitive_zur_adresse(self, monkeypatch):
        lr = self._lead_routes(monkeypatch)
        assert lr.unsubscribe_token_for("Kunde@Example.DE") == lr.unsubscribe_token_for(
            "kunde@example.de"
        )

    def test_ohne_jwt_secret_kein_token(self, monkeypatch):
        """Fail closed: ohne Secret darf nichts abgemeldet werden."""
        lr = _echtes_modul("lead_routes", "unsubscribe_lead")
        monkeypatch.delenv("JWT_SECRET", raising=False)
        assert lr._verify_unsubscribe_token("kunde@example.de", "irgendwas") is False


class TestStatsAdminOnly:
    @pytest.mark.asyncio
    async def test_nicht_admin_bekommt_403(self):
        """require_admin ist die kanonische Rollenprüfung aus dependencies."""
        deps = _echtes_modul("dependencies", "require_admin")
        HTTPException = deps.HTTPException

        with pytest.raises(HTTPException) as exc:
            await deps.require_admin(current_user={"id": 1, "role": "user"})
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_kommt_durch(self):
        deps = _echtes_modul("dependencies", "require_admin")
        user = {"id": 1, "role": "admin"}
        assert await deps.require_admin(current_user=user) is user


class TestRequireSiteOwnership:
    @pytest.mark.asyncio
    async def test_fremde_site_id_wird_abgelehnt(self, monkeypatch):
        atr = _echtes_modul("alt_text_routes", "require_site_ownership")
        HTTPException = atr.HTTPException

        async def _sites(_uid):
            return {"eigene-de"}

        monkeypatch.setattr(atr, "get_user_site_ids", _sites)

        with pytest.raises(HTTPException) as exc:
            await atr.require_site_ownership("fremde-de", {"id": 1})
        assert exc.value.status_code == 403

        assert await atr.require_site_ownership("eigene-de", {"id": 1}) == 1

    @pytest.mark.asyncio
    async def test_user_ohne_sites_bekommt_403(self, monkeypatch):
        """Leere Site-Menge darf NICHT als 'darf alles' durchgehen."""
        atr = _echtes_modul("alt_text_routes", "require_site_ownership")
        HTTPException = atr.HTTPException

        async def _sites(_uid):
            return set()

        monkeypatch.setattr(atr, "get_user_site_ids", _sites)

        with pytest.raises(HTTPException) as exc:
            await atr.require_site_ownership("irgendeine-de", {"id": 2})
        assert exc.value.status_code == 403
