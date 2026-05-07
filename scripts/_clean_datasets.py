
# # ASAP CRN — fix cloud-datasets repo
# ensure version files
# make sure archives are complete
# 21 May 2026
# Andy Henrie
# DO NOT EXECUTE


#
# %%
# %% Setup
from pathlib import Path
import asap_orchestrator as ao
from asap_orchestrator.doi import bump_doi_version

import json
import shutil
# TODO: confirm the root path resolves correctly for your environment

%load_ext autoreload
%autoreload 2
# 

root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"

# %% [Step 1] get all datasets in cloud-datasets/datasets

datasets = [
    d.name
    for d in (datasets_repo_path / "datasets").iterdir()
    if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
]

# confirm whats missing
datasets_file = datasets_repo_path / "datasets.json"
with open(datasets_file) as f:
    json_datasets = json.load(f)

datasets_in_json = set(json_datasets.keys())

set(datasets) - datasets_in_json
# %% [Step 2] ensure version files are present and in sync with dataset.json

for ds in datasets:
    ds_path = datasets_repo_path / "datasets" / ds
    dj_path = ds_path / "dataset.json"
    vf_path = ds_path / "version"

    with open(dj_path) as f:
        dj = json.load(f)

    dj_version = dj.get("version", "").strip().lstrip("v")
    if not vf_path.exists():
        # No version file — create from dataset.json
        print(f"  [{ds}] create version file: {dj_version}")
        vf_path.write_text(dj_version + "\n")

    else:
        current_version = vf_path.read_text().strip()
        if dj_version != current_version:
            # force dataset.json to match version file (since version file is the source of truth for releases)
            new_dj_version = current_version
            print(
                f"  [{ds}] version mismatch — "
                f"version_file={current_version!r}, dataset.json={dj_version!r} "
                f"→ updating dataset.json to {new_dj_version}"
            )
            dj["version"] = new_dj_version
            with open(dj_path, "w") as f:
                json.dump(dj, f, indent=4)
                f.write("\n") # do i need this?


# %%
# %% [Step 3] ensure each dataset has an archive directory with expected files

for ds in datasets:
    ds_path = datasets_repo_path / "datasets" / ds
    archive_path = ds_path / "archive"
    if not archive_path.exists():
        print(f"  [{ds}] create archive directory")
        archive_path.mkdir(parents=True, exist_ok=True)

    # load dataset.json to confirm expected archive files
    dj_path = ds_path / "dataset.json"
    with open(dj_path) as f:
        dj = json.load(f)
    releases = dj.get("releases", {})

    # find all release versions and identify the latest one.
    release_versions = []
    for rel_key, rel_data in releases.items():
        dv = rel_data.get("dataset_version", "").strip().lstrip("v")
        if dv:
            release_versions.append(dv)
    if release_versions:
        latest_release_version = max(release_versions)  # assumes semantic versioning that sorts correctly as strings
        expected_archive = archive_path / f"v{latest_release_version}"
        if not expected_archive.exists():
            print(f"  [{ds}] missing archive for latest release version {latest_release_version} — creating {expected_archive}")
            expected_archive.mkdir(parents=True, exist_ok=True)
            # copy DOI/ refs/ dataset.json, version files into archive from ds_path/
            for item in ["dataset.json", "version", "DOI", "refs"]:
                src = ds_path / item
                dst = expected_archive / item
                if src.exists():
                    if src.is_dir():
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                else:
                    print(f"  [{ds}] warning: expected {src} does not exist; skipping copy to archive")
    

    for release_version, release_info in releases.items():
        # check if latest_release

        # check if all release version have corresponding archive folders
        dataset_version = release_info.get("dataset_version", "").strip().lstrip("v") # defensive
        expected_archive = archive_path / f"v{dataset_version}"
        if not expected_archive.exists():
            print(f"  [{ds}] missing archive for dataset ver: {release_version} — creating {expected_archive}")
            expected_archive.mkdir(parents=True, exist_ok=True)
            # copy DOI/ refs/ dataset.json, version files into archive from ds_path/
            for item in ["dataset.json", "version", "DOI", "refs"]:
                src = ds_path / item
                dst = expected_archive / item
                if src.exists():
                    if src.is_dir():
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                else:
                    print(f"  [{ds}] warning: expected {src} does not exist; skipping copy to archive")
        else:
            # optionally, check for expected files within each archive (e.g. dataset.json, version, DOI/ and refs/
            # 
            # 
           
            expected_files = ["dataset.json", "version", "DOI", "refs"]
            for item in expected_files:
                item_path = expected_archive / item
                if not item_path.exists():
                    print(f"  [{ds}] warning: expected {item_path} does not exist in archive for dataset ver: {dataset_version}")
                    # copy from ds_path/ if it exists
                    src = ds_path / item
                    dst = item_path
                    if src.exists():
                        if src.is_dir():
                            shutil.copytree(src, dst)
                        else:
                            shutil.copy2(src, dst)
                    else:
                        print(f"  [{ds}] warning: expected {src} does not exist; skipping copy to archive")

# %% [Step 4] ensure each dataset has a DOI directory with expected files

# %% [Step 4] ensure each dataset has a DOI directory with expected files

# %% [Step 4] ensure each dataset has a DOI directory with expected files

# %% [Step 4] ensure each dataset has a DOI directory with expected files


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

