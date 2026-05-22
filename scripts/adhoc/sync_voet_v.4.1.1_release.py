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
import json
import shutil

# TODO: confirm the root path resolves correctly for your environment
root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"
collections_repo_path = root_path / "cloud-collections"
releases_repo_path = root_path / "cloud-releases"
metadata_repo_path = root_path / "asap-crn-cloud-dataset-metadata"

%load_ext autoreload
%autoreload 2

# %% [Step 1] Release parameters

PUBLICATION_DATE = "2026-05-31"   # e.g. "2026-05-01"
CDE_VERSION = "v4.4"              # e.g. "v3.3"


# %% [Step 2] Define datasets NEW or VERSION-BUMPED in this release
# Each entry needs a published (or pre-reserved) Zenodo DOI.
# Use version="v1.0" for datasets being released for the first time (promoted
# from WIP v0.1).  Use the new bumped version for datasets being re-released.
# v1.0 datasets, v4.3 cde
new_datasets = [
    "voet-pmdbs-sn-atacseq-10x",
    "voet-pmdbs-sn-atacseq-hydrop",
    "voet-pmdbs-sn-atacseq-scalebio-10x",
    "voet-pmdbs-sn-atacseq-scalebio-hydrop",
    "voet-pmdbs-sn-multimodal",
    "voet-pmdbs-sn-rnaseq",
    "voet-pmdbs-sn-rnaseq-parsebio",
    "scherzer-pmdbs-sn-rnaseq-midbrain-hybsel",
    "scherzer-pmdbs-lr-wgs"
    ]

# %%
zenodo = ao.setup_zenodo()

# %%

for ds in new_datasets:
    ds_path = datasets_repo_path / "WIP" / ds
    # TODO: update the filename to match the actual reference document
    
    # confirm we have v0.1
    # read version
    current_version = (ds_path / "version").read_text().strip()
    if current_version != "0.1":
        print(f"WARNING: expected version 0.1 for {ds}, but found {current_version}")

    # find the refs.docx
    ref_path = ds_path / "refs"
    if len(list(ref_path.glob("*.docx"))) == 1:
        ref_doc = list(ref_path.glob("*.docx"))[0]
    else:
        print(f"WARNING: expected exactly 1 .docx file in {ref_path}, but found {len(list(ref_path.glob('*.docx')))}")
        ref_doc = list(ref_path.glob("*.docx"))[1] # only voet-lr-wgs has 2 .docx files, so this is a temporary workaround.  Please rename the correct ref doc to avoid this in the future.

    v1_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    if not v1_doi_id:
        print(f"WARNING: no DOI found for {ds} at v1.0 after ingestion")
        continue
    else:        
        print(f"Found DOI for {ds} at v0.1: {v1_doi_id}")

    # assert v1.0
    ds_version = "1.0"
    # write version
    ao.write_version(ds_version, ds_path / "version")

    ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE)
    print(f"DOI info ingested: {ds}")

    # load deposition 
    # bump version
    # defensive / pause
    zenodo.set_deposition_id(v1_doi_id)
    deposition = zenodo.deposition

    file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"
    deposition = ao.add_anchor_file_to_doi(zenodo,  file_path, v1_doi_id)

    deposition = zenodo.deposition
    

    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition, prerelease=True)

# %%


# copy DOI/ and refs/ to datasets_repo_path / "WIP"
for ds in new_datasets:
    ds_path = metadata_repo_path / "datasets" / ds
    wip_path = datasets_repo_path / "WIP" / ds
    for item in ["DOI", "refs", "version"]:
        source_subdir = wip_path / item
        target_subdir = ds_path / item
        # print(f"copying {source_subdir} to {target_subdir}")
        if source_subdir.is_dir():
            shutil.copytree(source_subdir, target_subdir, dirs_exist_ok=True)
        elif source_subdir.is_file():
            shutil.copy2(source_subdir, target_subdir)
        else:
            print(f"Warning: {source_subdir} does not exist in source for {ds}")




# # %%
# new_dataset_defs = []
# # copy DOI/ and refs/ to datasets_repo_path / "WIP"
# for ds in new_datasets:
#     ds_path = metadata_repo_path / "datasets" / ds
#     wip_path = datasets_repo_path / "WIP" / ds
#     for item in ["DOI", "refs", "version"]:
#         source_subdir = ds_path / item
#         target_subdir = wip_path / item

#         # copy from datasets/ WIP to metadata repo
#         for item in ["DOI", "refs"]:
#             target_subdir = ds_path / item
#             source_subdir = wip_path / item
#             if source_subdir.is_dir():
#                 shutil.copytree(source_subdir, target_subdir, dirs_exist_ok=True)
#             elif source_subdir.is_file():
#                 shutil.copy2(source_subdir, target_subdir)
#             else:
#                 print(f"Warning: {source_subdir} does not exist in source for {ds}")


# %%
for ds in new_datasets:
    ds_path = datasets_repo_path / "WIP" / ds
    # TODO: update the filename to match the actual reference document
    
    v1_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    if not v1_doi_id:
        print(f"WARNING: no DOI found for {ds} at v1.0 after ingestion")
        continue
    else:        
        print(f"Found DOI for {ds} at v0.1: {v1_doi_id}")

    # defensive / pause
    zenodo.set_deposition_id(v1_doi_id)

    file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"

    # deposition = ao.add_anchor_file_to_doi(zenodo,  file_path, v1_doi_id)
    deposition = zenodo.deposition

    print(f"DOI info ingested: {ds}")
    print(f"README file: {file_path}")
    print(f"DOI: {v1_doi_id}, deposition: {deposition.get('title')}")

    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition, prerelease=True)


# %%
