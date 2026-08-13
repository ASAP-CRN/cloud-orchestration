# %% 
# # ASAP CRN — Release Template
#
# Copy this file and rename it, e.g. `define_v5.0.0_release.py`.
# Fill in every section marked with TODO before running cell by cell.
#
# **Lifecycle covered here:**
#   1. Define new datasets being added or version-bumped in this release
#   2. Assemble the full dataset + collection manifests
#   3. Build the ReleaseDefinition and CollectionDefinitions
#   4. Perform the release  (writes cloud-releases)
#   5. Update collections   (writes cloud-collections)
#   6. Archive dataset versions and update release records (writes cloud-datasets)
#   7. Rebuild master indexes (datasets.json, collections.json)
#
# DO NOT EXECUTE THIS FILE DIRECTLY — it is a template only.

# %% Setup
from pathlib import Path
import asap_orchestrator as ao
import json

# TODO: confirm the root path resolves correctly for your environment
root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"
collections_repo_path = root_path / "cloud-collections"
releases_repo_path = root_path / "cloud-releases"


# %% [Step 1] Release parameters
# TODO: fill in release version, type, CDE version, and optional release DOI
RELEASE_VERSION = "v5.1.0"    # e.g. "v5.1.0"
RELEASE_TYPE = "Minor"        # "Urgent" | "Minor" | "Major"
CDE_VERSION = "v4.5"          # e.g. "?"
RELEASE_DOI = "10.5281/zenodo.20186059"              # Zenodo concept DOI for the release itself, or ""
RELEASE_DATE = "2026-09-31"

PUBLICATION_DATE = "2026-09-31"   # e.g. "2026-05-01"

# steps
# 1 define which datasets are new or newly curated 
# 2. define new collections
# 3. do any dataset, collection version bumps
# 4. build the release manifest with define_release()
    


old_datasets = [
    "biederer-pmdbs-spatial-geomx-lamda",
    "biederer-mouse-spatial-geomx-lamda"
]


new_datasets = [   
    "desjardins-mouse-bulk-rnaseq-striatum-pink1",
    "desjardins-mouse-bulk-rnaseq-nigra-pink1",
    "desjardins-human-pbmc-multimodal-sc-rna-tcr",
    "desjardins-mouse-sc-rnaseq-colon-immune-lrrk2",
    "desjardins-ipsc-sc-rnaseq-myeloid-pink1",
    "desjardins-mouse-sc-rnaseq-colon-immune-pink1",
    "rio-hesc-spheroids-sc-rnaseq-irradiated",
    "rio-hesc-sc-rnaseq-irradiated",
    "rio-hesc-sc-rnaseq-wt-dopaminergic",
    "rio-hesc-targeted-ngs-mutant-zygosity",
    "rio-hesc-wgs-iscore-pd-genotyping-and-snps"
]


do_nothing_datasets = [
    "alessi-mouse-sn-rnaseq-dorsal-striatum-g2019s",
    "lee-mouse-liver-bulk-rnaseq-g2019s",
    "lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet",
    # "lee-mouse-sn-rnaseq-midbrain-g2019s-hf-diet",
    "schlossmacher-mouse-sn-rnaseq-osn-aav-transd",
    "voet-pmdbs-sn-rnaseq"
]

updated_datasets = [
    "cragg-mouse-sn-rnaseq-striatum",
    "voet-pmdbs-sn-multimodal"
]


## STEP 1
#. create dataset.json




# %% [Step 2] Define datasets NEW or VERSION-BUMPED in this release
new_collections = [
    "invitro-bulk-rnaseq",
    "pmdbs-sc-atacseq",
]

# define
# %%
new_dataset_defs = []

# all of our datasets have previously been released.
for ds in new_datasets:
    ds_path = datasets_repo_path / "datasets" / ds
    with open(ds_path / "dataset.json", "r") as f:
        ds_info = json.load(f)

    dataset_model = ao.Dataset.load(ds_path)
    new_dataset_defs.append(dataset_model)


# %%

# %% [Step 3] Build the full dataset list for the release manifest
# This must include ALL datasets (new + previously released).
# Read existing dataset entries directly from their dataset.json files so DOIs
# and versions stay in sync with the source of truth.

previous_release = "v5.0.0"
# load dataset.json
prev_release_path = releases_repo_path / previous_release

with open(prev_release_path / "release.json", "r") as f:
    release_info = json.load(f)

# %%
previous_datasets = {ds["name"]:ds for ds in release_info.get("datasets")}
previously_released_names = list(previous_datasets.keys())


# %%
prev_dataset_defs = []

for ds in previously_released_names:
    ds_path = datasets_repo_path / "datasets" / ds
    with open(ds_path / "dataset.json", "r") as f:
        ds_info = json.load(f)

    dataset_model = ao.Dataset.load(ds_path)

    prev_dataset_defs.append(dataset_model)

# %%
# convert to release entries...

# check for overlap
re_released = set(previously_released_names) & set(new_datasets)
if len(re_released)>0:
    print(f"careful!  we have some re-releasaed datasets: {re_released}")

# %%

all_datasets = prev_dataset_defs + new_dataset_defs

all_datasets_list = [ dict( name = data.name, doi=data.doi, dataset_version=data.version) for data in all_datasets]
new_datasets_list = [ dict( name = data.name, doi=data.doi, dataset_version=data.version) for data in new_dataset_defs]








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







