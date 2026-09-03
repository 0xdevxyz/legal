"""
Shared test configuration and environment setup for Complyo backend tests.
Loaded automatically by pytest before any test module.
"""

import os
import sys

# Ensure required environment variables exist before any module import
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

# Stripe-Schluessel fuer Zusatzmodule: `addon_payment_routes` verlangt sie beim
# Import. Fehlten sie, sprang der Import und die 19 Tests in
# test_addon_plan_escalation.py uebersprangen mit dem Grund "laeuft im
# Backend-Container" — sie liefen aber AUCH im Backend-Container nie. Ein
# irrefuehrender Skip-Grund ist schlimmer als ein roter Test: er sieht wie
# Absicht aus. (Dieselbe Falle wie beim Wissensspeicher weiter unten.)
os.environ.setdefault("STRIPE_WEBHOOK_SECRET_ADDONS", "whsec_test_nur_fuer_tests")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_nur_fuer_tests")

# Make backend package importable from tests/ subdirectory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ---------------------------------------------------------------------------
# Der Wissensspeicher (Gesetzestexte + Rechtstext-Vorlagen)
# ---------------------------------------------------------------------------
#
# Die Anwendung bekommt ihn als Volume: `./knowledge:/data/knowledge:ro`
# (docker-compose). Wer die Tests in einem nackten Container startet, hat ihn
# nicht — und bekam dann 32 rote Tests, die wie kaputte Rechtstexte aussahen.
#
# Im Audit vom 10.08.2026 haben genau diese 32 Fehlschlaege tagelang als
# "vorbestehend" gegolten. Sie waren es nicht: die Vorlagen lagen in der
# Produktion vollstaendig vor, im Log stand kein einziges
# "Template nicht gefunden". Kaputt war der Testaufruf, nicht das Produkt.
#
# Ein fehlender Mount soll deshalb SAGEN, dass er fehlt — statt sich als
# Produktfehler zu verkleiden. Die betroffenen Tests ueberspringen dann mit
# einem Grund, den man lesen kann.
_VAULT = os.getenv("KNOWLEDGE_VAULT_PATH", "/data/knowledge")
os.environ.setdefault("KNOWLEDGE_VAULT_PATH", _VAULT)

VAULT_VORHANDEN = os.path.isdir(os.path.join(_VAULT, "templates", "legal"))

VAULT_HINWEIS = (
    f"Wissensspeicher fehlt unter {_VAULT}. Die Tests brauchen ihn so, wie ihn "
    f"die Anwendung bekommt:\n"
    f"    docker run --rm -v $(pwd)/backend:/app "
    f"-v $(pwd)/knowledge:/data/knowledge:ro -w /app legal-backend "
    f"python -m pytest tests/ -q"
)


def pytest_configure(config):
    """Einmal deutlich sagen, wenn die Umgebung unvollstaendig ist."""
    if not VAULT_VORHANDEN:
        config.stash.setdefault("complyo_hinweise", [])
        print(f"\n\033[33m! {VAULT_HINWEIS}\033[0m\n")
