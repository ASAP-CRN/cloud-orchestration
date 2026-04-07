"""Populate the cloud-releases repository from release resource files.

Assumptions
-----------
- All repos share the same parent directory.
- Source data lives in  ../asap-crn-cloud-release-resources/releases/<version>/
- Target repo is         ../cloud-releases/

Actions
-------
1. Copy templates/README-releases.md  →  cloud-releases/README.md
2. For each release version:
     a. Create  cloud-releases/releases/<version>/
     b. Copy (or generate) release.json
     c. Copy release_scripts/ contents → releases/<version>/scripts/
3. Write cloud-releases/releases.json  (root index of all releases)
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path


# ── Path resolution ────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]          # parent of all repos

SRC_RELEASES  = ROOT / "asap-crn-cloud-release-resources" / "releases"
ORCH_ROOT     = ROOT / "cloud-orchestration"
TEMPLATE_DIR  = ORCH_ROOT / "templates"
REF_DIR       = ORCH_ROOT / "references"
TARGET_REPO   = ROOT / "cloud-releases"

RELEASES_REF  = REF_DIR / "releases_references.json"

VERSIONS = [
    "v1.0.0", "v2.0.0", "v2.0.1", "v2.0.2", "v2.0.3",
    "v3.0.0", "v3.0.1", "v3.0.2", "v4.0.0",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_releases_ref() -> dict:
    with open(RELEASES_REF) as f:
        return json.load(f)


def _normalise_list(items: list, lookup: dict) -> list:
    """Ensure every element in *items* is an object {name, doi, version}.

    *items* may contain plain name strings (legacy source files) or already
    be dicts.  *lookup* maps name → reference entry for doi/version fill-in.
    """
    result = []
    for item in items:
        if isinstance(item, str):
            ref = lookup.get(item, {})
            result.append({
                "name":    item,
                "doi":     ref.get("doi"),
                "version": ref.get("version"),
            })
        else:
            # Already an object — ensure all three keys exist
            result.append({
                "name":    item.get("name"),
                "doi":     item.get("doi"),
                "version": item.get("version"),
            })
    return result


def _ds_obj(ds: dict) -> dict:
    """Convert a dataset entry from releases_references to a release.json object."""
    return {"name": ds["name"], "doi": ds.get("doi"), "version": ds.get("version")}


def _col_obj(c: dict) -> dict:
    """Convert a collection entry from releases_references to a release.json object."""
    return {"name": c["name"], "doi": c.get("doi"), "version": c.get("version")}


def generate_release_json(version: str, ref: dict) -> dict:
    """Build a release.json dict from releases_references.json for versions
    that don't have one in the source tree."""
    rel = ref[version]
    datasets     = [_ds_obj(ds) for ds in rel.get("all_datasets", [])]
    new_datasets = [_ds_obj(ds) for ds in rel.get("new_datasets", [])]
    collections  = [_col_obj(c) for c in rel.get("all_collections", [])]
    # derive cde_version from first dataset entry
    cde = next(
        (ds.get("cde_version") for ds in rel.get("all_datasets", []) if ds.get("cde_version")),
        None,
    )
    return {
        "release_version": version,
        "cde_version":     cde,
        "release_doi":     "",
        "datasets":        datasets,
        "new_datasets":    new_datasets,
        "collections":     collections,
        "created":         datetime.now().isoformat(),
        "metadata": {
            "total_datasets":    len(datasets),
            "total_collections": len(collections),
            "source":            "generated from releases_references.json",
        },
    }


def copy_scripts(src_scripts_dir: Path, dst_scripts_dir: Path) -> int:
    """Copy all files from src_scripts_dir into dst_scripts_dir. Returns count."""
    if not src_scripts_dir.exists():
        return 0
    dst_scripts_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in src_scripts_dir.iterdir():
        dst = dst_scripts_dir / item.name
        if item.is_file():
            shutil.copy2(item, dst)
            count += 1
        elif item.is_dir():
            shutil.copytree(item, dst, dirs_exist_ok=True)
            count += 1
    return count


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    releases_ref = load_releases_ref()

    # 1. README
    src_readme = TEMPLATE_DIR / "README-releases.md"
    dst_readme = TARGET_REPO / "README.md"
    shutil.copy2(src_readme, dst_readme)
    print(f"Copied README  →  {dst_readme.relative_to(ROOT)}")

    index = {}   # will become releases.json

    for version in VERSIONS:
        if version not in releases_ref:
            print(f"  SKIP {version} (not in releases_references.json)")
            continue

        src_ver   = SRC_RELEASES / version
        dst_ver   = TARGET_REPO / "releases" / version
        dst_ver.mkdir(parents=True, exist_ok=True)

        # 2a. release.json
        src_rjson = src_ver / "release.json"
        dst_rjson = dst_ver / "release.json"
        ref = releases_ref[version]
        if src_rjson.exists():
            with open(src_rjson) as f:
                release_data = json.load(f)
            # Normalise datasets/new_datasets/collections to object form and
            # ensure new_datasets is present — source files store flat name lists.
            release_data["datasets"] = _normalise_list(
                release_data.get("datasets", []),
                {ds["name"]: ds for ds in ref.get("all_datasets", [])},
            )
            release_data["new_datasets"] = _normalise_list(
                release_data.get("new_datasets")
                or [ds["name"] for ds in ref.get("new_datasets", [])],
                {ds["name"]: ds for ds in ref.get("new_datasets", [])},
            )
            release_data["collections"] = _normalise_list(
                release_data.get("collections", []),
                {c["name"]: c for c in ref.get("all_collections", [])},
            )
            with open(dst_rjson, "w") as f:
                json.dump(release_data, f, indent=2)
            print(f"  {version}: copied   release.json")
        else:
            generated = generate_release_json(version, releases_ref)
            with open(dst_rjson, "w") as f:
                json.dump(generated, f, indent=2)
            print(f"  {version}: generated release.json")

        # 2b. scripts/
        n = copy_scripts(src_ver / "release_scripts", dst_ver / "scripts")
        print(f"  {version}: copied {n} item(s) → scripts/")

        # accumulate index entry
        index[version] = releases_ref[version]

    # 3. releases.json at repo root
    dst_index = TARGET_REPO / "releases.json"
    with open(dst_index, "w") as f:
        json.dump(index, f, indent=2)
    print(f"\nWrote releases.json  →  {dst_index.relative_to(ROOT)}")
    print(f"\nDone. Populated {len(index)} release(s) in {TARGET_REPO.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
