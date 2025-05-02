# data/save_datasets.py

from datasets import load_dataset
import os, pickle
from categories import categories, subcategories  # Changed from 'data.categories' to work when run from NLP-team9/

def save_datasets():
    # Load datasets (unchanged)
    ds_en = load_dataset("cais/mmlu", "all", split="test")
    ds_fr = load_dataset("openai/MMMLU", "FR_FR", split="test")

    # Get all categories (unchanged)
    selected_categories = []
    for v in categories.values():
        selected_categories += v

    # Pick one subcategory per category (unchanged)
    selected_subcategories = {}
    for k, v in subcategories.items():
        category = v[0]
        if category in selected_categories:
            selected_subcategories[category] = k
            selected_categories.remove(category)
        if not selected_categories:
            break

    # Select 100 examples per subcategory and convert to dicts for portability
    # Changed: Convert Dataset objects to lists of dicts so pickle works across machines
    ds_portable = {}
    for i, subcategory in enumerate(selected_subcategories.values()):
        ds_portable[subcategory] = {
            "en": [row for row in ds_en.filter(lambda x: x["subject"] == subcategory).select(range(100))],
            "fr": [row for row in ds_fr.filter(lambda x: x["Subject"] == subcategory).select(range(100))]
        }
        # Changed: Simplified print to show row counts instead of Dataset shapes
        print(f"Subcategory {i:2d} {subcategory:35s} en={len(ds_portable[subcategory]['en'])} fr={len(ds_portable[subcategory]['fr'])}")

    # Save to pickle in data/
    # Changed: Use __file__ to always save to data/ds_selected.pkl, not current directory
    pickle_file = os.path.join(os.path.dirname(__file__), "ds_selected.pkl")
    with open(pickle_file, "wb") as f:
        pickle.dump(ds_portable, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Saved to {pickle_file}")

if __name__ == "__main__":
    # Changed: Check for pickle in data/ using __file__-based path
    pickle_file = os.path.join(os.path.dirname(__file__), "ds_selected.pkl")
    if os.path.exists(pickle_file):
        print("Dataset exists. Loading...")
    else:
        save_datasets()



# from datasets import load_dataset
# import pandas as pd
# import numpy as np
# import os, pickle
# from data.categories import categories, subcategories

# def save_datasets():
#     # Load the original datasets
#     ds_en = load_dataset("cais/mmlu", "all", split="test")
#     ds_fr = load_dataset("openai/MMMLU", "FR_FR", split="test")

#     # Get the list of all categories
#     selected_categories = []
#     for v in categories.values():
#         selected_categories += v

#     # Select the first subcategory for each category
#     selected_subcategories = {}
#     for k, v in subcategories.items():
#         category = v[0]
#         if category in selected_categories:
#             selected_subcategories[category] = k
#             selected_categories.remove(category)
#         if len(selected_categories) == 0:
#             break

#     # Select the first 100 examples for each subcategory for both datasets
#     ds_selected = {}
#     print()
#     for i, subcategory in enumerate(selected_subcategories.values()):
#         ds_selected[subcategory] ={}
#         ds_selected[subcategory]["en"] = ds_en.filter(lambda x: x["subject"] == subcategory).select(range(100))
#         ds_selected[subcategory]["fr"] = ds_fr.filter(lambda x: x["Subject"] == subcategory).select(range(100))
#         print(f"Subcategory {i:2d} {subcategory:35s}", ds_selected[subcategory]["en"].shape, ds_selected[subcategory]["fr"].shape)

#     # Save the selected datasets (dict) to a pickle file
#     fn = "ds_selected.pkl"
#     with open(fn, "wb") as f:
#         pickle.dump(ds_selected, f, protocol=pickle.HIGHEST_PROTOCOL)
#     print(f"Saved selected datasets to {fn}")

# if __name__ == "__main__":
#     if os.path.exists("ds_selected.pkl"):
#         print("Selected datasets already exist. Loading...")
#     else:
#         save_datasets()