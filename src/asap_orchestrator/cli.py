"""Command line interface for ASAP orchestration."""

import click
import os
from pathlib import Path
from .orchestrator import Orchestrator
from .doi_sync import sync_release, sync_all_releases, sync_release_doi, sync_all_release_dois
from .dataset_archive import archive_dataset, archive_all_datasets
from .dataset_release_sync import sync_dataset, sync_all_datasets as sync_all_dataset_releases, _build_release_index


@click.group()
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub access token')
@click.option('--zenodo-token', envvar='ZENODO_TOKEN', help='Zenodo access token')
@click.pass_context
def cli(ctx, github_token, zenodo_token):
    """ASAP CRN Cloud Orchestration CLI"""
    ctx.ensure_object(dict)
    ctx.obj['github_token'] = github_token
    ctx.obj['zenodo_token'] = zenodo_token


@cli.command()
@click.argument('version')
@click.pass_context
def release(ctx, version):
    """Create a new release and manage datasets/collections."""
    orchestrator = Orchestrator(
        github_token=ctx.obj['github_token'],
        zenodo_token=ctx.obj['zenodo_token']
    )
    orchestrator.process_release(version)


@cli.command()
@click.argument('dataset_name')
@click.option('--title', help='Dataset title')
@click.option('--description', help='Dataset description')
@click.option('--version', default='1.0.0', help='Dataset version')
@click.pass_context
def create_dataset(ctx, dataset_name, title, description, version):
    """Create a new dataset."""
    orchestrator = Orchestrator(
        github_token=ctx.obj['github_token'],
        zenodo_token=ctx.obj['zenodo_token']
    )
    metadata = {
        'title': title or dataset_name,
        'description': description or '',
        'version': version,
        'creators': [{'name': 'ASAP CRN'}]
    }
    orchestrator.dataset_manager.create_dataset(dataset_name, metadata)


@cli.command()
@click.argument('collection_name')
@click.option('--title', help='Collection title')
@click.option('--description', help='Collection description')
@click.option('--version', default='1.0.0', help='Collection version')
@click.option('--datasets', multiple=True, help='Dataset names to include')
@click.pass_context
def create_collection(ctx, collection_name, title, description, version, datasets):
    """Create a new collection."""
    orchestrator = Orchestrator(
        github_token=ctx.obj['github_token'],
        zenodo_token=ctx.obj['zenodo_token']
    )
    metadata = {
        'title': title or collection_name,
        'description': description or '',
        'version': version,
        'creators': [{'name': 'ASAP CRN'}]
    }
    orchestrator.collection_manager.create_collection(collection_name, metadata, list(datasets))


@cli.command('sync-dois')
@click.argument('version', required=False)
@click.option('--dry-run', is_flag=True, help='Show what would be updated without writing files.')
def sync_dois(version, dry_run):
    """Sync DOIs from asap-crn-cloud-release-resources into release.json files.

    If VERSION is provided, only that release is synced; otherwise all releases are synced.
    """
    if version:
        results = [sync_release(version, dry_run=dry_run)]
    else:
        results = sync_all_releases(dry_run=dry_run)

    mode = "[DRY RUN] " if dry_run else ""
    for r in results:
        if "error" in r:
            click.echo(f"{mode}{r['version']}: ERROR — {r['error']}")
            continue
        n = r.get("total_updated", 0)
        if n == 0:
            click.echo(f"{mode}{r['version']}: no changes")
            continue
        click.echo(f"{mode}{r['version']}: updated {n} DOI(s)")
        for key in ("datasets", "new_datasets", "collections"):
            for entry in r.get(key, []):
                click.echo(f"  [{key}] {entry['name']} → {entry['doi']}")


@cli.command('sync-release-doi')
@click.argument('version', required=False)
@click.option('--dry-run', is_flag=True, help='Show what would be updated without writing files.')
def sync_release_doi_cmd(version, dry_run):
    """Sync the top-level release_doi field from README PDFs.

    If VERSION is provided, only that release is synced; otherwise all releases are synced.
    The DOI is extracted from the *README*.pdf file in each release directory.
    """
    if version:
        results = [sync_release_doi(version, dry_run=dry_run)]
    else:
        results = sync_all_release_dois(dry_run=dry_run)

    mode = "[DRY RUN] " if dry_run else ""
    for r in results:
        if "error" in r:
            doi_str = f" (doi={r.get('release_doi')})" if r.get('release_doi') else ""
            click.echo(f"{mode}{r['version']}: ERROR — {r['error']}{doi_str}")
            continue
        changed = r.get("changed", False)
        status = "updated" if changed else "no change"
        click.echo(f"{mode}{r['version']}: {status} → {r['release_doi']}  [{r.get('pdf', '')}]")


@cli.command('archive-dataset')
@click.argument('dataset_name', required=False)
@click.option('--dry-run', is_flag=True, help='Show what would be copied without writing files.')
def archive_dataset_cmd(dataset_name, dry_run):
    """Archive the current dataset version into archive/<version>/.

    Copies DOI/, refs/, and dataset.json from the dataset directory into
    cloud-datasets/datasets/<name>/archive/<version>/.

    If DATASET_NAME is provided, only that dataset is archived; otherwise all datasets are processed.
    Skips any archive/<version>/ that already has real content.
    """
    if dataset_name:
        results = [archive_dataset(dataset_name, dry_run=dry_run)]
    else:
        results = archive_all_datasets(dry_run=dry_run)

    mode = "[DRY RUN] " if dry_run else ""
    for r in results:
        if "error" in r:
            click.echo(f"{mode}{r['dataset']}: ERROR — {r['error']}")
        elif r.get("skipped"):
            click.echo(f"{mode}{r['dataset']} {r['version']}: skipped — {r['reason']}")
        else:
            click.echo(f"{mode}{r['dataset']} {r['version']}: archived {r['files_copied']} file(s) → archive/{r['version']}/")


@cli.command('sync-dataset-releases')
@click.argument('dataset_name', required=False)
@click.option('--dry-run', is_flag=True, help='Show what would change without writing files.')
def sync_dataset_releases_cmd(dataset_name, dry_run):
    """Sync dataset.json release history from release.json files.

    For each dataset, ensures the `releases` dict has an entry for every cloud
    release it participated in, replaces the `date` field with `dataset_version`,
    and updates the top-level `version` to match the most recent release.

    If DATASET_NAME is provided, only that dataset is synced; otherwise all datasets are synced.
    """
    dataset_map, cde_map = _build_release_index()

    if dataset_name:
        results = [sync_dataset(dataset_name, dataset_map, cde_map, dry_run=dry_run)]
    else:
        results = sync_all_dataset_releases(dry_run=dry_run)

    mode = "[DRY RUN] " if dry_run else ""
    for r in results:
        if "error" in r:
            click.echo(f"{mode}{r['dataset']}: ERROR — {r['error']}")
        elif r.get("skipped"):
            click.echo(f"{mode}{r['dataset']}: skipped — {r.get('reason', '')}")
        elif not r.get("changes"):
            click.echo(f"{mode}{r['dataset']}: no changes")
        else:
            click.echo(f"{mode}{r['dataset']}: {len(r['changes'])} change(s)")
            for c in r["changes"]:
                click.echo(f"  {c}")


if __name__ == '__main__':
    cli()