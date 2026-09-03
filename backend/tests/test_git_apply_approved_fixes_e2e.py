"""
E2E fuer den Ein-Klick-Fix: freigegebener Fix -> Pull Request.

Warum dieser Test existiert
---------------------------
Die Reparatur ist das einzige Versprechen, das complyo von Anbietern
unterscheidet, die nur pruefen. Bis hierher war sie nur in Einzelteilen
getestet: der Patch-Builder fuer sich (test_fix_patch_builder.py), die Routen
auf Login-Zwang (test_git_integration_auth.py). Was niemand geprueft hat: ob
der Weg vom freigegebenen Alt-Text bis zum Dateiinhalt im Branch tatsaechlich
durchlaeuft — und ob am Ende der richtige Inhalt drinsteht.

Deshalb wird hier nur die HTTP-Schicht ersetzt (`_request`). Alles darueber —
Baum holen, Kandidaten filtern, Dateien lesen, Patches bauen, Branch anlegen,
committen, PR eroeffnen — ist echter Produktionscode. Ein Fehler im Commit-Weg
faellt hier auf, nicht erst im Kunden-Repository.
"""
import base64
import os
import sys
from typing import Any, Dict, Optional, Tuple

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import git_routes
from fix_patch_builder import inhalt_hash, zaehle_pr_faehig
from git_service import GitHubClient, GitCredentials, GitProvider


# =============================================================================
# Fake-GitHub: nur die HTTP-Schicht, der Rest ist echter Client-Code
# =============================================================================

class FakeGitHub(GitHubClient):
    """GitHub-API als Dictionary. Ersetzt ausschliesslich `_request`."""

    def __init__(self, dateien: Dict[str, str]):
        super().__init__("test-token")
        self.branches = {"main": "sha-main"}
        self.dateien = dict(dateien)          # pfad -> inhalt (Stand: main)
        self.commits: list = []               # (pfad, inhalt) in Reihenfolge
        self.pr_erstellt: Optional[Dict[str, Any]] = None

    async def _request(
        self, method: str, endpoint: str,
        data: Optional[Dict] = None, params: Optional[Dict] = None,
    ) -> Tuple[bool, Any]:
        teile = endpoint.strip("/").split("/")

        # GET /repos/{o}/{r}/git/ref/heads/{branch}
        if method == "GET" and "/git/ref/heads/" in endpoint:
            branch = endpoint.split("/git/ref/heads/")[1]
            sha = self.branches.get(branch)
            return (True, {"object": {"sha": sha}}) if sha else (False, {"message": "not found"})

        # POST /repos/{o}/{r}/git/refs  -> Branch anlegen
        if method == "POST" and endpoint.endswith("/git/refs"):
            self.branches[(data or {})["ref"].replace("refs/heads/", "")] = (data or {})["sha"]
            return True, {"object": {"sha": (data or {})["sha"]}}

        # GET /repos/{o}/{r}/git/trees/{sha}?recursive=1
        if method == "GET" and "/git/trees/" in endpoint:
            return True, {
                "truncated": False,
                "tree": [
                    {"path": p, "type": "blob", "size": len(c.encode())}
                    for p, c in self.dateien.items()
                ],
            }

        # GET /repos/{o}/{r}/contents/{path}
        if method == "GET" and "/contents/" in endpoint:
            pfad = endpoint.split("/contents/", 1)[1]
            if pfad not in self.dateien:
                return False, {"message": "Not Found"}
            roh = self.dateien[pfad].encode("utf-8")
            return True, {
                "content": base64.b64encode(roh).decode("ascii"),
                "sha": f"blob-{hash(self.dateien[pfad]) & 0xffff:x}",
            }

        # PUT /repos/{o}/{r}/contents/{path}  -> Datei schreiben
        if method == "PUT" and "/contents/" in endpoint:
            pfad = endpoint.split("/contents/", 1)[1]
            neu = base64.b64decode((data or {})["content"]).decode("utf-8")
            self.dateien[pfad] = neu
            self.commits.append((pfad, neu))
            return True, {"commit": {"sha": f"commit-{len(self.commits)}"}}

        # POST /repos/{o}/{r}/pulls
        if method == "POST" and teile[-1] == "pulls":
            self.pr_erstellt = dict(data or {})
            return True, {"id": 4711, "number": 42,
                          "html_url": "https://github.com/kunde/site/pull/42"}

        return False, {"message": f"Fake kennt {method} {endpoint} nicht"}


