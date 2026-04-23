"""ASAP CRN Cloud Orchestration Package.

Usage::

    import asap_orchestrator as ao

    # Define a release
    release_def = ao.define_release(
        release_version="v4.1.0",
        release_type="Minor",
        cde_version="v3.3",
        datasets=[{"name": "...", "doi": "...", "version": "v1.0"}],
        new_datasets=[],
        collections=[{"name": "pmdbs-sc-rnaseq", "doi": "...", "version": "v3.2.0"}],
    )

    # Write release artifacts
    ao.perform_release(release_def, releases_repo_path="/path/to/cloud-releases")

    # Update a collection
    ao.update_collection(
        collection_name="pmdbs-sc-rnaseq",
        new_version="v3.2.0",
        new_datasets=["new-team-pmdbs-sn-rnaseq"],
        release_def=release_def,
        collections_repo_path="/path/to/cloud-collections",
    )
"""

__version__ = "0.1.0"

from .dataset import (
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
    "archive_CDE"
]
