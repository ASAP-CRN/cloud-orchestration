# %% 
#
# template script for creating a new tranch of WIP Datasets
# Andy Henrie
# DO NOT EXECUTE
#. requires a "datsets.json" configuration file

#%%
import pandas as pd
from pathlib import Path
import os, sys
import shutil


repo_root = Path(__file__).resolve().parents[1]
wf_common_path = repo_root / "src" / "asap_orchestrator"

import asap_orchestrator as ao


%load_ext autoreload
%autoreload 2

# %%
root_path = Path(__file__).resolve().parents[2]
dest_path = root_path / "cloud-datasets/WIP"
source_path = root_path / "asap-crn-cloud-dataset-metadata/datasets/"



# %%
# step 1:  create dataset.json stub
#.         need a dataset name, reference file path, and date

version = "v0.1"

dataset_names = [
    "teamX-A",
    "teamX-B"
]
ref_paths = [
    "/path/to/X-A.docx",
    "/path/to/X-B.docx"
]

date = "0000-00-00"

datasets = {}

# create example datasets A and B
for name,ref in zip(dataset_names,ref_paths):
    dataset = {"name":name,
                "ref":ref,
                "date":date}
    dataset["version"] = "v0.1"
    datasets[name] = dataset
    



# %%
# ingest references

for ds,dsinfo in datasets.items:

    ds_name = dsinfo["name"]
    ds_ref = dsinfo["ref"]
    ds_date = dsinfo["date"]
    ds_path = dest_path / ds_name
    ao.ingest_DOI_doc()
    ao.setup_DOI_info(ds_path, ds_ref, publication_date=ds_date)
    # force v0.1
    ao.write_version("0.1", ds_path / "version")


# %%
# make v0.1 DOI

for ds,dsinfo in datasets.items:
    # find the ref name for ingest
    print(f"Processing {ds}")
    ds_path = ldataset_path / ds

    zenodo = ao.setup_zenodo()

    current_dataset_version = "0.1"
    local_metadata = ao.create_draft_metadata(ds_path, version=current_dataset_version)
    local_metadata.pop("grants")
    local_metadata["version"] = current_dataset_version
    deposition, metadata = ao.create_draft_doi(zenodo, ds_path, version=current_dataset_version,metadata= local_metadata)
    v1_beta_doi_id = deposition['id']

    file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"
    # deposition = update_doi_metadata(zenodo, v1_beta_doi_id, metadata)
    deposition = ao.add_anchor_file_to_doi(zenodo,  file_path, v1_beta_doi_id)
    deposition = ao.publish_doi(zenodo, v1_beta_doi_id)

    ao.archive_deposition_local(ds_path, "beta-deposition", deposition)
    finalize_DOI(ds_path, deposition)



# %%
