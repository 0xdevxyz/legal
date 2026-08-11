"""
Ein Import darf nicht am Dateisystem scheitern.

`file_storage_service` instanziiert am Modulende einen Singleton, dessen
Konstruktor Verzeichnisse anlegte. Wo `/app` nicht schreibbar ist — auf dem
CI-Runner zum Beispiel — starb dabei nicht der Upload, sondern der **Import**.
Sieben Testdateien fielen schon beim Einsammeln um, mit einer Meldung, die
nichts mit ihrem Inhalt zu tun hatte. Die Backend-Tests der CI sind daran
seit Wochen rot, ohne dass ein einziger echter Fehler dahintersteckte.

Dieselbe Klasse wie der irrefuehrende Skip-Grund in
test_addon_plan_escalation.py: ein Signal, das auf etwas anderes zeigt als
auf die Ursache, ist schlimmer als gar keins.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from file_storage_service import FileStorageService

# Ein Pfad, unter dem sich garantiert nichts anlegen laesst.
UNSCHREIBBAR = "/proc/kein-verzeichnis/uploads"


def test_konstruktor_stirbt_nicht_an_unschreibbarem_pfad(caplog):
    """Der Import darf durchlaufen — sonst reisst er fremde Module mit."""
    with caplog.at_level("WARNING"):
        dienst = FileStorageService(storage_path=UNSCHREIBBAR)

    assert dienst.storage_path == UNSCHREIBBAR
    assert any("nicht anlegbar" in r.getMessage() for r in caplog.records), \
        "das Betriebsproblem muss im Log stehen"


def test_die_warnung_nennt_pfad_und_ausweg(caplog):
    """Eine Warnung ohne Handlungsanweisung wird ueberlesen."""
    with caplog.at_level("WARNING"):
        FileStorageService(storage_path=UNSCHREIBBAR)

    text = " ".join(r.getMessage() for r in caplog.records)
    assert UNSCHREIBBAR in text
    assert "FILE_STORAGE_PATH" in text


def test_schreiben_scheitert_weiterhin_hoerbar():
    """Leise werden darf der Fehler nicht — nur an der richtigen Stelle laut."""
    dienst = FileStorageService(storage_path=UNSCHREIBBAR)

    with pytest.raises(OSError):
        dienst._get_user_dir(1)


def test_schreibbarer_pfad_wird_wie_bisher_angelegt(tmp_path):
    """Das Verhalten in der Produktion bleibt unveraendert."""
    ziel = tmp_path / "uploads"
    dienst = FileStorageService(storage_path=str(ziel))

    assert ziel.is_dir()
    assert (ziel / "ai_documentation").is_dir()
    assert dienst._get_user_dir(42).is_dir()


def test_die_sieben_module_lassen_sich_einsammeln():
    """Genau die Dateien, die in der CI beim Einsammeln umfielen."""
    os.environ.setdefault("FILE_STORAGE_PATH", "/tmp/complyo-test-uploads")
    import importlib

    for modul in ("file_storage_service", "cookie_compliance_routes"):
        importlib.import_module(modul)
