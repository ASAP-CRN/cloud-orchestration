# %% [markdown]
# # ASAP CRN — Release Archive
#
# Copy this file and rename it, e.g. `make_v4.1.1_release.py`.
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
import shutil
# !pip install google-cloud-storage
# # Imports the Google Cloud client library
# from google.cloud import storage


# TODO: confirm the root path resolves correctly for your environment
root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"
collections_repo_path = root_path / "cloud-collections"
releases_repo_path = root_path / "cloud-releases"

archive_path = root_path / "release_archive"

# %%
# create the archive_path = root_path / "release_archive"

if not archive_path.exists():
    print(f"  [{archive_path}] create archive directory")
    archive_path.mkdir(parents=True, exist_ok=True)


# # %% 
# #  get all the releases from cloud-releases
# # load the releases.json
# with (releases_repo_path / "releases.json").open("r") as f:
#     releases = json.load(f)

# %% 
#  get all the collections from cloud-collections
with (collections_repo_path / "collections.json").open("r") as f:
    collections = json.load(f)
    
# %%    
# get all the datasets from cloud-datasets
with (datasets_repo_path / "datasets.json").open("r") as f:
    datasets = json.load(f)


# %%    
# now loop through all datasets and begin to build the archive

dataset_archive = archive_path 

if not dataset_archive.exists():
    print(f"  [{dataset_archive}] create dataset archive directory")
    dataset_archive.mkdir(parents=True, exist_ok=True)



# %%
for dataset, dataset_info in datasets.items():

    print(f"  [{dataset}] get dataset.json")
    ds_path = datasets_repo_path / "datasets" / dataset
    dataset_model = ao.Dataset.load(ds_path)

    # get the dataset bucket
    ds_ver = dataset_model.version

    ds_bucket = dataset_model.buckets.prod
 

    # make an archive of dataset from asap-crn-cloud-dataset-metadata repo based on teh dataset.json
    #  - dataset.json
    # from the cloud-datasets repo datasets/dataset 
    #. - datasets's refs/archive/<dataset_version>/DOI/
    #. - datasets's refs/archive/<dataset_version>/refs/

    # # copy the ds_path/ to the archive
    # shutil.copytree(
    #     ds_path,
    #     f"{dataset_archive}/{dataset}"
    # )
    
    # make an archive of datasets from the curated bucket
    #  - dataset's metadata/release/
    #  - dataset's metadata/original/ 
    #  - datasets's file_metadata/                                        
    ao.gcloud_rsync(f"{ds_bucket}/metadata/release/", f"{dataset_archive}/{dataset}/metadata/release/",directory=True,clobber=True)
    ao.gcloud_rsync(f"{ds_bucket}/file_metadata/", f"{dataset_archive}/{dataset}/file_metadata/",directory=True,clobber=True)


# NOW SYNC THE COLLECTIONS TO THE ARCHIVE


# %%    
# now loop through all collections and begin to build the archive

collections_archive = archive_path / "collections"

if not collections_archive.exists():    
    print(f"  [{collections_archive}] create collection archive directory")
    collections_archive.mkdir(parents=True, exist_ok=True)

# %%
with(collections_repo_path / f"collections.json").open("r") as f:
    collection_info = json.load(f)

for collection, collection_info in collections.items():
    print(f"  [{collection}] get collection.json")
    with(collections_repo_path / f"{collection}" / f"collection.json").open("r") as f:
        collection_info = json.load(f)

    # make an archive of collection from asap-crn-cloud-dataset-metadata repo based on the collection.json
    #  - collection.json
    # collection_archive = archive_path / "collections" / collection
    # if not collection_archive.exists():
    #     print(f"  [{collection_archive}] create collection archive directory")
    #     collection_archive.mkdir(parents=True, exist_ok=True)

    # copy the collection path to the archive
    shutil.copytree(
        collections_repo_path / collection,
        f"{collections_archive}/collections/{collection}"
    )




# %% NOW loop through all releases and copy the releases to the archive
releases = ["v1.0.0","v2.0.0","v2.0.1","v2.0.2","v2.0.3","v3.0.0","v3.0.1","v3.0.2","v4.0.0","v4.0.1","v4.0.2","v4.1.0"]

releases_archive = archive_path / "releases"

if not releases_archive.exists():
    releases_archive.mkdir(parents=True, exist_ok=True)

for release in releases:
    print(f"  [{release}] get release.json")
    with(releases_repo_path /f"{release}/release.json").open("r") as f:
        release_info = json.load(f)

    # make an archive of release from asap-crn-cloud-dataset-metadata repo based on the release.json
    #  - release.json

    # copy the release path to the archive
    shutil.copytree(
        releases_repo_path / release,
        f"{releases_archive}/releases/{release}"
    )



#############################
# %%
# now loop through all the subdirectories of the release_archive and rsync with the bucket

release_resources_bucket = f"gs://asap-crn-cloud-release-resources"

for directory in archive_path.iterdir():
    if directory.is_dir():
        print(f"  [{directory}] rsync with bucket")
        ao.gcloud_rsync(str(directory), f"{release_resources_bucket}/{directory.name}", directory=True, clobber=True)


ew3# %%




# %%

