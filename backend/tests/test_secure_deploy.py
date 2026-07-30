"""
Direct-Deploy: Backup-Pflicht, Review-Gate, Rollback
====================================================

Betreiber-Bedingung (29.07.2026): Direktschreiben ist nur zulässig, "wenn sie
mit backup schreibt". Der alte Motor erfüllte das nicht — das Backup war ein
Stub (FTP/SFTP: `pass`) und meldete trotzdem backup_created=True. Diese Tests
stellen sicher, dass die Bedingung dauerhaft erfüllt bleibt.
"""
import base64
import os
import sys
import types

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)

from compliance_engine.secure_deployment import (  # noqa: E402
    DeployFile,
    DeploymentError,
    SecureDeploymentEngine,
)
import compliance_engine.secure_deployment as sd  # noqa: E402


class _FakeTransport:
    """Protokolliert Reihenfolge und simuliert einen Remote-Bestand."""

    def __init__(self, bestand=None, download_wirft=False):
        self.bestand = dict(bestand or {})
        self.download_wirft = download_wirft
        self.aktionen = []

    def download(self, path):
        self.aktionen.append(("download", path))
        if self.download_wirft:
            raise IOError("Verbindung abgerissen")
        return self.bestand.get(path)

    def upload(self, path, inhalt):
        self.aktionen.append(("upload", path))
        self.bestand[path] = inhalt

    def delete(self, path):
        self.aktionen.append(("delete", path))
        self.bestand.pop(path, None)

    def close(self):
        self.aktionen.append(("close", None))


@pytest.fixture()
def fake_transport(monkeypatch):
    """_transport liefert einen kontrollierbaren Fake."""
    halter = {}

    def _factory(method, credentials):
        if method not in ("ftp", "sftp"):
            raise DeploymentError("nicht unterstützt")
        return halter["t"]

    monkeypatch.setattr(sd, "_transport", _factory)
    def setze(t):
        halter["t"] = t
        return t
    return setze


class TestBackupPflicht:
    @pytest.mark.asyncio
    async def test_backup_passiert_vor_dem_upload(self, fake_transport):
        t = fake_transport(_FakeTransport(bestand={"index.html": b"<alt>"}))
        engine = SecureDeploymentEngine()
        ergebnis = await engine.deploy(
            "ftp", {"host": "x"}, [DeployFile("index.html", "<neu>")]
        )
        arten = [a for a, _ in t.aktionen]
        assert arten.index("download") < arten.index("upload"), (
            "Der Upload lief vor dem Backup"
        )
        eintrag = ergebnis.backup_contents["index.html"]
        assert eintrag["existed"] is True
        assert base64.b64decode(eintrag["content_b64"]) == b"<alt>"

    @pytest.mark.asyncio
    async def test_backup_fehler_verhindert_deploy(self, fake_transport):
        t = fake_transport(_FakeTransport(download_wirft=True))
        engine = SecureDeploymentEngine()
        with pytest.raises(DeploymentError):
            await engine.deploy("ftp", {"host": "x"}, [DeployFile("index.html", "<neu>")])
        assert ("upload", "index.html") not in t.aktionen, (
            "Trotz Backup-Fehler wurde deployt — fail-closed verletzt"
        )

    @pytest.mark.asyncio
    async def test_neue_datei_wird_als_nicht_existent_gesichert(self, fake_transport):
        fake_transport(_FakeTransport())
        engine = SecureDeploymentEngine()
        ergebnis = await engine.deploy("ftp", {"host": "x"}, [DeployFile("neu.html", "<x>")])
        assert ergebnis.backup_contents["neu.html"] == {"existed": False, "content_b64": None}

    @pytest.mark.asyncio
    async def test_unbekannte_methode_wird_abgelehnt(self):
        engine = SecureDeploymentEngine()
        for methode in ("wordpress", "netlify", "vercel", "github_pr"):
            with pytest.raises(DeploymentError):
                await engine.deploy(methode, {}, [DeployFile("a", "b")])


class TestRestore:
    @pytest.mark.asyncio
    async def test_bestand_wird_wiederhergestellt(self, fake_transport):
        t = fake_transport(_FakeTransport(bestand={"index.html": b"<kaputt>"}))
        engine = SecureDeploymentEngine()
        pfade = await engine.restore(
            "ftp", {"host": "x"},
            {"index.html": {"existed": True, "content_b64": base64.b64encode(b"<alt>").decode()}},
        )
        assert pfade == ["index.html"]
        assert t.bestand["index.html"] == b"<alt>"

    @pytest.mark.asyncio
    async def test_vorher_nicht_existente_datei_wird_entfernt(self, fake_transport):
        t = fake_transport(_FakeTransport(bestand={"neu.html": b"<deployt>"}))
        engine = SecureDeploymentEngine()
        await engine.restore(
            "ftp", {"host": "x"}, {"neu.html": {"existed": False, "content_b64": None}}
        )
        assert "neu.html" not in t.bestand

    @pytest.mark.asyncio
    async def test_leeres_backup_wird_abgelehnt(self):
        engine = SecureDeploymentEngine()
        with pytest.raises(DeploymentError):
            await engine.restore("ftp", {"host": "x"}, {})


class TestRouteVertraege:
    """Statische Wächter über fix_apply_routes.py."""

    @staticmethod
    def _src():
        """Quelltext ohne Docstrings/Kommentare — die Historie im Modul-Docstring
        nennt die alten kaputten Namen bewusst und darf nicht anschlagen."""
        import re
        with open(os.path.join(_BACKEND, "fix_apply_routes.py"), encoding="utf-8") as fh:
            src = fh.read()
        src = re.sub(r'"""(?:.|\n)*?"""', "", src)
        return "\n".join(re.sub(r"#.*$", "", z) for z in src.splitlines())

    def test_review_gate_wird_durchgesetzt(self):
        src = self._src()
        assert "_DEPLOYBARE_STATUS" in src
        assert 'quality_gate_status") not in _DEPLOYBARE_STATUS' in src.replace("'", '"')

    def test_kundenbestaetigung_ist_pflicht(self):
        src = self._src()
        assert src.count("user_confirmed") >= 4, (
            "Apply und Rollback muessen die explizite Bestaetigung pruefen"
        )

    def test_credentials_werden_nie_persistiert(self):
        src = self._src()
        # Kein INSERT/UPDATE darf das credentials-Dict beruehren.
        for zeile in src.splitlines():
            if "INSERT" in zeile.upper() or "UPDATE" in zeile.upper():
                assert "credential" not in zeile.lower()
        assert "json.dumps(apply_request.credentials" not in src
        assert "json.dumps(rollback_request.credentials" not in src

    def test_alter_kaputter_pfad_bleibt_entfernt(self):
        src = self._src()
        assert "generated_fixes" not in src, "fix_data-Spalte existiert nicht — alter Pfad"
        assert "backed_up_files" not in src, "Spalte existiert nicht — alter Rollback-Pfad"
        assert "DeploymentEngine" not in src.replace("SecureDeploymentEngine", ""), (
            "Der alte Motor (Backup-Stub) darf nicht zurueckkehren"
        )
        assert "/apply/preview" not in src, (
            "Der Preview-Stub (erfundene Staging-URL) bleibt entfernt"
        )
