"""Release management for cloud-releases repository.

Provides operations for creating and managing ASAP CRN Cloud releases.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import CollectionEntry, DatasetEntry, ReleaseDefinition, ReleaseType  # noqa: F401 – re-exported

__all__ = [
    "ReleaseDefinition",
    "ReleaseType",
    "define_release",
    "perform_release",
]


def define_release(
    release_version: str,
    release_type: ReleaseType,
    cde_version: str,
    datasets: list[dict],
    new_datasets: list[dict],
    collections: list[dict],
) -> ReleaseDefinition:
    """Build a :class:`ReleaseDefinition` describing a pending release.

    Each dataset or collection entry should be a dict with at minimum
    ``"name"``, ``"doi"``, and ``"version"`` keys.

    Args:
        release_version: New release version string, e.g. ``"v4.1.0"``.
        release_type: One of ``"Urgent"``, ``"Minor"``, or ``"Major"``.
        cde_version: CDE schema version applied to all datasets, e.g. ``"v3.3"``.
        datasets: All datasets included in the release.
        new_datasets: Subset of *datasets* that are new or updated.
        collections: All collections included in the release.

    Returns:
        A :class:`ReleaseDefinition` ready to be passed to
        :func:`perform_release` or
        :func:`~asap_orchestrator.collection.update_collection`.
    """
    return ReleaseDefinition(
        release_version=release_version,
        release_type=release_type,
        cde_version=cde_version,
        datasets=[DatasetEntry.model_validate(d) for d in datasets],
        new_datasets=[DatasetEntry.model_validate(d) for d in new_datasets],
        collections=[CollectionEntry.model_validate(d) for d in collections],
    )


def perform_release(
    release_def: ReleaseDefinition,
    releases_repo_path: Path | str,
    release_doi: Optional[str] = None,
) -> Path:
    """Write ``release.json`` and update ``releases.json`` for a new release.

    Creates ``<releases_repo_path>/<release_version>/release.json`` with the
    full release manifest and appends an entry to the top-level
    ``releases.json`` index (and its mirror at ``releases/releases.json`` if
    that directory exists).

    Args:
        release_def: The release definition from :func:`define_release`.
        releases_repo_path: Path to the cloud-releases repository root.
        release_doi: Optional Zenodo concept DOI for the release record itself.

    Returns:
        Path to the newly created release directory.
    """
    releases_repo_path = Path(releases_repo_path)
    version = release_def.release_version

    release_dir = releases_repo_path / version
    release_dir.mkdir(parents=True, exist_ok=True)

    created = datetime.now().isoformat()

    datasets_list = [e.model_dump() for e in release_def.datasets]
    new_datasets_list = [e.model_dump() for e in release_def.new_datasets]
    collections_list = [e.model_dump() for e in release_def.collections]

    release_manifest = {
        "release_version": version,
        "release_type": release_def.release_type,
        "cde_version": release_def.cde_version,
        "release_doi": release_doi or "",
        "datasets": datasets_list,
        "new_datasets": new_datasets_list,
        "collections": collections_list,
        "created": created,
        "metadata": {
            "total_datasets": len(datasets_list),
            "total_collections": len(collections_list),
        },
    }

    with open(release_dir / "release.json", "w") as f:
        json.dump(release_manifest, f, indent=2)

    # Update releases.json index
    index_path = releases_repo_path / "releases.json"
    releases_index: dict[str, dict] = {}
    if index_path.exists():
        with open(index_path) as f:
            releases_index = json.load(f)

    releases_index[version] = {
        "all_datasets": datasets_list,
        "new_datasets": new_datasets_list,
        "all_collections": collections_list,
    }

    with open(index_path, "w") as f:
        json.dump(releases_index, f, indent=2)

    # Mirror to releases/releases.json if that directory exists
    mirror_dir = releases_repo_path / "releases"
    if mirror_dir.is_dir():
        with open(mirror_dir / "releases.json", "w") as f:
            json.dump(releases_index, f, indent=2)

    return release_dir
