from datasets import load_dataset
import pandas as pd
import numpy as np
import os, pickle
from data.categories import categories, subcategories

def save_datasets():
    # Load the original datasets
    ds_en = load_dataset("cais/mmlu", "all", split="test")
    ds_fr = load_dataset("openai/MMMLU", "FR_FR", split="test")

    # Get the list of all categories
    selected_categories = []
    for v in categories.values():
        selected_categories += v

    # Select the first subcategory for each category
    selected_subcategories = {}
    for k, v in subcategories.items():
        category = v[0]
        if category in selected_categories:
            selected_subcategories[category] = k
            selected_categories.remove(category)
        if len(selected_categories) == 0:
            break

    # Select the first 100 examples for each subcategory for both datasets
    ds_selected = {}
    print()
    for i, subcategory in enumerate(selected_subcategories.values()):
        ds_selected[subcategory] ={}
        ds_selected[subcategory]["en"] = ds_en.filter(lambda x: x["subject"] == subcategory).select(range(100))
        ds_selected[subcategory]["fr"] = ds_fr.filter(lambda x: x["Subject"] == subcategory).select(range(100))
        print(f"Subcategory {i:2d} {subcategory:35s}", ds_selected[subcategory]["en"].shape, ds_selected[subcategory]["fr"].shape)

    # Save the selected datasets (dict) to a pickle file
    fn = "ds_selected.pkl"
    with open(fn, "wb") as f:
        pickle.dump(ds_selected, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Saved selected datasets to {fn}")

if __name__ == "__main__":
    if os.path.exists("ds_selected.pkl"):
        print("Selected datasets already exist. Loading...")
    else:
        save_datasets()
