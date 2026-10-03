
#%%
import pandas as pd
from pathlib import Path
import os, sys
import shutil
import asap_orchestrator as ao

# %%
root_path = Path(__file__).resolve().parents[3]
source_path_wip = root_path / "cloud-datasets/WIP"
source_path_published = root_path / "cloud-datasets/datasets"

#%%

old_datasets = [
    "biederer-pmdbs-spatial-geomx-lamda",
    "biederer-mouse-spatial-geomx-lamda"
]


new_datasets = [   
    "desjardins-mouse-bulk-rnaseq-striatum-pink1",
    "desjardins-mouse-bulk-rnaseq-nigra-pink1",
    # "desjardins-human-pbmc-multimodal-sc-rna-tcr",
    "desjardins-mouse-sc-rnaseq-colon-immune-lrrk2",
    "desjardins-ipsc-sc-rnaseq-myeloid-pink1",
    "desjardins-mouse-sc-rnaseq-colon-immune-pink1",
    "rio-hesc-wgs-iscore-pd-genotyping-and-snps",
    "rio-hesc-spheroids-sc-rnaseq-irradiated",
    "rio-hesc-sc-rnaseq-irradiated",
    "rio-hesc-sc-rnaseq-wt-dopaminergic",
    "rio-hesc-targeted-ngs-mutant-zygosity",
]

do_nothing_datasets = [
    "alessi-mouse-sn-rnaseq-dorsal-striatum-g2019s",
    "lee-mouse-liver-bulk-rnaseq-g2019s",
    "lee-mouse-bulk-rnaseq-striatum-g2019s-hf-diet",
    # "lee-mouse-sn-rnaseq-midbrain-g2019s-hf-diet",
    "schlossmacher-mouse-sn-rnaseq-osn-aav-transd",
    # "voet-pmdbs-sn-rnaseq"
]

updated_datasets = [
    "cragg-mouse-sn-rnaseq-striatum", # v1.0 -> v2.0 fixed metadata AND replaced corrupt fastqs
    "voet-pmdbs-sn-multimodal"  # new samples v1.0 -> v2.0
]

all_datasets = old_datasets + new_datasets + do_nothing_datasets + updated_datasets


# # %%

for dataset in all_datasets:
    # print(dataset)
    # check if the dataset is in wip
    if (source_path_wip / dataset).exists():
        print(f"we only have a WIP DOI for {dataset}, copy from WIP to dest")
        src_path = source_path_wip / dataset
        dest_path = source_path_published / dataset

        if not dest_path.exists():
            # check if we have a dataset path in the dest
            print(f"Copy {src_path} to {dest_path}")
            # move path to dest
            shutil.move(src_path, source_path_published)
            # shutil.copytree(src_path/"DOI", dest_path/"DOI", dirs_exist_ok=True)
        
        else:
            print(f"Destination stub {dest_path} exists")




# %%

publish_datasets = {
    "cragg-mouse-sn-rnaseq-striatum" : "22784504",
    "voet-pmdbs-sn-multimodal" : "22785836",
}
 

zenodo = ao.setup_zenodo()


for dataset, doi_id in publish_datasets.items():
    ds_path = source_path_published / dataset
    # # read version file
    # version_file = src_path / "version"
    # with open(version_file, "r") as f:
    #     version = f.read().strip()

    curr_doi_id = ao.get_doi_from_dataset(ds_path, version=True)


    print(f"release: {dataset}: {curr_doi_id} -> {doi_id}")
    zenodo.set_deposition_id(doi_id)
    deposition = zenodo.deposition
    # deposition = ao.publish_doi(zenodo, doi_id)
    
    # archive deposition
    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)



# %%
publish_datasets = {
    "biederer-pmdbs-spatial-geomx-lamda" : "22732220",
    "biederer-mouse-spatial-geomx-lamda" : "22732174",
    "desjardins-ipsc-sc-rnaseq-myeloid-pink1" : "22728641",
    "desjardins-mouse-bulk-rnaseq-nigra-pink1" : "22728636",
    "desjardins-mouse-bulk-rnaseq-striatum-pink1" :"22728589",
    # "desjardins-human-pbmc-multimodal-sc-rna-tcr",
    "desjardins-mouse-sc-rnaseq-colon-immune-lrrk2" : "22728637",
    "desjardins-mouse-sc-rnaseq-colon-immune-pink1" : "22730904",
    "rio-hesc-sc-rnaseq-irradiated" : "22732608", # might be v0.1...
    "rio-hesc-sc-rnaseq-wt-dopaminergic" : "22732751",
    "rio-hesc-spheroids-sc-rnaseq-irradiated" : "22732608",
    "rio-hesc-targeted-ngs-mutant-zygosity" : "22732760",
    "rio-hesc-wgs-iscore-pd-genotyping-and-snps" : "22759832",
}
 



zenodo = ao.setup_zenodo()


for dataset, doi_id in publish_datasets.items():
    ds_path = source_path_published / dataset
    # # read version file
    # version_file = src_path / "version"
    # with open(version_file, "r") as f:
    #     version = f.read().strip()

    curr_doi_id = ao.get_doi_from_dataset(ds_path, version=True)


    print(f"release: {dataset}: {curr_doi_id} -> {doi_id}")
    zenodo.set_deposition_id(doi_id)
    deposition = zenodo.deposition
    deposition = ao.publish_doi(zenodo, doi_id)
    
    # archive deposition
    ao.archive_deposition_local(ds_path, "final-deposition", deposition)


# %%


