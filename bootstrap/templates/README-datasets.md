# ASAP CRN Cloud Datasets

This repository contains the source-of-truth archive of ASAP CRN datasets.

## Structure

- `datasets.json`: JSON index containing all datasets with their DOIs and references
- `datasets/<dataset_name>/`: Individual dataset directories
  - `dataset.json`: Dataset metadata including title, description, creators, DOI, and version
  - version: current version of the dataset
  - 'DOI/' sub directory which contains the DOI files for the most current version of the dataset
    - 'project.json': JSON file capturing Dataset details
    - 'dataset.doi': all versions reference 
    - 'version.doi': current versions reference 
    - '<dataset_name>_README.md'
    - '<dataset_name>_README.pdf'
    - 'deposition.json': JSON file for the Zenodo deposition
  - 'refs/' sub directory which contains reference files for the most current version of the  dataset
  - 'scripts/' sub directory which contains any scripts related to the most current version of the dataset
  - 'archive/' sub directory which contains all files from all  versions of the dataset
    - '<version>' sub directory which contains all files from all  versions of the dataset
      - 'version.doi': current versions reference 
          - '<version>' sub directory which contains all files from all  versions of the dataset
      - 'DOI/' sub directory which contains the DOI files for the most current version of the dataset
        - 'project.json': JSON file capturing Dataset details
        - 'dataset.doi': all versions reference 
        - 'version.doi':  <versions> reference 
        - '<dataset_name>_README.md'
        - '<dataset_name>_README.pdf'
        - 'deposition.json': JSON file for the Zenodo deposition
      - 'refs/' sub directory which contains reference files for the version of the  dataset
      - 'scripts/' sub directory which contains any scripts related to the version of the dataset


## Dataset Metadata Schema
Example
```json

{
  "name": "jakobsson-pmdbs-bulk-rnaseq",
  "title": "team-jakobsson-pmdbs-bulk-rnaseq",
  "description": "pmdbs-bulk-rnaseq dataset from team-jakobsson",
  "version": "v1.0",
  "doi": null,
  "creators": [
    {
      "name": "team-jakobsson",
      "affiliation": "ASAP CRN"
    }
  ],
  "keywords": [
    "pmdbs-bulk-rnaseq",
    "other-pmdbs",
    "jakobsson"
  ],
  "license": "CC-BY-4.0",
  "references": [],
  "collection": "pmdbs-bulk-rnaseq",
  "buckets": {
    "raw": "gs://asap-raw-team-jakobsson-pmdbs-bulk-rnaseq",
    "dev": "gs://asap-dev-team-jakobsson-pmdbs-bulk-rnaseq",
    "uat": "gs://asap-uat-team-jakobsson-pmdbs-bulk-rnaseq",
    "prod": "gs://asap-curated-team-jakobsson-pmdbs-bulk-rnaseq"
  },
  "releases": "v3.0.0": {
      "cde_version": "v3.2",
      "date": null
    },
    "v4.0.0": {
      "cde_version": "v3.3",
      "date": null
    }
}

```

## Management

This repository is automatically managed by the [cloud-orchestration](https://github.com/ASAP-CRN/cloud-orchestration) system. Manual changes should be avoided.

For dataset submissions or updates, please use the orchestration system or contact the ASAP CRN team.