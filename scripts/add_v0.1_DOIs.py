


# %% [markdown]
# ASAP CRN Metadata validation
#
# adding WIP
# Andy Henrie
# DO NOT EXECUTE

#%%
import pandas as pd
from pathlib import Path
import os, sys
import shutil

from crn_utils.util import (
    read_CDE,
    NULL,
    prep_table,
    read_meta_table,
    read_CDE_asap_ids,
    export_meta_tables,
    load_tables,
    write_version,
)

from crn_utils.asap_ids import *
from crn_utils.validate import validate_table, ReportCollector, process_table

from crn_utils.bucket_util import gcloud_ls, gcloud_ls_long

from crn_utils.constants import *
from crn_utils.doi import *

%load_ext autoreload
%autoreload 2

# %%
root_path = Path(__file__).resolve().parents[2]
dest_path = root_path / "cloud-datasets/WIP"
source_path = root_path / "asap-crn-cloud-dataset-metadata/datasets/"

# %%

datasets = [
    'vangheluwe-ipsc-bulk-atacseq-astro-atp13a2lof',
    'vangheluwe-ipsc-bulk-rnaseq-astro-atp13a2lof',
    'vangheluwe-ipsc-bisulfseq-astro-atp13a2lof',
    'lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet',
    'lee-mouse-sn-rnaseq-midbrain-g2019s-hf-diet',
    'lee-mouse-liver-bulk-rnaseq-g2019s',
    'lee-mouse-ms-mb-plasma-2019s-hf-diet',
    'lee-mouse-ms-mb-liver-g2019s-hf-diet',
    'lee-mouse-ms-mb-striatum-g2019s-hf-diet',
    'lee-mouse-ms-mb-lung-g2019s-hf-diet',
    'lee-mouse-ms-mb-kidney-g2019s-hf-diet',
    'lee-mouse-ms-l-plasma-g2019s-hf-diet',
    'lee-mouse-ms-l-liver-g2019s-hf-diet',
    'lee-mouse-ms-l-striatum-g2019s-hf-diet',
    'lee-mouse-ms-l-lung-g2019s-hf-diet',
    'lee-mouse-ms-l-kidney-g2019s-hf-diet',
    'lee-mouse-ms-mb-plasma-g2019s-nuc-quant',
    'lee-mouse-ms-mb-striatum-g2019s-nuc-quant',
    'lee-mouse-ms-mb-midbrain-g2019s-nuc-quant',
    'alessi-mouse-ms-p-lung-vps35-d620n-wt',
    'alessi-mouse-ms-p-brain-vps35-d620n-wt',
    'alessi-mouse-ms-p-brain-vps35-d620n-dmso-mli2',
    'alessi-mouse-ms-p-lung-vps35-d620n-dmso-mli2',
    'scherzer-pmdbs-sn-rnaseq-midbrain-hybsel',
    'scherzer-pmdbs-lr-wgs',
    'scherzer-pmdbs-sn-multiome-midbrain',
    'decamilli-invitro-ms-p-hek293-apex-atg2-silac',
    "indipd-ipsc-bulk-rnaseq-kolf21j-wt",
    "indipd-ipsc-cageseq-kolf21j-wt",
    "indipd-ipsc-hicseq-kolf21j-wt",
    "indipd-ipsc-lr-wgs-kolf21j-wt",
    'alessi-mefs-ms-p-vps35-d620n-wt',
    'alessi-mefs-ms-p-vps35-d620n-dmso-mli2',
    'sulzer-fecal-metagenome-fp-spf',
    'alessi-invitro-ms-p-hek293-gtip',
    'schapira-fecal-metagenome-human-baseline',
    'lee-mouse-liver-bulk-rnaseq-g2019s', 
    'lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet', 
    'lee-mouse-sn-rnaseq-midbrain-g2019s-hf-diet', 
    'liddle-human-colon-spatial-cosmx-rna-1000p',
    'liddle-human-colon-spatial-cosmx-protein-64p'
    ]
# %%

