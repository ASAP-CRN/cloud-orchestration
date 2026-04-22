"""Common Data Elements (CDE) management utilities."""

import json
from datetime import datetime
from typing import Dict, List, Optional
from .github_manager import GitHubManager


class CDEManager:
    """Manages Common Data Elements in the cloud-cde repository."""

    def __init__(self, github_manager: GitHubManager):
        """Initialize CDE manager."""
        self.github = github_manager
        self.repo_name = "ASAP-CRN/cloud-cde"

    def get_cdes(self) -> List[Dict]:
        """Get all CDEs from the repository."""
        try:
            repo = self.github.get_repo(self.repo_name)
            contents = repo.get_contents("cde.json")
            data = json.loads(contents.decoded_content.decode())
            return data.get("cdes", [])
        except Exception:
            return []

    def update_cde_index(self) -> None:
        """Update the CDE index JSON file."""
        cdes = self.get_cdes()
        index_data = {
            "last_updated": datetime.now().isoformat(),
            "total_cdes": len(cdes),
            "cdes": cdes
        }
        index_content = json.dumps(index_data, indent=2)
        
        repo = self.github.get_repo(self.repo_name)
        try:
            contents = repo.get_contents("cde.json")
            repo.update_file("cde.json", "Update CDE index", index_content, contents.sha)
        except:
            repo.create_file("cde.json", "Create CDE index", index_content)

    def add_cde(self, cde_data: Dict) -> None:
        """Add a new CDE."""
        cdes = self.get_cdes()
        cdes.append(cde_data)
        
        index_data = {
            "last_updated": datetime.now().isoformat(),
            "total_cdes": len(cdes),
            "cdes": cdes
        }
        index_content = json.dumps(index_data, indent=2)
        
        repo = self.github.get_repo(self.repo_name)
        try:
            contents = repo.get_contents("cde.json")
            repo.update_file("cde.json", "Add CDE", index_content, contents.sha)
        except:
            repo.create_file("cde.json", "Create CDE index", index_content)

    def update_cde(self, cde_id: str, cde_data: Dict) -> None:
        """Update an existing CDE."""
        cdes = self.get_cdes()
        for i, cde in enumerate(cdes):
            if cde.get("cde_id") == cde_id:
                cdes[i] = cde_data
                break
        
        index_data = {
            "last_updated": datetime.now().isoformat(),
            "total_cdes": len(cdes),
            "cdes": cdes
        }
        index_content = json.dumps(index_data, indent=2)
        
        repo = self.github.get_repo(self.repo_name)
        contents = repo.get_contents("cde.json")
        repo.update_file("cde.json", f"Update CDE {cde_id}", index_content, contents.sha)