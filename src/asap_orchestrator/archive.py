"""Archive management for versioned snapshots in cloud-datasets and cloud-collections.

**Dataset archives** — ``archive/<version>/dataset.json`` snapshots represent a
dataset *at* a given version, with its history up to that version: ``releases``
and ``curation`` cover every release of ``all_versions``, which ends at that
version.

**Collection archives** — ``archive/<version>/collection.json`` snapshots represent
a collection *at* a given version, with its history up to that version:
``versions`` contains every entry up to and including the target version, and
the top-level current fields (``version``, ``date``, ``doi``, ``datasets``,
``teams``, ``release``) describe the target version.

Usage::

    import asap_orchestrator as ao

    # ── Dataset archives ──────────────────────────────────────────────────────
    # Validate all archive entries for a dataset
    report = ao.validate_all_archives(
        ds_path=datasets_repo / "datasets" / "jakobsson-pmdbs-sn-rnaseq",
        releases_repo_path=releases_repo,
    )
    for version, issues in report.items():
        print(version, issues or "OK")

    # Repair a bad archive entry
    ao.repair_archive_entry(ds_path, "v2.0")

    # Create missing archive entries for all historical versions
    ao.ensure_all_archives(ds_path)

    # ── Collection archives ───────────────────────────────────────────────────
    # Validate all collection archive entries
    report = ao.validate_all_collection_archives(
        col_path=collections_repo / "pmdbs-sc-rnaseq",
        releases_repo_path=releases_repo,
    )
    for version, issues in report.items():
        print(version, issues or "OK")

    # Backfill collection archives for all historical versions
    ao.ensure_all_collection_archives(collections_repo / "pmdbs-sc-rnaseq")
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

Issues = list[str]


# ── internal helpers ──────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _versions_up_to(all_versions: list[str], version: str) -> list[str]:
    """Return *all_versions* up to and including *version*."""
    if version not in all_versions:
        raise KeyError(f"version '{version}' not in all_versions {all_versions}")
    return all_versions[: all_versions.index(version) + 1]


# ── public API ────────────────────────────────────────────────────────────────

def build_archive_dataset(ds_path: Path | str, version: str) -> dict:
    """Build a version-scoped ``dataset.json`` dict for an archive entry.

    Reads the current ``dataset.json`` and returns a new dict representing the
    dataset *at* *version*:

    - ``version`` is forced to *version*.
    - ``all_versions`` is truncated after *version*.
    - ``releases`` is filtered to releases that shipped one of those versions.
    - ``curation`` is filtered to those same releases.

    All other fields (name, doi, creators, buckets, etc.) are carried over
    unchanged from the current ``dataset.json``.

    Args:
        ds_path: Dataset directory containing ``dataset.json``.
        version: The dataset version this archive entry represents, e.g. ``"v1.0"``.

    Returns:
        Dict ready to write as ``archive/<version>/dataset.json``.

    Raises:
        KeyError: When *version* is not in ``all_versions``.
    """
    ds_path = Path(ds_path)
    ds = _load_json(ds_path / "dataset.json")

    versions = _versions_up_to(ds.get("all_versions", []), version)
    filtered = {rv: dv for rv, dv in ds.get("releases", {}).items() if dv in versions}
    curation = ds.get("curation", {})

    # Build the archive entry from the current dataset, overriding version-specific fields
    entry = {k: v for k, v in ds.items()}
    entry["version"] = version
    entry["curation"] = {rv: curation[rv] for rv in filtered if rv in curation}
    entry["all_versions"] = versions
    entry["releases"] = filtered

    return entry


def ensure_archive_entry(
    ds_path: Path | str,
    version: str,
    *,
    overwrite: bool = False,
) -> Path:
    """Write ``archive/<version>/dataset.json`` unless it already exists.

    Only writes ``dataset.json``; any existing ``DOI/`` and ``refs/``
    subdirectories in the archive directory are left untouched.

    Args:
        ds_path: Dataset directory.
        version: Dataset version to archive, e.g. ``"v1.0"``.
        overwrite: When ``True``, always rewrite even if the file exists.

    Returns:
        Path to the ``archive/<version>/`` directory.
    """
    ds_path = Path(ds_path)
    archive_dir = ds_path / "archive" / version
    archive_json = archive_dir / "dataset.json"

    if archive_json.exists() and not overwrite:
        return archive_dir

    archive_dir.mkdir(parents=True, exist_ok=True)
    entry = build_archive_dataset(ds_path, version)
    archive_json.write_text(json.dumps(entry, indent=4))
    return archive_dir


def repair_archive_entry(ds_path: Path | str, version: str) -> Path:
    """Overwrite ``archive/<version>/dataset.json`` with a freshly built entry.

    Use this to fix archive entries whose ``releases`` dict incorrectly
    includes releases from other dataset versions.

    Args:
        ds_path: Dataset directory.
        version: Dataset version to repair, e.g. ``"v2.0"``.

    Returns:
        Path to the ``archive/<version>/`` directory.
    """
    return ensure_archive_entry(ds_path, version, overwrite=True)


def validate_archive_entry(
    ds_path: Path | str,
    version: str,
    releases_repo_path: Optional[Path | str] = None,
) -> Issues:
    """Validate ``archive/<version>/dataset.json`` for one dataset version.

    Checks:

    - The archive directory and ``dataset.json`` exist.
    - The ``version`` field in the archive matches the directory name.
    - ``all_versions``, if present, ends at *version*.
    - Every ``releases`` entry maps to a version in ``all_versions``.
    - If *releases_repo_path* given: each listed release exists in
      cloud-releases and contains this dataset at the correct version.

    Args:
        ds_path: Dataset directory.
        version: Dataset version to validate, e.g. ``"v1.0"``.
        releases_repo_path: Root of the cloud-releases repository (optional).

    Returns:
        List of human-readable issue strings.  Empty list means clean.
    """
    ds_path = Path(ds_path)
    issues: Issues = []

    archive_dir = ds_path / "archive" / version
    archive_json = archive_dir / "dataset.json"

    if not archive_dir.exists():
        return [f"archive directory missing: {archive_dir}"]
    if not archive_json.exists():
        return [f"dataset.json missing in archive: {archive_json}"]

    arch = _load_json(archive_json)
    ds_name: str = arch.get("name", ds_path.name)
    arch_version: str = arch.get("version", "")
    arch_releases: dict[str, str] = arch.get("releases", {})
    arch_all_versions: Optional[list] = arch.get("all_versions")  # may be absent in old format

    # ── version field must match directory name ───────────────────────────────
    # normalise so "v1.0" == "v1.0" and "1.0" == "v1.0"
    def _vn(v: str) -> str:
        return v if v.startswith("v") else f"v{v}"

    if _vn(arch_version) != _vn(version):
        issues.append(
            f"version field '{arch_version}' does not match "
            f"archive directory '{version}'"
        )

    # ── all_versions, if present, must end at this version ───────────────────
    if arch_all_versions is not None and (
        not arch_all_versions or _vn(arch_all_versions[-1]) != _vn(version)
    ):
        issues.append(
            f"all_versions should end at '{version}' for an archive snapshot, "
            f"got {arch_all_versions}"
        )

    # ── releases must all be for versions up to this one ─────────────────────
    known = {_vn(v) for v in (arch_all_versions or [version])}
    wrong = {rv: dv for rv, dv in arch_releases.items() if _vn(dv) not in known}
    if wrong:
        issues.append(
            f"releases contain entries for versions after '{version}': "
            + ", ".join(f"'{rv}' (dataset_version='{dv}')" for rv, dv in wrong.items())
        )

    # ── cross-reference against release.json files ───────────────────────────
    if releases_repo_path is not None:
        releases_repo_path = Path(releases_repo_path)
        for rv in arch_releases:
            release_json = releases_repo_path / rv / "release.json"
            if not release_json.exists():
                issues.append(f"release '{rv}' not found: {release_json}")
                continue

            release = _load_json(release_json)
            found = {
                name: e.get("dataset_version", "")
                for name, e in release.get("datasets", {}).items()
            }
            if ds_name not in found:
                issues.append(
                    f"dataset '{ds_name}' not found in release '{rv}' datasets"
                )
            else:
                rel_version = found[ds_name]
                if rel_version and rel_version != arch_releases[rv]:
                    issues.append(
                        f"version mismatch in release '{rv}': "
                        f"release says '{rel_version}', archive records '{arch_releases[rv]}'"
                    )

    return issues


def validate_all_archives(
    ds_path: Path | str,
    releases_repo_path: Optional[Path | str] = None,
) -> dict[str, Issues]:
    """Validate all archive entries for a dataset.

    Checks every directory under ``archive/`` and also flags versions listed
    in ``dataset.all_versions`` (excluding the current version) that have no
    archive directory at all.

    Args:
        ds_path: Dataset directory.
        releases_repo_path: Root of the cloud-releases repository (optional).

    Returns:
        ``{version: [issue, ...]}`` for every archived version.  A version
        that has no issues maps to an empty list.  Versions with missing
        archive directories appear with a single issue string.
    """
    ds_path = Path(ds_path)
    results: dict[str, Issues] = {}

    archive_root = ds_path / "archive"
    if archive_root.exists():
        for version_dir in sorted(archive_root.iterdir()):
            if not version_dir.is_dir():
                continue
            ver = version_dir.name
            results[ver] = validate_archive_entry(ds_path, ver, releases_repo_path)

    # Flag historical versions that have no archive entry at all
    ds_json_path = ds_path / "dataset.json"
    if ds_json_path.exists():
        ds = _load_json(ds_json_path)
        current_version: str = ds.get("version", "")
        for ver in ds.get("all_versions", []):
            if ver == current_version:
                continue  # current version lives at root, not in archive
            if ver not in results:
                results[ver] = [f"archive directory missing for version '{ver}'"]

    return results


def ensure_all_archives(
    ds_path: Path | str,
    *,
    overwrite: bool = False,
) -> dict[str, Path]:
    """Ensure archive entries exist for all non-current versions.

    Creates ``archive/<version>/dataset.json`` for each version in
    ``dataset.all_versions`` that does not already have one (or all, if
    *overwrite* is ``True``).

    Args:
        ds_path: Dataset directory.
        overwrite: When ``True``, recreate all archive entries.

    Returns:
        ``{version: archive_dir}`` for every version processed.
    """
    ds_path = Path(ds_path)

    ds_json_path = ds_path / "dataset.json"
    if not ds_json_path.exists():
        raise FileNotFoundError(f"dataset.json not found: {ds_json_path}")

    ds = _load_json(ds_json_path)
    current_version: str = ds.get("version", "")
    results: dict[str, Path] = {}

    for ver in ds.get("all_versions", []):
        if ver == current_version:
            continue
        archive_dir = ensure_archive_entry(ds_path, ver, overwrite=overwrite)
        results[ver] = archive_dir

    return results


# ── Collection archive API ────────────────────────────────────────────────────

def build_archive_collection(col_path: Path | str, version: str) -> dict:
    """Build a version-scoped ``collection.json`` dict for a collection archive entry.

    Reads the current ``collection.json`` and returns a new dict with the same
    metadata (``name``, ``title``, ``collection_doi``, ``types``), ``versions``
    truncated after *version*, the top-level current fields
    (``date``, ``doi``, ``datasets``, ``teams``, ``release``, ``version``) set
    from that entry, and ``curation`` limited to that version's datasets.

    Args:
        col_path: Collection directory containing ``collection.json``.
        version: The collection version this archive represents, e.g. ``"v3.1.1"``.

    Returns:
        Dict ready to write as ``archive/<version>/collection.json``.

    Raises:
        KeyError: When *version* is not present in ``collection.json``.
    """
    col_path = Path(col_path)
    col = _load_json(col_path / "collection.json")

    versions: dict = col.get("versions", {})
    if version not in versions:
        raise KeyError(
            f"version '{version}' not found in {col_path / 'collection.json'}; "
            f"available: {sorted(versions.keys())}"
        )

    keys = list(versions)
    ver_entry = versions[version]

    entry = {k: v for k, v in col.items()}
    entry["date"] = ver_entry.get("date")
    entry["doi"] = ver_entry.get("doi")
    entry["datasets"] = ver_entry.get("datasets", [])
    entry["teams"] = sorted({ds.split("-")[0] for ds in entry["datasets"]})
    entry["release"] = ver_entry.get("release", {})
    entry["version"] = version
    entry["versions"] = {k: versions[k] for k in keys[: keys.index(version) + 1]}
    entry["curation"] = {
        ds: rec for ds, rec in col.get("curation", {}).items() if ds in entry["datasets"]
    }
    return entry


def ensure_collection_archive_entry(
    col_path: Path | str,
    version: str,
    *,
    overwrite: bool = False,
) -> Path:
    """Write ``archive/<version>/collection.json`` unless it already exists.

    Only writes ``collection.json``; any existing ``DOI/`` subdirectory in the
    archive directory is left untouched.

    Args:
        col_path: Collection directory.
        version: Collection version to archive, e.g. ``"v3.1.1"``.
        overwrite: When ``True``, always rewrite even if the file exists.

    Returns:
        Path to the ``archive/<version>/`` directory.
    """
    col_path = Path(col_path)
    archive_dir = col_path / "archive" / version
    archive_json = archive_dir / "collection.json"

    if archive_json.exists() and not overwrite:
        return archive_dir

    archive_dir.mkdir(parents=True, exist_ok=True)
    entry = build_archive_collection(col_path, version)
    archive_json.write_text(json.dumps(entry, indent=4))
    return archive_dir


def repair_collection_archive_entry(col_path: Path | str, version: str) -> Path:
    """Overwrite ``archive/<version>/collection.json`` with a freshly built entry.

    Args:
        col_path: Collection directory.
        version: Collection version to repair, e.g. ``"v3.1.1"``.

    Returns:
        Path to the ``archive/<version>/`` directory.
    """
    return ensure_collection_archive_entry(col_path, version, overwrite=True)


def validate_collection_archive_entry(
    col_path: Path | str,
    version: str,
    releases_repo_path: Optional[Path | str] = None,
    datasets_repo_path: Optional[Path | str] = None,
) -> Issues:
    """Validate ``archive/<version>/collection.json`` for one collection version.

    Checks:

    - The archive directory and ``collection.json`` exist.
    - ``versions`` ends at the entry keyed by *version* (no later versions),
      and the top-level ``version`` equals *version*.
    - The collection ``name`` matches the directory name.
    - The version entry's ``release.version`` exists in cloud-releases (if
      *releases_repo_path* given), and the release contains this collection at
      the correct version with the matching concept DOI.
    - All datasets listed in the version entry exist in cloud-datasets (if
      *datasets_repo_path* given).

    Args:
        col_path: Collection directory.
        version: Collection version to validate, e.g. ``"v3.1.1"``.
        releases_repo_path: Root of the cloud-releases repository (optional).
        datasets_repo_path: Root of the cloud-datasets repository (optional).

    Returns:
        List of human-readable issue strings.  Empty list means clean.
    """
    col_path = Path(col_path)
    issues: Issues = []

    archive_dir = col_path / "archive" / version
    archive_json = archive_dir / "collection.json"

    if not archive_dir.exists():
        return [f"archive directory missing: {archive_dir}"]
    if not archive_json.exists():
        return [f"collection.json missing in archive: {archive_json}"]

    arch = _load_json(archive_json)
    arch_name: str = arch.get("name", col_path.name)
    arch_versions: dict = arch.get("versions", {})
    collection_doi: str = arch.get("collection_doi", "") or ""

    # ── name must match directory ─────────────────────────────────────────────
    if arch_name != col_path.name:
        issues.append(
            f"name '{arch_name}' does not match collection directory '{col_path.name}'"
        )

    # ── versions must contain exactly the target version ─────────────────────
    if version not in arch_versions:
        issues.append(
            f"version '{version}' not found in archive versions; "
            f"found: {sorted(arch_versions.keys())}"
        )
        return issues  # remaining checks would all fail

    keys = list(arch_versions)
    later = keys[keys.index(version) + 1:]
    if later:
        issues.append(
            f"archive contains versions after '{version}': {later}"
        )
    if arch.get("version") != version:
        issues.append(
            f"top-level version '{arch.get('version')}' does not match "
            f"archive directory '{version}'"
        )

    ver_entry: dict = arch_versions[version]
    ver_release: dict = ver_entry.get("release", {})
    ver_release_version: str = ver_release.get("version", "")
    ver_doi: str = ver_entry.get("doi", "") or ""
    ver_datasets: list[str] = ver_entry.get("datasets", [])

    # ── cross-reference against release.json ─────────────────────────────────
    if releases_repo_path is not None and ver_release_version:
        releases_repo_path = Path(releases_repo_path)
        release_json = releases_repo_path / ver_release_version / "release.json"

        if not release_json.exists():
            issues.append(
                f"release '{ver_release_version}' not found: {release_json}"
            )
        else:
            release = _load_json(release_json)
            rel_cols: dict[str, dict] = release.get("collections", {})

            if arch_name not in rel_cols:
                issues.append(
                    f"collection '{arch_name}' not found in release "
                    f"'{ver_release_version}' collections"
                )
            else:
                rel_entry = rel_cols[arch_name]
                rel_col_version = rel_entry.get("version", "")
                rel_col_doi = rel_entry.get("doi", "") or ""

                if rel_col_version and rel_col_version != version:
                    issues.append(
                        f"version mismatch in release '{ver_release_version}': "
                        f"release says '{rel_col_version}', archive is '{version}'"
                    )
                # Release stores concept DOI; compare against collection_doi
                if rel_col_doi and collection_doi and rel_col_doi != collection_doi:
                    issues.append(
                        f"concept DOI mismatch in release '{ver_release_version}': "
                        f"release='{rel_col_doi}', collection_doi='{collection_doi}'"
                    )

    # ── dataset membership ────────────────────────────────────────────────────
    if datasets_repo_path is not None:
        datasets_dir = Path(datasets_repo_path) / "datasets"
        for ds_name in ver_datasets:
            if not (datasets_dir / ds_name).is_dir():
                issues.append(
                    f"dataset '{ds_name}' not found in {datasets_dir}"
                )

    return issues


def validate_all_collection_archives(
    col_path: Path | str,
    releases_repo_path: Optional[Path | str] = None,
    datasets_repo_path: Optional[Path | str] = None,
) -> dict[str, Issues]:
    """Validate all archive entries for a collection.

    Checks every directory under ``archive/`` and also flags versions present
    in ``collection.json["versions"]`` that have no archive directory.

    Args:
        col_path: Collection directory.
        releases_repo_path: Root of the cloud-releases repository (optional).
        datasets_repo_path: Root of the cloud-datasets repository (optional).

    Returns:
        ``{version: [issue, ...]}`` for every version.  Clean versions map to
        ``[]``.  Missing archive directories appear with a single issue string.
    """
    col_path = Path(col_path)
    results: dict[str, Issues] = {}

    archive_root = col_path / "archive"
    if archive_root.exists():
        for version_dir in sorted(archive_root.iterdir()):
            if not version_dir.is_dir():
                continue
            ver = version_dir.name
            results[ver] = validate_collection_archive_entry(
                col_path, ver, releases_repo_path, datasets_repo_path
            )

    # Flag versions in collection.json that have no archive directory
    col_json_path = col_path / "collection.json"
    if col_json_path.exists():
        col = _load_json(col_json_path)
        for ver in col.get("versions", {}):
            if ver not in results:
                results[ver] = [f"archive directory missing for version '{ver}'"]

    return results


def ensure_all_collection_archives(
    col_path: Path | str,
    *,
    overwrite: bool = False,
) -> dict[str, Path]:
    """Ensure archive entries exist for all versions in ``collection.json``.

    Creates ``archive/<version>/collection.json`` for any version that does not
    already have one.

    Args:
        col_path: Collection directory.
        overwrite: When ``True``, recreate all archive entries.

    Returns:
        ``{version: archive_dir}`` for every version processed.
    """
    col_path = Path(col_path)

    col_json_path = col_path / "collection.json"
    if not col_json_path.exists():
        raise FileNotFoundError(f"collection.json not found: {col_json_path}")

    col = _load_json(col_json_path)
    results: dict[str, Path] = {}

    for ver in col.get("versions", {}):
        archive_dir = ensure_collection_archive_entry(col_path, ver, overwrite=overwrite)
        results[ver] = archive_dir

    return results
