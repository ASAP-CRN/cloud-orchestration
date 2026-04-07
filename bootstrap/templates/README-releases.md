# ASAP CRN Cloud Releases

This repository contains release information for ASAP CRN datasets and collections.

## Structure
- 'releases.doi': all versions reference 
- `releases.json`: JSON index containing all releases with associated datasets and collections
- `releases/<release_version>/`: Individual release directories
  - version: current version of the dataset
  - `release.json`: Collection metadata including title, description, DOI, version, and list of datasets and collections
  - 'release.doi': current release reference 
  - 'scripts/' sub directory which contains any scripts related to the most current release
  - 'README.pdf'
  - 'README.md'


- Release tags (e.g., `v1.0.0`) correspond to published versions

in the 'releases/' directory, there are subdirectories for each release. Each release has a 'release.json' file that contains the release metadata.

Currently there are 9 releases: v1.0.0, v2.0.0, v2.0.1, v2.0.2, v2.0.3, v3.0.0, v3.0.1, v3.0.2, and v4.0.0





## Release 

The release.json file contains the following information:

```json
{
  "version": "1.0.0",
  "release_date": "2024-01-15T10:00:00Z",
  "datasets": [
    {
      "name": "dataset_name",
      "doi": "10.5281/zenodo.1234567",
      "version": "1.0.0"
    }
  ],

    "new_datasets": [
    {
      "name": "dataset_name",
      "doi": "10.5281/zenodo.1234567",
      "version": "1.0.0"
    }
  ],
  "collections": [
    {
      "name": "collection_name",
      "doi": "10.5281/zenodo.7654321",
      "version": "1.0.0"
    }
  ],
  "description": "Release notes and changes"
}
```


## Release Process

Releases are created through the [cloud-orchestration](https://github.com/ASAP-CRN/cloud-orchestration) system:

1. Datasets and collections are prepared and assigned DOIs
2. A release is created with a version tag
3. All associated repositories are updated
4. Zenodo records are published

## Management

This repository is automatically managed by the cloud-orchestration system. Manual changes should be avoided.