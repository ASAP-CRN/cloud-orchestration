# %% [markdown]
# # ASAP CRN — Release Template
#
#. curation bucket composition for supporting VWB Data Collections, and overall versioning.
# **Lifecycle covered here:**
#   1. Get Collection definitions for the Release
#   2. locate individual dataset locations (curated buckets)
#   3. create versioned bucket (if nescessary)
#   4. copy files between buckets
#   5. create summary (add bucket locations to cloud-collection bucket)
#
# DO NOT EXECUTE THIS FILE DIRECTLY — it is a template only.

# %% Setup
from pathlib import Path
import asap_orchestrator as ao
import json
import pandas as pd

# TODO: confirm the root path resolves correctly for your environment
root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"
collections_repo_path = root_path / "cloud-collections"
releases_repo_path = root_path / "cloud-releases"

import os
os.environ["CLOUDSDK_PYTHON"] = "/opt/homebrew/opt/python@3.13/bin/python3.13"

%load_ext autoreload
%autoreload 2


# #NEW COLLECTION
# # invitro-bulk-rnaseq
# asap-crn-invitro-bulk-rnaseq-collection-v1

# #DATASETS
# team-jakobsson-invitro-bulk-rnaseq-dopaminergic DOI:10.5281/zenodo.17149266
# team-jakobsson-invitro-bulk-rnaseq-microglia DOI: 10.5281/zenodo.17149290
# asap-cohort-invitro-bulk-rnaseq


# # pmdbs-sc-atac
# asap-crn-pmdbs-sc-atacseq-collection-v1
# team-voet-pmdbs-sn-atacseq-10x


# mouse-spatial-rnaseq: release v4.0.0 has DOI ...16979297 but collection_doi is ...16979296 — consecutive Zenodo IDs, likely the version-specific DOI was stored in the release instead of the concept DOI
# pmdbs-sc-rnaseq v3.1.1: the collection entry says release.version=v4.1.0 but v4.1.0's release.json doesn't include pmdbs-sc-rnaseq — it was actually released in v4.1.1 (data inconsistency in the collection.json)
# All 5 collection archives: missing collection.json files (only DOI/ subdirs exist, backfill needed)



pmdbs_sc_atacseq = {
    "name": "pmdbs-sc-atacseq",
    "title": "PMDBS single-cell ATACseq",
    "collection_doi": "10.5281/zenodo.17149266",
    "current_version": "v1.0.0",
    "doi": "10.5281/zenodo.17149267",
    "datasets": [
      "voet-pmdbs-sn-atacseq-10x"
    ],
    "curation": {
      "bucket": "gs://asap-crn-pmdbs-sc-atacseq-collection-v1",
      "datasets": {
          "voet-pmdbs-sn-atacseq-10x" : "gs://asap-curated-team-voet-pmdbs-sn-atacseq-10x/release/v1.0.0/"
      },
        "workflow" : {
          "name": "bulk_rnaseq_analysis-v2.0.0",
          "version":"v2.0.0",
          "github_url":"https://github.com/ASAP-CRN/bulk-rnaseq-wf/releases/tag/bulk_rnaseq_analysis-v2.0.0",
        },
    },  
    "release": {
      "version": "v5.0.0",
      "cde_version": "v4.3",
      "date": "2026-06-15"
    },
    "versions": {
      "v1.0.0": {
        "version": "v1.0.0",
        "date": "2025-12-15",
        "doi": "10.5281/zenodo.20400939",
        "datasets": [
          "voet-pmdbs-sn-atacseq-10x"
        ],
        "teams": [
          "voet",
        ],
        "types": [
          "pmdbs-sc-atacseq"
        ],
        "curation": {
          "bucket": "gs://asap-crn-pmdbs-sc-atacseq-collection-v1",
          "datasets": {
              "voet-pmdbs-sn-atacseq-10x" : "gs://asap-curated-team-voet-pmdbs-sn-atacseq-10x/release/v1.0.0/"
          },
          "workflow" : {
            "name": "bulk_rnaseq_analysis-v2.0.0",
            "version":"v2.0.0",
            "github_url":"https://github.com/ASAP-CRN/bulk-rnaseq-wf/releases/tag/bulk_rnaseq_analysis-v2.0.0",
          },
        },
        "release": {
          "version": "v5.0.0",
          "cde_version": "v4.3",
          "date": "2026-06-15"
        }
      }
    }
}



