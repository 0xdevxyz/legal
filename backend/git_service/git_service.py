"""
Git Service für automatische PR-Erstellung
Unterstützt GitHub und GitLab

Features:
- OAuth-Integration
- Branch erstellen
- Patches committen
- Pull Requests erstellen
- Webhook-Verarbeitung
"""

import os
import base64
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Data Classes
# =============================================================================

class GitProvider(str, Enum):
    """Unterstützte Git-Provider"""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class PRStatus(str, Enum):
    """Pull Request Status"""
    OPEN = "OPEN"
    MERGED = "MERGED"
    CLOSED = "CLOSED"
    DRAFT = "DRAFT"


@dataclass
class GitCredentials:
    """Git-Zugangsdaten"""
    provider: GitProvider
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    installation_id: Optional[str] = None  # Für GitHub Apps


@dataclass
class RepoInfo:
    """Repository-Informationen"""
    provider: GitProvider
    owner: str
    repo: str
    default_branch: str = "main"
    full_name: str = ""
    
    def __post_init__(self):
        self.full_name = f"{self.owner}/{self.repo}"


@dataclass
class PullRequestResult:
    """Ergebnis einer PR-Erstellung"""
    success: bool
    pr_id: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    branch_name: Optional[str] = None
    status: PRStatus = PRStatus.OPEN
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "pr_id": self.pr_id,
            "pr_number": self.pr_number,
            "pr_url": self.pr_url,
            "branch_name": self.branch_name,
            "status": self.status.value,
            "error": self.error
        }


@dataclass
class CommitResult:
    """Ergebnis eines Commits"""
    success: bool
    commit_sha: Optional[str] = None
    branch_name: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)
    error: Optional[str] = None


# =============================================================================
# GitHub API Client
# =============================================================================

