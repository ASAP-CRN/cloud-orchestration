# # ASAP CRN — New WIP Dataset Acceptance Template
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

PUBLICATION_DATE = "2026-07-29"   # e.g. "2026-05-01"
CDE_VERSION = "v4.4"  # actually have no ideal 

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
    "biederer-pmdbs-spatial-geomx-lamda",
    "biederer-mouse-spatial-geomx-lamda"
]

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
from asap_orchestrator.dataset import update_dataset_doi
from asap_orchestrator.doi import _make_metadata_from_project
import docx
import os
import json 
from markdown import markdown
import pandas as pd

# %%
# need to run this section for each dataset
dataset_name = "biederer-pmdbs-spatial-geomx-lamda"
dataset_name =   "biederer-mouse-spatial-geomx-lamda"

ds_path = datasets_repo_path / "WIP" / dataset_name
# TODO: update the filename to match the actual reference document
# check the refs/ path for any docx documents
docs = ds_path / "refs"
for doc in docs.iterdir():
    if doc.suffix == ".docx":
        doi_doc_path = doc

# %%
version="v0.1"
publication_date=PUBLICATION_DATE

ds_path = Path(ds_path)
doi_doc_path = Path(doi_doc_path)
long_dataset_name = ds_path.name

# just read in as text
with open(os.path.join(ds_path, "version"), "r") as f:
    ds_ver = f.read().strip()

doi_path = ds_path / "DOI"

# read the docx

# should read this from ds_path/version
# ds_ver = "v2.0"

# Load the document
document = docx.Document(doi_doc_path)

table_names = ["affiliation_header", "affiliations", "datasets", "projects", "extra1", "extra2"]
for name, table in zip(table_names, document.tables):
    # print(f"Processing table: {name}")
    table_data = []
    for row in table.rows:
        row_data = [cell.text for cell in row.cells]
        table_data.append(row_data)

    print(f"Table {name} data: {table_data}")

    # Assuming the first row is the header
    if name == "affiliation_header":
        fields = table_data[0]
        # data = table_data[1:]

    elif name == "affiliations":
        # fields = table_data[0]
        # data = table_data[1:]
        data = table_data

        # affiliations = pd.DataFrame(table_data[1:], columns=table_data[0])
        # if affiliations.shape[0] == 1:
        #     affiliations = affiliations.iloc[0, 0]

        print("made affiliation table")
    elif name == "datasets":
        dataset_title = (
            table_data[0][1].strip().replace("\n", " ").replace("\u2019", "'")
        )
        dataset_description = (
            table_data[1][1].strip().replace("\n", " ").replace("\u2019", "'")
        )
        print("got dataset title/description")
    elif name == "projects":
        project_title = (
            table_data[0][1].strip().replace("\n", " ").replace("\u2019", "'")
        )
        project_description = (
            table_data[1][1].strip().replace("\n", " ").replace("\u2019", "'")
        )
        if len(table_data) > 2:
            ASAP_team_name = table_data[2][1].strip()
        else:
            ASAP_team_name = None
        if len(table_data) > 3:
            grant_ids = table_data[3][1].strip()
        else:
            grant_ids = None

        print("got project title/description")

    else:
        # test if its the "Project Team" table
        if (
            table_data[0][1] == "First name"
            and table_data[0][2] == "Last name"
            and table_data[0][3] == "Email"
        ):
            pj_team_table = table_data
        else:
            print(f"what is this extra thing?: {name}")
            print(table_data)

# %%
# title
# string	Title of deposition (automatically set from metadata). Defaults to empty string.
title = dataset_title.strip().replace("Singel", "Single")

# upload_type  string	Yes	Controlled vocabulary:
upload_type = "dataset"

# creators
creators = []
for indiv in data:
    name = f"{indiv[0].strip()}, {indiv[1].strip()}"  # , ".join(indiv[:2])
    # hack
    name = name.replace("* Corresponding author", "")
    affiliation = indiv[2].strip()
    oricid = indiv[3].strip()

    if name == ", ":  # this should block empty names
        continue

    to_append = {"name": name}

    # hacks
    affiliation = affiliation.replace(", United States.", ".")

    if affiliation == "":
        affiliation = None
    else:
        # if there are carriage split into a lis
        if "\n" in affiliation:
            affiliation = [
                x.strip() for x in affiliation.split("\n") if x.strip() != ""
            ]
            if len(affiliation) == 1:
                affiliation = affiliation[0]
            else:
                affiliation = ",& ".join(affiliation)  # this is a hack"

        to_append["affiliation"] = affiliation

    if oricid == "":
        oricid = None
    else:
        to_append["orcid"] = oricid.lstrip("https://orcid.org/")
    creators.append(to_append)

    # creators.append({"name": name, "affiliation": affiliation, "orcid": oricid})

