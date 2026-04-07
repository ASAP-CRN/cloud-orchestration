# ASAP CRN Cloud Collections

This repository contains curated collections of ASAP CRN datasets.

## Structure

- `collections.json`: JSON index containing all collections with their DOIs and references
- `collections/<collection_name>/`: Individual collection directories
  - version: current version of the dataset
  - `collection.json`: Collection metadata including title, description, DOI, version, and list of datasets
  - 'collection.doi': all versions reference 
  - 'collection_version.doi': current versions reference 
  - '<collection_name>_README.md' (optional)
  - '<collection_name>_README.pdf'
  - 'scripts/' sub directory which contains any scripts related to the most current version of the collection
  - 'archive/' sub directory which contains all files from all      - 'version.doi': current versions reference 
  - 'README.pdf' most current collection README
  - 'README.md' most current collection README
 versions of the collection
    - '<version>' sub directory which contains all files from all  versions of the collection
      - 'collection_version.doi': current versions reference 
      - `collection.json`: Collection metadata including title, description, DOI, version, and list of datasets
      -  'README.pdf' version collection README
      - 'README.md' version collection README

## Collection Metadata Schema

```json
{
 {
  "name": "pmdbs-bulk-rnaseq",
  "title": "PMDBS bulkRNAseq",
  "types": [
    "pmdbs-bulk-rnaseq"
  ],
  "versions": {
    "v1.0.0" : {
      "doi": null,
      "datasets": [
        "hardy-pmdbs-bulk-rnaseq",
        "lee-pmdbs-bulk-rnaseq-mfg",
        "wood-pmdbs-bulk-rnaseq",
        "cohort-pmdbs-bulk-rnaseq"
      ],
      "teams": [
        "cohort",
        "hardy",
        "jakobsson",
        "lee",
        "wood"
      ],
      "release": {
        "version": "v1.0.0",
        "cde_version" : "v3.0",
        "date": null
      },
    },
    "v1.1.0" : {
      "doi": null,
      "datasets": [
        "hardy-pmdbs-bulk-rnaseq",
        "lee-pmdbs-bulk-rnaseq-mfg",
        "wood-pmdbs-bulk-rnaseq",
        "cohort-pmdbs-bulk-rnaseq",
      ],
      "teams": [
        "cohort",
        "hardy",
        "jakobsson",
        "lee",
        "wood"
      ],
      "release": {
        "version": "v1.1.0",
        "cde_version" : "v3.2",
        "date": null
      }
    },
    "v1.2.0" : {
      "doi": null,
      "datasets": [
        "hardy-pmdbs-bulk-rnaseq",
        "lee-pmdbs-bulk-rnaseq-mfg",
        "wood-pmdbs-bulk-rnaseq",
        "cohort-pmdbs-bulk-rnaseq",
        "jakobsson-pmdbs-bulk-rnaseq"
      ],
      "teams": [
        "cohort",
        "hardy",
        "jakobsson",
        "lee",
        "wood"
      ],
      "release": {
        "version": "v1.2.0",
        "cde_version" : "v3.3",
        "date": null
      }
    }
  }
}
```

## Management

This repository is automatically managed by the [cloud-orchestration](https://github.com/ASAP-CRN/cloud-orchestration) system. Manual changes should be avoided.

Collections are curated sets of related datasets that are published together. For collection submissions or updates, please use the orchestration system or contact the ASAP CRN team.