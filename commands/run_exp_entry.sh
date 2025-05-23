#!/bin/bash

# Default values
MODEL_FAMILY="gemini"
MODEL_NAME="gemini-2.0-flash-lite"
PROMPT_FORMAT="base"
OUTPUT_FORMAT="base"
LANGUAGE="en"
SUBTASK="abstract_algebra"
NUM_QUESTIONS=1
NUM_PERMUTATIONS=1
PERMUTATION_TYPE="factorial"
OUTPUT_FILE="default.jsonl"
DELAY=2
DRY_RUN=0

# Parse arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --model_family) MODEL_FAMILY="$2"; shift ;;
    --model_name) MODEL_NAME="$2"; shift ;;
    --language) LANGUAGE="$2"; shift ;;
    --subtask) SUBTASK="$2"; shift ;;
    --output_file) OUTPUT_FILE="$2"; shift ;;
    --prompt_format) PROMPT_FORMAT="$2"; shift ;;
    --output_format) OUTPUT_FORMAT="$2"; shift ;;
    --num_questions) NUM_QUESTIONS="$2"; shift ;;
    --num_factorial_permutations) NUM_PERMUTATIONS="$2"; shift ;;
    --permutation_type) PERMUTATION_TYPE="$2"; shift ;;
    --delay) DELAY="$2"; shift ;;
    --dry-run) DRY_RUN=1 ;;
    *) echo "Warning: Unknown argument: $1";;
  esac
  shift
done

# # Required parameters check
# if [[ -z "$MODEL_NAME" || -z "$LANGUAGE" || -z "$SUBTASK" ]]; then
#   echo "Error: Missing required parameters."
#   echo "Required: --model_name, --language, --subtask"
#   exit 1
# fi

# Determine final output file name
if [[ "$OUTPUT_FILE" = "" ]]; then
  timestamp=$(date +"%Y%m%d-%H%M%S")
  OUTPUT_DIR="${MODEL_NAME}_${LANGUAGE}_i-${PROMPT_FORMAT}_o-${OUTPUT_FORMAT}_${PERMUTATION_TYPE}_${timestamp}"
else
  timestamp=$(date +"%Y%m%d-%H%M%S")
  OUTPUT_DIR="${OUTPUT_FILE}_${timestamp}"
fi
# Dry-run display
if [ "$DRY_RUN" -eq 1 ]; then
  echo "Dry-run: would execute:"
  echo "python experiments/run_experiment.py \\"
  keys=(--model_family --model_name --language --prompt_format --output_format --subtasks \
        --num_questions --permutation_type --num_factorial_permutations --output_dir --output_file --delay)
  values=("$MODEL_FAMILY" "$MODEL_NAME" "$LANGUAGE" "$PROMPT_FORMAT" "$OUTPUT_FORMAT" "$SUBTASK" \
          "$NUM_QUESTIONS" "$PERMUTATION_TYPE" "$NUM_PERMUTATIONS" "$OUTPUT_DIR" "raw.jsonl" "$DELAY")

  for ((i = 0; i < ${#keys[@]}; i++)); do
    key="${keys[$i]}"
    val="${values[$i]}"
    if [ $i -lt $((${#keys[@]} - 1)) ]; then
      echo "$key $val \\"
    else
      echo "$key $val"
    fi
  done

  exit 0
fi


# Run the experiment
python experiments/run_experiment.py \
  --model_family "$MODEL_FAMILY" \
  --model_name "$MODEL_NAME" \
  --language "$LANGUAGE" \
  --prompt_format "$PROMPT_FORMAT" \
  --output_format "$OUTPUT_FORMAT" \
  --subtasks "$SUBTASK" \
  --num_questions "$NUM_QUESTIONS" \
  --permutation_type "$PERMUTATION_TYPE" \
  --num_factorial_permutations "$NUM_PERMUTATIONS" \
  --output_dir "$OUTPUT_DIR" \
  --output_file "raw.jsonl" \
  --delay "$DELAY"


echo "Full evaluation script for $MODEL_FAMILY $LANGUAGE i:$PROMPT_FORMAT o:$OUTPUT_FORMAT completed."
echo "Output in results/$OUTPUT_DIR/$OUTPUT_FILE"
