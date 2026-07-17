import os
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

import inspect
import re


def _service():
    """AuthService an __init__ vorbei bauen und die benötigten Felder selbst setzen.

    Die Tests umgehen `__init__` (braucht einen echten asyncpg-Pool). Dadurch muss
    jedes Attribut, das die Methoden lesen, hier gesetzt werden — sonst kippt der
    Test mit AttributeError statt eine echte Aussage zu treffen. Genau das war der
    Fall, als `self.redis` (JTI-Blacklist) im Produktcode dazukam und hier fehlte.
    `redis = None` ist der bewusste Zustand „ohne Redis": `create_access_token`
    überspringt dann die JTI-Registrierung.
    """
    from auth_service import AuthService

    service = AuthService.__new__(AuthService)
    service.jwt_secret = "test-secret"
    service.jwt_issuer = "https://complyo.de"
    service.jwt_audience = "complyo-api"
    service.access_token_expire = 60
    service.redis = None
    return service


class TestAuthService:
    def test_create_access_token(self):
        service = _service()
        token = service.create_access_token("user-123")
        assert token is not None
        assert isinstance(token, str)

    def test_verify_token_valid(self):
        service = _service()
        token = service.create_access_token("user-123")
        payload = service.verify_token(token)
        assert payload is not None
        assert payload["user_id"] == "user-123"

    def test_verify_token_invalid(self):
        service = _service()
        result = service.verify_token("invalid.token.here")
        assert result is None

    def test_konstruktor_und_testaufbau_bleiben_synchron(self):
        """Wächter: Schlägt an, sobald `__init__` ein Feld setzt, das `_service()` nicht kennt.

        Die drei Tests oben bauen das Objekt an `__init__` vorbei. Wächst der
        Konstruktor, laufen sie sonst wieder in AttributeError — so wie bei `redis`.
        """
        from auth_service import AuthService

        quelle = inspect.getsource(AuthService.__init__)
        gesetzt = set(re.findall(r"self\.(\w+)\s*=", quelle))
        bekannt = set(vars(_service()))
        # Felder, die die getesteten Methoden nachweislich nicht brauchen:
        unbenutzt = {"db_pool", "refresh_token_expire", "pwd_context", "algorithm"}
        fehlend = gesetzt - bekannt - unbenutzt
        assert not fehlend, (
            f"AuthService.__init__ setzt neue Felder, die der Testaufbau nicht kennt: "
            f"{sorted(fehlend)}. Entweder in _service() ergänzen oder — falls die "
            f"getesteten Methoden sie nicht brauchen — in `unbenutzt` aufnehmen."
        )
