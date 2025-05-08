python experiments/run_experiment.py \
--model_family gemini \
--model_name gemini-2.0-flash-lite \
--language fr \
--prompt_format base \
--subtasks abstract_algebra anatomy\
--num_questions 1 \
--num_permutations 1 \
--output_file test_output.jsonl \
--delay 2
