#run_exp.sh
#!/bin/bash

JSON_FILE="commands/params.json"
ENTRY_SCRIPT="commands/run_exp_entry.sh"

DEFAULT_MODEL_FAMILY="gemini"
DEFAULT_MODEL_NAME="gemini-2.0-flash-lite"
DEFAULT_PROMPT_FORMAT="base"
DEFAULT_OUTPUT_FORMAT="base"
DEFAULT_LANGUAGE="en"
DEFAULT_SUBTASK="abstract_algebra"
DEFAULT_NUM_QUESTIONS=1
DEFAULT_NUM_PERMUTATIONS=1
DEFAULT_NUM_PERMUTATIONS="factorial"
DEFAULT_OUTPUT_FILE="default.jsonl"
DEFAULT_DELAY=2

SETUP_EVAL=0

print_help() {
  echo "Usage: commands/run_exp.sh [id1 id2 ...] [--language] [--format] [--key value ...]"
  echo
  echo "Runs one or more experiments defined in $JSON_FILE using their ID."
  echo "If no ID is provided, a default small experiment will be executed."
  echo
  echo "Language Options (required unless default used):"
  echo "  --en                Use English prompts"
  echo "  --fr                Use French prompts"
  echo
  echo "Prompt Format Options:"
  echo "  --i-base              Plain text prompt format"
  echo "  --i-json              JSON-based prompt format"
  echo "  --i-xml               XML-based prompt format"
  echo
  echo "Output Format Options:"
  echo "  --o-base              Plain text prompt format"
  echo "  --o-json              JSON-based prompt format"
  echo "  --o-xml               XML-based prompt format"
  echo
  echo "Execution Control:"
  echo "  --dry-run           Print the full command without executing"
  echo "  --key value         Manually override additional arguments to the entry script"
  echo "                      Example: --num_questions 5 --delay 0"
  echo
  echo "Evaluation Presets (override ID list):"
  echo "  t\$q\$p\$ stands for # of subtasks/questions/permutations. t1 runs abstrackt_algebra."
  echo "  --default-t1q1p1-gemini       Run pre-defined tiny Gemini evaluation"
  echo "  --default-t1q1p1-mistral      Run pre-defined tiny Mistral evaluation"
  echo "  --default-t1q1p1-gemini       Run pre-defined tiny Gemini evaluation"
  echo "  --default-t1q1p1-gemini       Run pre-defined tiny Gemini evaluation"
  echo "  --default-t1q1p1-gemini       Run pre-defined tiny Gemini evaluation"
  echo
  echo "Metadata Browsing:"
  echo "  --list              Show the first 15 available experiments with IDs"
  echo "  --list all          Show all experiments"
  echo
  echo "  --search <kw1> [kw2 ...] [all]   Search experiments matching ALL keywords."
  echo "                                   Keywords search across: exp_name, model_name,"
  echo "                                   subtask, num_questions, permutation_type,"
  echo "                                   num_permutations, delay."
  echo "                                   You may also specify field-specific filters:"
  echo "                                     field:value (e.g. model_name:gemini)"
  echo "                                   Examples:"
  echo "                                     --search algebra"
  echo "                                     --search gemini 24"
  echo "                                     --search num_questions:10 model_name:gemini"
  echo "                                     --search delay:1 all"
  echo
}

# Handle help
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  print_help
  exit 0
fi

# Handle list
if [[ "$1" == "--list" ]]; then
  MODE="$2"
  TOTAL=$(jq length "$JSON_FILE")

  if [[ "$MODE" == "all" ]]; then
    echo "Listing all $TOTAL experiments:"
    jq -r '
      ["id", "model_name", "subtask", "#_questions", "permutation_type", "#_permutations", "delay"],
      (to_entries | map(select(.value | type == "object")) | .[] | [ .key, .value.model_name, .value.subtask, .value.num_questions, .value.permutation_type, .value.num_permutations, .value.delay ])
      | @tsv
    ' "$JSON_FILE" | column -t
  else
    echo "Showing first 15 of $TOTAL experiments:"
    jq -r '
      ["id", "model_name", "subtask", "#_questions", "permutation_type", "#_permutations", "delay"],
      (to_entries | map(select(.value | type == "object")) | .[] | [ .key, .value.model_name, .value.subtask, .value.num_questions, .value.permutation_type, .value.num_permutations, .value.delay ])
      | @tsv
    ' "$JSON_FILE" | head -n 16 | column -t
    echo "(Use --list all to see full list)"
  fi

  exit 0
fi

