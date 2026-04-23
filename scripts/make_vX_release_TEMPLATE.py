# %% [markdown]
# # ASAP CRN — Release Template
#
# Copy this file and rename it, e.g. `make_v4.1.0_release.py`.
# Fill in every section marked with TODO before running cell by cell.
#
# **Lifecycle covered here:**
#   1. Define new datasets being added or version-bumped in this release
#   2. Assemble the full dataset + collection manifests
#   3. Build the ReleaseDefinition and CollectionDefinitions
#   4. Perform the release  (writes cloud-releases)
#   5. Update collections   (writes cloud-collections)
#   6. Archive dataset versions and update release records (writes cloud-datasets)
#   7. Rebuild master indexes (datasets.json, collections.json)
#
# DO NOT EXECUTE THIS FILE DIRECTLY — it is a template only.

# %% Setup
from pathlib import Path
import asap_orchestrator as ao

# TODO: confirm the root path resolves correctly for your environment
root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"
collections_repo_path = root_path / "cloud-collections"
releases_repo_path = root_path / "cloud-releases"

# %% [Step 1] Release parameters
# TODO: fill in release version, type, CDE version, and optional release DOI
RELEASE_VERSION = "vX.Y.Z"    # e.g. "v4.1.0"
RELEASE_TYPE = "Minor"        # "Urgent" | "Minor" | "Major"
CDE_VERSION = "vX.Y"          # e.g. "v3.3"
RELEASE_DOI = ""              # Zenodo concept DOI for the release itself, or ""

# %% [Step 2] Define datasets NEW or VERSION-BUMPED in this release
# Each entry needs a published (or pre-reserved) Zenodo DOI.
# Use version="v1.0" for datasets being released for the first time (promoted
# from WIP v0.1).  Use the new bumped version for datasets being re-released.

new_dataset_defs = [
    ao.define_dataset(
        name="teamX-tissue-modality",             # TODO: replace
        collection="tissue-modality",             # TODO: replace, or None
        version="v1.0",                           # TODO: replace
        doi="10.5281/zenodo.XXXXXXXX",            # TODO: replace with published DOI
        cde_version=CDE_VERSION,
    ),
    # Add more ao.define_dataset() entries for each new/bumped dataset...
]

# %% [Step 3] Build the full dataset list for the release manifest
# This must include ALL datasets (new + previously released).
# Read existing dataset entries directly from their dataset.json files so DOIs
# and versions stay in sync with the source of truth.

previously_released_names = [
    # TODO: list every dataset name that was in prior releases and carries
    # forward unchanged into this one, e.g.:
    # "hafler-pmdbs-sn-rnaseq-pfc",
    # "hardy-pmdbs-bulk-rnaseq",
]

all_dataset_entries = [
    ao.read_dataset_entry(datasets_repo_path / name)
    for name in previously_released_names
] + [ds.to_release_entry() for ds in new_dataset_defs]

new_dataset_entries = [ds.to_release_entry() for ds in new_dataset_defs]

# %% [Step 4] Define the collections being versioned in this release
# Only collections that have new or updated datasets need a version bump.
# For an Urgent release with no curated datasets, this list may be empty.
#
# Each entry: {"name": <collection-name>, "doi": <zenodo-doi>, "version": <new-version>}
# The DOI here is the Zenodo concept DOI for the new collection version.

collection_entries = [
    # TODO: fill in for each updated collection, e.g.:
    # {"name": "pmdbs-sc-rnaseq", "doi": "10.5281/zenodo.YYYYYYYY", "version": "v3.2.0"},
]

# %% [Step 5] Build the ReleaseDefinition
release_def = ao.define_release(
    release_version=RELEASE_VERSION,
    release_type=RELEASE_TYPE,
    cde_version=CDE_VERSION,
    datasets=all_dataset_entries,
    new_datasets=new_dataset_entries,
    collections=collection_entries,
)

# %% [Step 6] Define collections (one CollectionDefinition per updated collection)
# Maps each new collection version to the datasets it gains in this release.
# `new_datasets` lists only the names added/bumped in *this* release; existing
# datasets are carried forward automatically from the collection's current state.

collection_defs = [
    # TODO: add one ao.define_collection() call per entry in collection_entries, e.g.:
    # ao.define_collection(
    #     collection_name="pmdbs-sc-rnaseq",
    #     new_version="v3.2.0",
    #     new_datasets=[ds.name for ds in new_dataset_defs if ds.collection == "pmdbs-sc-rnaseq"],
    #     release_def=release_def,
    # ),
]

# %% [Step 7] Perform the release
# Writes <release_version>/release.json and updates releases.json in cloud-releases.
release_dir = ao.perform_release(
    release_def,
    releases_repo_path=releases_repo_path,
    release_doi=RELEASE_DOI,
)
print(f"Release written: {release_dir}")

# %% [Step 8] Update collections
# Writes collection.json and archive snapshots in cloud-collections.
for col_def in collection_defs:
    ao.update_collection(col_def, collections_repo_path)
    print(f"Updated collection: {col_def.collection_name} -> {col_def.new_version}")

# %% [Step 9] Archive dataset versions and record release in dataset.json
# For each NEW or BUMPED dataset:
#   - copies DOI/ and refs/ to archive/<old_version>/
#   - sets the new version in dataset.json
#   - adds the release record under dataset.json["releases"]
#   - updates all_versions entry

for ds_def in new_dataset_defs:
    ds_path = datasets_repo_path / ds_def.name
    if not ds_path.exists():
        # Dataset may still be under WIP/ — promote it first
        wip_path = datasets_repo_path / "WIP" / ds_def.name
        if wip_path.exists():
            import shutil
            shutil.move(str(wip_path), str(ds_path))
            print(f"Promoted from WIP: {ds_def.name}")
        else:
            print(f"WARNING: dataset directory not found: {ds_def.name}")
            continue

    ao.update_dataset_version(
        ds_path=ds_path,
        new_version=ds_def.version,
        release_version=RELEASE_VERSION,
        cde_version=CDE_VERSION,
    )
    print(f"Archived dataset: {ds_def.name} -> {ds_def.version}")

# %% [Step 10] Rebuild master indexes
ao.update_datasets_index(datasets_repo_path)
print("datasets.json updated")

# collections.json is rebuilt automatically inside update_collection(),
# but run explicitly here if collections were not updated above.
if not collection_defs:
    ao.update_collections_index(collections_repo_path)
    print("collections.json updated")
