"""ASAP CRN Cloud Orchestration Package.

Usage::

    import asap_orchestrator as ao

    # ── Dataset acceptance (WIP, v0.1) ──────────────────────────────────────
    ds_def = ao.define_dataset(
        name="teamX-pmdbs-sn-rnaseq",
        collection="pmdbs-sc-rnaseq",
        cde_version="v3.3",
    )
    ds_path = ao.create_dataset_stub(ds_def, datasets_repo_path="/path/to/cloud-datasets")

    # Ingest DOI reference document and create draft Zenodo DOI
    ao.setup_DOI_info(ds_path, ref_doc, publication_date="2026-04-23")
    zenodo = ao.setup_zenodo()
    ao.create_dataset_doi(ds_path, zenodo, version="v0.1")

    # ── Release definition ───────────────────────────────────────────────────
    new_datasets = [
        ao.define_dataset(
            name="teamX-pmdbs-sn-rnaseq",
            collection="pmdbs-sc-rnaseq",
            version="v1.0",
            doi="10.5281/zenodo.XXXXXXXX",
            cde_version="v3.3",
        ),
    ]

    all_dataset_entries = [
        ao.read_dataset_entry("/path/to/cloud-datasets/previously-released-dataset"),
    ] + [ds.to_release_entry() for ds in new_datasets]

    release_def = ao.define_release(
        release_version="v4.1.0",
        release_type="Minor",
        cde_version="v3.3",
        datasets=all_dataset_entries,
        new_datasets=[ds.to_release_entry() for ds in new_datasets],
        collections=[{"name": "pmdbs-sc-rnaseq", "doi": "10.5281/zenodo.YYYYYYYY", "version": "v3.2.0"}],
    )

    # ── Collection definition ────────────────────────────────────────────────
    col_def = ao.define_collection(
        collection_name="pmdbs-sc-rnaseq",
        new_version="v3.2.0",
        new_datasets=["teamX-pmdbs-sn-rnaseq"],
        release_def=release_def,
    )

    # ── Perform release and collection updates ───────────────────────────────
    ao.perform_release(release_def, releases_repo_path="/path/to/cloud-releases")
    ao.update_collection(col_def, collections_repo_path="/path/to/cloud-collections")
    ao.update_datasets_index("/path/to/cloud-datasets")
"""

__version__ = "0.1.0"

from .dataset import (
    DatasetDefinition,
    define_dataset,
    create_dataset_stub,
    read_dataset_entry,
    create_dataset_doi,
    update_dataset_doi,
    publish_dataset_doi,
    update_dataset_version,
    update_datasets_index,
)
from .release import (
    ReleaseDefinition,
    define_release,
    perform_release,
)
from .collection import (
    CollectionDefinition,
    define_collection,
    update_collection,
    update_collections_index,
)

from .doi import (
    ingest_DOI_doc,
    setup_DOI_info,
    setup_zenodo,
    create_draft_metadata,
    get_doi_from_dataset,
    bump_doi_version,
    replace_anchor_file_in_doi,
    add_anchor_file_to_doi,
    finalize_DOI,
    archive_deposition_local,
)

from .util import *

__all__ = [
    # dataset
    "DatasetDefinition",
    "define_dataset",
    "create_dataset_stub",
    "read_dataset_entry",
    "create_dataset_doi",
    "update_dataset_doi",
    "publish_dataset_doi",
    "update_dataset_version",
    "update_datasets_index",
    # release
    "ReleaseDefinition",
    "define_release",
    "perform_release",
    # collection
    "CollectionDefinition",
    "define_collection",
    "update_collection",
    "update_collections_index",
    # doi
    "ingest_DOI_doc",
    "setup_DOI_info",
    "setup_zenodo",
    "create_draft_metadata",
    "get_doi_from_dataset",
    "bump_doi_version",
    "replace_anchor_file_in_doi",
    "add_anchor_file_to_doi",
    "finalize_DOI",
    "archive_deposition_local",
    # util
    "get_dataset_version",
    "get_release_version",
    "get_cde_version",
    "write_version",
    "archive_CDE",
]
