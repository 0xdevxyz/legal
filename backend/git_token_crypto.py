"""Verschlüsselung für Git-OAuth-Tokens (git_credentials).

Fail-closed: Ohne konfigurierten Schlüssel (GIT_TOKEN_ENC_KEY) wird kein Token
gespeichert und keiner gelesen — lieber "GitHub-Verbindung nicht verfügbar" als
Klartext-Tokens in der Datenbank. Ein GitHub-Token erlaubt Schreibzugriff auf
Kunden-Repositories; ein DB-Leak dürfte daraus keine Repo-Übernahme machen.

Schlüssel erzeugen (einmalig, in .env als GIT_TOKEN_ENC_KEY):
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


class GitTokenCryptoError(RuntimeError):
    """Verschlüsselung nicht verfügbar oder Token nicht entschlüsselbar."""


def _fernet() -> Fernet:
    key = os.getenv("GIT_TOKEN_ENC_KEY", "").strip()
    if not key:
        raise GitTokenCryptoError(
            "GIT_TOKEN_ENC_KEY ist nicht gesetzt — Git-Tokens werden ohne "
            "Schlüssel weder gespeichert noch gelesen (fail-closed)."
        )
    try:
        return Fernet(key.encode())
    except Exception as e:  # ungültiges Schlüsselformat
        raise GitTokenCryptoError(f"GIT_TOKEN_ENC_KEY ist kein gültiger Fernet-Schlüssel: {e}")


def encrypt_token(token: Optional[str]) -> Optional[str]:
    if token is None or token == "":
        return None
    return _fernet().encrypt(token.encode()).decode()


def decrypt_token(ciphertext: Optional[str]) -> Optional[str]:
    if ciphertext is None or ciphertext == "":
        return None
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        # Falscher Schlüssel oder korrupter Wert — niemals den Ciphertext
        # zurückgeben, das wäre je nach Aufrufer ein stiller Klartext-Ersatz.
        raise GitTokenCryptoError(f"Git-Token nicht entschlüsselbar: {e}")
