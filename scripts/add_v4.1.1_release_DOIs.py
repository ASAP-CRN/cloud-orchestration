
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

# TODO: confirm the root path resolves correctly for your environment

%load_ext autoreload
%autoreload 2
# 

root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"

# %% [Step 5a] Release parameters
# TODO: set the publication date and CDE version for this acceptance tranche
PUBLICATION_DATE = "2026-04-30"   # e.g. "2026-05-01"
CDE_VERSION = "v4.3"              # e.g. "v3.3"


# %% [Step 5b].  Tranche of v1.0 datasets

# v1.0 datasets, v4.3 cde
datasets = [
    'lee-mouse-ms-p-lung-g2019s-hf-diet',
    'lee-mouse-ms-mb-plasma-g2019s-hf-diet', #    'lee-mouse-ms-mb-plasma-2019s-hf-diet',
    'lee-mouse-ms-mb-liver-g2019s-hf-diet',
    'lee-mouse-ms-mb-striatum-g2019s-hf-diet',
    'lee-mouse-ms-mb-lung-g2019s-hf-diet',
    'lee-mouse-ms-mb-kidney-g2019s-hf-diet',
    'lee-mouse-ms-l-plasma-g2019s-hf-diet',
    'lee-mouse-ms-l-liver-g2019s-hf-diet',
    'lee-mouse-ms-l-striatum-g2019s-hf-diet',
    'lee-mouse-ms-l-lung-g2019s-hf-diet',
    'lee-mouse-ms-l-kidney-g2019s-hf-diet',
    'lee-mouse-ms-mb-plasma-g2019s-nuc-quant',
    'lee-mouse-ms-mb-striatum-g2019s-nuc-quant',
    'lee-mouse-ms-mb-midbrain-g2019s-nuc-quant',
    'alessi-mouse-ms-p-lung-vps35-d620n-wt',
    'alessi-mouse-ms-p-brain-vps35-d620n-wt',
    'alessi-mouse-ms-p-brain-vps35-d620n-dmso-mli2',
    'alessi-mouse-ms-p-lung-vps35-d620n-dmso-mli2',
]

# %% [Step 3] Re-Ingest DOI reference documents
# Place the team-supplied .docx reference file in <name>/refs/ first, then
# run this cell to populate DOI/<name>.json, project.json, and the README.
#
# Update the filename in `ref_doc` for each dataset as needed.

for ds in datasets:
    ds_path = datasets_repo_path / "WIP" / ds
    # TODO: update the filename to match the actual reference document
    

    # confirm we have v0.1
    # read version
    current_version = (ds_path / "version").read_text().strip()
    if current_version != "0.1":
        print(f"WARNING: expected version 0.1 for {d}, but found {current_version}")
        continue


    # find the refs.docx
    ref_path = ds_path / "refs"
    ref_path.glob("**.docx")
    if len(list(ref_path.glob("**.docx"))) == 1:
        ref_doc = list(ref_path.glob("**.docx"))[0]
    else:
        print(f"WARNING: expected exactly 1 .docx file in {ref_path}, but found {len(list(ref_path.glob('**.docx')))}")
        continue

    ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE)
    print(f"DOI info ingested: {ds}")




    # assert v1.0
    ds_version = "1.0"
    # write version
    ao.write_version(ds_version, ds_path / "version")

    # # load deposition 
    # # bump version
    # ao.bump_doi_version()

# %% [Step 5] Create Zenodo draft DOIs (v0.1)
# Requires ZENODO_TOKEN (or ZENODO_SANDBOX_TOKEN) set in your environment.
# Each dataset gets a new Zenodo deposition draft; the concept DOI is written
# back to dataset.json and DOI/dataset.doi.

zenodo = ao.setup_zenodo()
ds = datasets[0]

