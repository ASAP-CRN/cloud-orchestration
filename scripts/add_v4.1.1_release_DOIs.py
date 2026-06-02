
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

    # make sure we are published
    deposition = ao.publish_doi(zenodo, v1_beta_doi_id)


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
    if file_path.exists():
        # not sure why this fails... seems that the REST API has changed behavior
        deposition = ao.replace_anchor_file_in_doi(zenodo, ds_path, new_doi_id, file_path)
        print(f"Uploaded README: {ds_path.name}")

    else:
        print(f"WARNING: README PDF not found for {ds_path.name}")

    deposition = zenodo.deposition
    

    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)

# %%

####################
# create dataset.json . 

# %%


for ds in datasets:
    ds_path = datasets_repo_path / "WIP" / ds


    ds_model = ao.define_dataset(
        name=ds,           # TODO: replace
        collection=None,           # TODO: replace, or None
        cde_version=CDE_VERSION,
        title="",  # TODO: replace
        description="",  # TODO: replace
    )
    ds_path = datasets_repo_path / "WIP" / ds
    ds_model.save(ds_path)



# %%
# create this now even thouth we'll re-make it later.
new_dataset_defs = []
for ds in datasets:
    ds_path = datasets_repo_path / "WIP" / ds

    ds_in = ao.Dataset.load(ds_path)
    ds_def = ao.fill_dataset_stub(ds_in,ds_path)


    ds_def.save(ds_path)

    new_dataset_defs.append(ds_def)
    
# %%    




# %%
# move below to part of a release script
# # %%
zenodo = ao.setup_zenodo()

for ds_def in new_dataset_defs:
    ds_path = datasets_repo_path / "WIP" / ds_def.name
    readme_pdf = ds_path / "DOI" / f"{ds_def.name}_README.pdf"
    doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    print(f"NEW:  {ds_def.name}: {ds_def.doi} ||| {doi_id}")
    readme_pdf = ds_path / "DOI" / f"{ds_def.name}_README.pdf"

    if readme_pdf.exists():
        # not sure why this fails... seems that the REST API has changed behavior
        deposition = ao.replace_anchor_file_in_doi(zenodo, ds_path, doi_id, readme_pdf)
        print(f"Uploaded README: {ds_def.name}")

        ao.finalize_DOI(ds_path, deposition, prerelease=True)
        # archive deposition
        ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)

    else:
        print(f"WARNING: README PDF not found for {ds_def.name}")



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