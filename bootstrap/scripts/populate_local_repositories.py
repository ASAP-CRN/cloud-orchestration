"""Populate local cloud-datasets and cloud-collections repos from processed references.

Reads the pre-built reference files in references/ and writes dataset.json / collection.json files
plus stub subdirectory structures directly to the local repo checkouts — no GitHub
API calls or tokens required.

Also syncs source files from asap-crn-cloud-dataset-metadata into cloud-datasets:
  DOI/, refs/, scripts/ are copied from the source repo per dataset.

Folder structure created / populated:
  cloud-datasets/
    datasets/<name>/dataset.json
    datasets/<name>/DOI/          ← copied from asap-crn-cloud-dataset-metadata
    datasets/<name>/refs/         ← copied from asap-crn-cloud-dataset-metadata
    datasets/<name>/scripts/      ← copied from asap-crn-cloud-dataset-metadata
    datasets/<name>/archive/      ← stub only (no source archive/ per dataset)
  cloud-collections/
    collections/<name>/collection.json
    collections/<name>/scripts/
    collections/<name>/archive/

References schema
-----------------
datasets_references.json:
  { "<dataset_name>": { "name", "title", "versions": { "<ver>": { ... } } } }

collections_references.json:
  { "<collection_name>": { "name", "title", "versions": { "<ver>": { ... } } } }

The *latest* version entry (highest sort key) is used for dataset.json / collection.json.
"""

import json
import shutil
import sys
from pathlib import Path


# ── Path resolution ────────────────────────────────────────────────────────────

ROOT      = Path(__file__).resolve().parents[2]   # parent of all repos
REF_DIR   = ROOT / "cloud-orchestration" / "references"
DS_REPO   = ROOT / "cloud-datasets"
COL_REPO  = ROOT / "cloud-collections"
DS_META   = ROOT / "asap-crn-cloud-dataset-metadata" / "datasets"

DATASETS_REF    = REF_DIR / "datasets_references.json"
COLLECTIONS_REF = REF_DIR / "collections_references.json"

# Subdirectories to sync from the source dataset metadata repo
SYNC_SUBDIRS = ["DOI", "refs", "scripts"]


# ── Helpers ────────────────────────────────────────────────────────────────────

def latest_version(versions: dict) -> dict:
    """Return the value for the highest-sorted version key."""
    return versions[sorted(versions)[-1]]


def stub_dirs(base: Path, subdirs: list[str]) -> None:
    """Create empty stub subdirectories (with a .gitkeep) under base."""
    for name in subdirs:
        d = base / name
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.touch()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def copy_subdir(src: Path, dst: Path) -> int:
    """Copy all files from src into dst, removing any .gitkeep stub first.
    Returns the number of files copied."""
    if not src.exists():
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    # Remove stub placeholder if present
    stub = dst / ".gitkeep"
    if stub.exists():
        stub.unlink()
    count = 0
    for item in src.iterdir():
        target = dst / item.name
        if item.is_file():
            shutil.copy2(item, target)
            count += 1
        elif item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
            count += 1
    return count


# ── Dataset population ─────────────────────────────────────────────────────────

def populate_datasets(dataset_filter: str | None = None) -> int:
    with open(DATASETS_REF) as f:
        datasets: dict = json.load(f)

    if dataset_filter:
        datasets = {k: v for k, v in datasets.items() if k == dataset_filter}

    created = 0
    for name, info in sorted(datasets.items()):
        ver_info = latest_version(info["versions"])
        base = DS_REPO / "datasets" / name

        # Aggregate releases across ALL dataset versions (not just the latest),
        # so the full release history is captured in dataset.json.
        all_releases: dict = {}
        for vinfo in info["versions"].values():
            all_releases.update(vinfo.get("releases", {}))

        metadata = {
            "name":        name,
            "title":       info["title"],
            "description": ver_info.get("description", ""),
            "version":     ver_info["version"],
            "doi":         ver_info.get("doi"),
            "creators":    ver_info.get("creators", []),
            "keywords":    ver_info.get("keywords", []),
            "license":     ver_info.get("license", "CC-BY-4.0"),
            "references":  ver_info.get("references", []),
            "collection":  ver_info.get("collection"),
            "buckets":     ver_info.get("buckets", {}),
            "cde_version": ver_info.get("cde_version"),
            "releases":    all_releases,
        }

        write_json(base / "dataset.json", metadata)
        stub_dirs(base, ["DOI", "refs", "scripts", "archive"])
        print(f"  dataset: {name}  (version {ver_info['version']})")
        created += 1

    return created


