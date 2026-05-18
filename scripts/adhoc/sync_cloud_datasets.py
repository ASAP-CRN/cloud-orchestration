#!/usr/bin/env python3
"""
Validate and repair the cloud-datasets repo:

  1. Ensure each dataset's version file matches dataset.json (version file is truth;
     if missing, create it from dataset.json).
  2. Ensure each dataset's archive/ directory contains a snapshot for every unique
     dataset_version referenced in its releases, plus the current version.
  3. Rebuild the root datasets.json from all individual dataset.json files.

Usage:
  python3 scripts/sync_cloud_datasets.py [--cloud-datasets PATH] [--dry-run]
"""

import argparse
import json
import os
import shutil
from pathlib import Path


def norm(v: str) -> str:
    """Strip leading 'v' and whitespace for comparison."""
    return v.strip().lstrip("v")


def with_v(v: str) -> str:
    """Ensure version string has a 'v' prefix."""
    v = v.strip()
    return v if v.startswith("v") else f"v{v}"


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def write_json(path: Path, data: dict, dry_run: bool) -> None:
    if dry_run:
        return
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
        f.write("\n")


def archive_dirs(ds_dir: Path) -> set:
    arch = ds_dir / "archive"
    if not arch.is_dir():
        return set()
    return {
        d.name
        for d in arch.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    }


def main():
    parser = argparse.ArgumentParser(description="Sync cloud-datasets repo state")
    parser.add_argument(
        "--cloud-datasets",
        default="/home/ergonyc/Projects/ASAP/cloud-datasets",
        help="Path to cloud-datasets repo root",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without writing anything",
    )
    args = parser.parse_args()
    dry_run = args.dry_run

    cloud_root = Path(args.cloud_datasets)
    datasets_root = cloud_root / "datasets"
    root_json_path = cloud_root / "datasets.json"

    if dry_run:
        print("[DRY RUN — no files will be written]\n")

    dataset_dirs = sorted(
        d
        for d in datasets_root.iterdir()
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
    )
    print(f"Processing {len(dataset_dirs)} datasets in {datasets_root}\n")

    warnings = []
    changes = []
    root_datasets = {}

    for ds_dir in dataset_dirs:
        name = ds_dir.name
        dj_path = ds_dir / "dataset.json"
        vf_path = ds_dir / "version"
        arch_dir = ds_dir / "archive"

        if not dj_path.exists():
            warnings.append(f"{name}: missing dataset.json — skipped")
            continue

        dj = load_json(dj_path)
        dj_version = dj.get("version", "")

        # ── Task 1: Sync version file ↔ dataset.json ─────────────────────────────

        if not vf_path.exists() or vf_path.read_text().strip() == "":
            # No version file — create from dataset.json
            vf_content = norm(dj_version)
            print(f"  [{name}] create version file: {vf_content}")
            changes.append(f"{name}: created version file → {vf_content}")
            if not dry_run:
                vf_path.write_text(vf_content + "\n")
            current_version = vf_content
        else:
            vf_content = vf_path.read_text().strip()
            current_version = norm(vf_content)
            if norm(dj_version) != current_version:
                new_dj_version = with_v(vf_content)
                print(
                    f"  [{name}] version mismatch — "
                    f"version_file={vf_content!r}, dataset.json={dj_version!r} "
                    f"→ updating dataset.json to {new_dj_version}"
                )
                changes.append(
                    f"{name}: dataset.json version {dj_version} → {new_dj_version}"
                )
                dj["version"] = new_dj_version
                dj_version = new_dj_version
                write_json(dj_path, dj, dry_run)

        # ── Task 2: Ensure archive is complete ───────────────────────────────────

        releases = dj.get("releases", {})

        # Collect unique dataset_versions referenced in releases
        release_dataset_versions: dict[str, list[str]] = {}  # norm_ver → [release_keys]
        for rel_key, rel_data in releases.items():
            dv = rel_data.get("dataset_version", "")
            if not dv:
                continue
            nv = norm(dv)
            release_dataset_versions.setdefault(nv, []).append(rel_key)

        # Always include the current version
        release_dataset_versions.setdefault(current_version, []).append("current")

        existing = archive_dirs(ds_dir)
        arch_dir.mkdir(exist_ok=True)

        for nv, refs in sorted(release_dataset_versions.items()):
            dir_name = with_v(nv)
            if dir_name in existing:
                continue

            # Flag dataset_versions that look inconsistent with version_file
            # (i.e. not related to the current version lineage and != current_version)
            if nv != current_version:
                # Heuristic: if the version has a higher major than the current version
                # and the current version is a simple increment, it's likely a data error
                # (e.g., dataset_version="3.1.1" in v4.1.0 for a dataset at version "1.1")
                cur_parts = [int(x) for x in current_version.split(".") if x.isdigit()]
                nv_parts = [int(x) for x in nv.split(".") if x.isdigit()]
                if nv_parts and cur_parts and nv_parts[0] > cur_parts[0]:
                    warnings.append(
                        f"{name}: release(s) {refs} reference dataset_version={dv!r} "
                        f"but version_file={vf_content!r} — looks like a CDE version "
                        f"mis-filed as dataset_version; skipping archive/{dir_name}/"
                    )
                    continue

            print(f"  [{name}] create archive/{dir_name}/dataset.json")
            changes.append(f"{name}: created archive/{dir_name}/")

            if not dry_run:
                archive_version_dir = arch_dir / dir_name
                archive_version_dir.mkdir(exist_ok=True)
                # Snapshot dataset.json with the archive version set correctly
                snap = dict(dj)
                snap["version"] = dir_name
                write_json(archive_version_dir / "dataset.json", snap, dry_run=False)

        # ── Collect entry for root datasets.json ─────────────────────────────────

        root_datasets[name] = {
            "name": dj.get("name", name),
            "title": dj.get("title", ""),
            "version": dj_version,
            "doi": dj.get("doi"),
            "release": releases,
        }

    # ── Task 3: Rebuild root datasets.json ───────────────────────────────────────

    print(f"\nRebuilding {root_json_path} ({len(root_datasets)} datasets)")
    changes.append(f"datasets.json rebuilt with {len(root_datasets)} entries")
    write_json(root_json_path, root_datasets, dry_run)

    # ── Summary ──────────────────────────────────────────────────────────────────

    print("\n── Changes ──────────────────────────────────────────────────────────")
    for c in changes:
        print(f"  {c}")

    if warnings:
        print("\n── Warnings ─────────────────────────────────────────────────────────")
        for w in warnings:
            print(f"  [WARN] {w}")

    print(f"\nTotal changes: {len(changes)}  Warnings: {len(warnings)}")


if __name__ == "__main__":
    main()
