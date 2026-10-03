"""Release management for cloud-releases repository.

Provides operations for creating and managing ASAP CRN Cloud releases.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import CollectionEntry, DatasetEntry, ReleaseDefinition  # noqa: F401 – re-exported

__all__ = [
    "ReleaseDefinition",
    "define_release",
    "perform_release",
]


def define_release(
    release_version: str,
    cde_version: str,
    datasets: dict[str, dict],
    new_datasets: list[str],
    collections: dict[str, dict],
) -> ReleaseDefinition:
    """Build a :class:`ReleaseDefinition` describing a pending release.

    Args:
        release_version: New release version string, e.g. ``"v4.1.0"``.
        cde_version: CDE schema version applied to all datasets, e.g. ``"v3.3"``.
        datasets: ``{dataset_name: {"dataset_version", "doi"}}`` for every
            dataset in the release (see :meth:`Dataset.to_release_entry`).
        new_datasets: Names of datasets that are new or updated.
        collections: ``{collection_name: {"doi", "version"}}`` for every
            collection in the release.

    Returns:
        A :class:`ReleaseDefinition` ready to be passed to
        :func:`perform_release` or
        :func:`~asap_orchestrator.collection.define_collection`.
    """
    return ReleaseDefinition(
        release_version=release_version,
        cde_version=cde_version,
        datasets={name: DatasetEntry.model_validate(d) for name, d in datasets.items()},
        new_datasets=list(new_datasets),
        collections={name: CollectionEntry.model_validate(c) for name, c in collections.items()},
        datasets_names=list(datasets),
        collection_names=list(collections),
    )


def perform_release(
    release_def: ReleaseDefinition,
    releases_repo_path: Path | str,
    release_doi: Optional[str] = None,
) -> Path:
    """Write ``release.json`` and update ``releases.json`` for a new release.

    Creates ``<releases_repo_path>/<release_version>/release.json`` and sets
    ``releases.json[<release_version>]`` to the same content (also mirrored to
    ``releases/releases.json`` if that directory exists).

    Args:
        release_def: The release definition from :func:`define_release`.
            ``created`` is set to now, and ``release_doi`` when given.
        releases_repo_path: Path to the cloud-releases repository root.
        release_doi: Optional Zenodo concept DOI for the release record itself.

    Returns:
        Path to the newly created release directory.
    """
    releases_repo_path = Path(releases_repo_path)
    version = release_def.release_version

    release_dir = releases_repo_path / version
    release_dir.mkdir(parents=True, exist_ok=True)

    if release_doi:
        release_def.release_doi = release_doi
    release_def.created = datetime.now().isoformat()
    release_def.save(release_dir)

    # Update releases.json index
    index_path = releases_repo_path / "releases.json"
    releases_index: dict[str, dict] = {}
    if index_path.exists():
        with open(index_path) as f:
            releases_index = json.load(f)

    releases_index[version] = release_def.model_dump()

    with open(index_path, "w") as f:
        json.dump(releases_index, f, indent=4)

    # Mirror to releases/releases.json if that directory exists
    mirror_dir = releases_repo_path / "releases"
    if mirror_dir.is_dir():
        with open(mirror_dir / "releases.json", "w") as f:
            json.dump(releases_index, f, indent=4)

    return release_dir
