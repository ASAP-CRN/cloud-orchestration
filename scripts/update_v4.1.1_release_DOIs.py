
# # ASAP CRN — fix errors in Voet v4.1.1 release DOIs
#
# %% Setup
from pathlib import Path
import subprocess
import asap_orchestrator as ao
from asap_orchestrator.doi import bump_doi_version
from asap_orchestrator.doi import setup_DOI_info_v1 as ao_setup_DOI_info_v1
import shutil, json
# TODO: confirm the root path resolves correctly for your environment

%load_ext autoreload
%autoreload 2
# 

root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"
metadata_repo_path = root_path / "asap-crn-cloud-dataset-metadata"

# %% [Step 5a] Release parameters
# TODO: set the publication date and CDE version for this acceptance tranche
PUBLICATION_DATE = "2026-05-31"   # e.g. "2026-05-01"
CDE_VERSION = "v4.4"              # e.g. "v3.3"


# %% [Step 5b].  Tranche of v1.0 datasets

# v1.0 datasets, v4.3 cde
datasets = [
    "voet-pmdbs-sn-atacseq-scalebio-hydrop", # 20076952
    "voet-pmdbs-sn-atacseq-10x", # 20077637
    "voet-pmdbs-sn-atacseq-hydrop",
    "voet-pmdbs-sn-atacseq-scalebio-10x",
    "voet-pmdbs-sn-multimodal",
    "voet-pmdbs-sn-rnaseq",
    "voet-pmdbs-sn-rnaseq-parsebio",
    # "scherzer-pmdbs-sn-rnaseq-midbrain-hybsel",
    # "scherzer-pmdbs-lr-wgs"
    ]


# %%

# # %% [Step 3] Re-Ingest DOI reference documents
# Place the team-supplied .docx reference file in <name>/refs/ first, then
# run this cell to populate DOI/<name>.json, project.json, and the README.
#
# Update the filename in `ref_doc` for each dataset as needed.
# %%

zenodo = ao.setup_zenodo()

# %%


for ds in datasets:
    ds_path = datasets_repo_path / "datasets" / ds
    # TODO: update the filename to match the actual reference document
    
    # confirm we have v1.0
    # read version
    current_version = (ds_path / "version").read_text().strip()


    # find the refs.docx
    ref_path = ds_path / "refs"
    if len(list(ref_path.glob("*.docx"))) > 1:
        ref_doc = list(ref_path.glob("*.docx"))
        # ref_doc = [f for f in ref_doc if "depricated" not in f.name.lower()]
        ref_doc = min(ref_doc)

    v1_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    if not v1_doi_id:
        print(f"WARNING: no DOI found for {ds} at v1.0 after ingestion")
        continue
    else:        
        print(f"Found DOI for {ds} at v1.0: {v1_doi_id}")
    ao_setup_DOI_info_v1(ds_path, ref_doc, publication_date=PUBLICATION_DATE)
    print(f"DOI info ingested: {ds}")

# %%
for ds in datasets:
    ds_path = datasets_repo_path / "datasets" / ds

    v1_doi_id = ao.get_doi_from_dataset(ds_path, version=True)
    # load deposition 
    # bump version


    # defensive / pause
    zenodo.set_deposition_id(v1_doi_id)
    deposition = zenodo.deposition

    new_doi_id = f"{deposition['id']}"
    print(f"assert DOI for {ds} to v1.0: {new_doi_id}")

    # defensive / pause
    zenodo.set_deposition_id(new_doi_id)

    # 
    long_dataset_name = ds_path.name
    doi_path = ds_path / "DOI"
    with open((doi_path / f"{long_dataset_name}.json"), "r") as f:
        metadata = json.load(f)
    print(f"Metadata for {ds} at v1.0: {metadata}")

    # datset_title is not correct...


    # # this might have to happen by hand since already published...
    # it did fail all this does is archive the deposition locally and finalize the DOI, which should be safe to do even if the DOI is already published.
    # just update the metadata
    deposition = ao.update_doi_metadata(zenodo, new_doi_id, metadata)
    # if ds == "voet-pmdbs-sn-atacseq-scalebio-hydrop":
    #     file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"
    #     # deposition = update_doi_metadata(zenodo, v1_beta_doi_id, metadata)
    #     if file_path.exists():
    #         # not sure why this fails... seems that the REST API has changed behavior
    #         deposition = ao.replace_anchor_file_in_doi(zenodo, ds_path, new_doi_id, file_path)
    #         print(f"Uploaded README: {ds_path.name}")

    #     else:
    #         print(f"WARNING: README PDF not found for {ds_path.name}")
 
    zenodo.set_deposition_id(new_doi_id)
    
    # deposition = ao.publish_dataset_doi(ds_path, zenodo)

    deposition = zenodo.deposition

    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)

