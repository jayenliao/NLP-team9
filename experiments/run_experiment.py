# experiments/run_experiment.py
import logging
import sys
import os
import argparse
import json
import time
import itertools

from core_runner import (
    load_prompt_template, format_prompt, parse_response,
    structure_result, get_api_client, call_llm_api
)
from utils import load_prepared_dataset, load_api_keys

# --- Restored Basic Logging Setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Define log file path relative to this script's location -> project root -> logs/
log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'experiment.log')
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
# Prevent adding handlers multiple times if script/module is reloaded
if not logger.handlers:
    # Console Handler
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.INFO)
    # File Handler
    f_handler = logging.FileHandler(log_file_path)
    f_handler.setLevel(logging.INFO)
    # Formatter
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    c_handler.setFormatter(log_format)
    f_handler.setFormatter(log_format)
    # Add Handlers to Logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
# --- End Logging Setup ---


def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Run LLM evaluation experiments for order sensitivity.")
    parser.add_argument("--model_family", type=str, required=True, choices=['gemini', 'mistral'], help="LLM family ('gemini' or 'mistral').")
    parser.add_argument("--model_name", type=str, required=True, help="Specific model name (e.g., 'gemini-1.5-flash-latest', 'mistral-small-latest').")
    parser.add_argument("--language", type=str, default='en', choices=['en', 'fr'], help="Language code ('en' or 'fr').")
    parser.add_argument("--prompt_format", type=str, default='base', choices=['base', 'json', 'xml'], help="Prompt format ('base', 'json', 'xml').")
    parser.add_argument("--subtasks", type=str, default='all', help="Comma-separated list of subtasks, or 'all'.")
    parser.add_argument("--num_questions", type=int, default=100, help="Number of questions per subtask.")
    parser.add_argument("--start_index", type=int, default=0, help="0-based index of the first question.")
    parser.add_argument("--output_dir", type=str, default='results', help="Directory to save results files.")
    parser.add_argument("--output_file", type=str, default=None, help="Specific name for the output JSONL file.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds between API calls.")

    args = parser.parse_args()
    logger.info(f"Starting experiment with arguments: {args}") # Restored Log

    # --- Initialization ---
    logger.info("----- Initializing -----") # Restored Log
    load_api_keys()
    client = get_api_client(args.model_family)
    if not client:
        print(f"Fatal: Failed to initialize API client for {args.model_family}.") # Keep fatal error print
        return

    full_dataset = load_prepared_dataset()
    if not full_dataset:
        print("Fatal: Failed to load prepared dataset.") # Keep fatal error print
        return

    template_content = load_prompt_template(args.prompt_format)
    if not template_content:
        print(f"Fatal: Failed to load prompt template '{args.prompt_format}'.") # Keep fatal error print
        return

    # --- Determine Subtasks ---
    if args.subtasks.lower() == 'all':
        subtasks_to_run = list(full_dataset.keys())
    else:
        requested_subtasks = args.subtasks.split(',')
        subtasks_to_run = [st for st in requested_subtasks if st in full_dataset]
        if not subtasks_to_run:
            print("Fatal: No valid subtasks found in the dataset.") # Keep fatal error print
            return
    logger.info(f"Running specified subtasks: {subtasks_to_run}") # Restored Log

    # --- Prepare Output File ---
    if args.output_file is None:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{args.model_family}_{args.model_name}_{args.language}_{args.prompt_format}_{timestamp}.jsonl"
    else:
        filename = args.output_file if args.output_file.endswith(".jsonl") else f"{args.output_file}.jsonl"

    output_path_dir = os.path.join(os.path.dirname(__file__), '..', args.output_dir)
    os.makedirs(output_path_dir, exist_ok=True)
    output_path = os.path.join(output_path_dir, filename)
    # Use os.path.abspath for a clearer log message
    # logger.info(f"Results will be saved to: {os.path.abspath(output_path)}")
    logger.info(f"Results will be saved to: {output_path}") # Restored Log (using original relative path style)


    # --- Main Experiment Loop ---
    logger.info("----- Starting Experiment Loop -----")
    total_processed_count = 0
    try:
        with open(output_path, 'a', encoding='utf-8') as f_out:
            for subtask in subtasks_to_run:
                logger.info(f"--- Processing Subtask: {subtask} ---") # Restored Log

                if subtask not in full_dataset or args.language not in full_dataset[subtask]:
                    continue

                task_data = full_dataset[subtask][args.language]
                end_index = min(args.start_index + args.num_questions, len(task_data))

                if args.start_index >= len(task_data) or args.start_index >= end_index:
                     continue

                logger.info(f"Processing questions {args.start_index} to {end_index - 1} (inclusive).") # Restored Log

                for i in range(args.start_index, end_index):
                    data_item = task_data[i]
                    question_index_in_run = i

                    logger.info(f"Processing {subtask} - {args.language} - Question Index: {question_index_in_run}") # Restored Log

                    option_order = ['A', 'B', 'C', 'D']

                    # 1. Format Prompt
                    current_prompt = format_prompt(template_content, data_item, option_order)
                    if not current_prompt:
                        continue

                    # 2. Call LLM API
                    api_response, api_ok = call_llm_api(client, args.model_family, args.model_name, current_prompt)

                    # 3. Parse Response
                    parsed_answer = None
                    if api_ok and api_response:
                        response_text = None
                        try:
                            if args.model_family == 'gemini':
                               response_text = api_response.text
                            elif args.model_family == 'mistral':
                                response_text = api_response.choices[0].message.content
                        except Exception:
                            pass

                        if response_text:
                            parsed_answer = parse_response(response_text)

                    # 4. Structure Result
                    result_dict = structure_result(
                        data_item=data_item,
                        subtask=subtask,
                        language=args.language,
                        model_name=args.model_name,
                        input_format=args.prompt_format,
                        option_permutation=option_order,
                        api_raw_response=api_response,
                        api_call_successful=api_ok,
                        extracted_answer=parsed_answer,
                        log_probabilities=None,
                        question_index=question_index_in_run
                    )

                    # 5. Save Result
                    try:
                        json_string = json.dumps(result_dict, ensure_ascii=False)
                        f_out.write(json_string + '\n')
                        total_processed_count += 1
                    except Exception as e:
                        # Add minimal error logging for write failure if needed
                        # logger.error(f"Failed to write result for index {question_index_in_run}: {e}")
                        pass # Continue processing other questions

                    # 6. Delay
                    if args.delay > 0:
                        time.sleep(args.delay)

                logger.info(f"--- Finished Subtask: {subtask} ---") # Restored Log

    except Exception as e:
         # Log general errors during the loop execution
         logger.error(f"An unexpected error occurred during the experiment loop: {e}", exc_info=True) # Use logger.error for loop errors
    finally:
        logger.info("----- Experiment Loop Finished -----") # Restored Log
        logger.info(f"Total questions processed and saved: {total_processed_count}") # Restored Log


if __name__ == "__main__":
    main()

"""
    --- How to run base case in terminal ---
    python experiments/run_experiment.py \
    --model_family gemini \
    --model_name gemini-1.5-flash-latest \
    --language en \
    --prompt_format base \
    --subtasks abstract_algebra \
    --num_questions 5 \
    --output_file base_case_run.jsonl \
    --delay 2
    
    """
