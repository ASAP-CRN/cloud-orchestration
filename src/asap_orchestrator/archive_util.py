"""Release archive: a local snapshot of a release, synced to the release-resources bucket.

Builds ``<archive_path>/`` for a release::

    <archive_path>/
    ├── <dataset_name>/                 one per dataset in the release
    │   ├── dataset.json, version,      from cloud-datasets
    │   │   DOI/, refs/, archive/
    │   ├── metadata/                   rsync of <curated bucket>/metadata/ + chosen release/<rv>/ files promoted
    │   └── file_metadata/              rsync of <curated bucket>/file_metadata/ + chosen release/<rv>/ files promoted
    ├── collections/<collection>/       from cloud-collections (collections in the release)
    ├── releases/<release_version>/     from cloud-releases (all releases up to and including this one)
    └── CDE/ASAP_CDE_<cde_version>.csv  from cloud-cde, falling back to the CDE Google Sheet

Every copy is an rsync (``local_rsync`` / ``gcloud_rsync``) with ``clobber=False``,
so nothing is ever deleted at the destination.  Every function defaults to
``dry_run=True``: it prints rsync's report of what would be written and returns
the number of files in that report.

Usage::

    import asap_orchestrator as ao

    rv = "v5.1.0"
    n = ao.archive_datasets(rv, releases_repo, datasets_repo, archive, dry_run=True)
    n += ao.archive_collections(rv, releases_repo, collections_repo, archive, dry_run=True)
    n += ao.archive_releases(rv, releases_repo, archive, dry_run=True)
    n += ao.archive_cdes(rv, releases_repo, cde_repo, archive, dry_run=True)
    ao.push_archive_to_bucket(rv, releases_repo, archive, dry_run=True)
"""
from __future__ import annotations

import json
from pathlib import Path

from .bucket_util import gcloud_ls, gcloud_rsync
from .google_spreadsheets import read_google_sheet, GOOGLE_SHEET_ID
from .models import Dataset
from .util import local_rsync

__all__ = [
    "RELEASE_RESOURCES_BUCKET",
    "releases_up_to",
    "report_rsync",
    "latest_release_dir",
    "archive_dataset",
    "archive_datasets",
    "archive_collections",
    "archive_releases",
    "archive_cdes",
    "push_archive_to_bucket",
]

RELEASE_RESOURCES_BUCKET = "gs://asap-crn-cloud-release-resources"


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _load_release(releases_repo_path: Path | str, release_version: str) -> dict:
    return _load_json(Path(releases_repo_path) / release_version / "release.json")


def releases_up_to(releases_repo_path: Path | str, release_version: str) -> list[str]:
    """Release versions from ``releases.json``, oldest first, up to and including *release_version*."""
    index = list(_load_json(Path(releases_repo_path) / "releases.json"))
    return index[: index.index(release_version) + 1]


def report_rsync(out: str) -> int:
    """Print an rsync report (``local_rsync`` or ``gcloud_rsync``) indented.

    Returns:
        Number of file lines in the report: written, or to be written on a dry run.
    """
    n = 0
    for line in out.splitlines():
        if not line.strip():
            continue
        print(f"      {line}")
        if line.startswith((">f", "<f", "Would copy", "Copying")):
            n += 1
    return n


def latest_release_dir(ds_bucket: str, folder: str, release_versions: list[str]) -> str | None:
    """Return the first *release_versions* entry with a ``<folder>/release/<rv>/`` in the bucket.

    Args:
        ds_bucket: ``gs://`` bucket URI.
        folder: ``"metadata"`` or ``"file_metadata"``.
        release_versions: candidate release versions, in order of preference.
    """
    existing = {
        u.rstrip("/").rsplit("/", 1)[-1]
        for u in gcloud_ls(ds_bucket, f"{folder}/release")
        if u.endswith("/")
    }
    present = [rv for rv in release_versions if rv in existing]
    if not present:
        print(f"    no release/<rv>/ found for {folder}/ (tried {release_versions})")
        return None
    if present[0] != release_versions[0]:
        print(f"    WARNING: {folder}/release/{release_versions[0]}/ missing, falling back to {present[0]}")
    return present[0]


