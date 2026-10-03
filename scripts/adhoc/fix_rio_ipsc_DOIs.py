
# # ASAP CRN — New WIP Dataset Acceptance Template
#


#
# %%
# %% Setup
import json
from pathlib import Path
import asap_orchestrator as ao
from asap_orchestrator.doi import bump_doi_version, make_readme_file

import shutil

# TODO: confirm the root path resolves correctly for your environment

%load_ext autoreload
%autoreload 2
# 

root_path = Path(__file__).resolve().parents[3]
datasets_repo_path = root_path / "cloud-datasets"

# %% 

# rio-hesc-targeted-ngs-mutant-zygosity
# v0.1 DOI: 10.5281/zenodo.19600813
# draft record: https://zenodo.org/uploads/22732760
# rio-hesc-spheroids-sc-rnaseq-irradiated
# v0.1 DOI: 10.5281/zenodo.19600804
# draft record: https://zenodo.org/uploads/22732608
# rio-hesc-sc-rnaseq-irradiated 
# v0.1 DOI: 10.5281/zenodo.19600808
# draft record: https://zenodo.org/uploads/22732742
# rio-hesc-sc-rnaseq-wt-dopaminergic 
# v0.1: 10.5281/zenodo.19600811
# draft record: https://zenodo.org/uploads/22732751

# 
fix_datasets = [
    "rio-hesc-spheroids-sc-rnaseq-irradiated",
    "rio-hesc-sc-rnaseq-irradiated",
    "rio-hesc-sc-rnaseq-wt-dopaminergic",
    "rio-hesc-targeted-ngs-mutant-zygosity",
    "rio-hesc-wgs-iscore-pd-genotyping-and-snps" # v1,0 - 22759832 - OK
]


# %%

# make v1.0 DOI as draft

# mitigations is to update the current v0.1 DOIs to v0.0-incorrect, then make new
# v0.1 DOIs by hand...

# steps,
# archive "deposition" as v0.0-incorrect
# update version to v0.0
# make new v0.1
# upload new v0.1 pdf
# publish

# make v1.0 DOI as draft

# %%

PUBLICATION_DATE = "2026-09-30"  
CDE_VERSION = "v4.5"   
RELEASE_VERSION = "v5.1.0"

zenodo = ao.setup_zenodo()

# %%
# hack for "beta-deposition"

# dois = [
# ]

# for ds, current_doi_id in zip(fix_datasets,dois):
#     ds_path = datasets_repo_path / "WIP" / ds
#     # current_doi_id = ao.get_doi_from_dataset(ds_path, version=True)
#     deposition = zenodo.get_deposition(current_doi_id)

#     # check that the current version is as expected before bumping
#     metadata = deposition.get("metadata")
#     print(f"Current version for {ds}: {current_version}, metadata version: {metadata.get('version')}")

#     ao.archive_deposition_local(ds_path, "beta-deposition", deposition)
#     # ao.archive_deposition_local(ds_path, f"deposition_v{current_version}", deposition)


# %%
for ds in fix_datasets:
    ds_path = datasets_repo_path / "datasets" / ds

    readme_pdf = ds_path / "DOI" / f"{ds}_README.pdf"
    og_data_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    print(f"dataset: {ds} ||| DOI: 10.5281/zenodo.{og_data_doi_id}")




    docs = ds_path / "refs"
    for doc in docs.iterdir():
        if doc.suffix == ".docx":
            ref_doc = doc
            break
    else:
        print(f"WARNING: no .docx file found in {docs}")
        continue


    zenodo.set_deposition_id(og_data_doi_id)
    # deposition = ao.bump_doi_version(zenodo, og_data_doi_id)
    deposition = zenodo.deposition
    metadata = deposition.get("metadata")
    new_doi_id = f"{deposition['id']}"

    print(f"NEW:  {ds}: ||| {new_doi_id} {og_data_doi_id}")
    readme_pdf = ds_path / "DOI" / f"{ds}_README.pdf"

    # initialize the v1.0 DOI
    # update v1.0
    metadata['version'] = '0.1'

    communities = [{'identifier': 'asaphub'}, {'identifier': 'crn-cloud'}]
    metadata['communities'] = communities

    deposition = ao.update_doi_metadata(zenodo, new_doi_id, metadata)


    ao.finalize_DOI(ds_path, deposition, prerelease=True)
    # archive deposition
    ao.archive_deposition_local(ds_path, "beta-deposition", deposition)

    # do i need to publish?

    # bump to v1.0
    ao.write_version("1.0", ds_path / "version")
    # re-ingest docx to update the Zenodo metadata for v1.0
    deposition = ao.bump_doi_version(zenodo, og_data_doi_id)
    # 22759832

    ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE, force=True)

    zenodo.set_deposition_id(og_data_doi_id)
    # deposition = ao.bump_doi_version(zenodo, og_data_doi_id)
    new_doi_id = f"{deposition['id']}"

    print(f"NEW:  {ds}: ||| {new_doi_id} {og_data_doi_id}")
    readme_pdf = ds_path / "DOI" / f"{ds}_README.pdf"

    # initialize the v1.0 DOI
    # update v1.0
    metadata['version'] = 'v1.0'
    deposition = ao.update_doi_metadata(zenodo, new_doi_id, metadata)

    print(f"Updated DOI for {ds}: {new_doi_id}")

    if readme_pdf.exists():
        # not sure why this fails... seems that the REST API has changed behavior
        deposition = ao.replace_anchor_file_in_doi(zenodo, ds_path, new_doi_id, readme_pdf)
        print(f"Uploaded README: {ds}")
    else:
        print(f"WARNING: README PDF not found for {ds_def}")


    ao.finalize_DOI(ds_path, deposition, prerelease=True)
    # archive deposition
    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)




#%%


fix_datasets = [
    # "desjardins-mouse-bulk-rnaseq-striatum-pink1",
    # "desjardins-mouse-bulk-rnaseq-nigra-pink1",
    # "desjardins-mouse-sc-rnaseq-colon-immune-lrrk2",
    # "desjardins-ipsc-sc-rnaseq-myeloid-pink1",
    "desjardins-mouse-sc-rnaseq-colon-immune-pink1",
    # "desjardins-human-pbmc-multimodal-sc-rna-tcr",
]
