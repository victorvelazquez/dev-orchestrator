"""GitHub and Git operations manager."""

import logging
import re
from pathlib import Path
from typing import Any

from git import Repo
from github import Github, GithubException


logger = logging.getLogger(__name__)


class GitHubManager:
    """Manages Git and GitHub operations."""
    
    PROTECTED_BRANCHES = {"main", "master", "develop", "development"}
    
    def __init__(
        self,
        token: str,
        workspace_path: Path,
    ) -> None:
        """Initialize with GitHub token and workspace path."""
        self.github = Github(token)
        self.workspace_path = workspace_path
        self.workspace_path.mkdir(parents=True, exist_ok=True)
    
    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """
        Parse repository URL to get owner and repo name.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Tuple of (owner, repo_name)
        """
        # Handle various URL formats
        patterns = [
            r"github\.com[/:]([^/]+)/([^/\.]+)",  # HTTPS or SSH
            r"^([^/]+)/([^/]+)$",  # owner/repo format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2).rstrip(".git")
        
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    async def clone_repository(
        self,
        repo_url: str,
        task_id: str,
    ) -> Path:
        """
        Clone a repository for a task.
        
        Args:
            repo_url: Repository URL
            task_id: Task ID for workspace organization
            
        Returns:
            Path to cloned repository
        """
        owner, repo_name = self.parse_repo_url(repo_url)
        
        # Get repo info from GitHub API
        try:
            gh_repo = self.github.get_repo(f"{owner}/{repo_name}")
        except GithubException as e:
            logger.error("Failed to get repo %s/%s: %s", owner, repo_name, e)
            raise
        
        # Clone to workspace
        clone_path = self.workspace_path / task_id / repo_name
        
        if clone_path.exists():
            logger.info("Repository already exists, pulling latest...")
            repo = Repo(clone_path)
            repo.remotes.origin.pull()
        else:
            logger.info("Cloning %s to %s", repo_url, clone_path)
            clone_path.parent.mkdir(parents=True, exist_ok=True)
            Repo.clone_from(gh_repo.clone_url, clone_path)
        
        return clone_path
    
    async def create_branch(
        self,
        repo_path: Path,
        branch_name: str,
        base_branch: str = "main",
    ) -> str:
        """
        Create a new branch.
        
        Args:
            repo_path: Path to local repository
            branch_name: Name for new branch
            base_branch: Base branch to create from
            
        Returns:
            Created branch name
        """
        repo = Repo(repo_path)
        
        # Ensure we're on base branch and up to date
        repo.git.checkout(base_branch)
        repo.remotes.origin.pull()
        
        # Create and checkout new branch
        repo.git.checkout("-b", branch_name)
        
        logger.info("Created branch: %s", branch_name)
        return branch_name
    
    def is_protected_branch(self, branch_name: str) -> bool:
        """Check if branch is protected."""
        return branch_name.lower() in self.PROTECTED_BRANCHES
    
    async def commit_changes(
        self,
        repo_path: Path,
        message: str,
        files: list[str] | None = None,
    ) -> str:
        """
        Commit changes to repository.
        
        Args:
            repo_path: Path to local repository
            message: Commit message
            files: Specific files to commit, or None for all changes
            
        Returns:
            Commit SHA
        """
        repo = Repo(repo_path)
        
        # Check we're not on protected branch
        current_branch = repo.active_branch.name
        if self.is_protected_branch(current_branch):
            raise ValueError(f"Cannot commit directly to protected branch: {current_branch}")
        
        # Stage files
        if files:
            repo.index.add(files)
        else:
            repo.git.add("-A")
        
        # Commit
        commit = repo.index.commit(message)
        
        logger.info("Created commit: %s", commit.hexsha[:8])
        return commit.hexsha
    
    async def push_branch(
        self,
        repo_path: Path,
        branch_name: str | None = None,
    ) -> None:
        """
        Push branch to remote.
        
        Args:
            repo_path: Path to local repository
            branch_name: Branch to push, or None for current branch
        """
        repo = Repo(repo_path)
        
        if branch_name is None:
            branch_name = repo.active_branch.name
        
        if self.is_protected_branch(branch_name):
            raise ValueError(f"Cannot push to protected branch: {branch_name}")
        
        # Push with upstream tracking
        repo.git.push("-u", "origin", branch_name)
        
        logger.info("Pushed branch: %s", branch_name)
    
    async def create_pull_request(
        self,
        repo_url: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
    ) -> dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            repo_url: Repository URL
            title: PR title
            body: PR body/description
            head_branch: Branch with changes
            base_branch: Target branch
            
        Returns:
            PR details dict
        """
        owner, repo_name = self.parse_repo_url(repo_url)
        
        try:
            gh_repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            pr = gh_repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
            )
            
            logger.info("Created PR #%d: %s", pr.number, pr.html_url)
            
            return {
                "number": pr.number,
                "url": pr.html_url,
                "title": pr.title,
                "state": pr.state,
            }
            
        except GithubException as e:
            logger.error("Failed to create PR: %s", e)
            raise
    
    async def get_repository_info(self, repo_url: str) -> dict[str, Any]:
        """Get repository information."""
        owner, repo_name = self.parse_repo_url(repo_url)
        
        try:
            gh_repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            return {
                "full_name": gh_repo.full_name,
                "default_branch": gh_repo.default_branch,
                "private": gh_repo.private,
                "description": gh_repo.description,
                "language": gh_repo.language,
                "topics": gh_repo.get_topics(),
            }
            
        except GithubException as e:
            logger.error("Failed to get repo info: %s", e)
            raise
    
    async def get_file_content(
        self,
        repo_url: str,
        file_path: str,
        branch: str | None = None,
    ) -> str:
        """Get file content from repository."""
        owner, repo_name = self.parse_repo_url(repo_url)
        
        try:
            gh_repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            ref = branch or gh_repo.default_branch
            content = gh_repo.get_contents(file_path, ref=ref)
            
            if isinstance(content, list):
                raise ValueError(f"Path is a directory: {file_path}")
            
            return content.decoded_content.decode("utf-8")
            
        except GithubException as e:
            logger.error("Failed to get file content: %s", e)
            raise
    
    async def list_directory(
        self,
        repo_url: str,
        path: str = "",
        branch: str | None = None,
    ) -> list[dict[str, Any]]:
        """List directory contents in repository."""
        owner, repo_name = self.parse_repo_url(repo_url)
        
        try:
            gh_repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            ref = branch or gh_repo.default_branch
            contents = gh_repo.get_contents(path, ref=ref)
            
            if not isinstance(contents, list):
                contents = [contents]
            
            return [
                {
                    "name": c.name,
                    "path": c.path,
                    "type": c.type,  # "file" or "dir"
                    "size": c.size,
                }
                for c in contents
            ]
            
        except GithubException as e:
            logger.error("Failed to list directory: %s", e)
            raise
