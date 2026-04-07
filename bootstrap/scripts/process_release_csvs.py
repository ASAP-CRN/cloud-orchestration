"""Script to process release CSV files and generate dataset and collection references.

Two CSV files are recognised per release directory:
  datasets.csv     – full snapshot of ALL datasets present at this release
  new_datasets.csv – only the datasets that are new or updated in this release

Both files share the same column schema.  When a dataset appears in both,
new_datasets.csv is authoritative (it carries the most specific updated info)
and the entry is flagged with ``is_new_in_release``.

In some releases every dataset is "new" (e.g. the very first release, or a
release where the whole cohort is refreshed), so a version directory is
considered valid when it contains *either* file.
"""

import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


# ── Low-level CSV reader ──────────────────────────────────────────────────────

def _na(value: Optional[str]) -> Optional[str]:
    """Return None for empty / 'NA' strings, otherwise return the value."""
    return None if (not value or value.strip().upper() == 'NA') else value


def _build_dataset_entry(ds: Dict, include_release: bool = False) -> Dict:
    """Build a full dataset metadata entry from a raw CSV record.

    Args:
        ds:              Dict returned by ``read_csv``.
        include_release: When True, appends a ``release`` sub-dict with the
                         dataset's ``latest_release`` value.  Set False when
                         the release context is already known from the parent
                         structure (e.g. inside releases_references.json).
    """
    entry: Dict = {
        'name':        ds['name'],
        'title':       ds['full_name'],
        'description': f"{ds['type']} dataset from {ds['team_name']}",
        'version':     ds['version'],
        'doi':         None,
        'creators':    [{'name': ds['team_name'], 'affiliation': 'ASAP CRN'}],
        'keywords':    [ds['type'], ds['grouping'], ds['team']],
        'license':     'CC-BY-4.0',
        'references':  [],
        'collection':  ds['collection'],
        'buckets':     ds['buckets'],
        'cde_version': ds.get('cde_version'),
    }
    if include_release:
        entry['release'] = {'version': ds['latest_release'], 'date': None}
    return entry


def read_csv(csv_path: str, version: str) -> List[Dict]:
    """Read a datasets CSV file and return a list of dataset dicts.

    Args:
        csv_path: Path to the CSV file.
        version:  Release version string used to stamp ``release_processed``.
    """
    records = []
    with open(csv_path, newline='') as f:
        for row in csv.DictReader(f):
            records.append({
                'name':               row['dataset_name'],
                'full_name':          row['full_dataset_name'],
                'type':               row['dataset_type'],
                'version':            row['dataset_version'],
                'team':               row['team'],
                'team_name':          row['team_name'],
                'collection':         _na(row.get('collection')),
                'collection_name':    _na(row.get('collection_name')),
                'collection_version': _na(row.get('collection_version')),
                'workflow':           _na(row.get('workflow')),
                'buckets': {
                    'raw':  row['raw_bucket_name'],
                    'dev':  row['dev_bucket_name'],
                    'uat':  row['uat_bucket_name'],
                    'prod': row['prod_bucket_name'],
                },
                'cde_version':     row['cde_version'],
                'grouping':        row['grouping'],
                'cohort':          row['cohort'].strip().lower() == 'true',
                'latest_release':  row['latest_release'],
                'release_type':    row['release_type'],
                'release_processed': version,
            })
    return records


# ── Dataset processing ────────────────────────────────────────────────────────

