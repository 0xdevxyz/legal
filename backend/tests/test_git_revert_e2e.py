"""
E2E fuer den Rueckweg: einen ueber complyo erstellten PR zuruecknehmen.

Warum dieser Test existiert
---------------------------
Der Hinweg ist geprueft (test_git_apply_approved_fixes_e2e.py). Der Rueckweg
war es bis heute **ueberhaupt nicht** — `grep -rl revert tests/` fand keine
einzige Datei. Ein Rueckweg, den nie jemand gegangen ist, ist kein Rueckweg,
sondern ein Versprechen; und genau dieses Versprechen ist die Bedingung, unter
der complyo ueberhaupt in fremde Repositories schreiben darf.

Nach demselben Muster wie der Hinweg wird nur die HTTP-Schicht ersetzt
(`_request`). Alles darueber — PR-Zustand lesen, Merge-Commit und dessen
ersten Parent bestimmen, Revert-Branch abzweigen, Dateien einzeln
zuruecksetzen, hinzugefuegte Dateien loeschen, Gegen-PR eroeffnen — ist echter
Produktionscode.

Das Fake-GitHub modelliert Refs wie git selbst: Branches zeigen auf Snapshots,
ein Schreibvorgang erzeugt einen neuen Snapshot und haengt den Branch um.
Nur so laesst sich die entscheidende Frage ueberhaupt stellen: bleibt `main`
unangetastet, waehrend der Revert-Branch sich aendert?
"""
import base64
import hashlib
import os
import sys
from typing import Any, Dict, Optional, Tuple

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from git_service import GitHubClient, GitCredentials, GitProvider
from git_service.git_service import GitService, PRStatus, RepoInfo

ALT = "<h1>Willkommen</h1>\n<img src=\"team.jpg\">\n"
NEU = "<h1>Willkommen</h1>\n<img src=\"team.jpg\" alt=\"Unser Team vor dem Buero\">\n"
FREMD = "<h1>Kontakt</h1>\n"
ZUSATZ = ".sr-only { position: absolute; }\n"


def _blob(inhalt: str) -> str:
    return "blob-" + hashlib.sha1(inhalt.encode("utf-8")).hexdigest()[:12]


# =============================================================================
# Fake-GitHub: Refs und Snapshots, sonst echter Client-Code
# =============================================================================