class GitHubClient:
    """GitHub API Client für Barrierefreiheits-Fixes"""
    
    API_BASE = "https://api.github.com"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Tuple[bool, Any]:
        """Führt API-Request aus"""
        url = f"{self.API_BASE}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()
                    
                    if response.status in [200, 201, 204]:
                        return True, result
                    else:
                        logger.error(f"GitHub API error: {response.status} - {result}")
                        return False, result
        
        except Exception as e:
            logger.error(f"GitHub API request failed: {e}")
            return False, {"error": str(e)}
    
    async def get_user(self) -> Dict[str, Any]:
        """Gibt aktuellen User zurück"""
        success, data = await self._request("GET", "/user")
        return data if success else {}
    
    async def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Gibt Repository-Info zurück"""
        success, data = await self._request("GET", f"/repos/{owner}/{repo}")
        return data if success else {}
    
    async def get_default_branch(self, owner: str, repo: str) -> str:
        """Ermittelt Default-Branch"""
        repo_info = await self.get_repo(owner, repo)
        return repo_info.get("default_branch", "main")
    
    async def get_branch_sha(self, owner: str, repo: str, branch: str) -> Optional[str]:
        """Gibt SHA des Branch-Heads zurück"""
        success, data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/git/ref/heads/{branch}"
        )
        if success:
            return data.get("object", {}).get("sha")
        return None
    
    async def create_branch(
        self,
        owner: str,
        repo: str,
        branch_name: str,
        from_branch: str = "main"
    ) -> Tuple[bool, str]:
        """
        Erstellt einen neuen Branch
        
        Returns:
            Tuple von (success, sha oder error)
        """
        # Hole SHA des Quell-Branches
        base_sha = await self.get_branch_sha(owner, repo, from_branch)
        if not base_sha:
            return False, f"Branch '{from_branch}' nicht gefunden"
        
        # Erstelle neuen Branch
        success, data = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/refs",
            data={
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            }
        )
        
        if success:
            return True, data.get("object", {}).get("sha", base_sha)
        else:
            error = data.get("message", "Branch-Erstellung fehlgeschlagen")
            return False, error
    
    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        branch: str = "main"
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Lädt Datei-Inhalt
        
        Returns:
            Tuple von (content, sha) oder (None, None)
        """
        success, data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": branch}
        )
        
        if success and data.get("content"):
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content, data.get("sha")
        
        return None, None
    
    async def update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
        file_sha: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Aktualisiert oder erstellt eine Datei
        
        Returns:
            Tuple von (success, commit_sha)
        """
        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": branch
        }
        
        if file_sha:
            data["sha"] = file_sha
        
        success, result = await self._request(
            "PUT",
            f"/repos/{owner}/{repo}/contents/{path}",
            data=data
        )
        
        if success:
            return True, result.get("commit", {}).get("sha")
        
        return False, None
    
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False
    ) -> PullRequestResult:
        """
        Erstellt einen Pull Request
        """
        success, data = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            data={
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch,
                "draft": draft
            }
        )
        
        if success:
            return PullRequestResult(
                success=True,
                pr_id=str(data.get("id")),
                pr_number=data.get("number"),
                pr_url=data.get("html_url"),
                branch_name=head_branch,
                status=PRStatus.DRAFT if draft else PRStatus.OPEN
            )
        
        return PullRequestResult(
            success=False,
            error=data.get("message", "PR-Erstellung fehlgeschlagen")
        )
    
    async def apply_unified_diff(
        self,
        owner: str,
        repo: str,
        branch: str,
        file_path: str,
        unified_diff: str,
        commit_message: str
    ) -> CommitResult:
        """
        Wendet einen Unified Diff auf eine Datei an
        """
        # 1. Lade aktuelle Datei
        content, file_sha = await self.get_file_content(owner, repo, file_path, branch)
        
        if content is None:
            return CommitResult(
                success=False,
                error=f"Datei '{file_path}' nicht gefunden"
            )
        
        # 2. Wende Diff an
        try:
            patched_content = self._apply_diff(content, unified_diff)
        except Exception as e:
            return CommitResult(
                success=False,
                error=f"Diff konnte nicht angewendet werden: {e}"
            )
        
        # 3. Committe Änderung
        success, commit_sha = await self.update_file(
            owner, repo, file_path, patched_content, commit_message, branch, file_sha
        )
        
        if success:
            return CommitResult(
                success=True,
                commit_sha=commit_sha,
                branch_name=branch,
                files_changed=[file_path]
            )
        
        return CommitResult(success=False, error="Commit fehlgeschlagen")
    
    def _apply_diff(self, original: str, diff: str) -> str:
        """
        Wendet einen Unified Diff auf Text an
        
        Vereinfachte Implementierung - für komplexere Diffs
        sollte eine Library wie `patch` verwendet werden.
        """
        original_lines = original.split('\n')
        result_lines = original_lines.copy()
        
        # Parse Diff-Hunks
        hunk_pattern = r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
        
        # Finde alle Hunks
        hunks = []
        current_hunk = None
        
        for line in diff.split('\n'):
            match = re.match(hunk_pattern, line)
            if match:
                if current_hunk:
                    hunks.append(current_hunk)
                current_hunk = {
                    'old_start': int(match.group(1)),
                    'old_count': int(match.group(2) or 1),
                    'new_start': int(match.group(3)),
                    'new_count': int(match.group(4) or 1),
                    'lines': []
                }
            elif current_hunk is not None:
                if line.startswith('+') and not line.startswith('+++'):
                    current_hunk['lines'].append(('+', line[1:]))
                elif line.startswith('-') and not line.startswith('---'):
                    current_hunk['lines'].append(('-', line[1:]))
                elif line.startswith(' '):
                    current_hunk['lines'].append((' ', line[1:]))
        
        if current_hunk:
            hunks.append(current_hunk)
        
        # Wende Hunks rückwärts an (um Zeilennummern nicht zu verschieben)
        offset = 0
        for hunk in hunks:
            line_num = hunk['old_start'] - 1 + offset
            
            for action, content in hunk['lines']:
                if action == '-':
                    # Zeile entfernen
                    if line_num < len(result_lines):
                        result_lines.pop(line_num)
                        offset -= 1
                elif action == '+':
                    # Zeile hinzufügen
                    result_lines.insert(line_num, content)
                    line_num += 1
                    offset += 1
                else:
                    # Kontextzeile überspringen
                    line_num += 1
        
        return '\n'.join(result_lines)


# =============================================================================
# GitLab API Client
# =============================================================================

class GitLabClient:
    """GitLab API Client"""
    
    API_BASE = "https://gitlab.com/api/v4"
    
    def __init__(self, access_token: str, base_url: str = None):
        self.access_token = access_token
        self.api_base = base_url or self.API_BASE
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Tuple[bool, Any]:
        """Führt API-Request aus"""
        url = f"{self.api_base}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()
                    
                    if response.status in [200, 201, 204]:
                        return True, result
                    else:
                        logger.error(f"GitLab API error: {response.status} - {result}")
                        return False, result
        
        except Exception as e:
            logger.error(f"GitLab API request failed: {e}")
            return False, {"error": str(e)}
    
    def _encode_path(self, path: str) -> str:
        """URL-encodes project path für GitLab API"""
        from urllib.parse import quote
        return quote(path, safe='')
    
    async def get_project(self, project_path: str) -> Dict[str, Any]:
        """Gibt Projekt-Info zurück"""
        encoded = self._encode_path(project_path)
        success, data = await self._request("GET", f"/projects/{encoded}")
        return data if success else {}
    
    async def create_branch(
        self,
        project_path: str,
        branch_name: str,
        from_branch: str = "main"
    ) -> Tuple[bool, str]:
        """Erstellt einen neuen Branch"""
        encoded = self._encode_path(project_path)
        success, data = await self._request(
            "POST",
            f"/projects/{encoded}/repository/branches",
            data={
                "branch": branch_name,
                "ref": from_branch
            }
        )
        
        if success:
            return True, data.get("commit", {}).get("id", "")
        
        return False, data.get("message", "Branch-Erstellung fehlgeschlagen")
    
    async def create_merge_request(
        self,
        project_path: str,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str = "main"
    ) -> PullRequestResult:
        """Erstellt einen Merge Request"""
        encoded = self._encode_path(project_path)
        success, data = await self._request(
            "POST",
            f"/projects/{encoded}/merge_requests",
            data={
                "title": title,
                "description": description,
                "source_branch": source_branch,
                "target_branch": target_branch
            }
        )
        
        if success:
            return PullRequestResult(
                success=True,
                pr_id=str(data.get("iid")),
                pr_number=data.get("iid"),
                pr_url=data.get("web_url"),
                branch_name=source_branch,
                status=PRStatus.OPEN
            )
        
        return PullRequestResult(
            success=False,
            error=data.get("message", "MR-Erstellung fehlgeschlagen")
        )


# =============================================================================
# Git Service (Unified Interface)
# =============================================================================

class GitService:
    """
    Unified Git Service für Barrierefreiheits-Fixes
    
    Unterstützt GitHub, GitLab und Bitbucket.
    """
    
    def __init__(self):
        self.github_client_id = os.getenv("GITHUB_CLIENT_ID", "")
        self.github_client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")
        self.gitlab_client_id = os.getenv("GITLAB_CLIENT_ID", "")
        self.gitlab_client_secret = os.getenv("GITLAB_CLIENT_SECRET", "")
        
        logger.info("🔧 GitService initialisiert")
    
    def get_client(
        self,
        provider: GitProvider,
        credentials: GitCredentials
    ):
        """Gibt den passenden Client zurück"""
        if provider == GitProvider.GITHUB:
            return GitHubClient(credentials.access_token)
        elif provider == GitProvider.GITLAB:
            return GitLabClient(credentials.access_token)
        else:
            raise ValueError(f"Provider {provider} nicht unterstützt")
    
    async def create_accessibility_pr(
        self,
        credentials: GitCredentials,
        repo_info: RepoInfo,
        patches: List[Dict[str, Any]],
        feature_ids: List[str],
        scan_id: Optional[str] = None
    ) -> PullRequestResult:
        """
        Erstellt einen PR mit Barrierefreiheits-Fixes
        
        Args:
            credentials: Git-Zugangsdaten
            repo_info: Repository-Informationen
            patches: Liste von Patches mit unified_diff und file_path
            feature_ids: Liste von Feature-IDs (z.B. ["ALT_TEXT", "CONTRAST"])
            scan_id: Optional Scan-ID für Referenz
            
        Returns:
            PullRequestResult
        """
        logger.info(f"🔧 Creating PR for {repo_info.full_name} with {len(patches)} patches")
        
        # Generiere Branch-Name
        date_str = datetime.now().strftime("%Y%m%d")
        features_str = "-".join(feature_ids[:2]).lower()
        branch_name = f"fix/a11y-{features_str}-{date_str}"
        
        client = self.get_client(repo_info.provider, credentials)
        
        try:
            if repo_info.provider == GitProvider.GITHUB:
                return await self._create_github_pr(
                    client, repo_info, patches, branch_name, feature_ids
                )
            elif repo_info.provider == GitProvider.GITLAB:
                return await self._create_gitlab_mr(
                    client, repo_info, patches, branch_name, feature_ids
                )
            else:
                return PullRequestResult(
                    success=False,
                    error=f"Provider {repo_info.provider} noch nicht implementiert"
                )
        
        except Exception as e:
            logger.error(f"❌ PR creation failed: {e}")
            return PullRequestResult(success=False, error=str(e))
    
    async def _create_github_pr(
        self,
        client: GitHubClient,
        repo_info: RepoInfo,
        patches: List[Dict[str, Any]],
        branch_name: str,
        feature_ids: List[str]
    ) -> PullRequestResult:
        """Erstellt GitHub PR"""
        owner, repo = repo_info.owner, repo_info.repo
        
        # 1. Branch erstellen
        success, result = await client.create_branch(
            owner, repo, branch_name, repo_info.default_branch
        )
        if not success:
            return PullRequestResult(success=False, error=f"Branch-Erstellung: {result}")
        
        # 2. Patches committen
        files_changed = []
        for patch in patches:
            if patch.get("unified_diff") and patch.get("file_path"):
                commit_result = await client.apply_unified_diff(
                    owner, repo, branch_name,
                    patch["file_path"],
                    patch["unified_diff"],
                    f"fix({patch.get('feature_id', 'a11y')}): {patch.get('description', 'Accessibility fix')[:50]}"
                )
                if commit_result.success:
                    files_changed.extend(commit_result.files_changed)
        
        if not files_changed:
            return PullRequestResult(
                success=False,
                error="Keine Dateien geändert"
            )
        
        # 3. PR erstellen
        pr_title, pr_body = self._generate_pr_content(patches, feature_ids, files_changed)
        
        return await client.create_pull_request(
            owner, repo, pr_title, pr_body, branch_name, repo_info.default_branch
        )
    
    async def _create_gitlab_mr(
        self,
        client: GitLabClient,
        repo_info: RepoInfo,
        patches: List[Dict[str, Any]],
        branch_name: str,
        feature_ids: List[str]
    ) -> PullRequestResult:
        """Erstellt GitLab MR"""
        project_path = repo_info.full_name
        
        # 1. Branch erstellen
        success, result = await client.create_branch(
            project_path, branch_name, repo_info.default_branch
        )
        if not success:
            return PullRequestResult(success=False, error=f"Branch-Erstellung: {result}")
        
        # 2. Patches committen (GitLab Commit API ist anders - vereinfacht)
        # TODO: Implement GitLab file commit API
        
        # 3. MR erstellen
        pr_title, pr_body = self._generate_pr_content(patches, feature_ids, [])
        
        return await client.create_merge_request(
            project_path, pr_title, pr_body, branch_name, repo_info.default_branch
        )
    
    def _generate_pr_content(
        self,
        patches: List[Dict[str, Any]],
        feature_ids: List[str],
        files_changed: List[str]
    ) -> Tuple[str, str]:
        """Generiert PR-Titel und Body"""
        
        # Titel
        if len(feature_ids) == 1:
            title = f"fix(a11y): {feature_ids[0]} - Barrierefreiheit verbessern"
        else:
            title = f"fix(a11y): {', '.join(feature_ids[:3])} - Barrierefreiheit verbessern"
        
        # Body
        summary_lines = []
        for patch in patches:
            desc = patch.get("description", "Accessibility-Fix")[:80]
            summary_lines.append(f"- {desc}")
        
        wcag_refs = set()
        for patch in patches:
            wcag_refs.update(patch.get("wcag_criteria", []))
        
        body = f"""## Automatisch generiert von Complyo.tech

