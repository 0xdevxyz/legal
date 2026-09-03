"""
Git Integration API Routes
Automatische PR-Erstellung für Barrierefreiheits-Fixes

Endpoints:
- GET /api/v2/git/oauth/{provider}/url - OAuth URL generieren
- POST /api/v2/git/oauth/{provider}/callback - OAuth Code einlösen
- POST /api/v2/git/repos/connect - Repository verbinden
- POST /api/v2/git/apply-patches - Patches anwenden und PR erstellen
- GET /api/v2/git/repos - Verbundene Repositories
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import json
import secrets
from datetime import datetime
from dependencies import get_current_user

from git_service import (
    git_service, GitProvider, GitCredentials, RepoInfo, PullRequestResult, PRStatus
)
from git_token_crypto import GitTokenCryptoError, decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

# Router Setup
git_router = APIRouter(prefix="/api/v2/git", tags=["git-integration"])

# Global references
db_pool = None
auth_service = None
redis_client = None

_OAUTH_STATE_TTL = 600  # 10 minutes


async def _set_oauth_state(state: str, data: Dict[str, Any]) -> None:
    if redis_client:
        await redis_client.setex(f"oauth_state:{state}", _OAUTH_STATE_TTL, json.dumps(data))
    else:
        raise RuntimeError("Redis not available – OAuth state cannot be stored securely")


async def _get_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    if redis_client:
        raw = await redis_client.get(f"oauth_state:{state}")
        return json.loads(raw) if raw else None
    raise RuntimeError("Redis not available")


async def _del_oauth_state(state: str) -> None:
    if redis_client:
        await redis_client.delete(f"oauth_state:{state}")


# =============================================================================
# Request/Response Models
# =============================================================================

class OAuthUrlResponse(BaseModel):
    """OAuth URL Response"""
    url: str
    state: str
    provider: str


class OAuthCallbackRequest(BaseModel):
    """OAuth Callback Request"""
    code: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """OAuth Callback Response"""
    success: bool
    provider: str
    user_name: Optional[str] = None
    error: Optional[str] = None


class ConnectRepoRequest(BaseModel):
    """Repository verbinden Request"""
    provider: str = Field(..., description="github oder gitlab")
    owner: str = Field(..., description="Repository Owner/Organisation")
    repo: str = Field(..., description="Repository Name")
    default_branch: str = Field("main", description="Default Branch")


class ConnectRepoResponse(BaseModel):
    """Repository verbinden Response"""
    success: bool
    repo_id: Optional[str] = None
    full_name: Optional[str] = None
    error: Optional[str] = None


class ApplyPatchesRequest(BaseModel):
    """Patches anwenden Request"""
    repo_id: str = Field(..., description="Verbundenes Repository ID")
    patches: List[Dict[str, Any]] = Field(..., description="Liste von Patches")
    feature_ids: List[str] = Field(..., description="Feature-IDs (z.B. ALT_TEXT)")
    scan_id: Optional[str] = Field(None, description="Optional Scan-ID")
    create_pr: bool = Field(True, description="PR erstellen?")


class ApplyPatchesResponse(BaseModel):
    """Patches anwenden Response"""
    success: bool
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    files_changed: List[str] = []
    error: Optional[str] = None


class ConnectedRepo(BaseModel):
    """Verbundenes Repository"""
    id: str
    provider: str
    full_name: str
    default_branch: str
    connected_at: str


# =============================================================================
# OAuth Endpoints
# =============================================================================

@git_router.get("/oauth/{provider}/url", response_model=OAuthUrlResponse)
async def get_oauth_url(
    provider: str,
    redirect_uri: str = Query(..., description="Redirect URI nach OAuth"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> OAuthUrlResponse:
    """
    Generiert OAuth-URL für Git-Provider
    
    Unterstützte Provider: github, gitlab
    """
    if provider not in ["github", "gitlab"]:
        raise HTTPException(status_code=400, detail="Unterstützte Provider: github, gitlab")

    # Ohne registrierte OAuth-App ist die Anmeldung bei GitHub sinnlos: die URL
    # wuerde mit leerem client_id gebaut und der Kunde landete auf einer
    # GitHub-Fehlerseite, ohne zu erfahren, dass der Fehler bei uns liegt.
    _schluessel = {
        "github": (git_service.github_client_id, git_service.github_client_secret),
        "gitlab": (git_service.gitlab_client_id, git_service.gitlab_client_secret),
    }[provider]
    if not all(_schluessel):
        logger.error(f"OAuth fuer {provider} angefragt, aber client_id/secret sind leer.")
        _name = {"github": "GitHub", "gitlab": "GitLab"}[provider]
        raise HTTPException(
            status_code=503,
            detail=(
                f"Die Verbindung zu {_name} ist auf unserer Seite noch nicht "
                "eingerichtet. Ihre Fixes können Sie in der Zwischenzeit als "
                "Patch-Datei herunterladen oder über das complyo-Widget ausliefern."
            ),
        )

    # Generiere State für CSRF-Schutz
    state = secrets.token_urlsafe(32)
    await _set_oauth_state(state, {
        "user_id": user.get("user_id"),
        "provider": provider,
        "redirect_uri": redirect_uri,
        "created_at": datetime.now().isoformat()
    })
    
    if provider == "github":
        url = git_service.get_github_oauth_url(redirect_uri, state)
    else:
        url = git_service.get_gitlab_oauth_url(redirect_uri, state)
    
    return OAuthUrlResponse(url=url, state=state, provider=provider)


@git_router.post("/oauth/{provider}/callback", response_model=OAuthCallbackResponse)
async def oauth_callback(
    provider: str,
    request: OAuthCallbackRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> OAuthCallbackResponse:
    """
    Verarbeitet OAuth-Callback und speichert Credentials
    """
    # Validiere State
    state_data = await _get_oauth_state(request.state)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid state - CSRF protection")
    
    if state_data.get("user_id") != user.get("user_id"):
        raise HTTPException(status_code=400, detail="State mismatch")
    
    await _del_oauth_state(request.state)
    
    # Tausche Code gegen Token
    if provider == "github":
        credentials = await git_service.exchange_github_code(
            request.code, state_data.get("redirect_uri", "")
        )
    else:
        raise HTTPException(status_code=501, detail="GitLab OAuth noch nicht implementiert")
    
    if not credentials:
        return OAuthCallbackResponse(
            success=False,
            provider=provider,
            error="Token-Austausch fehlgeschlagen"
        )
    
    # Hole User-Info und speichere in DB
    try:
        if provider == "github":
            from git_service import GitHubClient
            client = GitHubClient(credentials.access_token)
            git_user = await client.get_user()
            user_name = git_user.get("login", "Unknown")
        else:
            user_name = "Unknown"
        
        # Speichere Credentials in DB
        if db_pool:
            await _save_git_credentials(
                user.get("user_id"),
                provider,
                credentials,
                user_name
            )
        
        return OAuthCallbackResponse(
            success=True,
            provider=provider,
            user_name=user_name
        )
    
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return OAuthCallbackResponse(
            success=False,
            provider=provider,
            error=str(e)
        )


# =============================================================================
# Repository Endpoints
# =============================================================================

@git_router.post("/repos/connect", response_model=ConnectRepoResponse)
async def connect_repository(
    request: ConnectRepoRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> ConnectRepoResponse:
    """
    Verbindet ein Repository für automatische PRs
    """
    user_id = user.get("user_id")
    
    # Lade Git-Credentials
    credentials = await _get_git_credentials(user_id, request.provider)
    if not credentials:
        return ConnectRepoResponse(
            success=False,
            error=f"Keine {request.provider}-Verbindung. Bitte zuerst OAuth durchführen."
        )
    
    # Verifiziere Repository-Zugriff
    try:
        if request.provider == "github":
            from git_service import GitHubClient
            client = GitHubClient(credentials.access_token)
            repo_info = await client.get_repo(request.owner, request.repo)
            
            if not repo_info.get("id"):
                return ConnectRepoResponse(
                    success=False,
                    error=f"Repository {request.owner}/{request.repo} nicht gefunden oder kein Zugriff"
                )
            
            full_name = repo_info.get("full_name", f"{request.owner}/{request.repo}")
            default_branch = repo_info.get("default_branch", request.default_branch)
        else:
            full_name = f"{request.owner}/{request.repo}"
            default_branch = request.default_branch
        
        # Speichere in DB
        repo_id = await _save_connected_repo(
            user_id,
            request.provider,
            request.owner,
            request.repo,
            default_branch
        )
        
        return ConnectRepoResponse(
            success=True,
            repo_id=repo_id,
            full_name=full_name
        )
    
    except Exception as e:
        logger.error(f"Connect repo error: {e}")
        return ConnectRepoResponse(success=False, error=str(e))


@git_router.get("/repos", response_model=List[ConnectedRepo])
async def list_connected_repos(
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[ConnectedRepo]:
    """
    Listet alle verbundenen Repositories
    """
    user_id = user.get("user_id")
    
    if not db_pool:
        return []
    
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, provider, owner, repo, default_branch, created_at
                FROM git_connected_repos
                WHERE user_id = $1 AND active = TRUE
                ORDER BY created_at DESC
            """, user_id)
            
            return [
                ConnectedRepo(
                    id=str(row["id"]),
                    provider=row["provider"],
                    full_name=f"{row['owner']}/{row['repo']}",
                    default_branch=row["default_branch"],
                    connected_at=row["created_at"].isoformat()
                )
                for row in rows
            ]
    
    except Exception as e:
        logger.error(f"List repos error: {e}")
        return []


