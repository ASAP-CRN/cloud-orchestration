"""Dataset management utilities."""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
from .github_manager import GitHubManager
from .zenodo_manager import ZenodoManager, ZenodoDeposition


class DatasetManager:
    """Manages datasets in the cloud-datasets repository."""

    def __init__(self, github_manager: GitHubManager, zenodo_manager: Optional[ZenodoManager] = None):
        """Initialize dataset manager."""
        self.github = github_manager
        self.zenodo = zenodo_manager
        self.repo_name = "ASAP-CRN/cloud-datasets"

    def get_datasets(self) -> List[Dict]:
        """Get all datasets from the repository."""
        try:
            repo = self.github.get_repo(self.repo_name)
            contents = repo.get_contents("")
            datasets = []
            for item in contents:
                if item.type == "dir":
                    dataset_info = self._load_dataset_info(item.name)
                    if dataset_info:
                        datasets.append(dataset_info)
            return datasets
        except Exception as e:
            print(f"Error getting datasets: {e}")
            return []

    def _load_dataset_info(self, dataset_name: str) -> Optional[Dict]:
        """Load dataset information from metadata file."""
        try:
            repo = self.github.get_repo(self.repo_name)
            metadata_path = f"{dataset_name}/dataset.json"
            contents = repo.get_contents(metadata_path)
            metadata = json.loads(contents.decoded_content.decode())
            metadata["name"] = dataset_name
            return metadata
        except Exception:
            return None

    def create_dataset(self, name: str, metadata: Dict, files: Optional[List[str]] = None) -> None:
        """Create a new dataset."""
        repo = self.github.get_repo(self.repo_name)

        # Create dataset directory
        dataset_dir = f"datasets/{name}"
        repo.create_file(f"{dataset_dir}/.gitkeep", f"Create dataset {name}", "")

        # Create metadata file
        metadata_path = f"{dataset_dir}/dataset.json"
        metadata_content = json.dumps(metadata, indent=2)
        repo.create_file(metadata_path, f"Add metadata for {name}", metadata_content)

        # Upload files if provided
        if files:
            for file_path in files:
                filename = os.path.basename(file_path)
                with open(file_path, "rb") as f:
                    content = f.read()
                repo.create_file(f"{dataset_dir}/{filename}", f"Add {filename} to {name}", content)

    def update_dataset(self, name: str, metadata: Dict, files: Optional[List[str]] = None) -> None:
        """Update an existing dataset."""
        repo = self.github.get_repo(self.repo_name)

        # Update metadata
        metadata_path = f"datasets/{name}/dataset.json"
        try:
            contents = repo.get_contents(metadata_path)
            metadata_content = json.dumps(metadata, indent=2)
            repo.update_file(metadata_path, f"Update metadata for {name}", metadata_content, contents.sha)
        except:
            # Metadata doesn't exist, create it
            metadata_content = json.dumps(metadata, indent=2)
            repo.create_file(metadata_path, f"Add metadata for {name}", metadata_content)

        # Upload/update files if provided
        if files:
            for file_path in files:
                filename = os.path.basename(file_path)
                file_repo_path = f"datasets/{name}/{filename}"
                with open(file_path, "rb") as f:
                    content = f.read()
                try:
                    contents = repo.get_contents(file_repo_path)
                    repo.update_file(file_repo_path, f"Update {filename} in {name}", content, contents.sha)
                except:
                    repo.create_file(file_repo_path, f"Add {filename} to {name}", content)

    def update_dataset_index(self) -> None:
        """Update the datasets index JSON file."""
        datasets = self.get_datasets()
        index_data = {
            "last_updated": datetime.now().isoformat(),
            "total_datasets": len(datasets),
            "datasets": datasets
        }
        index_content = json.dumps(index_data, indent=2)
        
        repo = self.github.get_repo(self.repo_name)
        try:
            # Try to update existing file
            contents = repo.get_contents("datasets.json")
            repo.update_file("datasets.json", "Update datasets index", index_content, contents.sha)
        except:
            # File doesn't exist, create it
            repo.create_file("datasets.json", "Create datasets index", index_content)

    def create_dataset(self, name: str, metadata: Dict, files: Optional[List[str]] = None) -> None:
        """Create a new dataset."""
        # ... existing code ...
        
        # Update index after creating dataset
        self.update_dataset_index()

    def update_dataset(self, name: str, metadata: Dict, files: Optional[List[str]] = None) -> None:
        """Update an existing dataset."""
        # ... existing code ...
        
        # Update index after updating dataset
        self.update_dataset_index()