for dataset in datasets:
    print(f"Processing {dataset}")

    src_path = source_path / dataset
    if not  src_path.exists():
        print(f"warning {src_path} not found")
        continue

    ds_path = dest_path / dataset

    # copy DOI and refs
    for subdir in ("DOI", "refs"):
        src_sub = src_path / subdir
        dst_sub = ds_path / subdir
        if src_sub.exists():
            shutil.copytree(src_sub, dst_sub, dirs_exist_ok=True)


    # if not ds_path.exists():
    #     print(f"    {ds_path} does not exist")
    #     ds_path.mkdir(parents=True, exist_ok=True)

    # # metadata_path = ds_path / "metadata"
    # # if not metadata_path.exists():
    # #     metadata_path.mkdir(parents=True, exist_ok=True)
    # doi_path = ds_path / "DOI"  
    # if not doi_path.exists():
    #     doi_path.mkdir(parents=True, exist_ok=True)
    # refs_path = ds_path / "refs"
    # if not refs_path.exists():
    #     refs_path.mkdir(parents=True, exist_ok=True)
    # # scripts_path = ds_path / "refs"
    # # if not scripts_path.exists():
    # #     scripts_path.mkdir(parents=True, exist_ok=True)


# %%


# %%

# import pypandoc
from xhtml2pdf import pisa
import docx
from markdown import markdown
import json

# %%
def _setup_DOI_info(
    ds_path: str | Path,
    doi_doc_path: str | Path,
    publication_date: None | str = None,
    cde_ver: str = "v3.3",
):
    ds_path = Path(ds_path)

    _ingest_DOI_doc(ds_path, doi_doc_path, publication_date=publication_date)
    _make_readme_file(ds_path)
    # depricate updating study table
    # update_study_table(ds_path, cde_ver=cde_ver)


