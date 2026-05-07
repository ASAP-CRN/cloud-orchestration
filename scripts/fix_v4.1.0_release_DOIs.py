
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



# cde v3.3
fix_datasets = [
'scherzer-pmdbs-sn-rnaseq-mtg',# v1.2
'scherzer-pmdbs-sn-rnaseq-mtg-hybsel',# v1.2
]
PUBLICATION_DATE = "2026-04-30"   # e.g. "2026-05-01"
CDE_VERSION = "v3.3"              # e.g. "v3.3"

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
    ao.archive_deposition_local(ds_path, f"deposition_v{current_version}", deposition)



    project_json_path = ds_path / "DOI" / f"project.json"
    with open(project_json_path, "r") as f:
        project_json = json.load(f)

    # # fix project.json metadata if needed, e.g. add version bump note to description
    dataset_description = project_json.get("dataset_description", "")
    description = project_json.pop("description", "")
    dataset_description += description
    
    project_json['dataset_description'] = dataset_description

    project_json['publication_date'] = PUBLICATION_DATE
    # save updated json
    with open(ds_path / "DOI"  / f"project.json", "w") as f:
            json.dump(project_json, f, indent=4)


    # load json
    # make the new pdf the anchor file for the DOI, and update the metadata to reflect the new version and description
    ao.make_readme_file(ds_path)

    # save metadata as ds_path / "DOI" / f"{ds_path.name}.json",
    with open(ds_path / "DOI" / f"{ds_path.name}.json", "w") as f:
        json.dump(metadata, f, indent=4)

    # make copies
    project_json_path = ds_path / "DOI" / f"project_v{current_version}.json"
    deposition_json_path = ds_path / "DOI" / f"deposition_v{current_version}.json"
    dataset_json_path = ds_path / "DOI" / f"{ds_path.name}_v{current_version}.json"
    shutil.copy(ds_path / "DOI" / f"project.json", project_json_path)
    shutil.copy(ds_path / "DOI" / f"final-deposition.json", deposition_json_path)
    shutil.copy(ds_path / "DOI" / f"{ds_path.name}.json", dataset_json_path)


    file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"



#%%
