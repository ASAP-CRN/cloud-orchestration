import os
import subprocess
import shutil
from pathlib import Path

__all__ = [
    "gcloud_ls",
    "gcloud_rsync",
    "gcloud_mv",
    "gcloud_rm",
    "gcloud_cp",
    "authenticate_with_service_account",
    "create_collection_bucket",
    "describe_bucket"
]

# force the right python version path
os.environ["CLOUDSDK_PYTHON"] = "/opt/homebrew/opt/python@3.13/bin/python3.13"

def _find_gcloud():
    """
    Find the gcloud executable path.

    Returns:
        str: Path to gcloud executable

    Raises:
        FileNotFoundError: If gcloud is not found
    """
    # Try to find gcloud in PATH
    gcloud_path = shutil.which("gcloud")

    if gcloud_path:
        return gcloud_path

    # Common installation paths
    possible_paths = [
        "/opt/homebrew/bin/gcloud",  # Homebrew on Apple Silicon
        "/usr/local/bin/gcloud",  # Homebrew on Intel Mac
        os.path.expanduser("~/google-cloud-sdk/bin/gcloud"),  # Manual installation
        "/usr/bin/gcloud",  # System installation
        "/opt/homebrew/share/google-cloud-sdk/bin/gcloud" # new Hombrew location
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        "gcloud command not found. Please install Google Cloud SDK: "
        "https://cloud.google.com/sdk/docs/install"
    )


# Cache the gcloud path to avoid repeated lookups
_GCLOUD_PATH = None

PROJECT="dnastack-asap-parkinsons"
REGION="us-central1"

MEMBER_DTI="group:asap-dti@dnastack.com"
MEMBER_READER="group:asap-cloud-readers@verily-bvdp.com"

ROLE_DTI="roles/storage.objectAdmin"
ROLE_READER="roles/storage.objectViewer"

def _get_gcloud_path():
    """Get cached gcloud path or find it."""
    global _GCLOUD_PATH
    if _GCLOUD_PATH is None:
        _GCLOUD_PATH = _find_gcloud()
    return _GCLOUD_PATH


# create functions to list, rsync and delete files into GCP
# Updated to use gcloud instead of gsutil
def gcloud_ls(bucket_name: str, prefix: str, project: str | None = None, dirs_only=False):
    """
    prints the files in a GCS bucket matching a given prefix.

    Args:
        bucket_name (str): The name of the GCS bucket.
        prefix (str): The prefix to filter objects.
        project (str | None): GCP project name. If None, uses default project [dnastack-asap-parkinsons]
        dirs_only (bool): If True, only returns directories
    Returns:
       list of files

    """
    default_project = "dnastack-asap-parkinsons"
    if project is None:
        project = default_project

    if prefix is None:
        prefix = ""

    if bucket_name.startswith("gs://"):
        bucket_name = bucket_name[5:]
        
    prefix = prefix + "/" if not prefix.endswith("/") else prefix
    gcloud = _get_gcloud_path()
    cmd = [
        gcloud,
        "storage",
        "ls",
        f"gs://{bucket_name}/{prefix}",
        f"--billing-project={project}",
    ]

    if dirs_only:
        cmd += ["--depth=1", "|", "grep", "'/$'"]

    # print(f"IN: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    # print(f"OUT: {result.stdout}")
    if result.returncode == 0:
        pass
    else:
        print(f"gcloud command failed: {result.stderr}")

    return result.stdout.split("\n")


def gcloud_ls_long(bucket_name: str, prefix: str, project: str | None = None):
    """
    prints the files in a GCS bucket matching a given prefix.

    Args:
        bucket_name (str): The name of the GCS bucket.
        prefix (str): The prefix to filter objects.
        project (str | None): GCP project name. If None, uses default project [dnastack-asap-parkinsons]

    Returns:
       list of files

    """
    default_project = "dnastack-asap-parkinsons"
    if project is None:
        project = default_project

    gcloud = _get_gcloud_path()
    cmd = [
        gcloud,
        "storage",
        "ls -a",
        f"gs://{bucket_name}/{prefix}",
        f"--billing-project={project}",
    ]

    print(f"IN: {' '.join(cmd)}")
    prefix = prefix + "/" if not prefix.endswith("/") else prefix
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"OUT: {result.stdout}")
    if result.returncode == 0:
        pass
    else:
        print(f"gcloud command failed: {result.stderr}")

    return result.stdout.split("\n")


