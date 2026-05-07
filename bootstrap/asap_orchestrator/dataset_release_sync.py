"""Sync dataset.json release history from cloud-releases release.json files.

For each dataset that appears in one or more releases:
- Ensures the dataset.json `releases` dict has an entry for every release version it participated in.
- Replaces the `date` field with `dataset_version` (the dataset's version string from the release).
- Updates the top-level `version` field to match the most recent release the dataset appears in.
"""

import json
from pathlib import Path

RELEASES_BASE = Path(__file__).parents[3] / "cloud-releases" / "releases"
DATASETS_BASE = Path(__file__).parents[3] / "cloud-datasets" / "datasets"

RELEASE_ORDER = [
    "v1.0.0", "v2.0.0", "v2.0.1", "v2.0.2", "v2.0.3",
    "v3.0.0", "v3.0.1", "v3.0.2", "v4.0.0",
]


def _build_release_index() -> tuple[dict, dict]:
    """Return (dataset_map, cde_map).

    dataset_map: {dataset_name: {release_version: dataset_version_str}}
    cde_map:     {release_version: cde_version_str}
    """
    dataset_map: dict[str, dict[str, str]] = {}
    cde_map: dict[str, str] = {}

    for rv in RELEASE_ORDER:
        rj = RELEASES_BASE / rv / "release.json"
        if not rj.exists():
            continue
        data = json.loads(rj.read_text())
        cde_map[rv] = data.get("cde_version", "")
        for entry in data.get("datasets", []):
            name = entry.get("name")
            ver = entry.get("version")
            if name and ver:
                dataset_map.setdefault(name, {})[rv] = ver

    return dataset_map, cde_map


def sync_dataset(dataset_name: str, dataset_map: dict, cde_map: dict,
                 dry_run: bool = False) -> dict:
    """Sync one dataset.json against the release index."""
    dj_path = DATASETS_BASE / dataset_name / "dataset.json"
    if not dj_path.exists():
        return {"dataset": dataset_name, "error": "dataset.json not found"}

    release_versions = dataset_map.get(dataset_name)
    if not release_versions:
        return {"dataset": dataset_name, "skipped": True, "reason": "not in any release"}

    data = json.loads(dj_path.read_text())
    releases = data.get("releases", {})
    changes: list[str] = []

    # Process releases in chronological order so the final `version` is the latest
    latest_dataset_version = None
    for rv in RELEASE_ORDER:
        if rv not in release_versions:
            continue
        dataset_version = release_versions[rv]
        latest_dataset_version = dataset_version

        if rv not in releases:
            # Add a missing release entry
            releases[rv] = {
                "cde_version": cde_map.get(rv, ""),
                "dataset_version": dataset_version,
            }
            changes.append(f"added releases[{rv}] dataset_version={dataset_version}")
        else:
            entry = dict(releases[rv])
            # Replace `date` with `dataset_version`
            if "date" in entry:
                del entry["date"]
                entry["dataset_version"] = dataset_version
                releases[rv] = entry
                changes.append(f"releases[{rv}]: date → dataset_version={dataset_version}")
            elif entry.get("dataset_version") != dataset_version:
                entry["dataset_version"] = dataset_version
                releases[rv] = entry
                changes.append(f"releases[{rv}]: updated dataset_version={dataset_version}")

    # Rebuild releases in chronological order
    data["releases"] = {rv: releases[rv] for rv in RELEASE_ORDER if rv in releases}

    # Update top-level version
    if latest_dataset_version and data.get("version") != latest_dataset_version:
        changes.append(f"version: {data.get('version')} → {latest_dataset_version}")
        data["version"] = latest_dataset_version

    summary = {"dataset": dataset_name, "changes": changes, "skipped": False}

    if not dry_run and changes:
        dj_path.write_text(json.dumps(data, indent=2) + "\n")

    return summary


def sync_all_datasets(dry_run: bool = False) -> list[dict]:
    """Sync release history for all datasets in cloud-datasets."""
    dataset_map, cde_map = _build_release_index()
    results = []
    for ds_dir in sorted(DATASETS_BASE.iterdir()):
        if not ds_dir.is_dir() or not (ds_dir / "dataset.json").exists():
            continue
        results.append(sync_dataset(ds_dir.name, dataset_map, cde_map, dry_run=dry_run))
    return results
