"""Sync DOIs from asap-crn-cloud-release-resources into cloud-releases release.json files."""

import json
import re
from pathlib import Path
from typing import Optional


RESOURCES_BASE = Path(__file__).parents[3] / "asap-crn-cloud-release-resources" / "releases"
RELEASES_BASE = Path(__file__).parents[3] / "cloud-releases" / "releases"

_ZENODO_DOI_RE = re.compile(r'10\.\d{4,}/zenodo\.(\d+)')


def extract_release_doi_from_pdf(pdf_path: Path) -> Optional[str]:
    """Extract the version-specific release DOI from a README PDF.

    Handles several PDF formats across release history:
    - "ASAP CRN Release DOI: 10.5281/..." and/or "Major Release DOI: 10.5281/..."
      → when both present, picks the highest zenodo record ID (version-specific)
    - Standalone "DOI: 10.5281/..." line
    - Inline "currently release X.Y.Z, 10.5281/..." or DOI on the following line
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required: pip install pdfplumber")

    with pdfplumber.open(pdf_path) as pdf:
        text = "".join(p.extract_text() or "" for p in pdf.pages[:2])

    lines = text.splitlines()
    release_doi_candidates: list[tuple[int, str]] = []
    standalone_doi: Optional[str] = None
    inline_doi: Optional[str] = None
    prev_line = ""

    for line in lines:
        lower = line.lower()
        if "release doi" in lower:
            for m in _ZENODO_DOI_RE.finditer(line):
                release_doi_candidates.append((int(m.group(1)), m.group(0)))
        elif line.strip().startswith("DOI:") and standalone_doi is None:
            m = _ZENODO_DOI_RE.search(line)
            if m:
                standalone_doi = m.group(0)
        else:
            # DOI may be on its own line immediately after "currently release ..."
            if "currently release" in prev_line.lower() and inline_doi is None:
                m = _ZENODO_DOI_RE.match(line.strip())
                if m:
                    inline_doi = m.group(0)
            if "currently release" in lower and inline_doi is None:
                m = _ZENODO_DOI_RE.search(line)
                if m:
                    inline_doi = m.group(0)
        prev_line = line

    if release_doi_candidates:
        return max(release_doi_candidates)[1]
    if standalone_doi:
        return standalone_doi
    return inline_doi


def find_release_pdf(version: str) -> Optional[Path]:
    """Return the README PDF for a release version, or None."""
    version_dir = RELEASES_BASE / version
    matches = sorted(version_dir.glob("*README*.pdf")) + sorted(version_dir.glob("*readme*.pdf"))
    return matches[0] if matches else None


def _read_doi_file(path: Path) -> Optional[str]:
    """Read and return a DOI string from a file, or None if missing."""
    if path.exists():
        return path.read_text().strip()
    return None


def _get_dataset_doi(version: str, dataset_name: str) -> Optional[str]:
    doi_path = RESOURCES_BASE / version / "datasets" / dataset_name / "DOI" / "dataset.doi"
    return _read_doi_file(doi_path)


def _get_collection_doi(version: str, collection_name: str) -> Optional[str]:
    doi_dir = RESOURCES_BASE / version / "collections" / collection_name / "DOI"
    # Prefer collection.doi, fall back to dataset.doi
    doi = _read_doi_file(doi_dir / "collection.doi")
    if doi is None:
        doi = _read_doi_file(doi_dir / "dataset.doi")
    return doi


def _inject_dois(entries: list[dict], lookup_fn) -> tuple[list[dict], int]:
    """Return a new list with doi fields filled in and count of updates made."""
    updated = 0
    result = []
    for entry in entries:
        entry = dict(entry)
        doi = lookup_fn(entry["name"])
        if doi and entry.get("doi") != doi:
            entry["doi"] = doi
            updated += 1
        result.append(entry)
    return result, updated


def sync_release_doi(version: str, dry_run: bool = False) -> dict:
    """Sync only the top-level release_doi field from the README PDF."""
    release_path = RELEASES_BASE / version / "release.json"
    if not release_path.exists():
        return {"version": version, "error": f"release.json not found at {release_path}"}

    pdf = find_release_pdf(version)
    if pdf is None:
        return {"version": version, "release_doi": None, "error": "no README PDF found"}

    doi = extract_release_doi_from_pdf(pdf)
    if doi is None:
        return {"version": version, "release_doi": None, "error": f"could not extract DOI from {pdf.name}"}

    data = json.loads(release_path.read_text())
    changed = data.get("release_doi") != doi
    summary = {"version": version, "release_doi": doi, "changed": changed, "pdf": pdf.name}

    if not dry_run and changed:
        data["release_doi"] = doi
        release_path.write_text(json.dumps(data, indent=2) + "\n")

    return summary


def sync_release(version: str, dry_run: bool = False) -> dict:
    """Sync DOIs for a single release version. Returns a summary dict."""
    release_path = RELEASES_BASE / version / "release.json"
    if not release_path.exists():
        return {"version": version, "error": f"release.json not found at {release_path}"}

    data = json.loads(release_path.read_text())
    total_updated = 0
    summary = {"version": version, "datasets": [], "new_datasets": [], "collections": []}

    dataset_lookup = lambda name: _get_dataset_doi(version, name)
    collection_lookup = lambda name: _get_collection_doi(version, name)

    for key, lookup_fn in [
        ("datasets", dataset_lookup),
        ("new_datasets", dataset_lookup),
        ("collections", collection_lookup),
    ]:
        if key not in data:
            continue
        updated_entries, n = _inject_dois(data[key], lookup_fn)
        data[key] = updated_entries
        total_updated += n
        for entry in updated_entries:
            if entry.get("doi"):
                summary[key].append({"name": entry["name"], "doi": entry["doi"]})

    summary["total_updated"] = total_updated

    if not dry_run and total_updated > 0:
        release_path.write_text(json.dumps(data, indent=2) + "\n")

    return summary


def sync_all_releases(dry_run: bool = False) -> list[dict]:
    """Sync dataset/collection DOIs for all release versions found in cloud-releases."""
    versions = sorted(
        [d.name for d in RELEASES_BASE.iterdir() if d.is_dir() and (d / "release.json").exists()]
    )
    return [sync_release(v, dry_run=dry_run) for v in versions]


def sync_all_release_dois(dry_run: bool = False) -> list[dict]:
    """Sync the top-level release_doi field for all release versions."""
    versions = sorted(
        [d.name for d in RELEASES_BASE.iterdir() if d.is_dir() and (d / "release.json").exists()]
    )
    return [sync_release_doi(v, dry_run=dry_run) for v in versions]
