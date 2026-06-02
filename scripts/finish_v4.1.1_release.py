
# # ASAP CRN 
#
# **Lifecycle covered here:**
#.  assumes dataset v0.1 dataset DOIs are created:
#   1. Define dataset metadata (name, collection, CDE version, buckets)
#   2. Create `dataset.json` stubs in `cloud-datasets/WIP/`
#   3. Ingest DOI reference `.docx` files to generate Zenodo metadata
#   4. Create Zenodo draft DOIs at `v0.1`
#   5. define release paramaters and list of new datasets to release
#   6a. confirm reference exists and v0.1 DOI available
#   6b. create dataset.json stubs in `cloud-datasets/WIP/`
#   6c. create v1.0 DOI reference files, including additional annotation for .pdf (e.g. version bump copy)
#   6d. create unpublished v1.0 zenodo reference
### STARTS Here
#   7. publish DOI and copy WIP dataset tree to cloud-datasets root


#
# %%
# %% Setup
import collections
from importlib.metadata import metadata
from os import name, write
from pathlib import Path
import asap_orchestrator as ao
from asap_orchestrator.doi import bump_doi_version

import shutil, json
# TODO: confirm the root path resolves correctly for your environment

%load_ext autoreload
%autoreload 2
# 

root_path = Path(__file__).resolve().parents[2]
root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"
collections_repo_path = root_path / "cloud-collections"
releases_repo_path = root_path / "cloud-releases"

# %% [Step 5a] Release parameters

# %% [Step 1] Release parameters
# TODO: fill in release version, type, CDE version, and optional release DOI
RELEASE_VERSION = "v4.1.1"    # e.g. "v4.1.0"
RELEASE_TYPE = "Minor"        # "Urgent" | "Minor" | "Major"
CDE_VERSION = "v4.4"          # e.g. "v3.3"
RELEASE_DOI = "10.5281/zenodo.20185963"              #10.5281/zenodo.20185963
RELEASE_DATE = "2026-05-30"
# %% [Step 2] Define datasets NEW or VERSION-BUMPED in this release
# Each entry needs a published (or pre-reserved) Zenodo DOI.
# Use version="v1.0" for datasets being released for the first time (promoted
# from WIP v0.1).  Use the new bumped version for datasets being re-released.
# v1.0 datasets, v4.3 cde
new_datasets = [
    "voet-pmdbs-sn-multimodal",
    "voet-pmdbs-sn-atacseq-scalebio-hydrop",
    "voet-pmdbs-sn-atacseq-scalebio-10x",
    "voet-pmdbs-sn-atacseq-hydrop",
    "voet-pmdbs-sn-atacseq-10x",
    "voet-pmdbs-sn-rnaseq-parsebio",
    "voet-pmdbs-sn-rnaseq",
    "scherzer-pmdbs-sn-rnaseq-midbrain-hybsel",
    "scherzer-pmdbs-lr-wgs"
 ]




# %%
# move below to part of a release script
# # %%
zenodo = ao.setup_zenodo()

# %% [Step 67] publish DOI and move WIP dataset tree to cloud-datasets root

for ds in new_datasets:
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

new_dataset_defs = []
for ds in new_datasets:
    ds_path = datasets_repo_path / "datasets" / ds

    ds_in = ao.Dataset.load(ds_path)
    ds_def = ao.fill_dataset_stub(ds_in,ds_path)


    ds_def.save(ds_path)

    new_dataset_defs.append(ds_def)
    


# %%
# create this now even thouth we'll re-make it later.
new_dataset_defs = []
PARTS2 = ["raw", "dev", "uat", "curated"]
target_keywords = ["pmdbs", "lr-wgs", "sn-rnaseq", "sn-atacseq","sn-multimodal"]  # used to identify which datasets to apply this release_info to; e.g. if your release includes datasets from multiple teams or with different characteristics, you can use this field to specify which datasets get which release_info

