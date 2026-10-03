"""Zenodo InvenioRDM Records API client for DOI generation and version management.

This is the InvenioRDM-based counterpart to `zenodo_util.ZenodoClient`, which
targets Zenodo's legacy Deposit API (`/api/deposit/depositions`). Zenodo now
runs on InvenioRDM, whose current REST API is the Records API
(`/api/records`) used here. Endpoint shapes are documented at
https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records/; the
official (higher-level) Python client is
https://github.com/inveniosoftware/inveniordm-py.

Not yet wired into `doi.py` / `__init__.py`. Method names mirror
`ZenodoClient` where a direct equivalent exists, so callers can be migrated
later, but note the model differences:

- Deposits are called "records"; an unpublished one is a "draft".
- Files are keyed by filename (`key`), not a numeric file id, and are
  uploaded in three steps: initialize, PUT content, commit.
- There is no `newversion`/`discard` action link; use
  `POST /api/records/{id}/versions` and `DELETE /api/records/{id}/draft`
  instead. Editing a published record's metadata means first calling
  `POST /api/records/{id}/draft` (`unlock_deposition`) to create an
  editable draft copy.

Usage::

    from asap_orchestrator.zenodo_rdm_util import ZenodoRDMClient

    zenodo = ZenodoRDMClient(sandbox=True)
    draft = zenodo.create_new_deposition(metadata)
    zenodo.upload_file("README.md")
    zenodo.publish()
"""

import json
import os
from pathlib import Path

import requests

__all__ = [
    "ZenodoRDMClient",
]


