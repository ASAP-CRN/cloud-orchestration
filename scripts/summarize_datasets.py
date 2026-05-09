
# # ASAP CRN — Summarize Datasets to create Collections and Releases
#

# **Lifecycle covered here:**
#   1a. read datasets.json to get the list of all datasets and their metadata
#   1b. remake datasets.json if needed to ensure it reflects the actual dataset directories and metadata on disk (DOI, version, ref file presence) 
#   2. Summarize all releases from datasets 
#   3. collate all collections from releases
#   4. identify missing DOIs, reference files, etc

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
releases_repo_path = root_path / "cloud-releases"
collections_repo_path = root_path / "cloud-collections"

# %% [Step 5a] Release parameters
# TODO: set the publication date and CDE version for this acceptance tranche
CURRENT_RELEASE = "v4.1.0"   


# %% [Step 1].  get all datasets
datasets_json_path = datasets_repo_path / "datasets.json"
with open(datasets_json_path, "r") as f:
    datasets = json.load(f)

all_datasets = list(datasets.keys())
print(f"Found {len(all_datasets)} datasets in {datasets_json_path}")

#%%
# make sure we have the expected directory structure for each dataset, and if not, create it.  This is a pre-requisite for the next steps where we will read from these directories.
dataset_dirs = [ds.name for ds in (datasets_repo_path / "datasets").glob("*")]

extra_json_dsets = set(all_datasets) - set(dataset_dirs)
extra_dir_dsets = set(dataset_dirs) - set(all_datasets)
if extra_json_dsets:
    print(f"WARNING: the following datasets are listed in {datasets_json_path} but do not have a corresponding directory in cloud-datasets/datasets/: {extra_json_dsets}")
if extra_dir_dsets:    
    print(f"WARNING: the following datasets have a directory in cloud-datasets/datasets/ but are not listed in {datasets_json_path}: {extra_dir_dsets}")


#%% [Step 2] Summarize all releases from datasets
# For each dataset, read the version file to determine which release it belongs to.  Then
# collate all datasets by release, and print a summary of which datasets belong to which releases, along with their DOI and reference file status.
# e.g.
    # "alessi-invitro-ms-p-hek293-gtip": {
    #     "name": "alessi-invitro-ms-p-hek293-gtip",
    #     "title": "team-alessi-invitro-ms-p-hek293-gtip",
    #     "description": "proteomics dataset from team-alessi",
    #     "version": "v1.1",
    #     "doi": "10.5281/zenodo.17355407",
    #     "releases": ["v4.0.2"],
    #     "current_release": "v4.0.2"
    #     "creators": ["alessi"],
    #     "releases": ["v4.0.2"]
    # }

fix_authors = True
fix_lists = True
datasets_dict = {}
for dataset, ds_info in datasets.items():
    if "cohort" not in dataset:
        continue
    else:
        print(f"Processing {dataset}")
    # load dataset.json into Dataset model
    ds_path = datasets_repo_path / "datasets" / dataset
    
    dataset_json_path = ds_path / "dataset.json"
    if dataset_json_path.exists():
        with open(dataset_json_path, "r") as f:
            dataset_json = json.load(f)
    else:
        print(f"WARNING: dataset.json not found for dataset {dataset} at expected path: {dataset_json_path}")
        dataset_json = {}

    # load project.json to get authors
    project_json_path = ds_path / "DOI" / "project.json"
    if project_json_path.exists():
        with open(project_json_path, "r") as f:
            project_info = json.load(f)
        authors = project_info.get("creators", [])
        dataset_title = project_info.get("title", "")
    else:
        print(f"WARNING: project.json not found for dataset {dataset} at expected path: {project_json_path}")
        authors = []
        dataset_title = ""
    
    # if fix creators
    # load dataset.json for update
    if fix_authors: 
        dataset_json["creators"] = authors if authors else dataset_json.get("creators", [])
        dataset_json["dataset_title"] = dataset_title if dataset_title else dataset_json.get("title", "")

        with open(dataset_json_path, "w") as f:
            json.dump(dataset_json, f, indent=4)


    # fix the all_versions while we are here
    all_versions = dataset_json.get("releases", {})
    ds_vers = []
    releases = []
    for rel_ver, rel_info in all_versions.items():
        releases.append(rel_ver)
    ds_vers.append(rel_info["dataset_version"])

    dataset_model = ao.Dataset.load(ds_path)
    export_to_datasets = dataset_model.model_dump()
    export_to_datasets["all_versions"] = list(set(ds_vers))
    export_to_datasets["all_releases"] = releases
    
    datasets_dict[dataset] = export_to_datasets

#%% write back to datasets.json
datasets_json_path = datasets_repo_path / "datasets.json"
with open(datasets_json_path, "w") as f:
    json.dump(datasets_dict, f, indent=4)



#%% [Step 2] Summarize all releases from datasets
# For each dataset, read the version file to determine which release it belongs to.  Then
# collate all datasets by release, and print a summary of which datasets belong to which releases, along with their DOI and reference file status.
# e.g.
    # "alessi-invitro-ms-p-hek293-gtip": {
    #     "name": "alessi-invitro-ms-p-hek293-gtip",
    #     "title": "team-alessi-invitro-ms-p-hek293-gtip",
    #     "description": "proteomics dataset from team-alessi",
    #     "version": "v1.1",
    #     "doi": "10.5281/zenodo.17355407",
    #     "releases": ["v4.0.2"],
    #     "current_release": "v4.0.2"
    #     "authors": ["alessi"],
    # }