for ds in new_datasets:
    ds_path = datasets_repo_path / "datasets" / ds

    with open(ds_path / "dataset.json", "r") as f:
        ds_info = json.load(f)

    team = ds.split("-")[0]

    keywords = [k for k in target_keywords if k in ds]  #
    keywords += [team]

    fix_buckets = ds_info["buckets"].copy()
    for part in PARTS2:
        # keep it simple since we just have non-cohort datsets.
        bucket = f"gs://asap-{part}-team-{ds}"
        if part == "curated":
            fix_buckets["prod"] = bucket
        else:
            fix_buckets[part] = bucket


    # make a new ds_info in the correct order.
    new_ds_info = dict(
        name=ds_info["name"],
        title=ds_info["title"],
        description=ds_info["description"],
        version=ds_info["version"],         
        doi=ds_info["doi"],
        keywords=keywords,
        license=ds_info["license"],
        references=ds_info["references"],
        collection = ds_info["collection"],
        buckets=fix_buckets,
        cde_version=CDE_VERSION,
        releases=ds_info["releases"],
        dataset_title=ds_info["dataset_title"],
    )

    with open(ds_path / "dataset.json", "w") as f:
        json.dump(new_ds_info, f, indent=4)
    new_dataset_defs.append(ao.Dataset.load(ds_path))

    
# %%    

# get all the datasets and see if the jsons are up to spec
all_datasets = [d.name for d in (datasets_repo_path / "datasets").glob("*")]

# %%


# for ds in all_datasets:
#     ds_path = datasets_repo_path / "datasets" / ds
#     with open(ds_path / "dataset.json", "r") as f:
#         ds_info = json.load(f)

#     # if len(ds_info["curation"]):
#     #     curation_info = ds_info["curation"]

#     #     print(f"dataset {ds} has curation info")
#     #     release_version = ds_info["curation"]["release"]
#     #     dataset_version =ds_info["releases"][release_version]["dataset_version"]
#     #     collection_version = ds_info["curation"]["version"]
#     #     new_curation_info = dict(
#     #         name=curation_info["name"],
#     #         dataset_version=dataset_version,
#     #         release_version=release_version,
#     #         collection_version=collection_version,
#     #         collection=curation_info["collection"],
#     #         releases=curation_info["releases"],
#     #     )

#     #     ds_info["curation"] = new_curation_info 

#     # else:
#     #     print(f"dataset {ds} has NO curation info, adding empty curation field")
#     #     ds_info["curation"] = dict()


#     # fix title and description from project.json
#     project_json_path = ds_path / "DOI" / f"project.json"
#     if project_json_path.exists():
#         with open(project_json_path, "r") as f:
#             project_json = json.load(f)
#         short_desc = ds_info["description"]
#         ds_info["title"] = project_json.get("dataset_title", ds_info["title"])
#         ds_info["description"] = project_json.get("dataset_description", ds_info["description"])
#         ds_info["short_description"] = short_desc

#     with open(ds_path / "dataset.json", "w") as f:
#         json.dump(ds_info, f, indent=4)

# %%

successfully_loaded = []
unsuccessfully_loaded = []
all_ds_model = {}
for ds in all_datasets:
    print(f"dataset: {ds}")

    ds_path = datasets_repo_path / "datasets" / ds
    with open(ds_path / "dataset.json", "r") as f:
        ds_info = json.load(f)

    # try to load with the model to confirm it works
    try:
        dataset_model = ao.Dataset.load(ds_path)
        successfully_loaded.append(f"{ds}")
    except Exception as e:
        print(f"Error loading dataset: {ds_path}")
        unsuccessfully_loaded.append(f"{ds}")
        print(e)
        continue
    
    curr_key = dataset_model.name
    print(curr_key)
    # print(f"Loaded dataset: {dataset_model.name} (version: {dataset_model.version}, doi: {dataset_model.doi})")
    all_ds_model[ds] = dataset_model

####################
# update the dataset.json stubs for the new datasets being released in this tranche. This is necessary to ensure the release manifest is up to date with the correct DOIs and versions, which are used as the source of truth for this information.

# %%
# now lets loop through all datasets and update the dataset.json to include the curated_version

is_major_release = lambda v: v.split(".")[1:] == ["0", "0"]



# for ds in all_datasets:
#     ds_path = datasets_repo_path / "datasets" / ds
#     with open(ds_path / "dataset.json", "r") as f:
#         ds_info = json.load(f)

#     refs = ds_info.get("references", [])
#     if len(refs)>0:
#         print(f"dataset {ds} has {len(refs)} references")

# # %%. now lets confirm we can load them all with the model
# all_datasets = [d.name for d in (datasets_repo_path / "datasets").glob("*")]

# successfully_loaded = []
# unsuccessfully_loaded = []
# all_ds_model = {}
# for ds in all_datasets:
#     print(f"dataset: {ds}")

#     ds_path = datasets_repo_path / "datasets" / ds
#     with open(ds_path / "dataset.json", "r") as f:
#         ds_info = json.load(f)


    
#     # add all_releases
#     all_releases = [r for r in ds_info["releases"].keys()]
#     # add all_versions
#     all_versions = [v["dataset_version"] for v in ds_info["releases"].values()]

