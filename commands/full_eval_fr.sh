python experiments/run_experiment.py \
--model_family mistral \
--model_name mistral-small-latest \
--language fr \
--prompt_format json \
--subtasks all \
--num_questions 100 \
--num_permutations 24 \
--output_file mistral_all_fr_json_n100p24.jsonl \
--delay 2
