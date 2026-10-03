"""Cross-repository consistency validation for ASAP CRN Cloud artifacts.

Checks that dataset.json, release.json, and collection.json entries agree on
names, DOIs, and dataset versions.  All functions return plain lists of
human-readable issue strings so they can be used interactively in notebooks
or integrated into CI scripts.

Usage::

    import asap_orchestrator as ao

    # Validate one dataset against all releases it claims to be in
    issues = ao.check_dataset_consistency(
        ds_path=datasets_repo / "datasets" / "jakobsson-pmdbs-sn-rnaseq",
        releases_repo_path=releases_repo,
        collections_repo_path=collections_repo,
    )
    for issue in issues:
        print(issue)

    # Validate an entire release
    report = ao.check_release_consistency(
        release_path=releases_repo / "v4.1.1",
        datasets_repo_path=datasets_repo,
        collections_repo_path=collections_repo,
    )
    for section, issues in report.items():
        for issue in issues:
            print(f"[{section}] {issue}")

    # Scan every dataset
    report = ao.check_all_datasets(datasets_repo, releases_repo, collections_repo)
    for ds_name, issues in report.items():
        print(ds_name, issues)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

Issues = list[str]


# ── internal helpers ──────────────────────────────────────────────────────────

def _vn(v: str) -> str:
    """Normalise a version string to always have a leading 'v'."""
    return v if v.startswith("v") else f"v{v}"


def _load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _release_datasets(release: dict) -> dict[str, dict]:
    """Return ``{name: {"doi", "version"}}`` from a raw release dict."""
    return {
        name: {
            "doi": entry.get("doi") or "",
            "version": entry.get("dataset_version", ""),
        }
        for name, entry in release.get("datasets", {}).items()
    }


# ── public API ────────────────────────────────────────────────────────────────

def check_dataset_consistency(
    ds_path: Path | str,
    releases_repo_path: Path | str,
    collections_repo_path: Optional[Path | str] = None,
) -> Issues:
    """Validate ``dataset.json`` against every release it claims to be in.

    Checks:

    - For each ``release_version`` in ``dataset.releases``: the release exists,
      the dataset appears in it, and versions/DOIs agree.
    - ``all_versions`` matches the unique dataset versions in ``releases``.
    - Current ``version`` appears in ``all_versions``.
    - If *collections_repo_path* given and ``dataset.collection`` is set:
      the dataset appears in some version of that collection.

    Args:
        ds_path: Dataset directory containing ``dataset.json``.
        releases_repo_path: Root of the cloud-releases repository.
        collections_repo_path: Root of the cloud-collections repository (optional).

    Returns:
        List of human-readable issue strings.  Empty list means clean.
    """
    ds_path = Path(ds_path)
    releases_repo_path = Path(releases_repo_path)
    issues: Issues = []

    ds_json_path = ds_path / "dataset.json"
    if not ds_json_path.exists():
        return [f"dataset.json not found: {ds_json_path}"]

    ds = _load_json(ds_json_path)
    ds_name: str = ds.get("name", ds_path.name)
    ds_version: str = ds.get("version", "")
    ds_doi: str = ds.get("doi", "") or ""
    ds_releases: dict[str, str] = ds.get("releases", {})
    ds_all_versions: list[str] = ds.get("all_versions", [])
    ds_collection: str | None = ds.get("collection")

    # ── all_versions consistency ──────────────────────────────────────────────
    versions_in_releases = sorted({v for v in ds_releases.values() if v})
    if ds_all_versions and sorted(_vn(v) for v in ds_all_versions) != [_vn(v) for v in versions_in_releases]:
        issues.append(
            f"all_versions out of sync: has {sorted(ds_all_versions)}, "
            f"unique dataset_versions in releases={versions_in_releases}"
        )

    if ds_version and ds_all_versions and _vn(ds_version) not in [_vn(v) for v in ds_all_versions]:
        issues.append(
            f"current version '{ds_version}' not listed in all_versions={ds_all_versions}"
        )

    # ── per-release checks ────────────────────────────────────────────────────
    for rel_version, recorded_ds_version in ds_releases.items():

        release_json = releases_repo_path / rel_version / "release.json"
        if not release_json.exists():
            issues.append(f"release '{rel_version}' not found: {release_json}")
            continue

        release = _load_json(release_json)
        rel_datasets = _release_datasets(release)

        if ds_name not in rel_datasets:
            issues.append(
                f"dataset not found in release '{rel_version}' datasets list"
            )
            continue

        rel_entry = rel_datasets[ds_name]
        rel_ds_version = rel_entry["version"]
        rel_doi = rel_entry["doi"]

        if recorded_ds_version and rel_ds_version and recorded_ds_version != rel_ds_version:
            issues.append(
                f"version mismatch in release '{rel_version}': "
                f"dataset.releases says '{recorded_ds_version}', "
                f"release.json says '{rel_ds_version}'"
            )

        if ds_doi and rel_doi and ds_doi != rel_doi:
            issues.append(
                f"DOI mismatch in release '{rel_version}': "
                f"dataset.doi='{ds_doi}', release.json='{rel_doi}'"
            )

    # ── collection check ──────────────────────────────────────────────────────
    if ds_collection and collections_repo_path is not None:
        col_json_path = Path(collections_repo_path) / ds_collection / "collection.json"
        if not col_json_path.exists():
            issues.append(
                f"collection '{ds_collection}' not found: {col_json_path}"
            )
        else:
            col = _load_json(col_json_path)
            containing = [
                ver for ver, entry in col.get("versions", {}).items()
                if ds_name in entry.get("datasets", [])
            ]
            if not containing:
                issues.append(
                    f"dataset not found in any version of "
                    f"collection '{ds_collection}'"
                )

    return issues


def check_release_consistency(
    release_path: Path | str,
    datasets_repo_path: Path | str,
    collections_repo_path: Optional[Path | str] = None,
) -> dict[str, Issues]:
    """Validate all entries in a ``release.json``.

    Checks each dataset entry against the corresponding ``dataset.json`` and,
    when *collections_repo_path* is given, each collection entry against
    ``collection.json``.

    Args:
        release_path: Release directory containing ``release.json``.
        datasets_repo_path: Root of the cloud-datasets repository.
        collections_repo_path: Root of the cloud-collections repository (optional).

    Returns:
        ``{"datasets": [...], "collections": [...]}`` where each list contains
        human-readable issue strings.
    """
    release_path = Path(release_path)
    datasets_repo_path = Path(datasets_repo_path)
    result: dict[str, Issues] = {"datasets": [], "collections": []}

    release_json_path = release_path / "release.json"
    if not release_json_path.exists():
        result["datasets"].append(f"release.json not found: {release_json_path}")
        return result

    release = _load_json(release_json_path)
    release_version: str = release.get("release_version", release_path.name)
    rel_datasets = _release_datasets(release)
    rel_new_datasets: list[str] = release.get("new_datasets", [])
    rel_collections: dict[str, dict] = release.get("collections", {})

    # ── new_datasets must be a subset of datasets ─────────────────────────────
    for ds_name in rel_new_datasets:
        if ds_name not in rel_datasets:
            result["datasets"].append(
                f"[{ds_name}] appears in new_datasets but not in datasets"
            )

    # ── per-dataset checks ────────────────────────────────────────────────────
    for ds_name, rel_entry in rel_datasets.items():
        rel_version = rel_entry["version"]
        rel_doi = rel_entry["doi"]

        ds_json_path = datasets_repo_path / "datasets" / ds_name / "dataset.json"
        if not ds_json_path.exists():
            result["datasets"].append(
                f"[{ds_name}] dataset.json not found: {ds_json_path}"
            )
            continue

        ds = _load_json(ds_json_path)
        ds_version: str = ds.get("version", "")
        ds_doi: str = ds.get("doi", "") or ""
        ds_releases: dict[str, str] = ds.get("releases", {})
        all_releases = list(ds_releases)

        # DOI must match concept DOI in dataset.json
        if rel_doi and ds_doi and rel_doi != ds_doi:
            result["datasets"].append(
                f"[{ds_name}] DOI mismatch: "
                f"release='{rel_doi}', dataset.json='{ds_doi}'"
            )

        # A new/updated dataset must record this release; carried-over datasets don't
        if release_version not in ds_releases:
            if ds_name in rel_new_datasets:
                result["datasets"].append(
                    f"[{ds_name}] release '{release_version}' not recorded "
                    f"in dataset.json releases"
                )
        else:
            recorded_version = ds_releases[release_version]
            if rel_version and recorded_version and rel_version != recorded_version:
                result["datasets"].append(
                    f"[{ds_name}] version mismatch in releases['{release_version}']: "
                    f"dataset.releases records '{recorded_version}', "
                    f"release.json has '{rel_version}'"
                )

        # If this is the most recent release for the dataset, versions should match
        if all_releases and release_version == max(all_releases):
            if rel_version and ds_version and rel_version != ds_version:
                result["datasets"].append(
                    f"[{ds_name}] latest release version mismatch: "
                    f"release says '{rel_version}', "
                    f"current dataset.json version='{ds_version}'"
                )

    # ── per-collection checks ─────────────────────────────────────────────────
    if collections_repo_path is not None:
        collections_repo_path = Path(collections_repo_path)
        for col_name, col_entry in rel_collections.items():
            col_version = col_entry.get("version", "")
            col_doi = col_entry.get("doi", "") or ""

            col_json_path = collections_repo_path / col_name / "collection.json"
            if not col_json_path.exists():
                result["collections"].append(
                    f"[{col_name}] collection.json not found: {col_json_path}"
                )
                continue

            col = _load_json(col_json_path)
            col_versions: dict = col.get("versions", {})

            if col_version and col_version not in col_versions:
                result["collections"].append(
                    f"[{col_name}] version '{col_version}' not in collection.json"
                )
                continue

            if col_version:
                col_ver_entry = col_versions[col_version]
                # Collection version's release.version must match
                col_rel_version = col_ver_entry.get("release", {}).get("version", "")
                if col_rel_version and col_rel_version != release_version:
                    result["collections"].append(
                        f"[{col_name}] version '{col_version}' has "
                        f"release.version='{col_rel_version}', "
                        f"expected '{release_version}'"
                    )
                # DOI check
                col_ver_doi = col_ver_entry.get("doi", "") or ""
                if col_doi and col_ver_doi and col_doi != col_ver_doi:
                    result["collections"].append(
                        f"[{col_name}] DOI mismatch for version '{col_version}': "
                        f"release='{col_doi}', collection.json='{col_ver_doi}'"
                    )

    return result


def check_collection_consistency(
    col_path: Path | str,
    releases_repo_path: Path | str,
    datasets_repo_path: Optional[Path | str] = None,
) -> Issues:
    """Validate ``collection.json`` against every release it claims to belong to.

    Checks:

    - For each version entry: its ``release.version`` exists in cloud-releases,
      the release contains this collection at that version, and the release's
      collection DOI matches ``collection_doi``.
    - Dataset membership only grows (no datasets removed between versions).
    - If *datasets_repo_path* given: all datasets in every version exist.

    Args:
        col_path: Collection directory containing ``collection.json``.
        releases_repo_path: Root of the cloud-releases repository.
        datasets_repo_path: Root of the cloud-datasets repository (optional).

    Returns:
        List of human-readable issue strings.  Empty list means clean.
    """
    col_path = Path(col_path)
    releases_repo_path = Path(releases_repo_path)
    issues: Issues = []

    col_json_path = col_path / "collection.json"
    if not col_json_path.exists():
        return [f"collection.json not found: {col_json_path}"]

    col = _load_json(col_json_path)
    col_name: str = col.get("name", col_path.name)
    collection_doi: str = col.get("collection_doi", "") or ""
    col_versions: dict[str, dict] = col.get("versions", {})

    prev_datasets: set[str] = set()

    for ver, ver_entry in col_versions.items():
        ver_release: dict = ver_entry.get("release", {})
        ver_release_version: str = ver_release.get("version", "")
        ver_doi: str = ver_entry.get("doi", "") or ""
        ver_datasets: list[str] = ver_entry.get("datasets", [])
        ver_datasets_set = set(ver_datasets)

        # ── release must exist and contain this collection ────────────────────
        if ver_release_version:
            release_json = releases_repo_path / ver_release_version / "release.json"
            if not release_json.exists():
                issues.append(
                    f"[{ver}] release '{ver_release_version}' not found: {release_json}"
                )
            else:
                release = _load_json(release_json)
                rel_cols: dict[str, dict] = release.get("collections", {})

                if col_name not in rel_cols:
                    issues.append(
                        f"[{ver}] collection not found in release "
                        f"'{ver_release_version}' collections"
                    )
                else:
                    rel_entry = rel_cols[col_name]
                    rel_col_version = rel_entry.get("version", "")
                    rel_col_doi = rel_entry.get("doi", "") or ""

                    if rel_col_version and rel_col_version != ver:
                        issues.append(
                            f"[{ver}] version mismatch in release "
                            f"'{ver_release_version}': release says '{rel_col_version}'"
                        )
                    # Release should store concept DOI, not version DOI
                    if rel_col_doi and collection_doi and rel_col_doi != collection_doi:
                        issues.append(
                            f"[{ver}] concept DOI mismatch in release "
                            f"'{ver_release_version}': "
                            f"release='{rel_col_doi}', collection_doi='{collection_doi}'"
                        )

        # ── dataset membership must be monotonically growing ─────────────────
        if prev_datasets and not prev_datasets.issubset(ver_datasets_set):
            removed = prev_datasets - ver_datasets_set
            issues.append(
                f"[{ver}] datasets were removed relative to the previous version: "
                f"{sorted(removed)}"
            )
        prev_datasets = ver_datasets_set

        # ── all listed datasets must exist ────────────────────────────────────
        if datasets_repo_path is not None:
            datasets_dir = Path(datasets_repo_path) / "datasets"
            for ds_name in ver_datasets:
                if not (datasets_dir / ds_name).is_dir():
                    issues.append(
                        f"[{ver}] dataset '{ds_name}' not found in {datasets_dir}"
                    )

    return issues


def check_all_collections(
    collections_repo_path: Path | str,
    releases_repo_path: Path | str,
    datasets_repo_path: Optional[Path | str] = None,
    *,
    verbose: bool = False,
) -> dict[str, Issues]:
    """Run :func:`check_collection_consistency` over every collection.

    Args:
        collections_repo_path: Root of the cloud-collections repository.
        releases_repo_path: Root of the cloud-releases repository.
        datasets_repo_path: Root of the cloud-datasets repository (optional).
        verbose: When ``True``, include collections with no issues.

    Returns:
        ``{collection_name: [issue, ...]}`` for collections that have issues.
    """
    collections_repo_path = Path(collections_repo_path)
    results: dict[str, Issues] = {}

    for col_dir in sorted(collections_repo_path.iterdir()):
        if not col_dir.is_dir() or not (col_dir / "collection.json").exists():
            continue
        issues = check_collection_consistency(col_dir, releases_repo_path, datasets_repo_path)
        if issues or verbose:
            results[col_dir.name] = issues

    return results


def check_all_datasets(
    datasets_repo_path: Path | str,
    releases_repo_path: Path | str,
    collections_repo_path: Optional[Path | str] = None,
    *,
    verbose: bool = False,
) -> dict[str, Issues]:
    """Run :func:`check_dataset_consistency` over every dataset in cloud-datasets.

    Args:
        datasets_repo_path: Root of the cloud-datasets repository.
        releases_repo_path: Root of the cloud-releases repository.
        collections_repo_path: Root of the cloud-collections repository (optional).
        verbose: When ``True``, include datasets with no issues in the output.

    Returns:
        ``{dataset_name: [issue, ...]}`` for datasets that have issues.
        Datasets with no issues are omitted unless *verbose* is ``True``.
    """
    datasets_repo_path = Path(datasets_repo_path)
    results: dict[str, Issues] = {}

    datasets_dir = datasets_repo_path / "datasets"
    if not datasets_dir.exists():
        return {"_error": [f"datasets directory not found: {datasets_dir}"]}

    for ds_dir in sorted(datasets_dir.iterdir()):
        if not ds_dir.is_dir():
            continue
        issues = check_dataset_consistency(
            ds_dir, releases_repo_path, collections_repo_path
        )
        if issues or verbose:
            results[ds_dir.name] = issues

    return results
