# %% [markdown]
# # ASAP CRN — New WIP Dataset Acceptance Template
#
# Copy this file and rename it, e.g. `add_v4.1.0_datasets.py`.
# Fill in every section marked with TODO before running cell by cell.
#
# **Lifecycle covered here:**
#   1. Define dataset metadata (name, collection, CDE version, buckets)
#   2. Create `dataset.json` stubs in `cloud-datasets/WIP/`
#   3. Ingest DOI reference `.docx` files to generate Zenodo metadata
#   4. Create Zenodo draft DOIs at `v0.1`
#
# DO NOT EXECUTE THIS FILE DIRECTLY — it is a template only.

# %% Setup
from pathlib import Path
import asap_orchestrator as ao
import json

%load_ext autoreload
%autoreload 2

# TODO: confirm the root path resolves correctly for your environment
root_path = Path(__file__).resolve().parents[3]
datasets_repo_path = root_path / "cloud-datasets"

# %% [Step 1] Release parameters
# TODO: set the publication date and CDE version for this acceptance tranche
# guess for now.. 

PUBLICATION_DATE = "2026-08-31"   #
CDE_VERSION = "v4.5"              # TBD

# %% [Step 2] Define the datasets being accepted
# Each ao.define_dataset() call describes one team-contributed dataset.
# `collection` is the curated collection name (e.g. "pmdbs-sc-rnaseq") or
# None for uncurated/urgent datasets that go straight into a release without
# a collection version bump.
#
# Bucket names are inferred from `name` automatically:
#   raw:  gs://asap-raw-<name>
#   dev:  gs://asap-dev-<name>
#   uat:  gs://asap-uat-<name>
#   prod: gs://asap-curated-<name>
# Override `buckets=` if the actual bucket names differ.

add_dataset_defs = [
    'scherzer-pmdbs-sn-multiome-midbrain',
    'scherzer-pmdbs-sn-rnaseq-midbrain',
]

# %% [Step 3] Create dataset stubs in `cloud-datasets/WIP/`
# Run this cell to create the dataset stubs in the WIP bucket.

ds_path = datasets_repo_path / "WIP" / add_dataset_defs[1]
doi_path = ds_path / "DOI"
if not doi_path.exists():
    doi_path.mkdir(parents=True, exist_ok=True)

ref_path = ds_path / "refs"
if not ref_path.exists(): # 
    ref_path.mkdir(parents=True, exist_ok=True)



# %%



# %% [Step 1]  Ingest DOI reference documents
# Place the team-supplied .docx reference file in <name>/refs/ first, then
# run this cell to populate DOI/<name>.json, project.json, and the README.
#
# Update the filename in `ref_doc` for each dataset as needed.


for ds_def in add_dataset_defs:
    ds_path = datasets_repo_path / "WIP" / ds_def
    # TODO: update the filename to match the actual reference document
    # check the refs/ path for any docx documents
    docs = ds_path / "refs"
    for doc in docs.iterdir():
        if doc.suffix == ".docx":
            ref_doc = doc
            break
    else:
        print(f"WARNING: no .docx file found in {docs}")
        continue


    #  force v0.1
    # # write the v0.1 version file
    # (ds_path / "version").write_text("0.1")
    ao.write_version("0.1", ds_path / "version")

    # SETUP DOI INFO
    # setup_DOI_info calls two functions:
    #.   ingest_DOI_doc - which parses the .docx file, creates the "project.json",
    #     make_readme_file - which creates the .md and pdf file from the project.json file
    if ref_doc.exists():
        ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE, force=True)
        print(f"DOI info ingested: {ds_def}")
    else:
        print(f"WARNING: ref doc not found — place it at {ref_doc}")


# %% [Step 2] Create Zenodo draft DOIs (v0.1)
# Requires ZENODO_TOKEN (or ZENODO_SANDBOX_TOKEN) set in your environment.
# Each dataset gets a new Zenodo deposition draft; the concept DOI is written
# back to dataset.json and DOI/dataset.doi.

zenodo = ao.setup_zenodo()

# %%
# we already have the first 0.1 doi created and published.
ds_def = add_dataset_defs[1]
ds_path = datasets_repo_path / "WIP" / ds_def
deposition,metadata = ao.create_draft_doi(
    zenodo, ds_path, version="v0.1", 
)
doi = deposition.get("doi") or deposition.get("metadata", {}).get("prereserve_doi", {}).get("doi", "draft")
print(f"{ds_def}: {doi}")


