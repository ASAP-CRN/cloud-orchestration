"""Pydantic models for ASAP CRN cloud artifact JSON schemas.

These models define and validate the on-disk JSON artifacts managed by the
orchestrator: dataset.json (Dataset), release.json (ReleaseDefinition), and
collection.json (Collection / CollectionDefinition).

Schemas follow the canonical formats in ``cloud-fixup/ground_truth``.  Field
order matches the on-disk key order so that ``save`` round-trips those files.

Every ASAP version identifier (dataset, collection, release, CDE) is stored
with a leading ``v``; see :data:`VStr`.  Third-party tool versions inside
:class:`Curation` (e.g. ``preprocess_cellranger``) are stored as-is.

This module is kept identical in ``cloud-orchestration/src/asap_orchestrator/``
and ``cloud-fixup/scripts/``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal, Optional

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
    model_serializer,
)

ReleaseType = Literal["Urgent", "Minor", "Major"]


def ensure_v_prefix(v: object) -> object:
    if isinstance(v, str) and v and not v.startswith("v"):
        return f"v{v}"
    return v


VStr = Annotated[str, BeforeValidator(ensure_v_prefix)]
"""An ASAP version string, normalized to a leading ``v`` (``"5.1.0"`` → ``"v5.1.0"``)."""


def _write_json(path: Path, data: dict) -> None:
    """Write *data* in the ground-truth format: 4-space indent, no trailing newline."""
    path.write_text(json.dumps(data, indent=4))


class _DropUnset(BaseModel):
    """Base for records whose keys vary per file: only serialize fields that were set.

    Distinguishes an absent key from an explicit ``null`` (e.g. ``orcid``).
    """

    @model_serializer(mode="wrap")
    def _drop_unset(self, handler):
        data = handler(self)
        return {k: v for k, v in data.items() if k in self.model_fields_set}


class GcpUri(BaseModel):
    """``curation[...]["gcp_uri"]`` bucket paths."""

    collection_bucket: str
    dataset_bucket: str


class Curation(_DropUnset):
    """A curation record: workflow provenance for one dataset in one collection version.

    Used in ``dataset.json["curation"][release_version]`` and
    ``collection.json["curation"][dataset_name]``.  Which fields are present
    depends on the workflow (sc-rnaseq, bulk-rnaseq, spatial, ...); an empty
    record (``{}``) is valid.
    """

    workflow: Optional[str] = None
    collection_version: Optional[VStr] = None
    workflow_version: Optional[str] = None
    workflow_url: Optional[str] = None
    upstream: Optional[str] = None
    downstream: Optional[str] = None
    qc: Optional[str] = None
    preprocess_cellranger: Optional[str] = None
    preprocess_counts_to_adata: Optional[str] = None
    preprocess_cellbender: Optional[str] = None
    cohort_analysis: Optional[str] = None
    spaceranger: Optional[str] = None
    counts_adata: Optional[str] = None
    fastq_dcc: Optional[str] = None
    dcc_rds: Optional[str] = None
    collection_version_doi: Optional[str] = None
    gcp_uri: Optional[GcpUri] = None


class Creator(_DropUnset):
    """A Zenodo-compatible creator entry."""

    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None



PARTS1 = "gs://asap"
PARTS2 = ["raw", "dev", "uat", "curated"]
PARTS3 = "team"

class DatasetBuckets(BaseModel):
    """GCS bucket URIs for each deployment environment."""

    raw: str
    dev: str
    uat: str
    prod: str
    # add checking to make sure that the buckets are valid

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("raw", "dev", "uat", "prod")
    def check_bucket(cls, v):
        if not v.startswith("gs://"):
            raise ValueError("Bucket URIs must start with gs://")

        v_parts = v.split("-")
        # check parts 1, 2, 3

        if "cohort" not in v:
            if v_parts[0] != PARTS1 or v_parts[1] not in PARTS2 or v_parts[2] != PARTS3:
                raise ValueError("Invalid bucket URI")
        else:
            if v_parts[0] != PARTS1 or v_parts[1] not in PARTS2 or v_parts[2] != "cohort":
                raise ValueError("Invalid bucket URI")

        return v


class Dataset(BaseModel):
    """Schema and I/O model for ``dataset.json`` artifacts.

    Field order matches the canonical on-disk key order so that
    :meth:`save` produces minimal diffs against existing files.

    Attributes:
        name: Dataset slug following ``<team>-<tissue>-<modality>`` convention.
        title: Human-readable title.
        description: Short description for Zenodo metadata.
        doi: Zenodo concept DOI (all-versions).  ``None`` until assigned.
        creators: Zenodo creator list.  ``None`` (omitted on save) when absent.
        keywords: Discovery keywords.
        license: SPDX license identifier.
        collection: Collection slug this dataset belongs to, or ``None``.
        buckets: GCS bucket URIs per environment.
        dataset_title: Display title.
        short_description: Display description.  ``None`` (omitted on save) when absent.
        version: Dataset version string, e.g. ``"v1.0"``.
        curation: Map of release version → curation record (may be empty).
        all_versions: Every dataset version released so far.
        releases: Map of release version → dataset version in that release.
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    title: str = ""
    description: str = ""
    doi: Optional[str] = None
    creators: Optional[list[Creator]] = None
    keywords: list[str] = Field(default_factory=list)
    license: str = "CC-BY-4.0"
    collection: Optional[str] = None
    buckets: DatasetBuckets
    dataset_title: str = ""
    short_description: Optional[str] = None
    version: VStr = "v0.1"
    curation: dict[VStr, Curation] = Field(default_factory=dict)
    all_versions: list[VStr] = Field(default_factory=list)
    releases: dict[VStr, VStr] = Field(default_factory=dict)

    @field_validator("doi", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v

    # ── I/O ────────────────────────────────────────────────────────────────────

    @classmethod
    def load(cls, ds_path: Path | str) -> "Dataset":
        """Read and validate ``dataset.json`` from *ds_path*.

        Args:
            ds_path: Dataset directory containing ``dataset.json``.

        Raises:
            FileNotFoundError: When ``dataset.json`` is absent.
            pydantic.ValidationError: When the JSON does not conform to this schema.
        """
        p = Path(ds_path) / "dataset.json"
        if not p.exists():
            raise FileNotFoundError(f"dataset.json not found: {p}")
        return cls.model_validate_json(p.read_text())

    def to_dict(self) -> dict:
        """Return the on-disk ``dataset.json`` dict.

        ``creators`` and ``short_description`` are omitted when ``None`` so
        files that lack them round-trip unchanged.
        """
        data = self.model_dump()
        for key in ("creators", "short_description"):
            if data[key] is None:
                del data[key]
        return data

    def save(self, ds_path: Path | str) -> None:
        """Write this dataset to ``dataset.json`` inside *ds_path*.

        Args:
            ds_path: Dataset directory to write into (must already exist).
        """
        _write_json(Path(ds_path) / "dataset.json", self.to_dict())

    # ── Manifest helpers ───────────────────────────────────────────────────────

    def to_release_entry(self) -> dict:
        """Return ``{"dataset_version", "doi"}`` for ``release.json["datasets"][name]``."""
        return DatasetEntry(dataset_version=self.version, doi=self.doi).model_dump()


# Backward-compatible alias — existing callers of DatasetDefinition continue to work.
DatasetDefinition = Dataset


# ── Release models ─────────────────────────────────────────────────────────────

class DatasetEntry(BaseModel):
    """Value of ``release.json["datasets"][dataset_name]``."""

    dataset_version: VStr
    doi: Optional[str] = None

    @field_validator("doi", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v


class CollectionEntry(BaseModel):
    """Value of ``release.json["collections"][collection_name]``."""

    doi: Optional[str] = None
    version: VStr

    @field_validator("doi", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v


class ReleaseDefinition(BaseModel):
    """Schema and I/O model for ``release.json`` artifacts.

    Attributes:
        release_version: Release version string, e.g. ``"v4.1.0"``.
        cde_version: CDE schema version applied across all datasets.
        release_doi: Zenodo concept DOI for the release record.
        datasets: Map of dataset name → version/DOI for every dataset in the release.
        new_datasets: Names of datasets that are new or updated in this release.
        collections: Map of collection name → DOI/version for every collection.
        created: ISO timestamp when the release was created.
        datasets_names: Names of all datasets in the release.
        collection_names: Names of all collections in the release.
    """

    model_config = ConfigDict(extra="ignore")

    release_version: VStr
    cde_version: VStr
    release_doi: Optional[str] = None
    datasets: dict[str, DatasetEntry] = Field(default_factory=dict)
    new_datasets: list[str] = Field(default_factory=list)
    collections: dict[str, CollectionEntry] = Field(default_factory=dict)
    created: Optional[str] = None
    datasets_names: list[str] = Field(default_factory=list)
    collection_names: list[str] = Field(default_factory=list)

    @field_validator("release_doi", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v

    @classmethod
    def load(cls, release_path: Path | str) -> "ReleaseDefinition":
        """Read and validate ``release.json`` from *release_path*.

        Args:
            release_path: Release directory containing ``release.json``.

        Raises:
            FileNotFoundError: When ``release.json`` is absent.
            pydantic.ValidationError: When the JSON does not conform to this schema.
        """
        p = Path(release_path) / "release.json"
        if not p.exists():
            raise FileNotFoundError(f"release.json not found: {p}")
        return cls.model_validate_json(p.read_text())

    def save(self, release_path: Path | str) -> None:
        """Write this release to ``release.json`` inside *release_path*.

        Args:
            release_path: Release directory to write into (must already exist).
        """
        _write_json(Path(release_path) / "release.json", self.model_dump())


# ── Collection models ──────────────────────────────────────────────────────────

class CollectionReleaseRef(BaseModel):
    """Release reference embedded in a collection or :class:`CollectionVersion`."""

    version: VStr = ""
    cde_version: VStr = ""
    date: Optional[str] = None


class CollectionVersion(BaseModel):
    """A single version entry within ``collection.json["versions"]``."""

    date: Optional[str] = None
    doi: Optional[str] = None
    datasets: list[str] = Field(default_factory=list)
    release: CollectionReleaseRef = Field(default_factory=CollectionReleaseRef)

    @field_validator("doi", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v


class Collection(BaseModel):
    """Schema and I/O model for ``collection.json`` artifacts.

    The top-level ``date`` / ``doi`` / ``datasets`` / ``teams`` / ``release`` /
    ``version`` describe the current version; ``versions`` holds every version.

    Attributes:
        name: Collection slug, e.g. ``"pmdbs-sc-rnaseq"``.
        title: Human-readable title.
        collection_doi: Zenodo concept DOI for the collection.
        types: Collection type tags.
        date: Release date of the current version.
        doi: Zenodo DOI of the current version.
        datasets: Dataset names in the current version.
        teams: Contributing team names in the current version.
        release: Release that published the current version.
        version: Current collection version, e.g. ``"v3.1.2"``.
        versions: Map of version string → version snapshot.
        curation: Map of dataset name → curation record.
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    title: str = ""
    collection_doi: Optional[str] = None
    types: list[str] = Field(default_factory=list)
    date: Optional[str] = None
    doi: Optional[str] = None
    datasets: list[str] = Field(default_factory=list)
    teams: list[str] = Field(default_factory=list)
    release: CollectionReleaseRef = Field(default_factory=CollectionReleaseRef)
    version: VStr = ""
    versions: dict[VStr, CollectionVersion] = Field(default_factory=dict)
    curation: dict[str, Curation] = Field(default_factory=dict)

    @field_validator("collection_doi", "doi", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v

    @classmethod
    def load(cls, collection_path: Path | str) -> "Collection":
        """Read and validate ``collection.json`` from *collection_path*.

        Returns an empty :class:`Collection` when ``collection.json`` is absent.

        Args:
            collection_path: Collection directory containing ``collection.json``.
        """
        p = Path(collection_path) / "collection.json"
        if not p.exists():
            return cls(name=Path(collection_path).name)
        return cls.model_validate_json(p.read_text())

    def save(self, collection_path: Path | str) -> None:
        """Write this collection to ``collection.json`` inside *collection_path*.

        Args:
            collection_path: Collection directory to write into.
        """
        _write_json(Path(collection_path) / "collection.json", self.model_dump())


class CollectionDefinition(BaseModel):
    """Describes a pending collection version update.

    Produced by :func:`~asap_orchestrator.collection.define_collection` and
    consumed by :func:`~asap_orchestrator.collection.update_collection`.

    Attributes:
        collection_name: Name of the collection, e.g. ``"pmdbs-sc-rnaseq"``.
        new_version: New collection version string, e.g. ``"v3.2.0"``.
        new_datasets: Dataset names that are new or updated in this version.
        release_version: Release version this collection update belongs to.
        cde_version: CDE schema version applied across datasets in this version.
        version_doi: Zenodo DOI for this specific collection version.
    """

    collection_name: str
    new_version: VStr
    new_datasets: list[str] = Field(default_factory=list)
    release_version: VStr = ""
    cde_version: VStr = ""
    version_doi: str = ""