class ZenodoRDMClient:
    """Client for Zenodo's InvenioRDM Records API.

    Use this class to create, update, version, and publish Zenodo records
    via the current (InvenioRDM) REST API.
    """

    title: str | None = None
    record_id: str | None = None
    sandbox: bool = False
    _token: str | None = None

    def __init__(
        self,
        record_id: str | None = None,
        sandbox: bool | None = None,
        token: str | None = None,
    ):
        """initialization method"""
        self.sandbox = bool(sandbox)
        if self.sandbox:
            self._endpoint = "https://sandbox.zenodo.org/api"
        else:
            self._endpoint = "https://zenodo.org/api"

        self.record_id = record_id
        self._token = self._load_from_env() if token is None else token

    def __repr__(self):
        return f"ZenodoRDMClient('{self.title}', '{self.record_id}')"

    def __str__(self):
        return f"{self.title} --- {self.record_id}"

    # ---------------------------------------------
    # token loading (same ~/.zenodo_token convention as ZenodoClient)
    # ---------------------------------------------
    @staticmethod
    def _load_token(sandbox: bool = False) -> str:
        """reads the configuration file

        Configuration file should be ~/.zenodo_token

        Args:
            sandbox (bool): whether to load the sandbox token

        Returns:
            str: the API access token
        """
        target_key = "ACCESS_TOKEN-sandbox" if sandbox else "ACCESS_TOKEN"

        dotrc = os.environ.get(
            target_key, os.path.join(str(Path.home()), ".zenodo_token")
        )

        if os.path.exists(dotrc):
            api_token = ""
            with open(dotrc) as file:
                for line in file.readlines():
                    if ":" in line:
                        key, value = line.strip().split(":", 1)
                        if key == target_key:
                            api_token = value.strip()
                            break
                    else:
                        api_token = line.strip()
        else:
            api_token = dotrc

        return api_token

    def _load_from_env(self) -> str:
        return self._load_token(self.sandbox)

    @property
    def token(self) -> str | None:
        return self._token

    def _headers(self, content_type: str | None = "application/json") -> dict:
        headers = {"Authorization": f"Bearer {self.token}"}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    # ---------------------------------------------
    # record / draft retrieval
    # ---------------------------------------------
    @property
    def deposition(self) -> dict:
        """Get the current record: the draft if unpublished, else the published record."""
        return self._get_record_by_id()

    def _get_record_by_id(self, record_id: str | None = None) -> dict:
        """gets a record by id, preferring the draft over the published version

        Args:
            record_id (str): record id, if None, uses self.record_id

        Returns:
            dict: the record/draft JSON
        """
        record_id = record_id if record_id is not None else self.record_id
        if record_id is None:
            raise ValueError(
                "No record_id set. Call create_new_deposition() or set_deposition_id() first."
            )

        self.record_id = record_id

        r = requests.get(
            f"{self._endpoint}/records/{record_id}/draft", headers=self._headers()
        )
        if r.status_code == 404:
            r = requests.get(
                f"{self._endpoint}/records/{record_id}", headers=self._headers()
            )
        r.raise_for_status()
        data = r.json()
        self.title = data.get("metadata", {}).get("title")
        return data

    def get_deposition(self, record_id: str | None = None) -> dict:
        """gets the record/draft by id (alias for the `deposition` property, kept for parity
        with `ZenodoClient.get_deposition`).

        Args:
            record_id (str): record id, if None, uses self.record_id

        Returns:
            dict: the record/draft JSON
        """
        return self._get_record_by_id(record_id)

    def set_deposition_id(self, record_id: str):
        """point the client at an existing record/draft by id"""
        self._get_record_by_id(record_id)

    def _get_record_id_from_doi(self, doi: str) -> str:
        """return the record id for a given Zenodo DOI (10.5281/zenodo.NNNNNNN)

        Args:
            doi (str): the zenodo doi

        Returns:
            str: the record id (the trailing digits of the doi)
        """
        return doi.rstrip("/").split(".")[-1]

    def get_record_by_doi(self, doi: str) -> dict:
        """search for a published record by DOI

        Args:
            doi (str): the zenodo doi, e.g. "10.5281/zenodo.1234567"

        Returns:
            dict: the matching record JSON

        Raises:
            ValueError: if no record matches the DOI
        """
        r = requests.get(
            f"{self._endpoint}/records",
            params={"q": f'pids.doi.identifier:"{doi}"'},
            headers=self._headers(),
        )
        r.raise_for_status()
        hits = r.json().get("hits", {}).get("hits", [])
        if not hits:
            raise ValueError(f"No record found for DOI {doi}")
        return hits[0]

    # ---------------------------------------------
    # create / update
    # ---------------------------------------------
    def create_new_deposition(self, metadata: dict | None = None) -> dict:
        """creates a new draft record

        Unlike the legacy Deposit API, a draft is created with its metadata
        (and access settings) in the same request rather than empty-then-set.

        Args:
            metadata (dict, optional): initial record metadata. Defaults to
                a minimal dataset resource_type if not provided.

        Returns:
            dict: the created draft JSON
        """
        payload = {
            "access": {"record": "public", "files": "public"},
            "files": {"enabled": True},
            "metadata": metadata or {"resource_type": {"id": "dataset"}},
        }
        r = requests.post(
            f"{self._endpoint}/records",
            headers=self._headers(),
            data=json.dumps(payload),
        )
        r.raise_for_status()
        data = r.json()
        self.record_id = data["id"]
        self.title = data.get("metadata", {}).get("title")
        return data

    def change_metadata(self, metadata: dict) -> dict:
        """update the current draft's metadata

        Args:
            metadata (dict): metadata to set on the draft.

        Returns:
            dict: the updated draft JSON

        PUT replaces the whole draft body, so the current draft is fetched
        first and only its `metadata` key is replaced.
        """
        if self.record_id is None:
            raise ValueError(
                "Not pointing to a record. Call create_new_deposition() or set_deposition_id() first."
            )

        draft = self._get_record_by_id()
        draft["metadata"] = metadata

        r = requests.put(
            f"{self._endpoint}/records/{self.record_id}/draft",
            headers=self._headers(),
            data=json.dumps(draft),
        )
        r.raise_for_status()
        return r.json()

    def unlock_deposition(self, record_id: str | None = None) -> dict:
        """create an editable draft from a published record

        Args:
            record_id (str): record id, if None, uses self.record_id

        Returns:
            dict: the new draft JSON
        """
        record_id = record_id if record_id is not None else self.record_id
        r = requests.post(
            f"{self._endpoint}/records/{record_id}/draft", headers=self._headers()
        )
        r.raise_for_status()
        self.record_id = record_id
        return r.json()

    def delete_deposition(self, record_id: str | None = None):
        """delete a draft record (published records cannot be deleted via the API)

        Args:
            record_id (str): record id, if None, uses self.record_id
        """
        record_id = record_id if record_id is not None else self.record_id
        r = requests.delete(
            f"{self._endpoint}/records/{record_id}/draft", headers=self._headers()
        )
        r.raise_for_status()

    # ---------------------------------------------
    # files
    # ---------------------------------------------
    def list_files(self, record_id: str | None = None):
        """list files on the current draft

        Args:
            record_id (str): record id, if None, uses self.record_id

        prints filenames to screen
        """
        files = self.get_files(record_id)
        print("Files")
        print("------------------------")
        for file in files:
            print(file["key"])

    def get_files(self, record_id: str | None = None) -> list[dict]:
        """get files on the current draft

        Args:
            record_id (str): record id, if None, uses self.record_id

        Returns:
            list[dict]: file entries
        """
        record_id = record_id if record_id is not None else self.record_id
        r = requests.get(
            f"{self._endpoint}/records/{record_id}/draft/files",
            headers=self._headers(),
        )
        r.raise_for_status()
        return r.json().get("entries", [])

    def get_file_ids(self, record_id: str | None = None) -> dict:
        """get filename:key for files on the current draft

        InvenioRDM keys files by filename (there is no separate numeric file
        id), so this returns {filename: filename} — kept for parity with
        `ZenodoClient.get_file_ids`, whose callers index files by name.

        Args:
            record_id (str): record id, if None, uses self.record_id

        Returns:
            dict: {filename: key}
        """
        files = self.get_files(record_id)
        return {file["key"]: file["key"] for file in files}

    def delete_file(self, file_key: str):
        """delete a file from the current draft

        Args:
            file_key (str): the file's key (filename)
        """
        r = requests.delete(
            f"{self._endpoint}/records/{self.record_id}/draft/files/{file_key}",
            headers=self._headers(),
        )
        r.raise_for_status()

    def upload_file(self, file_path: Path | str) -> dict:
        """upload a file to the current draft

        Args:
            file_path (str | Path): path of the file to upload

        Returns:
            dict: the committed file's metadata

        Runs InvenioRDM's three-step upload: initialize the file entry, PUT
        the raw content, then commit.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(
                f"{file_path} does not exist. Please check you entered the correct path"
            )
        if self.record_id is None:
            raise ValueError(
                "Not pointing to a record. Call create_new_deposition() before uploading a file"
            )

        filename = file_path.name

        r = requests.post(
            f"{self._endpoint}/records/{self.record_id}/draft/files",
            headers=self._headers(),
            data=json.dumps([{"key": filename}]),
        )
        r.raise_for_status()

        with open(file_path, "rb") as fp:
            r = requests.put(
                f"{self._endpoint}/records/{self.record_id}/draft/files/{filename}/content",
                headers=self._headers(content_type="application/octet-stream"),
                data=fp,
            )
        r.raise_for_status()

        r = requests.post(
            f"{self._endpoint}/records/{self.record_id}/draft/files/{filename}/commit",
            headers=self._headers(),
        )
        r.raise_for_status()
        print(f"{file_path} successfully uploaded!")
        return r.json()

    # ---------------------------------------------
    # versioning / publish
    # ---------------------------------------------
    def make_new_version(self) -> dict:
        """create a new draft version of the current record

        Returns:
            dict: the new draft version JSON
        """
        if self.record_id is None:
            raise ValueError(
                "Not pointing to a record. Call create_new_deposition() first."
            )
        print(f"making new version of record id: {self.record_id}")
        r = requests.post(
            f"{self._endpoint}/records/{self.record_id}/versions",
            headers=self._headers(),
        )
        r.raise_for_status()
        data = r.json()
        self.record_id = data["id"]
        return data

    def publish(self) -> dict:
        """publish the current draft, minting/finalizing its DOI

        Returns:
            dict: the published record JSON
        """
        if self.record_id is None:
            raise ValueError(
                "Not pointing to a record. Call create_new_deposition() first."
            )
        r = requests.post(
            f"{self._endpoint}/records/{self.record_id}/draft/actions/publish",
            headers=self._headers(),
        )
        r.raise_for_status()
        return r.json()