# scherzer-pmdbs-sn-rnaseq-midbrain: 10.5281/zenodo.22218189

# %% [Step 2, continued] Upload README anchor file to each draft
# Uploads the generated <name>_README.pdf as the anchor file for each DOI.


readme_pdf = ds_path / "DOI" / f"{ds_def}_README.pdf"
doi_id = ao.get_doi_from_dataset(ds_path, version=True)

print(f"{ds_def}: ||| {doi_id}")

if readme_pdf.exists():
    deposition = ao.add_anchor_file_to_doi(zenodo, readme_pdf, doi_id)
    print(f"Uploaded README: {ds_def}")
    ao.finalize_DOI(ds_path, deposition, prerelease=True)

else:
    print(f"WARNING: README PDF not found for {ds_def}")


# %% [Step 2, continued]
# publish 0.1 
##. warning this step might need to be currently performed by hand.  
#   (It is currently performed by hand via the "Cloud Team" community)    

zenodo = ao.setup_zenodo()

ds_def = add_dataset_defs[1]
ds_path = datasets_repo_path / "WIP" / ds_def

ds_path = datasets_repo_path / "WIP" / ds_def
readme_pdf = ds_path / "DOI" / f"{ds_def}_README.pdf"
beta_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

print(f"BETA: {ds_def}: {beta_doi_id}")
zenodo.set_deposition_id(beta_doi_id)
deposition = zenodo.deposition

# something has changed in the Zenodo API,
#. publish_doi seems to be stuck. .. might have just been an ORCID issue
deposition = ao.publish_doi(zenodo, beta_doi_id)

# archive deposition
ao.archive_deposition_local(ds_path, "v0.1-deposition", deposition)

# %%.  [Step 3] - v1.0 DOI creation
# initialize the v1.0 DOI, bump version, re-uploade

for ds_def in add_dataset_defs:
    ds_path = datasets_repo_path / "WIP" / ds_def
    readme_pdf = ds_path / "DOI" / f"{ds_def}_README.pdf"
    beta_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    docs = ds_path / "refs"
    for doc in docs.iterdir():
        if doc.suffix == ".docx":
            ref_doc = doc
            break
    else:
        print(f"WARNING: no .docx file found in {docs}")
        continue


    # bump to v1.0
    ao.write_version("1.0", ds_path / "version")
    # re-ingest docx to update the Zenodo metadata for v1.0
    ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE, force=True)

    zenodo.set_deposition_id(beta_doi_id)
    deposition = ao.bump_doi_version(zenodo, beta_doi_id)
    metadata = deposition.get("metadata")
    new_doi_id = f"{deposition['id']}"


    print(f"NEW:  {ds_def}: ||| {new_doi_id}")
    readme_pdf = ds_path / "DOI" / f"{ds_def}_README.pdf"

    # %%.  [Step 4] - v1.0 DOI creation
    # initialize the v1.0 DOI

    if readme_pdf.exists():
        # not sure why this fails... seems that the REST API has changed behavior
        deposition = ao.replace_anchor_file_in_doi(zenodo, ds_path, new_doi_id, readme_pdf)
        print(f"Uploaded README: {ds_def}")

    else:
        print(f"WARNING: README PDF not found for {ds_def}")


    ao.finalize_DOI(ds_path, deposition, prerelease=True)
    # archive deposition
    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)


    
# %%  
# %%.  [Step 4] -  publish v1.0 dataset doi with release
zenodo = ao.setup_zenodo()

for ds_def in add_dataset_defs:
    ds_path = datasets_repo_path / "WIP" / ds_def
    readme_pdf = ds_path / "DOI" / f"{ds_def}_README.pdf"
    doi_id = ao.get_doi_from_dataset(ds_path, version=True)

        
    print(f"release: {ds_def}: {doi_id}")
    zenodo.set_deposition_id(doi_id)
    deposition = zenodo.deposition
    deposition = ao.publish_doi(zenodo, doi_id)
    
    # archive deposition
    ao.archive_deposition_local(ds_path, "final-deposition", deposition)

# %%
# NOTE:  above still assumes that the artefacts are in the WIP/<dataset_name> path.