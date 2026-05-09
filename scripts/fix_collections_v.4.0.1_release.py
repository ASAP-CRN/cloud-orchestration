
# %% Setup
from pathlib import Path
import asap_orchestrator as ao
import json

# TODO: confirm the root path resolves correctly for your environment
root_path = Path(__file__).resolve().parents[2]
datasets_repo_path = root_path / "cloud-datasets"
collections_repo_path = root_path / "cloud-collections"
releases_repo_path = root_path / "cloud-releases"


# %%

with open(collections_repo_path / "collections.json", "r") as f:
    collection_info = json.load(f)

collection_names = list(collection_info.keys())

for collection in collection_names:
    c_info = collection_info[collection]
    for version, v_info in c_info["versions"].items():
        datasets = v_info["datasets"]
        release = v_info["release"]["version"]
        for ds in datasets:
            ds_path = datasets_repo_path / "datasets" / ds
            with open(ds_path / "dataset.json", "r") as f:
                ds_info = json.load(f)
            ds_version = ds_info["releases"][release]["dataset_version"]
            ds_info["collection"] = collection

            # save collection info into datset.json
            with open(ds_path / "dataset.json", "w") as f:
                json.dump(ds_info, f, indent=4)

            # also save it to the archive
            with open(ds_path / "archive" / ds_version / "dataset.json", "w") as f:
                json.dump(ds_info, f, indent=4)


# %%

with open(datasets_repo_path / "datasets.json", "r") as f:
    datasets = json.load(f)


all_datasets = list(datasets.keys())
datasets_dict = {}
for dataset, ds_info in datasets.items():

    # load dataset.json into Dataset model
    ds_path = datasets_repo_path / "datasets" / dataset
    
    dataset_json_path = ds_path / "dataset.json"
    if dataset_json_path.exists():
        with open(dataset_json_path, "r") as f:
            dataset_json = json.load(f)
    else:
        print(f"WARNING: dataset.json not found for dataset {dataset} at expected path: {dataset_json_path}")
        dataset_json = {}



    # fix the all_versions while we are here
    all_versions = dataset_json.get("releases", {})
    ds_vers = []
    releases = []
    for rel_ver, rel_info in all_versions.items():
        releases.append(rel_ver)
    ds_vers.append(rel_info["dataset_version"])

    dataset_model = ao.Dataset.load(ds_path)
    export_to_datasets = dataset_model.model_dump()
    export_to_datasets["all_versions"] = list(set(ds_vers))
    export_to_datasets["all_releases"] = releases
    
    datasets_dict[dataset] = export_to_datasets

#%% write back to datasets.json
datasets_json_path = datasets_repo_path / "datasets.json"
with open(datasets_json_path, "w") as f:
    json.dump(datasets_dict, f, indent=4)



# %%
