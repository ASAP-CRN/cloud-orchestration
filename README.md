# cloud-orchestration

Central management system for the ASAP CRN Cloud data infrastructure.  Initially this will use python scripts maintain the source-of-truth archives for ASAP CRN Cloud entities: _Datasets_, _Collections_, _Releases_, and _Common Data Elements (CDE)_.  In the future we would like to use configuration files and GitHub Actions to perform the maintainebce.

## Managed Repositories

| Repository | Purpose |
|---|---|
| [ASAP-CRN/cloud-datasets](https://github.com/ASAP-CRN/cloud-datasets) | Source-of-truth archive for all team-contributed datasets |
| [ASAP-CRN/cloud-collections](https://github.com/ASAP-CRN/cloud-collections) | Curated collections of datasets, versioned for VWB Data Collections |
| [ASAP-CRN/cloud-releases](https://github.com/ASAP-CRN/cloud-releases) | Release records tying datasets and collections to versioned snapshots |
| [ASAP-CRN/cloud-cde](https://github.com/ASAP-CRN/cloud-cde) | Common Data Element definitions and versioning |

## Functionality

Functionality involves several steps which create effects in _Datasets_, _Collections_, _Releases_, _CDE_ repos.  

### Dataset DOI creation and version maintanence
As contributions to the ASAP CRN Cloud are _Accepted_ one of the first steps is to create a zenodo Dataset DOI.  Datasets are _accepted_ as "v0.1".  When Datasets are first released, the Datasets are version bumped to "v1.0".   Any additional changes to Datasets can result in major or minor version bumps (depending on the revisions being made.) A Dataset's _all versions_ reference is contained in the "dataset.doi" file. Individual release version references are kept in "version.doi" files organized by version.

functions:
- `create_dataset`
    - `make_wip_dataset`
    - `create_dataset_doi`:  
- `publish_dataset`:  
    - `publish_dataset_doi`:  
- `update_dataset`:  
    - `update_dataset_doi`:  
    - `update_dataset_version`:

Scripts named by tranches of datasets will use these functions to compose configurations for each dataset (new_dataset.json), and then either update or create and then publish those datasets.


### Releases
Regular _"Urgent" Releases_ to ASAP CRN Cloud are made for newly _Accepted_ but uncurated Datasets.    Less regular "Major" or "Minor" Releases are made to release new or updated _Curated_ Datasets.  _Curated_ Datasets are organized into Collections which share common Curation workflows/pipelines.   

#### functions:
- `define_release`:  Enumerates the release number, what type of release (Urgent, Minor, Major), and which individual Datasets and Colections belong to the Release.
- `perform_release`: Create `release.json`, and manage the release archive, and produce the releases.json

Scripts named by versions will use these functions to compose configurations for each release update (new_release.json), and then create those releases.  Note that new_collections.json may be defined using the functions detailed below.


### Collection
"Major" or "Minor" Releases are made to release new or updated _Curated_ Datasets.  _Curated_ Datasets are organized into Collections which share common Curation workflows/pipelines.   


#### functions:
- `define_collection`:  Reads the Collection update from the `define_release` described above. 
- `update_collection`:  Reads the Collection details created from `define_collection` described above and updates the details. 





## Architecture

The `asap_orchestrator` Python package coordinates operations across all managed repositories.

``` python3
import asap_orchestrator as ao

```

##  api spec

TBC 


## Repository Structure Overview

### cloud-datasets
```
datasets.json                            # Master index of all datasets
├── WIP/                                 # Triage area for WIP Datasets not yet released
|    └──<dataset_name>/  
|       ├── wip_files
:       :
└── <dataset_name>                           # format: <team>-<tissue>-<modality>_<unique_name>
    ├── dataset.json                         # Metadata: DOI, GCS buckets, releases, CDE version
    ├── DOI/                                 # Zenodo deposition files and DOI references
    ├── refs/                                # Reference files for current version
    └── archive/<version>/                   # Immutable snapshots of past versions
        └── DOI/                             # Version-specific DOI files
```

### cloud-collections
```
collections.json                         # Master index of all collections
└── <collection-name>/
    ├── collection.json                      # Metadata: DOI versions, datasets per release version
    └── archive/<version>/                   # Immutable snapshots of past versions
        └── collection.json                  # Version-specific metadata snapshot
```

### cloud-releases
```
releases.json                            # Master index of all releases
└── <release-version>/
    ├── release.json                         # Snapshot: all datasets, new_datasets, collections, CDE 
    └── *README*.pdf                            # Release-specific README
```

### cloud-cde
```
cdes.json                                 # Index of all Common Data Elements with versions
└── <cde-version>/
    ├── cde.json                         # CDE date, version, list of tables 
    ├── cde.csv                          # Snapshot CDE schema table  
```

## Bootstrap 

The `bootstrap/` directory contains scripts, tools, and templates used to create the historical (pre Release v4.0.1) archive of Datasets, Collections, and Releases.  An initial YOLO stab of Claude generated code for the `asap_orchestrator` is also here.