# Handle Search
if [[ "$1" == "--search" ]]; then
  shift

  if [[ "$#" -eq 0 ]]; then
    echo "Error: Please provide one or more keywords to search."
    exit 1
  fi

  SHOW_ALL=0
  if [[ "${@: -1}" == "all" ]]; then
    SHOW_ALL=1
    set -- "${@:1:$(($#-1))}"  # remove "all"
  fi

  echo "Searching for experiments matching: $*"

  SEARCHABLE_FIELDS=("exp_name" "model_name" "subtask" "num_questions" "permutation_type" "num_permutations" "delay")
  JQ_FILTER='true'

  for raw_kw in "$@"; do
    if [[ "$raw_kw" == *:* ]]; then
      # Field-specific query: field:value
      field="${raw_kw%%:*}"
      value="${raw_kw#*:}"
      # ALLOWED_FIELDS=("exp_name" "model_name" "subtask" "difficulty" "version" "seed")
      if [[ " ${SEARCHABLE_FIELDS[*]} " != *" $field "* ]]; then
        echo "Warning: unsupported field '$field'"
        continue
      fi
      JQ_FILTER="$JQ_FILTER and (.value.$field // \"\" | test(\"$value\"; \"i\"))"
    else
      # General fallback query (across all searchable fields)
      OR_GROUP=""
      for f in "${SEARCHABLE_FIELDS[@]}"; do
        OR_GROUP="$OR_GROUP (.value.$f // \"\" | test(\"$raw_kw\"; \"i\")) or"
      done
      OR_GROUP="${OR_GROUP%or}"  # remove trailing 'or'
      JQ_FILTER="$JQ_FILTER and ($OR_GROUP)"
    fi
  done

  JQ_CMD='["id", "model_name", "subtask", "#_questions", "permutation_type", "#_permutations", "delay"],
  (to_entries
   | map(select(.value | type == "object"))
   | .[]
   | select('"$JQ_FILTER"')
   | [ .key, .value.model_name, .value.subtask, .value.num_questions, .value.permutation_type, .value.num_permutations, .value.delay ]) | @tsv'

  OUTPUT=$(jq -r "$JQ_CMD" "$JSON_FILE")

  if [ "$SHOW_ALL" -eq 1 ]; then
    echo "$OUTPUT" | column -t
  else
    MATCHED=$(echo "$OUTPUT" | wc -l)
    SHOWN=$(( MATCHED < 17 ? MATCHED : 16 ))  # header + 15 rows
    echo "$OUTPUT" | head -n "$SHOWN" | column -t
    if [ "$MATCHED" -gt 16 ]; then
      echo "(Showing first 15 of $((MATCHED-1)) matches. Use '--search ... all' to show all.)"
    fi
  fi

  exit 0
fi


# Parse exp_names and overrides
EXP_NAMES=()
OVERRIDES=()

while [[ "$1" != "" ]]; do
  case "$1" in
    --default-t1q1p1-mistral)
      SETUP_EVAL=1
      EXP_NAME="default-t1q1p1-mistral"
      shift
      ;;
    --default-t1q1p24-mistral)
      SETUP_EVAL=2
      EXP_NAME="default-t1q1p24-mistral"
      shift
      ;;
    --default-t17q1p1-mistral)
      SETUP_EVAL=3
      EXP_NAME="default-t17q1p1-mistral"
      shift
      ;;
    ----default-t1q100p24-mistral)
      SETUP_EVAL=4
      EXP_NAME="default-t1q100p24-mistral"
      shift
      ;;
    --default-t17q1p100-mistral)
      SETUP_EVAL=5
      EXP_NAME="default-t17q1p100-mistral"
      shift
      ;;
    --default-t1q1p1-gemini)
      SETUP_EVAL=6
      EXP_NAME="default-t1q1p1-gemini"
      shift
      ;;
    --default-t1q1p24-gemini)
      SETUP_EVAL=7
      EXP_NAME="default-t1q1p24-gemini"
      shift
      ;;
    --default-t17q1p1-gemini)
      SETUP_EVAL=8
      EXP_NAME="default-t17q1p1-gemini"
      shift
      ;;
    ----default-t1q100p24-gemini)
      SETUP_EVAL=9
      EXP_NAME="default-t1q100p24-gemini"
      shift
      ;;
    --default-t17q1p100-gemini)
      SETUP_EVAL=10
      EXP_NAME="default-t17q1p100-gemini"
      shift
      ;;
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
    --i-base)
      OVERRIDES+=("--prompt_format" "base")
      shift
      ;;
    --i-xml)
      OVERRIDES+=("--prompt_format" "xml")
      shift
      ;;
    --i-json)
      OVERRIDES+=("--prompt_format" "json")
      shift
      ;;
    --o-base)
      OVERRIDES+=("--output_format" "base")
      shift
      ;;
    --o-xml)
      OVERRIDES+=("--output_format" "xml")
      shift
      ;;
    --o-json)
      OVERRIDES+=("--output_format" "json")
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