# ── Collection population ──────────────────────────────────────────────────────

def populate_collections(collection_filter: str | None = None) -> int:
    with open(COLLECTIONS_REF) as f:
        collections: dict = json.load(f)

    if collection_filter:
        collections = {k: v for k, v in collections.items() if k == collection_filter}

    created = 0
    for name, info in sorted(collections.items()):
        base = COL_REPO / "collections" / name

        # Collect all types across all versions for the top-level field
        all_types: list = []
        for vinfo in info["versions"].values():
            for t in vinfo.get("types", []):
                if t not in all_types:
                    all_types.append(t)

        metadata = {
            "name":     name,
            "title":    info["title"],
            "types":    sorted(all_types),
            "versions": info["versions"],
        }

        write_json(base / "collection.json", metadata)
        stub_dirs(base, ["scripts", "archive"])
        latest = sorted(info["versions"])[-1]
        print(f"  collection: {name}  ({len(info['versions'])} version(s), latest {latest})")
        created += 1

    return created


# ── datasets.json / collections.json index ─────────────────────────────────────

def write_datasets_index() -> None:
    with open(DATASETS_REF) as f:
        datasets: dict = json.load(f)

    index = {}
    for name, info in sorted(datasets.items()):
        ver_info = latest_version(info["versions"])
        index[name] = {
            "name":    name,
            "title":   info["title"],
            "version": ver_info["version"],
            "doi":     ver_info.get("doi"),
            "release": ver_info.get("release", {}),
        }

    write_json(DS_REPO / "datasets.json", index)
    print(f"Wrote datasets.json  ({len(index)} entries)")


def write_collections_index() -> None:
    with open(COLLECTIONS_REF) as f:
        collections: dict = json.load(f)

    index = {}
    for name, info in sorted(collections.items()):
        ver_info = latest_version(info["versions"])
        index[name] = {
            "name":     name,
            "title":    info["title"],
            "version":  ver_info["version"],
            "doi":      ver_info.get("doi"),
            "datasets": ver_info.get("datasets", []),
            "release":  ver_info.get("release", {}),
        }

    write_json(COL_REPO / "collections.json", index)
    print(f"Wrote collections.json  ({len(index)} entries)")


# ── File sync from asap-crn-cloud-dataset-metadata ────────────────────────────

def sync_dataset_files(dataset_filter: str | None = None) -> tuple[int, int]:
    """Copy DOI/, refs/, scripts/ from asap-crn-cloud-dataset-metadata into cloud-datasets.

    Only operates on datasets that exist in datasets_references.json (i.e. the
    25 released datasets).  Datasets missing from the source metadata repo are
    skipped with a warning.

    Returns:
        (datasets_synced, total_files_copied)
    """
    with open(DATASETS_REF) as f:
        datasets: dict = json.load(f)

    if dataset_filter:
        datasets = {k: v for k, v in datasets.items() if k == dataset_filter}

    synced = 0
    total_files = 0
    for name in sorted(datasets):
        src_base = DS_META / name
        dst_base = DS_REPO / "datasets" / name

        if not src_base.exists():
            print(f"  SKIP {name}: not found in asap-crn-cloud-dataset-metadata")
            continue

        file_count = 0
        for subdir in SYNC_SUBDIRS:
            n = copy_subdir(src_base / subdir, dst_base / subdir)
            file_count += n

        print(f"  synced: {name}  ({file_count} file(s) across {SYNC_SUBDIRS})")
        synced += 1
        total_files += file_count

    return synced, total_files


