import json
import os
from pathlib import Path
import re
import requests
from datetime import datetime
import time
from dataclasses import dataclass, field

# from dotenv import load_dotenv

__all__ = [
    "ZenodoClient",
]

http_status_codes = """200	OK	Request succeeded. Response included. Usually sent for GET/PUT/PATCH requests.
201	Created	Request succeeded. Response included. Usually sent for POST requests.
202	Accepted	Request succeeded. Response included. Usually sent for POST requests, where background processing is needed to fulfill the request.
204	No Content	Request succeeded. No response included. Usually sent for DELETE requests.
400	Bad Request	Request failed. Error response included.
401	Unauthorized	Request failed, due to an invalid access token. Error response included.
403	Forbidden	Request failed, due to missing authorization (e.g. deleting an already submitted upload or missing scopes for your access token). Error response included.
404	Not Found	Request failed, due to the resource not being found. Error response included.
405	Method Not Allowed	Request failed, due to unsupported HTTP method. Error response included.
409	Conflict	Request failed, due to the current state of the resource (e.g. edit a deopsition which is not fully integrated). Error response included.
415	Unsupported Media Type	Request failed, due to missing or invalid request header Content-Type. Error response included.
429	Too Many Requests	Request failed, due to rate limiting. Error response included.
500	Internal Server Error	Request failed, due to an internal server error. Error response NOT included. Don’t worry, Zenodo admins have been notified and will be dealing with the problem ASAP.""".split(
    "\n"
)

http_stat_codes = {}
for line in http_status_codes:
    if line == "":
        continue
    code, name, desc = line.split("\t")
    http_stat_codes[code] = {"name": name, "desc": desc}

# [
#     "created",
#     "modified",
#     "id",
#     "conceptrecid",
#     "doi",
#     "conceptdoi",
#     "doi_url",
#     "metadata",
#     "title",
#     "links",
#     "record_id",
#     "owner",
#     "files",
#     "state",
#     "submitted",
# ]


