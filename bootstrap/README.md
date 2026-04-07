# cloud-orchestration
functions and resources for bootstrapping the public facing repos from existing archives (metadata/release resources)

## repos
- [ASAP-CRN/cloud-datasets](https://github.com/ASAP-CRN/cloud-datasets)
- [ASAP-CRN/cloud-collections](https://github.com/ASAP-CRN/cloud-collections)
- [ASAP-CRN/cloud-releases](https://github.com/ASAP-CRN/cloud-releases)
- [ASAP-CRN/cloud-cde](https://github.com/ASAP-CRN/cloud-cde)


## bootstrapping

The `bootstrap/templates/` directory contains README templates for each repository type:

- `README-datasets.md`: Template for cloud-datasets repository
- `README-collections.md`: Template for cloud-collections repository  
- `README-releases.md`: Template for cloud-releases repository
- `README-cde.md`: Template for cloud-cde repository

Use these templates to initialize the README files in each managed repository.

## Scripts

The `bootstrap/scripts/` directory contains utilities for processing release data:

- `process_release_csvs.py`: Processes `datasets.csv` and `new_datasets.csv` files from release directories to create dataset and collection references
- `generate_release_jsons.py`: Generates `release.json` files for each release containing version, CDE version, datasets, and collections
- `populate_repositories.py`: Uses the processed references to populate the cloud-datasets and cloud-collections repositories via the GitHub API (requires `GITHUB_TOKEN`)
- `populate_local_repositories.py`: Writes dataset/collection JSON files and stub directory structures directly to local repo checkouts — no GitHub API calls required; also syncs source files from `asap-crn-cloud-dataset-metadata`
- `setup_cloud_releases.py`: Populates the cloud-releases repository by copying release resources and templates for each release version

## Reference Files and Release JSON

### Dataset References

The `bootstrap/references/` directory contains processed data from release CSV files:

- `datasets_references.json`: Complete dataset metadata extracted from all processed releases
- `collections_references.json`: Collection metadata with dataset relationships
- `releases_references.json`: Release-level metadata index across all processed versions
- `release_summary.json`: Summary of processed versions and statistics
- `VWB/generic_contents.py`: Helper for generating generic repository contents

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

# Populate local repo checkouts directly (no GitHub token required)
python scripts/populate_local_repositories.py

# OR populate via GitHub API
export GITHUB_TOKEN=your_token
python scripts/populate_repositories.py

# Populate the cloud-releases repository
python scripts/setup_cloud_releases.py
```

The processing scripts look for data in `~/Projects/ASAP/asap-crn-cloud-release-resources/releases/`
