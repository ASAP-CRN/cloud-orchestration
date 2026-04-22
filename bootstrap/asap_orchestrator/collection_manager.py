"""Collection management utilities."""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
from .github_manager import GitHubManager
from .zenodo_manager import ZenodoManager


class CollectionManager:
    """Manages collections in the cloud-collections repository."""

    def __init__(self, github_manager: GitHubManager, zenodo_manager: Optional[ZenodoManager] = None):
        """Initialize collection manager."""
        self.github = github_manager
        self.zenodo = zenodo_manager
        self.repo_name = "ASAP-CRN/cloud-collections"

    def update_collection_index(self) -> None:
        """Update the collections index JSON file."""
        collections = self.get_collections()
        index_data = {
            "last_updated": datetime.now().isoformat(),
            "total_collections": len(collections),
            "collections": collections
        }
        index_content = json.dumps(index_data, indent=2)
        
        repo = self.github.get_repo(self.repo_name)
        try:
            # Try to update existing file
            contents = repo.get_contents("collections.json")
            repo.update_file("collections.json", "Update collections index", index_content, contents.sha)
        except:
            # File doesn't exist, create it
            repo.create_file("collections.json", "Create collections index", index_content)

    def _load_collection_info(self, collection_name: str) -> Optional[Dict]:
        """Load collection information from metadata file."""
        try:
            repo = self.github.get_repo(self.repo_name)
            metadata_path = f"{collection_name}/collection.json"
            contents = repo.get_contents(metadata_path)
            metadata = json.loads(contents.decoded_content.decode())
            metadata["name"] = collection_name
            return metadata
        except Exception:
            return None

    def create_collection(self, name: str, metadata: Dict, dataset_names: Optional[List[str]] = None) -> None:
        """Create a new collection."""
        repo = self.github.get_repo(self.repo_name)

        # Create collection directory
        collection_dir = f"collections/{name}"
        repo.create_file(f"{collection_dir}/.gitkeep", f"Create collection {name}", "")

        # Create metadata file
        metadata_path = f"{collection_dir}/collection.json"
        if dataset_names:
            metadata["datasets"] = dataset_names
        metadata_content = json.dumps(metadata, indent=2)
        repo.create_file(metadata_path, f"Add metadata for {name}", metadata_content)

        # Update index after creating collection
        self.update_collection_index()

    def update_collection(self, name: str, metadata: Dict, dataset_names: Optional[List[str]] = None) -> None:
        """Update an existing collection."""
        repo = self.github.get_repo(self.repo_name)

        # Update metadata
        metadata_path = f"collections/{name}/collection.json"
        if dataset_names:
            metadata["datasets"] = dataset_names
        try:
            contents = repo.get_contents(metadata_path)
            metadata_content = json.dumps(metadata, indent=2)
            repo.update_file(metadata_path, f"Update metadata for {name}", metadata_content, contents.sha)
        except:
            # Metadata doesn't exist, create it
            metadata_content = json.dumps(metadata, indent=2)
            repo.create_file(metadata_path, f"Add metadata for {name}", metadata_content)

        # Update index after updating collection
        self.update_collection_index()

    def add_datasets_to_collection(self, collection_name: str, dataset_names: List[str]) -> None:
        """Add datasets to an existing collection."""
        collection_info = self._load_collection_info(collection_name)
        if not collection_info:
            raise ValueError(f"Collection {collection_name} not found")

        current_datasets = collection_info.get("datasets", [])
        current_datasets.extend(dataset_names)
        # Remove duplicates
        current_datasets = list(set(current_datasets))

        collection_info["datasets"] = current_datasets
        self.update_collection(collection_name, collection_info)

    def publish_to_zenodo(self, name: str) -> Optional[str]:
        """Publish collection to Zenodo and get DOI."""
        if not self.zenodo:
            return None

        collection_info = self._load_collection_info(name)
        if not collection_info:
            return None

        # Prepare Zenodo metadata
        zenodo_metadata = {
            "title": collection_info.get("title", name),
            "description": collection_info.get("description", ""),
            "creators": collection_info.get("creators", []),
            "keywords": collection_info.get("keywords", []),
            "version": collection_info.get("version", "1.0.0"),
            "upload_type": "dataset"
        }

        # Create deposition
        deposition = self.zenodo.create_deposition(zenodo_metadata)

        # Create a manifest file with dataset references
        manifest = {
            "collection": name,
            "datasets": collection_info.get("datasets", []),
            "metadata": collection_info
        }
        manifest_content = json.dumps(manifest, indent=2)

        # Upload manifest to Zenodo
        with open(f"/tmp/{name}_manifest.json", "w") as f:
            f.write(manifest_content)
        self.zenodo.upload_file(deposition.id, f"/tmp/{name}_manifest.json", f"{name}_manifest.json")
        os.remove(f"/tmp/{name}_manifest.json")

        # Publish and get DOI
        doi = self.zenodo.publish_deposition(deposition.id)

        # Update collection metadata with DOI
        collection_info["doi"] = doi
        self.update_collection(name, collection_info)

        return doi