class FakeGitHub(GitHubClient):
    """GitHub-API als Snapshot-Speicher. Ersetzt ausschliesslich `_request`."""

    def __init__(self):
        super().__init__("test-token")

        # Stand VOR dem Merge: Alt-Text fehlt, Zusatzdatei existiert nicht.
        vorher = {"index.html": ALT, "kontakt.html": FREMD}
        # Stand NACH dem Merge: das, was complyo vorgeschlagen hat.
        nachher = {"index.html": NEU, "kontakt.html": FREMD, "assets/a11y.css": ZUSATZ}

        self.snapshots: Dict[str, Dict[str, str]] = {
            "sha-vorher": vorher,
            "sha-merge": nachher,
        }
        self.branches: Dict[str, str] = {"main": "sha-merge"}

        # PR #42: von complyo erstellt, vom Kunden gemerged.
        self.pr = {
            "number": 42,
            "state": "closed",
            "merged_at": "2026-08-11T09:00:00Z",
            "merge_commit_sha": "sha-merge",
            "html_url": "https://github.com/kunde/site/pull/42",
            "head": {"ref": "complyo/fixes-20260811"},
        }
        self.pr_dateien = [
            {"filename": "index.html", "status": "modified"},
            {"filename": "assets/a11y.css", "status": "added"},
        ]

        self.geschlossen: list = []          # PR-Nummern, die PATCHed wurden
        self.neuer_pr: Optional[Dict[str, Any]] = None
        self.schreibvorgaenge: list = []     # (methode, pfad, branch)
        self.sha_zaehler = 0

    # -- Hilfen ---------------------------------------------------------------

    def stand(self, ref: str) -> Optional[Dict[str, str]]:
        """Loest einen Ref auf — Branchname oder roher Commit-SHA."""
        if ref in self.branches:
            return self.snapshots[self.branches[ref]]
        return self.snapshots.get(ref)

    def _neuer_snapshot(self, branch: str) -> Dict[str, str]:
        """Wie git: Schreiben erzeugt einen neuen Commit, kein In-Place-Edit."""
        self.sha_zaehler += 1
        sha = f"sha-commit-{self.sha_zaehler}"
        self.snapshots[sha] = dict(self.snapshots[self.branches[branch]])
        self.branches[branch] = sha
        return self.snapshots[sha]

    # -- die einzige ersetzte Schicht -----------------------------------------

    async def _request(
        self, method: str, endpoint: str,
        data: Optional[Dict] = None, params: Optional[Dict] = None,
    ) -> Tuple[bool, Any]:
        data = data or {}
        params = params or {}
        teile = endpoint.strip("/").split("/")

        # GET /repos/{o}/{r}/pulls/{n}/files
        if method == "GET" and endpoint.endswith("/files") and "/pulls/" in endpoint:
            return (True, self.pr_dateien) if params.get("page", 1) == 1 else (True, [])

        # GET /repos/{o}/{r}/pulls/{n}
        if method == "GET" and "/pulls/" in endpoint:
            return (True, self.pr) if teile[-1] == str(self.pr["number"]) else (False, {"message": "Not Found"})

        # PATCH /repos/{o}/{r}/pulls/{n}  -> PR schliessen
        if method == "PATCH" and "/pulls/" in endpoint:
            self.geschlossen.append((int(teile[-1]), data.get("state")))
            return True, {"state": data.get("state")}

        # GET /repos/{o}/{r}/commits/{sha}
        if method == "GET" and "/commits/" in endpoint:
            sha = teile[-1]
            if sha == "sha-merge":
                # Erster Parent = Stand des Default-Branch vor dem Merge.
                return True, {"parents": [{"sha": "sha-vorher"}, {"sha": "sha-feature"}]}
            return False, {"message": "Not Found"}

        # GET /repos/{o}/{r}/git/ref/heads/{branch}
        if method == "GET" and "/git/ref/heads/" in endpoint:
            branch = endpoint.split("/git/ref/heads/")[1]
            sha = self.branches.get(branch)
            return (True, {"object": {"sha": sha}}) if sha else (False, {"message": "Not Found"})

        # POST /repos/{o}/{r}/git/refs  -> Branch anlegen
        if method == "POST" and endpoint.endswith("/git/refs"):
            self.branches[data["ref"].replace("refs/heads/", "")] = data["sha"]
            return True, {"object": {"sha": data["sha"]}}

        # GET /repos/{o}/{r}/contents/{path}
        if method == "GET" and "/contents/" in endpoint:
            pfad = endpoint.split("/contents/", 1)[1]
            snapshot = self.stand(params.get("ref", "main"))
            if snapshot is None or pfad not in snapshot:
                return False, {"message": "Not Found"}
            return True, {
                "content": base64.b64encode(snapshot[pfad].encode("utf-8")).decode("ascii"),
                "sha": _blob(snapshot[pfad]),
            }

        # PUT / DELETE /repos/{o}/{r}/contents/{path}
        if method in ("PUT", "DELETE") and "/contents/" in endpoint:
            pfad = endpoint.split("/contents/", 1)[1]
            branch = data["branch"]
            aktuell = self.stand(branch) or {}

            # Optimistische Sperre wie bei GitHub: mitgeschickter SHA muss passen.
            if data.get("sha") and pfad in aktuell and data["sha"] != _blob(aktuell[pfad]):
                return False, {"message": "is at ... but expected ..."}

            snapshot = self._neuer_snapshot(branch)
            if method == "DELETE":
                snapshot.pop(pfad, None)
            else:
                snapshot[pfad] = base64.b64decode(data["content"]).decode("utf-8")
            self.schreibvorgaenge.append((method, pfad, branch))
            return True, {"commit": {"sha": self.branches[branch]}}

        # POST /repos/{o}/{r}/pulls
        if method == "POST" and teile[-1] == "pulls":
            self.neuer_pr = dict(data)
            return True, {"id": 99, "number": 43,
                          "html_url": "https://github.com/kunde/site/pull/43"}

        return False, {"message": f"Fake kennt {method} {endpoint} nicht"}


@pytest.fixture
def welt(monkeypatch):
    github = FakeGitHub()
    service = GitService()
    monkeypatch.setattr(service, "get_client", lambda provider, creds: github)
    creds = GitCredentials(provider=GitProvider.GITHUB, access_token="test-token")
    repo = RepoInfo(provider=GitProvider.GITHUB, owner="kunde", repo="site")
    return service, github, creds, repo


def _revert_branch(github: FakeGitHub) -> str:
    namen = [b for b in github.branches if b.startswith("revert/")]
    assert len(namen) == 1, f"erwartet genau einen Revert-Branch, gefunden: {namen}"
    return namen[0]


# =============================================================================
# Der Hauptfall: gemergter PR wird zurueckgenommen
# =============================================================================

@pytest.mark.asyncio
async def test_gemergter_pr_stellt_alten_inhalt_byteweise_wieder_her(welt):
    """Der Kern des Versprechens: der alte Dateiinhalt kommt exakt zurueck."""
    service, github, creds, repo = welt

    ergebnis = await service.revert_pull_request(creds, repo, 42)

    assert ergebnis.success, ergebnis.error
    branch = _revert_branch(github)
    assert github.stand(branch)["index.html"] == ALT


@pytest.mark.asyncio
async def test_vom_pr_angelegte_datei_wird_geloescht_nicht_geleert(welt):
    """Der Fall, den man vergisst: `added` heisst rueckwaerts `entfernen`."""
    service, github, creds, repo = welt

    await service.revert_pull_request(creds, repo, 42)

    branch = _revert_branch(github)
    assert "assets/a11y.css" not in github.stand(branch)
    assert ("DELETE", "assets/a11y.css", branch) in github.schreibvorgaenge