# description
dataset_description = dataset_description.strip()
project_description = project_description.strip()
# fix description to enable the numbered and bulletted lists...
for i in range(10):
    rep_from = f" {i}. "
    rep_to = f"\n\n{i}. "
    project_description = project_description.strip().replace(rep_from, rep_to)
    dataset_description = dataset_description.strip().replace(rep_from, rep_to)
project_description = project_description.strip().replace("* ", "\n\t* ")
dataset_description = dataset_description.strip().replace("* ", "\n\t* ")

description = f"""This Zenodo deposit contains a publicly available description of the Dataset:

**Title:** "{title}".

**Description:** {dataset_description}

--------------------------

> This dataset is made available to researchers via the ASAP CRN Cloud: [cloud.parkinsonsroadmap.org](https://cloud.parkinsonsroadmap.org). Instructions for how to request access can be found in the [User Manual](https://storage.googleapis.com/asap-public-assets/wayfinding/ASAP-CRN-Cloud-User-Manual.pdf).

> This research was funded by the Aligning Science Across Parkinson's Collaborative Research Network (ASAP CRN), through the Michael J. Fox Foundation for Parkinson's Research (MJFF).

> This Zenodo deposit was created by the ASAP CRN Cloud staff on behalf of the dataset authors. It provides a citable reference for a CRN Cloud Dataset

"""

# fill details

ASAP_lab_name = ""

# get details from the pj_team_table
field_name = [tb[0] for tb in pj_team_table]

PI_full_name = ""
PI_email = ""
submitter_name = ""
submitter_email = ""
cPI_full_name = []
cPI_email = []
for name, row in zip(field_name, pj_team_table):
    # skip if blank
    if len(row[1]) < 1:
        continue

    if name == "Principal Investigator":
        PI_full_name = f"{row[1]} {row[2]}"
        PI_email = f"{row[3]}"
    elif name == "Co-Principal Investigator":
        cPI_full_name.append(f"{row[1]} {row[2]}")
        cPI_email.append(f"{row[3]}")
    elif name == "Data Submitter":
        submitter_name = f"{row[1]} {row[2]}"
        submitter_email = f"{row[3]}"

publication_DOI = ""

print(grant_ids)
team_name = ds_path.name.split("-")[0].capitalize()

# Convert to html for good formatting
description = markdown(description)

# ASAP
communities = [{"identifier": "asaphub"}]
# version
version = ds_ver  # "2.0"?  also do "v1.0"
# license
license = {"id": "cc-by-4.0"}
refrences = [
    "Aligning Science Across Parkinson's Collaborative Research Network Cloud, https://cloud.parkinsonsroadmap.org/collections, RRID:SCR_023923",
    f"Team {team_name}",
]

# publication_date
if publication_date is None:
    publication_date = pd.Timestamp.now().strftime(
        "%Y-%m-%d"
    )  # "2.0"?  also do "v1.0"

if not pd.isna(grant_ids):
    if "," in grant_ids:
        grant_ids = grant_ids.split(",")
    elif ";" in grant_ids:
        grant_ids = grant_ids.split(";")
    else:
        grant_ids = [grant_ids]

else:
    grant_ids = None
    print("Warning: No grant ids found")
print(grant_ids)
# also dump the table to make the documents and
# ## save a simple table to update STUDY table
project_dict = {
    "project_name": f"{project_title.strip()}",  # protect the parkionson's apostrophe
    "project_description": f"{project_description.strip()}",
    "dataset_title": f"{dataset_title.strip()}",
    "dataset_description": f"{dataset_description}",
    "creators": creators,
    "publication_date": publication_date,
    "version": version,
    "title": title,
    ### add the additional stuff from the study df
    "ASAP_lab_name": ASAP_lab_name,
    "PI_full_name": PI_full_name,
    "PI_email": PI_email,
    "coPI_full_name": cPI_full_name,
    "coPI_email": cPI_email,
    "submitter_name": submitter_name,
    "submitter_email": submitter_email,
    "publication_DOI": publication_DOI,
    "grant_ids": grant_ids,
    "team_name": team_name,
}

