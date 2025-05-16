import os
import json
from datetime import datetime

# filepath: /Users/kkyzl/Desktop/GIT_REPO/NLP-team9/results/generate_info_files.py
# Define the base directory
base_dir = "/Users/kkyzl/Desktop/GIT_REPO/NLP-team9/results"

# Iterate through all subdirectories in the base directory
for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if os.path.isdir(folder_path):
        # Check for _api_failed.jsonl and _other_failed.jsonl files
        api_failed = any(f.endswith("_api_failed.jsonl") for f in os.listdir(folder_path))
        other_failed = any(f.endswith("_other_failed.jsonl") for f in os.listdir(folder_path))
        rerun = any(f.endswith("_reruned.jsonl") for f in os.listdir(folder_path))
        fixed = any(f.endswith("_fix.jsonl") for f in os.listdir(folder_path))
        # Determine filter_state
        filter_state = "success"
        if api_failed:
            if rerun:
                if fixed:
                    api_failed_state = "fixed"
                else:
                    api_failed_state = "rerunned"
            else:
                api_failed_state = "haven't rerunned"
            filter_state = "filtered"
        elif other_failed:
            filter_state = "filtered"
            if fixed:
                other_failed_state = "fixed"
            else:
                other_failed_state = "not fixed"
        else:
            filter_state = "unfiltered"
        # Check if the folder contains any JSON files
        json_files = [f for f in os.listdir(folder_path) if f.endswith(".jsonl")]
        if not json_files:
            print(f"No JSON files found in {folder_path}. Skipping...")
            continue
    
        # Create the info dictionary
        info = {
            "model_name": folder.split("_")[0],  # Assuming model name is part of the folder name
            "language": "fr",  # Default language
            "input_format": "base",  # Default input format
            "time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "filter_state": filter_state,
            "api_failed_state": api_failed_state if api_failed else "none",
            "other_failed_state": other_failed_state if other_failed else "none",
        }

        # Write the info to 0_info.json
        info_file_path = os.path.join(folder_path, "0_info.json")
        with open(info_file_path, "w", encoding="utf-8") as info_file:
            json.dump(info, info_file, indent=4, ensure_ascii=False)

        print(f"Generated 0_info.json for {folder}")