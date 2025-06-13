#experiments/fix_concact.py
import os
import json
import shutil
from datetime import datetime
from fix_format import (
    fix_format
)
    
# Paths
logs_dir = "results/__logs__"
backup_dir = os.path.join(logs_dir, "backup")
results_dir = "results"

# Backup function
def backup_logs():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(backup_dir, exist_ok=True)
    for file in os.listdir(logs_dir):
        if file.endswith(".txt"):
            shutil.copy(os.path.join(logs_dir, file), os.path.join(backup_dir, f"{file}.{timestamp}.backup"))

# Load experiment lists
def load_experiment_list(file_name):
    file_path = os.path.join(logs_dir, file_name)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return [line.strip() for line in f.readlines()]
    return []

# Save experiment list
def save_experiment_list(file_name, experiments):
    file_path = os.path.join(logs_dir, file_name)
    with open(file_path, "w") as f:
        f.writelines(f"{exp}\n" for exp in experiments)

# Concatenate results
def concatenate_results():
    to_manual_fix = load_experiment_list("2-to-Manual-Fix")
    to_rerun = load_experiment_list("1-to-Rerun")
    to_fix = load_experiment_list("0-to-Filter")
    to_concact = load_experiment_list("3-to-Concact")
    to_analyze = load_experiment_list("4-to-Analyze")

    updated_to_concact = []

    for experiment in to_concact:
        if experiment in to_manual_fix or experiment in to_rerun or experiment in to_fix:
            print(f"Experiment {experiment} is not ready since it is listed in "
                  f"{'2-to-Manual-Fix' if experiment in to_manual_fix else ''}"
                  f"{'1-to-Rerun' if experiment in to_rerun else ''}"
                  f"{'0-to-Filter' if experiment in to_fix else ''}.")
            continue

        experiment_dir = os.path.join(results_dir, experiment)
        raw_file = os.path.join(experiment_dir, "raw.jsonl")
        rerun_file = os.path.join(experiment_dir, "rerun.jsonl")
        other_failed_file = os.path.join(experiment_dir, "other_failed.json")

        if not os.path.exists(raw_file):
            print(f"Raw file missing for experiment {experiment}. Skipping.")
            continue

        # Load raw.jsonl
        with open(raw_file, "r") as f:
            raw_data = [json.loads(line) for line in f]

        # Load rerun.jsonl and other_failed.json if they exist
        rerun_data = []
        if os.path.exists(rerun_file):
            with open(rerun_file, "r") as f:
                rerun_data = [json.loads(line) for line in f]

        other_failed_data = []
        if os.path.exists(other_failed_file):
            with open(other_failed_file, "r") as f:
                other_failed_data = json.load(f)

        # Filter data with non-null "extracted_answer" and "is_correct"
        filtered_data = [
            obj for obj in raw_data + rerun_data + other_failed_data
            if obj.get("extracted_answer") is not None and obj.get("is_correct") is not None
        ]

        temp_a = [
            obj for obj in rerun_data
            if obj.get("extracted_answer") is not None and obj.get("is_correct") is not None
        ]

        temp_b = [
            obj for obj in other_failed_data
            if obj.get("extracted_answer") is not None and obj.get("is_correct") is not None
        ]

        temp_c = [
            obj for obj in raw_data
            if obj.get("extracted_answer") is not None and obj.get("is_correct") is not None
        ]
        print(len(temp_a), len(temp_b), len(temp_c))

        # Check object counts
        if len(filtered_data) != len(raw_data):
            print(f"Experiment {experiment} requires manual check: total # of objects in raw.jsonl is {len(raw_data)}, "
                  f"while there are {len(filtered_data)} objects to be concatenated.")
            updated_to_concact.append(experiment)
            continue

        # Save concatenated results to fix.jsonl
        fix_file = os.path.join(experiment_dir, "fix.jsonl")
        with open(fix_file, "w") as f:
            for obj in filtered_data:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        fix_format(exp = experiment, ismain=False)
        print(f"Experiment {experiment} concatenated successfully.")
        to_analyze.append(experiment)

    # Update experiment lists
    save_experiment_list("3-to-Concact", updated_to_concact)
    save_experiment_list("4-to-Analyze", to_analyze)

if __name__ == "__main__":
    backup_logs()
    concatenate_results()