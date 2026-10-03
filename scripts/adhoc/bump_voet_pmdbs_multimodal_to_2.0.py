# # ASAP CRN — New WIP Dataset Acceptance Template
#
# ** add v0.1->v1.0 DOI EXAMPLE **
#   1. Ingest DOI reference `.docx` files to generate Zenodo metadata
#   2. Create Zenodo draft DOIs at `v0.1`
#        - update zenodo metadata
#        - upload README .pdf
#        - publish
#   3. add v1.0 DOI 
#        - re-Ingest DOI reference `.docx` files to generate Zenodo metadata
#        - "bumnp" DOI from v0.l1 to v1.0 
#         - sync new README.dpf 
#   4. publish v1.0 DOI EXAMPLE
#

# DO NOT EXECUTE THIS FILE DIRECTLY — it is a template only.

# %% Setup
from pathlib import Path
import asap_orchestrator as ao
import json
import shutil

%load_ext autoreload
%autoreload 2

# TODO: confirm the root path resolves correctly for your environment
root_path = Path(__file__).resolve().parents[3]
datasets_repo_path = root_path / "cloud-datasets"


# %%
PUBLICATION_DATE = "2026-09-30"   # e.g. "2026-05-01"

dataset_names = [
    "voet-pmdbs-sn-multimodal"
]

 
# %% 
# add message:  

add_message = f"""
This v2.0 Dataset reflects fixing some metadata encoding erros of fastq file names."""



# %%
# STEP 1:
#        make v1.0 archive
# STEP 2:
#        read v1.0 DOI
# STEP 3:
#        bump v1.0 DOI
#        add "v2.0" message
#        add v2.0 DOI
# STEP 4:
#        publish v2.0 DOI



# %%
def append_message_to_dataset_json(ds_path, message):
    """
    adds a message to the project.json file which captures details of the version bump
    
    """
    # load project.json
    project_json_path = ds_path / "DOI" / f"project.json"
    with open(project_json_path, "r") as f:
        project_json = json.load(f)


    # sanitize message
    message = message.replace("\n", " ")
    message = message.strip()
    message = f"\n\n{message}"
    # add message
    project_json["dataset_description"] += message


    # save project.json
    with open(project_json_path, "w") as f:
        json.dump(project_json, f, indent=2)




# %%
# step 1: sync v1.0 archive

for ds_def in dataset_names:
    ds_path = datasets_repo_path / "datasets" / ds_def
    if not ds_path.exists():
        # Dataset may still be under WIP/ — promote it first
        print(f"WARNING: dataset directory not found: {ds_def}")
        continue
    # copy files to archive
    
    current_version = (ds_path/"version").read_text().strip()
    arch_path = ds_path / f"archive/v{current_version}/"

    print(f"  [{ds_def}] copy files to archive: {arch_path}")
    # copy DOI
    shutil.copytree(ds_path / "DOI", arch_path / "DOI", dirs_exist_ok=True)
    # copy refs
    shutil.copytree(ds_path / "refs", arch_path / "refs", dirs_exist_ok=True)
    # copy version
    shutil.copy2(ds_path / "version", arch_path / "version")
    # copy dataset.json
    shutil.copy2(ds_path / "dataset.json", arch_path / "dataset.json")

# initialize the v2.0 DOI, bump version, re-upload
# %%

zenodo = ao.setup_zenodo()

bump_version = "2.0"
for ds_def in dataset_names:
    ds_path = datasets_repo_path / "datasets" / ds_def
    readme_pdf = ds_path / "DOI" / f"{ds_def}_README.pdf"
    doi_id = ao.get_doi_from_dataset(ds_path, version=True)

        
    print(f"v1.0: {ds_def}: {doi_id}")
    zenodo.set_deposition_id(doi_id)
    deposition = zenodo.deposition
    ao.archive_deposition_local(ds_path, "v1.0-deposition", deposition)

# %%.  [Step 3] - v1.0 DOI creation
# initialize the v1.0 DOI, bump version, re-uploade


for ds_def in dataset_names:
    ds_path = datasets_repo_path / "datasets" / ds_def
    readme_pdf = ds_path / "DOI" / f"{ds_def}_README.pdf"
    og_data_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    docs = ds_path / "refs"
    for doc in docs.iterdir():
        if doc.suffix == ".docx":
            ref_doc = doc
            break
    else:
        print(f"WARNING: no .docx file found in {docs}")
        continue

    # bump to v2.0
    append_message_to_dataset_json(ds_path, add_message)
    ao.write_version("2.0", ds_path / "version")
    # re-ingest docx to update the Zenodo metadata for v1.0
    ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE, force=False)

    zenodo.set_deposition_id(og_data_doi_id)
    deposition = ao.bump_doi_version(zenodo, og_data_doi_id)
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

    # had to do this by hand
    # # updated metadata
    # metadata = deposition.get("metadata")
    # metadata['version'] = '2.0'
    # deposition = ao.update_doi_metadata(zenodo, new_doi_id, metadata)
    # print(f"Updated DOI for {ds_def}: {new_doi_id}")

    ao.finalize_DOI(ds_path, deposition, prerelease=True)
    # archive deposition
    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)


    
# %%  
# %%.  [Step 4] -  publish v2.0 dataset doi with release
zenodo = ao.setup_zenodo()

for ds_def in add_dataset_defs:
    ds_path = datasets_repo_path / "datasets" / ds_def
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

