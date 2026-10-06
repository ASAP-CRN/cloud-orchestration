# %% [markdown]
# # ASAP CRN — Release Archive v5.1.0
#
# Builds a local snapshot of release v5.1.0 under `release_archive/`, then syncs it
# to gs://asap-crn-cloud-release-resources.  Layout and copy rules are documented in
# `asap_orchestrator.archive_util`.
# Based on scripts/adhoc/create_v.4.1.1_release_archive.py.
#
# Every copy is an rsync with clobber=False (nothing is ever deleted at the destination).
# DRY_RUN = True (default) runs every step with --dry-run and writes nothing; the
# console log is rsync's own report:
#   - local copies (ao.local_rsync, system rsync):  ">f... <path>" per file to be written
#   - bucket copies (ao.gcloud_rsync):              "Would copy <src> to <dest>"
#
# Requires `gcloud auth login` (bucket rsync/ls) and Google Sheets credentials (CDE fallback).

# %% Setup
from pathlib import Path

import asap_orchestrator as ao

RELEASE_VERSION = "v5.1.0"

# True: rsync --dry-run everything, write nothing.  False: build release_archive/.
DRY_RUN = False
# Push release_archive/ to the release-resources bucket (only when DRY_RUN is False).
PUSH_TO_BUCKET = False

root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"
collections_repo_path = root_path / "cloud-collections"
releases_repo_path = root_path / "cloud-releases"
cde_repo_path = root_path / "cloud-cde"

archive_path = root_path / "release_archive"

n_files = 0

print(f"{'DRY RUN — nothing will be written' if DRY_RUN else 'BUILDING'}: {archive_path}")

# %% Datasets
n_files += ao.archive_datasets(
    RELEASE_VERSION, releases_repo_path, datasets_repo_path, archive_path, dry_run=DRY_RUN
)

# %% Collections
n_files += ao.archive_collections(
    RELEASE_VERSION, releases_repo_path, collections_repo_path, archive_path, dry_run=DRY_RUN
)

# %% Releases (all up to and including RELEASE_VERSION)
n_files += ao.archive_releases(RELEASE_VERSION, releases_repo_path, archive_path, dry_run=DRY_RUN)

# %% CDE (every CDE version used by an archived release)
n_files += ao.archive_cdes(
    RELEASE_VERSION, releases_repo_path, cde_repo_path, archive_path, dry_run=DRY_RUN
)

print(f"{'[DRY RUN] would write' if DRY_RUN else 'wrote'} {n_files} files into {archive_path}")

# %% Sync archive to the release-resources bucket
# On a dry run, prints a gcloud dry-run report for archive dirs already on disk.
PUSH_TO_BUCKET = True

if DRY_RUN or PUSH_TO_BUCKET:
    ao.push_archive_to_bucket(RELEASE_VERSION, releases_repo_path, archive_path, dry_run=DRY_RUN)
else:
    print("PUSH_TO_BUCKET is False, skipping rsync to the release-resources bucket")

# %%
