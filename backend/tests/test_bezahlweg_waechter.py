"""Der Betriebswächter meldet, wenn niemand bezahlen kann.

Stripe im Testmodus ist kein technischer Ausfall: jede Route antwortet, der
Checkout öffnet sich, nur echte Karten werden abgelehnt. Genau deshalb blieb
der Zustand vom 31.08. bis 11.09.2026 unbemerkt auf einer Entscheidungsliste.
Diese Tests halten fest, dass der Wächter ihn wie einen Ausfall behandelt.
"""
import os
import sys

HIER = os.path.dirname(__file__)
BACKEND = os.path.abspath(os.path.join(HIER, '..'))
sys.path.insert(0, os.path.join(BACKEND, 'cronjobs'))


def _waechter(monkeypatch, **env):
    for modul in ("betriebswaechter",):
        sys.modules.pop(modul, None)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import betriebswaechter
    return betriebswaechter


def test_testschluessel_wird_gemeldet(monkeypatch):
    w = _waechter(monkeypatch, ENVIRONMENT="production", STRIPE_SECRET_KEY="sk_test_abc")
    befunde = w.pruefe_bezahlweg()
    assert [s for s, _ in befunde] == ["stripe-testmodus"]
    assert "kein Kunde kann bezahlen" in befunde[0][1]


def test_liveschluessel_ist_ruhig(monkeypatch):
    w = _waechter(monkeypatch, ENVIRONMENT="production", STRIPE_SECRET_KEY="sk_live_abc")
    assert w.pruefe_bezahlweg() == []


def test_fehlender_schluessel_wird_gemeldet(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    w = _waechter(monkeypatch, ENVIRONMENT="production")
    assert [s for s, _ in w.pruefe_bezahlweg()] == ["stripe-schluessel-fehlt"]


def test_nur_in_produktion(monkeypatch):
    """Die Testsuite selbst läuft mit sk_test_dummy; sie darf keinen Alarm auslösen."""
    w = _waechter(monkeypatch, ENVIRONMENT="test", STRIPE_SECRET_KEY="sk_test_dummy")
    assert w.pruefe_bezahlweg() == []


def test_ist_im_hauptlauf_verdrahtet():
    """Eine Prüfung, die niemand aufruft, bewacht nichts."""
    with open(os.path.join(BACKEND, 'cronjobs', 'betriebswaechter.py'), encoding='utf-8') as f:
        s = f.read()
    hauptlauf = s[s.index("async def main()"):]
    assert "pruefe_bezahlweg()" in hauptlauf
