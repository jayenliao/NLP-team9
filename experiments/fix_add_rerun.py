import json
import shutil

dir_name = "results/rerun/"
file_name = "gemini-2.0-flash-lite_fr_xml_20250511-214536"
jsonl_file = dir_name + file_name + "_api_failed_reruned.jsonl"
retry_info = ["question_index", "subtask", "option_permutation", "ground_truth_answer"]

rerun_results = []
# with open(jsonl_file, "r") as file:
#     for line in file:
#         json_obj = json.loads(line)
#         rerun_results.append(json_obj)

dir_name = "results/"
jsonl_file = dir_name + file_name + ".jsonl"
ori_results = []

with open(jsonl_file, "r") as file:
    for line in file:
        json_obj = json.loads(line)
        ori_results.append(json_obj)

dir_name = "results/failed/"
jsonl_file = dir_name + file_name + "_other_failed.json"
parse_error = []

with open(jsonl_file, "r") as file:
    parse_error = json.load(file)

temp = [obj for obj in ori_results if obj["extracted_answer"] != None]

temp_temp = []
for p in parse_error:
    temp_temp += [obj for obj in ori_results 
            if obj["question_index"] == p["question_index"] 
            and obj["option_permutation"] == p["option_permutation"]
            and obj["extracted_answer"] != None]
for p in rerun_results:
    temp_temp += [obj for obj in ori_results 
            if obj["question_index"] == p["question_index"] 
            and obj["option_permutation"] == p["option_permutation"]
            and obj["extracted_answer"] != None]
    
print(len(temp), len(parse_error), len(rerun_results), len(temp_temp))
new_response = temp + rerun_results + parse_error
print(len(new_response))


output_file = "results/fix_exp/" + file_name + "_fix.jsonl"


with open(output_file, "x", encoding='utf-8') as file:
    for entry in new_response:
        json.dump(entry, file)
        file.write('\n')

