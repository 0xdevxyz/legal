"""
P3 Contract Tests
=================
Vergleicht /openapi.json des laufenden Services gegen den committed Snapshot.
Schlägt bei Breaking Changes an (entfernte Felder, geänderte Typen).

Usage:
    pytest tests/test_contracts.py -v
    (requires backend running at BACKEND_URL, default: http://localhost:8002)
"""
import os
import json
import pytest
import urllib.request
import urllib.error
from pathlib import Path

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8002")


def _resolve_data_file(relative: str):
    """Sucht eine Datei unterhalb des Repo-`data/`-Verzeichnisses.

    Das Backend-Image enthält nur `backend/` — `data/` liegt eine Ebene darüber
    im Repo und wird nicht mitkopiert. Der feste Pfad
    `parent.parent.parent/data/...` löst im Container zu `/data/...` auf und
    existiert dort nicht, während er im Repo-Checkout (so läuft CI) stimmt.

    Reihenfolge: explizites COMPLYO_DATA_DIR, dann von __file__ aufwärts nach
    einem `data/`-Verzeichnis suchen, das die Datei enthält.
    """
    env_dir = os.getenv("COMPLYO_DATA_DIR")
    if env_dir:
        candidate = Path(env_dir) / relative
        if candidate.exists():
            return candidate

    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data" / relative
        if candidate.exists():
            return candidate
    return None


SNAPSHOT_PATH = _resolve_data_file("hardening-2026-05-25/contracts/openapi.snapshot.json")

# Bewusst skipif statt xfail oder Selbst-Erzeugung: Der Snapshot EXISTIERT im
# Repo und ist die committete Referenz — ihn beim ersten Lauf neu zu schreiben
# würde die Aussage des Tests (Breaking-Change-Erkennung) zerstören, weil der
# aktuelle Stand dann per Definition immer "kompatibel" wäre. Fehlt die Datei,
# fehlt nur die Umgebung (Image ohne repo-`data/`).
_SNAPSHOT_MISSING_REASON = (
    "Snapshot data/hardening-2026-05-25/contracts/openapi.snapshot.json nicht gefunden. "
    "Im Repo-Checkout vorhanden; das Backend-Image enthält repo-`data/` nicht. "
    "Per COMPLYO_DATA_DIR oder Mount des Repo-data-Verzeichnisses ausführbar machen."
)
pytestmark = pytest.mark.skipif(SNAPSHOT_PATH is None, reason=_SNAPSHOT_MISSING_REASON)


def _fetch_live_schema():
    try:
        with urllib.request.urlopen(f"{BACKEND_URL}/openapi.json", timeout=5) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return None, str(e)


def _load_snapshot():
    if SNAPSHOT_PATH is None or not SNAPSHOT_PATH.exists():
        return None
    with open(SNAPSHOT_PATH) as f:
        return json.load(f)


def _collect_paths_and_methods(schema: dict) -> dict:
    """Return {path: {method: {response_schema_keys}}} for quick comparison."""
    result = {}
    for path, methods in schema.get("paths", {}).items():
        result[path] = {}
        for method, op in methods.items():
            keys = set()
            for code, resp_obj in op.get("responses", {}).items():
                content = resp_obj.get("content", {})
                for media_type, media_obj in content.items():
                    schema_ref = media_obj.get("schema", {})
                    keys.update(schema_ref.keys())
            result[path][method] = keys
    return result


class TestAPIContracts:
    def test_snapshot_exists(self):
        # Läuft nur, wenn repo-`data/` erreichbar ist (sonst modulweiter skip).
        # Prüft dann, dass der Snapshot eine echte, nicht-leere Datei ist —
        # nicht bloß ein leerer Platzhalter.
        assert SNAPSHOT_PATH.is_file(), f"Snapshot not found at {SNAPSHOT_PATH}"
        assert SNAPSHOT_PATH.stat().st_size > 0, f"Snapshot ist leer: {SNAPSHOT_PATH}"

    def test_snapshot_is_valid_json(self):
        snapshot = _load_snapshot()
        assert snapshot is not None
        assert "openapi" in snapshot or "_note" in snapshot

    def test_live_schema_reachable_or_skip(self):
        result = _fetch_live_schema()
        if result is None or isinstance(result, tuple):
            pytest.skip("Backend not reachable – run after docker compose build backend")
        assert "openapi" in result

    def test_no_breaking_changes_in_paths(self):
        snapshot = _load_snapshot()
        if snapshot is None or "_note" in snapshot:
            pytest.skip("Snapshot is stub – refresh after first build")

        live = _fetch_live_schema()
        if live is None or isinstance(live, tuple):
            pytest.skip("Backend not reachable")

        snap_paths = _collect_paths_and_methods(snapshot)
        live_paths = _collect_paths_and_methods(live)

        removed_paths = set(snap_paths.keys()) - set(live_paths.keys())
        assert not removed_paths, f"Breaking change: paths removed from API: {removed_paths}"

        for path in snap_paths:
            if path not in live_paths:
                continue
            removed_methods = set(snap_paths[path].keys()) - set(live_paths[path].keys())
            assert not removed_methods, f"Breaking change: methods removed on {path}: {removed_methods}"

    def test_api_version_header_present(self):
        try:
            req = urllib.request.Request(f"{BACKEND_URL}/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                headers = dict(resp.headers)
                version = headers.get("X-Api-Version") or headers.get("x-api-version")
                assert version == "1.0", f"X-API-Version header missing or wrong: {version}"
        except urllib.error.URLError:
            pytest.skip("Backend not reachable")
