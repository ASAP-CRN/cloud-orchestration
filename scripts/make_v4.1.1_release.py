


# %% [markdown]
# ASAP CRN Metadata validation
#
#
# 21 May 2026
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
root_path = Path(__file__).resolve().parents[3]
datasets_path = root_path / "datasets"

# %%

# v1.0 datasets, v4.4 cde
datasets = [
    "voet-pmdbs-sn-multimodal",
    "voet-pmdbs-sn-atacseq-scalebio-hydrop",
    "voet-pmdbs-sn-atacseq-scalebio-10x",
    "voet-pmdbs-sn-atacseq-hydrop",
    "voet-pmdbs-sn-atacseq-10x",
    "voet-pmdbs-sn-rnaseq-parsebio",
    "voet-pmdbs-sn-rnaseq",
    "scherzer-pmdbs-sn-rnaseq-midbrain-hybsel",
    "scherzer-pmdbs-lr-wgs"
    ]



# %%

for dataset in datasets:
    print(f"Processing {dataset}")
    ds_path = datasets_path / dataset
    if not ds_path.exists():
        print(f"    {ds_path} does not exist")
        ds_path.mkdir(parents=True, exist_ok=True)

    # metadata_path = ds_path / "metadata"
    # if not metadata_path.exists():
    #     metadata_path.mkdir(parents=True, exist_ok=True)
    doi_path = ds_path / "DOI"  
    if not doi_path.exists():
        doi_path.mkdir(parents=True, exist_ok=True)
    refs_path = ds_path / "refs"
    if not refs_path.exists():
        refs_path.mkdir(parents=True, exist_ok=True)
    scripts_path = ds_path / "refs"
    if not scripts_path.exists():
        scripts_path.mkdir(parents=True, exist_ok=True)


# %%
# %%



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

