"""Dataset management for cloud-datasets repository.

Provides operations for Dataset DOI creation and version maintenance.
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Creator, Dataset, DatasetBuckets, ReleaseRecord, VersionRecord
from .zenodo_util import ZenodoClient

__all__ = [
    "DatasetDefinition",
    "Dataset",
    "define_dataset",
    "create_dataset_stub",
    "read_dataset_entry",
    "create_dataset_doi",
    "update_dataset_doi",
    "publish_dataset_doi",
    "update_dataset_version",
    "update_datasets_index",
]

# Backward-compatible alias re-exported from models
DatasetDefinition = Dataset


def define_dataset(
    name: str,
    collection: Optional[str] = None,
    version: str = "v0.1",
    doi: str = "",
    cde_version: str = "",
    title: str = "",
    description: str = "",
    creators: Optional[list[dict]] = None,
    keywords: Optional[list[str]] = None,
    buckets: Optional[dict] = None,
    references: Optional[list] = None,
    license: str = "CC-BY-4.0",
) -> Dataset:
    """Build a :class:`Dataset` for a new or updated dataset.

    Bucket paths are inferred from *name* when not provided, following the
    ASAP CRN naming convention::

        raw:  gs://asap-raw-<name>
        dev:  gs://asap-dev-<name>
        uat:  gs://asap-uat-<name>
        prod: gs://asap-curated-<name>

    Args:
        name: Dataset name, e.g. ``"hafler-pmdbs-sn-rnaseq-pfc"``.
        collection: Collection name, e.g. ``"pmdbs-sc-rnaseq"``.  ``None``
            for uncurated/urgent-release datasets.
        version: Initial version string (default ``"v0.1"``).
        doi: Zenodo concept DOI if already assigned.
        cde_version: CDE schema version to apply.
        title: Human-readable title; defaults to *name*.
        description: Short description; auto-generated from *collection* and
            team name if omitted.
        creators: List of creator dicts; inferred from team prefix if omitted.
        keywords: Keyword list; inferred from *collection* and team if omitted.
        buckets: GCS bucket map; inferred from *name* if omitted.
        references: Zenodo reference strings.
        license: SPDX license id.

    Returns:
        A :class:`Dataset` ready for :func:`create_dataset_stub`.
    """
    team = name.split("-")[0]

    if buckets is None:
        resolved_buckets = DatasetBuckets(
            raw=f"gs://asap-raw-{name}",
            dev=f"gs://asap-dev-{name}",
            uat=f"gs://asap-uat-{name}",
            prod=f"gs://asap-curated-{name}",
        )
    else:
        resolved_buckets = DatasetBuckets(**buckets)

    if keywords is None:
        keywords = [k for k in [collection, team] if k]
    if creators is None:
        resolved_creators = [Creator(name=f"team-{team}", affiliation="ASAP CRN")]
    else:
        resolved_creators = [Creator(**c) for c in creators]

    auto_description = (
        f"{collection} dataset from team-{team}" if collection else f"Dataset from team-{team}"
    )

    return Dataset(
        name=name,
        collection=collection,
        version=version,
        doi=doi or None,
        cde_version=cde_version or None,
        title=title or name,
        description=description or auto_description,
        creators=resolved_creators,
        keywords=keywords,
        buckets=resolved_buckets,
        references=list(references) if references else [],
        license=license,
    )


def create_dataset_stub(
    dataset_def: Dataset,
    datasets_repo_path: Path | str,
    wip: bool = True,
) -> Path:
    """Write a ``dataset.json`` stub for a new dataset.

    Places the dataset under ``WIP/<name>/`` when *wip* is ``True``, or
    directly under ``<datasets_repo_path>/<name>/`` otherwise.  Also creates
    empty ``DOI/`` and ``refs/`` subdirectories.

    Args:
        dataset_def: Dataset definition from :func:`define_dataset`.
        datasets_repo_path: Path to the cloud-datasets repository root.
        wip: Place dataset under ``WIP/`` subdirectory (default ``True``).

    Returns:
        Path to the newly created dataset directory.
    """
    datasets_repo_path = Path(datasets_repo_path)
    parent = datasets_repo_path / "WIP" if wip else datasets_repo_path
    ds_path = parent / dataset_def.name
    ds_path.mkdir(parents=True, exist_ok=True)
    (ds_path / "DOI").mkdir(exist_ok=True)
    (ds_path / "refs").mkdir(exist_ok=True)

    dataset_def.save(ds_path)
    return ds_path


def read_dataset_entry(ds_path: Path | str) -> dict:
    """Read a dataset's release entry from its ``dataset.json``.

    Returns the minimal ``{"name", "doi", "version"}`` dict used in release
    and collection manifests.

    Args:
        ds_path: Path to the dataset directory in cloud-datasets.
    """
    ds_path = Path(ds_path)
    try:
        dataset = Dataset.load(ds_path)
        return dataset.to_release_entry()
    except FileNotFoundError:
        return {"name": ds_path.name, "doi": "", "version": ""}


# ── helpers ────────────────────────────────────────────────────────────────────

def _doi_dir(ds_path: Path) -> Path:
    return ds_path / "DOI"


def _read_doi_metadata(ds_path: Path) -> dict:
    """Read Zenodo metadata dict from DOI/<dataset-name>.json."""
    meta_file = _doi_dir(ds_path) / f"{ds_path.name}.json"
    if not meta_file.exists():
        raise FileNotFoundError(f"DOI metadata not found: {meta_file}")
    import json
    with open(meta_file) as f:
        data = json.load(f)
    return data.get("metadata", data)


def _write_doi_files(ds_path: Path, deposition: dict, *, prerelease: bool) -> None:
    """Write version.doi, dataset.doi, anchor file, and deposition.json."""
    import json
    doi_dir = _doi_dir(ds_path)
    doi_dir.mkdir(parents=True, exist_ok=True)

    doi = deposition.get("doi", "")
    doi_url = deposition.get("doi_url", "")

    if not doi:
        prereserve = deposition.get("metadata", {}).get("prereserve_doi", {})
        doi = prereserve.get("doi", "")
        doi_url = f"https://doi.org/{doi}"

    if "conceptdoi" in deposition:
        concept_doi = deposition["conceptdoi"]
    else:
        concept_doi = f"10.5281/zenodo.{deposition['conceptrecid']}"
    concept_url = f"https://doi.org/{concept_doi}"

    (doi_dir / "version.doi").write_text(doi)
    (doi_dir / "dataset.doi").write_text(concept_doi)

    anchor = concept_doi.replace("/", "_")
    label = "CURRENT (prerelease)" if prerelease else "CURRENT            "
    (doi_dir / anchor).write_text(
        f"ALL_VERSIONS        : {concept_url}\n{label}: {doi_url}"
    )

    with open(doi_dir / "deposition.json", "w") as f:
        json.dump(deposition, f, indent=2)


# ── public API ─────────────────────────────────────────────────────────────────

def create_dataset_doi(
    ds_path: Path | str,
    zenodo: ZenodoClient,
    version: str = "v0.1",
    publication_date: Optional[str] = None,
) -> dict:
    """Create an initial draft DOI for an accepted dataset.

    Reads Zenodo metadata from ``DOI/<dataset-name>.json``, creates a new
    Zenodo draft deposition, writes DOI reference files back to ``DOI/``,
    and records the concept DOI in ``dataset.json``.

    Datasets are accepted as ``"v0.1"``; they are bumped to ``"v1.0"`` when
    first released via :func:`update_dataset_version`.

    Args:
        ds_path: Path to the dataset directory in cloud-datasets.
        zenodo: Authenticated :class:`~asap_orchestrator.zenodo_util.ZenodoClient`.
        version: Initial dataset version (default ``"v0.1"``).
        publication_date: ISO date string ``"YYYY-MM-DD"``; defaults to today.

    Returns:
        The Zenodo deposition dict for the new draft.
    """
    ds_path = Path(ds_path)
    if publication_date is None:
        publication_date = datetime.now().strftime("%Y-%m-%d")

    metadata = _read_doi_metadata(ds_path)
    metadata["version"] = version
    metadata.setdefault("publication_date", publication_date)

    deposition = zenodo.create_new_deposition()
    deposition = zenodo.change_metadata(metadata)

    _write_doi_files(ds_path, deposition, prerelease=True)

    dataset = Dataset.load(ds_path)
    concept_doi = (_doi_dir(ds_path) / "dataset.doi").read_text().strip()
    dataset.doi = concept_doi or None
    if not dataset.version:
        dataset.version = version
    dataset.save(ds_path)

    return deposition


def update_dataset_doi(
    ds_path: Path | str,
    zenodo: ZenodoClient,
    metadata: Optional[dict] = None,
) -> dict:
    """Update Zenodo metadata for an existing dataset DOI.

    If the deposition is already published it is unlocked for editing first.

    Args:
        ds_path: Path to the dataset directory.
        zenodo: Authenticated :class:`~asap_orchestrator.zenodo_util.ZenodoClient`.
        metadata: Metadata dict to apply.  If ``None``, re-reads from
            ``DOI/<dataset-name>.json``.

    Returns:
        Updated Zenodo deposition dict.
    """
    ds_path = Path(ds_path)
    doi_file = _doi_dir(ds_path) / "version.doi"
    if not doi_file.exists():
        raise FileNotFoundError(f"version.doi not found in {_doi_dir(ds_path)}")
    doi_id = doi_file.read_text().strip().split(".")[-1]

    if metadata is None:
        metadata = _read_doi_metadata(ds_path)

    zenodo.deposition_id = doi_id
    if zenodo.deposition.get("state") == "done":
        zenodo.unlock_deposition()

    return zenodo.change_metadata(metadata)


def publish_dataset_doi(
    ds_path: Path | str,
    zenodo: ZenodoClient,
) -> dict:
    """Publish a draft DOI for a dataset.

    Updates the local ``DOI/`` files with the published deposition data.

    Args:
        ds_path: Path to the dataset directory.
        zenodo: Authenticated :class:`~asap_orchestrator.zenodo_util.ZenodoClient`.

    Returns:
        Published Zenodo deposition dict.
    """
    ds_path = Path(ds_path)
    doi_file = _doi_dir(ds_path) / "version.doi"
    if not doi_file.exists():
        raise FileNotFoundError(f"version.doi not found in {_doi_dir(ds_path)}")
    doi_id = doi_file.read_text().strip().split(".")[-1]

    zenodo.deposition_id = doi_id
    dep = zenodo.deposition
    if dep.get("state") == "done":
        return dep

    deposition = zenodo.publish()
    _write_doi_files(ds_path, deposition, prerelease=False)
    return deposition


def update_dataset_version(
    ds_path: Path | str,
    new_version: str,
    release_version: str,
    cde_version: str,
    zenodo: Optional[ZenodoClient] = None,
) -> None:
    """Archive the current state and bump the dataset to a new version.

    Copies ``DOI/`` and ``refs/`` to ``archive/<old_version>/``, then updates
    ``dataset.json`` with the new version, records the version in
    ``all_versions``, and adds a release record.  If *zenodo* is supplied, a
    new Zenodo version draft is created via the ``newversion`` action.

    Args:
        ds_path: Path to the dataset directory.
        new_version: New version string, e.g. ``"v1.0"``.
        release_version: Release this bump is tied to, e.g. ``"v4.1.0"``.
        cde_version: CDE schema version for this release, e.g. ``"v3.3"``.
        zenodo: Optional :class:`~asap_orchestrator.zenodo_util.ZenodoClient`;
            when provided creates a Zenodo version draft for the new version.
    """
    ds_path = Path(ds_path)
    dataset = Dataset.load(ds_path)
    old_version = dataset.version

    archive_dir = ds_path / "archive" / old_version
    archive_dir.mkdir(parents=True, exist_ok=True)
    for subdir in ("DOI", "refs"):
        src = ds_path / subdir
        if src.exists():
            dst = archive_dir / subdir
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    if zenodo is not None:
        doi_file = _doi_dir(ds_path) / "version.doi"
        if doi_file.exists():
            old_doi_id = doi_file.read_text().strip().split(".")[-1]
            zenodo.deposition_id = old_doi_id
            new_dep = zenodo.make_new_version()
            _write_doi_files(ds_path, new_dep, prerelease=True)

    version_doi = ""
    doi_file = _doi_dir(ds_path) / "version.doi"
    if doi_file.exists():
        version_doi = doi_file.read_text().strip()

    dataset.version = new_version
    dataset.all_versions[new_version] = VersionRecord(doi=version_doi)
    dataset.releases[release_version] = ReleaseRecord(
        cde_version=cde_version, dataset_version=new_version
    )
    dataset.save(ds_path)


def update_datasets_index(datasets_repo_path: Path | str) -> None:
    """Rebuild ``datasets.json`` master index from all ``dataset.json`` files.

    Args:
        datasets_repo_path: Path to the cloud-datasets repository root.
    """
    import json

    datasets_repo_path = Path(datasets_repo_path)
    index: dict[str, dict] = {}
    for ds_dir in sorted(datasets_repo_path.iterdir()):
        if not ds_dir.is_dir():
            continue
        try:
            dataset = Dataset.load(ds_dir)
        except FileNotFoundError:
            continue
        index[dataset.name] = {
            "name": dataset.name,
            "title": dataset.title,
            "version": dataset.version,
            "doi": dataset.doi or "",
            "collection": dataset.collection or "",
            "release": {k: v.model_dump() for k, v in dataset.releases.items()},
        }
    with open(datasets_repo_path / "datasets.json", "w") as f:
        json.dump(index, f, indent=2)