releases = {}
for dataset, ds_info in datasets.items():
    # load dataset.json into Dataset model
    ds_path = datasets_repo_path / "datasets" / dataset
    dataset_model = ao.Dataset.load(ds_path)
    release = ds_info.get("release", [])
    if not release:
        print(f"WARNING: no release information found for dataset {dataset} in {datasets_json_path}")
    for release_ver in release:



        if release_ver not in releases:
            releases[release_ver] = {}
        releases[release_ver].append(dataset)






for dataset in all_datasets:
    # find the ref name for ingest
    # print(f"Processing {dataset}")
    ds_path = datasets_repo_path / "datasets" / dataset
    if not ds_path.exists():
        # dataset is missing
        print(f"missing dataset: {dataset} at expected path: {ds_path}")
 

# %%
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

# # %% [Step 3] Re-Ingest DOI reference documents
# Place the team-supplied .docx reference file in <name>/refs/ first, then
# run this cell to populate DOI/<name>.json, project.json, and the README.
#
# Update the filename in `ref_doc` for each dataset as needed.
# %%

# datasets = [
#     # "voet-pmdbs-sn-atacseq-scalebio-hydrop", # 20076952
#     # "voet-pmdbs-sn-atacseq-10x", # 20077637
#     # "voet-pmdbs-sn-atacseq-hydrop", # 20077714
#     # "voet-pmdbs-sn-multimodal",     # 20078306
#     # "scherzer-pmdbs-lr-wgs" # 20078329
#     ]
zenodo = ao.setup_zenodo()

# %%


for ds in datasets:
    ds_path = datasets_repo_path / "WIP" / ds
    # TODO: update the filename to match the actual reference document
    
    # confirm we have v0.1
    # read version
    current_version = (ds_path / "version").read_text().strip()
    if current_version != "0.1":
        print(f"WARNING: expected version 0.1 for {ds}, but found {current_version}")
        continue


    # find the refs.docx
    ref_path = ds_path / "refs"
    if len(list(ref_path.glob("*.docx"))) == 1:
        ref_doc = list(ref_path.glob("*.docx"))[0]
    else:
        print(f"WARNING: expected exactly 1 .docx file in {ref_path}, but found {len(list(ref_path.glob('*.docx')))}")
        ref_doc = list(ref_path.glob("*.docx"))[1] # only voet-lr-wgs has 2 .docx files, so this is a temporary workaround.  Please rename the correct ref doc to avoid this in the future.

    v1_beta_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    if not v1_beta_doi_id:
        print(f"WARNING: no DOI found for {ds} at v0.1 after ingestion")
        continue
    else:        
        print(f"Found DOI for {ds} at v0.1: {v1_beta_doi_id}")

    # assert v1.0
    ds_version = "1.0"
    # write version
    ao.write_version(ds_version, ds_path / "version")

    ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE)
    print(f"DOI info ingested: {ds}")

    # load deposition 
    # bump version


    # defensive / pause
    zenodo.set_deposition_id(v1_beta_doi_id)
    deposition = ao.bump_doi_version(zenodo, v1_beta_doi_id)

    new_doi_id = f"{deposition['id']}"
    print(f"Bumped DOI for {ds} to v1.0: {new_doi_id}")

    # update v1.0
    metadata = deposition.get("metadata")
    metadata['version'] = '1.0'
    deposition = ao.update_doi_metadata(zenodo, new_doi_id, metadata)

    # defensive / pause
    zenodo.set_deposition_id(new_doi_id)

    file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"
    # deposition = update_doi_metadata(zenodo, v1_beta_doi_id, metadata)
    deposition = ao.add_anchor_file_to_doi(zenodo,  file_path, new_doi_id)

    deposition = zenodo.deposition
    

    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)

# %%

# # remake v1 pdf
datasets = [
    "voet-pmdbs-sn-rnaseq-parsebio",
    "scherzer-pmdbs-sn-rnaseq-midbrain-hybsel",
   "voet-pmdbs-sn-rnaseq",
   "voet-pmdbs-sn-atacseq-scalebio-10x",
]

for ds in datasets:
    ds_path = datasets_repo_path / "WIP" / ds
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


    # defensive / pause
    zenodo.set_deposition_id(v1_doi_id)

    file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"
    # deposition = update_doi_metadata(zenodo, v1_beta_doi_id, metadata)
    deposition = ao.add_anchor_file_to_doi(zenodo,  file_path, new_doi_id)

    deposition = zenodo.deposition
    
    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)




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


####################
# %% [Step 67] publish DOI and move WIP dataset tree to cloud-datasets root

for ds in datasets:
    ds_path = datasets_repo_path / "WIP" / ds
    # TODO: update the filename to match the actual reference document
    doi_id = ao.get_doi_from_dataset(ds_path, version=True)
    deposition = zenodo.get_deposition(doi_id)


    deposition = ao.publish_doi(zenodo, doi_id)
    ao.archive_deposition_local(ds_path, "final-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)

    # move WIP to datasets/
    final_ds_path = datasets_repo_path / "datasets" / ds
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