class FakeSaver:
    """AccessibilityFixSaver-Ersatz: liefert genau die freigegebenen Fixes."""

    daten: Dict[str, list] = {"alt": [], "doc": [], "link": []}

    def __init__(self, pool):  # Pool wird nicht gebraucht
        pass

    async def get_fixes_for_site(self, site_id, status="approved"):
        return list(self.daten["alt"])

    async def get_document_fixes_for_site(self, site_id, status="approved"):
        return list(self.daten["doc"])

    async def get_link_fixes_for_site(self, site_id, status="approved"):
        return list(self.daten["link"])


INDEX_HTML = (
    '<!doctype html>\n'
    '<html>\n'
    '  <head><title>Spedition Krause</title></head>\n'
    '  <body>\n'
    '    <img src="/assets/img/team.jpg" class="hero">\n'
    '    <img src="/assets/img/logo.svg" alt="">\n'
    '    <main id="main"><p>Willkommen</p></main>\n'
    '  </body>\n'
    '</html>\n'
)


@pytest.fixture
def welt(monkeypatch):
    """Verdrahtet Fakes so, dass nur Netz und DB ersetzt sind."""
    import accessibility_fix_saver
    import widget_routes

    github = FakeGitHub({
        "index.html": INDEX_HTML,
        "node_modules/paket/index.html": '<html><img src="team.jpg"></html>',
        "README.md": "# Doku",
    })

    FakeSaver.daten = {
        "alt": [{"image_src": "https://kunde.de/wp-content/uploads/team.jpg",
                 "suggested_alt": "Das Team der Spedition vor dem Fuhrpark"}],
        "doc": [{"fix_type": "html-lang", "payload": {"value": "de"}},
                {"fix_type": "skip-link",
                 "payload": {"label": "Zum Inhalt springen", "target": "#main"}}],
        "link": [],
    }

    monkeypatch.setattr(accessibility_fix_saver, "AccessibilityFixSaver", FakeSaver)
    monkeypatch.setattr(widget_routes, "db_pool", object())
    monkeypatch.setattr(git_routes, "db_pool", None)  # kein PR-Record-Insert
    monkeypatch.setattr(git_routes.git_service, "get_client", lambda provider, creds: github)

    async def fake_repo(user_id, repo_id):
        return {"provider": "github", "owner": "kunde", "repo": "site", "default_branch": "main"}

    async def fake_creds(user_id, provider):
        return GitCredentials(provider=GitProvider.GITHUB, access_token="t", refresh_token=None)

    monkeypatch.setattr(git_routes, "_get_connected_repo", fake_repo)
    monkeypatch.setattr(git_routes, "_get_git_credentials", fake_creds)
    return github


async def _auslösen():
    return await git_routes.apply_approved_fixes(
        git_routes.ApplyApprovedFixesRequest(repo_id="1", site_id="site-abc"),
        user={"user_id": "u1"},
    )


# =============================================================================
# Der Hauptweg
# =============================================================================

class TestEinKlickFix:
    @pytest.mark.asyncio
    async def test_freigegebener_altText_landet_im_branch(self, welt):
        res = await _auslösen()

        assert res.success, res.error
        assert res.pr_number == 42
        assert res.files_changed == ["index.html"]

        # Entscheidend: der Inhalt im Branch, nicht nur "irgendein Commit".
        geschrieben = dict(welt.commits)["index.html"]
        assert 'alt="Das Team der Spedition vor dem Fuhrpark"' in geschrieben
        assert '<html lang="de">' in geschrieben
        assert 'class="skip-link"' in geschrieben

    @pytest.mark.asyncio
    async def test_bestehendes_alt_bleibt_leer(self, welt):
        """logo.svg trug bewusst alt="" (dekorativ) — das bleibt so."""
        await _auslösen()
        geschrieben = dict(welt.commits)["index.html"]
        assert '<img src="/assets/img/logo.svg" alt="">' in geschrieben

    @pytest.mark.asyncio
    async def test_rest_der_datei_bleibt_unveraendert(self, welt):
        """Minimal-invasiv: der Kunde muss im Diff sehen, was passiert."""
        await _auslösen()
        geschrieben = dict(welt.commits)["index.html"]
        assert "<title>Spedition Krause</title>" in geschrieben
        assert "<p>Willkommen</p>" in geschrieben

        # Echter Zeilen-Diff statt Positionsvergleich: der Sprunglink schiebt
        # alle Folgezeilen um eins, positionsweise waere alles "geaendert".
        import difflib
        diff = list(difflib.unified_diff(
            INDEX_HTML.splitlines(), geschrieben.splitlines(), n=0, lineterm=""
        ))
        entfernt = [z for z in diff if z.startswith("-") and not z.startswith("---")]
        ergaenzt = [z for z in diff if z.startswith("+") and not z.startswith("+++")]
        assert len(entfernt) == 2, entfernt   # <html> und das team.jpg-Tag
        assert len(ergaenzt) == 3, ergaenzt   # dieselben zwei + Sprunglink-Zeile

    @pytest.mark.asyncio
    async def test_ausgeschlossene_pfade_werden_nie_angefasst(self, welt):
        await _auslösen()
        assert "node_modules/paket/index.html" not in dict(welt.commits)

    @pytest.mark.asyncio
    async def test_zweimal_ausfuehren_ergibt_denselben_inhalt(self, welt):
        """Deterministisch: ohne Determinismus taugt weder Review noch Revert."""
        await _auslösen()
        erster = dict(welt.commits)["index.html"]
        welt.commits.clear()
        welt.dateien["index.html"] = INDEX_HTML  # Ausgangsstand wiederherstellen
        await _auslösen()
        assert dict(welt.commits)["index.html"] == erster

    @pytest.mark.asyncio
    async def test_zweiter_lauf_auf_gefixtem_stand_aendert_nichts(self, welt):
        """Guarded: was schon versorgt ist, wird nicht erneut angefasst."""
        await _auslösen()
        welt.commits.clear()
        res = await _auslösen()
        assert not res.success
        assert welt.commits == []


