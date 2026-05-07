"""Collection management for cloud-collections repository.

Provides operations for updating versioned dataset collections.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .release import ReleaseDefinition

__all__ = [
    "CollectionDefinition",
    "define_collection",
    "update_collection",
    "update_collections_index",
]


@dataclass
class CollectionDefinition:
    """Describes a pending collection version update.

    Produced by :func:`define_collection` and consumed by
    :func:`update_collection`.

    Attributes:
        collection_name: Name of the collection, e.g. ``"pmdbs-sc-rnaseq"``.
        new_version: New collection version string, e.g. ``"v3.2.0"``.
        new_datasets: Dataset names that are new or updated in this version.
        release_version: Release version this collection update belongs to.
        cde_version: CDE schema version applied across datasets in this version.
        version_doi: Zenodo DOI for this specific collection version.
    """

    collection_name: str
    new_version: str
    new_datasets: list[str] = field(default_factory=list)
    release_version: str = ""
    cde_version: str = ""
    version_doi: str = ""


def define_collection(
    collection_name: str,
    new_version: str,
    new_datasets: list[str],
    release_def: ReleaseDefinition,
    version_doi: Optional[str] = None,
) -> CollectionDefinition:
    """Build a :class:`CollectionDefinition` from a release definition.

    Looks up the *version_doi* for this collection from
    ``release_def.collections`` when not explicitly provided.

    Args:
        collection_name: Name of the collection, e.g. ``"pmdbs-sc-rnaseq"``.
        new_version: New collection version string, e.g. ``"v3.2.0"``.
        new_datasets: Dataset names that are new or updated in this version.
        release_def: Release definition from
            :func:`~asap_orchestrator.release.define_release`.
        version_doi: Zenodo DOI for this collection version.  If ``None``,
            the DOI is looked up from ``release_def.collections`` by name.

    Returns:
        A :class:`CollectionDefinition` ready to be passed to
        :func:`update_collection`.
    """
    if version_doi is None:
        for col_entry in release_def.collections:
            if col_entry.get("name") == collection_name:
                version_doi = col_entry.get("doi", "")
                break

    return CollectionDefinition(
        collection_name=collection_name,
        new_version=new_version,
        new_datasets=list(new_datasets),
        release_version=release_def.release_version,
        cde_version=release_def.cde_version,
        version_doi=version_doi or "",
    )


# ── helpers ────────────────────────────────────────────────────────────────────

def _read_collection_json(collection_path: Path) -> dict:
    p = collection_path / "collection.json"
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)


def _write_collection_json(collection_path: Path, data: dict) -> None:
    with open(collection_path / "collection.json", "w") as f:
        json.dump(data, f, indent=2)


# ── public API ─────────────────────────────────────────────────────────────────

def update_collection(
    collection_def: CollectionDefinition,
    collections_repo_path: Path | str,
) -> None:
    """Apply a :class:`CollectionDefinition` to the cloud-collections repository.

    Merges the new datasets into the collection's existing dataset list, adds
    the new version entry to ``collection.json``, writes an immutable snapshot
    to ``archive/<new_version>/collection.json``, and rebuilds
    ``collections.json``.

    Args:
        collection_def: Collection definition from :func:`define_collection`.
        collections_repo_path: Path to the cloud-collections repository root.
    """
    collections_repo_path = Path(collections_repo_path)
    collection_path = collections_repo_path / collection_def.collection_name
    collection_path.mkdir(parents=True, exist_ok=True)

    collection = _read_collection_json(collection_path)
    collection.setdefault("name", collection_def.collection_name)

    # Build the full dataset list: carry forward existing + add new
    versions = collection.setdefault("versions", {})
    if versions:
        latest_ver = max(versions.keys())
        current_datasets: list[str] = list(versions[latest_ver].get("datasets", []))
    else:
        current_datasets = []

    for ds in collection_def.new_datasets:
        if ds not in current_datasets:
            current_datasets.append(ds)

    teams = sorted({ds.split("-")[0] for ds in current_datasets})
    types = collection.get("types", [collection_def.collection_name])

    from datetime import datetime
    release_date = datetime.now().strftime("%Y-%m-%d")

    version_entry = {
        "version": collection_def.new_version,
        "date": release_date,
        "doi": collection_def.version_doi,
        "datasets": current_datasets,
        "teams": teams,
        "types": types,
        "release": {
            "version": collection_def.release_version,
            "cde_version": collection_def.cde_version,
            "date": release_date,
        },
    }

    versions[collection_def.new_version] = version_entry
    _write_collection_json(collection_path, collection)

    # Write immutable archive snapshot
    archive_dir = collection_path / "archive" / collection_def.new_version
    archive_dir.mkdir(parents=True, exist_ok=True)
    with open(archive_dir / "collection.json", "w") as f:
        json.dump(collection, f, indent=2)

    update_collections_index(collections_repo_path)


def update_collections_index(collections_repo_path: Path | str) -> None:
    """Rebuild ``collections.json`` master index from all ``collection.json`` files.

    Args:
        collections_repo_path: Path to the cloud-collections repository root.
    """
    collections_repo_path = Path(collections_repo_path)
    index: dict[str, dict] = {}

    for col_dir in sorted(collections_repo_path.iterdir()):
        col_json = col_dir / "collection.json"
        if not (col_dir.is_dir() and col_json.exists()):
            continue
        with open(col_json) as f:
            data = json.load(f)
        name = data.get("name", col_dir.name)

        versions = data.get("versions", {})
        if versions:
            current_version = max(versions.keys())
            current = versions[current_version]
        else:
            current_version = None
            current = {}

        index[name] = {
            "name": name,
            "title": data.get("title", ""),
            "collection_doi": data.get("collection_doi", ""),
            "current_version": current_version,
            "doi": current.get("doi", ""),
            "datasets": current.get("datasets", []),
            "release": current.get("release", {}),
            "versions": versions,
        }

    with open(collections_repo_path / "collections.json", "w") as f:
        json.dump(index, f, indent=2)