def _ingest_DOI_doc(
    ds_path: str | Path,
    doi_doc_path: str | Path,
    publication_date: None | str = None,
):
    """
    read docx, extract the information, and save in os.path.join(dataset, DOI) subdirectory
    """
    ds_path = Path(ds_path)
    doi_doc_path = Path(doi_doc_path)
    long_dataset_name = ds_path.name

 
    # read the docx

    # should read this from ds_path/version
    # just read in as text
    with open(os.path.join(ds_path, "version"), "r") as f:
        ds_ver = f.read().strip()
    # ds_ver = "v2.0"

    # Load the document
    document = docx.Document(doi_doc_path)

    table_names = ["affiliations", "datasets", "projects", "extra1", "extra2"]
    for name, table in zip(table_names, document.tables):
        table_data = []
        for row in table.rows:
            row_data = [cell.text for cell in row.cells]
            table_data.append(row_data)
        # Assuming the first row is the header
        if name == "affiliations":
            fields = table_data[0]
            data = table_data[1:]
            # affiliations = pd.DataFrame(table_data[1:], columns=table_data[0])
            # if affiliations.shape[0] == 1:
            #     affiliations = affiliations.iloc[0, 0]

            print("made affiliation table")
        elif name == "datasets":
            dataset_title = (
                table_data[0][1].strip().replace("\n", " ").replace("\u2019", "'")
            )
            dataset_description = (
                table_data[1][1].strip().replace("\n", " ").replace("\u2019", "'")
            )
            print("got dataset title/description")
        elif name == "projects":
            project_title = (
                table_data[0][1].strip().replace("\n", " ").replace("\u2019", "'")
            )
            project_description = (
                table_data[1][1].strip().replace("\n", " ").replace("\u2019", "'")
            )
            if len(table_data) > 2:
                ASAP_team_name = (
                    table_data[2][1].strip()
                )
            else:
                ASAP_team_name = None
            if len(table_data) > 3:
                grant_ids = (
                    table_data[3][1].strip()
                )
            else:
                grant_ids = None
            
            print("got project title/description")

        else:
            # test if its the "Project Team" table
            if table_data[0][1] == "First name" and table_data[0][2] == "Last name" and table_data[0][3] == "Email":
                pj_team_table = table_data
            else:
                print(f"what is this extra thing?: {name}")
                print(table_data)


    # title
    # string	Title of deposition (automatically set from metadata). Defaults to empty string.
    title = dataset_title.strip().replace("Singel", "Single")

    # upload_type  string	Yes	Controlled vocabulary:
    upload_type = "dataset"

    # creators
    creators = []
    for indiv in data:
        name = f"{indiv[0].strip()}, {indiv[1].strip()}"  # , ".join(indiv[:2])
        # hack
        name = name.replace("* Corresponding author", "")
        affiliation = indiv[2].strip()
        oricid = indiv[3].strip()

        if name == ", ":  # this should block empty names
            continue

        to_append = {"name": name}

        # hacks
        affiliation = affiliation.replace(", United States.", ".")

        if affiliation == "":
            affiliation = None
        else:
            # if there are carriage split into a lis
            if "\n" in affiliation:
                affiliation = [
                    x.strip() for x in affiliation.split("\n") if x.strip() != ""
                ]
                if len(affiliation) == 1:
                    affiliation = affiliation[0]
                else:
                    affiliation = ",& ".join(affiliation)  # this is a hack"

            to_append["affiliation"] = affiliation

        if oricid == "":
            oricid = None
        else:
            to_append["orcid"] = oricid.lstrip("https://orcid.org/")
        creators.append(to_append)

        # creators.append({"name": name, "affiliation": affiliation, "orcid": oricid})

    # description
    dataset_description = dataset_description.strip()
    project_description = project_description.strip()
    # fix description to enable the numbered and bulletted lists...
    for i in range(10):
        rep_from = f" {i}. "
        rep_to = f"\n\n{i}. "
        project_description = project_description.strip().replace(rep_from, rep_to)
        dataset_description = dataset_description.strip().replace(rep_from, rep_to)
    project_description = project_description.strip().replace("* ", "\n\t* ")
    dataset_description = dataset_description.strip().replace("* ", "\n\t* ")

    description = f"""This Zenodo deposit contains a publicly available description of the Dataset:

**Title:** "{title}".

**Description:** {dataset_description}

--------------------------

> This dataset is made available to researchers via the ASAP CRN Cloud: [cloud.parkinsonsroadmap.org](https://cloud.parkinsonsroadmap.org). Instructions for how to request access can be found in the [User Manual](https://storage.googleapis.com/asap-public-assets/wayfinding/ASAP-CRN-Cloud-User-Manual.pdf).

> This research was funded by the Aligning Science Across Parkinson's Collaborative Research Network (ASAP CRN), through the Michael J. Fox Foundation for Parkinson's Research (MJFF).

> This Zenodo deposit was created by the ASAP CRN Cloud staff on behalf of the dataset authors. It provides a citable reference for a CRN Cloud Dataset

"""


   # fill details 

    ASAP_lab_name = ""

    # get details from the pj_team_table 
    field_name = [ tb[0] for tb in pj_team_table]

    PI_full_name = ""
    PI_email = ""
    submitter_name = ""
    submitter_email = ""
    cPI_full_name = []
    cPI_email = []
    for name,row in zip(field_name, pj_team_table):
        # skip if blank
        if len(row[1])<1:
            continue

        if name == "Principal Investigator":
            PI_full_name = f"{row[1]} {row[2]}"
            PI_email = f"{row[3]}"
        elif name == "Co-Principal Investigator":
            cPI_full_name.append(f"{row[1]} {row[2]}")
            cPI_email.append(f"{row[3]}")
        elif name == "Data Submitter":
            submitter_name = f"{row[1]} {row[2]}"
            submitter_email = f"{row[3]}"


    publication_DOI = ""

    print(grant_ids)
    team_name = ds_path.name.split('-')[0].capitalize() 
    



    # Convert to html for good formatting
    description = markdown(description)

    # ASAP
    communities = [{"identifier": "asaphub"}]
    # version
    version = ds_ver  # "2.0"?  also do "v1.0"
    # license
    license = {"id": "cc-by-4.0"}
    refrences = [
        "Aligning Science Across Parkinson's Collaborative Research Network Cloud, https://cloud.parkinsonsroadmap.org/collections, RRID:SCR_023923",
        f"Team {team_name}",
    ]

    # publication_date
    if publication_date is None:
        publication_date = pd.Timestamp.now().strftime(
            "%Y-%m-%d"
        )  # "2.0"?  also do "v1.0"

    metadata = {
        "title": title,
        "upload_type": upload_type,
        "description": description,
        "publication_date": publication_date,
        "version": version,
        # "access_right": "open",
        "creators": creators,
        "resource_type": "dataset",
        "communities": communities,
        "references": refrences,
        "license": license,
    }

    if not pd.isna(grant_ids):
        if "," in grant_ids:
            grant_ids = grant_ids.split(",")
        elif ";" in grant_ids:
            grant_ids = grant_ids.split(";")
        else:
            grant_ids = [grant_ids]

        grants = [{"id": f"10.13039/100018231::{grant_id}"} for grant_id in grant_ids]
        metadata["grants"] = grants

    else:
        print("Warning: No grant ids found")

    export_data = {"metadata": metadata}

    # dump json
    doi_path = os.path.join(ds_path, "DOI")

    if not os.path.exists(doi_path):
        os.makedirs(doi_path, exist_ok=True)

    with open(os.path.join(doi_path, f"{long_dataset_name}.json"), "w") as f:
        json.dump(export_data, f, indent=4)

    # also dump the table to make the documents and
    # ## save a simple table to update STUDY table
    project_dict = {
        "project_name": f"{project_title.strip()}",  # protect the parkionson's apostrophe
        "project_description": f"{project_description.strip()}",
        "dataset_title": f"{dataset_title.strip()}",
        "dataset_description": f"{dataset_description}",
        "creators": creators,
        "publication_date": publication_date,
        "version": version,
        "title": title,
        ### add the additional stuff from the study df
        "ASAP_lab_name": ASAP_lab_name,
        "PI_full_name": PI_full_name,
        "PI_email": PI_email,
        "coPI_full_name": cPI_full_name,
        "coPI_email": cPI_email,
        "submitter_name": submitter_name,
        "submitter_email": submitter_email,
        "publication_DOI": publication_DOI,
        "grant_ids": grant_ids,
        "team_name": team_name,
    }

    with open(os.path.join(doi_path, f"project.json"), "w") as f:
        json.dump(project_dict, f, indent=4)

    # df = pd.DataFrame(project_dict, index=[0])
    # df.to_csv(doi_path / f"{long_dataset_name}.csv", index=False)
    # write the files.



