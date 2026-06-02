
# # ASAP CRN — New WIP Dataset Acceptance Template
#
# Copy this file and rename it, e.g. `add_v4.1.0_dataset_release_DOIS.py`.
# Fill in every section marked with TODO before running cell by cell.
#
# **Lifecycle covered here:**
#.  assumes dataset v0.1 dataset DOIs are created:
#   1. Define dataset metadata (name, collection, CDE version, buckets)
#   2. Create `dataset.json` stubs in `cloud-datasets/WIP/`
#   3. Ingest DOI reference `.docx` files to generate Zenodo metadata
#   4. Create Zenodo draft DOIs at `v0.1`
### STARTS Here
#   5. define release paramaters and list of new datasets to release
#   6a. confirm reference exists and v0.1 DOI available
#   6b. create v1.0 DOI reference files, including additional annotation for .pdf (e.g. version bump copy)
#   6c. create unpublished v1.0 zenodo reference
#  7. publish DOI and copy WIP dataset tree to cloud-datasets root


#
# %%
# %% Setup
from pathlib import Path
import asap_orchestrator as ao
from asap_orchestrator.doi import bump_doi_version

import shutil, json
# TODO: confirm the root path resolves correctly for your environment

%load_ext autoreload
%autoreload 2
# 

root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"

# %% [Step 1] Release parameters
# TODO: fill in release version, type, CDE version, and optional release DOI
RELEASE_VERSION = "v5.0.0"    # e.g. "v4.1.0"
RELEASE_TYPE = "Major"        # "Urgent" | "Minor" | "Major"
CDE_VERSION = "v4.4"          # e.g. "v3.3"
RELEASE_DOI = "10.5281/zenodo."              # Zenodo concept DOI for the release itself, or ""
RELEASE_DATE = "2026-06-10"
# %% [Step 2] Define datasets NEW or VERSION-BUMPED in this release
# Each entry needs a published (or pre-reserved) Zenodo DOI.
# Use version="v1.0" for datasets being released for the first time (promoted
# from WIP v0.1).  Use the new bumped version for datasets being re-released.
# v1.0 datasets, v4.3 cde
new_datasets = [
    "team-jakobsson-invitro-bulk-rnaseq-microglia",
    "team-jakobsson-invitro-bulk-rnaseq-dopaminergic",
    "team-voet-pmdbs-sn-atacseq-10x",
]


new_collections = [
    "invitro-bulk-rnaseq",
    "pmdbs-sc-atacseq",

]
# %% [Step 0] move datasets DOI, ref, version from metadata repo to WIP
metadata_repo_path = root_path / "asap-crn-cloud-dataset-metadata"
for ds in datasets:

    if "voet" in ds:
        # append "voet-pmdbs-sn-multiplex"
        source_path = metadata_repo_path / "datasets/voet-pmdbs-sn-multiplex" / ds
    else:
        source_path = metadata_repo_path / "datasets/" / ds

    ds_path = datasets_repo_path / "WIP" / ds
    # now we need to copy things
    if not ds_path.exists():
        ds_path.mkdir(parents=True, exist_ok=True)

    for item in ["DOI", "refs", "version"]:
        source_subdir = source_path / item
        target_subdir = ds_path / item

        if source_subdir.is_dir():
            shutil.copytree(source_subdir, target_subdir, dirs_exist_ok=True)
        elif source_subdir.is_file():
            shutil.copy2(source_subdir, target_subdir)
        else:
            print(f"Warning: {source_subdir} does not exist in source for {ds}")



# %%

# %%

