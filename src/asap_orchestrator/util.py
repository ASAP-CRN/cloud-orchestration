import os
import shutil
from pathlib import Path

__all__ = [
    "get_dataset_version",
    "get_release_version",
    "get_cde_version",
    "write_version",
    "archive_CDE",
]


######## HELPERS ########


def get_dataset_version(dataset_name: str, datasets_path: Path) -> str:
    """
    Get the version of the dataset from the dataset name
    """
    dataset_path = os.path.join(datasets_path, dataset_name)
    with open(os.path.join(dataset_path, "version"), "r") as f:
        ds_ver = f.read().strip()
    # ds_ver = "v2.0"

    return ds_ver


def get_release_version(release_path: Path) -> str:
    """
    Get the version of the release from the release_path
    """

    with open(os.path.join(release_path, "version"), "r") as f:
        release_ver = f.read().strip()

    return release_ver


def get_cde_version(cde_path: Path):
    """
    Get the version of the CDE from the cde_path
    """
    with open(os.path.join(cde_path, "cde_version"), "r") as f:
        cde_ver = f.read().strip()
    return cde_ver


def write_version(version: str, version_path: Path):
    """
    Write the version to the version_path
    """

    with open(version_path, "w") as f:
        f.write(version)


def archive_CDE(cde_path: Path, version: str, archive_root: Path) -> Path:
    """Copy a CDE version directory into an archive location.

    Args:
        cde_path: Path to the current CDE version directory.
        version: Version string used as the archive subdirectory name.
        archive_root: Root directory to archive into.

    Returns:
        Path to the archived CDE directory.
    """
    cde_path = Path(cde_path)
    dst = Path(archive_root) / version
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(cde_path, dst)
    return dst
