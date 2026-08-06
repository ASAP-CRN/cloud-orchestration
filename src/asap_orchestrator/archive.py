"""Archive management for versioned snapshots in cloud-datasets and cloud-collections.

**Dataset archives** — ``archive/<version>/dataset.json`` snapshots represent a
dataset *at* a given version.  The key invariant: ``releases`` contains only
entries where ``dataset_version == version``.

**Collection archives** — ``archive/<version>/collection.json`` snapshots represent
a collection *at* a given version.  The key invariant: ``versions`` contains
exactly the one target version entry.

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


def _releases_for_version(
    ds_releases: dict[str, dict], version: str
) -> dict[str, dict]:
    """Filter a dataset's releases dict to entries where ``dataset_version == version``."""
    return {
        rv: rec
        for rv, rec in ds_releases.items()
        if rec.get("dataset_version", "") == version
    }


def _cde_for_version(filtered_releases: dict[str, dict], fallback: str = "") -> str:
    """Return the CDE version from the most recent release in *filtered_releases*."""
    if not filtered_releases:
        return fallback
    latest_rv = max(filtered_releases.keys())
    return filtered_releases[latest_rv].get("cde_version", fallback)


# ── public API ────────────────────────────────────────────────────────────────

def build_archive_dataset(ds_path: Path | str, version: str) -> dict:
    """Build a version-scoped ``dataset.json`` dict for an archive entry.

    Reads the current ``dataset.json`` and returns a new dict representing the
    dataset *at* *version*:

    - ``version`` is forced to *version*.
    - ``releases`` is filtered to entries where ``dataset_version == version``.
    - ``all_releases`` is derived from the filtered releases.
    - ``cde_version`` is taken from the most recent filtered release.
    - ``all_versions`` is set to ``[version]`` (single-version snapshot).

    All other fields (name, doi, creators, buckets, etc.) are carried over
    unchanged from the current ``dataset.json``.

    Args:
        ds_path: Dataset directory containing ``dataset.json``.
        version: The dataset version this archive entry represents, e.g. ``"v1.0"``.

    Returns:
        Dict ready to write as ``archive/<version>/dataset.json``.
    """
    ds_path = Path(ds_path)
    ds = _load_json(ds_path / "dataset.json")

    filtered = _releases_for_version(ds.get("releases", {}), version)
    cde = _cde_for_version(filtered, fallback=ds.get("cde_version", "") or "")

    # Build the archive entry from the current dataset, overriding version-specific fields
    entry = {k: v for k, v in ds.items()}
    entry["version"] = version
    entry["cde_version"] = cde
    entry["releases"] = filtered
    entry["all_releases"] = sorted(filtered.keys())
    entry["all_versions"] = [version]

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
    - Every ``releases`` entry has ``dataset_version == version``.
    - ``all_releases`` matches ``releases.keys()``.
    - ``all_versions``, if present, equals ``[version]``.
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
    arch_releases: dict = arch.get("releases", {})
    arch_all_releases: list = arch.get("all_releases", [])
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

    # ── releases must all be for this version ─────────────────────────────────
    wrong = {
        rv: rec.get("dataset_version", "")
        for rv, rec in arch_releases.items()
        if rec.get("dataset_version", "") not in (version, arch_version)
    }
    if wrong:
        issues.append(
            f"releases contain entries for wrong dataset versions: "
            + ", ".join(f"'{rv}' (dataset_version='{dv}')" for rv, dv in wrong.items())
        )

    # ── all_releases must match releases.keys() ───────────────────────────────
    if sorted(arch_all_releases) != sorted(arch_releases.keys()):
        issues.append(
            f"all_releases {sorted(arch_all_releases)} does not match "
            f"releases.keys() {sorted(arch_releases.keys())}"
        )

    # ── all_versions, if present, should be a single-entry snapshot ──────────
    if arch_all_versions is not None:
        expected = [version] if version.startswith("v") else [f"v{version}"]
        if arch_all_versions not in ([version], [arch_version], expected):
            issues.append(
                f"all_versions should be ['{version}'] for an archive snapshot, "
                f"got {arch_all_versions}"
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
                e["name"]: e.get("version") or e.get("dataset_version", "")
                for e in release.get("datasets", [])
            }
            if ds_name not in found:
                issues.append(
                    f"dataset '{ds_name}' not found in release '{rv}' datasets"
                )
            else:
                rel_version = found[ds_name]
                if rel_version and rel_version not in (version, arch_version):
                    issues.append(
                        f"version mismatch in release '{rv}': "
                        f"release says '{rel_version}', archive is '{version}'"
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
    top-level metadata (``name``, ``title``, ``collection_doi``, ``types``) but
    with ``versions`` containing **only** the single entry for *version*.

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

    entry = {k: v for k, v in col.items() if k != "versions"}
    entry["versions"] = {version: versions[version]}
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
    archive_json.write_text(json.dumps(entry, indent=2))
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
    - ``versions`` contains exactly the one entry keyed by *version*.
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

    extra = [v for v in arch_versions if v != version]
    if extra:
        issues.append(
            f"archive contains extra versions (expected only '{version}'): {extra}"
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
            rel_cols = release.get("collections", {})
            if isinstance(rel_cols, list):
                rel_cols = {c.get("name", ""): c for c in rel_cols}

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
