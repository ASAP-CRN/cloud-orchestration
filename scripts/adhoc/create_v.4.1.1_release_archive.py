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
from xml.etree.ElementPath import find
import asap_orchestrator as ao
import json
import shutil
# !pip install google-cloud-storage
# # Imports the Google Cloud client library
# from google.cloud import storage

%load_ext autoreload
%autoreload 2


# TODO: confirm the root path resolves correctly for your environment
root_path = Path(__file__).resolve().parents[3]
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
for dataset_name, dataset_info in datasets.items():

    print(f"  [{dataset_name}] get dataset.json")
    ds_path = datasets_repo_path / "datasets" / dataset_name
    dataset_model = ao.Dataset.load(ds_path)

    # get the dataset bucket
    ds_ver = dataset_model.version


    if dataset_name not in new_datasets:
        # continue
        ds_bucket = dataset_model.buckets.prod
    else:
        ds_bucket = dataset_model.buckets.raw

    # make an archive of dataset from asap-crn-cloud-dataset-metadata repo based on teh dataset.json
    #  - dataset.json
    # from the cloud-datasets repo datasets/dataset 
    #. - datasets's refs/archive/<dataset_version>/DOI/
    #. - datasets's refs/archive/<dataset_version>/refs/

    # # copy the ds_path/ to the archive
    # folders_to_copy = ["archive", "DOI", "refs"]
    # for folder in folders_to_copy:
    #     src_folder = ds_path / folder
    #     if src_folder.exists() and src_folder.is_dir():
    #         dest_folder = dataset_archive / dataset_name / folder
    #         print(f"  [{dataset_name}] copying {src_folder} to {dest_folder}")
    #         shutil.copytree(
    #             src_folder,
    #             dest_folder
    #         )
    #     else:
    #         print(f"  [{dataset_name}] source folder {src_folder} does not exist, skipping copy")

    # shutil.copytree(
    #     ds_path,
    #     f"{dataset_archive}/{dataset}"
    # )
    
    # make an archive of datasets from the curated bucket
    #  - dataset's metadata/release/
    #  - dataset's metadata/original/ 
    #  - datasets's file_metadata/    
    local_metadata_path = dataset_archive / dataset_name / "metadata" 

    if not (local_metadata_path).exists():
        print(f"  [{dataset_name}] create dataset archive directory")
        local_metadata_path.mkdir(parents=True, exist_ok=True)

    local_fmetadata_path = dataset_archive / dataset_name / "file_metadata" 
    if not local_fmetadata_path.exists():
        print(f"  [{dataset_name}] create dataset file_metadata directory")
        local_fmetadata_path.mkdir(parents=True, exist_ok=True)

    ao.gcloud_rsync(f"{ds_bucket}/metadata/", f"{local_metadata_path}/",directory=True,clobber=True)
    ao.gcloud_rsync(f"{ds_bucket}/file_metadata/", f"{local_fmetadata_path}/",directory=True,clobber=True)


    
    # make a copy of the release metadata in the dest metadata/
    # find out which 
    # ao.gcloud_rsync(f"{ds_bucket}/metadata/release/", f"{dataset_archive}/{dataset}/metadata/",directory=True,clobber=False)

# NOW SYNC THE COLLECTIONS TO THE ARCHIVE

