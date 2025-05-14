import os
import json
import shutil
from datetime import datetime

# File paths
base_path = "results/0_logs/"
manual_fix_path = os.path.join(base_path, "To-Manual-Fix")
rerun_path = os.path.join(base_path, "To-Rerun")
concat_path = os.path.join(base_path, "To-Concact")
backup_manual_fix_path = os.path.join(base_path, "To-Manual-Fix.backup")
backup_concat_path = os.path.join(base_path, "To-Concact.backup")

# Ensure backup directories exist
os.makedirs(backup_manual_fix_path, exist_ok=True)
os.makedirs(backup_concat_path, exist_ok=True)

# Backup function
def backup_file(file_path, backup_folder):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file_path = os.path.join(backup_folder, f"{timestamp}.txt")
    shutil.copy(file_path, backup_file_path)

# Read experiment names from files
def read_experiment_names(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file.readlines()]

# Write experiment names to file
def write_experiment_names(file_path, experiment_names):
    with open(file_path, "w") as file:
        file.write("\n".join(experiment_names))

def update_correctness_one(extracted_answer, option_permutation, ground_truth_label):
    if extracted_answer in ['A', 'B', 'C', 'D']:
        # Find the 0-based index corresponding to the extracted positional answer
        # 'A' -> 0, 'B' -> 1, 'C' -> 2, 'D' -> 3
        choice_index = ord(extracted_answer.upper()) - ord('A')

        # Use this index to find the original label from the permutation list
        if 0 <= choice_index < len(option_permutation):
            model_choice_original_label = option_permutation[choice_index]
            # print(f"Extracted answer (positional): '{extracted_answer}', "
            #                 f"Permutation: {option_permutation}, "
            #                 f"Calculated original label: '{model_choice_original_label}'")
        else:
                # print(f"Extracted answer '{extracted_answer}' resulted in an invalid index {choice_index} "
                #             f"for permutation {option_permutation}. Cannot determine original label.")
                model_choice_original_label = "ERROR_MAP" # Indicate mapping error
    else:
        is_correct = False
        model_choice_original_label = "INVALID_EXT" # Indicate invalid extracted answer
    if model_choice_original_label and model_choice_original_label not in ["ERROR_MAP", "INVALID_EXT"] and \
    ground_truth_label != "UNKNOWN" and ground_truth_label != "ERROR_GT":
        try:
            is_correct = (model_choice_original_label == ground_truth_label)
            # print(f"Comparing model original '{model_choice_original_label}' with ground truth '{ground_truth_label}'. Correct: {is_correct}")
        except Exception as e:
                # print(f"Error comparing labels for correctness: {e}", exc_info=True)
                is_correct = None # Error during comparison
    else:
        # print("Cannot determine correctness (missing model choice, ground truth, or error occurred).")
        is_correct = None # Cannot determine correctness
    return is_correct, model_choice_original_label

def update_correctness(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)

    for obj in data:
        if obj.get("extracted_answer"):
            obj["is_correct"], obj["model_choice_original_label"] = update_correctness_one(
                obj["extracted_answer"],
                list(obj.get("option_permutation", "")),  # Convert "ABCD" to ['A', 'B', 'C', 'D']
                obj.get("ground_truth_answer", "UNKNOWN")
            )
        
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)
# Check if the JSON file is correctly revised
def is_correctly_revised(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    null_trials = [obj["trial_id"] for obj in data if obj.get("is_correct") is None or obj.get("extracted_answer") is None]
    return null_trials

# Main logic
def process_experiments():
    # Backup original files
    backup_file(manual_fix_path, backup_manual_fix_path)
    backup_file(concat_path, backup_concat_path)

    # Read experiment names
    manual_fix_experiments = read_experiment_names(manual_fix_path)
    rerun_experiments = set(read_experiment_names(rerun_path))
    concat_experiments = read_experiment_names(concat_path)

    updated_manual_fix = []
    updated_concat = concat_experiments

    for experiment in manual_fix_experiments:
        json_file_path = f"results/{experiment}/other_failed.json"
        if os.path.exists(json_file_path):
            update_correctness(json_file_path)
            null_trials = is_correctly_revised(json_file_path)
            if null_trials:
                print(f"Experiment '{experiment}' has {len(null_trials)} unresolved cases: ")
                for trial in null_trials:
                    print(f"\t\tTrial ID: {trial}")
                updated_manual_fix.append(experiment)
            else:
                if experiment in rerun_experiments:
                    print(f"Experiment '{experiment}' hasn't finished with API-failed cases.")
                    updated_manual_fix.append(experiment)
                else:
                    updated_concat.append(experiment)
        else:
            print(f"JSON file for experiment '{experiment}' not found.")
            updated_manual_fix.append(experiment)

    # Write updated lists back to files
    write_experiment_names(manual_fix_path, updated_manual_fix)
    write_experiment_names(concat_path, updated_concat)

# Run the script
if __name__ == "__main__":
    process_experiments()