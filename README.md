# cloud-orchestration

Central management system for the ASAP CRN Cloud data infrastructure. Python scripts maintain the source-of-truth archives for ASAP CRN Cloud entities: _Datasets_, _Collections_, and _Releases_.

## Managed Repositories

| Repository | Purpose |
|---|---|
| [ASAP-CRN/cloud-datasets](https://github.com/ASAP-CRN/cloud-datasets) | Source-of-truth archive for all team-contributed datasets |
| [ASAP-CRN/cloud-collections](https://github.com/ASAP-CRN/cloud-collections) | Curated collections of datasets, versioned for VWB Data Collections |
| [ASAP-CRN/cloud-releases](https://github.com/ASAP-CRN/cloud-releases) | Release records tying datasets and collections to versioned snapshots |
| [ASAP-CRN/cloud-cde](https://github.com/ASAP-CRN/cloud-cde) | Common Data Element definitions and versioning |

## Functionality

### Dataset lifecycle

Datasets follow a versioned lifecycle tied to Zenodo DOIs:

1. **WIP** — new dataset is staged in `WIP/` with a `version` file and optional stub `dataset.json`
2. **Acceptance** — `dataset.json` is created with a concept DOI (`v0.1`), buckets, and metadata
3. **First release** — dataset version bumped to `v1.0`, DOI files written, archive snapshot created
4. **Updates** — major/minor version bumps produce new archive snapshots and updated DOI files

The repo also contains summaries of the dataset references and DOI / README generating docs. i.e. `dataset.json`, `datasets.json`, etc.

### Releases

Regular releases publish newly accepted or updated datasets:

- **Urgent releases** — newly accepted, uncurated datasets
- **Minor/Major releases** — updated or newly curated datasets, typically organized into Collections

Each release record enumerates which datasets (and dataset versions) and collections belong to it, along with the CDE version in effect. Urgent releases are "un-curated". Minor and Major releases may introduce curated data to the dataset, and include said datasets into Collections.

### Scripts

Release and dataset management scripts live in `scripts/`. Scripts follow a release-version-specific naming convention. Two templates cover the main workflows:

| Script | Purpose |
|---|---|
| `add_v0.1_Dataset_TEMPLATE.py` | **Template** — new dataset acceptance: define metadata stubs, ingest DOI `.docx`, create `v0.1` Zenodo draft |
| `make_vX_release_TEMPLATE.py` | **Template** — full release definition and collection update workflow (copy and fill in per release) |

Per-release scripts are named after the release version they target:

| Script pattern | Purpose |
|---|---|
| `define_v.X.Y.Z_release.py` | Assemble all datasets and collections, build `ReleaseDefinition`, write `release.json` to cloud-releases |
| `add_vX.Y.Z_release_DOIs.py` | Attach published Zenodo DOIs to dataset records after deposition |
| `sync_vX.Y.Z_release_DOIs.py` | Sync and verify local DOI files against Zenodo for a release |
| `update_vX.Y.Z_release_DOIs.py` | Update Zenodo deposition metadata for datasets in a release |
| `finish_vX.Y.Z_release.py` | Finalize release: promote WIP datasets, record release in `dataset.json` |
| `fix_vX.Y.Z_release_DOIs.py` | One-off fixes for specific DOI issues in a release |
| `collection_curation_vX.Y.Z.py` | Manage collection version entries for a release |
| `WIP_datasets_notes.py` | Working notes and status tracking for in-progress datasets |

## Architecture

The `asap_orchestrator` Python package (`src/asap_orchestrator/`) is installed via `pip install -e .` and imported as:

```python
import asap_orchestrator as ao
```

### Modules

| Module | Key exports | Purpose |
|---|---|---|
| `models.py` | `Dataset`, `DatasetBuckets`, `Creator`, `ReleaseRecord`, `ReleaseDefinition`, `Collection`, `CollectionDefinition`, `DatasetEntry`, `CollectionEntry` | Pydantic models and I/O for `dataset.json`, `release.json`, `collection.json` artifacts |
| `dataset.py` | `define_dataset`, `create_dataset_stub`, `fill_dataset_stub`, `read_dataset_entry`, `create_dataset_doi`, `update_dataset_doi`, `publish_dataset_doi`, `update_dataset_version`, `update_datasets_index` | Dataset lifecycle operations in cloud-datasets |
| `release.py` | `define_release`, `perform_release` | Release composition and writing to cloud-releases |
| `collection.py` | `define_collection`, `update_collection`, `update_collections_index` | Collection version management in cloud-collections |
| `doi.py` | `setup_DOI_info`, `ingest_DOI_doc`, `make_readme_file`, `finalize_DOI`, `bump_doi_version`, `add_anchor_file_to_doi`, `replace_anchor_file_in_doi`, `update_doi_metadata`, `publish_doi`, `archive_deposition_local`, `get_doi_from_dataset`, `create_draft_metadata`, `create_dataset_json` | Zenodo DOI creation, ingestion of team `.docx` reference docs, README/PDF generation |
| `zenodo_util.py` | `ZenodoClient` | REST API client wrapping Zenodo deposition operations |
| `bucket_util.py` | `gcloud_ls`, `gcloud_rsync`, `gcloud_cp`, `gcloud_mv`, `gcloud_rm`, `create_collection_bucket`, `describe_bucket` | GCS bucket operations via `gcloud storage` |
| `google_spreadsheets.py` | `read_google_sheet`, `GOOGLE_SHEET_ID` | Read the CDE schema from the ASAP CRN Google Sheet |
| `util.py` | `get_dataset_version`, `get_release_version`, `get_cde_version`, `write_version`, `archive_CDE` | File-level version and CDE archive utilities |

### Example usage

```python
import asap_orchestrator as ao

# ── Dataset acceptance (WIP, v0.1) ──────────────────────────────────────
ds_def = ao.define_dataset(
    name="teamX-pmdbs-sn-rnaseq",
    collection="pmdbs-sc-rnaseq",
    cde_version="v4.1",
)
ds_path = ao.create_dataset_stub(ds_def, datasets_repo_path="/path/to/cloud-datasets")

ao.setup_DOI_info(ds_path, ref_doc, publication_date="2026-06-10")
zenodo = ao.setup_zenodo()
ao.create_dataset_doi(ds_path, zenodo, version="v0.1")

# ── Release definition ───────────────────────────────────────────────────
release_def = ao.define_release(
    release_version="v5.0.0",
    release_type="Major",
    cde_version="v4.4",
    datasets=all_dataset_entries,
    new_datasets=new_dataset_entries,
    collections=collection_entries,
)
ao.perform_release(release_def, releases_repo_path="/path/to/cloud-releases")

# ── Collection update ────────────────────────────────────────────────────
col_def = ao.define_collection(
    collection_name="pmdbs-sc-rnaseq",
    new_version="v3.2.0",
    new_datasets=["teamX-pmdbs-sn-rnaseq"],
    release_def=release_def,
)
ao.update_collection(col_def, collections_repo_path="/path/to/cloud-collections")

# ── Rebuild master indexes ───────────────────────────────────────────────
ao.update_datasets_index("/path/to/cloud-datasets")
ao.update_collections_index("/path/to/cloud-collections")
```

### Known legacy / unused functions

The following functions exist in the module but are superseded, not exported from the package, or dead code:

| Function | Module | Status |
|---|---|---|
| `update_study_table_with_doi` | `doi.py` | Listed in `doi.__all__` but function body is entirely commented out — safe to remove |
| `setup_DOI_info_v1` / `ingest_DOI_doc_v1` | `doi.py` | Legacy v1 variants; not exported; superseded by `setup_DOI_info` / `ingest_DOI_doc` |
| `create_draft_doi` | `doi.py` | In `doi.__all__` but not re-exported from package; superseded by `dataset.create_dataset_doi` |
| `get_published_deposition` | `doi.py` | Not re-exported from package; internal use only |
| `make_pdf_file` | `doi.py` | Not re-exported from package; internal helper called by `make_readme_file` |
| `authenticate_with_service_account` | `bucket_util.py` | Marked `# NOTE: this is deprecated` in source; still exported |
| `gcloud_ls_long` | `bucket_util.py` | Not in `__all__`; debug variant of `gcloud_ls` |

## Repository Structure Overview

### cloud-datasets
```
datasets.json                            # Master index of all datasets (rebuilt by update_datasets_index())
WIP/                                     # Staging area for in-progress datasets
└── <dataset-name>/
    ├── dataset.json                     # Stub metadata (optional)
    └── version                          # Target version string
datasets/
└── <dataset-name>/                      # format: <team>-<tissue>-<modality>[-<qualifier>]
    ├── dataset.json                     # Canonical metadata: DOI, GCS buckets, releases, CDE version
    ├── version                          # Current version string (source of truth)
    ├── DOI/                             # Zenodo deposition files for current version
    │   ├── project.json                 # Full project/team metadata (from ingested .docx)
    │   ├── <dataset-name>.json          # Zenodo upload metadata
    │   ├── <dataset-name>_README.md     # Generated README
    │   ├── <dataset-name>_README.pdf    # Generated README (anchor file for Zenodo)
    │   ├── dataset.doi                  # Concept DOI (all versions)
    │   ├── version.doi                  # Version-specific DOI
    │   └── deposition.json              # Full Zenodo deposition response
    ├── refs/                            # Reference files for current version
    └── archive/                         # Immutable snapshots of past versions
        └── <version>/
            ├── dataset.json             # Version snapshot
            ├── DOI/
            └── refs/
```

### cloud-collections
```
collections.json                         # Master index of all collections
└── <collection-name>/
    ├── collection.json                  # Metadata: DOI, versions, datasets per release
    └── archive/<version>/
        └── collection.json              # Version-specific metadata snapshot
```

### cloud-releases
```
releases.json                            # Master index of all releases
└── <release-version>/
    ├── release.json                     # Snapshot: all datasets, new_datasets, collections, CDE version
    └── *README*.pdf                     # Release-specific README
```

### cloud-cde
```
cdes.json                                # Index of all CDE versions
└── <cde-version>/
    ├── cde.json                         # CDE date, version, list of tables
    └── cde.csv                          # Snapshot CDE schema table
```

## Bootstrap

The `bootstrap/` directory contains scripts, tools, and templates used to create the historical (pre v4.0.1) archive of Datasets, Collections, and Releases.
