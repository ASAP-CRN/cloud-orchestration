# %% [markdown]
# # ASAP CRN —  NOTES
# DO NOT EXECUTE THIS FILE DIRECTLY — it is a template only.

# %% Setup
from pathlib import Path
import asap_orchestrator as ao
import json
import shutil

# TODO: confirm the root path resolves correctly for your environment
root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"
collections_repo_path = root_path / "cloud-collections"
releases_repo_path = root_path / "cloud-releases"
metadata_repo_path = root_path / "asap-crn-cloud-dataset-metadata"

%load_ext autoreload
%autoreload 2

# %% [Step 1] Release parameters

PUBLICATION_DATE = "2026-05-31"   # e.g. "2026-05-01"
CDE_VERSION = "v4.4"              # e.g. "v3.3"


# %% [Step 2] Define datasets NEW or VERSION-BUMPED in this release

############# WIP datasets
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
'lee-mouse-ms-mb-plasma-g2019s-hf-diet',
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

new_datasets = [
    'vangheluwe-ipsc-bulk-atacseq-astro-atp13a2lof',
    'vangheluwe-ipsc-bulk-rnaseq-astro-atp13a2lof',
    'vangheluwe-ipsc-bisulfseq-astro-atp13a2lof',
    ]
# %%
zenodo = ao.setup_zenodo()

# %%

for ds in new_datasets:
    ds_path = datasets_repo_path / "WIP" / ds
    # TODO: update the filename to match the actual reference document
    
    # confirm we have v0.1
    # read version
    current_version = (ds_path / "version").read_text().strip()
    if current_version != "0.1":
        print(f"WARNING: expected version 0.1 for {ds}, but found {current_version}")

    # find the refs.docx
    ref_path = ds_path / "refs"
    if len(list(ref_path.glob("*.docx"))) == 1:
        ref_doc = list(ref_path.glob("*.docx"))[0]
    else:
        print(f"WARNING: expected exactly 1 .docx file in {ref_path}, but found {len(list(ref_path.glob('*.docx')))}")
        ref_doc = list(ref_path.glob("*.docx"))[1] # only voet-lr-wgs has 2 .docx files, so this is a temporary workaround.  Please rename the correct ref doc to avoid this in the future.

    v1_doi_id = ao.get_doi_from_dataset(ds_path, version=True)

    if not v1_doi_id:
        print(f"WARNING: no DOI found for {ds} at v1.0 after ingestion")
        continue
    else:        
        print(f"Found DOI for {ds} at v0.1: {v1_doi_id}")

    # assert v1.0
    ds_version = "1.0"
    # write version
    ao.write_version(ds_version, ds_path / "version")

    ao.setup_DOI_info(ds_path, ref_doc, publication_date=PUBLICATION_DATE)
    print(f"DOI info ingested: {ds}")

    # load deposition 
    # bump version
    # defensive / pause
    zenodo.set_deposition_id(v1_doi_id)
    deposition = zenodo.deposition

    file_path = ds_path / "DOI" / f"{ds_path.name}_README.pdf"
    deposition = ao.add_anchor_file_to_doi(zenodo,  file_path, v1_doi_id)

    deposition = zenodo.deposition
    

    ao.archive_deposition_local(ds_path, "pre-release-deposition", deposition)
    ao.finalize_DOI(ds_path, deposition, prerelease=True)

# %%
