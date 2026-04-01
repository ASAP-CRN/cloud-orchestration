# cloud-orchestration
repo for controlling ASAP CRN  Dataset, Collection, CDE, and Release reference repos

## repos

- [ASAP-CRN/cloud-datasets](https://github.com/ASAP-CRN/cloud-datasets)
- [ASAP-CRN/cloud-collections](https://github.com/ASAP-CRN/cloud-collections)
- [ASAP-CRN/cloud-releases](https://github.com/ASAP-CRN/cloud-releases)
- [ASAP-CRN/cloud-cde](https://github.com/ASAP-CRN/cloud-cde)

## management strategy
Using a combination of AI (claude code) and github actions, maintanenence of the source-of-truth archive of the ASAP CRN Cloud entitites of _Datasets_, _Collections_, _Releases_, and Common Data Elements (_CDE_).

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

1. Create a release in this repository with a version tag (e.g., `v1.0.0`)
2. The workflow will:
   - Update all managed repositories
   - Generate DOIs for new datasets and collections via Zenodo
   - Create corresponding releases in the target repositories

### Manual Workflow Dispatch

You can also trigger the orchestration manually:

1. Go to Actions tab in GitHub
2. Select "Release Management" workflow
3. Click "Run workflow"
4. Enter the version tag to process

## Architecture

The orchestration system consists of several modules:

- `github_manager.py`: Handles GitHub repository operations
- `zenodo_manager.py`: Manages DOI generation and versioning via Zenodo
- `dataset_manager.py`: Manages datasets in cloud-datasets repo
- `collection_manager.py`: Manages collections in cloud-collections repo
- `orchestrator.py`: Main coordination logic
- `cli.py`: Command-line interface

## Repository Structure

Each managed repository maintains a JSON index file containing the current state:

### cloud-datasets
- **datasets.json**: Index of all datasets with DOIs and references
- **datasets/{name}/**: Individual dataset directories containing:
  - `metadata.json`: Dataset metadata including DOI
  - Dataset files

### cloud-collections  
- **collections.json**: Index of all collections with DOIs and references
- **collections/{name}/**: Individual collection directories containing:
  - `metadata.json`: Collection metadata including DOI and dataset references

### cloud-releases
- **releases.json**: Index of all releases with associated datasets and collections
- Release tags correspond to published versions

### cloud-cde
- **cde.json**: Index of Common Data Elements
- CDE definitions and metadata

## Repository Templates

The `templates/` directory contains README templates for each repository type:

- `README-datasets.md`: Template for cloud-datasets repository
- `README-collections.md`: Template for cloud-collections repository  
- `README-releases.md`: Template for cloud-releases repository
- `README-cde.md`: Template for cloud-cde repository

Use these templates to initialize the README files in each managed repository.

## Scripts

The `scripts/` directory contains utilities for processing release data:

- `process_release_csvs.py`: Processes `datasets.csv` and `new_datasets.csv` files from release directories to create dataset and collection references
- `generate_release_jsons.py`: Generates `release.json` files for each release containing version, CDE version, datasets, and collections
- `populate_repositories.py`: Uses the processed references to populate the cloud-datasets and cloud-collections repositories

## Reference Files and Release JSON

### Dataset References

The `references/` directory contains processed data from release CSV files:

- `datasets_references.json`: Complete dataset metadata extracted from all processed releases
- `collections_references.json`: Collection metadata with dataset relationships
- `release_summary.json`: Summary of processed versions and statistics

### Release JSON Files

Each release directory contains a `release.json` file with the following structure:

```json
{
  "release_version": "v1.0.0",
  "cde_version": "v2.1",
  "release_doi": "",
  "datasets": ["dataset-name-1", "dataset-name-2"],
  "collections": ["collection-name-1"],
  "created": "ISO timestamp",
  "metadata": {
    "total_datasets": 5,
    "total_collections": 1,
    "source": "v1.0.0/datasets.csv"
  }
}
```

**Fields:**
- `release_version`: Version tag in format v.major.minor.patch
- `cde_version`: Common Data Elements version used in this release
- `release_doi`: DOI URL for the release (empty if not yet assigned)
- `datasets`: List of dataset names in this release
- `collections`: List of collection names in this release
- `created`: Timestamp when release.json was generated
- `metadata`: Additional metadata including source information

## Processing Release Data

To generate all release files:

```bash
# Process CSV files from release directories
python scripts/process_release_csvs.py

# Generate release.json files for each release
python scripts/generate_release_jsons.py

# Populate repositories with processed references
export GITHUB_TOKEN=your_token
python scripts/populate_repositories.py
```

The processing scripts look for data in `~/Projects/ASAP/asap-crn-cloud-release-resources/releases/`
