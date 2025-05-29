import json
import os
import re
import shutil
from datetime import datetime

from core_runner import (
    # load_prompt_template,
    parse_response,
    structure_result
)# 假設 parse_response 已經寫好，直接貼上函式（根據你的版本加上修正）

# Step 1: 取得 exp_name
def read_experiment_names(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file.readlines()]

log_dir = 'results/__logs__/2-to-Manual-Fix'
# exp_names = [name for name in os.listdir(log_dir) if os.path.isdir(os.path.join(log_dir, name))]
exp_names = read_experiment_names(log_dir)
if not exp_names:
    raise RuntimeError("No experiment found in results/__logs__/2-to-Manual-Fix")
# for exp_name in exp_names:
#     # exp_name = exp_names[0]  # 這裡取第一個 exp_name，或你可以指定某個名稱

#     # 檔案路徑
#     file_path = f'results/{exp_name}/other_failed.json'
#     backup_dir = f'results/{exp_name}/other_failed.backup'
#     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#     backup_file = os.path.join(backup_dir, f'other_failed_{timestamp}.json')

#     # Step 2: Backup original JSON
#     os.makedirs(backup_dir, exist_ok=True)
#     shutil.copyfile(file_path, backup_file)
#     print(f"Backed up original file to {backup_file}")

#     # Step 3: Load JSON data, modify, and overwrite original
#     with open(file_path, 'r', encoding='utf-8') as infile:
#         data = json.load(infile)  # Expecting a list of objects
    
#     for obj in data:
#     # line = line.strip()
#         if not obj:
#             continue
#         try:
#             # obj = json.loads(line)
            
#             api_response_text = obj.get('api_response_text', '')
#             parsed_answer = parse_response(api_response_text)
#             output_format = ""
#             try:
#                 output_format = obj["output_format"]
#             except KeyError:
#                 output_format = "base"
#             data_item = {}
#             data_item['answer_label'] = obj["ground_truth_answer"]
#             data_item['id'] = obj["question_id"]
#             # TODO: 在這裡執行你要的部分更動
#             new_obj = structure_result(
#                 data_item=data_item,
#                 subtask=obj["subtask"],
#                 language=obj["language"],
#                 model_name=obj["model_name"],
#                 input_format=obj["input_format"],
#                 output_format=output_format,
#                 option_permutation=list(obj["option_permutation"]), # The list like ['D', 'A', 'B', 'C']
#                 api_raw_response=obj["api_raw_response"],
#                 api_call_successful=obj["api_call_successful"],
#                 extracted_answer=parsed_answer, # e.g., 'A', 'B', 'C', or 'D'
#                 log_probabilities=None,
#                 question_index=obj["question_index"], # Absolute index from the dataset for this subtask/language
#                 api_response_text = str(obj["api_response_text"]) if obj["api_response_text"] is not None else None, # Raw text from the API response
#             )
#             outfile.write(json.dump(new_obj, ensure_ascii=False) + '\n')
#         except json.JSONDecodeError as e:
#             print(f"JSON decode error: {e} in line: {line}")

#     with open(file_path, 'w', encoding='utf-8') as outfile:


for exp_name in exp_names:
    print(f"\nProcessing {exp_name}...")

    file_path = f'results/{exp_name}/other_failed.json'
    backup_dir = f'results/{exp_name}/other_failed.backup'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'{timestamp}.json')

    # Check if file exists and is not empty
    if not os.path.exists(file_path):
        print(f"{exp_name}'s other_failed.json does not exist. Skipping.")
        continue

    if os.stat(file_path).st_size == 0:
        print(f"{exp_name}'s other_failed.json is empty. Skipping.")
        continue

    # Backup the original file
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copyfile(file_path, backup_file)
    print(f"Backed up to {backup_file}")

    # Load JSON, process, and overwrite
    with open(file_path, 'r', encoding='utf-8') as infile:
        try:
            data = json.load(infile)  # Expecting a list of objects
        except json.JSONDecodeError as e:
            print(f"JSON decode error in {exp_name}'s other_failed.json: {e}")
            continue

    total = len(data)
    failed = 0
    for obj in data:
        api_response_text = obj.get('api_response_text', '')
        # answer = parse_response(api_response_text)
        # TODO: Additional modifications here
        parsed_answer = parse_response(api_response_text)
        if obj["extracted_answer"] is None:
            obj["extracted_answer"] = parsed_answer

        output_format = ""
        try:
            output_format = obj["output_format"]
        except KeyError:
            output_format = "base"
        api_response_text = ""
        try:
            api_response_text = obj["api_response_text"]
        except KeyError:
            api_response_text = ""
        data_item = {}
        data_item['answer_label'] = obj["ground_truth_answer"]
        data_item['id'] = obj["question_id"]
        # TODO: 在這裡執行你要的部分更動
        new_obj = structure_result(
            data_item=data_item,
            subtask=obj["subtask"],
            language=obj["language"],
            model_name=obj["model_name"],
            input_format=obj["input_format"],
            output_format=output_format,
            option_permutation=list(obj["option_permutation"]), # The list like ['D', 'A', 'B', 'C']
            api_raw_response=obj["api_raw_response"],
            api_call_successful=obj["api_call_successful"],
            extracted_answer=obj["extracted_answer"], # e.g., 'A', 'B', 'C', or 'D'
            log_probabilities=None,
            question_index=obj["question_index"], # Absolute index from the dataset for this subtask/language
            api_response_text = api_response_text # Raw text from the API response
        )
        if new_obj["extracted_answer"] is None:
            failed += 1
    with open(file_path, 'w', encoding='utf-8') as outfile:
        json.dump(data, outfile, ensure_ascii=False, indent=2)

    print(f"Processing complete for {exp_name}.")
    print(f"Updated {file_path}.")
    print(f"Total {total}, failed {failed}.")
    print("")
