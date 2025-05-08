#!/bin/bash

JSON_FILE="commands/result.json"
ENTRY_SCRIPT="commands/run_exp_entry.sh"
DEFAULT_EXP_NAME="gemini_fr_algebra"

DEFAULT_MODEL_FAMILY="gemini"
DEFAULT_MODEL_NAME="gemini-2.0-flash-lite"
DEFAULT_PROMPT_FORMAT="base"
DEFAULT_LANGUAGE="en"
DEFAULT_SUBTASK="all"
DEFAULT_NUM_QUESTIONS=1
DEFAULT_NUM_PERMUTATIONS=1
DEFAULT_OUTPUT_FILE=""
DEFAULT_DELAY=2


print_help() {
  echo "Usage: commands/run_exp.sh [exp_name1 exp_name2 ...] --{lang} --{format} [--key value ...]"
  echo
  echo "If no exp_name is provided, the small experiment will be executed, but you can still manually specify values"
  echo "If no lang/format specified, default would be fr/base"
  echo "Options:"
  echo "  -h, --help             Show this help message"
  echo "  --list                 List all available experiment names"
  echo "  --{lang}               Set experiment's language."
  echo "    --en                 for English"
  echo "    --fr                 for French"
  echo "  --{format}             Set prompt's format."
  echo "    --base               for plain text"
  echo "    --json               for JSON format"
  echo "    --xml                for XML format"
  echo "  --key value            Manual setting for some specific keysto the experiment script"
  echo "  --dry-run              Show the command that would be executed, without actually running it."
}

# Handle help
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  print_help
  exit 0
fi

# Handle list
if [[ "$1" == "--list" ]]; then
  jq -r '.[].exp_name' "$JSON_FILE"
  exit 0
fi

# Parse exp_names and overrides
EXP_NAMES=()
OVERRIDES=()

while [[ "$1" != "" ]]; do
  case "$1" in
    --fr)
      OVERRIDES+=("--language" "fr")
      shift
      ;;
    --en)
      OVERRIDES+=("--language" "en")
      shift
      ;;
    --base)
      OVERRIDES+=("--prompt_format" "base")
      shift
      ;;
    --xml)
      OVERRIDES+=("--prompt_format" "xml")
      shift
      ;;
    --json)
      OVERRIDES+=("--prompt_format" "json")
      shift
      ;;
    --dry-run)
      OVERRIDES+=("--dry-run")
      shift
      ;;
    --*) OVERRIDES+=("$1" "$2")
      shift 2
      ;;
    *)   EXP_NAMES+=("$1")
      shift
      ;;
  esac
done

if [ ${#EXP_NAMES[@]} -eq 0 ]; then
#   EXP_NAMES=("$DEFAULT_EXP_NAME")
  bash "$ENTRY_SCRIPT" \
    --model_family "gemini" \
    --model_name "gemini-2.0-flash-lite" \
    --language "fr" \
    --prompt_format "base" \
    --subtask "abstract_algebra" \
    --output_file "" \
    --num_questions "1" \
    --num_permutations "1" \
    --delay "2" \
    "${OVERRIDES[@]}"

  exit 0

else
    for EXP_NAME in "${EXP_NAMES[@]}"; do
        echo "Running experiment: $EXP_NAME"

        JQ_BASE=".[] | select(.exp_name == \"$EXP_NAME\")"

        model_family=$(jq -r "$JQ_BASE | .model_family // \"\"" "$JSON_FILE")
        model_name=$(jq -r "$JQ_BASE | .model_name // \"\"" "$JSON_FILE")
        language=$(jq -r "$JQ_BASE | .language // \"\"" "$JSON_FILE")
        prompt_format=$(jq -r "$JQ_BASE | .prompt_format // \"\"" "$JSON_FILE")
        subtask=$(jq -r "$JQ_BASE | .subtask // \"\"" "$JSON_FILE")
        output_file=$(jq -r "$JQ_BASE | .output_file // \"\"" "$JSON_FILE")
        num_questions=$(jq -r "$JQ_BASE | .num_questions // \"\"" "$JSON_FILE")
        num_permutations=$(jq -r "$JQ_BASE | .num_permutations // \"\"" "$JSON_FILE")
        delay=$(jq -r "$JQ_BASE | .delay // \"\"" "$JSON_FILE")

        # Provide fallbacks for missing values (only if variable is empty)
        model_family="${model_family:-$DEFAULT_MODEL_FAMILY}"
        model_name="${model_name:-$DEFAULT_MODEL_NAME}"
        language="${language:-$DEFAULT_LANGUAGE}"
        prompt_format="${prompt_format:-$DEFAULT_PROMPT_FORMAT}"
        subtask="${subtask:-$DEFAULT_SUBTASK}"
        output_file="${output_file:-}"
        num_questions="${num_questions:-$DEFAULT_NUM_PERMUTATIONS}"
        num_permutations="${num_permutations:-$DEFAULT_NUM_QUESTIONS}"
        delay="${delay:-$DEFAULT_DELAY}"

        # Call entry script with base parameters and additional overrides
        bash "$ENTRY_SCRIPT" \
            --model_family "$model_family" \
            --model_name "$model_name" \
            --language "$language" \
            --prompt_format "$prompt_format" \
            --subtask "$subtask" \
            --output_file "$output_file" \
            --num_questions "$num_questions" \
            --num_permutations "$num_permutations" \
            --delay "$delay" \
            "${OVERRIDES[@]}"

    done

fi