with open(os.path.join(doi_path, f"project.json"), "w") as f:
    json.dump(project_dict, f, indent=4)

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
    # (ds_path / "version").write_text("0.1")
    ao.write_version("0.1", ds_path / "version")

    if ref_doc.exists():
        ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE, force=False)
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

    # deposition already made
    # deposition = ao.create_dataset_doi(
    #     ds_path, zenodo, version="v0.1", publication_date=PUBLICATION_DATE
    # )

    doi_id = ao.get_doi_from_dataset(ds_path, version=True)
    metadata = ao.create_draft_metadata(ds_path, version="v0.1")
    
    grants = metadata.pop("grants",None)
    if grants is not None:
        print(f"removed: {grants}")

    deposition = ao.update_dataset_doi(ds_path, zenodo, metadata)

    doi = deposition.get("doi") or deposition.get("metadata", {}).get("prereserve_doi", {}).get("doi", "draft")
    print(f"{ds_def.name}: {doi}")


# surmeier-mouse-sn-rnaseq-ventral-midbrain: 10.5281/zenodo.21308458

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

###################################################
# end here
if False:
    # %%
    new_dataset_defs = []
    for ds_def in add_dataset_defs:
        ds_path = datasets_repo_path / "WIP" / ds_def

        ds_def = ao.Dataset.load(ds_path)
        new_dataset_defs.append(ds_def)


    # %% 
    # publish 0.1 and initialize the v1.0 DOI
    #     biederer-pmdbs-spatial-geomx-lamda: 10.5281/zenodo.21727341
    # biederer-mouse-spatial-geomx-lamda: 10.5281/zenodo.21727343
    # %%
    zenodo = ao.setup_zenodo()

    # %%

    for ds_def in new_dataset_defs:

        ds_path = datasets_repo_path / "WIP" / ds_def.name
        readme_pdf = ds_path / "DOI" / f"{ds_def.name}_README.pdf"
        beta_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

        # if ds_def.name in [
        #     'desjardins-mouse-sc-rnaseq-colon-immune-lrrk2',
        #     'desjardins-mouse-sc-rnaseq-colon-immune-pink1'
        #     ]: 
        #     print(f"Skipping {ds_def.name}")
        #     continue
            
        print(f"BETA: {ds_def.name}: {ds_def.doi} ||| {beta_doi_id}")
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
        ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE)

        zenodo.set_deposition_id(beta_doi_id)
        deposition = zenodo.deposition
        deposition = ao.publish_doi(zenodo, beta_doi_id)
        
    # %%
    zenodo = ao.setup_zenodo()

    # %%
    for ds_def in new_dataset_defs:

        # if ds_def.name in [
        #     'desjardins-mouse-sc-rnaseq-colon-immune-lrrk2',
        #     ]: 
        #     print(f"Skipping {ds_def.name}")
        #     continue
        ds_path = datasets_repo_path / "WIP" / ds_def.name
        readme_pdf = ds_path / "DOI" / f"{ds_def.name}_README.pdf"
        beta_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

        zenodo.set_deposition_id(beta_doi_id)


        deposition = ao.bump_doi_version(zenodo, beta_doi_id)
        metadata = deposition.get("metadata")
        new_doi_id = f"{deposition['id']}"


        print(f"NEW:  {ds_def.name}: {ds_def.doi} ||| {new_doi_id}")
        readme_pdf = ds_path / "DOI" / f"{ds_def.name}_README.pdf"

        if readme_pdf.exists():
            # not sure why this fails... seems that the REST API has changed behavior
            deposition = ao.replace_anchor_file_in_doi(zenodo, ds_path, new_doi_id, readme_pdf)
            print(f"Uploaded README: {ds_def.name}")

        else:
            print(f"WARNING: README PDF not found for {ds_def.name}")

        ao.finalize_DOI(ds_path, deposition, prerelease=True)
        # archive deposition
        ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)


    # %%
    # %%
    for ds_def in new_dataset_defs:

        # if ds_def.name in [
        #     'desjardins-mouse-sc-rnaseq-colon-immune-lrrk2',
        #     ]: 
        #     print(f"Skipping {ds_def.name}")
        #     continue
        ds_path = datasets_repo_path / "WIP" / ds_def.name
        readme_pdf = ds_path / "DOI" / f"{ds_def.name}_README.pdf"
        doi_id = ao.get_doi_from_dataset(ds_path, version=True)

        zenodo.set_deposition_id(doi_id)
        deposition = zenodo.deposition
        metadata = deposition.get("metadata")

        # update v1.0
        metadata['version'] = '1.0'
        deposition = ao.update_doi_metadata(zenodo, doi_id, metadata)



        ao.finalize_DOI(ds_path, deposition, prerelease=True)
        # archive deposition
        ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)


    # %%

    #######################
    # %%
    new_dataset_defs = []
    for ds in add_dataset_defs:
        ds_path = datasets_repo_path / "WIP" / ds

        ds_in = ao.Dataset.load(ds_path)
        ds_def = ao.fill_dataset_stub(ds_in,ds_path)

        ds_def.save(ds_path)

        new_dataset_defs.append(ds_def)
        
    # %%    