### Änderungen

{chr(10).join(summary_lines)}

### Abgedeckte WCAG-Kriterien

{', '.join(sorted(wcag_refs)) if wcag_refs else 'Siehe Einzelpatches'}

### Relevanz für BFSG/EAA

Diese Änderungen verbessern die Barrierefreiheit gemäß:
- Barrierefreiheitsstärkungsgesetz (BFSG)
- European Accessibility Act (EAA)
- Web Content Accessibility Guidelines (WCAG) 2.1

### Geänderte Dateien

{chr(10).join([f'- `{f}`' for f in files_changed]) if files_changed else 'Siehe Commits'}

### Hinweise

⚠️ Bitte prüfen Sie die semantische Korrektheit der generierten Texte (z.B. Alt-Texte, Labels).

---
*Generiert von [Complyo.tech](https://complyo.tech) - Barrierefreiheit leicht gemacht.*
"""
        
        return title, body
    
    # =========================================================================
    # OAuth Flow
    # =========================================================================
    
    def get_github_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generiert GitHub OAuth URL"""
        return (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={self.github_client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=repo,user:email"
            f"&state={state}"
        )
    
    def get_gitlab_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generiert GitLab OAuth URL"""
        return (
            f"https://gitlab.com/oauth/authorize"
            f"?client_id={self.gitlab_client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope=api+read_user+read_repository+write_repository"
            f"&state={state}"
        )
    
    async def exchange_github_code(
        self,
        code: str,
        redirect_uri: str
    ) -> Optional[GitCredentials]:
        """Tauscht GitHub Code gegen Access Token"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://github.com/login/oauth/access_token",
                    headers={"Accept": "application/json"},
                    data={
                        "client_id": self.github_client_id,
                        "client_secret": self.github_client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri
                    }
                ) as response:
                    data = await response.json()
                    
                    if "access_token" in data:
                        return GitCredentials(
                            provider=GitProvider.GITHUB,
                            access_token=data["access_token"],
                            refresh_token=data.get("refresh_token")
                        )
        
        except Exception as e:
            logger.error(f"GitHub OAuth exchange failed: {e}")
        
        return None


# Globale Instanz
git_service = GitService()
