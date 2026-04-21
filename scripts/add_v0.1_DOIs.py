


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

v01_datasets = [
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
    ]
# %%
# v4.0.1
v1_datasets = [
    'schapira-fecal-metagenome-human-baseline',
    'lee-mouse-liver-bulk-rnaseq-g2019s', 
    'lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet', 
    'lee-mouse-sn-rnaseq-midbrain-g2019s-hf-diet', 
    'liddle-human-colon-spatial-cosmx-rna-1000p',
    'liddle-human-colon-spatial-cosmx-protein-64p',
    # v4.0.2
    'alessi-mefs-ms-p-vps35-d620n-wt',
    'alessi-mefs-ms-p-vps35-d620n-dmso-mli2',
    'sulzer-fecal-metagenome-fp-spf',
]

# # this one is already move from WIP since its a bump.
# v11_datasets = [
#     'alessi-invitro-ms-p-hek293-gtip'
# ]

datasets = list(set(v01_datasets) | set(v1_datasets))

# %%
for dataset in datasets:
    print(f"Processing {dataset}")

    src_path = source_path / dataset

    if 'indipd' in dataset:
        src_path = source_path / "indipd-ipsc" / dataset


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
    
    # force v0.1
    write_version("0.1", ds_path / "version")


# # %%

#     # copy version file
#     src_ver = src_path / "version"
#     if src_ver.exists():
#         shutil.copy2(src_ver, ds_path / "version")


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
##########################################################


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
    setup_DOI_info(ds_path, intake_doc, publication_date="2026-04-15")

# %%

