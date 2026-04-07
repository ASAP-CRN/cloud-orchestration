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
  - `dataset.json`: Dataset metadata including DOI
  - Dataset files

### cloud-collections  
- **collections.json**: Index of all collections with DOIs and references
- **collections/{name}/**: Individual collection directories containing:
  - `collection.json`: Collection metadata including DOI and dataset references

### cloud-releases
- **releases.json**: Index of all releases with associated datasets and collections
- Release tags correspond to published versions

### cloud-cde
- **cde.json**: Index of Common Data Elements
- CDE definitions and metadata
