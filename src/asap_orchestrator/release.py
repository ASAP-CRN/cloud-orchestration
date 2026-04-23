"""Release management for cloud-releases repository.

Provides operations for creating and managing ASAP CRN Cloud releases.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

__all__ = [
    "ReleaseDefinition",
    "define_release",
    "perform_release",
]

ReleaseType = Literal["Urgent", "Minor", "Major"]


@dataclass
class ReleaseDefinition:
    """Describes a pending release before it is written to disk.

    Produced by :func:`define_release` and consumed by :func:`perform_release`
    and :func:`~asap_orchestrator.collection.update_collection`.

    Attributes:
        release_version: Version string, e.g. ``"v4.1.0"``.
        release_type: ``"Urgent"`` (new uncurated datasets), ``"Minor"``
            (new/updated curated datasets), or ``"Major"`` (new tissue/modality
            scope).
        cde_version: CDE schema version applied across all datasets.
        datasets: All datasets in the release as ``{"name", "doi", "version"}``
            dicts.
        new_datasets: Subset of *datasets* that are newly added or updated.
        collections: All collections as ``{"name", "doi", "version"}`` dicts.
    """

    release_version: str
    release_type: ReleaseType
    cde_version: str
    datasets: list[dict] = field(default_factory=list)
    new_datasets: list[dict] = field(default_factory=list)
    collections: list[dict] = field(default_factory=list)


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
        datasets=list(datasets),
        new_datasets=list(new_datasets),
        collections=list(collections),
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

    release_manifest = {
        "release_version": version,
        "release_type": release_def.release_type,
        "cde_version": release_def.cde_version,
        "release_doi": release_doi or "",
        "datasets": release_def.datasets,
        "new_datasets": release_def.new_datasets,
        "collections": release_def.collections,
        "created": created,
        "metadata": {
            "total_datasets": len(release_def.datasets),
            "total_collections": len(release_def.collections),
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
        "all_datasets": release_def.datasets,
        "new_datasets": release_def.new_datasets,
        "all_collections": release_def.collections,
    }

    with open(index_path, "w") as f:
        json.dump(releases_index, f, indent=2)

    # Mirror to releases/releases.json if that directory exists
    mirror_dir = releases_repo_path / "releases"
    if mirror_dir.is_dir():
        with open(mirror_dir / "releases.json", "w") as f:
            json.dump(releases_index, f, indent=2)

    return release_dir
