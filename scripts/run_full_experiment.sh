#!/bin/bash
# Full Experiment Runner for NLP Team 9

SUBTASKS=(
    "abstract_algebra" "anatomy" "astronomy" "business_ethics"
    "college_biology" "college_chemistry" "college_computer_science"
    "econometrics" "electrical_engineering" "formal_logic"
    "global_facts" "high_school_european_history"
    "high_school_geography" "high_school_government_and_politics"
    "high_school_psychology" "human_sexuality" "international_law"
)

MODELS=("gemini-2.0-flash-lite" "mistral-small-latest")

echo "Starting Full MMMLU Order Sensitivity Experiment"
echo "==============================================="

for model in "${MODELS[@]}"; do
    for subtask in "${SUBTASKS[@]}"; do
        echo "Running $subtask with $model..."
        
        # English
        python cli.py run --subtask "$subtask" --model "$model" --format all --en
        
        # French
        python cli.py run --subtask "$subtask" --model "$model" --format all --fr
        
        sleep 2
    done
done

echo "All experiments submitted!"
