"""
Complyo GitHub Integration
Automatic PR creation for compliance fixes
"""

import base64
import httpx
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class GitHubPRResult:
    """Result of GitHub PR creation"""
    success: bool
    pr_url: Optional[str]
    pr_number: Optional[int]
    branch_name: str
    repository: str
    error: Optional[str] = None


class GitHubIntegration:
    """
    GitHub Integration for Automatic PR Creation
    
    Features:
    - Create branch from main/master
    - Commit fixes
    - Create Pull Request with detailed description
    - Support for multiple files
    - Issue tracking integration
    """
    
    def __init__(self):
        self.base_url = "https://api.github.com"
    
    async def create_pr_for_fix(
        self,
        repository: str,
        github_token: str,
        fix_id: str,
        fix_data: Dict[str, Any],
        target_branch: str = "main"
    ) -> GitHubPRResult:
        """
        Create Pull Request for a compliance fix
        
        Args:
            repository: Repository in format "owner/repo"
            github_token: GitHub Personal Access Token
            fix_id: Unique fix ID
            fix_data: Fix data including code, category, description
            target_branch: Target branch (default: "main")
            
        Returns:
            GitHubPRResult with PR details
        """
        try:
            branch_name = f"complyo-fix-{fix_id}"
            
            logger.info(f"🚀 Creating GitHub PR for {repository}")
            
            # Get base branch SHA
            base_sha = await self._get_branch_sha(
                repository, target_branch, github_token
            )
            
            # Create new branch
            await self._create_branch(
                repository, branch_name, base_sha, github_token
            )
            logger.info(f"✅ Branch created: {branch_name}")
            
            # Commit fixes
            files_committed = await self._commit_fixes(
                repository, branch_name, fix_data, github_token
            )
            logger.info(f"✅ Files committed: {len(files_committed)}")
            
            # Create Pull Request
            pr_data = await self._create_pull_request(
                repository,
                branch_name,
                target_branch,
                fix_data,
                github_token
            )
            
            logger.info(f"✅ PR created: {pr_data['html_url']}")
            
            return GitHubPRResult(
                success=True,
                pr_url=pr_data['html_url'],
                pr_number=pr_data['number'],
                branch_name=branch_name,
                repository=repository
            )
            
        except Exception as e:
            logger.error(f"❌ GitHub PR creation failed: {e}")
            return GitHubPRResult(
                success=False,
                pr_url=None,
                pr_number=None,
                branch_name=branch_name,
                repository=repository,
                error=str(e)
            )
    
    async def _get_branch_sha(
        self,
        repository: str,
        branch: str,
        token: str
    ) -> str:
        """Get SHA of branch HEAD"""
        url = f"{self.base_url}/repos/{repository}/git/refs/heads/{branch}"
        headers = self._get_headers(token)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data['object']['sha']
    
    async def _create_branch(
        self,
        repository: str,
        branch_name: str,
        base_sha: str,
        token: str
    ):
        """Create new branch"""
        url = f"{self.base_url}/repos/{repository}/git/refs"
        headers = self._get_headers(token)
        
        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
    
    async def _commit_fixes(
        self,
        repository: str,
        branch: str,
        fix_data: Dict[str, Any],
        token: str
    ) -> List[str]:
        """
        Commit fix files to branch
        
        Returns:
            List of committed file paths
        """
        committed_files = []
        
        # Get current tree
        branch_sha = await self._get_branch_sha(repository, branch, token)
        commit_data = await self._get_commit(repository, branch_sha, token)
        tree_sha = commit_data['tree']['sha']
        
        # Prepare files for commit
        files = self._prepare_files_for_commit(fix_data)
        
        # Create blobs for each file
        blobs = []
        for file_path, content in files.items():
            blob_sha = await self._create_blob(
                repository, content, token
            )
            blobs.append({
                'path': file_path,
                'mode': '100644',
                'type': 'blob',
                'sha': blob_sha
            })
            committed_files.append(file_path)
        
        # Create new tree
        new_tree_sha = await self._create_tree(
            repository, tree_sha, blobs, token
        )
        
        # Create commit
        commit_message = self._generate_commit_message(fix_data)
        new_commit_sha = await self._create_commit(
            repository, commit_message, new_tree_sha, branch_sha, token
        )
        
        # Update branch reference
        await self._update_ref(
            repository, branch, new_commit_sha, token
        )
        
        return committed_files
    
    async def _create_pull_request(
        self,
        repository: str,
        head_branch: str,
        base_branch: str,
        fix_data: Dict[str, Any],
        token: str
    ) -> Dict[str, Any]:
        """Create Pull Request"""
        url = f"{self.base_url}/repos/{repository}/pulls"
        headers = self._get_headers(token)
        
        title, body = self._generate_pr_content(fix_data)
        
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def _get_commit(
        self,
        repository: str,
        sha: str,
        token: str
    ) -> Dict[str, Any]:
        """Get commit data"""
        url = f"{self.base_url}/repos/{repository}/git/commits/{sha}"
        headers = self._get_headers(token)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def _create_blob(
        self,
        repository: str,
        content: str,
        token: str
    ) -> str:
        """Create blob (file content)"""
        url = f"{self.base_url}/repos/{repository}/git/blobs"
        headers = self._get_headers(token)
        
        # Base64 encode content
        content_b64 = base64.b64encode(content.encode()).decode()
        
        payload = {
            "content": content_b64,
            "encoding": "base64"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['sha']
    
    async def _create_tree(
        self,
        repository: str,
        base_tree: str,
        tree: List[Dict],
        token: str
    ) -> str:
        """Create git tree"""
        url = f"{self.base_url}/repos/{repository}/git/trees"
        headers = self._get_headers(token)
        
        payload = {
            "base_tree": base_tree,
            "tree": tree
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['sha']
    
    async def _create_commit(
        self,
        repository: str,
        message: str,
        tree: str,
        parent: str,
        token: str
    ) -> str:
        """Create commit"""
        url = f"{self.base_url}/repos/{repository}/git/commits"
        headers = self._get_headers(token)
        
        payload = {
            "message": message,
            "tree": tree,
            "parents": [parent]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['sha']
    
    async def _update_ref(
        self,
        repository: str,
        branch: str,
        sha: str,
        token: str
    ):
        """Update branch reference"""
        url = f"{self.base_url}/repos/{repository}/git/refs/heads/{branch}"
        headers = self._get_headers(token)
        
        payload = {
            "sha": sha,
            "force": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(url, headers=headers, json=payload)
            response.raise_for_status()
    
    def _prepare_files_for_commit(
        self,
        fix_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Prepare files for commit
        
        Returns:
            Dict mapping file paths to content
        """
        files = {}
        
        category = fix_data.get('issue_category', 'compliance')
        code = fix_data.get('code', '')
        
        # Determine file path based on category
        if category == 'cookies':
            files['public/cookie-banner.html'] = code
        elif category == 'impressum':
            files['public/impressum.html'] = code
        elif category == 'datenschutz':
            files['public/datenschutz.html'] = code
        elif category == 'barrierefreiheit':
            if 'css' in code.lower():
                files['public/css/accessibility-fixes.css'] = code
            else:
                files['public/js/accessibility-fixes.js'] = code
        else:
            files[f'compliance-fixes/{category}.html'] = code
        
        return files
    
    def _generate_commit_message(self, fix_data: Dict[str, Any]) -> str:
        """Generate commit message"""
        category = fix_data.get('issue_category', 'Compliance').title()
        fix_id = fix_data.get('issue_id', 'unknown')
        
        return f"""🤖 Complyo Auto-Fix: {category} Compliance

Fix-ID: {fix_id}
Kategorie: {category}
Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Dieser automatische Fix wurde von Complyo generiert um Compliance-Probleme 
im Bereich {category} zu beheben.

---
🛡️ Generiert von Complyo (https://complyo.tech)
"""
    
    def _generate_pr_content(
        self,
        fix_data: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Generate PR title and body
        
        Returns:
            Tuple of (title, body)
        """
        category = fix_data.get('issue_category', 'Compliance').title()
        fix_id = fix_data.get('issue_id', 'unknown')
        
        title = f"🤖 Complyo Auto-Fix: {category} Compliance"
        
        body = f"""## Automatischer Compliance-Fix

**Kategorie:** {category}  
**Fix-ID:** {fix_id}  
**Generiert:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

### Beschreibung

Dieser Pull Request behebt automatisch erkannte Compliance-Probleme im Bereich **{category}**.

### Änderungen

Die folgenden Dateien wurden hinzugefügt/geändert:
- Automatisch generierte {category}-Fixes
- WCAG 2.1 / DSGVO / TTDSG / TMG konform

### Nächste Schritte

1. ✅ **Review:** Prüfen Sie die Änderungen
2. ✅ **Testing:** Testen Sie die Funktionalität lokal
3. ✅ **Anpassungen:** Passen Sie bei Bedarf an (z.B. Firmendaten in Impressum)
4. ✅ **Merge:** Wenn alles passt, mergen Sie den PR

### Rechtliche Hinweise

Dieser automatische Fix basiert auf Best Practices und aktuellen Rechtsgrundlagen. 
Wir empfehlen jedoch immer eine Prüfung durch einen Rechtsanwalt, insbesondere bei:
- Impressum (Firmendaten)
- Datenschutzerklärung (spezifische Datenverarbeitungen)

### Support

Bei Fragen wenden Sie sich an:
- 📧 support@complyo.tech
- 📚 [Complyo Dokumentation](https://docs.complyo.tech)

---

🛡️ Generiert von [Complyo](https://complyo.tech) | Fix-ID: {fix_id}
"""
        
        return (title, body)
    
    def _get_headers(self, token: str) -> Dict[str, str]:
        """Get HTTP headers for GitHub API"""
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }


# Global instance
github_integration = GitHubIntegration()

