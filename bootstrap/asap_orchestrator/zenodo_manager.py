"""Zenodo API client for DOI generation and version management."""

import os
import requests
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class ZenodoDeposition:
    """Represents a Zenodo deposition."""
    id: int
    doi: Optional[str]
    title: str
    version: str
    status: str


class ZenodoManager:
    """Manages Zenodo deposits for DOI generation and versioning."""

    BASE_URL = "https://zenodo.org/api"

    def __init__(self, token: Optional[str] = None):
        """Initialize Zenodo manager with access token."""
        self.token = token or os.getenv("ZENODO_TOKEN")
        if not self.token:
            raise ValueError("Zenodo access token is required")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def create_deposition(self, metadata: Dict) -> ZenodoDeposition:
        """Create a new deposition."""
        url = f"{self.BASE_URL}/deposit/depositions"
        response = requests.post(url, json={"metadata": metadata}, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return ZenodoDeposition(
            id=data["id"],
            doi=data.get("doi"),
            title=data["title"],
            version=data.get("metadata", {}).get("version", ""),
            status=data["state"]
        )

    def update_deposition(self, deposition_id: int, metadata: Dict) -> None:
        """Update deposition metadata."""
        url = f"{self.BASE_URL}/deposit/depositions/{deposition_id}"
        response = requests.put(url, json={"metadata": metadata}, headers=self.headers)
        response.raise_for_status()

    def upload_file(self, deposition_id: int, file_path: str, filename: str) -> None:
        """Upload a file to a deposition."""
        url = f"{self.BASE_URL}/deposit/depositions/{deposition_id}/files"
        with open(file_path, "rb") as f:
            files = {"file": (filename, f)}
            response = requests.post(url, files=files, headers=self.headers)
            response.raise_for_status()

    def publish_deposition(self, deposition_id: int) -> str:
        """Publish a deposition and get DOI."""
        url = f"{self.BASE_URL}/deposit/depositions/{deposition_id}/actions/publish"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data["doi"]

    def create_new_version(self, deposition_id: int) -> int:
        """Create a new version of an existing deposition."""
        url = f"{self.BASE_URL}/deposit/depositions/{deposition_id}/actions/newversion"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        # Extract new deposition ID from the response
        new_url = data["links"]["latest_draft"]
        new_id = int(new_url.split("/")[-1])
        return new_id

    def get_deposition(self, deposition_id: int) -> ZenodoDeposition:
        """Get deposition details."""
        url = f"{self.BASE_URL}/deposit/depositions/{deposition_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return ZenodoDeposition(
            id=data["id"],
            doi=data.get("doi"),
            title=data["title"],
            version=data.get("metadata", {}).get("version", ""),
            status=data["state"]
        )

    def list_depositions(self) -> List[ZenodoDeposition]:
        """List all depositions."""
        url = f"{self.BASE_URL}/deposit/depositions"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return [
            ZenodoDeposition(
                id=item["id"],
                doi=item.get("doi"),
                title=item["title"],
                version=item.get("metadata", {}).get("version", ""),
                status=item["state"]
            )
            for item in data
        ]