"""Command line interface for ASAP orchestration."""

import click
import os
from pathlib import Path
from .orchestrator import Orchestrator


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


if __name__ == '__main__':
    cli()