if [ $SETUP_EVAL != 0 ]; then
  # EXP_NAME=""

  # if [$SETUP_EVAL > 5]; then
  #   SETUP_EVAL=$SETUP_EVAL - 5
  #   model_family="gemini"
  #   model_name="gemini-2.0-flash-lite"
  # else
  #   model_family="mistral"
  #   model_name="mistral-small-latest"
  # fi

  
  echo "Running experiment: $EXP_NAME"

  JQ_BASE=".[] | select(.exp_name == \"$EXP_NAME\")"

  model_family=$(jq -r "$JQ_BASE | .model_family // \"\"" "$JSON_FILE")
  model_name=$(jq -r "$JQ_BASE | .model_name // \"\"" "$JSON_FILE")
  language=$(jq -r "$JQ_BASE | .language // \"\"" "$JSON_FILE")
  prompt_format=$(jq -r "$JQ_BASE | .prompt_format // \"\"" "$JSON_FILE")
  output_format=$(jq -r "$JQ_BASE | .output_format // \"\"" "$JSON_FILE")
  subtask=$(jq -r "$JQ_BASE | .subtask // \"\"" "$JSON_FILE")
  output_file=$(jq -r "$JQ_BASE | .output_file // \"\"" "$JSON_FILE")
  num_questions=$(jq -r "$JQ_BASE | .num_questions // \"\"" "$JSON_FILE")
  permutation_type=$(jq -r "$JQ_BASE | .permutation_type // \"\"" "$JSON_FILE")
  num_permutations=$(jq -r "$JQ_BASE | .num_permutations // \"\"" "$JSON_FILE")
  delay=$(jq -r "$JQ_BASE | .delay // \"\"" "$JSON_FILE")

  language="${language:-$DEFAULT_LANGUAGE}"
  prompt_format="${prompt_format:-$DEFAULT_PROMPT_FORMAT}"
  output_format="${output_format:-$DEFAULT_OUTPUT_FORMAT}"

  bash "$ENTRY_SCRIPT" \
            --model_family "$model_family" \
            --model_name "$model_name" \
            --language "$language" \
            --prompt_format "$prompt_format" \
            --output_format "$output_format" \
            --subtask "$subtask" \
            --output_file "$output_file" \
            --num_questions "$num_questions" \
            --permutation_type "$permutation_type" \
            --num_factorial_permutations "$num_permutations" \
            --delay "$delay" \
            "${OVERRIDES[@]}"

  exit 0
fi

if [ ${#EXP_NAMES[@]} -eq 0 ]; then
  bash "$ENTRY_SCRIPT" \
    --model_family "gemini" \
    --model_name "gemini-2.0-flash-lite" \
    --language "en" \
    --prompt_format "base" \
    --output_format "base" \
    --subtask "abstract_algebra" \
    --output_file "default.jsonl" \
    --num_questions "1" \
    --permutation_type "factorial" \
    --num_factorial_permutations "1" \
    --delay "2" \
    "${OVERRIDES[@]}"

  exit 0

else
    for EXP_NAME in "${EXP_NAMES[@]}"; do
        echo "Running experiment: #$EXP_NAME"

        # JQ_BASE=".[] | select(.id == \"$EXP_NAME\")"
        JQ_BASE=".[$EXP_NAME]"

        model_family=$(jq -r "$JQ_BASE | .model_family // \"\"" "$JSON_FILE")
        model_name=$(jq -r "$JQ_BASE | .model_name // \"\"" "$JSON_FILE")
        language=$(jq -r "$JQ_BASE | .language // \"\"" "$JSON_FILE")
        prompt_format=$(jq -r "$JQ_BASE | .prompt_format // \"\"" "$JSON_FILE")
        output_format=$(jq -r "$JQ_BASE | .output_format // \"\"" "$JSON_FILE")
        subtask=$(jq -r "$JQ_BASE | .subtask // \"\"" "$JSON_FILE")
        output_file=$(jq -r "$JQ_BASE | .output_file // \"\"" "$JSON_FILE")
        num_questions=$(jq -r "$JQ_BASE | .num_questions // \"\"" "$JSON_FILE")
        num_permutations=$(jq -r "$JQ_BASE | .num_permutations // \"\"" "$JSON_FILE")
        permutation_type=$(jq -r "$JQ_BASE | .permutation_type // \"\"" "$JSON_FILE")
        delay=$(jq -r "$JQ_BASE | .delay // \"\"" "$JSON_FILE")

        # Provide fallbacks for missing values (only if variable is empty)
        model_family="${model_family:-$DEFAULT_MODEL_FAMILY}"
        model_name="${model_name:-$DEFAULT_MODEL_NAME}"
        language="${language:-$DEFAULT_LANGUAGE}"
        prompt_format="${prompt_format:-$DEFAULT_PROMPT_FORMAT}"
        output_format="${output_format:-$DEFAULT_OUTPUT_FORMAT}"
        subtask="${subtask:-$DEFAULT_SUBTASK}"
        output_file="${output_file:-}"
        num_questions="${num_questions:-$DEFAULT_NUM_PERMUTATIONS}"
        num_permutations="${num_permutations:-$DEFAULT_NUM_QUESTIONS}"
        permutation_type="${permutation_type:-$DEFAULT_NUM_PERMUTATIONS}"
        delay="${delay:-$DEFAULT_DELAY}"

        # Call entry script with base parameters and additional overrides
        bash "$ENTRY_SCRIPT" \
            --model_family "$model_family" \
            --model_name "$model_name" \
            --language "$language" \
            --prompt_format "$prompt_format" \
            --output_format "$output_format" \
            --subtask "$subtask" \
            --output_file "$output_file" \
            --permutation_type "$permutation_type" \
            --num_questions "$num_questions" \
            --num_factorial_permutations "$num_permutations" \
            --delay "$delay" \
            "${OVERRIDES[@]}"

    done

fi

