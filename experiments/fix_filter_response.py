import json
import shutil

dir_name = "results/"
file_name = "mistral-small-latest_fr_json_20250512-030100"
jsonl_file = dir_name + file_name + ".jsonl"
null_response_list = []
null_answer_list = []
retry_info = ["question_index", "subtask", "option_permutation", "ground_truth_answer"]

shutil.copy(jsonl_file, dir_name + "raw/" + file_name + "_raw.jsonl")

with open(jsonl_file, "r") as file:
    for line in file:
        json_obj = json.loads(line)
        if(not json_obj["extracted_answer"]):
            if(not json_obj["api_raw_response"]):
                retry = {}
                for i in retry_info:
                    retry[i] = json_obj[i]
                null_response_list.append(retry)
            else:
                null_answer_list.append(json_obj)
output_file = "results/failed/" + file_name + "_api_failed.jsonl"

with open(output_file, "w", encoding='utf-8') as file:
    for entry in null_response_list:
        json.dump(entry, file)
        file.write('\n')

output_file = "results/failed/" + file_name + "_other_failed.json"

with open(output_file, "w", encoding='utf-8') as file:
    json.dump(null_answer_list, file, indent=2, ensure_ascii=False)
    # for entry in null_answer_list:
        # json.dump(entry, file)
        # file.write('\n')