# get collections
# none new in this release
collections={}
for ds in all_datasets:
    collection = ds.collection
    if collection is not None:
        print(f"dataset {ds.name} belongs to collection {collection}")

        # need to get the collection + version...
        collection_path = collections_repo_path / collection / "collection.json"
        with open(collection_path, "r") as f:
            collection_info = json.load(f)
        # find highest version
        collection_vers = {ver : x["release"]["version"] for ver,x in collection_info["versions"].items() if x["release"]["version"]<=RELEASE_VERSION }
        # check release.versiopn is NOT > current
        cver = max(collection_vers.keys())
        if collection_vers[cver]<RELEASE_VERSION:
            collections[collection] = dict(name=collection,doi=collection_info["collection_doi"],version=cver)
        else:
            print(f"WARNING: collection {collection} already has version {collection_vers[cver]} >= release version {RELEASE_VERSION}")

# build metadata
metadata = dict(
    total_datasets = len(all_datasets_list),
    total_collections = len(collections),
    source=Path(__file__).name
)




release_dict = dict(
    release_version=RELEASE_VERSION,
    cde_version=CDE_VERSION, 
    release_doi=RELEASE_DOI, 
    datasets=all_datasets_list,
    new_datasets=new_datasets_list,
    collections=collections,
    created=RELEASE_DATE,
    metadata=metadata
    )

# %% 
# write release.json
release_path = releases_repo_path / RELEASE_VERSION 

with open(release_path / "release.json", "w") as f:
    json.dump(release_dict, f, indent=4)




############################    for name in previously_released_names
############################    for name in previously_released_names
############################    for name in previously_released_names
############################    for name in previously_released_names



# %%
all_dataset_entries = [
    ao.read_dataset_entry(datasets_repo_path / "datasets" / name)
] + [ds.to_release_entry() for ds in new_dataset_defs]

new_dataset_entries = [ds.to_release_entry() for ds in new_dataset_defs]

# %% [Step 4] Define the collections being versioned in this release
# Only collections that have new or updated datasets need a version bump.
# For an Urgent release with no curated datasets, this list may be empty.
#
# Each entry: {"name": <collection-name>, "doi": <zenodo-doi>, "version": <new-version>}
# The DOI here is the Zenodo concept DOI for the new collection version.

collection_entries = [
    # TODO: fill in for each updated collection, e.g.:
    # {"name": "pmdbs-sc-rnaseq", "doi": "10.5281/zenodo.YYYYYYYY", "version": "v3.2.0"},
]

# %% [Step 5] Build the ReleaseDefinition
release_def = ao.define_release(
    release_version=RELEASE_VERSION,
    release_type=RELEASE_TYPE,
    cde_version=CDE_VERSION,
    datasets=all_dataset_entries,
    new_datasets=new_dataset_entries,
    collections=collection_entries,
)

# %% [Step 6] Define collections (one CollectionDefinition per updated collection)
# Maps each new collection version to the datasets it gains in this release.
# `new_datasets` lists only the names added/bumped in *this* release; existing
# datasets are carried forward automatically from the collection's current state.

collection_defs = [
    # TODO: add one ao.define_collection() call per entry in collection_entries, e.g.:
    # ao.define_collection(
    #     collection_name="pmdbs-sc-rnaseq",
    #     new_version="v3.2.0",
    #     new_datasets=[ds.name for ds in new_dataset_defs if ds.collection == "pmdbs-sc-rnaseq"],
    #     release_def=release_def,
    # ),
]

# %% [Step 7] Perform the release
# Writes <release_version>/release.json and updates releases.json in cloud-releases.
release_dir = ao.perform_release(
    release_def,
    releases_repo_path=releases_repo_path,
    release_doi=RELEASE_DOI,
)
print(f"Release written: {release_dir}")

# %% [Step 8] Update collections
# Writes collection.json and archive snapshots in cloud-collections.
for col_def in collection_defs:
    ao.update_collection(col_def, collections_repo_path)
    print(f"Updated collection: {col_def.collection_name} -> {col_def.new_version}")

# %% [Step 9] Archive dataset versions and record release in dataset.json
# For each NEW or BUMPED dataset:
#   - copies DOI/ and refs/ to archive/<old_version>/
#   - sets the new version in dataset.json
#   - adds the release record under dataset.json["releases"]
#   - updates all_versions entry

for ds_def in new_dataset_defs:
    ds_path = datasets_repo_path / "datasets" / ds_def.name
    if not ds_path.exists():
        # Dataset may still be under WIP/ — promote it first
        wip_path = datasets_repo_path / "WIP" / ds_def.name
        if wip_path.exists():
            import shutil
            shutil.move(str(wip_path), str(ds_path))
            print(f"Promoted from WIP: {ds_def.name}")
        else:
            print(f"WARNING: dataset directory not found: {ds_def.name}")
            continue

    ao.update_dataset_version(
        ds_path=ds_path,
        new_version=ds_def.version,
        release_version=RELEASE_VERSION,
        cde_version=CDE_VERSION,
    )
    print(f"Archived dataset: {ds_def.name} -> {ds_def.version}")

# %% [Step 10] Rebuild master indexes
ao.update_datasets_index(datasets_repo_path)
print("datasets.json updated")

# collections.json is rebuilt automatically inside update_collection(),
# but run explicitly here if collections were not updated above.
if not collection_defs:
    ao.update_collections_index(collections_repo_path)
    print("collections.json updated")
