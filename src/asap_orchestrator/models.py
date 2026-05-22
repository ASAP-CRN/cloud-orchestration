"""Pydantic models for ASAP CRN cloud artifact JSON schemas.

These models define and validate the on-disk JSON artifacts managed by the
orchestrator: dataset.json (Dataset), release.json (ReleaseDefinition), and
collection.json (Collection / CollectionDefinition).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

ReleaseType = Literal["Urgent", "Minor", "Major"]


class Creator(BaseModel):
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
            if v_parts[0] != PARTS1 or v_parts[1] != "cohort" or v_parts[2] != PARTS3:
                raise ValueError("Invalid bucket URI")
            
        return v


class ReleaseRecord(BaseModel):
    """Per-release snapshot stored under ``dataset.json["releases"]``."""

    cde_version: Optional[str] = None
    dataset_version: Optional[str] = None


# class VersionRecord(BaseModel):
#     """Per-version record stored under ``dataset.json["all_versions"]``."""

#     doi: str = ""
#     releases: dict[str, Any] = Field(default_factory=dict)


class Dataset(BaseModel):
    """Schema and I/O model for ``dataset.json`` artifacts.

    Field order matches the canonical on-disk key order so that
    :meth:`save` produces minimal diffs against existing files.

    Attributes:
        name: Dataset slug following ``<team>-<tissue>-<modality>`` convention.
        title: Human-readable title.
        description: Short description for Zenodo metadata.
        version: Dataset version string, e.g. ``"v1.0"``.
        doi: Zenodo concept DOI (all-versions).  ``None`` until assigned.
        creators: Zenodo creator list.
        keywords: Discovery keywords.
        license: SPDX license identifier.
        references: Zenodo reference strings.
        collection: Collection slug this dataset belongs to, or ``None``.
        buckets: GCS bucket URIs per environment.
        cde_version: CDE schema version applied to this dataset.
        releases: Map of release version → release snapshot.
        all_versions: Map of dataset version → version DOI and release map.
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    title: str = ""
    description: str = ""
    version: str = "v0.1"
    dataset_title:  str = ""
    doi: Optional[str] = None
    creators: list[Creator] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    license: str = "CC-BY-4.0"
    references: list[str] = Field(default_factory=list)
    collection: Optional[str] = None
    buckets: DatasetBuckets
    cde_version: Optional[str] = None
    releases: dict[str, ReleaseRecord] = Field(default_factory=dict)
    all_versions: list[str] = Field(default_factory=list)
    all_releases: list[str] = Field(default_factory=list)

    @field_validator("doi", "cde_version", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v

    @field_validator("version", mode="before")
    @classmethod
    def _ensure_v_prefix(cls, v: object) -> object:
        if isinstance(v, str) and v and not v.startswith("v"):
            return f"v{v}"
        return v

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

    def save(self, ds_path: Path | str) -> None:
        """Write this dataset to ``dataset.json`` inside *ds_path*.

        Fields are serialized in model-definition order with 2-space indentation.
        ``all_versions`` is omitted from the output when empty to avoid noisy
        diffs on files that predate the field.

        Args:
            ds_path: Dataset directory to write into (must already exist).
        """
        data = self.model_dump()
        if not data.get("all_versions"):
            del data["all_versions"]
        (Path(ds_path) / "dataset.json").write_text(json.dumps(data, indent=4))

    # ── Manifest helpers ───────────────────────────────────────────────────────

    def to_release_entry(self) -> dict:
        """Return ``{"name", "doi", "version"}`` for release/collection manifests."""
        return {"name": self.name, "doi": self.doi, "version": self.version}


# Backward-compatible alias — existing callers of DatasetDefinition continue to work.
DatasetDefinition = Dataset


# ── Release models ─────────────────────────────────────────────────────────────

class DatasetEntry(BaseModel):
    """A ``{"name", "doi", "version"}`` reference used in release/collection manifests."""

    name: str
    doi: Optional[str] = None
    version: str = ""

    @field_validator("doi", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v


class CollectionEntry(BaseModel):
    """A ``{"name", "doi", "version"}`` collection reference in release manifests."""

    name: str
    doi: Optional[str] = None
    version: str = ""

    @field_validator("doi", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v


class ReleaseMetadata(BaseModel):
    """Metadata block embedded in ``release.json``."""

    total_datasets: int = 0
    total_collections: int = 0
    source: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ReleaseDefinition(BaseModel):
    """Schema and I/O model for ``release.json`` artifacts.

    Attributes:
        release_version: Release version string, e.g. ``"v4.1.0"``.
        release_type: One of ``"Urgent"``, ``"Minor"``, or ``"Major"``.  ``None``
            when loading legacy files that predate this field.
        cde_version: CDE schema version applied across all datasets.
        datasets: All datasets included in the release.
        new_datasets: Subset of *datasets* that are new or updated.
        collections: All collections included in the release.
        release_doi: Zenodo concept DOI for the release record.
        created: ISO timestamp when the release was created.
        metadata: Summary counters and optional source annotation.
    """

    model_config = ConfigDict(extra="ignore")

    release_version: str
    release_type: Optional[ReleaseType] = None
    cde_version: str
    datasets: list[DatasetEntry] = Field(default_factory=list)
    new_datasets: list[DatasetEntry] = Field(default_factory=list)
    collections: list[CollectionEntry] = Field(default_factory=list)
    release_doi: Optional[str] = None
    created: Optional[str] = None
    metadata: ReleaseMetadata = Field(default_factory=ReleaseMetadata)

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
        (Path(release_path) / "release.json").write_text(
            json.dumps(self.model_dump(), indent=2)
        )


# ── Collection models ──────────────────────────────────────────────────────────

class CollectionReleaseRef(BaseModel):
    """Release reference embedded in a :class:`CollectionVersion`."""

    version: str = ""
    cde_version: str = ""
    date: Optional[str] = None


class CollectionVersion(BaseModel):
    """A single version entry within ``collection.json["versions"]``."""

    version: str
    date: Optional[str] = None
    doi: Optional[str] = None
    datasets: list[str] = Field(default_factory=list)
    teams: list[str] = Field(default_factory=list)
    types: list[str] = Field(default_factory=list)
    release: CollectionReleaseRef = Field(default_factory=CollectionReleaseRef)

    @field_validator("doi", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v


class Collection(BaseModel):
    """Schema and I/O model for ``collection.json`` artifacts.

    Attributes:
        name: Collection slug, e.g. ``"pmdbs-sc-rnaseq"``.
        title: Human-readable title.
        collection_doi: Zenodo concept DOI for the collection.
        types: Collection type tags.
        versions: Map of version string → version snapshot.
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    title: str = ""
    collection_doi: Optional[str] = None
    types: list[str] = Field(default_factory=list)
    versions: dict[str, CollectionVersion] = Field(default_factory=dict)

    @field_validator("collection_doi", mode="before")
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
        (Path(collection_path) / "collection.json").write_text(
            json.dumps(self.model_dump(), indent=2)
        )


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
    new_version: str
    new_datasets: list[str] = Field(default_factory=list)
    release_version: str = ""
    cde_version: str = ""
    version_doi: str = ""
