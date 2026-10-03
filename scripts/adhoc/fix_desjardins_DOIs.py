
# # ASAP CRN — New WIP Dataset Acceptance Template
#


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

root_path = Path(__file__).resolve().parents[3]
datasets_repo_path = root_path / "cloud-datasets"

# %% 

# 
fix_datasets = [
    "desjardins-mouse-bulk-rnaseq-striatum-pink1",
    "desjardins-mouse-bulk-rnaseq-nigra-pink1",
    "desjardins-mouse-sc-rnaseq-colon-immune-lrrk2",
    "desjardins-ipsc-sc-rnaseq-myeloid-pink1",
    "desjardins-mouse-sc-rnaseq-colon-immune-pink1", # beta version - .20276572
    # "desjardins-human-pbmc-multimodal-sc-rna-tcr",
]


# %%
# v0.1 DOIs include erroneous pdf versions in the v0.1 DOI.

# steps,
# archive "deposition" as v0.0-incorrect
# update version to v0.0
# make new v0.1
# upload new v0.1 pdf
# publish

# make v1.0 DOI as draft



PUBLICATION_DATE = "2026-02-26"  
CDE_VERSION = "v4.5"   
RELEASE_VERSION = "v5.1.0"

zenodo = ao.setup_zenodo()

# %%




# %% 
# datasets have been changed to current v0.0.1-error 
for ds in fix_datasets:
    ds_path = datasets_repo_path / "WIP" / ds

    current_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    # renname 

    deposition = zenodo.get_deposition(current_doi_id)

    # get current version from version file
    ao.write_version("0.1", ds_path / "version")

    version_file = ds_path / "version"
    current_version = version_file.read_text().strip()

    # check that the current version is as expected before bumping
    metadata = deposition.get("metadata")
    print(f"Current version for {ds}: {current_version}, metadata version: {metadata.get('version')}")
  
    ao.archive_deposition_local(ds_path, "v0.0.1-error-deposition", deposition)
    # ao.archive_deposition_local(ds_path, f"deposition_v{current_version}", deposition)

    # we will fix project.json by hand since the docx is the old format

    ref_path = ds_path / "refs"
    if len(list(ref_path.glob("*.docx"))) == 1:
        ref_doc = list(ref_path.glob("*.docx"))[0]
    else:
        print(f"WARNING: expected exactly 1 .docx file in {ref_path}, but found {len(list(ref_path.glob('*.docx')))}")
        
    ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE)

    project_json_path = ds_path / "DOI" / f"project.json"
    with open(project_json_path, "r") as f:
        project_json = json.load(f)



# mitigations is to update the current v0.1 DOIs to v0.0-incorrect, then make new
# v0.1 DOIs by hand...

# steps,
# archive "deposition" as v0.0-incorrect
# update version to v0.0
# make new v0.1
# upload new v0.1 pdf
# publish

# make v1.0 DOI as draft

# %%

PUBLICATION_DATE = "2026-09-30"  
CDE_VERSION = "v4.5"   
RELEASE_VERSION = "v5.1.0"

zenodo = ao.setup_zenodo()

# %%
# hack for "beta-deposition"

# dois = [
#     "20334808",
#     "20334811",
#     "22728401",
#     "20334804",
#      "20276572"]

# for ds, current_doi_id in zip(fix_datasets,dois):
#     ds_path = datasets_repo_path / "WIP" / ds

#     current_doi_id = "20276572"
#     # current_doi_id = ao.get_doi_from_dataset(ds_path, version=True)
#     deposition = zenodo.get_deposition(current_doi_id)

#     # check that the current version is as expected before bumping
#     metadata = deposition.get("metadata")
#     print(f"Current version for {ds}: {current_version}, metadata version: {metadata.get('version')}")

#     ao.archive_deposition_local(ds_path, "beta-deposition", deposition)
#     # ao.archive_deposition_local(ds_path, f"deposition_v{current_version}", deposition)
current_doi_id = "20276572"
zenodo.set_deposition_id(current_doi_id)
deposition = zenodo.deposition
ao.archive_deposition_local(ds_path, "beta-deposition", deposition)

current_doi_id = "22730904"
zenodo.set_deposition_id(current_doi_id)
deposition = zenodo.deposition
ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)

# %%
for ds in fix_datasets:
    ds_path = datasets_repo_path / "WIP" / ds

    readme_pdf = ds_path / "DOI" / f"{ds}_README.pdf"
    og_data_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    print(og_data_doi_id)

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

    zenodo.set_deposition_id(og_data_doi_id)
    # deposition = ao.bump_doi_version(zenodo, og_data_doi_id)
    deposition = zenodo.deposition
    metadata = deposition.get("metadata")
    new_doi_id = f"{deposition['id']}"

    print(f"NEW:  {ds}: ||| {new_doi_id} {og_data_doi_id}")
    readme_pdf = ds_path / "DOI" / f"{ds}_README.pdf"

    # initialize the v1.0 DOI
    # update v1.0
    metadata['version'] = 'v1.0'
    deposition = ao.update_doi_metadata(zenodo, new_doi_id, metadata)

    print(f"Updated DOI for {ds}: {new_doi_id}")

    if readme_pdf.exists():
        # not sure why this fails... seems that the REST API has changed behavior
        deposition = ao.replace_anchor_file_in_doi(zenodo, ds_path, new_doi_id, readme_pdf)
        print(f"Uploaded README: {ds_def}")

    else:
        print(f"WARNING: README PDF not found for {ds_def}")


    ao.finalize_DOI(ds_path, deposition, prerelease=True)
    # archive deposition
    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)




#%%


fix_datasets = [
    # "desjardins-mouse-bulk-rnaseq-striatum-pink1",
    # "desjardins-mouse-bulk-rnaseq-nigra-pink1",
    # "desjardins-mouse-sc-rnaseq-colon-immune-lrrk2",
    # "desjardins-ipsc-sc-rnaseq-myeloid-pink1",
    "desjardins-mouse-sc-rnaseq-colon-immune-pink1",
    # "desjardins-human-pbmc-multimodal-sc-rna-tcr",
]