def process_datasets(base_path: str, versions: List[str]) -> Dict[str, Dict]:
    """Build a release-keyed datasets dict from all release CSV files.

    Processing order per version (later step wins for the same dataset name):
      1. ``datasets.csv``     – full snapshot; establishes the baseline
      2. ``new_datasets.csv`` – new/updated entries; overrides baseline and
                                adds ``is_new_in_release`` flag

    Returns:
        { release_version: { dataset_name: dataset_info } }
    """
    all_datasets: Dict[str, Dict] = {}

    for version in sorted(versions):
        version_path = os.path.join(base_path, version)

        # ── Step 1: full snapshot ─────────────────────────────────────────────
        datasets_csv = os.path.join(version_path, 'datasets.csv')
        if os.path.exists(datasets_csv):
            print(f"  [datasets    ] {datasets_csv}")
            for ds in read_csv(datasets_csv, version):
                all_datasets.setdefault(ds['latest_release'], {})[ds['name']] = ds

        # ── Step 2: new / updated entries (override) ──────────────────────────
        new_datasets_csv = os.path.join(version_path, 'new_datasets.csv')
        if os.path.exists(new_datasets_csv):
            print(f"  [new_datasets] {new_datasets_csv}")
            for ds in read_csv(new_datasets_csv, version):
                ds['is_new_in_release'] = version   # mark before storing
                all_datasets.setdefault(ds['latest_release'], {})[ds['name']] = ds

    return all_datasets


# ── Dataset reference builder ─────────────────────────────────────────────────

def build_datasets_references(datasets_by_release: Dict[str, Dict]) -> Dict[str, Dict]:
    """Build a name-keyed dataset reference with a per-dataset-version history.

    ``datasets_by_release`` is keyed by ``latest_release``, so each unique
    dataset version (e.g. jakobsson v1.0 vs v2.0) naturally lands in a
    different bucket.  Iterating in sorted order accumulates every release a
    given dataset version appeared in under ``releases`` (plural), so no
    release history is lost when the same dataset version spans multiple
    consecutive releases.

    Schema:
      {
        "dataset_name": {
          "name": ..., "title": ...,
          "versions": {
            "v1.0": {
              "version": "v1.0", "date": null,
              "description": ..., "doi": null,
              "creators": [...], "keywords": [...],
              "license": "CC-BY-4.0", "references": [],
              "collection": ..., "buckets": {...}, "cde_version": ...,
              "releases": {
                "v1.0.0": {"cde_version": "v2.0", "date": null},
                "v2.0.0": {"cde_version": "v2.5", "date": null}
              }
            },
            "v2.0": { ... }
          }
        }
      }
    """
    flat: Dict[str, Dict] = {}

    for release in sorted(datasets_by_release):
        for name, ds in datasets_by_release[release].items():
            if name not in flat:
                flat[name] = {
                    'name':     ds['name'],
                    'title':    ds['full_name'],
                    'versions': {},
                }
            ds_version = ds['version']
            if ds_version not in flat[name]['versions']:
                flat[name]['versions'][ds_version] = {
                    'version':     ds_version,
                    'date':        None,
                    'description': f"{ds['type']} dataset from {ds['team_name']}",
                    'doi':         None,
                    'creators':    [{'name': ds['team_name'], 'affiliation': 'ASAP CRN'}],
                    'keywords':    [ds['type'], ds['grouping'], ds['team']],
                    'license':     'CC-BY-4.0',
                    'references':  [],
                    'collection':  ds['collection'],
                    'buckets':     ds['buckets'],
                    'cde_version': ds.get('cde_version'),
                    'releases':    {},
                }
            # Accumulate every release this dataset version appeared in
            flat[name]['versions'][ds_version]['releases'][release] = {
                'cde_version': ds.get('cde_version'),
                'date':        None,
            }

    return flat


# ── Collection processing ─────────────────────────────────────────────────────

