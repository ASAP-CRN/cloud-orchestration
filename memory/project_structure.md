---
name: ASAP Orchestration Project Structure
description: Core modules and repo layout for cloud-orchestration refactor
type: project
---

The `asap_orchestrator` package lives in `src/asap_orchestrator/`. Key modules:

- `dataset.py` — `create_dataset_doi`, `update_dataset_doi`, `publish_dataset_doi`, `update_dataset_version`, `update_datasets_index`
- `release.py` — `ReleaseDefinition` dataclass, `define_release`, `perform_release`
- `collection.py` — `update_collection`, `update_collections_index`
- `zenodo_util.py` — `ZenodoClient` (low-level Zenodo API wrapper)
- `doi.py` — legacy DOI helpers (imports broken: needs `xhtml2pdf`, `docx`, `.util`); not imported by new modules
- `google_spreadsheets.py` — read Google Sheets tabs as DataFrames

Managed repos (local siblings of cloud-orchestration):
- `../cloud-datasets` — per-dataset `dataset.json` + `datasets.json` index
- `../cloud-releases` — per-release `release.json` + `releases.json` index
- `../cloud-collections` — per-collection `collection.json` + `collections.json` index

**Why:** refactor branch adding proper module structure; bootstrap/ contains historical scripts.

**How to apply:** new release scripts should `import asap_orchestrator as ao` and use `define_release` → `perform_release` + `update_collection` + `update_dataset_version` pipeline.
