#experiments/fix_format.py
import os
import json
import shutil

def fix_format(exp, ismain=False):
    exp_names = []
    if (ismain):
        logs_path = "results/__logs__/5-to-Format"
        if not os.path.exists(logs_path):
            print(f"Log file not found: {logs_path}")
            return

        # Read experiment names
        with open(logs_path, "r") as f:
            exp_names = [line.strip() for line in f if line.strip()]
    else:
        exp_names = [exp]
    for exp_name in exp_names:
        exp_dir = f"results/{exp_name}"
        fix_path = os.path.join(exp_dir, "fix.jsonl")
        fix_old_path = os.path.join(exp_dir, "fix_old.jsonl")

        if not os.path.exists(fix_path):
            print(f"File not found: {fix_path}")
            continue

        # Rename original file
        shutil.move(fix_path, fix_old_path)

        # Read original objects
        with open(fix_old_path, "r", encoding="utf-8") as fin:
            lines = fin.readlines()

        # Write reformatted objects
        with open(fix_path, "w", encoding="utf-8") as fout:
            for line in lines:
                obj = json.loads(line)
                new_obj = {
                    "trial_id": obj.get("trial_id"),
                    "question_id": obj.get("question_id"),
                    "question_index": obj.get("question_index"),
                    "subtask": obj.get("subtask"),
                    "language": obj.get("language"),
                    "model_name": obj.get("model_name"),
                    "input_format": obj.get("input_format"),
                    "output_format": obj.get("output_format", "base"),
                    "option_permutation": obj.get("option_permutation"),
                    "api_call_successful": obj.get("api_call_successful"),
                    "extracted_answer": obj.get("extracted_answer"),
                    "model_choice_original_label": obj.get("model_choice_original_label"),
                    "log_probabilities": obj.get("log_probabilities"),
                    "ground_truth_answer": obj.get("ground_truth_answer"),
                    "is_correct": obj.get("is_correct"),
                    "api_response_text": obj.get("api_response_text", ""),
                    "api_raw_response": obj.get("api_raw_response"),
                }
                fout.write(json.dumps(new_obj, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    fix_format(ismain=True)