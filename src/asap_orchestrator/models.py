"""Pydantic models for ASAP CRN cloud artifact JSON schemas.

These models define and validate the on-disk JSON artifacts managed by the
orchestrator: dataset.json (Dataset), and in future passes collection.json and
release.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Creator(BaseModel):
    """A Zenodo-compatible creator entry."""

    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None


class DatasetBuckets(BaseModel):
    """GCS bucket URIs for each deployment environment."""

    raw: str
    dev: str
    uat: str
    prod: str


class ReleaseRecord(BaseModel):
    """Per-release snapshot stored under ``dataset.json["releases"]``."""

    cde_version: Optional[str] = None
    dataset_version: Optional[str] = None


class VersionRecord(BaseModel):
    """Per-version record stored under ``dataset.json["all_versions"]``."""

    doi: str = ""
    releases: dict[str, Any] = Field(default_factory=dict)


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
    doi: Optional[str] = None
    creators: list[Creator] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    license: str = "CC-BY-4.0"
    references: list[str] = Field(default_factory=list)
    collection: Optional[str] = None
    buckets: DatasetBuckets
    cde_version: Optional[str] = None
    releases: dict[str, ReleaseRecord] = Field(default_factory=dict)
    all_versions: dict[str, VersionRecord] = Field(default_factory=dict)

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
        (Path(ds_path) / "dataset.json").write_text(json.dumps(data, indent=2))

    # ── Manifest helpers ───────────────────────────────────────────────────────

    def to_release_entry(self) -> dict:
        """Return ``{"name", "doi", "version"}`` for release/collection manifests."""
        return {"name": self.name, "doi": self.doi, "version": self.version}


# Backward-compatible alias — existing callers of DatasetDefinition continue to work.
DatasetDefinition = Dataset