@pytest.mark.asyncio
async def test_dateien_ausserhalb_des_prs_bleiben_unberuehrt(welt):
    """Ein Revert darf nur zuruecknehmen, was complyo angefasst hat."""
    service, github, creds, repo = welt

    await service.revert_pull_request(creds, repo, 42)

    branch = _revert_branch(github)
    assert github.stand(branch)["kontakt.html"] == FREMD
    angefasst = {pfad for _, pfad, _ in github.schreibvorgaenge}
    assert "kontakt.html" not in angefasst


@pytest.mark.asyncio
async def test_main_wird_nicht_angetastet(welt):
    """Auch der Revert wird nur vorgeschlagen. Gemerged wird vom Kunden."""
    service, github, creds, repo = welt
    main_vorher = dict(github.stand("main"))

    await service.revert_pull_request(creds, repo, 42)

    assert github.stand("main") == main_vorher
    assert all(branch.startswith("revert/") for _, _, branch in github.schreibvorgaenge)


@pytest.mark.asyncio
async def test_gegen_pr_wird_eroeffnet_und_nennt_die_dateien(welt):
    service, github, creds, repo = welt

    ergebnis = await service.revert_pull_request(creds, repo, 42)

    assert github.neuer_pr is not None, "kein Gegen-PR eroeffnet"
    assert "#42" in github.neuer_pr["title"]
    rumpf = github.neuer_pr["body"]
    assert "index.html" in rumpf and "assets/a11y.css" in rumpf
    assert "gemerged wird von Ihnen" in rumpf
    assert ergebnis.pr_number == 43


# =============================================================================
# Die anderen Zustaende, in denen ein PR sein kann
# =============================================================================

@pytest.mark.asyncio
async def test_offener_pr_wird_nur_geschlossen(welt):
    """Nichts wurde gemerged — es gibt nichts zurueckzusetzen."""
    service, github, creds, repo = welt
    github.pr["state"] = "open"
    github.pr["merged_at"] = None

    ergebnis = await service.revert_pull_request(creds, repo, 42)

    assert ergebnis.success
    assert ergebnis.status == PRStatus.CLOSED
    assert github.geschlossen == [(42, "closed")]
    assert github.schreibvorgaenge == [], "geschlossener PR darf nichts schreiben"
    assert not [b for b in github.branches if b.startswith("revert/")]


@pytest.mark.asyncio
async def test_geschlossener_nie_gemergter_pr_wird_erklaert_nicht_bearbeitet(welt):
    service, github, creds, repo = welt
    github.pr["merged_at"] = None

    ergebnis = await service.revert_pull_request(creds, repo, 42)

    assert not ergebnis.success
    assert "nie gemerged" in ergebnis.error
    assert github.schreibvorgaenge == []


@pytest.mark.asyncio
async def test_unbekannter_pr_meldet_klartext(welt):
    service, github, creds, repo = welt

    ergebnis = await service.revert_pull_request(creds, repo, 999)

    assert not ergebnis.success
    assert "999" in ergebnis.error
    assert github.schreibvorgaenge == []


@pytest.mark.asyncio
async def test_gitlab_wird_ehrlich_abgelehnt(welt):
    """Lieber ein klares Nein als ein halber Revert."""
    service, github, creds, _ = welt
    repo = RepoInfo(provider=GitProvider.GITLAB, owner="kunde", repo="site")

    ergebnis = await service.revert_pull_request(creds, repo, 42)

    assert not ergebnis.success
    assert "GitHub" in ergebnis.error


# =============================================================================
# Wenn der alte Stand nicht mehr lesbar ist
# =============================================================================

@pytest.mark.asyncio
async def test_unlesbarer_vorzustand_bricht_ab_statt_zu_raten(welt):
    """Kein Revert auf gut Glueck: was nicht belegbar ist, wird nicht geschrieben."""
    service, github, creds, repo = welt
    del github.snapshots["sha-vorher"]["index.html"]

    ergebnis = await service.revert_pull_request(creds, repo, 42)

    assert not ergebnis.success
    assert "index.html" in ergebnis.error
    branch = _revert_branch(github)
    assert github.stand(branch)["index.html"] == NEU, "es wurde geraten statt abzubrechen"


@pytest.mark.asyncio
async def test_abbruch_mittendrin_laesst_main_unberuehrt(welt):
    """Ein Teil-Revert darf nur auf dem Vorschlags-Branch existieren."""
    service, github, creds, repo = welt
    github.pr_dateien = [
        {"filename": "index.html", "status": "modified"},
        {"filename": "kontakt.html", "status": "modified"},
    ]
    del github.snapshots["sha-vorher"]["kontakt.html"]
    main_vorher = dict(github.stand("main"))

    ergebnis = await service.revert_pull_request(creds, repo, 42)

    assert not ergebnis.success
    assert github.stand("main") == main_vorher
    assert github.neuer_pr is None, "abgebrochener Revert darf keinen PR eroeffnen"


@pytest.mark.asyncio
async def test_fehlender_merge_commit_bricht_ab(welt):
    service, github, creds, repo = welt
    github.pr["merge_commit_sha"] = "sha-unbekannt"

    ergebnis = await service.revert_pull_request(creds, repo, 42)

    assert not ergebnis.success
    assert "vor dem Merge" in ergebnis.error
    assert github.schreibvorgaenge == []
