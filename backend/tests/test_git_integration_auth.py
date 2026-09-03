"""
Auth- und Verschlüsselungs-Wächter für die Git-Integration
==========================================================

Der PR-Kanal ist der strategische Auslieferungsweg (Betreiber-Entscheidung
29.07.2026): die KI schreibt nie selbst in die Kundenseite, der Kunde merged
den PR. Damit das trägt, müssen zwei Dinge dauerhaft gelten:

1. Jede Route verlangt einen angemeldeten Nutzer (OAuth-Tokens und Repos sind
   kontogebunden).
2. OAuth-Tokens liegen nie im Klartext in der Datenbank — ein GitHub-Token
   erlaubt Schreibzugriff auf Kunden-Repositories.

Statische Wächter nach dem Muster von test_ab_test_auth.py.
"""
import os
import re

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(name: str) -> str:
    with open(os.path.join(_BACKEND, name), encoding="utf-8") as fh:
        return fh.read()


_ROUTE_PATTERN = re.compile(
    r'@git_router\.(get|post|patch|delete|put)\("([^"]*)"[^)]*\)\s*\n'
    r'async def (\w+)\(((?:[^()]|\([^()]*\))*)\)',
    re.S,
)


def _routen():
    src = _lese("git_routes.py")
    for m in _ROUTE_PATTERN.finditer(src):
        methode, pfad, fn, signatur = m.group(1), m.group(2), m.group(3), m.group(4)
        yield methode.upper(), pfad, fn, "get_current_user" in signatur


class TestGitRouten:
    def test_routen_werden_erkannt(self):
        assert len(list(_routen())) >= 5

    def test_jede_route_verlangt_login(self):
        offen = {f"{m} {p}" for m, p, _, geschuetzt in _routen() if not geschuetzt}
        assert not offen, "Git-Route(n) ohne get_current_user: " + ", ".join(sorted(offen))


class TestTokenVerschluesselung:
    def test_speichern_verschluesselt(self):
        """Der INSERT in git_credentials darf nur verschlüsselte Werte sehen."""
        src = _lese("git_routes.py")
        insert_block = src.split("INSERT INTO git_credentials", 1)[0].rsplit("async def", 1)[1]
        assert "encrypt_token(" in insert_block, (
            "_save_git_credentials verschlüsselt nicht mehr vor dem INSERT"
        )
        # Das Klartext-Feld darf nicht mehr direkt an execute gehen.
        nach_insert = src.split("INSERT INTO git_credentials", 1)[1][:400]
        assert "credentials.access_token" not in nach_insert, (
            "Klartext-Token wird wieder direkt gespeichert"
        )

    def test_lesen_entschluesselt(self):
        src = _lese("git_routes.py")
        assert "decrypt_token(row[" in src, "_get_git_credentials entschlüsselt nicht mehr"

    def test_fail_closed_ohne_schluessel(self):
        """Ohne GIT_TOKEN_ENC_KEY: speichern lehnt ab, statt Klartext zu schreiben."""
        src = _lese("git_token_crypto.py")
        assert "GitTokenCryptoError" in src
        assert 'os.getenv("GIT_TOKEN_ENC_KEY"' in src
        # encrypt ohne Schlüssel muss werfen — nachvollzogen am Guard in _fernet().
        assert "raise GitTokenCryptoError" in src

    def test_crypto_verhalten(self):
        """Verhalten direkt, mit gesetztem Testschlüssel."""
        from cryptography.fernet import Fernet
        os.environ["GIT_TOKEN_ENC_KEY"] = Fernet.generate_key().decode()
        try:
            from git_token_crypto import decrypt_token, encrypt_token
            ct = encrypt_token("ghp_abc")
            assert ct != "ghp_abc" and decrypt_token(ct) == "ghp_abc"
            assert encrypt_token(None) is None and decrypt_token(None) is None
        finally:
            os.environ.pop("GIT_TOKEN_ENC_KEY", None)

    def test_falscher_ciphertext_gibt_nie_klartext_zurueck(self):
        from cryptography.fernet import Fernet
        os.environ["GIT_TOKEN_ENC_KEY"] = Fernet.generate_key().decode()
        try:
            from git_token_crypto import GitTokenCryptoError, decrypt_token
            with pytest.raises(GitTokenCryptoError):
                decrypt_token("kein-echter-ciphertext")
        finally:
            os.environ.pop("GIT_TOKEN_ENC_KEY", None)


class TestDuplikateBleibenEntfernt:
    def test_propose_pr_bleibt_entfernt(self):
        src = _lese("fix_routes.py")
        assert '"/propose-pr"' not in src
        assert "ProposePRRequest" not in src

    def test_github_integration_bleibt_entfernt(self):
        assert not os.path.exists(
            os.path.join(_BACKEND, "compliance_engine", "github_integration.py")
        )
