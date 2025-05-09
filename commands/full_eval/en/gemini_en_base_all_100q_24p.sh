        #!/bin/bash

        # Full Eval: Gemini, English, base prompt, ALL (17 selected) subtasks, 100 questions each, 24 permutations
        # Results will be saved in results/full_eval_outputs/en/

        SCRIPT_DIR=$(cd $(dirname "$0") && pwd)
        PROJECT_ROOT=$(cd "$SCRIPT_DIR/../../../" && pwd) # Note: one more ../
        OUTPUT_DIR="$PROJECT_ROOT/results/full_eval_outputs/en"
        mkdir -p "$OUTPUT_DIR" # Ensure output directory exists

        python "$PROJECT_ROOT/experiments/run_experiment.py" \
            --model_family gemini \
            --model_name gemini-2.0-flash-lite \
            --language en \
            --prompt_format base \
            --subtasks all \
            --num_questions 100 \
            --num_permutations 24 \
            --output_dir "results/full_eval_outputs/en" \
            --output_file "gemini_en_base_all_100q_24p.jsonl" \
            --delay 3.0

        echo "Full evaluation script for Gemini EN Base completed. Output in $OUTPUT_DIR/gemini_en_base_all_100q_24p.jsonl"
        