# =============================================================================
# Apply Patches Endpoint
# =============================================================================

@git_router.post("/apply-patches", response_model=ApplyPatchesResponse)
async def apply_patches(
    request: ApplyPatchesRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> ApplyPatchesResponse:
    """
    Wendet Patches an und erstellt einen PR
    
    Dies ist der Hauptendpoint für die Git-Integration:
    1. Lädt Repository-Info
    2. Erstellt Branch
    3. Wendet Patches an
    4. Erstellt Pull Request
    """
    user_id = user.get("user_id")
    
    # Lade Repository-Info
    repo_data = await _get_connected_repo(user_id, request.repo_id)
    if not repo_data:
        return ApplyPatchesResponse(
            success=False,
            error="Repository nicht gefunden"
        )
    
    # Lade Credentials
    credentials = await _get_git_credentials(user_id, repo_data["provider"])
    if not credentials:
        return ApplyPatchesResponse(
            success=False,
            error="Git-Verbindung abgelaufen. Bitte erneut verbinden."
        )
    
    # Erstelle RepoInfo
    repo_info = RepoInfo(
        provider=GitProvider(repo_data["provider"]),
        owner=repo_data["owner"],
        repo=repo_data["repo"],
        default_branch=repo_data["default_branch"]
    )
    
    # Erstelle PR
    logger.info(f"🔧 Applying {len(request.patches)} patches to {repo_info.full_name}")
    
    result = await git_service.create_accessibility_pr(
        credentials=credentials,
        repo_info=repo_info,
        patches=request.patches,
        feature_ids=request.feature_ids,
        scan_id=request.scan_id
    )
    
    if result.success:
        # Speichere PR in DB für Tracking
        if db_pool:
            await _save_pr_record(
                user_id,
                request.repo_id,
                result,
                request.feature_ids,
                request.scan_id
            )
        
        return ApplyPatchesResponse(
            success=True,
            branch_name=result.branch_name,
            pr_url=result.pr_url,
            pr_number=result.pr_number,
            files_changed=[p.get("file_path", "") for p in request.patches if p.get("file_path")]
        )
    
    return ApplyPatchesResponse(
        success=False,
        error=result.error
    )


class ApplyApprovedFixesRequest(BaseModel):
    """Ein-Klick-Fix: freigegebene Fixes einer Site als PR."""
    repo_id: str = Field(..., description="Verbundenes Repository")
    site_id: str = Field(..., description="Site, deren freigegebene Fixes angewendet werden")


@git_router.post("/apply-approved-fixes")
async def apply_approved_fixes(
    request: ApplyApprovedFixesRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> ApplyPatchesResponse:
    """
    Ein Klick: freigegebene Fixes -> Pull Request. Ohne LLM.

    Der Weg bis hierher war zweigeteilt: die KI erzeugt Vorschlaege (einmal,
    mit menschlicher Freigabe in der Worklist), und ein EXTERNER Agent via MCP
    musste daraus Patches formulieren. Dieser Endpunkt ersetzt den Agenten
    durch Mechanik: Manifest lesen, Repo-Baum holen, Kandidaten-Templates
    laden, guarded transformieren, PR erstellen. Deterministisch — dieselben
    freigegebenen Fixes ergeben denselben PR. Gemerged wird weiterhin nur vom
    Kunden; Revert bleibt verfuegbar.
    """
    from fix_patch_builder import baue_patches, ist_kandidat, zaehle_pr_faehig, MAX_DATEIEN
    from widget_routes import db_pool as widget_db_pool
    from accessibility_fix_saver import AccessibilityFixSaver

    user_id = user.get("user_id")

    repo_data = await _get_connected_repo(user_id, request.repo_id)
    if not repo_data:
        return ApplyPatchesResponse(success=False, error="Repository nicht gefunden")
    credentials = await _get_git_credentials(user_id, repo_data["provider"])
    if not credentials:
        return ApplyPatchesResponse(success=False, error="Git-Verbindung abgelaufen. Bitte erneut verbinden.")
    if repo_data["provider"] != "github":
        return ApplyPatchesResponse(success=False, error="Ein-Klick-Fix ist aktuell nur für GitHub verfügbar.")

    # Freigegebene Fixes laden — dieselbe Quelle wie das Fix-Manifest.
    pool = widget_db_pool or db_pool
    if not pool:
        return ApplyPatchesResponse(success=False, error="Datenbank nicht verfügbar.")
    saver = AccessibilityFixSaver(pool)
    manifest = {
        "alt_texts": await saver.get_fixes_for_site(request.site_id, status="approved"),
        "document_fixes": await saver.get_document_fixes_for_site(request.site_id, status="approved"),
    }
    # Link-Zwecke werden hier nur GEZAEHLT, nicht angewendet — sie gehen ueber
    # Widget/Plugin raus (Begruendung in fix_patch_builder.zaehle_pr_faehig).
    # Ohne diese Zahl lautete die Fehlermeldung faelschlich "keine Fixes
    # freigegeben", obwohl der Kunde gerade welche freigegeben hatte.
    link_fixes = await saver.get_link_fixes_for_site(request.site_id, status="approved")
    zaehlung = zaehle_pr_faehig(manifest["alt_texts"], link_fixes, manifest["document_fixes"])

    if zaehlung["deliverable"] == 0:
        if zaehlung["manifest_only"] > 0:
            return ApplyPatchesResponse(
                success=False,
                error=(
                    f"Ihre {zaehlung['manifest_only']} freigegebenen Fixes werden über das "
                    f"Widget bzw. WordPress-Plugin ausgeliefert und nicht als Code-Änderung — "
                    f"für einen Pull Request braucht es Alt-Texte oder dokumentweite Fixes "
                    f"(Sprache, Sprunglink)."
                ),
            )
        return ApplyPatchesResponse(
            success=False,
            error="Keine freigegebenen Fixes vorhanden. Bitte zuerst Vorschläge in der Worklist prüfen und freigeben.",
        )

    repo_info = RepoInfo(
        provider=GitProvider(repo_data["provider"]),
        owner=repo_data["owner"],
        repo=repo_data["repo"],
        default_branch=repo_data["default_branch"],
    )
    client = git_service.get_client(repo_info.provider, credentials)

    baum = await client.get_tree(repo_info.owner, repo_info.repo, repo_info.default_branch)
    kandidaten = [e["path"] for e in baum if ist_kandidat(e["path"], e.get("size"))][:MAX_DATEIEN]
    if not kandidaten:
        return ApplyPatchesResponse(
            success=False,
            error=(
                "Keine bearbeitbaren Template-Dateien (.html/.php/.twig …) im Repository gefunden. "
                "Für Build-basierte Projekte (React/Vue) nutzen Sie den MCP-Agenten-Weg."
            ),
        )

    dateien: Dict[str, str] = {}
    for pfad in kandidaten:
        inhalt, _sha = await client.get_file_content(
            repo_info.owner, repo_info.repo, pfad, repo_info.default_branch
        )
        if inhalt:
            dateien[pfad] = inhalt

    patches = baue_patches(manifest, dateien)
    if not patches:
        return ApplyPatchesResponse(
            success=False,
            error=(
                "Die freigegebenen Fixes treffen keine Datei in diesem Repository "
                "(Bilder nicht gefunden oder bereits versorgt). Nichts zu tun."
            ),
        )

    feature_ids = sorted({p["feature_id"] for p in patches})
    logger.info(
        f"Ein-Klick-Fix: {len(patches)} Patch(es) aus {len(dateien)} Dateien "
        f"für {repo_info.full_name} (site {request.site_id})"
    )
    result = await git_service.create_accessibility_pr(
        credentials=credentials,
        repo_info=repo_info,
        patches=patches,
        feature_ids=feature_ids,
        scan_id=None,
    )
    if result.success:
        if db_pool:
            await _save_pr_record(user_id, request.repo_id, result, feature_ids, None)
        return ApplyPatchesResponse(
            success=True,
            branch_name=result.branch_name,
            pr_url=result.pr_url,
            pr_number=result.pr_number,
            files_changed=[p["file_path"] for p in patches],
        )
    return ApplyPatchesResponse(success=False, error=result.error)


@git_router.get("/status")
async def git_connection_status(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Verbindungsstatus fuer die Einstellungs-Seite.

    Bewusst ohne Token-Inhalte — nur ob eine Verbindung existiert und unter
    welchem Git-Namen sie laeuft.
    """
    user_id = user.get("user_id")
    if not db_pool:
        return {"connected": False, "providers": []}

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT provider, git_username, created_at FROM git_credentials WHERE user_id = $1",
            user_id,
        )
    return {
        "connected": bool(rows),
        "providers": [
            {
                "provider": r["provider"],
                "git_username": r["git_username"],
                "connected_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ],
    }


@git_router.get("/prs")
async def list_pull_requests(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Alle ueber complyo erstellten PRs des Kontos (fuer PR-Liste + Rollback)."""
    user_id = user.get("user_id")
    if not db_pool:
        return {"prs": []}

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT p.id, p.pr_number, p.pr_url, p.branch_name, p.feature_ids,
                   p.scan_id, p.status, p.created_at,
                   r.provider, r.owner, r.repo
            FROM git_pull_requests p
            JOIN git_connected_repos r ON p.repo_id = r.id
            WHERE p.user_id = $1
            ORDER BY p.created_at DESC
            LIMIT 100
            """,
            user_id,
        )
    return {
        "prs": [
            {
                "id": r["id"],
                "pr_number": r["pr_number"],
                "pr_url": r["pr_url"],
                "branch_name": r["branch_name"],
                "feature_ids": list(r["feature_ids"] or []),
                "scan_id": r["scan_id"],
                "status": r["status"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "repo_full_name": f"{r['owner']}/{r['repo']}",
                "provider": r["provider"],
            }
            for r in rows
        ]
    }


@git_router.post("/prs/{pr_id}/revert")
async def revert_pull_request(
    pr_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Nimmt einen ueber complyo erstellten PR zurueck.

    Offene PRs werden geschlossen; gemergte bekommen einen Gegen-PR, der den
    Stand von vor dem Merge wiederherstellt. Auch der Revert wird nur
    vorgeschlagen — gemerged wird vom Kunden (gleiche Regel wie hinwaerts).
    """
    user_id = user.get("user_id")

    async with db_pool.acquire() as conn:
        pr_row = await conn.fetchrow(
            """
            SELECT p.id, p.pr_number, p.status, p.repo_id,
                   r.provider, r.owner, r.repo, r.default_branch
            FROM git_pull_requests p
            JOIN git_connected_repos r ON p.repo_id = r.id
            WHERE p.id = $1 AND p.user_id = $2
            """,
            pr_id, user_id,
        )
    if not pr_row:
        raise HTTPException(status_code=404, detail="Pull Request nicht gefunden.")

    credentials = await _get_git_credentials(user_id, pr_row["provider"])
    if not credentials:
        raise HTTPException(
            status_code=409,
            detail="Git-Verbindung abgelaufen. Bitte erneut mit GitHub verbinden.",
        )

    repo_info = RepoInfo(
        provider=GitProvider(pr_row["provider"]),
        owner=pr_row["owner"],
        repo=pr_row["repo"],
        default_branch=pr_row["default_branch"],
    )

    result = await git_service.revert_pull_request(
        credentials=credentials,
        repo_info=repo_info,
        pr_number=pr_row["pr_number"],
    )
    if not result.success:
        raise HTTPException(status_code=422, detail=result.error or "Revert fehlgeschlagen.")

    async with db_pool.acquire() as conn:
        if result.status == PRStatus.CLOSED:
            # Offener PR wurde geschlossen — Original-Eintrag nachziehen.
            await conn.execute(
                "UPDATE git_pull_requests SET status = 'CLOSED', updated_at = NOW() WHERE id = $1",
                pr_id,
            )
            aktion = "closed"
        else:
            # Gegen-PR entstanden: Original als MERGED markieren (Revert setzt
            # einen Merge voraus) und den Revert-PR fuers Tracking speichern.
            await conn.execute(
                "UPDATE git_pull_requests SET status = 'MERGED', updated_at = NOW() WHERE id = $1",
                pr_id,
            )
            await conn.execute(
                """
                INSERT INTO git_pull_requests
                (user_id, repo_id, pr_number, pr_url, branch_name, feature_ids, scan_id, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NULL, $7, NOW())
                """,
                user_id, pr_row["repo_id"], result.pr_number, result.pr_url,
                result.branch_name, ["REVERT"], result.status.value,
            )
            aktion = "revert_pr_created"

    return {
        "success": True,
        "action": aktion,
        "pr_number": result.pr_number,
        "pr_url": result.pr_url,
        "branch_name": result.branch_name,
    }


# =============================================================================
# Database Helpers
# =============================================================================

async def _save_git_credentials(
    user_id: str,
    provider: str,
    credentials: GitCredentials,
    user_name: str
):
    """Speichert Git-Credentials"""
    if not db_pool:
        return
    
    # Tokens niemals im Klartext ablegen: ein GitHub-Token erlaubt
    # Schreibzugriff auf Kunden-Repos. Ohne Schluessel wird nicht gespeichert.
    try:
        access_enc = encrypt_token(credentials.access_token)
        refresh_enc = encrypt_token(credentials.refresh_token)
    except GitTokenCryptoError as e:
        logger.error(f"Git-Credentials nicht gespeichert: {e}")
        raise HTTPException(
            status_code=503,
            detail="Git-Integration ist serverseitig nicht konfiguriert (Verschlüsselung).",
        )

    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO git_credentials (user_id, provider, access_token, refresh_token, git_username, created_at)
            VALUES ($1, $2, $3, $4, $5, NOW())
            ON CONFLICT (user_id, provider)
            DO UPDATE SET access_token = $3, refresh_token = $4, git_username = $5, updated_at = NOW()
        """, user_id, provider, access_enc, refresh_enc, user_name)


async def _get_git_credentials(user_id: str, provider: str) -> Optional[GitCredentials]:
    """Lädt Git-Credentials"""
    if not db_pool:
        return None
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT access_token, refresh_token
            FROM git_credentials
            WHERE user_id = $1 AND provider = $2
        """, user_id, provider)
        
        if row:
            try:
                return GitCredentials(
                    provider=GitProvider(provider),
                    access_token=decrypt_token(row["access_token"]),
                    refresh_token=decrypt_token(row["refresh_token"]),
                )
            except GitTokenCryptoError as e:
                # Schluessel rotiert/fehlt: wie "nicht verbunden" behandeln —
                # der Aufrufer fordert den Nutzer zum erneuten Verbinden auf.
                logger.error(f"Git-Credentials nicht lesbar (user={user_id}, {provider}): {e}")
                return None
    
    return None


async def _save_connected_repo(
    user_id: str,
    provider: str,
    owner: str,
    repo: str,
    default_branch: str
) -> str:
    """Speichert verbundenes Repository"""
    if not db_pool:
        return ""
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO git_connected_repos (user_id, provider, owner, repo, default_branch, active, created_at)
            VALUES ($1, $2, $3, $4, $5, TRUE, NOW())
            ON CONFLICT (user_id, provider, owner, repo)
            DO UPDATE SET default_branch = $5, active = TRUE, updated_at = NOW()
            RETURNING id
        """, user_id, provider, owner, repo, default_branch)
        
        return str(row["id"]) if row else ""


async def _get_connected_repo(user_id: str, repo_id: str) -> Optional[Dict[str, Any]]:
    """Lädt verbundenes Repository"""
    if not db_pool:
        return None
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT provider, owner, repo, default_branch
            FROM git_connected_repos
            WHERE id = $1 AND user_id = $2 AND active = TRUE
        """, int(repo_id), user_id)
        
        if row:
            return dict(row)
    
    return None


async def _save_pr_record(
    user_id: str,
    repo_id: str,
    result: PullRequestResult,
    feature_ids: List[str],
    scan_id: Optional[str]
):
    """Speichert PR-Record für Tracking"""
    if not db_pool:
        return
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO git_pull_requests 
            (user_id, repo_id, pr_number, pr_url, branch_name, feature_ids, scan_id, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
        """, user_id, int(repo_id), result.pr_number, result.pr_url,
             result.branch_name, feature_ids, scan_id, result.status.value)


# =============================================================================
# Init Function
# =============================================================================

def init_git_routes(pool, auth_svc, redis_svc=None):
    """Initialize route dependencies"""
    global db_pool, auth_service, redis_client
    db_pool = pool
    auth_service = auth_svc
    redis_client = redis_svc
    logger.info("✅ Git routes initialized")
