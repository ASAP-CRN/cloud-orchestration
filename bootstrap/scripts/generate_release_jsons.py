"""Script to generate release.json files for each release version."""

import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime


def get_datasets_from_csv(csv_path: str) -> tuple:
    """Extract dataset names and collections from a datasets CSV file."""
    datasets = []
    collections = set()
    cde_version = None

    if not os.path.exists(csv_path):
        return datasets, list(collections), cde_version

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dataset_name = row['dataset_name']
            if dataset_name not in datasets:
                datasets.append(dataset_name)

            # Track CDE version (should be consistent within a release)
            if cde_version is None:
                cde_version = row['cde_version']

            # Track collections
            collection = row.get('collection')
            if collection and collection != 'NA':
                collections.add(collection)

    return datasets, sorted(list(collections)), cde_version or 'v1.0'


def generate_release_jsons():
    """Generate release.json files for all releases from CSV files."""
    # Base path to releases
    releases_base = "/Users/ergonyc/Projects/ASAP/asap-crn-cloud-release-resources/releases"

    # Versions
    versions = ['v1.0.0', 'v2.0.0', 'v2.0.1', 'v2.0.2', 'v2.0.3', 'v3.0.0', 'v3.0.1']

    for version in versions:
        version_path = os.path.join(releases_base, version)

        if not os.path.exists(version_path):
            print(f"Warning: Release directory not found: {version_path}")
            continue

        print(f"Generating release.json for {version}")

        # Read datasets from CSV
        datasets_csv = os.path.join(version_path, 'datasets.csv')
        datasets, collections, cde_version = get_datasets_from_csv(datasets_csv)

        # Create release.json structure
        release_json = {
            'release_version': version,
            'cde_version': cde_version,
            'release_doi': '',  # Empty for now, will be populated when DOI is available
            'datasets': datasets,
            'collections': collections,
            'created': datetime.now().isoformat(),
            'metadata': {
                'total_datasets': len(datasets),
                'total_collections': len(collections),
                'source': f'{version}/datasets.csv'
            }
        }

        # Write to file
        output_path = os.path.join(version_path, 'release.json')
        with open(output_path, 'w') as f:
            json.dump(release_json, f, indent=2)

        print(f"  ✓ Created {output_path}")
        print(f"    - Datasets: {len(datasets)}")
        print(f"    - Collections: {len(collections)}")
        print(f"    - CDE Version: {cde_version}")

    print("\nRelease JSON generation complete!")


def main():
    """Main function."""
    generate_release_jsons()


if __name__ == '__main__':
    main()