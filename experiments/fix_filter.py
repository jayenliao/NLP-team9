#experiments/fix_filter.py
import os
import json
import shutil
import datetime

# Path to the "0-to-Filter" file
base_dir = "./results"
base_log_dir = "./results/__logs__/"
to_fix_path = base_log_dir + "0-to-Filter"
to_rerun_path = base_log_dir + "1-to-Rerun"
backup_dir = base_log_dir + "0-to-Filter.backup"
to_manual_fix_path = base_log_dir + "2-to-Manual-Fix"
to_analyze_path = base_log_dir + "4-to-Analyze"

if not os.path.exists(base_log_dir):
    os.makedirs(base_log_dir)

# Read the folder names from "0-to-Filter"
with open(to_fix_path, "r", encoding="utf-8") as file:
    folders = [line.strip() for line in file.readlines()]

to_rerun = []
remaining_folders = []  # 要留下的 folders

for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    raw_file_path = os.path.join(folder_path, "raw.jsonl")
    api_failed_path = os.path.join(folder_path, "api_failed.jsonl")
    other_failed_path = os.path.join(folder_path, "other_failed.json")

    if not os.path.exists(raw_file_path):
        print(f"raw.jsonl not found in {folder}")
        remaining_folders.append(folder)
        continue

    api_failed = []
    other_failed = []

    found_failure = False
    execution_success = True
    # Process the raw.jsonl file
    with open(raw_file_path, "r", encoding="utf-8") as raw_file:
        for line in raw_file:
            try:
                data = json.loads(line)
                if data.get("extracted_answer") is None:
                    if not data.get("api_raw_response", True):
                        api_failed.append(data)
                    else:
                        other_failed.append(data)
            except json.JSONDecodeError:
                print(f"Invalid JSON in {raw_file_path}: {line.strip()}")
                execution_success = False
                break

    # Save api_failed cases
    if api_failed:
        with open(api_failed_path, "w", encoding="utf-8") as api_failed_file:
            for item in api_failed:
                api_failed_file.write(json.dumps(item, ensure_ascii=False) + "\n")
        to_rerun.append(folder)
        found_failure = True

    # Save other_failed cases
    if other_failed:
        with open(other_failed_path, "w", encoding="utf-8") as other_failed_file:
            json.dump(other_failed, other_failed_file, indent=4, ensure_ascii=False)
        with open(to_manual_fix_path, "a", encoding="utf-8") as manual_fix_file:
            manual_fix_file.write(folder + "\n")
        found_failure = True

    if not execution_success:
        remaining_folders.append(folder)

    if not found_failure and execution_success:
        shutil.copy(raw_file_path, os.path.join(folder_path, "fix.jsonl"))
        print(f"Ready to analyze for {folder_path}/fix.jsonl")
        if not os.path.exists(to_analyze_path):
            with open(to_analyze_path, "w", encoding="utf-8") as analyze_file:
                analyze_file.write(folder + "\n")
        else:
            with open(to_analyze_path, "a", encoding="utf-8") as analyze_file:
                analyze_file.write(folder + "\n")
# Save the folders to "1-to-Rerun"
if to_rerun:
    with open(to_rerun_path, "w", encoding="utf-8") as rerun_file:
        for folder in to_rerun:
            rerun_file.write(folder + "\n")

# backup the original 0-to-Filter
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(backup_dir, f"{timestamp}.txt")
shutil.copy(to_fix_path, backup_path)
print(f"Backed up original 0-to-Filter to {backup_path}")

# renew 0-to-Filter
with open(to_fix_path, "w", encoding="utf-8") as file:
    for folder in remaining_folders:
        file.write(folder + "\n")

# list remainders
if remaining_folders:
    print("\nFolders that were not successfully filtered (kept in 0-to-Filter):")
    for folder in remaining_folders:
        print(f"  - {folder}")
