"""Collection management for cloud-collections repository.

Provides operations for updating versioned dataset collections.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .archive import ensure_collection_archive_entry
from .models import (  # noqa: F401 – CollectionDefinition, ReleaseDefinition re-exported
    Collection,
    CollectionDefinition,
    CollectionReleaseRef,
    CollectionVersion,
    ReleaseDefinition,
)

__all__ = [
    "CollectionDefinition",
    "define_collection",
    "update_collection",
    "update_collections_index",
]


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
        col_entry = release_def.collections.get(collection_name)
        if col_entry is not None:
            version_doi = col_entry.doi or ""

    return CollectionDefinition(
        collection_name=collection_name,
        new_version=new_version,
        new_datasets=list(new_datasets),
        release_version=release_def.release_version,
        cde_version=release_def.cde_version,
        version_doi=version_doi or "",
    )


# ── public API ─────────────────────────────────────────────────────────────────

def update_collection(
    collection_def: CollectionDefinition,
    collections_repo_path: Path | str,
) -> None:
    """Apply a :class:`CollectionDefinition` to the cloud-collections repository.

    Merges the new datasets into the collection's current dataset list, adds
    the new version entry to ``versions``, makes it the current version
    (top-level ``date`` / ``doi`` / ``datasets`` / ``teams`` / ``release`` /
    ``version``), writes an immutable snapshot to
    ``archive/<new_version>/collection.json``, and rebuilds ``collections.json``.

    Args:
        collection_def: Collection definition from :func:`define_collection`.
        collections_repo_path: Path to the cloud-collections repository root.
    """
    collections_repo_path = Path(collections_repo_path)
    collection_path = collections_repo_path / collection_def.collection_name
    collection_path.mkdir(parents=True, exist_ok=True)

    collection = Collection.load(collection_path)

    # Build the full dataset list: carry forward current + add new
    current_datasets = list(collection.datasets)
    for ds in collection_def.new_datasets:
        if ds not in current_datasets:
            current_datasets.append(ds)

    release_date = datetime.now().strftime("%Y-%m-%d")
    version_entry = CollectionVersion(
        date=release_date,
        doi=collection_def.version_doi,
        datasets=current_datasets,
        release=CollectionReleaseRef(
            version=collection_def.release_version,
            cde_version=collection_def.cde_version,
            date=release_date,
        ),
    )

    collection.versions[collection_def.new_version] = version_entry
    if not collection.types:
        collection.types = [collection_def.collection_name]
    collection.date = version_entry.date
    collection.doi = version_entry.doi
    collection.datasets = current_datasets
    collection.teams = sorted({ds.split("-")[0] for ds in current_datasets})
    collection.release = version_entry.release
    collection.version = collection_def.new_version
    collection.save(collection_path)

    # Write immutable archive snapshot (this version only)
    ensure_collection_archive_entry(collection_path, collection.version, overwrite=True)

    update_collections_index(collections_repo_path)


def update_collections_index(collections_repo_path: Path | str) -> None:
    """Rebuild ``collections.json`` master index from all ``collection.json`` files.

    The index maps each collection name to its full ``collection.json`` content.

    Args:
        collections_repo_path: Path to the cloud-collections repository root.
    """
    collections_repo_path = Path(collections_repo_path)
    index: dict[str, dict] = {}

    for col_dir in sorted(collections_repo_path.iterdir()):
        if not (col_dir.is_dir() and (col_dir / "collection.json").exists()):
            continue
        collection = Collection.load(col_dir)
        index[collection.name] = collection.model_dump()

    with open(collections_repo_path / "collections.json", "w") as f:
        json.dump(index, f, indent=4)
