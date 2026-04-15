"""Archive current dataset version: copy DOI/, refs/, and dataset.json into archive/<version>/."""

import json
import shutil
from pathlib import Path
from typing import Optional

DATASETS_BASE = Path(__file__).parents[3] / "cloud-datasets" / "datasets"


def _copy_dir(src: Path, dst: Path) -> int:
    """Copy all files from src into dst (non-recursively for top-level files, preserving subdirs).
    Returns number of files copied. Skips if src doesn't exist or is empty."""
    if not src.exists():
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
            count += sum(1 for _ in target.rglob("*") if _.is_file())
        else:
            shutil.copy2(item, target)
            count += 1
    return count


def archive_dataset(dataset_name: str, dry_run: bool = False) -> dict:
    """Create archive/<version>/ for the current dataset version.

    Copies DOI/, refs/, and dataset.json into archive/<version>/.
    Skips if the archive folder already has real content (beyond .gitkeep).
    """
    ds_dir = DATASETS_BASE / dataset_name
    dj_path = ds_dir / "dataset.json"
    if not dj_path.exists():
        return {"dataset": dataset_name, "error": "dataset.json not found"}

    data = json.loads(dj_path.read_text())
    version = data.get("version")
    if not version:
        return {"dataset": dataset_name, "error": "no version field in dataset.json"}

    archive_dir = ds_dir / "archive" / version

    # Skip if already populated (has files other than .gitkeep)
    if archive_dir.exists():
        real_files = [f for f in archive_dir.rglob("*") if f.is_file() and f.name != ".gitkeep"]
        if real_files:
            return {"dataset": dataset_name, "version": version, "skipped": True,
                    "reason": f"archive/{version}/ already has {len(real_files)} file(s)"}

    summary = {"dataset": dataset_name, "version": version, "skipped": False, "files_copied": 0}

    if not dry_run:
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Copy dataset.json
        shutil.copy2(dj_path, archive_dir / "dataset.json")
        summary["files_copied"] += 1

        # Copy DOI/
        doi_copied = _copy_dir(ds_dir / "DOI", archive_dir / "DOI")
        summary["files_copied"] += doi_copied

        # Copy refs/
        refs_copied = _copy_dir(ds_dir / "refs", archive_dir / "refs")
        summary["files_copied"] += refs_copied
    else:
        # Count what would be copied
        summary["files_copied"] = 1  # dataset.json
        for sub in ("DOI", "refs"):
            src = ds_dir / sub
            if src.exists():
                summary["files_copied"] += sum(1 for f in src.rglob("*") if f.is_file())

    return summary


def archive_all_datasets(dry_run: bool = False) -> list[dict]:
    """Archive all datasets in cloud-datasets/datasets/."""
    results = []
    for ds_dir in sorted(DATASETS_BASE.iterdir()):
        if not ds_dir.is_dir() or not (ds_dir / "dataset.json").exists():
            continue
        results.append(archive_dataset(ds_dir.name, dry_run=dry_run))
    return results