def _make_readme_file(ds_path: Path):
    """
    Make the stereotyped .md from the

    """
    # TODO:  add grant_ids

    # Aligning Science Across Parkinson's: 10.13039/100018231
    # grants = [{'id': f"10.13039/100018231::{grant_id}"}]

    long_dataset_name = ds_path.name

    team = long_dataset_name.split("-")[0]

    # load jsons
    doi_path = os.path.join(ds_path, "DOI")
    with open(os.path.join(doi_path, f"project.json"), "r") as f:
        data = json.load(f)
    # data = clean_json_read(doi_path / f"project.json")

    title = data.get("title")
    project_title = data.get("project_name")
    project_description = data.get("project_description")
    dataset_title = data.get("dataset_title")
    dataset_description = data.get("dataset_description")
    creators = data.get("creators")
    publication_date = data.get("publication_date")
    version = data.get("version")
    ASAP_lab_name = data.get("ASAP_lab_name")
    PI_full_name = data.get("PI_full_name")
    PI_email = data.get("PI_email")
    submitter_name = data.get("submitter_name")
    submitter_email = data.get("submitter_email")
    publication_DOI = data.get("publication_DOI")
    grant_ids = data.get("grant_ids")
    team_name = data.get("team_name")


    coPI_full_name = data.get("coPI_full_name")
    coPI_email = data.get("coPI_email")

    # # avoid unicodes that mess up latex
    # rep_from = "α"
    # rep_to = "alpha"
    # project_description = project_description.strip().replace(rep_from, rep_to)
    # dataset_description = dataset_description.strip().replace(rep_from, rep_to)
    # rep_from = "₂"
    # rep_to = "2"
    # project_description = project_description.strip().replace(rep_from, rep_to)
    # dataset_description = dataset_description.strip().replace(rep_from, rep_to)

    description = f"""This Zenodo deposit contains a publicly available description of the Dataset:

# "{title}".

## Dataset Description:
 
{dataset_description.strip()}

"""
    readme_content = description

    readme_content += f"\n**Authors:**\n\n"
    for creator in creators:
        readme_content += f"* {creator['name']}"
        if "orcid" in creator:
            # format as link
            readme_content += (
                f"; [ORCID:{creator['orcid'].split("/")[-1]}]({creator['orcid']})"
            )
        if "affiliation" in creator:
            # remove newlines from affiliation
            # # check if its a list
            # if isinstance(creator["affiliation"], list):
            #     affiliation = ",& ".join(creator["affiliation"])
            # else:
            #     affiliation = creator["affiliation"]
            affiliation = creator["affiliation"]
            readme_content += f"; {affiliation}"
        readme_content += "\n"

    readme_content += f"\n\n**ASAP Team:** {team_name}\n\n"
    readme_content += f"**Dataset Name:** {ds_path.name}, v{version}\n\n"

    readme_content += f"**Principal Investigator:** {PI_full_name} <{PI_email}>\n\n"

    if len(coPI_full_name) > 1:
        preamble = f"**Co-Principal Investigators:**"
    else:
        preamble = f"**Co-Principal Investigator:**"

    for coPI, coPI_email in zip(coPI_full_name, coPI_email):
        if coPI is not None:           
            readme_content += f"{preamble} {coPI} <{coPI_email}>, \n"
    
    readme_content += f"\n"

    readme_content += f"**Dataset Submitter:** {submitter_name} <{submitter_email}>\n\n"
    readme_content += f"**Publication DOI:** {publication_DOI}\n\n"
    readme_content += f"**Grant IDs:** {grant_ids}\n\n"
    readme_content += f"**ASAP Lab:** {ASAP_lab_name}\n\n"
    readme_content += f"**ASAP Project:** {project_title}\n\n"
    readme_content += f"**Project Description:** {project_description}\n\n"
    readme_content += f"**Submission Date:** {publication_date}\n\n"
    readme_content += f"__________________________________________\n"

    readme_content += f"""

> This dataset is made available to researchers via the ASAP CRN Cloud: [cloud.parkinsonsroadmap.org](https://cloud.parkinsonsroadmap.org). Instructions for how to request access can be found in the [User Manual](https://storage.googleapis.com/asap-public-assets/wayfinding/ASAP-CRN-Cloud-User-Manual.pdf).

> This research was funded by the Aligning Science Across Parkinson's Collaborative Research Network (ASAP CRN), through the Michael J. Fox Foundation for Parkinson's Research (MJFF).

> This Zenodo deposit was created by the ASAP CRN Cloud staff on behalf of the dataset authors. It provides a citable reference for a CRN Cloud Dataset

"""


    # strip \xa0
    readme_content = readme_content.replace("\xa0", " ")

    readme_content_HTML = markdown(readme_content)

    print(f"{long_dataset_name=}")
    print(f"{doi_path=}")
    with open(os.path.join(doi_path, f"{long_dataset_name}_README.md"), "w") as f:
        f.write(readme_content)

    make_pdf_file(
        readme_content_HTML, os.path.join(doi_path, f"{long_dataset_name}_README.pdf")
    )




# %%
# %%

for dataset in datasets:
    # find the ref name for ingest
    print(f"Processing {dataset}")
    ds_path = datasets_path / dataset
    intake_doc = ds_path / "refs/APEX-ATG2A MS Data Set.docx"

    # write version = 0.1
    write_version("0.1", ds_path / "version")
    # refs_path = ds_path / "refs"
    # ref_files = list(refs_path.glob("*.docx"))

    # if len(ref_files) == 1:
    #     intake_doc = ref_files[0]
    # else:
    #     print("Multiple ref files found.  Please select the correct one.")
    #     break

    print(intake_doc)

    # INGEST DOI DOCS
    _setup_DOI_info(ds_path, intake_doc, publication_date="2026-04-07")

# %%