# %% [Step 1] Release parameters
# TODO: fill in release version, type, CDE version, and optional release DOI
RELEASE_VERSION = "v5.0.0"    # e.g. "v4.1.0"
RELEASE_TYPE = "Major"        # "Urgent" | "Minor" | "Major"
CDE_VERSION = "v4.3"          # e.g. "v3.3"
RELEASE_DOI = "10.5281/zenodo.20186059"      
RELEASE_DATE = "2026-06-15"
# %% [Step 1] 
#. get collections

# load collections.json
with open(collections_repo_path / "collections.json", "r") as f:
    collections = json.load(f)

# %%


# make a table of from, to

copy_dirs = ["artifacts","file_metadata","metadata"]
outs = []
# col_manifests = {}

c_info = pmdbs_sc_atacseq
c_name = c_info["name"]

# define bucket by getting the base version.
full_version = c_info["current_version"]
version = full_version.split(".")[0]

#
collection_bucket = f"gs://asap-crn-{c_name}-collection-{version}"

datasets = c_info["datasets"]


buk = ao.describe_bucket(collection_bucket)
# if not make the bucket
if len(buk)<1:
    print(f"need to make collection bucket: {collection_bucket}")
    ao.create_collection_bucket(collection_bucket)
else:
    print(f"we already have a collection bucket... just need to rsync data")



