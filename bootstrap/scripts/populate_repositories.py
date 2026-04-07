"""Script to populate cloud repositories using processed references.

References are nested under release-version keys:
  datasets_references.json  -> { "<release>": { "<dataset_name>": {...} } }
  collections_references.json -> { "<release>": { "<collection_name>": {...} } }

Folder structure created per template READMEs:
  cloud-datasets  : datasets/<name>/{dataset.json, DOI/, refs/, scripts/, archive/}
  cloud-collections: collections/<name>/{collection.json, scripts/, archive/}
  cloud-releases  : releases/<version>/{release.json, scripts/}
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from asap_orchestrator import Orchestrator


def load_references(references_dir: str):
    """Load the nested release-keyed references.

    Returns:
        datasets_by_release  – dict[release_version, dict[name, info]]
        collections_by_release – dict[release_version, dict[name, info]]
    """
    with open(os.path.join(references_dir, 'datasets_references.json'), 'r') as f:
        datasets_by_release = json.load(f)

    with open(os.path.join(references_dir, 'collections_references.json'), 'r') as f:
        collections_by_release = json.load(f)

    return datasets_by_release, collections_by_release


def create_dataset_metadata(dataset_info: dict) -> dict:
    """Convert dataset reference to metadata format for the orchestrator."""
    return {
        'title': dataset_info['full_name'],
        'description': f"{dataset_info['type']} dataset from {dataset_info['team_name']}",
        'version': dataset_info['version'],
        'creators': [{'name': dataset_info['team_name'], 'affiliation': 'ASAP CRN'}],
        'keywords': [dataset_info['type'], dataset_info['grouping'], dataset_info['team']],
        'license': 'CC-BY-4.0',
        'dataset_type': dataset_info['type'],
        'team': dataset_info['team'],
        'buckets': dataset_info['buckets'],
        'cde_version': dataset_info['cde_version'],
        'collection': dataset_info['collection'],
        'latest_release': dataset_info['latest_release'],
        'release_type': dataset_info['release_type']
    }


def create_collection_metadata(collection_info: dict) -> dict:
    """Convert collection reference to metadata format for the orchestrator."""
    return {
        'title': collection_info['full_name'],
        'description': f"Collection of {len(collection_info['datasets'])} datasets",
        'version': collection_info['version'],
        'creators': [{'name': team, 'affiliation': 'ASAP CRN'} for team in collection_info['teams']],
        'keywords': collection_info['types'] + ['collection'],
        'license': 'CC-BY-4.0',
        'dataset_types': collection_info['types'],
        'teams': collection_info['teams'],
        'dataset_count': len(collection_info['datasets'])
    }


def _create_placeholder(repo, path: str, message: str) -> None:
    """Create a .gitkeep placeholder file inside a subdirectory in a GitHub repo."""
    try:
        repo.create_file(f"{path}/.gitkeep", message, "")
    except Exception:
        pass  # already exists


def create_dataset_subdirs(repo, name: str) -> None:
    """Create template subdirectories for a dataset per README-datasets.md.

    Structure:
      datasets/<name>/DOI/
      datasets/<name>/refs/
      datasets/<name>/scripts/
      datasets/<name>/archive/
    """
    base = f"datasets/{name}"
    for subdir in ("DOI", "refs", "scripts", "archive"):
        _create_placeholder(repo, f"{base}/{subdir}", f"Init {subdir}/ for dataset {name}")


def create_collection_subdirs(repo, name: str) -> None:
    """Create template subdirectories for a collection per README-collections.md.

    Structure:
      collections/<name>/scripts/
      collections/<name>/archive/
    """
    base = f"collections/{name}"
    for subdir in ("scripts", "archive"):
        _create_placeholder(repo, f"{base}/{subdir}", f"Init {subdir}/ for collection {name}")


def create_release_structure(repo, version: str, release_info: dict) -> None:
    """Create the releases/<version>/ structure per README-releases.md.

    Structure:
      releases/<version>/release.json
      releases/<version>/scripts/
    """
    base = f"releases/{version}"
    release_json = json.dumps(release_info, indent=2)
    try:
        repo.create_file(f"{base}/release.json", f"Add release.json for {version}", release_json)
    except Exception:
        pass  # already exists
    _create_placeholder(repo, f"{base}/scripts", f"Init scripts/ for release {version}")


def populate_repositories(release_filter: Optional[str] = None):
    """Populate the cloud repositories with dataset and collection references.

    Args:
        release_filter: If provided, only process this release version (e.g. "v3.0.1").
                        When None (default) all releases are processed.
    """
    references_dir = Path(__file__).parent.parent / "references"
    datasets_by_release, collections_by_release = load_references(str(references_dir))

    # Optionally limit to one release
    if release_filter:
        datasets_by_release = {release_filter: datasets_by_release.get(release_filter, {})}
        collections_by_release = {release_filter: collections_by_release.get(release_filter, {})}

    # Initialize orchestrator (requires environment variables)
    github_token = os.getenv('GITHUB_TOKEN')
    zenodo_token = os.getenv('ZENODO_TOKEN')

    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        return

    orchestrator = Orchestrator(github_token=github_token, zenodo_token=zenodo_token)

    total_datasets = sum(len(v) for v in datasets_by_release.values())
    total_collections = sum(len(v) for v in collections_by_release.values())
    print(
        f"Processing {total_datasets} datasets and {total_collections} collections "
        f"across releases: {sorted(set(list(datasets_by_release) + list(collections_by_release)))}"
    )

    # ── Datasets ──────────────────────────────────────────────────────────────
    ds_repo = orchestrator.github_manager.get_repo("ASAP-CRN/cloud-datasets")
    for release, datasets in sorted(datasets_by_release.items()):
        print(f"\n[{release}] Creating/updating {len(datasets)} datasets")
        for name, dataset_info in datasets.items():
            print(f"  dataset: {name}")
            try:
                metadata = create_dataset_metadata(dataset_info)
                orchestrator.dataset_manager.create_dataset(name, metadata)
                create_dataset_subdirs(ds_repo, name)
            except Exception as e:
                print(f"  ERROR dataset {name}: {e}")

    # ── Collections ───────────────────────────────────────────────────────────
    coll_repo = orchestrator.github_manager.get_repo("ASAP-CRN/cloud-collections")
    for release, collections in sorted(collections_by_release.items()):
        print(f"\n[{release}] Creating/updating {len(collections)} collections")
        for name, collection_info in collections.items():
            print(f"  collection: {name}")
            try:
                metadata = create_collection_metadata(collection_info)
                dataset_names = collection_info['datasets']
                orchestrator.collection_manager.create_collection(name, metadata, dataset_names)
                create_collection_subdirs(coll_repo, name)
            except Exception as e:
                print(f"  ERROR collection {name}: {e}")

    # ── Releases ──────────────────────────────────────────────────────────────
    releases_repo = orchestrator.github_manager.get_repo("ASAP-CRN/cloud-releases")
    all_releases = sorted(set(list(datasets_by_release) + list(collections_by_release)))
    for release in all_releases:
        print(f"\n[{release}] Initialising release directory")
        release_info = {
            "release_version": release,
            "datasets": list(datasets_by_release.get(release, {}).keys()),
            "collections": list(collections_by_release.get(release, {}).keys()),
        }
        try:
            create_release_structure(releases_repo, release, release_info)
        except Exception as e:
            print(f"  ERROR release {release}: {e}")

    print("\nRepository population complete!")


def main():
    """Main function.

    Optional CLI argument: release version to process (e.g. v3.0.1).
    If omitted, all releases found in the reference files are processed.

    Usage:
        python scripts/populate_repositories.py            # process all releases
        python scripts/populate_repositories.py v3.0.1    # process a single release
    """
    import sys

    # Check if environment variables are set
    if not os.getenv('GITHUB_TOKEN'):
        print("Please set GITHUB_TOKEN environment variable")
        print("Example: export GITHUB_TOKEN=your_token_here")
        return

    release_filter = sys.argv[1] if len(sys.argv) > 1 else None
    if release_filter:
        print(f"Filtering to release: {release_filter}")

    populate_repositories(release_filter=release_filter)


if __name__ == '__main__':
    main()