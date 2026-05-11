
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
            ds_info["version"] = ds_version
            # fix releases to only note if the daset was "new"
            # load release.json
            test_releases = ds_info["releases"].copy()
            for rel_ver,info in test_releases.items():
                if rel_ver <= "v4.0.1":
                    with open(releases_repo_path / rel_ver / "release.json", "r") as f:
                        rel_info = json.load(f)
                    new_datasets = [x["name"] for x in rel_info["new_datasets"] ]
                    if ds not in new_datasets:
                        ds_info["releases"].pop(rel_ver)
            
            with open(ds_path / "archive" / ds_version / "dataset.json", "w") as f:
                json.dump(ds_info, f, indent=4)

# %%

with open(datasets_repo_path / "datasets.json", "r") as f:
    datasets = json.load(f)

# get all the datasets to check

for ds, _ds_info in datasets.items():
    print(f"processing {ds}")
    ds_path = datasets_repo_path / "datasets" / ds
    with open(ds_path / "dataset.json", "r") as f:
        ds_info = json.load(f)


    # test_releases = ds_info["releases"].copy()
    # # make sure that we only keep "new_release" entries..
    # for rel_ver,info in test_releases.items():
    #     if rel_ver <= "v4.0.1":
    #         with open(releases_repo_path / rel_ver / "release.json", "r") as f:
    #             rel_info = json.load(f)
    #         new_datasets = [x["name"] for x in rel_info["new_datasets"] ]
    #         if ds not in new_datasets:
    #             # print(f"(new) popping {ds_info["releases"][rel_ver]=}")
    #             ds_info["releases"].pop(rel_ver)

    # # save updated info root datset.json
    # with open(ds_path / "dataset.json", "w") as f:
    #     json.dump(ds_info, f, indent=4)

    # #reload
    # with open(ds_path / "dataset.json", "r") as f:
    #     ds_info = json.load(f)
    # print(f"{ds_info['releases']}")
    ds_info_copy = ds_info.copy() # start over fore each version...


    # now we need to check all of our versions....
    ds_vers = [info["dataset_version"] for rel_ver,info in ds_info["releases"].items()]
    ds_vers = sorted(list(set(ds_vers)), reverse=True)
    ds_info_releases = ds_info["releases"].copy()
    print(f"all versions = {ds_vers=}")


    for ds_ver in ds_vers: 
        # force this probe version
        _ds_info = ds_info_copy.copy()
        _ds_info["version"] = ds_ver

        print(f"DATASET version: {ds_ver}, {_ds_info['releases']=}")
        # just make sure we have all of the ds_ver


        # # need to make sure to get the higest release info for each version.
        # for rel_ver, info in ds_info_releases.items():
        #     if rel_ver <= "v4.0.1":
        #         with open(releases_repo_path / rel_ver / "release.json", "r") as f:
        #             rel_info = json.load(f)
        #         new_datasets_ver = {x["name"]:x["version"] for x in rel_info["new_datasets"] }

        #         if ds not in set(new_datasets_ver.keys()):
        #             # print(f"(new) popping {ds_info["releases"][rel_ver]=}")
        #             ds_info["releases"].pop(rel_ver)

        curr_ds_info_rel = _ds_info["releases"].copy()

        for rel_ver, info in curr_ds_info_rel.items():
            # start with new ds_info every time...
            # with open(ds_path / "dataset.json", "r") as f:
            #     ds_info_now = json.load(f)  
            ds_info_now = _ds_info.copy()
            # ds_info_now["version"] = ds_ver
            # now make sure we don't have any above ds_ver
            # now find the pop any releases where the ds_ver doesn't match
            print(f"dataset_version={info["dataset_version"]},{ds_ver=}")
            if info["dataset_version"] > ds_ver:
                print(f"(ds) ds {ds_ver=} popping {rel_ver} from {ds_info_now['releases']}")
                popped = ds_info_now["releases"].pop(rel_ver)
                print(f"{popped=}")

        ver_path = ds_path / "archive" / ds_ver 
        if not ver_path.exists():
            ver_path.mkdir(parents=True)

        with open(ds_path / "archive" / ds_ver / "dataset.json", "w") as f:
            json.dump(ds_info_now, f, indent=4)


# # %%
#     # also save it to the archive
#     # fix releases to only note if the daset was "new"
#     # load release.json
#     test_releases = ds_info["releases"].copy()
#     for rel_ver,info in test_releases.items():
#         if rel_ver <= "v4.0.1":
#             with open(releases_repo_path / rel_ver / "release.json", "r") as f:
#                 rel_info = json.load(f)
#             new_datasets = [x["name"] for x in rel_info["new_datasets"] ]
#             if ds not in new_datasets:
#                 ds_info["releases"].pop(rel_ver)
    




# %%

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



# %
# %%
