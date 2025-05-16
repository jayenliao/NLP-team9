import os
import json
import shutil
from run_question_selected import run_question_selected
import datetime

# Paths
base_dir = "./results/"
base_log_dir = "./results/__logs__/"
backup_dir = base_log_dir + "1-to-Rerun.backup"
to_rerun_file = base_log_dir + "1-to-Rerun"
to_concat_file = base_log_dir + "3-to-Concact"
to_manual_fix = base_log_dir + "2-to-Manual-Fix"

ori_manual_fix_list = []
rerun_after_rerun = []
# Load experiments to rerun
with open(to_rerun_file, "r") as f:
    experiments_to_rerun = [line.strip() for line in f.readlines()]
with open(to_manual_fix, "r") as f:
    ori_manual_fix_list = [line.strip() for line in f.readlines()]

print(len(experiments_to_rerun), "experiments to rerun")
for experiment in experiments_to_rerun:
    print(f"Processing experiment: {experiment}")
    experiment_path = f"results/{experiment}"
    api_failed_path = os.path.join(experiment_path, "api_failed.jsonl")
    rerun_path = os.path.join(experiment_path, "rerun.jsonl")
    other_failed_path = os.path.join(experiment_path, "other_failed.json")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Backup files
    
    api_failed_backup_dir = os.path.join(experiment_path, "api_failed.backup")
    if not os.path.exists(api_failed_backup_dir):
        os.makedirs(api_failed_backup_dir)
    api_failed_backup_path = os.path.join(api_failed_backup_dir, f"{timestamp}.jsonl")
    shutil.copy(api_failed_path, api_failed_backup_path)

    if os.path.exists(other_failed_path):
        other_failed_backup_dir = os.path.join(experiment_path, "other_failed.backup")
        if not os.path.exists(other_failed_backup_dir):
            os.makedirs(other_failed_backup_dir)
        other_failed_backup_path = os.path.join(other_failed_backup_dir, f"{timestamp}.txt")
        shutil.copy(other_failed_path, other_failed_backup_path)

    # Parse experiment name
    model_name, language, input_format, _ = experiment.split("_")
    model_family = model_name.split("-")[0]
    # Process api_failed.jsonl
    rerun_success = True
    rerun_results = []
    other_failed_results = []
    remaining_failed = []
    manual_fix = False
    with open(api_failed_path, "r") as f:
        for line in f:
            question = json.loads(line)
            result = run_question_selected(model_family, model_name, language, input_format, question)

            if result["extracted_answer"]:
                rerun_results.append(result)
            elif result["api_call_successful"]:
                other_failed_results.append(result)
                manual_fix = True
            else:
                remaining_failed.append(line)
                rerun_success = False

    # Write rerun.jsonl
    with open(rerun_path, "a") as f:
        for result in rerun_results:
            f.write(json.dumps(result) + "\n")

    # Write other_failed.json
    if manual_fix and experiment not in ori_manual_fix_list:
        with open(to_manual_fix, "a") as f:
            f.write(experiment + "\n")
        with open(other_failed_path, "w") as f:
            json.dump(other_failed_results, f, indent=4, ensure_ascii=False)

    if manual_fix and experiment in ori_manual_fix_list:
        with open(other_failed_path, "r") as f:
            other_failed_data = json.load(f)
        other_failed_data.extend(other_failed_results)
        with open(other_failed_path, "w") as f:
            json.dump(other_failed_data, f, indent=4, ensure_ascii=False)
            
    # Update api_failed.jsonl
    with open(api_failed_path, "w") as f:
        for line in remaining_failed:
            f.write(line)

    # Update 1-to-Rerun and 3-to-Concact
    if not rerun_success:
        with open(to_rerun_file, "a") as f:
            f.write(experiment + "\n")
    if rerun_success and not manual_fix and experiment not in ori_manual_fix_list:
        with open(to_concat_file, "a") as f:
            f.write(experiment + "\n")

# backup the original To-Run
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(backup_dir, f"{timestamp}.txt")
shutil.copy(to_rerun_file, backup_path)
print(f"Backed up original To-Run to {backup_path}")

# Save updated 1-to-Rerun
with open(to_rerun_file, "w") as f:
    for experiment in rerun_after_rerun:
        f.write(experiment + "\n")