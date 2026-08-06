
#%%
import pandas as pd
from pathlib import Path
import os, sys
import shutil

# %%
root_path = Path(__file__).resolve().parents[3]
source_path_wip = root_path / "cloud-datasets/WIP"
soruce_path_published = root_path / "cloud-datasets/datasets"
dest_path = root_path / "asap-crn-cloud-dataset-metadata/new_dois/"

#%%

old_datasets = [
    "biederer-pmdbs-spatial-geomx-lamda",
    "biederer-mouse-spatial-geomx-lamda"
]


new_datasets = [   
    "desjardins-mouse-bulk-rnaseq-striatum-pink1",
    "desjardins-mouse-bulk-rnaseq-nigra-pink1",
    "desjardins-human-pbmc-multimodal-sc-rna-tcr",
    "desjardins-mouse-sc-rnaseq-colon-immune-lrrk2",
    "desjardins-ipsc-sc-rnaseq-myeloid-pink1",
    "desjardins-mouse-sc-rnaseq-colon-immune-pink1",
    "rio-hesc-spheroids-sc-rnaseq-irradiated",
    "rio-hesc-sc-rnaseq-irradiated",
    "rio-hesc-sc-rnaseq-wt-dopaminergic",
    "rio-hesc-targeted-ngs-mutant-zygosity",
    "rio-hesc-wgs-iscore-pd-genotyping-and-snps"
]


do_nothing_datasets = [
    "alessi-mouse-sn-rnaseq-dorsal-striatum-g2019s",
    "lee-mouse-liver-bulk-rnaseq-g2019s",
    "lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet",
    # "lee-mouse-sn-rnaseq-midbrain-g2019s-hf-diet",
    "schlossmacher-mouse-sn-rnaseq-osn-aav-transd",
    "voet-pmdbs-sn-rnaseq"
]

updated_datasets = [
    "cragg-mouse-sn-rnaseq-striatum",
    "voet-pmdbs-sn-multimodal"
]

all_datasets = old_datasets + new_datasets + do_nothing_datasets + updated_datasets


# %%


for dataset in all_datasets:
    # print(dataset)
    # check if the dataset is in wip
    if (source_path_wip / dataset).exists():
        print(f"we only have a WIP DOI (v0.1) for {dataset}, copy from WIP to dest")
        src_path = source_path_wip / dataset
    # check if the dataset is already in published, if it is in published
    elif (soruce_path_published / dataset).exists():
        print(f"we already have a DOI for {dataset}, copy from published to dest")
        src_path = soruce_path_published / dataset
    else:
        print(f"Dataset {dataset} not found in WIP or published. Skipping.")
        continue 


    # check if we have a dataset path in the dest
    if (dest_path / dataset).exists():
        print(f"Destination stub  exists")
        # check if DOI is there
        if (dest_path / dataset / "DOI").exists():
            # if so we will need to check if the dataset
            print(f" {dataset} already has a DOI path.")
   
    dst_path = dest_path / dataset 
    # create the dataset path if it doesn't exist
    dst_path.mkdir(parents=True, exist_ok=True)
    print(f"Copy {src_path} to {dst_path}")

    shutil.copytree(src_path/"DOI", dst_path/"DOI", dirs_exist_ok=True)

    if dataset in updated_datasets:
        print(f"WARNING {dataset} is scheduled for version bump.")
        



# %%
# TODO: still working on the Biederer datasets `old_datasets` which are in WIP and need to be copied to the published datasets.
#.   still need to fix a bug in the document ingests
