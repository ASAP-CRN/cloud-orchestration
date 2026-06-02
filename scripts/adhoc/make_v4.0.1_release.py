
# ASAP CRN 
# 25 March 2026
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

datasets = [
    'schapira-fecal-metagenome-human-baseline',
    'lee-mouse-liver-bulk-rnaseq-g2019s', 
    'lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet', 
    'lee-mouse-sn-rnaseq-midbrain-g2019s-hf-diet', 
    'liddle-human-colon-spatial-cosmx-rna-1000p',
    'liddle-human-colon-spatial-cosmx-protein-64p'
]
# schapira-fecal-metagenome-human-baseline, DOI: 10.5281/zenodo.18353680
# lee-mouse-liver-bulk-rnaseq-g2019s, DOI: 10.5281/zenodo.18273810
# lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet, DOI: 10.5281/zenodo.18273802
# lee-mouse-sn-rnaseq-midbrain-g2019s-hf-diet, DOI: 10.5281/zenodo.18273808
# liddle-human-colon-spatial-cosmx-rna-1000p, DOI: 10.5281/zenodo.17917788
# liddle-human-colon-spatial-cosmx-protein-64p, DOI: 10.5281/zenodo.17917771
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
    setup_DOI_info(ds_path, intake_doc, publication_date="2026-04-07")

# %%