# %%
print(f"DATASET: {c_name}::  source -> destination")
datasets = c_info["datasets"]
for ds in datasets:
  if "spatial" in ds:
      if "geomx" in ds:
          dirs = copy_dirs + ["spatial", "spatial_geomx"]
      elif "visium" in ds:
          dirs = copy_dirs + ["spatial","spatial_visium"]
      else:
          print(f"ERROR:  non-geomx or visium {ds}")
  else:
      dirs = copy_dirs + [c_name.replace("-","_")]

  # print(f"################################\nfound these dirs: {dirs} for dataset: {ds}\n################################\n")


  ds_ver = 'v1.0'
  if "cohort" in ds:
    ds_bucket = f"gs://asap-curated-{ds}"
  else:
    ds_bucket = f"gs://asap-curated-team-{ds}"



  # # load datset.json
  # ds_path = datasets_repo_path / "datasets" / ds
  # with open(ds_path / "dataset.json", "r") as f:
  #     ds_info = json.load(f)
  # dataset_model = ao.Dataset.load(ds_path)
  # ds_ver = dataset_model.version

  c_rel_ver = rel_highest = "v5.0.0"

  # ds_bucket = dataset_model.buckets.prod
  # c_rel_ver = c_info["release"]["version"]  # curated data
  # rel_highest = max(dataset_model.releases.keys())  # metadata
  # print(f"|{ds}\t|\t{c_rel_ver=}\t|\t{rel_highest=}")

  all_manifests = pd.DataFrame()

  caveats = []
  for d in dirs:
    ds_source = f"{ds_bucket}/{d}"
    ds_dest = f"{collection_bucket}/{ds}/{d}"


    manifest=pd.DataFrame()

    # if d != "pmdbs_sc_atacseq":
    #   continue

    skip_archive = False
    if d in ["spatial_visium", "spatial_geomx","pmdbs_bulk_rnaseq","pmdbs_sc_rnaseq","mouse_bulk_rnaseq","mouse_sc_rnaseq","invitro_bulk_rnaseq","pmdbs_sc_atacseq"]:
      # curated artifacts
      # need to find the ghithest version in the release.
      ds_sourcepath = f"{d}/release/"
      # we need to loop over the subdirectories
      subdirs = ao.gcloud_ls(ds_bucket,prefix=ds_sourcepath)

      curated_vers = [sd.split("/")[-2] for sd in subdirs if sd != ""]
      max_ver = max(curated_vers)

      ds_source = f"{ds_bucket}/{d}/release/{max_ver}"
      ds_dest = f"{collection_bucket}/{ds}/{d}"
      text = f"The curated files in this directory were copied from the dataset's curated bucket (`{ds_bucket}/{d}/release/{max_ver}/`) to the collection bucket (`{collection_bucket}/{ds}/{d}/`).  The version numbers represent the most recent _release_ version of the curated data.  This is not the same as the _collection_ version ({version})."
      subdirs = ao.gcloud_ls(ds_bucket,prefix=f"{d}/release/{max_ver}/")
      subdirs = [sd for sd in subdirs if sd.endswith("/")]

      # # # # first remove ds_dest if it exists
      ao.gcloud_rm(ds_dest, directory=True)
      # # # also remove archive.
      # ao.gcloud_rm(f"{collection_bucket}/{ds}/archive/", directory=True)
      skip_archive = True

    elif d in ["metadata","file_metadata"]:
      ds_source = f"{ds_bucket}/{d}/release/{rel_highest}"
      ds_dest = f"{collection_bucket}/{ds}/{d}"
      text = f"The metadata files in this directory were copied from the dataset's curated bucket (`{ds_bucket}/{d}/release/{rel_highest}/`) to the collection bucket (`{collection_bucket}/{ds}/{d}/`).  The version numbers represent the most recent _release_ version of the curated data. This is not the same as the _cde_ version, but simply the most recent release's Dataset and File metadata."
      # #  remove ds_dest if it exists
      ao.gcloud_rm(ds_dest, directory=True)
      skip_archive = False
      

    else:
      ds_source = f"{ds_bucket}/{d}"
      ds_dest = f"{collection_bucket}/{ds}/{d}"
      text = f"The artifact files in this directory were copied from the dataset's curated bucket (`{ds_bucket}/{d}/`) to the collection bucket\n(`{collection_bucket}/{ds}/{d}/`)."
      # # #  remove ds_dest if it exists
      ao.gcloud_rm(ds_dest, directory=True)
      skip_archive = False
      

    print(f"{ds_source} -> {ds_dest}")

    # skip archive ... we'll create it later
    if skip_archive:
        # we need to loop over the subdirectories
        # defined above
        for sd in subdirs:
            if sd in ["archive", ""]:
                continue
            sd_source = f"{sd}"
            sd_dest = f"{ds_dest}/{sd.split("/")[-2]}"
            print(f"+++++++++ {ds}:{sd_source} -> {sd_dest}")

            if sd_source.endswith("VERSION"):
              ao.gcloud_rsync(sd_source,sd_dest, directory=False, dry_run=False)
            else:
              ao.gcloud_rsync(sd_source,sd_dest, directory=True, dry_run=False)

    else: 
      print(f"SKIP{ds}:{ds_source} -> {ds_dest}")
      ao.gcloud_rsync(ds_source,ds_dest, directory=True, dry_run=False)

    print(f"XXXXXX{ds}:{ds_source}\n\t-> {ds_dest}")
    # print(f"TEXT ::: {text}")

    caveats.append(text)

    manifest.loc[0,"dataset"] = ds
    manifest.loc[0,"source_url"] = ds_source
    manifest.loc[0,"dest_url"] = ds_dest
    print(f"{ds}:{ds_source}\n\t-> {ds_dest}")
    # file
    manifest_dest = f"{ds_dest}/data_source.csv"
    
    # make temp file for manifest_source
    if not (collections_repo_path / c_name).exists():
      (collections_repo_path / c_name).mkdir()

    manifest_source = collections_repo_path / c_name / f"data_source_{d}.csv"
    manifest.to_csv(manifest_source)

    # copy the message
    readme_source = collections_repo_path / c_name / f"README_{d}.txt"
    with open(readme_source, "w") as f:
        f.write(text)

    ao.gcloud_cp(readme_source,f"{ds_dest}/sourceREADME.txt", directory=False, dry_run=False)
    ao.gcloud_cp(manifest_source,f"{ds_dest}/data_source.csv", directory=False, dry_run=False)


    # copy version files
    ver_src = collections_repo_path / c_name / "VERSION"
    ver_dest = f"{ds_dest}/version.txt"

    all_manifests = pd.concat([all_manifests, manifest])



  all_manifest_source = collections_repo_path / c_name / f"data_source.csv"
  all_manifests.to_csv(all_manifest_source)


