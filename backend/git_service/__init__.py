"""
Git Service Module
Automatische PR-Erstellung für Barrierefreiheits-Fixes
"""

from .git_service import (
    GitService,
    GitProvider,
    GitCredentials,
    RepoInfo,
    PullRequestResult,
    CommitResult,
    PRStatus,
    GitHubClient,
    GitLabClient,
    git_service
)

__all__ = [
    "GitService",
    "GitProvider",
    "GitCredentials",
    "RepoInfo",
    "PullRequestResult",
    "CommitResult",
    "PRStatus",
    "GitHubClient",
    "GitLabClient",
    "git_service"
]
