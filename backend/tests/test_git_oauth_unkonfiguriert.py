"""
Was passiert, wenn die OAuth-App gar nicht registriert ist?

In der Produktion sind `GITHUB_CLIENT_ID` und `GITHUB_CLIENT_SECRET` leer.
Die Anmelde-URL wurde trotzdem gebaut — mit leerem `client_id`. Der Kunde
klickte auf „Repository verbinden" und landete auf einer GitHub-Fehlerseite,
die ihm nicht sagt, dass der Fehler bei uns liegt. Dieselbe Klasse Fehler wie
der fehlende `import re`: unser Problem, dem Kunden als seines vorgelegt.
"""
import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import git_routes

NUTZER = {"user_id": "u-1", "email": "kunde@example.org"}


@pytest.fixture
def ohne_datenbank(monkeypatch):
    async def merke_state(state, daten):
        return None
    monkeypatch.setattr(git_routes, "_set_oauth_state", merke_state)


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["github", "gitlab"])
async def test_ohne_registrierte_app_kommt_503_mit_ausweg(monkeypatch, ohne_datenbank, provider):
    for attribut in ("github_client_id", "github_client_secret",
                     "gitlab_client_id", "gitlab_client_secret"):
        monkeypatch.setattr(git_routes.git_service, attribut, "")

    with pytest.raises(HTTPException) as fehler:
        await git_routes.get_oauth_url(
            provider=provider, redirect_uri="https://app.complyo.tech/cb", user=NUTZER)

    assert fehler.value.status_code == 503
    text = str(fehler.value.detail)
    assert "auf unserer Seite" in text, "der Kunde muss erfahren, wo der Fehler liegt"
    assert {"github": "GitHub", "gitlab": "GitLab"}[provider] in text, \
        "Markenschreibweise: .capitalize() macht daraus Github/Gitlab"
    assert "koennen" not in text and "ueber" not in text, \
        "Umlaute nicht umschreiben — der Kunde liest diesen Satz"
    assert "Patch" in text or "Widget" in text, "ohne Ausweg ist die Meldung eine Sackgasse"


@pytest.mark.asyncio
async def test_halb_konfiguriert_zaehlt_als_nicht_konfiguriert(monkeypatch, ohne_datenbank):
    """Nur die client_id zu setzen fuehrt spaeter zum Fehler im Callback — zu spaet."""
    monkeypatch.setattr(git_routes.git_service, "github_client_id", "Iv1.abc123")
    monkeypatch.setattr(git_routes.git_service, "github_client_secret", "")

    with pytest.raises(HTTPException) as fehler:
        await git_routes.get_oauth_url(
            provider="github", redirect_uri="https://app.complyo.tech/cb", user=NUTZER)

    assert fehler.value.status_code == 503


@pytest.mark.asyncio
async def test_mit_registrierter_app_entsteht_eine_brauchbare_url(monkeypatch, ohne_datenbank):
    monkeypatch.setattr(git_routes.git_service, "github_client_id", "Iv1.abc123")
    monkeypatch.setattr(git_routes.git_service, "github_client_secret", "geheim")

    antwort = await git_routes.get_oauth_url(
        provider="github", redirect_uri="https://app.complyo.tech/cb", user=NUTZER)

    assert "client_id=Iv1.abc123" in antwort.url
    assert f"state={antwort.state}" in antwort.url
    assert len(antwort.state) >= 32, "CSRF-State muss raten-sicher sein"


@pytest.mark.asyncio
async def test_unbekannter_provider_bleibt_400(monkeypatch, ohne_datenbank):
    """400 statt 503: hier liegt der Fehler tatsaechlich beim Aufrufer."""
    with pytest.raises(HTTPException) as fehler:
        await git_routes.get_oauth_url(
            provider="bitbucket", redirect_uri="https://app.complyo.tech/cb", user=NUTZER)

    assert fehler.value.status_code == 400
