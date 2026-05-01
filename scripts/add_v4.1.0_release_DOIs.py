
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
import json
from pathlib import Path
import asap_orchestrator as ao
from asap_orchestrator.doi import bump_doi_version, make_readme_file

import shutil
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

# %% [Step 7] publish DOI and move WIP dataset tree to cloud-datasets root

zenodo = ao.setup_zenodo()
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


# cde v3.3
bump_datasets = [
'cohort-pmdbs-bulk-rnaseq',# v1.2.1
'cohort-pmdbs-sc-rnaseq', # v3.1.1
'hafler-pmdbs-sn-rnaseq-pfc',# v1.1
'hardy-pmdbs-bulk-rnaseq', # v1.1
'hardy-pmdbs-sn-rnaseq',# v1.1
'jakobsson-pmdbs-sn-rnaseq',# v2.1
'lee-pmdbs-bulk-rnaseq-mfg',# v1.1
'lee-pmdbs-sn-rnaseq', # v1.1
'scherzer-pmdbs-genetics',# v1.1
'scherzer-pmdbs-sn-rnaseq-mtg',# v1.2
'scherzer-pmdbs-sn-rnaseq-mtg-hybsel',# v1.2
'scherzer-pmdbs-spatial-visium-mtg',# v1.1
'sulzer-pmdbs-sn-rnaseq',# v1.1 
'wood-pmdbs-bulk-rnaseq', # v1.1 
]
PUBLICATION_DATE = "2026-04-30"   # e.g. "2026-05-01"
CDE_VERSION = "v3.3"              # e.g. "v3.3"

zenodo = ao.setup_zenodo()

for ds in bump_datasets[11:]:
    ds_path = datasets_repo_path / ds
    # TODO: update the filename to match the actual reference document
    version = False if "cohort" in ds else True
    current_doi_id = ao.get_doi_from_dataset(ds_path, version=version)
    deposition = zenodo.get_deposition(current_doi_id)



    # check if we have a final deposition already for this dataset, if not we should save it
    final_deposition_path = ds_path / "DOI" / "final-deposition.json"
    if not final_deposition_path.exists():
        ao.archive_deposition_local(ds_path, "final-deposition", deposition)

    # check that the current version is as expected before bumping
    metadata = deposition.get("metadata")
    current_version = metadata.get("version")
    print(f"Current version for {ds}: {current_version}") 

    # version bump. update 1.0 to 1.1, 2.0 to 2.1, 1.1 to 1.2, v1.1.0 to v1.1.1, 
    #. and v3.1.0 to v3.1.1 (for cohort scRNA-seq)
    if "cohort" in ds:
        major, minor, patch = current_version.split(".")
        new_version = f"{major}.{minor}.{int(patch)+1}"
        print(f"Bumping version for {ds} from {current_version} to {new_version}")
        print(f"add Collection DOI references by hand.")
        # we only want to bump and publish the DOIs for non-cohort datasets, so skip the DOI update for cohort scRNA-seq
        continue
    else:
        major, minor = current_version.split(".")
        new_version = f"{major}.{int(minor)+1}"

    # ao.update_dataset_doi(ds_path, zenodo, deposition, version="v1.0", publication_date=PUBLICATION_DATE)
    # define update_dataset_doi    
    deposition = ao.bump_doi_version(zenodo, current_doi_id)


    metadata = deposition.get("metadata")
    new_doi_id = f"{deposition['id']}"

    print(f"Updated DOI for {ds}: {new_doi_id}")

    metadata['version'] = new_version


    # ##

    # add note about version bump in the description
    description = metadata.get("description", "")
    description += f"\n\nVersion bump from {current_version} to {new_version}"
    description += f"\n\nThe updated Datasets fix inconsistencies in the ASAP assigned `ASAP_subject_id` and `ASAP_sample_id` for these previously released PMDBS Datasets. These erroneously included the string \"PMBDS\", now replaced with \"PMDBS\". This change does not affect the underlying data files, but does update the metadata to be consistent with the naming convention used for all other PMDBS Datasets and the corresponding CDEs."
    metadata['description'] = description

    deposition = ao.update_doi_metadata(zenodo, new_doi_id, metadata)


    ## archive things...
    # write version
    ao.write_version(new_version, ds_path / "version")

    ## update the pdf.
    # first copy the original one with the original version number, then update the metadata and add the new pdf with the new version number. This way we have both versions of the pdf in the DOI record, and the new one is clearly labeled with the new version number.
    file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"
    new_file_path = ds_path / "DOI" / f"{ds_path.name}_README_v{new_version}.pdf"
    shutil.copy(file_path, new_file_path)
    # copy project.json, deposition.json and <dataset_name>.json to versioned filenames for archival purposes
    project_json_path = ds_path / "DOI" / f"project_v{new_version}.json"
    deposition_json_path = ds_path / "DOI" / f"deposition_v{new_version}.json"
    dataset_json_path = ds_path / "DOI" / f"{ds_path.name}_v{new_version}.json"
    shutil.copy(ds_path / "DOI" / f"project.json", project_json_path)
    shutil.copy(ds_path / "DOI" / f"final-deposition.json", deposition_json_path)
    shutil.copy(ds_path / "DOI" / f"{ds_path.name}.json", dataset_json_path)


    # load json
    doi_path = ds_path / "DOI"
    with open(doi_path / f"project.json", "r") as f:
        data = json.load(f)

    data_description = data.get("description", "")
    data_description += f"\n\nVersion bump from {current_version} to {new_version}"
    data_description += f"\n\nThe updated Datasets fix inconsistencies in the ASAP assigned `ASAP_subject_id` and `ASAP_sample_id` for these previously released PMDBS Datasets. These erroneously included the string \"PMBDS\", now replaced with \"PMDBS\". This change does not affect the underlying data files, but does update the metadata to be consistent with the naming convention used for all other PMDBS Datasets and the corresponding CDEs."
    data['description'] = data_description
    data['version'] = new_version
    # save updated json
    with open(doi_path / f"project.json", "w") as f:
            json.dump(data, f, indent=4)
    
    # make the new pdf the anchor file for the DOI, and update the metadata to reflect the new version and description
    ao.make_readme_file(ds_path)


    file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"
    # deposition = update_doi_metadata(zenodo, v1_beta_doi_id, metadata)
    deposition = ao.add_anchor_file_to_doi(zenodo,  file_path, new_doi_id)

    ao.archive_deposition_local(ds_path, f"pre-{new_version}release-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)


#%%

# publish the updated DOIs for the bumped datasets

for ds in bump_datasets:
    ds_path = datasets_repo_path / ds
    doi_id = ao.get_doi_from_dataset(ds_path, version=True)
    deposition = zenodo.get_deposition(doi_id)
    deposition = ao.publish_doi(zenodo, doi_id)
    ao.archive_deposition_local(ds_path, "final-deposition", deposition)
    ao.archive_deposition_local(ds_path, f"final-{new_version}-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)

# %%
# %%

