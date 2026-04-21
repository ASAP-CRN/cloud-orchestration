


# %% [markdown]
# ASAP CRN Metadata validation
#
#
# 21 April 2026
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

# v1.0 datasets, v4.3 cde
datasets = [
    'lee-mouse-ms-p-lung-g2019s-hf-diet',
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
]

# cde v3.3
bump_datasets = [
'cohort-pmdbs-bulk-rnaseq',# v1.3
'cohort-pmdbs-sc-rnaseq', # v3.2.0
'team-hafler-pmdbs-sn-rnaseq-pfc',# v1.1
'team-hardy-pmdbs-bulk-rnaseq', # v1.1
'team-hardy-pmdbs-sn-rnaseq',# v1.1
'team-jakobsson-pmdbs-sn-rnaseq',# v2.1
'team-lee-pmdbs-bulk-rnaseq-mfg',# v1.1
'team-lee-pmdbs-sn-rnaseq', # v1.1
'team-scherzer-pmdbs-genetics',# v1.1
'team-scherzer-pmdbs-sn-rnaseq-mtg',# v1.2
'team-scherzer-pmdbs-sn-rnaseq-mtg-hybsel',# v1.2
'team-scherzer-pmdbs-spatial-visium-mtg',# v1.1
'team-sulzer-pmdbs-sn-rnaseq',# v1.1 
'team-wood-pmdbs-bulk-rnaseq', # v1.1 
]



datasets = [
'vangheluwe-ipsc-bulk-atacseq-astro-atp13a2lof',
'vangheluwe-ipsc-bulk-rnaseq-astro-atp13a2lof',
'vangheluwe-ipsc-bisulfseq-astro-atp13a2lof',


    ]


datasets = [
'lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet',
'lee-mouse-sn-rnaseq-midbrain-g2019s-hf-diet',
'lee-mouse-liver-bulk-rnaseq-g2019s',
'lee-mouse-ms-p-lung-g2019s-hf-diet',
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
    ]

'scherzer-pmdbs-sn-rnaseq-midbrain-hybsel',
'scherzer-pmdbs-lr-wgs',
'scherzer-pmdbs-sn-multiome-midbrain',
'decamilli-invitro-ms-p-hek293-apex-atg2-silac',


datasets = [
"indipd-ipsc-bulk-rnaseq-kolf21j-wt",
"indipd-ipsc-cageseq-kolf21j-wt",
"indipd-ipsc-hicseq-kolf21j-wt",
"indipd-ipsc-lr-wgs-kolf21j-wt",
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