def gcloud_rsync(
    source: str,
    destination: str,
    directory: bool = False,
    project: str | None = None,
    dry_run: bool = False,
    clobber: bool = False
):
    """
    rsync files to/from local paths or GCS buckets

    Args:
        source (str): local file path or GCS bucket path
        destination (str): local file path or GCS bucket path
        directory (bool): indicates if source the input is a directory
        project (str | None): GCP project name. If None, uses default project [dnastack-asap-parkinsons]

    Returns:
       None.
    """
    # if source.is_dir():
    #     if directory == False:
    #         print(f"mismatch between {source=} and {directory=}")
    #         directory = True

    if project is None:
        project = PROJECT

    gcloud = _get_gcloud_path()


    if directory:
        cmd = [
            gcloud,
            "storage",
            "rsync",
            "--recursive",
            # "--dry-run",
            source,
            destination,
            f"--billing-project={project}",
        ]
    else:
        cmd = [
            gcloud,
            "storage",
            "rsync",
            # "--dry-run",
            source,
            destination,
            f"--billing-project={project}",
        ]

    if dry_run:
        cmd += ["--dry-run"]
    elif clobber:
        cmd += ["--delete-unmatched-destination-objects"]
    
    print(f"IN: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        # print(f"gcloud command succeeded: {' '.join(cmd)}")
        pass
    else:
        print(f"gcloud command failed: {result.stderr}")
    return result.stdout


def gcloud_cp(
    source: str | Path,
    destination: str,
    directory=False,
    project: str | None = None,
    dry_run: bool = False
):
    """
    copies the files between os.path.join(paths, GCS) bucket path


    Args:
        source (str): local file path or GCS bucket path
        destination (str): local file path or GCS bucket path
        directory (bool): is the source or destination a directory
        project (str | None): GCP project name. If None, uses default project [dnastack-asap-parkinsons]

    Returns:
       None.
    """
    # force source to be a string
    if isinstance(source, Path):
        # if starts with "gs://", assume it's a GCS path
        if str(source).startswith("gs:/"):
            source = str(source).strip("gs://")
            source = f"gs://{source}"
        else:
            source = str(source)


    source = str(source)

    if project is None:
        project = PROJECT

    gcloud = _get_gcloud_path()

    if directory:
        cmd = [
            gcloud,
            "storage",
            "cp",
            "--recursive",
            # "--dry-run",
            source,
            destination,
            f"--billing-project={project}",
        ]
    else:
        cmd = [
            gcloud,
            "storage",
            "cp",
            # "--dry-run",
            source,
            destination,
            f"--billing-project={project}",
        ]

    if dry_run:
        cmd += "--dry-run"

    print(f"IN: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        # print(f"gcloud command succeeded: {' '.join(cmd)}")
        pass
    else:
        print(f"gcloud command failed: {result.stderr}")
    return result.stdout



def gcloud_mv(
    source: str | Path,
    destination: str,
    directory=False,
    project: str | None = None,
):
    """
    moves the files between os.path.join(paths, GCS) bucket path


    Args:
        source (str): local file path or GCS bucket path
        destination (str): local file path or GCS bucket path
        directory (bool): is the source or destination a directory
        project (str | None): GCP project name. If None, uses default project [dnastack-asap-parkinsons]

    Returns:
       None.
    """
    source = Path(source)

    if project is None:
        project = PROJECT

    if source.is_dir():
        if directory == False:
            print(f"mismatch between {source=} and {directory=}")
            directory = True

    gcloud = _get_gcloud_path()

    if directory:
        cmd = [
            gcloud,
            "storage",
            "mv",
            "--recursive",
            str(source),
            destination,
            f"--billing-project={project}",
        ]
    else:
        cmd = [
            gcloud,
            "storage",
            "mv",
            str(source),
            destination,
            f"--billing-project={project}",
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"gcloud command succeeded: {' '.join(cmd)}")
    else:
        print(f"gcloud command failed: {result.stderr}")

    return result.stdout


# NOTE: this is deprecated
def authenticate_with_service_account(key_file_path):
    """
    Authenticates with a Google Cloud service account using a key file.

    Args:
        key_file_path (str): The path to the service account key file.
    """

    gcloud = _get_gcloud_path()
    cmd = [gcloud, "auth", "activate-service-account", f"--key-file={key_file_path}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    return result


def gcloud_rm(destination: str | Path, directory=False, project: str | None = None):
    """
    copies the files to a GCS bucket path

    Args:
        destination (str): local file path or GCS bucket path
        directory (bool): is the source or destination a directory
        project (str | None): GCP project name. If None, uses default project [dnastack-asap-parkinsons]

    Returns:
       None.
    """

    if project is None:
        project = PROJECT

    gcloud = _get_gcloud_path()

    if directory:
        cmd = [
            gcloud,
            "storage",
            "rm",
            "--recursive",
            destination,
            f"--billing-project={project}",
        ]
    else:
        cmd = [gcloud, "storage", "rm", destination, f"--billing-project={project}"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"gcloud command succeeded: {' '.join(cmd)}")
    else:
        print(f"gcloud command failed: {result.stderr}")
    return result.stdout


def _create_bucket(bucket: str, project: str, region: str ):
    """
    
    """

    gcloud = _get_gcloud_path()

    cmd = [gcloud, "storage", "buckets", "create",  f"--location={region}", f"--project={project}", bucket]
    print(f"trying: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"gcloud command succeeded: {' '.join(cmd)}")
    else:
        print(f"gcloud command failed: {result.stderr}")
    return result.stdout


def create_collection_bucket(bucket: str, project: str | None = None, region: str | None = None):
    """
    
    """
    if project is None:
        project = PROJECT
    if region is None:
        region = REGION

    # MEMBER & ROLE hard-wired

    ret = _create_bucket(bucket, project, region)

    _add_policy(bucket, project, MEMBER_READER, ROLE_READER)
    _add_policy(bucket, project, MEMBER_DTI, ROLE_DTI)

def _add_policy(bucket: str, project: str, member: str, role:str):
    """
    
    """
    gcloud = _get_gcloud_path()
    cmd = [
        gcloud,  "storage", "buckets", 
        "add-iam-policy-binding", 
        bucket, f"--member={member}", f"--role={role}", 
        f"--project={project}"
        ]
    print(f"{' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"gcloud command succeeded: {' '.join(cmd)}")
    else:
        print(f"gcloud command failed: {result.stderr}")
    return result.stdout

def describe_bucket(bucket:str, project: str | None = None):
    """gcloud storage buckets describe gs://YOUR_BUCKET_NAME
    """
    if project is None:
        project = PROJECT
    gcloud = _get_gcloud_path()
    cmd = [gcloud, "storage", "buckets", "describe", bucket,  f"--project={project}"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"gcloud command succeeded: {' '.join(cmd)}")
    else:
        print(f"gcloud command failed: {result.stderr}")
    return result.stdout