def process_collections(base_path: str, versions: List[str]) -> Dict[str, Dict]:
    """Build a name-keyed collection reference with a per-collection-version history.

    Reads ``datasets.csv`` for each release in sorted order.  Every unique
    (collection, collection_version) pair seen across releases gets its own
    entry under ``versions``.  When the same collection version appears in
    multiple consecutive releases (datasets just carried forward), the later
    release wins so that ``datasets``, ``teams``, and ``types`` reflect the
    most-complete snapshot.

    Schema:
      {
        "collection_name": {
          "name": ..., "title": ...,
          "versions": {
            "v1.0.0": {
              "version": "v1.0.0", "date": null, "doi": null,
              "datasets": [...], "teams": [...], "types": [...],
              "release": {"version": ..., "date": null}
            },
            "v2.0.0": { ... }
          }
        }
      }
    """
    collections: Dict[str, Dict] = {}

    for version in sorted(versions):
        version_path = os.path.join(base_path, version)
        datasets_csv = os.path.join(version_path, 'datasets.csv')
        if not os.path.exists(datasets_csv):
            continue

        # Build a per-collection snapshot for this release
        coll_snapshot: Dict[str, Dict] = {}
        for ds in read_csv(datasets_csv, version):
            coll_name = ds.get('collection')
            if not coll_name:
                continue
            if coll_name not in coll_snapshot:
                coll_snapshot[coll_name] = {
                    'title':       ds.get('collection_name') or coll_name,
                    'version':     ds['collection_version'],
                    'cde_version': ds.get('cde_version'),
                    'datasets':    [],
                    'teams':       set(),
                    'types':       set(),
                }
            snap = coll_snapshot[coll_name]
            if ds['name'] not in snap['datasets']:
                snap['datasets'].append(ds['name'])
            snap['teams'].add(ds['team'])
            snap['types'].add(ds['type'])

        # Merge snapshot into versioned collection records
        for coll_name, snap in coll_snapshot.items():
            if coll_name not in collections:
                collections[coll_name] = {
                    'name':     coll_name,
                    'title':    snap['title'],
                    'versions': {},
                }
            # Prefer a non-trivial title
            if snap['title'] and snap['title'] != coll_name:
                collections[coll_name]['title'] = snap['title']

            coll_ver = snap['version']
            # Later releases overwrite earlier ones for the same collection
            # version, so datasets/teams/types stay current.
            collections[coll_name]['versions'][coll_ver] = {
                'version':  coll_ver,
                'date':     None,
                'doi':      None,
                'datasets': snap['datasets'],
                'teams':    sorted(snap['teams']),
                'types':    sorted(snap['types']),
                'release':  {
                    'version':     version,
                    'cde_version': snap['cde_version'],
                    'date':        None,
                },
            }

    return collections


# ── Release-summary processing ────────────────────────────────────────────────

def process_releases(base_path: str, versions: List[str]) -> Dict[str, Dict]:
    """Build a version-keyed releases reference dict.

    For each release directory the function reads both CSV files and produces:
      all_datasets    – every dataset listed in ``datasets.csv``
      new_datasets    – every dataset listed in ``new_datasets.csv``
      all_collections – unique collections derived from ``datasets.csv``

    Each dataset entry contains the full metadata (name, title, description,
    version, doi, creators, keywords, license, references, collection, buckets,
    cde_version) read from the per-release CSV — identical to the schema used in
    datasets_references.json except the ``release`` sub-dict is omitted (it is
    implied by the parent release key).  Each collection entry contains
    {name, version, doi, cde_version}.  All doi fields are placeholders to be
    filled in later via Zenodo.

    Schema:
      {
        "v3.0.1": {
          "all_datasets":    [{ <full dataset metadata> }, ...],
          "new_datasets":    [{ <full dataset metadata> }, ...],
          "all_collections": [{"name": ..., "version": ..., "doi": null, "cde_version": ...}]
        }
      }
    """
    releases: Dict[str, Dict] = {}

    for version in sorted(versions):
        version_path = os.path.join(base_path, version)

        all_ds:  List[Dict] = []
        new_ds:  List[Dict] = []
        colls_seen: Dict[str, Dict] = {}   # coll_name → entry

        # ── datasets.csv → all_datasets + all_collections ─────────────────────
        datasets_csv = os.path.join(version_path, 'datasets.csv')
        if os.path.exists(datasets_csv):
            for ds in read_csv(datasets_csv, version):
                all_ds.append(_build_dataset_entry(ds, include_release=False))
                if ds['collection'] and ds['collection'] not in colls_seen:
                    colls_seen[ds['collection']] = {
                        'name':        ds['collection'],
                        'version':     ds['collection_version'],
                        'doi':         None,
                        'cde_version': ds.get('cde_version'),
                    }

        # ── new_datasets.csv → new_datasets ───────────────────────────────────
        new_datasets_csv = os.path.join(version_path, 'new_datasets.csv')
        if os.path.exists(new_datasets_csv):
            for ds in read_csv(new_datasets_csv, version):
                new_ds.append(_build_dataset_entry(ds, include_release=False))

        releases[version] = {
            'all_datasets':    all_ds,
            'new_datasets':    new_ds,
            'all_collections': list(colls_seen.values()),
        }

    return releases


