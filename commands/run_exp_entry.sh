#!/bin/bash

# Default values
MODEL_FAMILY="gemini"
MODEL_NAME="gemini-2.0-flash-lite"
PROMPT_FORMAT="base"
LANGUAGE="en"
SUBTASK="abstract_algebra"
NUM_QUESTIONS=1
NUM_PERMUTATIONS=1
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
    --num_questions) NUM_QUESTIONS="$2"; shift ;;
    --num_permutations) NUM_PERMUTATIONS="$2"; shift ;;
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
if [[ -z "$OUTPUT_FILE" || "$OUTPUT_FILE" == "None" ]]; then
  timestamp=$(date +"%Y%m%d-%H%M%S")
  OUTPUT_FILE="${MODEL_NAME}_${LANGUAGE}_${PROMPT_FORMAT}_${timestamp}.jsonl"
else
  if [[ "$OUTPUT_FILE" != *.jsonl ]]; then
    timestamp=$(date +"%Y%m%d-%H%M%S")
    OUTPUT_FILE="${OUTPUT_FILE}_${timestamp}.jsonl"
  fi
fi

# Dry-run display
if [ "$DRY_RUN" -eq 1 ]; then
  echo "Dry-run: would execute:"
  echo "python experiments/run_experiment.py \\"

  keys=(--model_family --model_name --language --prompt_format --subtasks \
        --num_questions --num_permutations --output_file --delay)
  values=("$MODEL_FAMILY" "$MODEL_NAME" "$LANGUAGE" "$PROMPT_FORMAT" "$SUBTASK" \
          "$NUM_QUESTIONS" "$NUM_PERMUTATIONS" "$OUTPUT_FILE" "$DELAY")

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
  --subtasks "$SUBTASK" \
  --num_questions "$NUM_QUESTIONS" \
  --num_permutations "$NUM_PERMUTATIONS" \
  --output_file "$OUTPUT_FILE" \
  --delay "$DELAY"


echo "Full evaluation script for $MODEL_FAMILY $LANGUAGE $PROMPT_FORMAT completed."
echo "Output in results/$OUTPUT_FILE"
