# experiments/run_experiment.py
import logging
import sys
import os
import argparse
import json
import time
import itertools
from tqdm import tqdm

from core_runner import (
    load_prompt_template, format_prompt, parse_response,
    structure_result, get_api_client, call_llm_api
)
from utils import load_prepared_dataset, load_api_keys

# Logging Setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'experiment.log')
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
if not logger.handlers:
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.INFO)
    f_handler = logging.FileHandler(log_file_path)
    f_handler.setLevel(logging.INFO)
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    c_handler.setFormatter(log_format)
    f_handler.setFormatter(log_format)
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

def main():
    # Parse Arguments
    parser = argparse.ArgumentParser(description="Run LLM evaluation experiments for order sensitivity.")
    parser.add_argument("--model_family", type=str, required=True, choices=['gemini', 'mistral'], help="LLM family ('gemini' or 'mistral').")
    parser.add_argument("--model_name", type=str, required=True, help="Specific model name (e.g., 'gemini-1.5-flash-latest', 'mistral-small-latest').")
    parser.add_argument("--language", type=str, default='en', choices=['en', 'fr'], help="Language code ('en' or 'fr').")
    parser.add_argument("--prompt_format", type=str, default='base', choices=['base', 'json', 'xml'], help="Prompt format ('base', 'json', 'xml').")
    parser.add_argument("--subtasks", type=str, default='all', help="Comma-separated list of subtasks, or 'all'.")
    parser.add_argument("--num_questions", type=int, default=100, help="Number of questions per subtask.")
    parser.add_argument('--num_permutations', type=int, default=24, help='Number of option permutations to run per question (default: 24, max: 24)')
    parser.add_argument("--start_index", type=int, default=0, help="0-based index of the first question.")
    parser.add_argument("--output_dir", type=str, default='results', help="Directory to save results files.")
    parser.add_argument("--output_file", type=str, default=None, help="Specific name for the output JSONL file.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds between API calls.")

    args = parser.parse_args()
    logger.info(f"Starting experiment with args: {args}")

    # Initialize
    logger.info("Initializing")
    load_api_keys()
    client = get_api_client(args.model_family)
    if not client:
        print(f"Fatal: Failed to initialize API client for {args.model_family}.")
        return

    full_dataset = load_prepared_dataset()
    if not full_dataset:
        print("Fatal: Failed to load prepared dataset.")
        return

    template_content = load_prompt_template(args.prompt_format)
    if not template_content:
        print(f"Fatal: Failed to load prompt template '{args.prompt_format}'.")
        return

    # Determine Subtasks
    if args.subtasks.lower() == 'all':
        subtasks_to_run = list(full_dataset.keys())
    else:
        requested_subtasks = args.subtasks.split(',')
        subtasks_to_run = [st for st in requested_subtasks if st in full_dataset]
        if not subtasks_to_run:
            print("Fatal: No valid subtasks found in dataset.")
            return
    logger.info(f"Running subtasks: {subtasks_to_run}")

    # Prepare Output File
    if args.output_file is None:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{args.model_family}_{args.model_name}_{args.language}_{args.prompt_format}_{timestamp}.jsonl"
    else:
        print("output_file:", args.output_file)
        filename = args.output_file if args.output_file.endswith(".jsonl") else f"{args.output_file}.jsonl"
        print("real filename:", filename)
    output_path_dir = os.path.join(os.path.dirname(__file__), '..', args.output_dir)
    os.makedirs(output_path_dir, exist_ok=True)
    output_path = os.path.join(output_path_dir, filename)
    logger.info(f"Saving results to: {output_path}")

    # Experiment Loop
    logger.info("Starting experiment")
    total_processed_count = 0
    try:
        with open(output_path, 'a', encoding='utf-8') as f_out:
            for subtask in tqdm(subtasks_to_run, desc="Subtasks Progress"):
                logger.info(f"--- Processing Subtask: {subtask} ---")

                if subtask not in full_dataset or args.language not in full_dataset[subtask]:
                    logger.warning(f"Subtask {subtask} or language {args.language} not found in dataset. Skipping.")
                    continue

                task_data = full_dataset[subtask][args.language]
                end_index = min(args.start_index + args.num_questions, len(task_data))

                if args.start_index >= len(task_data) or args.start_index >= end_index:
                    logger.info(f"Start index {args.start_index} is beyond available data for subtask {subtask} ({len(task_data)} items). Skipping.")
                    continue

                logger.info(f"Processing questions {args.start_index} to {end_index - 1}")
                question_indices_to_process = range(args.start_index, end_index)
                for i in tqdm(question_indices_to_process, desc=f"  {subtask} Qs", leave=False): # leave=False for nested bars
                    data_item = task_data[i]
                    question_index_in_run = i

                    logger.info(f"Processing {subtask} - {args.language} - Question: {question_index_in_run}")

                    # Permutation Loop
                    original_labels = ['A', 'B', 'C', 'D']
                    num_perms_to_run = min(args.num_permutations, 24)
                    if args.num_permutations > 24:
                        logger.warning(f"--num_permutations requested {args.num_permutations}, but maximum is 24. Using 24.")

                    perm_iterator = itertools.islice(itertools.permutations(original_labels), num_perms_to_run)
                
                    for p_idx, current_permutation_tuple in enumerate(perm_iterator):
                        total_permutations_in_run = num_perms_to_run
                        current_permutation = list(current_permutation_tuple)
                        perm_string = "".join(current_permutation)
                        logger.info(f"    Running Permutation {p_idx + 1}/{total_permutations_in_run} ({perm_string}) for Q_idx:{question_index_in_run}")
                        # Format Prompt
                        current_prompt = format_prompt(template_content, data_item, current_permutation, args.language, args.prompt_format)
                        if not current_prompt:
                            logger.warning(f"Skipping Q:{question_index_in_run}, Perm:{perm_string} - Failed to format prompt.")
                            continue
                        # print(current_prompt)
                        # Call LLM API
                        api_response, api_ok = call_llm_api(client, args.model_family, args.model_name, current_prompt)
                        if not api_ok:
                            logger.warning(f"API call failed for Q:{question_index_in_run}, Perm:{perm_string}")

                        # Parse Response
                        parsed_answer = None
                        if api_ok and api_response:
                            response_text = None
                            try:
                                if args.model_family == 'gemini':
                                    # print(api_response.text)
                                    # print(api_response)
                                    response_text = api_response.text
                                elif args.model_family == 'mistral':
                                    response_text = api_response.choices[0].message.content
                            except AttributeError:
                                logger.warning(f"Attribute error for Q:{question_index_in_run}, Perm:{perm_string}. Response: {api_response}")
                                response_text = None
                            except Exception as e:
                                logger.error(f"Error accessing response for Q:{question_index_in_run}, Perm:{perm_string}: {e}")
                                response_text = None

                            if response_text:
                                parsed_answer = parse_response(response_text)
                                if parsed_answer:
                                    logger.info(f"Parsed answer for Q:{question_index_in_run}, Perm:{perm_string}: '{parsed_answer}'")
                                else:
                                    logger.warning(f"Failed to parse answer for Q:{question_index_in_run}, Perm:{perm_string}: {response_text[:100]}...")
                            else:
                                logger.warning(f"No response text for Q:{question_index_in_run}, Perm:{perm_string}")

                        # Structure Result
                        result_dict = structure_result(
                            data_item=data_item,
                            subtask=subtask,
                            language=args.language,
                            model_name=args.model_name,
                            input_format=args.prompt_format,
                            option_permutation=current_permutation,
                            api_raw_response=api_response,
                            api_call_successful=api_ok,
                            extracted_answer=parsed_answer,
                            log_probabilities=None,
                            question_index=question_index_in_run
                        )

                        # Save Result
                        try:
                            json_string = json.dumps(result_dict, ensure_ascii=False)
                            f_out.write(json_string + '\n')
                            total_processed_count += 1
                        except Exception as e:
                            logger.error(f"Failed to write result for Q:{question_index_in_run}, Perm:{perm_string}: {e}")

                        # Delay
                        if args.delay > 0:
                            logger.debug(f"Delaying for {args.delay} seconds...")
                            time.sleep(args.delay)

                    logger.info(f"Finished subtask: {subtask}")

    except Exception as e:
        logger.error(f"Experiment error: {e}")
    finally:
        logger.info("Experiment finished")
        logger.info(f"Total questions processed: {total_processed_count}")

if __name__ == "__main__":
    main()

"""
    --- How to run in terminal ---
    --model_family gemini \
    --model_name gemini-2.0-flash-lite \
    --language en \   
    --prompt_format base \
    --subtasks abstract_algebra \
    --num_questions 1 \
    --output_file output_file_name.jsonl \      
    --delay 5
    
    """