# %%
# now clean up archive and remove all folders from metadata/ that are not named "release"
for dataset_name, dataset_info in datasets.items():

    # if dataset_name  in new_datasets:
    #     print(f"  [{dataset_name}] skipping dataset")
    #     continue


    dataset_path = archive_path / dataset_name
    metadata_path = dataset_path / "metadata"
    # for item in metadata_path.iterdir():
    #     if item.is_dir() and item.name != "release":
    #         print(f"  [{dataset_name}] removing non-metadata directory: {item.name}")
    #         shutil.move(item, item.parent / f"release" / item.name)
    #         # shutil.rmtree(item)


    # # copy the dataset.json from the cloud-datasets repo to the archive dataset
    # # shutil.copy2(
    # #     datasets_repo_path / "datasets" / dataset_name / "dataset.json",
    # #     dataset_path / "dataset.json"
    # # )
    # # load the json
    # ds_path = datasets_repo_path / "datasets" / dataset_name

    # with open(ds_path / "dataset.json", "r") as f:
    #     dataset_json = json.load(f)
    # # get the max release
    # with open(dataset_path / "dataset.json", "w") as f:
    #     json.dump(dataset_json, f, indent=2)

    with open(dataset_path / "dataset.json", "r") as f:
        dataset_json = json.load(f)

    releases = sorted(dataset_json["releases"].keys(), reverse=True) 

    print(f"  [{dataset_name}] dataset releases: {releases}")

    for release in releases:
        # check if exists... if so copy it
        check_path = dataset_path / "metadata" / "release" / release
        if check_path.exists():
            print(f"  []found release metadata, copying {check_path.name} to {dataset_path / 'metadata'} ")
            # now copy the release metadata to the archive
            for item in check_path.iterdir():
                if item.is_file():
                    dest_path = dataset_path / "metadata" / item.name
                    shutil.copy2(f"{item}", f"{dest_path}")
                    print(f"    copying {item} -> {dest_path} ")
                
            break
        # results = ao.gcloud_ls(f"{ds_bucket}/metadata/release",prefix=f"{release}")
 
    # check if a file_metadata/release/ exists
    check_path1 = dataset_path / "file_metadata" / "release"
    if check_path1.exists():
       for release in releases:
            check_path = dataset_path / "file_metadata" / "release" / release
            if check_path.exists():
                print(f"  []found release file_metadata, copying {check_path.name} to {dataset_path / 'file_metadata'} ")
                # now copy the release file_metadata to the archive
                for item in check_path.iterdir():
                    if item.is_file():
                        dest_path = dataset_path / "file_metadata" / item.name
                        shutil.copy2(f"{item}", f"{dest_path}")
                        print(f"    copying {item} -> {dest_path} ")
                break



# now sync the release resources bucket with the archive


# %%    
# now loop through all collections and begin to build the archive
# TODO: NEED TO ALSO UPDATE THE COHORT DATASET COLLECTIONS.

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
        f"{releases_archive}/{release}"
    )




# %%
spreadsheet_id = ao.GOOGLE_SHEET_ID

# load releases.json
with(releases_repo_path /f"releases.json").open("r") as f:
    releases_info = json.load(f)

cdes = []
for _, release_info in releases_info.items():
    release_version = release_info["release_version"]
    cdes.append(release_info["cde_version"])

cde_vers = list(set(cdes))
cde_vers.sort()
# make cde archive
cde_repo_path = root_path / "cloud-cde"

for cde_ver in cde_vers:
    print(f"  [{cde_ver}] read google sheet")

    CDE = ao.read_google_sheet(spreadsheet_id, tab_name=cde_ver)

    cde_path = cde_repo_path / f"ASAP_CDE_{cde_ver}.csv" 
    CDE.to_csv(cde_path, index=False)


# downoad
# copy all ASAP_CDE_*.csv to the archive
archive_cde_path = archive_path / "CDE"
if not archive_cde_path.exists():
    print(f"  [{archive_cde_path}] create CDE archive directory")
    archive_cde_path.mkdir(parents=True, exist_ok=True)

for cde_ver in cde_vers:
    cde_path = cde_repo_path / f"ASAP_CDE_{cde_ver}.csv" 
    shutil.copy2(
        cde_path,
        archive_cde_path / f"ASAP_CDE_{cde_ver}.csv"
    )

# %%
# consider adding all the DOI stuff..?

#############################
# %%
# now loop through all the subdirectories of the release_archive and rsync with the bucket

release_resources_bucket = f"gs://asap-crn-cloud-release-resources"

for directory in archive_path.iterdir():
    if directory.is_dir():
        print(f"  [{directory}] rsync with bucket -> {release_resources_bucket}/{directory.name}")
        ao.gcloud_rsync(str(directory), f"{release_resources_bucket}/{directory.name}", directory=True, clobber=True)


# %%