# all_manifests = all_manifests.reset_index(drop=True)
# col_manifests[c_name] = all_manifests

# %%



# %%
# %%


# %%

ASAP - Production-Ready Bucket Creation Guide
Purpose
Enable DTi to create collection buckets in the ASAP GCP project: dnastack-asap-parkinsons, for use in Verily Workbench. These buckets will contain copies of the data from the curated buckets to ensure alignment with Verily’s Data Collection versioning structure.

DTi will own these buckets, including their creation, ongoing maintenance, and eventual deprecation. DNAstack will provide assistance as needed throughout the process.
Requirements
*Collection bucket versions should mirror Verily Data Collection versions.

Proposed naming convention: asap-crn-<collection_name>-collection-<collection_version>
Bucket permissions
It is critical that the buckets are created in the correct project and location, and that the appropriate permissions are granted to the designated principals.
Steps

Create the bucket in us-central1 (Iowa) in the dnastack-asap-parkinsons GCP project.
Add asap-cloud-readers@verily-bvdp.com (all verified researchers) as Storage Object Viewer.
Add asap-dti@dnastack.com as Storage Object Admin.

Helpful gcloud commands
PROJECT="dnastack-asap-parkinsons"
REGION="us-central1"
DESTINATION_BUCKET="gs://asap-crn-pmdbs-sc-rnaseq-collection-v3"
SOURCE_BUCKET="gs://asap-curated-cohort-pmdbs-sc-rnaseq"


# To generate md5sum
gcloud config set storage/parallel_composite_upload_enabled False

# Create a bucket in us-central1
gcloud storage buckets create \
  --project="${PROJECT}" \
  --location="${REGION}" "${DESTINATION_BUCKET}"

# Add permissions to bucket
gcloud storage buckets add-iam-policy-binding "${DESTINATION_BUCKET}" \
  --member="group:asap-cloud-readers@verily-bvdp.com" \
  --role="roles/storage.objectViewer" \
  --project="${PROJECT}"

gcloud storage buckets add-iam-policy-binding "${DESTINATION_BUCKET}" \
  --member="group:asap-dti@dnastack.com" \
  --role="roles/storage.objectAdmin" \
  --project="${PROJECT}"

# Copy files
gcloud storage cp \
  --recursive \
  "${SOURCE_BUCKET}"/path/to/folder \
  "${DESTINATION_BUCKET}"/path/to/folder \
  --billing-project="${PROJECT}"
 

# Rsync files - dry run (remove flag for real run)
gcloud storage rsync \
  --recursive \
  --dry-run \
  "${SOURCE_BUCKET}"/path/to/folder \
  "${DESTINATION_BUCKET}"/path/to/folder \
  --billing-project="${PROJECT}"






# %% [Step 3] Build the full dataset list for the release manifest
# This must include ALL datasets (new + previously released).
# Read existing dataset entries directly from their dataset.json files so DOIs
# and versions stay in sync with the source of truth.

previous_release = "v4.0.1"
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

all_datasets_list = [ dict( name = data.name, doi=data.doi, version=data.version) for data in all_datasets]
new_datasets_list = [ dict( name = data.name, doi=data.doi, version=data.version) for data in new_dataset_defs]

# get collections
# none new in this release
collections={}
for ds in all_datasets:
    collection = ds.collection
    if collection is not None:
        collection_path = collections_repo_path / collection / "collection.json"
        with open(collection_path, "r") as f:
            collection_info = json.load(f)
        # find highest version
        collection_vers = {ver : x["release"]["version"] for ver,x in collection_info["versions"].items() }
        # check release.versiopn is NOT > current
        cver = max(collection_vers.keys())
        if collection_vers[cver]<RELEASE_VERSION:
            collections[collection] = dict(name=collection,doi=collection_info["collection_doi"],version=cver)

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
if not release_path.exists():
    release_path.mkdir()

with open(release_path / "release.json", "w") as f:
    json.dump(release_dict, f, indent=4)




############################    for name in previously_released_names
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
