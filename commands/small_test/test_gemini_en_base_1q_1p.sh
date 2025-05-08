        #!/bin/bash

        # Small test: Gemini, English, base prompt, abstract_algebra, 1 question, 1 permutation
        # Results will be saved in results/small_test_outputs/

        SCRIPT_DIR=$(cd $(dirname "$0") && pwd)
        PROJECT_ROOT=$(cd "$SCRIPT_DIR/../../" && pwd)
        OUTPUT_DIR="$PROJECT_ROOT/results/small_test_outputs"
        mkdir -p "$OUTPUT_DIR" # Ensure output directory exists

        python "$PROJECT_ROOT/experiments/run_experiment.py" \
            --model_family gemini \
            --model_name gemini-2.0-flash-lite \
            --language en \
            --prompt_format base \
            --subtasks abstract_algebra \
            --num_questions 1 \
            --num_permutations 1 \
            --output_dir "results/small_test_outputs" \
            --output_file "test_gemini_en_base_1q_1p.jsonl" \
            --delay 1

        echo "Small test completed. Output in $OUTPUT_DIR/test_gemini_en_base_1q_1p.jsonl"
        