
from analyze_grouping import Analyze

targets = [
    # (["subtask"], ["language"], [("model", "gemini-2.0-flash")]),
    # (["subtask"], ["language"], [("model", "mistral-small-latest")]), 
    # (["subtask"], ["model"], [("language", "en")]), 
    # (["subtask"], ["model"], [("language", "fr")]),
    # (["subtask"], ["language", "model"], []),
    # (["subtask"], ["input_format", "output_format"], [("language", "en"), ("model", "gemini-2.0-flash")]),
    # (["subtask"], ["input_format", "output_format"], [("language", "fr"), ("model", "gemini-2.0-flash")]),
    # (["subtask"], ["input_format", "output_format"], [("language", "en"), ("model", "mistral-small-latest")]),
    # (["subtask"], ["input_format", "output_format"], [("language", "fr"), ("model", "mistral-small-latest")]), 
    # (["input_format", "output_format"], ["language", "model"], []), 
    (["subtask"], ["input_format"], [("language", "en"), ("output_format", "base")]),
    (["subtask"], ["output_format"], [("language", "en"), ("input_format", "base")]),
    (["subtask"], ["input_format"], [("language", "fr"), ("output_format", "base")]),
    (["subtask"], ["output_format"], [("language", "fr"), ("input_format", "base")])
]
# target = "subtask"
columns = ["accuracy", "avg_word_count", "accuracy_A", "accuracy_B", "accuracy_C", "accuracy_D", "FR", "FR_2", "RSD"]

acc_min = 0.5
acc_max = 1
awc_min = 75
awc_max = 325
fr_min = 0
fr_max = 0.45
fr2_min = 0
fr2_max = 0.1

plot_specs = [
    ("accuracy", "avg_word_count", "accuracy vs avg_word_count", acc_min, acc_max, awc_min, awc_max),
    ("accuracy", "FR", "accuracy vs Fluctuation Rate", acc_min, acc_max, fr_min, fr_max),
    ("accuracy", "FR_2", "accuracy vs Fluctuation Rate 2", acc_min, acc_max, fr2_min, fr2_max),
    ("FR", "avg_word_count", "Fluctuation Rate vs avg_word_count", fr_min, fr_max, awc_min, awc_max),
    ("FR_2", "avg_word_count", "Fluctuation Rate 2 vs avg_word_count", fr2_min, fr2_max, awc_min, awc_max),
    ("FR", "RSD", "FR vs RSD", fr_min, fr_max, 0, 0.13),
    ("FR", "accuracy_A", "FR vs accuracy_A", fr_min, fr_max, acc_min, acc_max),
    ("FR", "accuracy_B", "FR vs accuracy_B", fr_min, fr_max, acc_min, acc_max),
    ("FR", "accuracy_C", "FR vs accuracy_C", fr_min, fr_max, acc_min, acc_max),
    ("FR", "accuracy_D", "FR vs accuracy_D", fr_min, fr_max, acc_min, acc_max)
]

for target in targets:
    pertask = Analyze(target[0], target[1], target[2], columns)
    pertask.draw_plot(plot_specs)
