# cloud-orchestration

Central management system for the ASAP CRN Cloud data infrastructure. Uses a combination of AI (Claude Code) and GitHub Actions to maintain the source-of-truth archives for ASAP CRN Cloud entities: _Datasets_, _Collections_, _Releases_, and _Common Data Elements (CDE)_.

## Managed Repositories

| Repository | Purpose |
|---|---|
| [ASAP-CRN/cloud-datasets](https://github.com/ASAP-CRN/cloud-datasets) | Source-of-truth archive for all team-contributed datasets |
| [ASAP-CRN/cloud-collections](https://github.com/ASAP-CRN/cloud-collections) | Curated collections of datasets, versioned for VWB Data Collections |
| [ASAP-CRN/cloud-releases](https://github.com/ASAP-CRN/cloud-releases) | Release records tying datasets and collections to versioned snapshots |
| [ASAP-CRN/cloud-cde](https://github.com/ASAP-CRN/cloud-cde) | Common Data Element definitions and versioning |

## Architecture

The `asap_orchestrator` Python package coordinates operations across all managed repositories:

```
src/asap_orchestrator/
├── orchestrator.py       # Main coordination logic
├── cli.py                # Command-line interface
├── github_manager.py     # GitHub repository operations
├── zenodo_manager.py     # DOI generation and versioning via Zenodo
├── dataset_manager.py    # Dataset lifecycle management
├── collection_manager.py # Collection lifecycle management
└── cde_manager.py        # CDE versioning
```

## Installation

```bash
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and fill in your tokens:

- `GITHUB_TOKEN`: GitHub Personal Access Token with repo permissions
- `ZENODO_TOKEN`: Zenodo access token for DOI management

## Usage

### Command Line

```bash
# Process a release
asap-orchestrate release v1.0.0

# Create a dataset
asap-orchestrate create-dataset my-dataset --title "My Dataset" --description "Description"

# Create a collection
asap-orchestrate create-collection my-collection --title "My Collection" --datasets dataset1 dataset2
```

### GitHub Actions

The repository includes a GitHub Actions workflow that automatically processes releases:

1. Create a release in this repository with a version tag (e.g., `v4.0.0`)
2. The workflow will:
   - Update all managed repositories
   - Generate or update DOIs for new/modified datasets and collections via Zenodo
   - Create corresponding releases in the target repositories

### Manual Workflow Dispatch

1. Go to the Actions tab in GitHub
2. Select "Release Management" workflow
3. Click "Run workflow" and enter the version tag

## Release Process

A release ties a specific version of every dataset and collection together into a published, DOI-backed snapshot:

1. **Dataset acceptance** — new or updated datasets are scoped and associated with the release
2. **Collection update** — affected collections are versioned to include the new datasets
3. **DOI management** — new datasets get an initial DOI; updated datasets get a new version DOI via Zenodo
4. **Repository sync** — `releases.json`, `datasets.json`, and `collections.json` indexes are updated across all managed repos
5. **GitHub release** — release tags are created in each managed repository

## Repository Structure Overview

### cloud-datasets
```
datasets.json                            # Master index of all datasets
<team>-<tissue>-<modality>/
├── dataset.json                         # Metadata: DOI, GCS buckets, releases, CDE version
├── DOI/                                 # Zenodo deposition files and DOI references
├── refs/                                # Reference files for current version
└── archive/<version>/                   # Immutable snapshots of past versions
    └── DOI/                             # Version-specific DOI files
```

### cloud-collections
```
collections.json                         # Master index of all collections
<collection-name>/
├── collection.json                      # Metadata: DOI versions, datasets per release version
└── archive/<version>/                   # Immutable snapshots of past versions
    └── collection.json                  # Version-specific metadata snapshot
```

### cloud-releases
```
releases.json                            # Master index of all releases
<release-version>/
├── release.json                         # Snapshot: all datasets, new_datasets, collections, CDE 
└── *README*.pdf                            # Release-specific README
```

### cloud-cde
```
cde.json                                 # Index of all Common Data Elements with versions
```

## Bootstrap Templates

The `bootstrap/templates/` directory contains template READMEs and reference materials used when initializing or updating managed repositories.
