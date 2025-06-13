# analyze.py
from datasets import load_from_disk
import os
import pandas as pd
import numpy as np

models = ["gemini", "mistral"],
subtasks = ["abstract_algebra", "anatomy", "astronomy", "business_ethics", "college_biology", "college_chemistry", "college_computer_science", "econometrics", "electrical_engineering", "formal_logic", "global_facts", "high_school_european_history", "high_school_geography", "high_school_government_and_politics", "high_school_psychology", "human_sexuality", "international_law"],
languages = ["en", "fr"]
input_format = ["base", "json", "xml"]
output_format = ["base", "json", "xml"]
# 讀取儲存的資料夾
load_dir = os.path.join(os.path.dirname(__file__), "ds_saved")
ds = load_from_disk(load_dir)

# print(ds)
# from datasets import load_dataset
# import pandas as pd
# import numpy as np

# # 下載資料
# ds = load_dataset("r13922a24/nlptestrun")

def analyze_task(group):
    accuracy_by_answer = {}
    has_answer = 0
    for answer_option in ["A", "B", "C", "D"]:
        subset = group[group["parsed_answer"] == answer_option]
        if len(subset) == 0:
            accuracy = np.nan
        else:
            accuracy = subset["is_correct"].sum() / len(subset)
        accuracy_by_answer[answer_option] = accuracy
        has_answer += len(subset)

    accuracies = np.array([v for v in accuracy_by_answer.values() if not np.isnan(v)])
    if len(accuracies) == 0:
        mean_acc = std_dev = rsd = np.nan
    else:
        mean_acc = accuracies.mean()
        std_dev = accuracies.std()
        rsd = std_dev / mean_acc if mean_acc != 0 else np.nan
    # prnt(group[:1]["permutation"])i
    none_answer = len(group) - has_answer
    return mean_acc, std_dev, rsd, none_answer, accuracy_by_answer

def inverse_permutation(parsed_answer, permutation):
    index = 0
    if parsed_answer == "A":
        index = 0
    elif parsed_answer == "B":
        index = 1
    elif parsed_answer == "C":
        index = 2
    elif parsed_answer == "D":
        index = 3
    else:
        return 4
    return permutation[index]

def fluctuation(group):
    fluctuating_questions = 0
    total_questions = 0
    too_flutuating = 0
    for _, question_df in group.groupby("question_id"):
        # Get the original correct choice for all 4 permutations
        # print(type(question_df))
        # print(question_df)

        original_choices = []
        for _, q in question_df.iterrows():
            total_questions += 1
            # Map the parsed_answer back to original position
            original_choice = inverse_permutation(q["parsed_answer"], q["permutation"])
            original_choices.append(original_choice)
            # print(q["parsed_answer"], q["permutation"], original_choice)
            # If not all choices are the same, it fluctuated
            if len(set(original_choices)) > 1:
                fluctuating_questions += 1
                if len(set(original_choices)) > 2:
                    too_flutuating += 1

    FR = fluctuating_questions / total_questions
    FR_2 = too_flutuating / total_questions
    return FR, FR_2
# 轉成 pandas dataframe
df = ds["train"].to_pandas()

# # 只保留英文資料
# df = df[df["language"] == "en"]
# df = df[df["subtask"] == "global_facts"]
results = []

group_keys = ["subtask", "model", "language", "input_format", "output_format"]

# 依照 subtask 分組
for group_values, group_df in df.groupby(group_keys):
    
    mean_acc, std_dev, rsd, none_answer, accuracy_by_answer = analyze_task(group_df)
    acc = group_df["is_correct"].sum() / len(group_df)
    FR, FR_2 = fluctuation(group_df)
    # group_df["raw_response"]
    results.append({
        "subtask": group_values[0],
        "model": group_values[1],
        "language": group_values[2],
        "input_format": group_values[3],
        "output_format": group_values[4],
        "total_exp": len(group_df),
        "accuracy_A": accuracy_by_answer["A"],
        "accuracy_B": accuracy_by_answer["B"],
        "accuracy_C": accuracy_by_answer["C"],
        "accuracy_D": accuracy_by_answer["D"],
        "avg_word_count": group_df['raw_response'].astype(str).str.split().str.len().mean(),
        "accuracy": acc, 
        # "mean_accuracy": mean_acc,
        # "std_dev": std_dev,
        "RSD": rsd,
        "# of none": none_answer,
        "FR": FR,
        "FR_2": FR_2
    })

# 顯示結果
rsd_df = pd.DataFrame(results)
# print(rsd_df.sort_values("RSD", ascending=False).to_string(index=False))
rsd_df.to_csv("rsd_by_group.csv", index=False)
rsd_df.to_json("rsd_by_group.json", orient="records", indent=2)
