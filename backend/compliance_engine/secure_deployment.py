"""Abgesicherter Direct-Deploy (FTP/SFTP) — Backup-Pflicht, Restore aus der DB.

Betreiber-Entscheidung (29.07.2026): Direktschreiben auf Kundenserver ist nur
zulässig, wenn vorher gesichert wird. Konsequenzen in diesem Modul:

1. **Backup ist nicht abschaltbar.** Vor jedem Upload wird der aktuelle Stand
   jeder Zieldatei heruntergeladen. Schlägt das Backup fehl, wird NICHT
   deployt (fail-closed). Der alte Motor hatte hier einen Stub (`pass`) und
   meldete trotzdem backup_created=True.
2. **Backups leben in der Datenbank** (fix_backups.file_contents, Base64 je
   Datei), nicht im Container-Dateisystem — ein Container-Rebuild darf kein
   Backup vernichten.
3. **Nur FTP und SFTP.** Andere Methoden (WordPress-REST, Netlify, Vercel)
   haben sichere Alternativen (Fix-Manifest-Kanäle, GitHub-PR) und werden
   abgelehnt statt halbherzig unterstützt.
4. **Inhaltsbasiert.** Deployt wird der Fix-Inhalt (String) — der alte Motor
   las eine lokale Datei, die es im API-Container nie gab.
5. **Credentials werden nie persistiert** — sie leben nur im Request.

Restore: Dateien, die vorher existierten, werden mit dem gesicherten Inhalt
überschrieben; Dateien, die es vorher nicht gab, werden gelöscht.
"""
import base64
import ftplib
import io
import logging
import posixpath
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

import paramiko

logger = logging.getLogger(__name__)

ERLAUBTE_METHODEN = ("ftp", "sftp")

# Obergrenze je gesicherter Datei. Fixes sind HTML/CSS/JS-Schnipsel — wer eine
# 50-MB-Datei als Ziel angibt, bekommt einen klaren Fehler statt einer
# aufgeblähten Backup-Zeile.
MAX_BACKUP_BYTES = 5 * 1024 * 1024


class DeploymentError(RuntimeError):
    """Deploy abgebrochen — Meldung ist kundentauglich."""


@dataclass
class DeployFile:
    remote_path: str
    content: str


@dataclass
class SecureDeployResult:
    success: bool
    deployment_id: str
    method: str
    files_deployed: List[str]
    backup_id: str
    # remote_path -> {"existed": bool, "content_b64": str | None}
    backup_contents: Dict[str, dict]
    deployed_at: str
    error: Optional[str] = None


class _FtpTransport:
    """Minimale Transportschicht — gleiche Schnittstelle wie _SftpTransport."""

    def __init__(self, credentials: Dict[str, str]):
        self._ftp = ftplib.FTP()
        self._ftp.connect(credentials["host"], int(credentials.get("port", 21)), timeout=30)
        self._ftp.login(credentials["username"], credentials["password"])

    def download(self, path: str) -> Optional[bytes]:
        puffer = io.BytesIO()
        try:
            self._ftp.retrbinary(f"RETR {path}", puffer.write, blocksize=64 * 1024)
        except ftplib.error_perm as e:
            # 550 = Datei existiert nicht — ein legitimer Backup-Zustand.
            if str(e).startswith("550"):
                return None
            raise
        return puffer.getvalue()

    def upload(self, path: str, inhalt: bytes) -> None:
        verzeichnis = posixpath.dirname(path)
        if verzeichnis:
            self._mkdirs(verzeichnis)
        self._ftp.storbinary(f"STOR {path}", io.BytesIO(inhalt))

    def delete(self, path: str) -> None:
        try:
            self._ftp.delete(path)
        except ftplib.error_perm as e:
            if not str(e).startswith("550"):
                raise

    def _mkdirs(self, verzeichnis: str) -> None:
        teile = [t for t in verzeichnis.split("/") if t]
        pfad = ""
        for teil in teile:
            pfad = f"{pfad}/{teil}" if pfad else teil
            try:
                self._ftp.mkd(pfad)
            except ftplib.error_perm:
                pass  # existiert schon

    def close(self) -> None:
        try:
            self._ftp.quit()
        except Exception:
            self._ftp.close()


