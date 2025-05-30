#!/bin/bash
# Test all 9 format combinations

formats=("base" "json" "xml")

for in_fmt in "${formats[@]}"; do
    for out_fmt in "${formats[@]}"; do
        echo "Testing input=$in_fmt, output=$out_fmt"
        
        python experiments/run_experiment_new.py \
            --model_family gemini \
            --model_name gemini-1.5-flash-latest \
            --language en \
            --prompt_format $in_fmt \
            --output_format $out_fmt \
            --subtasks abstract_algebra \
            --num_questions 1 \
            --permutation_type circular \
            --output_dir test_formats \
            --output_file "test_${in_fmt}_${out_fmt}.jsonl" \
            --delay 0.5
        
        if [ $? -ne 0 ]; then
            echo "❌ Failed for $in_fmt -> $out_fmt"
            exit 1
        fi
    done
done

echo "✅ All format combinations work!"