class ZenodoClient(object):
    """Zenodo Client object

    Use this class to instantiate a zenodo object
    to interact with your Zenodo account

    """

    title: str | None = None
    bucket: str | None = None
    deposition_id: str | None = None
    sandbox: bool = False
    _token: str | None = None
    _all_depositions: list[dict] | None = None

    def __init__(
        self,
        title: str | None = None,
        bucket: str | None = None,
        deposition_id: str | None = None,
        sandbox: bool | None = None,
        token: str | None = None,
    ):
        """initialization method"""
        if sandbox:
            self._endpoint = "https://sandbox.zenodo.org/api"
        else:
            self._endpoint = "https://zenodo.org/api"

        self.title = title
        self.bucket = bucket
        self.deposition_id = deposition_id  # current deposition_id
        self.sandbox = sandbox
        self._token = self._load_from_env() if token is None else token
        # 'metadata/prereservation_doi/doi'

        # self._all_depositions = self._get_all_depositions()  # list[dict] =

    def __repr__(self):
        return f"zenodoapi('{self.title}','{self.bucket}','{self.deposition_id}')"

    def __str__(self):
        return f"{self.title} --- {self.deposition_id}"

    @staticmethod
    def _load_token(sandbox: bool = False):
        """reads the configuration file

        Configuration file should be ~/.zenodo_token

        Args:
            path (str): location of the file with ACCESS_TOKEN

        Returns:
            dict: dictionary with API ACCESS_TOKEN
        """

        if sandbox:
            target_key = "ACCESS_TOKEN-sandbox"
        else:
            target_key = "ACCESS_TOKEN"

        dotrc = os.environ.get(
            target_key, os.path.join(str(Path.home()), ".zenodo_token")
        )

        # NOTE: the if/else logic might not be accurate with the change from pathlib to os.path
        # check if the file exists.
        if os.path.exists(dotrc):
            #  read from the file
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

        # load_dotenv()
        # api_token = os.getenv("ZENODO_API_TOKEN")
        return api_token

    def _load_from_env(self):
        """reads the e token from env
        configuration file is ~/.zenodo_token
        Returns:
            str: ACCESS_TOKEN to connect to web3 storage
        """
        key = self._load_token(self.sandbox)
        return key

    def _get_depositions(self):
        """gets the current project deposition

        this provides details on the project, including metadata

        Returns:
            dict: dictionary containing project details
        """
        # get request, returns our response

        r = requests.get(
            f"{self._endpoint}/deposit/depositions", params={"access_token": self.token}
        )
        if r.ok:
            return r.json()
        else:
            return r.raise_for_status()

    def _get_all_depositions(self):
        """gets all the depositions

        this provides details on the project, including metadata

        Returns:
            dict: dictionary containing project details
        """
        depositions = self._get_depositions()

        deps = {}
        for deposition in depositions:
            doi = deposition["id"]
            deps[f"{doi}"] = deposition  # ZenodoDeposition.from_dict(deposition)
        return deps

    def get_deposition(self, dep_id: str | None = None):
        """gets the deposition based on deposition_id id

        this provides details on the project, including metadata

        Args:
            dep_id (str): project deposition ID, if None, uses the deposition_id of the class

        Returns:
            dict: dictionary containing project details
        """

        return self._get_deposition_by_id(dep_id)

    def _get_deposition_by_id(self, dep_id: str | None = None) -> dict:
        """gets the deposition based on deposition_id id

        this provides details on the project, including metadata

        Args:
            dep_id (str): project deposition ID, if None, uses the deposition_id of the class

        Returns:
            dict: dictionary containing project details
        """
        dep_id = dep_id if dep_id is not None else self.deposition_id
        if dep_id is None:
            dep = self._get_depositions()[0]
            dep_id = dep["id"]
            self.title = dep["title"]
            self.bucket = dep["links"]["bucket"]
            print(
                " ** no deposition id is set on the project ** choosing first deposition "
            )

        self.deposition_id = dep_id

        # get request, returns our response
        r = requests.get(
            f"{self._endpoint}/deposit/depositions/{dep_id}",
            params={"access_token": self.token},
        )

        # print(r.url)

        r.raise_for_status()
        dep_output = r.json()

        self.title = dep_output["title"]
        self.bucket = dep_output["links"]["bucket"]

        return dep_output

    def _get_deposition_files(self):
        """gets the file deposition

        ** not used, can safely be removed **

        Returns:
            dict: dictionary containing project details
        """
        # get request, returns our response
        if self.deposition_id is not None:
            r = requests.get(
                f"{self._endpoint}/deposit/depositions/{self.deposition_id}/files",
                params={"access_token": self.token},
            )
        else:
            print(" ** no deposition id is set on the project ** ")

        if r.ok:
            return r.json()
        else:
            return r.raise_for_status()

    def _get_bucket_by_title(self, title=None):
        """gets the bucket URL by project title

        This URL is what you upload files to

        Args:
            title (str): project title

        Returns:
            str: the bucket URL to upload files to
        """
        dic = self._get_depositions()
        dep_id = dic[title] if dic is not None else None

        # get request, returns our response, this the records metadata
        r = requests.get(
            f"{self._endpoint}/deposit/depositions/{dep_id}",
            params={"access_token": self.token},
        )

        if r.ok:
            return r.json()["links"]["bucket"]
        else:
            return r.raise_for_status()

    # def _get_bucket_by_id(self, dep_id=None):
    #     """gets the bucket URL by project deposition ID

    #     This URL is what you upload files to

    #     Args:
    #         dep_id (str): project deposition ID

    #     Returns:
    #         str: the bucket URL to upload files to
    #     """
    #     # get request, returns our response
    #     if dep_id is not None:
    #         r = requests.get(
    #             f"{self._endpoint}/deposit/depositions/{dep_id}",
    #             params={"access_token": self.token},
    #         )
    #     else:
    #         r = requests.get(
    #             f"{self._endpoint}/deposit/depositions/{self.deposition_id}",
    #             params={"access_token": self.token},
    #         )

    #     if r.ok:
    #         return r.json()["links"]["bucket"]
    #     else:
    #         return r.raise_for_status()

    def _is_doi(self, string=None):
        """test if string is of the form of a zenodo doi
        10.5281.zenodo.[0-9]+

        Args:
            string (strl): string to test. Defaults to None.

        Returns:
           bool: true is string is doi-like
        """
        import re

        pattern = re.compile("10.5281/zenodo.[0-9]+")
        return pattern.match(string)

    def _get_record_id_from_doi(self, doi: str | None = None):
        """return the record id for given doi

        Args:
            doi (string, optional): the zenodo doi. Defaults to None.

        Returns:
            str: the record id from the doi (just the last numbers)
        """
        return doi.split(".")[-1]

    def _get_latest_deposition(self):
        """return the latest record id for given record id

        Returns:
            str: the latest record id or 'None' if not found
        """
        try:
            record = self._get_deposition_by_id()["links"]["latest"].split("/")[-1]
        except:
            record = "None"
        return record

    def _delete_project(self, dep_id: str | None = None):
        """delete a project from repository by ID

        Args:
            dep_id (str): The project deposition ID
        """
        print("")
        # if input("are you sure you want to delete this project? (y/n)") == "y":
        # delete requests, we are deleting the resource at the specified URL
        dep_id = dep_id if dep_id is not None else self.deposition_id

        # could check to see if deposition["state"] == "done" and warn user that this is a published record...
        #  but it fails either way.
        r = requests.delete(
            f"{self._endpoint}/deposit/depositions/{dep_id}",
            params={"access_token": self.token},
        )
        # response status
        print(r.status_code)

        # reset class variables to None
        self.title = None
        self.bucket = None
        self.deposition_id = None

    def _check_parent_doi(self, dep_id: str, project_obj: dict):
        if project_obj["id"] == int(dep_id):
            return True
        concept_doi = project_obj.get("conceptdoi", None)
        if concept_doi != None:
            return int(dep_id) == int(concept_doi.split(".")[-1])
        return False

    # ---------------------------------------------
    # user facing functions/properties
    # ---------------------------------------------
    # ---------------------------------------------
    # properties
    # ---------------------------------------------

    @property
    def token(self):
        return self._token

    # @property
    # def bucket(self):
    #     if self.bucket is None and self.deposition_id is not None:
    #         self.bucket = self._get_bucket_by_id(self.deposition_id)
    #     return self._bucket

    @property
    def all_depositions(self):
        return self._all_depositions

    @property
    def deposition(self) -> dict:
        return self._get_deposition_by_id()

    def delete_deposition(self, dep_id: str):
        """delete a deposition by ID

        Args:
            dep_id (str): The deposition ID
        """
        r = requests.post(
            f"{self._endpoint}/deposit/depositions/{dep_id}/actions/discard",
            params={"access_token": self.token},
        )

        if r.ok:
            print(f"Deposition {dep_id} deleted")
            return r
        else:
            print("Oh no! something went wrong")
            return r.raise_for_status()

    def update_depositions(self):
        self._all_depositions = self._get_all_depositions()

    def list_files(self, dep_id: str | None = None):
        """list files in current deposition

        Args:
            dep_id (str): The project deposition ID

        prints filenames to screen
        """
        dep = self._get_deposition_by_id(dep_id)
        if dep is not None:
            print("Files")
            print("------------------------")
            for file in dep["files"]:
                print(file["filename"])
        else:
            print(
                " ** the object is not pointing to a project. Use either .set_deposition_id() or .create_deposition() before listing files ** "
            )
            # except UserWarning:
            # warnings.warn("The object is not pointing to a project. Either create a project or explicity set the project'", UserWarning)

    def get_files(self, dep_id: str | None = None) -> list[dict]:
        """get files in current deposition

        Args:
            dep_id (str): The project deposition ID

        returns list of filenames
        """
        if dep_id is not None:
            self.deposition_id = dep_id
        else:
            print(" * careful... you might not have set the deposition id")
        dep = self.deposition
        files = dep["files"]
        return files

    def get_file_ids(self, dep_id: str | None = None):
        """get file:id in current deposition

        Args:
            dep_id (str): The project deposition ID

        returns dict of filenames:id
        """
        files = self.get_files(dep_id)
        dep = self.deposition
        
        if files is not None:

            return {file["filename"]: file["id"] for file in dep["files"]}
        else:
            print(
                " ** the object is not pointing to a project. Use either .set_deposition_id() or .create_deposition() before listing files ** "
            )
            return {}

    def create_new_deposition(
        self,
        # metadata: dict,
    ) -> dict:
        """Creates a new deposition

        After a deposition is created the zenodopy object will point to the deposition

        title is required. If upload_type or description
        are not specified, then default values will be used

        Args:
            title (str): new title of project
            metadata_json (str): path to json file with metadata
        """

        # get request, returns our response
        r = requests.post(
            f"{self._endpoint}/deposit/depositions",
            params={"access_token": self.token},
            data=json.dumps({}),
            headers={"Content-Type": "application/json"},
        )

        r.raise_for_status()
        self.deposition_id = r.json()["id"]
        self.bucket = r.json()["links"]["bucket"]
        return r.json()

    # this is pretty useless....
    def set_deposition_id(self, dep_id):
        """set the project by id"""

        self.deposition_id = dep_id
        dep = self.deposition

        if dep is not None:
            self.title = dep["title"]
            self.bucket = dep["links"]["bucket"]
            

        # if depositions is not None:
        #     for d in depositions:
        #         if d["id"] == int(dep_id):
        #             self.title = d["title"]
        #             self.bucket = self._get_bucket_by_id(d["id"])
        #             self.deposition_id = f"{d["id"]}"
        #             return
        #     else:
        #         print(
        #             f" ** Deposition ID: {dep_id} does not exist in your depositions  ** "
        #         )

    def set_deposition_dataset_id(self, dataset_id: str | None = None):
        """set the deposition to the root of the generic dataset_id (conceptrecid)"""
        depositions = self._get_depositions()

        if depositions is not None:
            project_list = [
                d
                for d in depositions
                if self._check_parent_doi(dep_id=dataset_id, project_obj=d)
            ]
            if len(project_list) > 0:
                self.title = project_list[0]["title"]
                self.bucket = project_list[0]["links"]["bucket"]
                self.deposition_id = project_list[0]["id"]

        else:
            print(
                f" ** Deposition ID: {dep_id} does not exist in your depositions  ** "
            )

    def unlock_deposition(self, dep_id: str | None = None):
        """unlock a deposition

        Args:
            dep_id (str): The project deposition ID
        """
        dep_id = dep_id if dep_id is not None else self.deposition_id

        # url_action = self._get_deposition_by_id()["links"]["edit"]
        r = requests.post(
            f"{self._endpoint}/deposit/depositions/{dep_id}/actions/edit",
            params={"access_token": self.token},
        )
        if r.ok:
            print("::::::::Deposition unlocked")
            return r.json()
        else:
            # 400 Bad Request: Deposition state does not allow for editing (e.g. depositions in state inprogress).
            # 409 Conflict: Deposition is in the process of being integrated, please wait 5 minutes before trying again.
            return r.raise_for_status()

    def change_metadata(self, metadata: dict) -> dict:
        """
        Change project's metadata.

        Args:
            metadata (ZenodoMetadata): The metadata to update.

        Returns:
            dict: Dictionary with the updated metadata if the request is successful.
                  Raises an error if the request fails.

        This function updates the project's metadata on Zenodo.
        The metadata is sent as a JSON payload to the Zenodo API endpoint using a PUT request.
        If the request is successful, it returns the updated metadata as a dictionary.
        If the request fails, it raises an error with the status of the failed request.
        """

        if self.deposition_id is None:
            raise ValueError(
                "Not pointing to a project. Call .set_deposition_id() or .create_new_deposition() first."
            )

        data_payload = {"metadata": metadata}
        r = requests.put(
            f"{self._endpoint}/deposit/depositions/{self.deposition_id}",
            params={"access_token": self.token},
            data=json.dumps(data_payload),
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        return r.json()

    def delete_file(self, file_id: str):
        """delete a file from the deposition

        Args:
            file_name (str): The file name to delete
        """

        # delete requests, we are deleting the resource at the specified URL
        r = requests.delete(
            f"{self._endpoint}/deposit/depositions/{self.deposition_id}/files/{file_id}",
            params={"access_token": self.token},
        )

        # response status
        if r.ok:
            print("File deleted")
            return r.raise_for_status()
        else:
            return r.raise_for_status()

    def upload_file(self, file_path: Path | str | None = None, publish=False):
        """upload a file to a project

        Args:
            file_path (str): name of the file to upload
            publish (bool): whether implemente publish action or not
        """
        if file_path is None:
            print("You need to supply a path")
            return
        elif isinstance(file_path, str):
            file_path = Path(file_path)

        if not os.path.exists(file_path):
            print(
                f"{file_path} does not exist. Please check you entered the correct path"
            )

        if self.bucket is None:
            print(
                "You need to create a project with zenodo.create_deposition() "
                "or set a project zenodo.set_deposition_id) before uploading a file"
            )
            return {}
        else:
            bucket_link = self.bucket
            with open(file_path, "rb") as fp:
                # text after last '/' is the filename
                filename = file_path.name
                r = requests.put(
                    f"{bucket_link}/{filename}",
                    params={"access_token": self.token},
                    data=fp,
                )
                if r.ok:
                    response = r.json()
                    print(f"{file_path} successfully uploaded!")
                else:
                    print("Oh no! something went wrong")
                    response = r.raise_for_status()
            return response

    def make_new_version(self) -> dict:
        """update an existing record for a new version"""
        url_action = self._get_deposition_by_id()["links"]["newversion"]
        # print(url_action)
        print(f"making new version of deposition id: {self.deposition_id}")
        time.sleep(2)
        r = requests.post(url_action, params={"access_token": self.token})
        r.raise_for_status()

        # adding this to let new id propagate in the backend
        time.sleep(5)
        return r.json()

    def publish(self) -> dict:
        """publish a record"""
        dep_id = self.deposition_id
        url_action = self._get_deposition_by_id(dep_id)["links"]["publish"]
        r = requests.post(url_action, params={"access_token": self.token})
        r.raise_for_status()
        return r.json()

    def get_urls_from_doi(self, doi: str | None = None):
        """the files urls for the given doi

        Args:
            doi (str): the doi you want the urls from. Defaults to None.

        Returns:
            list: a list of the files urls for the given doi
        """
        if self._is_doi(doi):
            record_id = self._get_record_id_from_doi(doi)
        else:
            print(f"{doi} must be of the form: 10.5281/zenodo.[0-9]+")

        # get request (do not need to provide access token since public
        r = requests.get(
            f"https://zenodo.org/api/records/{record_id}"
        )  # params={'access_token': ACCESS_TOKEN})
        return [f["links"]["self"] for f in r.json()["files"]]
