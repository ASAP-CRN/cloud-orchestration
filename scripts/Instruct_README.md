
# cloud-orchestration
Central management system for the ASAP CRN Cloud data infrastructure. Python scripts maintain the source-of-truth archives for ASAP CRN Cloud entities: _Datasets_, _Collections_, _Releases_, and IN THE FUTURE _Common Data Elements (CDE)_.  Ignore cloud-cde for now.

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

### Releases

Regular releases publish newly accepted or updated datasets:
- **Urgent releases** — newly accepted, uncurated datasets
- **Minor/Major releases** — updated or newly curated datasets, typically organized into Collections

Each release record enumerates which datasets (and dataset versions) and collections belong to it, along with the CDE version in effect.

### Scripts

## Architecture
The `asap_orchestrator` Python package (`src/asap_orchestrator/`) provides:
provides a bunch of helper tools.  Read `scripts/define_v4.1.1_release.py` for some context.

``` python3
import asap_orchestrator as ao

```

## Repository Structure Overview

### cloud-datasets
```
datasets.json                            # Master index of all datasets (rebuilt by sync_cloud_datasets.py)
WIP/                                     # Staging area for in-progress datasets
└── <dataset-name>/
    ├── dataset.json                     # Stub metadata (optional)
    └── version                          # Target version string
datasets/
└── <dataset-name>/                      # format: <team>-<tissue>-<modality>[-<qualifier>]
    ├── dataset.json                     # Canonical metadata: DOI, GCS buckets, releases, CDE version
    ├── version                          # Current version string (source of truth)
    ├── DOI/                             # Zenodo deposition files for current version
    │   ├── <dataset-name>.json
    │   ├── dataset.doi                  # Concept DOI (all versions)
    │   ├── version.doi                  # Version-specific DOI
    │   └── deposition.json
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
    ├── collection.json                  # Metadata: DOI versions, datasets per release version
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


## TASK
The pydantic models supporting the Dataset structuring and modifications are working well.  Make pydantic models for Releases and Collections.  The individual collection `collection.json` seem to be accurate through the v4.1.1 "release".  Please make the `collections.json` reflect that data.  (And test for self-consistency between the Dataset and Release references.)



IGNORE BELOW:
### cloud-cde
```
cdes.json                                # Index of all CDE versions
└── <cde-version>/
    ├── cde.json                         # CDE date, version, list of tables
    └── cde.csv                          # Snapshot CDE schema table
```

## Bootstrap
The `bootstrap/` directory contains scripts, tools, and templates used to create the historical (pre v4.0.1) archive of Datasets, Collections, and Releases. 