# %%
# now republish everything
for ds in datasets:
    ds_path = datasets_repo_path / "datasets" / ds
    v1_doi_id = ao.get_doi_from_dataset(ds_path, version=True)
    zenodo.set_deposition_id(v1_doi_id)
    deposition = zenodo.deposition
    # deposition = ao.publish_doi(zenodo, v1_doi_id)
    ao.archive_deposition_local(ds_path, "final-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)

# now we need to sync the updated files back to the 
####################
# create dataset.json . 




# %%
# no rsync everything in DOI/ to metadata repo path
for ds in datasets:
    src_path = datasets_repo_path / "datasets" / ds / "DOI"
    dst_path = metadata_repo_path / "datasets" / ds / "DOI"
    if dst_path.exists(): 
        print(f"WARNING: {dst_path} already exists. Please resolve before moving.")

    # dry-run with print first to confirm paths look correct
    print(f"Syncing {src_path} to {dst_path}")
    subprocess.run(["rsync", "-avz", f"{src_path}/", f"{dst_path}/"], check=True)

        # shutil.copytree(src_path, dst_path)
        # print(f"Copied {src_path} to {dst_path}")



# %%
# create this now even thouth we'll re-make it later.
new_dataset_defs = []
for ds in datasets:
    ds_path = datasets_repo_path / "WIP" / ds

    ds_in = ao.Dataset.load(ds_path)
    ds_def = ao.fill_dataset_stub(ds_in,ds_path)


    ds_def.save(ds_path)

    new_dataset_defs.append(ds_def)
    
# %%    




# %%
# move below to part of a release script
# # %%
zenodo = ao.setup_zenodo()

for ds_def in new_dataset_defs:
    ds_path = datasets_repo_path / "WIP" / ds_def.name
    readme_pdf = ds_path / "DOI" / f"{ds_def.name}_README.pdf"
    doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    print(f"NEW:  {ds_def.name}: {ds_def.doi} ||| {doi_id}")
    readme_pdf = ds_path / "DOI" / f"{ds_def.name}_README.pdf"

    if readme_pdf.exists():
        # not sure why this fails... seems that the REST API has changed behavior
        deposition = ao.replace_anchor_file_in_doi(zenodo, ds_path, doi_id, readme_pdf)
        print(f"Uploaded README: {ds_def.name}")

        ao.finalize_DOI(ds_path, deposition, prerelease=True)
        # archive deposition
        ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)

    else:
        print(f"WARNING: README PDF not found for {ds_def.name}")



# %% [Step 67] publish DOI and move WIP dataset tree to cloud-datasets root

for ds in datasets:
    ds_path = datasets_repo_path / "WIP" / ds
    # TODO: update the filename to match the actual reference document
    doi_id = ao.get_doi_from_dataset(ds_path, version=True)
    deposition = zenodo.get_deposition(doi_id)

    deposition = ao.publish_doi(zenodo, doi_id)
    ao.archive_deposition_local(ds_path, "final-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition)

    # move WIP to datasets/
    final_ds_path = datasets_repo_path / "datasets" / ds
    if final_ds_path.exists():
        print(f"WARNING: {final_ds_path} already exists. Please resolve before moving.")
    else:
        shutil.move(str(ds_path), str(final_ds_path))
        print(f"Moved {ds_path} to {final_ds_path}")



# %%