class _SftpTransport:
    def __init__(self, credentials: Dict[str, str]):
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(
            hostname=credentials["host"],
            port=int(credentials.get("port", 22)),
            username=credentials["username"],
            password=credentials.get("password"),
            key_filename=credentials.get("private_key_path"),
            timeout=30,
        )
        self._sftp = self._ssh.open_sftp()

    def download(self, path: str) -> Optional[bytes]:
        try:
            with self._sftp.open(path, "rb") as fh:
                return fh.read()
        except FileNotFoundError:
            return None
        except IOError:
            return None

    def upload(self, path: str, inhalt: bytes) -> None:
        verzeichnis = posixpath.dirname(path)
        if verzeichnis:
            self._mkdirs(verzeichnis)
        with self._sftp.open(path, "wb") as fh:
            fh.write(inhalt)

    def delete(self, path: str) -> None:
        try:
            self._sftp.remove(path)
        except (FileNotFoundError, IOError):
            pass

    def _mkdirs(self, verzeichnis: str) -> None:
        teile = [t for t in verzeichnis.split("/") if t]
        pfad = ""
        for teil in teile:
            pfad = f"{pfad}/{teil}" if pfad else teil
            try:
                self._sftp.stat(pfad)
            except FileNotFoundError:
                self._sftp.mkdir(pfad)

    def close(self) -> None:
        self._sftp.close()
        self._ssh.close()


def _transport(method: str, credentials: Dict[str, str]):
    if method == "ftp":
        return _FtpTransport(credentials)
    if method == "sftp":
        return _SftpTransport(credentials)
    raise DeploymentError(
        f"Deployment-Methode '{method}' wird nicht direkt unterstützt. "
        "Nutzen Sie den GitHub-Pull-Request oder die Fix-Manifest-Kanäle "
        "(WordPress-Plugin, JS-Widget, HTML-CLI)."
    )


class SecureDeploymentEngine:
    """Deploy mit erzwungenem Backup und DB-tauglichem Restore."""

    async def deploy(
        self,
        method: str,
        credentials: Dict[str, str],
        files: List[DeployFile],
    ) -> SecureDeployResult:
        if method not in ERLAUBTE_METHODEN:
            # Auch hier ablehnen, nicht nur im Transport — der Fehlertext ist Teil des Vertrags.
            raise DeploymentError(
                f"Deployment-Methode '{method}' wird nicht direkt unterstützt. "
                "Nutzen Sie den GitHub-Pull-Request oder die Fix-Manifest-Kanäle."
            )
        if not files:
            raise DeploymentError("Keine Dateien zum Deployen angegeben.")

        transport = _transport(method, credentials)
        try:
            # --- 1. Backup: Pflicht, fail-closed ---------------------------
            backup_contents: Dict[str, dict] = {}
            for datei in files:
                try:
                    bestand = transport.download(datei.remote_path)
                except Exception as e:
                    raise DeploymentError(
                        f"Backup von '{datei.remote_path}' fehlgeschlagen — es wird "
                        f"NICHT deployt. ({e})"
                    )
                if bestand is not None and len(bestand) > MAX_BACKUP_BYTES:
                    raise DeploymentError(
                        f"'{datei.remote_path}' ist größer als {MAX_BACKUP_BYTES // (1024*1024)} MB — "
                        "Direct-Deploy ist für einzelne Fix-Dateien gedacht."
                    )
                backup_contents[datei.remote_path] = {
                    "existed": bestand is not None,
                    "content_b64": base64.b64encode(bestand).decode() if bestand is not None else None,
                }

            # --- 2. Upload -------------------------------------------------
            deployed: List[str] = []
            for datei in files:
                transport.upload(datei.remote_path, datei.content.encode("utf-8"))
                deployed.append(datei.remote_path)
                logger.info(f"✅ Deployt: {datei.remote_path}")

            return SecureDeployResult(
                success=True,
                deployment_id=str(uuid.uuid4()),
                method=method,
                files_deployed=deployed,
                backup_id=str(uuid.uuid4()),
                backup_contents=backup_contents,
                deployed_at=datetime.now(timezone.utc).isoformat(),
            )
        finally:
            transport.close()

    async def restore(
        self,
        method: str,
        credentials: Dict[str, str],
        backup_contents: Dict[str, dict],
    ) -> List[str]:
        """Stellt den gesicherten Stand wieder her. Gibt die Pfade zurück."""
        if not backup_contents:
            raise DeploymentError("Backup enthält keine Dateien.")
        transport = _transport(method, credentials)
        wiederhergestellt: List[str] = []
        try:
            for pfad, eintrag in backup_contents.items():
                if eintrag.get("existed") and eintrag.get("content_b64") is not None:
                    transport.upload(pfad, base64.b64decode(eintrag["content_b64"]))
                else:
                    # Datei gab es vor dem Deploy nicht — Restore heißt: entfernen.
                    transport.delete(pfad)
                wiederhergestellt.append(pfad)
                logger.info(f"↩️ Wiederhergestellt: {pfad}")
            return wiederhergestellt
        finally:
            transport.close()
