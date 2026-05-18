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

# TODO: confirm the root path resolves correctly for your environment
root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"

# %% [Step 1] Release parameters
# TODO: set the publication date and CDE version for this acceptance tranche
# guess for now.. 

PUBLICATION_DATE = "2026-05-18"   # e.g. "2026-05-01"
CDE_VERSION = "v4.3"              # e.g. "v3.3"

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
    "desjardins-mouse-sc-rnaseq-colon-immune-lrrk2",
    "desjardins-ipsc-sc-rnaseq-myeloid-pink1",
    "desjardins-mouse-bulk-rnaseq-striatum-pink1",
    "desjardins-mouse-bulk-rnaseq-nigra-pink1",
    "desjardins-human-pbmc-multimodal-sc-rna-tcr",
    "desjardins-mouse-sc-rnaseq-colon-immune-pink1",    


# %%

for ds in add_dataset_defs:
    ds_model = ao.define_dataset(
        name=ds,           # TODO: replace
        collection=None,           # TODO: replace, or None
        cde_version=CDE_VERSION,
        title="",  # TODO: replace
        description="",  # TODO: replace
    )
    # Create WIP stubs in cloud-datasets/WIP/
    # Creates <name>/dataset.json, <name>/DOI/, and <name>/refs/ for each dataset.
    ds_path = ao.create_dataset_stub(ds_model, datasets_repo_path, wip=True)
    print(f"Created: {ds_path}")




# %%



# %% [Step 4] Ingest DOI reference documents
# Place the team-supplied .docx reference file in <name>/refs/ first, then
# run this cell to populate DOI/<name>.json, project.json, and the README.
#
# Update the filename in `ref_doc` for each dataset as needed.

new_dataset_defs = []
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

    # this should get made automatically by create_dataset_stub
    # # write the v0.1 version file
    # (ds_path / "version").write_text("v0.1")

    if ref_doc.exists():
        ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE)
        print(f"DOI info ingested: {ds_def}")
    else:
        print(f"WARNING: ref doc not found — place it at {ref_doc}")

    ds_def = ao.Dataset.load(ds_path)
    new_dataset_defs.append(ds_def)

# %% [Step 5] Create Zenodo draft DOIs (v0.1)
# Requires ZENODO_TOKEN (or ZENODO_SANDBOX_TOKEN) set in your environment.
# Each dataset gets a new Zenodo deposition draft; the concept DOI is written
# back to dataset.json and DOI/dataset.doi.

zenodo = ao.setup_zenodo()

# %%
for ds_def in new_dataset_defs:
    ds_path = datasets_repo_path / "WIP" / ds_def.name
    deposition = ao.create_dataset_doi(
        ds_path, zenodo, version="v0.1", publication_date=PUBLICATION_DATE
    )
    doi = deposition.get("doi") or deposition.get("metadata", {}).get("prereserve_doi", {}).get("doi", "draft")
    print(f"{ds_def.name}: {doi}")


# desjardins-mouse-sc-rnaseq-colon-immune-lrrk2: 10.5281/zenodo.20276410
# desjardins-ipsc-sc-rnaseq-myeloid-pink1: 10.5281/zenodo.20276412
# desjardins-mouse-bulk-rnaseq-striatum-pink1: 10.5281/zenodo.20276414
# desjardins-mouse-bulk-rnaseq-nigra-pink1: 10.5281/zenodo.20276416
# desjardins-human-pbmc-multimodal-sc-rna-tcr: 10.5281/zenodo.20276418
# desjardins-mouse-sc-rnaseq-colon-immune-pink1: 10.5281/zenodo.20276571

# %% [Step 6] (Optional) Upload README anchor file to each draft
# Uploads the generated <name>_README.pdf as the anchor file for each DOI.

for ds_def in new_dataset_defs:
    ds_path = datasets_repo_path / "WIP" / ds_def.name
    readme_pdf = ds_path / "DOI" / f"{ds_def.name}_README.pdf"
    doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    print(f"{ds_def.name}: {ds_def.doi} ||| {doi_id}")

    if readme_pdf.exists():
        deposition = ao.add_anchor_file_to_doi(zenodo, readme_pdf, doi_id)
        print(f"Uploaded README: {ds_def.name}")
        ao.finalize_DOI(ds_path, deposition, prerelease=True)

    else:
        print(f"WARNING: README PDF not found for {ds_def.name}")


# # %%
# # publish 0.1 and initialize the v1.0 DOI
# for ds_def in new_dataset_defs:
#     ds_path = datasets_repo_path / "WIP" / ds_def.name
#     readme_pdf = ds_path / "DOI" / f"{ds_def.name}_README.pdf"
#     doi_id = ao.get_doi_from_dataset(ds_path, version=True)

#     print(f"{ds_def.name}: {ds_def.doi} ||| {doi_id}")

#     if readme_pdf.exists():
#         deposition = ao.add_anchor_file_to_doi(zenodo, readme_pdf, doi_id)
#         print(f"Uploaded README: {ds_def.name}")
#         ao.finalize_DOI(ds_path, deposition, prerelease=True)

#     else:
#         print(f"WARNING: README PDF not found for {ds_def.name}")


# %%