# ── Archive population from asap-crn-cloud-dataset-metadata ───────────────────

def archive_dataset_versions(dataset_filter: str | None = None) -> tuple[int, int]:
    """Populate archive/<version>/ for every prior dataset version.

    Per README-datasets.md each version under archive/ should contain:
      DOI/     — DOI files for that version (stubbed; source has current-only)
      refs/    — reference files for that version (stubbed)
      scripts/ — scripts for that version (stubbed)

    Source material used where available:
      metadata/archive/<version>/ — CDE metadata CSVs, copied flat into
                                    archive/<version>/ as reference snapshots

    The current (latest) version is skipped — its files live at the top level.

    Returns:
        (datasets_processed, total_files_copied)
    """
    with open(DATASETS_REF) as f:
        datasets: dict = json.load(f)

    if dataset_filter:
        datasets = {k: v for k, v in datasets.items() if k == dataset_filter}

    processed = 0
    total_files = 0
    for name, info in sorted(datasets.items()):
        all_versions = sorted(info["versions"])
        if len(all_versions) <= 1:
            continue  # nothing to archive

        src_base = DS_META / name
        dst_base = DS_REPO / "datasets" / name / "archive"
        prior_versions = all_versions[:-1]  # everything except the latest

        file_count = 0
        for ver in prior_versions:
            ver_dir = dst_base / ver

            # Always create the stub subdirectory structure
            stub_dirs(ver_dir, ["DOI", "refs", "scripts"])

            # Copy CDE metadata CSVs from source metadata/archive/<version>/
            # if the directory exists — these serve as the version's data snapshot.
            src_meta_archive = src_base / "metadata" / "archive" / ver
            if src_meta_archive.exists():
                n = copy_subdir(src_meta_archive, ver_dir)
                file_count += n

        print(f"  archive: {name}  ({len(prior_versions)} prior version(s): "
              f"{', '.join(prior_versions)})  {file_count} file(s) copied")
        processed += 1
        total_files += file_count

    return processed, total_files


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    """Populate local repos from references, and optionally sync source files.

    Usage:
        python scripts/populate_local_repositories.py                        # metadata + sync + archive all
        python scripts/populate_local_repositories.py --datasets             # datasets only
        python scripts/populate_local_repositories.py --collections          # collections only
        python scripts/populate_local_repositories.py --no-sync              # skip file sync + archive
        python scripts/populate_local_repositories.py --sync-only            # file sync + archive only
        python scripts/populate_local_repositories.py <name>                 # single dataset/collection
    """
    args = set(sys.argv[1:])
    do_datasets    = "--datasets"    in args or "--collections" not in args
    do_collections = "--collections" in args or "--datasets"    not in args
    do_sync        = "--no-sync"     not in args and "--collections" not in args
    sync_only      = "--sync-only"   in args
    name_filter    = next((a for a in args if not a.startswith("--")), None)

    if not sync_only:
        if do_datasets:
            print(f"\n── Datasets → {DS_REPO.relative_to(ROOT)} ──")
            n = populate_datasets(dataset_filter=name_filter)
            write_datasets_index()
            print(f"  {n} dataset(s) written")

        if do_collections:
            print(f"\n── Collections → {COL_REPO.relative_to(ROOT)} ──")
            n = populate_collections(collection_filter=name_filter)
            write_collections_index()
            print(f"  {n} collection(s) written")

    if do_sync or sync_only:
        print(f"\n── Sync files → {DS_REPO.relative_to(ROOT)}/datasets/ ──")
        print(f"   from {DS_META.relative_to(ROOT)}/")
        synced, files = sync_dataset_files(dataset_filter=name_filter)
        print(f"  {synced} dataset(s) synced, {files} file(s) copied")

        print(f"\n── Archive prior versions → {DS_REPO.relative_to(ROOT)}/datasets/<name>/archive/ ──")
        archived, arc_files = archive_dataset_versions(dataset_filter=name_filter)
        print(f"  {archived} dataset(s) with prior versions, {arc_files} file(s) copied")

    print("\nDone.")


if __name__ == "__main__":
    main()