# ── Top-level entry point ─────────────────────────────────────────────────────

def create_references(base_path: str, versions: List[str]) -> Dict:
    """Create all three reference dicts from release CSV files.

    Returns:
        {
          'datasets':    { name: dataset_info },              → datasets_references.json
          'collections': { name: collection_info },           → collections_references.json
          'releases':    { version: release_summary },        → releases_references.json
          'processed_versions': [...],
          'last_updated': '<ISO timestamp>',
        }
    """
    print(f"Processing {len(versions)} release version(s): {versions}")

    datasets_by_release = process_datasets(base_path, versions)
    datasets            = build_datasets_references(datasets_by_release)
    collections         = process_collections(base_path, versions)
    releases            = process_releases(base_path, versions)

    print(f"  → {len(datasets)} unique dataset(s)")
    print(f"  → {len(collections)} unique collection(s)")
    print(f"  → {len(releases)} release entries")

    return {
        'datasets':           datasets,
        'collections':        collections,
        'releases':           releases,
        'processed_versions': versions,
        'last_updated':       datetime.now().isoformat(),
    }


def get_all_versions(base_path: str, candidates: List[str]) -> List[str]:
    """Return the subset of candidate versions that have at least one CSV file.

    A release directory is considered valid when it contains either
    ``datasets.csv`` OR ``new_datasets.csv`` (or both).
    """
    available = []
    for version in candidates:
        version_path = os.path.join(base_path, version)
        has_csv = (
            os.path.exists(os.path.join(version_path, 'datasets.csv'))
            or os.path.exists(os.path.join(version_path, 'new_datasets.csv'))
        )
        if has_csv:
            available.append(version)
        else:
            print(f"Warning: no CSV files found for {version}, skipping")
    return available


def main():
    """Process all release versions and write the three reference JSON files."""

    root_path = Path(__file__).resolve().parents[2]

    base_path = root_path / f"asap-crn-cloud-release-resources/releases"
    output_dir = root_path / "cloud-orchestration/references"

    # Full list of known release versions (order matters for override logic)
    candidates = [
        'v1.0.0', 'v2.0.0', 'v2.0.1', 'v2.0.2', 'v2.0.3', 'v2.0.4',
        'v3.0.0', 'v3.0.1', 'v3.0.2', 'v4.0.0',
    ]

    # Only process versions that actually have data on disk
    versions = get_all_versions(base_path, candidates)
    print(f"Available versions: {versions}\n")

    # Build all three reference dicts
    references = create_references(base_path, versions)

    # Persist to disk
    os.makedirs(output_dir, exist_ok=True)

    # 1. datasets_references.json  — { dataset_name: metadata }
    with open(os.path.join(output_dir, 'datasets_references.json'), 'w') as f:
        json.dump(references['datasets'], f, indent=2)
    print("Wrote datasets_references.json")

    # 2. collections_references.json — { collection_name: metadata }
    with open(os.path.join(output_dir, 'collections_references.json'), 'w') as f:
        json.dump(references['collections'], f, indent=2)
    print("Wrote collections_references.json")

    # 3. releases_references.json — { version: { all_datasets, new_datasets, all_collections } }
    with open(os.path.join(output_dir, 'releases_references.json'), 'w') as f:
        json.dump(references['releases'], f, indent=2)
    print("Wrote releases_references.json")

    total_datasets    = len(references['datasets'])
    total_collections = len(references['collections'])
    print(f"\nDone. {total_datasets} datasets, {total_collections} collections, "
          f"{len(references['releases'])} releases.")


if __name__ == '__main__':
    main()