# =============================================================================
# Die Faelle, in denen der Knopf frueher gelogen hat
# =============================================================================

class TestKnopfVerspricht:
    @pytest.mark.asyncio
    async def test_nur_linkfixes_erklaert_den_richtigen_grund(self, welt):
        """Frueher: "Keine freigegebenen Fixes vorhanden" — obwohl welche da waren."""
        FakeSaver.daten = {"alt": [], "doc": [],
                           "link": [{"link_href": "/preise", "suggested_label": "Preisliste"}]}
        res = await _auslösen()
        assert not res.success
        assert "Widget" in res.error and "Plugin" in res.error
        assert "Keine freigegebenen Fixes vorhanden" not in res.error

    @pytest.mark.asyncio
    async def test_gar_nichts_freigegeben_bleibt_beim_alten_hinweis(self, welt):
        FakeSaver.daten = {"alt": [], "doc": [], "link": []}
        res = await _auslösen()
        assert not res.success
        assert "Keine freigegebenen Fixes" in res.error

    def test_zaehlung_trennt_pr_faehig_von_manifest(self):
        z = zaehle_pr_faehig(
            alt_texte=[{"image_src": "a.jpg", "suggested_alt": "A"}],
            link_fixes=[{"link_href": "/x"}, {"link_href": "/y"}],
            dokument_fixes=[{"fix_type": "html-lang"}, {"fix_type": "css-rule"}],
        )
        assert z["deliverable"] == 2        # 1 Alt-Text + html-lang
        assert z["manifest_only"] == 3      # 2 Linktexte + css-rule


# =============================================================================
# Der Schreib-Schutz
# =============================================================================

class TestSchreibschutz:
    @pytest.mark.asyncio
    async def test_fremde_aenderung_bricht_ab_statt_zu_ueberschreiben(self, welt):
        """
        Zwischen Analyse und Commit aendert jemand die Datei. Der Patch beruht
        dann auf einem Stand, den es nicht mehr gibt — er darf nicht schreiben.
        """
        echtes_lesen = welt.get_file_content
        zustand = {"erster_aufruf": True}

        async def lesen_mit_zwischenaenderung(owner, repo, path, branch="main"):
            ergebnis = await echtes_lesen(owner, repo, path, branch)
            if path == "index.html" and zustand["erster_aufruf"]:
                zustand["erster_aufruf"] = False
                welt.dateien["index.html"] = INDEX_HTML.replace(
                    "<p>Willkommen</p>", "<p>Willkommen bei uns</p>"
                )
            return ergebnis

        welt.get_file_content = lesen_mit_zwischenaenderung

        res = await _auslösen()
        assert not res.success
        assert "geaendert" in res.error or "geändert" in res.error
        assert welt.commits == []

    def test_hash_bindet_patch_an_den_gelesenen_stand(self):
        assert inhalt_hash("<html>") != inhalt_hash("<html> ")
        assert inhalt_hash("<html>") == inhalt_hash("<html>")
