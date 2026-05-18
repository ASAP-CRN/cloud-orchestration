
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

root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"

# %% 

# 
fix_datasets = [
    'lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet',
]


PUBLICATION_DATE = "2026-02-26"  
CDE_VERSION = "v4.1"   
RELEASE_VERSION = "v4.0.1"

zenodo = ao.setup_zenodo()

# %%
for ds in fix_datasets:
    ds_path = datasets_repo_path / "datasets" / ds

    current_doi_id = ao.get_doi_from_dataset(ds_path, version=True)
    deposition = zenodo.get_deposition(current_doi_id)

    # get current version from version file
    version_file = ds_path / "version"
    current_version = version_file.read_text().strip()

    # check that the current version is as expected before bumping
    metadata = deposition.get("metadata")
    print(f"Current version for {ds}: {current_version}, metadata version: {metadata.get('version')}")
  
    ao.archive_deposition_local(ds_path, "final-deposition", deposition)
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


    # make copies
    project_json_path = ds_path / "DOI" / f"project_v{current_version}.json"
    deposition_json_path = ds_path / "DOI" / f"deposition_v{current_version}.json"
    dataset_json_path = ds_path / "DOI" / f"{ds_path.name}_v{current_version}.json"
    shutil.copy(ds_path / "DOI" / f"project.json", project_json_path)
    shutil.copy(ds_path / "DOI" / f"final-deposition.json", deposition_json_path)
    shutil.copy(ds_path / "DOI" / f"{ds_path.name}.json", dataset_json_path)


    file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"

    # bumped and fixed by hand ow fix the deposition archive
    current_doi_id = ao.get_doi_from_dataset(ds_path, version=True)
    deposition = zenodo.get_deposition(current_doi_id)

    metadata = deposition.get("metadata")
    print(f"Current version for {ds}: {current_version}, metadata version: {metadata.get('version')}")
  
    ao.archive_deposition_local(ds_path, "final-deposition", deposition)
    ao.archive_deposition_local(ds_path, f"deposition_v{current_version}", deposition)

#%%
