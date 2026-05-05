
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
import json
from pathlib import Path
import asap_orchestrator as ao
from asap_orchestrator.doi import bump_doi_version, make_readme_file

import shutil
# TODO: confirm the root path resolves correctly for your environment

%load_ext autoreload
%autoreload 2
# 

root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"

# %% [Step 5a] Release parameters
# TODO: set the publication date and CDE version for this acceptance tranche
PUBLICATION_DATE = "2026-02-30"   # e.g. "2026-05-01"
CDE_VERSION = "v4.1"              # e.g. "v3.3"

RELEASE_VERSION = "v4.0.1" 
# %% [Step 5b].  Tranche of v1.0 datasets

# v1.0 datasets, v4.1 cde
datasets = [
    'schapira-fecal-metagenome-human-baseline',
    'lee-mouse-liver-bulk-rnaseq-g2019s', 
    'lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet', 
    'lee-mouse-sn-rnaseq-midbrain-g2019s-hf-diet', 
    'liddle-human-colon-spatial-cosmx-rna-1000p',
    'liddle-human-colon-spatial-cosmx-protein-64p'
]

# release info is the same for all of these
target_keywords = ["mouse", "liver", "bulk-rnaseq", "sn-rnaseq", "human-colon","spatial-cosmx","fecal-metagenome"]  # used to identify which datasets to apply this release_info to; e.g. if your release includes datasets from multiple teams or with different characteristics, you can use this field to specify which datasets get which release_info

# %% [Step 1] 
#   write version = 1.0 to version file
# copy to root if needed at end of script

for ds in datasets:
    ds_path = datasets_repo_path / "WIP" / ds

    # confirm we have v0.1
    # read version
    current_version = (ds_path / "version").read_text().strip()
    if current_version != "0.1":
        print(f"WARNING: expected version 0.1 for {ds_path.name}, but found {current_version}")
        continue
    # assert v1.0
    ds_version = "1.0"
    # write version
    ao.write_version(ds_version, ds_path / "version")
    keys = ds.split("-")
    keywords = [key for key in target_keywords if key in ds]  # e.g. "lee-mouse-liver-bulk-rnaseq-g2019s" -> ["mouse", "liver", "bulk-rnaseq"]
    release_info = {
        RELEASE_VERSION: {
        "cde_version": CDE_VERSION,
        "dataset_version": ds_version
        }
    }

    # description = f"{"-".join(ds.split('-')[1:])} from team-{ds.split('-')[0]}"
    dataset_json = ao.create_dataset_json(
        ds_path,
        cloud_datasets_path=ds_path,  # TODO: write to ds_path here.
        collection = None,  # TODO: add collection name if applicable
        cde_version = CDE_VERSION,
        keywords = keywords,  # TODO: add list of keywords if desired
        description = None,  # TODO: add description if desired
        release_info = release_info,  # optional dict of additional release-specific info to include in dataset.json
    )
 

    # move WIP to root
    final_ds_path = datasets_repo_path / ds
    if final_ds_path.exists():
        print(f"WARNING: {final_ds_path} already exists. Please resolve before moving.")
    else:
        shutil.move(str(ds_path), str(final_ds_path))
        print(f"Moved {ds_path} to {final_ds_path}")


# %%