# ── archive builders ──────────────────────────────────────────────────────────

def archive_dataset(
    dataset_name: str,
    datasets_repo_path: Path | str,
    archive_path: Path | str,
    release_versions: list[str],
    dry_run: bool = True,
) -> int:
    """Archive one dataset into ``<archive_path>/<dataset_name>/``.

    - ``dataset.json``, ``version``, ``DOI/``, ``refs/``, ``archive/`` from cloud-datasets.
    - ``metadata/`` and ``file_metadata/`` from the curated (prod) bucket, recursively
      (includes every ``release/<rv>/``).
    - The files of one ``release/<rv>/`` are promoted to the top of each folder
      (non-recursive rsync from the bucket).  *rv* is the dataset's most recent
      release in ``dataset.json["releases"]`` that is in *release_versions*,
      falling back to its earlier releases if that folder is missing.

    Args:
        dataset_name: dataset directory name in cloud-datasets.
        datasets_repo_path: root of cloud-datasets.
        archive_path: root of the release archive.
        release_versions: release versions eligible for promotion, oldest first
            (e.g. ``releases_up_to(...)``).
        dry_run: report only, write nothing.

    Returns:
        Number of files written (or that would be written).
    """
    ds_path = Path(datasets_repo_path) / "datasets" / dataset_name
    ds_archive = Path(archive_path) / dataset_name
    dataset_model = Dataset.load(ds_path)
    ds_bucket = dataset_model.buckets.prod  # curated bucket
    print(f"  [{dataset_name}] {dataset_model.version} from {ds_bucket}")
    n = 0

    for fname in ["dataset.json", "version"]:
        if (ds_path / fname).is_file():
            n += report_rsync(local_rsync(ds_path / fname, ds_archive / fname, dry_run=dry_run))
    for folder in ["DOI", "refs", "archive"]:
        if (ds_path / folder).is_dir():
            n += report_rsync(local_rsync(ds_path / folder, ds_archive / folder, directory=True, dry_run=dry_run))

    for folder in ["metadata", "file_metadata"]:
        local = ds_archive / folder
        if not dry_run:
            local.mkdir(parents=True, exist_ok=True)
        n += report_rsync(gcloud_rsync(
            f"{ds_bucket}/{folder}/", f"{local}/", directory=True, dry_run=dry_run, clobber=False
        ))

    # carried-over datasets don't list the current release in dataset.json "releases"
    ds_releases = [rv for rv in reversed(release_versions) if rv in dataset_model.releases]
    print(f"    dataset.json releases (newest first): {ds_releases}")
    for folder in ["metadata", "file_metadata"]:
        rv = latest_release_dir(ds_bucket, folder, ds_releases)
        if rv is None:
            continue
        print(f"    promote {folder}/release/{rv}/ -> {folder}/")
        n += report_rsync(gcloud_rsync(
            f"{ds_bucket}/{folder}/release/{rv}/", f"{ds_archive / folder}/",
            directory=False, dry_run=dry_run, clobber=False,
        ))
    return n


def archive_datasets(
    release_version: str,
    releases_repo_path: Path | str,
    datasets_repo_path: Path | str,
    archive_path: Path | str,
    dry_run: bool = True,
) -> int:
    """Run :func:`archive_dataset` for every dataset in *release_version*'s ``release.json``.

    Returns:
        Number of files written (or that would be written).
    """
    release_info = _load_release(releases_repo_path, release_version)
    release_versions = releases_up_to(releases_repo_path, release_version)
    return sum(
        archive_dataset(name, datasets_repo_path, archive_path, release_versions, dry_run=dry_run)
        for name in release_info["datasets"]
    )


