"""Main orchestration logic for ASAP CRN cloud management."""

from typing import Optional
from datetime import datetime
import json
from .github_manager import GitHubManager
from .zenodo_manager import ZenodoManager
from .dataset_manager import DatasetManager
from .collection_manager import CollectionManager
from .cde_manager import CDEManager


class Orchestrator:
    """Main orchestrator for managing ASAP CRN cloud repositories."""

    def __init__(self, github_token: str, zenodo_token: Optional[str] = None):
        """Initialize the orchestrator."""
        self.github_manager = GitHubManager(github_token)
        self.zenodo_manager = ZenodoManager(zenodo_token) if zenodo_token else None
        self.dataset_manager = DatasetManager(self.github_manager, self.zenodo_manager)
        self.collection_manager = CollectionManager(self.github_manager, self.zenodo_manager)
        self.cde_manager = CDEManager(self.github_manager)

    def process_release(self, version: str):
        """Process a new release: update repos, create DOIs, etc."""
        print(f"Processing release {version}")

        # Create release in cloud-releases repo
        release_body = f"Release {version}\n\nDatasets and Collections updated."
        self.github_manager.create_release("ASAP-CRN/cloud-releases", version, f"Release {version}", release_body)

        # Update releases index
        self.update_releases_index()

        # Get all datasets and collections
        datasets = self.dataset_manager.get_datasets()
        collections = self.collection_manager.get_collections()

        print(f"Found {len(datasets)} datasets and {len(collections)} collections")

        # Update versions in metadata
        for dataset in datasets:
            if 'version' not in dataset:
                dataset['version'] = version
                self.dataset_manager.update_dataset(dataset['name'], dataset)

        for collection in collections:
            if 'version' not in collection:
                collection['version'] = version
                self.collection_manager.update_collection(collection['name'], collection)

        # Generate/update DOIs if Zenodo is configured
        if self.zenodo_manager:
            print("Generating/updating DOIs via Zenodo...")
            for dataset in datasets:
                if 'doi' not in dataset or not dataset.get('doi'):
                    doi = self.dataset_manager.publish_to_zenodo(dataset['name'])
                    if doi:
                        print(f"Generated DOI for dataset {dataset['name']}: {doi}")

            for collection in collections:
                if 'doi' not in collection or not collection.get('doi'):
                    doi = self.collection_manager.publish_to_zenodo(collection['name'])
                    if doi:
                        print(f"Generated DOI for collection {collection['name']}: {doi}")

        # Update CDE repo if needed
        # This would involve checking for new common data elements
        # For now, just create a release
        self.github_manager.create_release("ASAP-CRN/cloud-cde", version, f"CDE Release {version}", f"Common Data Elements for release {version}")

        print(f"Release {version} processing complete")

    def update_releases_index(self) -> None:
        """Update the releases index JSON file."""
        releases = self.github_manager.get_releases("ASAP-CRN/cloud-releases")
        release_data = []
        
        for release in releases:
            release_info = {
                "version": release.tag_name,
                "title": release.title,
                "body": release.body,
                "created_at": release.created_at.isoformat() if release.created_at else None,
                "published_at": release.published_at.isoformat() if release.published_at else None
            }
            release_data.append(release_info)
        
        index_data = {
            "last_updated": datetime.now().isoformat(),
            "total_releases": len(release_data),
            "releases": release_data
        }
        
        index_content = json.dumps(index_data, indent=2)
        repo = self.github_manager.get_repo("ASAP-CRN/cloud-releases")
        try:
            contents = repo.get_contents("releases.json")
            repo.update_file("releases.json", "Update releases index", index_content, contents.sha)
        except:
            repo.create_file("releases.json", "Create releases index", index_content)

    def get_status(self) -> dict:
        """Get current status of all repositories."""
        return {
            'datasets': self.dataset_manager.get_datasets(),
            'collections': self.collection_manager.get_collections(),
            'cdes': self.cde_manager.get_cdes(),
            'releases': self.github_manager.get_releases("ASAP-CRN/cloud-releases"),
            'cde_releases': self.github_manager.get_releases("ASAP-CRN/cloud-cde")
        }