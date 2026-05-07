"""GitHub repository management utilities."""

import os
from typing import List, Optional
from github import Github
from github.Repository import Repository


class GitHubManager:
    """Manages interactions with GitHub repositories."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub manager with authentication token."""
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token is required")
        self.github = Github(self.token)

    def get_repo(self, repo_name: str) -> Repository:
        """Get a repository object by name."""
        return self.github.get_repo(repo_name)

    def clone_repo(self, repo_name: str, local_path: str) -> None:
        """Clone a repository to local path."""
        repo = self.get_repo(repo_name)
        clone_url = repo.clone_url.replace("https://", f"https://{self.token}@")
        os.system(f"git clone {clone_url} {local_path}")

    def create_release(self, repo_name: str, tag: str, name: str, body: str) -> None:
        """Create a new release in the repository."""
        repo = self.get_repo(repo_name)
        repo.create_git_release(tag=tag, name=name, body=body)

    def get_releases(self, repo_name: str) -> List:
        """Get all releases for a repository."""
        repo = self.get_repo(repo_name)
        return list(repo.get_releases())

    def update_file(self, repo_name: str, file_path: str, content: str, message: str, branch: str = "main") -> None:
        """Update a file in the repository."""
        repo = self.get_repo(repo_name)
        try:
            contents = repo.get_contents(file_path, ref=branch)
            repo.update_file(file_path, message, content, contents.sha, branch=branch)
        except:
            # File doesn't exist, create it
            repo.create_file(file_path, message, content, branch=branch)