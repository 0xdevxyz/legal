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
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import secrets
from datetime import datetime

from git_service import (
    git_service, GitProvider, GitCredentials, RepoInfo, PullRequestResult
)

logger = logging.getLogger(__name__)

# Router Setup
git_router = APIRouter(prefix="/api/v2/git", tags=["git-integration"])
security = HTTPBearer()

# Global references
db_pool = None
auth_service = None

# In-Memory OAuth State Store (Production: Redis)
oauth_states: Dict[str, Dict[str, Any]] = {}


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
# Auth Helper
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Verify JWT token and return user data"""
    try:
        if not auth_service:
            raise HTTPException(status_code=500, detail="Auth service not initialized")
        
        token = credentials.credentials
        user_data = auth_service.verify_token(token)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Not authenticated")


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
    
    # Generiere State für CSRF-Schutz
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "user_id": user.get("user_id"),
        "provider": provider,
        "redirect_uri": redirect_uri,
        "created_at": datetime.now().isoformat()
    }
    
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
    state_data = oauth_states.get(request.state)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid state - CSRF protection")
    
    if state_data.get("user_id") != user.get("user_id"):
        raise HTTPException(status_code=400, detail="State mismatch")
    
    # Lösche State (einmalig verwendbar)
    del oauth_states[request.state]
    
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
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO git_credentials (user_id, provider, access_token, refresh_token, git_username, created_at)
            VALUES ($1, $2, $3, $4, $5, NOW())
            ON CONFLICT (user_id, provider)
            DO UPDATE SET access_token = $3, refresh_token = $4, git_username = $5, updated_at = NOW()
        """, user_id, provider, credentials.access_token, credentials.refresh_token, user_name)


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
            return GitCredentials(
                provider=GitProvider(provider),
                access_token=row["access_token"],
                refresh_token=row.get("refresh_token")
            )
    
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

def init_git_routes(pool, auth_svc):
    """Initialize route dependencies"""
    global db_pool, auth_service
    db_pool = pool
    auth_service = auth_svc
    logger.info("✅ Git routes initialized")