for ds in datasets:
    ds_path = datasets_repo_path / "WIP" / ds
    # TODO: update the filename to match the actual reference document
    v1_beta_doi_id = ao.get_doi_from_dataset(ds_path, version=True)
    deposition = zenodo.get_deposition(v1_beta_doi_id)

    # ao.update_dataset_doi(ds_path, zenodo, deposition, version="v1.0", publication_date=PUBLICATION_DATE)
    # define update_dataset_doi    
    deposition = ao.bump_doi_version(zenodo, v1_beta_doi_id)


    metadata = deposition.get("metadata")
    new_doi_id = f"{deposition['id']}"

    print(f"Updated DOI for {ds}: {new_doi_id}")

    # update v1.0
    metadata['version'] = '1.0'
    deposition = ao.update_doi_metadata(zenodo, new_doi_id, metadata)


    file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"
    # deposition = update_doi_metadata(zenodo, v1_beta_doi_id, metadata)
    deposition = ao.add_anchor_file_to_doi(zenodo,  file_path, new_doi_id)

    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)

# %% [Step 67] publish DOI and move WIP dataset tree to cloud-datasets root

for ds in datasets:
    ds_path = datasets_repo_path / "WIP" / ds
    # TODO: update the filename to match the actual reference document
    doi_id = ao.get_doi_from_dataset(ds_path, version=True)
    deposition = zenodo.get_deposition(doi_id)


    deposition = ao.publish_doi(zenodo, doi_id)
    ao.archive_deposition_local(ds_path, "final-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)

    # move WIP to root
    final_ds_path = datasets_repo_path / ds
    if final_ds_path.exists():
        print(f"WARNING: {final_ds_path} already exists. Please resolve before moving.")
    else:
        shutil.move(str(ds_path), str(final_ds_path))
        print(f"Moved {ds_path} to {final_ds_path}")

# %%

for ds_def in new_dataset_defs:
    ds_path = datasets_repo_path / "WIP" / ds_def.name
    readme_pdf = ds_path / "DOI" / f"{ds_def.name}_README.pdf"
    doi_id = ao.get_doi_from_dataset(ds_path, version=True)
    if readme_pdf.exists():
        ao.add_anchor_file_to_doi(zenodo, readme_pdf, doi_id)
        print(f"Uploaded README: {ds_def.name}")
    else:
        print(f"WARNING: README PDF not found for {ds_def.name}")





        # find the ref name for ingest
        print(f"Processing {dataset}")
        ds_path = datasets_path / dataset

        # get doi info:
        v1_beta_doi_id = get_doi_from_dataset(ds_path)

        # begin DOI bumping to v1.0
        # write version = 1.0
        write_version("1.0", ds_path / "version")
        setup_DOI_info(ds_path, intake_doc, publication_date="2026-03-30")

        deposition = bump_doi_version(zenodo, v1_beta_doi_id)
        metadata = deposition.get("metadata")
        new_doi_id = f"{deposition['id']}"

        # update v1.0
        metadata['version'] = '1.0'
        deposition = update_doi_metadata(zenodo, new_doi_id, metadata)
        file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"
        # deposition = update_doi_metadata(zenodo, v1_beta_doi_id, metadata)
        deposition = add_anchor_file_to_doi(zenodo,  file_path, new_doi_id)

        archive_deposition_local(ds_path, "pre-release-deposition", deposition)
        finalize_DOI(ds_path, deposition)



# %% [markdown]
# ASAP CRN Metadata validation
#
#
# 21 May 2026
# Andy Henrie
# DO NOT EXECUTE

#%%
import pandas as pd
from pathlib import Path
import os, sys
import shutil

from crn_utils.util import (
    read_CDE,
    NULL,
    prep_table,
    read_meta_table,
    read_CDE_asap_ids,
    export_meta_tables,
    load_tables,
    write_version,
)

from crn_utils.asap_ids import *
from crn_utils.validate import validate_table, ReportCollector, process_table

from crn_utils.bucket_util import gcloud_ls, gcloud_ls_long

from crn_utils.constants import *
from crn_utils.doi import *

%load_ext autoreload
%autoreload 2

# %%
root_path = Path(__file__).resolve().parents[3]
datasets_path = root_path / "datasets"

# %%

# v1.0 datasets, v4.4 cde
datasets = [
    "voet-pmdbs-sn-multimodal",
    "voet-pmdbs-sn-atacseq-scalebio-hydrop",
    "voet-pmdbs-sn-atacseq-scalebio-10x",
    "voet-pmdbs-sn-atacseq-hydrop",
    "voet-pmdbs-sn-atacseq-10x",
    "voet-pmdbs-sn-rnaseq-parsebio",
    "voet-pmdbs-sn-rnaseq",
    "scherzer-pmdbs-sn-rnaseq-midbrain-hybsel",
    "scherzer-pmdbs-lr-wgs"
    ]

############# WIP datasets
datasets = [
    'vangheluwe-ipsc-bulk-atacseq-astro-atp13a2lof',
    'vangheluwe-ipsc-bulk-rnaseq-astro-atp13a2lof',
    'vangheluwe-ipsc-bisulfseq-astro-atp13a2lof',
        ]


datasets = [
'lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet',
'lee-mouse-sn-rnaseq-midbrain-g2019s-hf-diet',
'lee-mouse-liver-bulk-rnaseq-g2019s',
'lee-mouse-ms-p-lung-g2019s-hf-diet',
'lee-mouse-ms-mb-plasma-g2019s-hf-diet',
'lee-mouse-ms-mb-liver-g2019s-hf-diet',
'lee-mouse-ms-mb-striatum-g2019s-hf-diet',
'lee-mouse-ms-mb-lung-g2019s-hf-diet',
'lee-mouse-ms-mb-kidney-g2019s-hf-diet',
'lee-mouse-ms-l-plasma-g2019s-hf-diet',
'lee-mouse-ms-l-liver-g2019s-hf-diet',
'lee-mouse-ms-l-striatum-g2019s-hf-diet',
'lee-mouse-ms-l-lung-g2019s-hf-diet',
'lee-mouse-ms-l-kidney-g2019s-hf-diet',
'lee-mouse-ms-mb-plasma-g2019s-nuc-quant',
'lee-mouse-ms-mb-striatum-g2019s-nuc-quant',
'lee-mouse-ms-mb-midbrain-g2019s-nuc-quant',
    ]

'scherzer-pmdbs-sn-rnaseq-midbrain-hybsel',
'scherzer-pmdbs-lr-wgs',
'scherzer-pmdbs-sn-multiome-midbrain',
'decamilli-invitro-ms-p-hek293-apex-atg2-silac',


datasets = [
"indipd-ipsc-bulk-rnaseq-kolf21j-wt",
"indipd-ipsc-cageseq-kolf21j-wt",
"indipd-ipsc-hicseq-kolf21j-wt",
"indipd-ipsc-lr-wgs-kolf21j-wt",
    ]

# %%

for dataset in datasets:
    print(f"Processing {dataset}")
    ds_path = datasets_path / dataset
    if not ds_path.exists():
        print(f"    {ds_path} does not exist")
        ds_path.mkdir(parents=True, exist_ok=True)

    # metadata_path = ds_path / "metadata"
    # if not metadata_path.exists():
    #     metadata_path.mkdir(parents=True, exist_ok=True)
    doi_path = ds_path / "DOI"  
    if not doi_path.exists():
        doi_path.mkdir(parents=True, exist_ok=True)
    refs_path = ds_path / "refs"
    if not refs_path.exists():
        refs_path.mkdir(parents=True, exist_ok=True)
    scripts_path = ds_path / "refs"
    if not scripts_path.exists():
        scripts_path.mkdir(parents=True, exist_ok=True)


# %%
# %%



# %%
# %%

for dataset in datasets:
    # find the ref name for ingest
    print(f"Processing {dataset}")
    ds_path = datasets_path / dataset
    intake_doc = ds_path / "refs/APEX-ATG2A MS Data Set.docx"

    # write version = 0.1
    write_version("0.1", ds_path / "version")
    # refs_path = ds_path / "refs"
    # ref_files = list(refs_path.glob("*.docx"))

    # if len(ref_files) == 1:
    #     intake_doc = ref_files[0]
    # else:
    #     print("Multiple ref files found.  Please select the correct one.")
    #     break

    print(intake_doc)

    # INGEST DOI DOCS
    _setup_DOI_info(ds_path, intake_doc, publication_date="2026-04-07")

# %%