def archive_collections(
    release_version: str,
    releases_repo_path: Path | str,
    collections_repo_path: Path | str,
    archive_path: Path | str,
    dry_run: bool = True,
) -> int:
    """Copy each collection in *release_version* to ``<archive_path>/collections/<collection>/``.

    Returns:
        Number of files written (or that would be written).
    """
    release_info = _load_release(releases_repo_path, release_version)
    n = 0
    for collection in release_info["collections"]:
        print(f"  [{collection}] copy collection")
        n += report_rsync(local_rsync(
            Path(collections_repo_path) / collection,
            Path(archive_path) / "collections" / collection,
            directory=True, dry_run=dry_run,
        ))
    return n


def archive_releases(
    release_version: str,
    releases_repo_path: Path | str,
    archive_path: Path | str,
    dry_run: bool = True,
) -> int:
    """Copy every release up to and including *release_version* to ``<archive_path>/releases/<rv>/``.

    Returns:
        Number of files written (or that would be written).
    """
    n = 0
    for release in releases_up_to(releases_repo_path, release_version):
        src = Path(releases_repo_path) / release
        if not src.is_dir():
            print(f"  [{release}] not found in cloud-releases, skipping")
            continue
        print(f"  [{release}] copy release")
        n += report_rsync(local_rsync(src, Path(archive_path) / "releases" / release, directory=True, dry_run=dry_run))
    return n


def archive_cdes(
    release_version: str,
    releases_repo_path: Path | str,
    cde_repo_path: Path | str,
    archive_path: Path | str,
    dry_run: bool = True,
) -> int:
    """Copy every CDE version used by releases up to *release_version* to ``<archive_path>/CDE/``.

    Each ``ASAP_CDE_<ver>.csv`` comes from cloud-cde; versions missing there are
    read from the CDE Google Sheet (written to the archive only, not cloud-cde).

    Returns:
        Number of files written (or that would be written).
    """
    releases_index = _load_json(Path(releases_repo_path) / "releases.json")
    cde_vers = sorted({
        releases_index[rv]["cde_version"] for rv in releases_up_to(releases_repo_path, release_version)
    })
    archive_cde_path = Path(archive_path) / "CDE"
    n = 0
    for cde_ver in cde_vers:
        dest = archive_cde_path / f"ASAP_CDE_{cde_ver}.csv"
        src = Path(cde_repo_path) / f"ASAP_CDE_{cde_ver}.csv"
        if src.exists():
            print(f"  [{cde_ver}] copy from cloud-cde")
            n += report_rsync(local_rsync(src, dest, dry_run=dry_run))
        elif dry_run:
            print(f"  [{cde_ver}] not in cloud-cde, [DRY RUN] would read Google Sheet -> {dest}")
            n += 1
        else:
            print(f"  [{cde_ver}] not in cloud-cde, reading Google Sheet -> {dest}")
            archive_cde_path.mkdir(parents=True, exist_ok=True)
            read_google_sheet(GOOGLE_SHEET_ID, tab_name=cde_ver).to_csv(dest, index=False)
            n += 1
    return n


def push_archive_to_bucket(
    release_version: str,
    releases_repo_path: Path | str,
    archive_path: Path | str,
    bucket: str = RELEASE_RESOURCES_BUCKET,
    dry_run: bool = True,
) -> int:
    """rsync each top-level archive dir for *release_version* to ``<bucket>/<dir>``.

    Pushes the release's dataset dirs plus ``collections/``, ``releases/`` and ``CDE/``.
    ``clobber=False``: only adds/updates objects, never deletes from the bucket.
    On a dry run, dirs not yet built locally are listed but not rsync'd.

    Returns:
        Number of files uploaded (or that would be uploaded).
    """
    release_info = _load_release(releases_repo_path, release_version)
    archive_dirs = list(release_info["datasets"]) + ["collections", "releases", "CDE"]
    n = 0
    for name in archive_dirs:
        directory = Path(archive_path) / name
        dest = f"{bucket}/{name}"
        if not directory.is_dir():
            print(f"  [{name}] {'[DRY RUN] ' if dry_run else ''}not built locally, skipping rsync -> {dest}")
            continue
        print(f"  [{name}] {'[DRY RUN] ' if dry_run else ''}rsync -> {dest}")
        n += report_rsync(gcloud_rsync(str(directory), dest, directory=True, dry_run=dry_run, clobber=False))
    return n
