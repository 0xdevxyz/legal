"""
E2E fuer den Rueckweg des Direct-Deploy: FTP-Rollback, wirklich gelaufen.

Warum dieser Test existiert
---------------------------
`test_secure_deploy.py` prueft die Logik gegen einen Fake-Transport. Was damit
nicht geprueft war: ob der Rollback ueber eine echte Verbindung, mit echten
Dateien, tatsaechlich den alten Zustand herstellt. Die Tabelle `fix_backups`
hatte null Zeilen — dieser Weg war noch nie gegangen worden.

Deshalb laeuft hier ein echter FTP-Server im Testprozess (nicht gemockt, nur
lokal und wegwerfbar, damit keine fremden Zugangsdaten noetig sind). Geprueft
wird nicht der Rueckgabewert des Motors, sondern der Inhalt auf der Platte —
dieselbe Lehre wie bei der Alt-Text-Speicherung: dem Rueckgabewert glauben
heisst, sechs Wochen lang nichts zu merken.

Der entscheidende Fall ist Nummer 2: eine Datei, die es vorher **nicht** gab,
muss beim Rollback verschwinden und nicht bloss geleert werden.
"""
import asyncio
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# pyftpdlib traegt keine weiteren Abhaengigkeiten und steht in requirements.txt.
# Fehlt es doch, ist der Grund im Klartext lesbar statt als stiller Skip.
pyftpdlib = pytest.importorskip(
    "pyftpdlib",
    reason=("pyftpdlib fehlt — ohne echten FTP-Server ist der Rollback nur behauptet. "
            "Installieren: pip install pyftpdlib"),
)

from compliance_engine.secure_deployment import (  # noqa: E402
    DeployFile, DeploymentError, SecureDeploymentEngine,
)

BENUTZER = "rollback-test"
PASSWORT = "rollback-test"

ALT = "<!-- Bestand vor complyo -->\n<h1>Hallo Welt</h1>\n"
NEU = "<!-- von complyo geaendert -->\n<h1>Hallo Welt</h1>\n<p>barrierefrei</p>\n"


@pytest.fixture
def ftp(tmp_path):
    """Ein Wegwerf-FTP-Server auf einem freien Port, nur auf localhost."""
    from pyftpdlib.authorizers import DummyAuthorizer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers import FTPServer

    wurzel = str(tmp_path)
    auth = DummyAuthorizer()
    auth.add_user(BENUTZER, PASSWORT, wurzel, perm="elradfmwMT")
    handler = FTPHandler
    handler.authorizer = auth

    server = FTPServer(("127.0.0.1", 0), handler)
    port = server.address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield {
            "wurzel": wurzel,
            "zugang": {"host": "127.0.0.1", "port": port,
                       "username": BENUTZER, "password": PASSWORT},
        }
    finally:
        server.close_all()


def lies(wurzel, name):
    """Liest direkt vom Dateisystem — unabhaengig vom Motor, der geprueft wird."""
    pfad = os.path.join(wurzel, name)
    if not os.path.exists(pfad):
        return None
    with open(pfad, "rb") as fh:
        return fh.read()


def schreibe(wurzel, name, inhalt):
    with open(os.path.join(wurzel, name), "w") as fh:
        fh.write(inhalt)


# =============================================================================
# Der Hauptfall: geaenderte Datei zurueckrollen
# =============================================================================

@pytest.mark.asyncio
async def test_geaenderte_datei_kommt_byteweise_zurueck(ftp):
    wurzel, zugang = ftp["wurzel"], ftp["zugang"]
    schreibe(wurzel, "bestand.html", ALT)
    motor = SecureDeploymentEngine()

    erg = await motor.deploy(method="ftp", credentials=zugang,
                             files=[DeployFile(remote_path="/bestand.html", content=NEU)])
    assert erg.success, erg
    assert lies(wurzel, "bestand.html") == NEU.encode()

    wieder = await motor.restore(method="ftp", credentials=zugang,
                                 backup_contents=erg.backup_contents)

    assert wieder == ["/bestand.html"]
    assert lies(wurzel, "bestand.html") == ALT.encode()


@pytest.mark.asyncio
async def test_backup_merkt_sich_dass_die_datei_existierte(ftp):
    """Ohne dieses Merkmal kann der Rollback nicht zwischen 'zurueck' und 'weg' unterscheiden."""
    wurzel, zugang = ftp["wurzel"], ftp["zugang"]
    schreibe(wurzel, "bestand.html", ALT)

    erg = await SecureDeploymentEngine().deploy(
        method="ftp", credentials=zugang,
        files=[DeployFile(remote_path="/bestand.html", content=NEU)])

    assert erg.backup_contents["/bestand.html"]["existed"] is True


@pytest.mark.asyncio
async def test_neu_angelegte_datei_wird_geloescht_nicht_geleert(ftp):
    """Der Fall, den man vergisst — und der eine fremde Website veraendert zuruecklaesst."""
    wurzel, zugang = ftp["wurzel"], ftp["zugang"]
    motor = SecureDeploymentEngine()

    erg = await motor.deploy(method="ftp", credentials=zugang,
                             files=[DeployFile(remote_path="/neu.html", content=NEU)])
    assert erg.success
    assert erg.backup_contents["/neu.html"]["existed"] is False
    assert lies(wurzel, "neu.html") is not None

    await motor.restore(method="ftp", credentials=zugang,
                        backup_contents=erg.backup_contents)

    assert lies(wurzel, "neu.html") is None, "Datei blieb stehen — die Seite ist nicht im Ausgangszustand"


# =============================================================================
# Fail-closed: lieber nichts tun als ohne Rueckweg schreiben
# =============================================================================

@pytest.mark.asyncio
async def test_ohne_backup_wird_nicht_deployt(ftp):
    """Kein Rueckweg, kein Hinweg. Der Bestand muss unangetastet bleiben."""
    wurzel, zugang = ftp["wurzel"], ftp["zugang"]
    schreibe(wurzel, "bestand.html", ALT)
    unerreichbar = dict(zugang, port=1)

    with pytest.raises(Exception):
        await SecureDeploymentEngine().deploy(
            method="ftp", credentials=unerreichbar,
            files=[DeployFile(remote_path="/bestand.html", content="ZERSTOERT")])

    assert lies(wurzel, "bestand.html") == ALT.encode()


@pytest.mark.asyncio
async def test_leeres_backup_wird_abgelehnt(ftp):
    """Ein Restore ohne Inhalt wuerde stillschweigend nichts tun und Erfolg melden."""
    with pytest.raises(DeploymentError):
        await SecureDeploymentEngine().restore(
            method="ftp", credentials=ftp["zugang"], backup_contents={})


@pytest.mark.asyncio
async def test_nicht_unterstuetzte_methode_verweist_auf_den_sicheren_weg(ftp):
    with pytest.raises(DeploymentError) as fehler:
        await SecureDeploymentEngine().deploy(
            method="netlify", credentials=ftp["zugang"],
            files=[DeployFile(remote_path="/x.html", content="y")])

    assert "netlify" in str(fehler.value).lower() or "unterstütz" in str(fehler.value).lower()
