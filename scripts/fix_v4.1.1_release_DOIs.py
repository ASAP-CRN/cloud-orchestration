
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
#   6b. create dataset.json stubs in `cloud-datasets/WIP/`
#   6c. create v1.0 DOI reference files, including additional annotation for .pdf (e.g. version bump copy)
#   6d. create unpublished v1.0 zenodo reference
#   7. publish DOI and copy WIP dataset tree to cloud-datasets root


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

# %% [Step 5a] Release parameters
# TODO: set the publication date and CDE version for this acceptance tranche
PUBLICATION_DATE = "2026-05-31"   # e.g. "2026-05-01"
CDE_VERSION = "v4.4"              # e.g. "v3.3"


# %% [Step 5b].  Tranche of v1.0 datasets

# v1.0 datasets, v4.3 cde
datasets = [
    "voet-pmdbs-sn-atacseq-scalebio-hydrop", # 20076952
    "voet-pmdbs-sn-atacseq-10x", # 20077637
    "voet-pmdbs-sn-atacseq-hydrop",
    "voet-pmdbs-sn-atacseq-scalebio-10x",
    "voet-pmdbs-sn-multimodal",
    "voet-pmdbs-sn-rnaseq",
    "voet-pmdbs-sn-rnaseq-parsebio",
    "scherzer-pmdbs-sn-rnaseq-midbrain-hybsel",
    "scherzer-pmdbs-lr-wgs"
    ]

# %%

# # create this now even thouth we'll re-make it later.
# new_dataset_defs = []
# for ds in datasets:
#     ds_path = datasets_repo_path / "datasets" / ds

#     ds_in = ao.Dataset.load(ds_path)
 
#     new_dataset_defs.append(ds_def)
    
# # %%    




# %%
# move below to part of a release script
# # %%
zenodo = ao.setup_zenodo()


# %% 


for ds in datasets:
    ds_path = datasets_repo_path / "datasets" / ds
    # TODO: update the filename to match the actual reference document
    
    # confirm we have v0.1
    # read version
    current_version = (ds_path / "version").read_text().strip()
    if current_version != "1.0":
        print(f"WARNING: expected version 1.0 for {ds}, but found {current_version}")
        continue


    v1_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    if not v1_doi_id:
        print(f"WARNING: no DOI found for {ds} at v1.0 after ingestion")
        continue
    else:        
        print(f"Found DOI for {ds} at v1.0: {v1_doi_id}")



    # update v1.0
    metadata = ao.create_draft_metadata(ds_path, version="1.0")
    metadata["version"] = "v1.0"


    deposition = ao.update_doi_metadata(zenodo, v1_doi_id, metadata)


    deposition = zenodo.deposition
    
    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)
    # # make sure we are published
    # deposition = ao.publish_doi(zenodo, v1_doi_id)

    
    ao.archive_deposition_local(ds_path, "final-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)

# %%



for ds in datasets:
    ds_path = datasets_repo_path / "datasets" / ds
    # TODO: update the filename to match the actual reference document
    
    # confirm we have v0.1
    # read version
    current_version = (ds_path / "version").read_text().strip()
    if current_version != "1.0":
        print(f"WARNING: expected version 1.0 for {ds}, but found {current_version}")
        continue


    v1_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    if not v1_doi_id:
        print(f"WARNING: no DOI found for {ds} at v1.0 after ingestion")
        continue
    else:        
        print(f"Found DOI for {ds} at v1.0: {v1_doi_id}")



    zenodo.set_deposition_id(v1_doi_id)
    deposition = zenodo.deposition

    # # make sure we are published
    deposition = ao.publish_doi(zenodo, v1_doi_id)

    
    ao.archive_deposition_local(ds_path, "final-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)



# %%

# doi_id = "20078073"
# zenodo.set_deposition_id(doi_id)
# deposition = zenodo.deposition




# %%