#     ds_info["all_releases"] = all_releases  
#     ds_info["all_versions"] = list(set(all_versions))  # remove duplicates from all_versions

#     with open(ds_path / "dataset.json", "w") as f:
#         json.dump(ds_info, f, indent=4)

#     # try to load with the model to confirm it works
#     try:
#         dataset_model = ao.Dataset.load(ds_path)
#         successfully_loaded.append(f"{ds}")
#     except Exception as e:
#         print(f"Error loading dataset: {ds_path}")
#         unsuccessfully_loaded.append(f"{ds}")
#         print(e)
#         continue

#     all_ds_model[ds] = dataset_model

# create this now even thouth we'll re-make it later.
new_dataset_defs = []

for ds in new_datasets:
    ds_path = datasets_repo_path / "datasets" / ds

    new_dataset_defs.append(ao.Dataset.load(ds_path))

# %%
############# fix all release.json files
all_releases = [ r.name for r in (releases_repo_path).glob("v*.*.*") if r.is_dir() and "beta" not in r.name]
all_releases.sort(key=lambda x: x.split("."), reverse=False)
for rel_num in all_releases:
    # skip beta

    rel_path = releases_repo_path / rel_num
    with open(rel_path / "release.json", "r") as f:
        rel_info = json.load(f)



    # all_datasets
    number_of_datasets = len(rel_info["datasets"])
    
    # check that they are unique(e.g. no duplicates)
    dataset_names = [ds["name"] for ds in rel_info["datasets"]]
    if len(dataset_names) != len(set(dataset_names)):
        print(f"WARNING: release {rel_num} has duplicate dataset entries!")


    print(f"release {rel_num} datasets: {rel_info['datasets']}")
    # re_released
    
    new_datasets = rel_info.get("new_datasets", [])
    re_released = set([ds["name"] for ds in rel_info["datasets"]]) & set([ds["name"] for ds in new_datasets])
    new_datasets = [ds for ds in new_datasets if ds["name"] not in dataset_names]

    if len(re_released)>0:
        print(f"careful!  we have some re-releasaed datasets: {re_released}")

    print(f"release {rel_num} new datasets: {new_datasets}")
    
    # new_datasets




    # confirm metadta
    print(f"release {rel_num} metadata: {rel_info['metadata']}")
    print(f" length of datasets: {len(rel_info['datasets'])}")
    print(f" length of new_datasets: {len(rel_info['new_datasets'])}")
    print(f" length of collections: {len(rel_info['collections'])}")

    # with open(rel_path / "release.json", "w") as f:
    #     json.dump(rel_info, f, indent=4)


# %%
############################    for name in previously_released_names
############################    for name in previously_released_names
############################    for name in previously_released_names
############################    for name in previously_released_names
############################    for name in previously_released_names

# Update releases.json index

releases_index = {}
index_path = releases_repo_path / "releases.json"

for release in all_releases:
    rel_path = releases_repo_path / release
    with open(rel_path / "release.json", "r") as f:
        rel_info = json.load(f)

    releases_index[release] = rel_info

with open(index_path, "w") as f:
    json.dump(releases_index, f, indent=2)




#
# 
# 
# 

# update collections.json index
collection_names = [
    'pmdbs-sc-rnaseq',
    'pmdbs-bulk-rnaseq',
    'pmdbs-spatial-rnaseq',
    'mouse-spatial-rnaseq',
    'mouse-sc-rnaseq',
    ]
collections_index = {}
index_path = collections_repo_path / "collections.json"
for collection in collection_names:
    col_path = collections_repo_path / collection / "collection.json"
    with open(col_path, "r") as f:
        col_info = json.load(f)
    # update the collection index with the latest version info
    collections_index[collection] = col_info


with open(index_path, "w") as f:
    json.dump(collections_index, f, indent=2)


# %%
# load the v4.1.1_release archive

with (releases_repo_path / "v4.1.1" / "release.json").open("r") as f:
    release_info = json.load(f)

datasets_index = {}
for ds in release_info["datasets"]:
    dataset_name = ds["name"]
    dataset_path = datasets_repo_path / "datasets" / dataset_name

    # load the json
    with open(dataset_path/"dataset.json", "r") as f:
        dataset_json = json.load(f)
    datasets_index[dataset_name] = dataset_json

# write datsets.json
with (datasets_repo_path / "datasets.json").open("w") as f:
    json.dump(datasets_index, f, indent=2)


# %%
## CREATE AUTHORSHIP LIST DOCUMENT

# %%